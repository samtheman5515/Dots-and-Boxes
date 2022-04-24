from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
from DABcommon import *
clients = {}
games = {}
host = ""
address = (host, default_port)
server = socket(AF_INET, SOCK_STREAM)
server.bind(address)
should_run = True
def is_packet_expected(pkt, src_socket, expected_msg_ids):
    if type(expected_msg_ids) != tuple:
        expected_msg_ids = (expected_msg_ids,)
    if pkt.id not in expected_msg_ids:
        error_message = "Expected message ID of one of (%s), got %d instead, %s"%(",".join(map(str, expected_msg_ids)), pkt.id, pkt.msg)
        print(error_message)
        Packet.error(ERRID_UNEXPECTED, error_message).send(src_socket)
        return False
    return True
def is_disconnect(pkt, client, playername):
    if pkt.id == MSGID_DISCONNECT:
        if playername is not None:
            print("player %s disconnected from the server."%playername)
            del clients[playername]
        else:
            print("Unnamed player disconnected from the server.")
        client.close()
        return True
    return False
def wait_play_again(client, playagain):
    pkt = Packet.receive(client)
    if pkt.id != MSGID_PLAYAGAIN:
        Packet.error(ERRID_UNEXPECTED, "Expected play again").send(client)
    else:
        playagain[0] = pkt.msg

def handle_incoming_client(client: socket):
    res = Packet.receive(client)
    if is_disconnect(res, client, None):
        return
    if not is_packet_expected(res, client, MSGID_CONNECT):
        return
    playername = res.msg["player_name"]
    if playername in clients:
        Packet.error(ERRID_NAMETAKEN, playername + " is already taken").send(client)
        return
    clients[playername] = client
    roomname = res.msg["room_name"]
    if roomname != "":
        if roomname not in games or roomname not in clients:
            Packet.error(ERRID_ROOMNOTFOUND, "Could not find the room %s"%roomname).send(client)
            return
        game = games[roomname]
        p1name = roomname
        p2name = playername
        p1client = clients[roomname]
        p2client = client
        Packet(MSGID_PLAYER2JOINED, playername).send(p1client)
        Packet(MSGID_ROOMJOINED).send(p2client)
        keep_playing = True
        while keep_playing:
            while not game.is_game_over():
                current_name = p1name if game.playeroneturn else p2name
                current_client = p1client if game.playeroneturn else p2client
                other_client = p2client if game.playeroneturn else p1client
                pkt = Packet.receive(current_client)
                if is_disconnect(pkt, current_client, current_name):
                    del games[p1name]
                    Packet.error(ERRID_PLAYERDISCONNECT, current_name).send(other_client)
                    return
                if not is_packet_expected(pkt, current_client, MSGID_TURN):
                    continue
                turn = pkt.msg
                was_player_one_turn = game.playeroneturn
                filled_boxes = game.handle_turn(turn["index"], turn["is_row"])
                if filled_boxes is None:
                    Packet.error(ERRID_INVALIDMOVE).send(current_client)
                    continue
                complete_turn = Packet(MSGID_TURN, ServerTurnMessage(turn["index"], turn["is_row"], was_player_one_turn, filled_boxes).encode())
                complete_turn.send(p1client)
                complete_turn.send(p2client)
            scores = game.calculate_scores()
            gameover = Packet(MSGID_GAMEOVER, ServerGameOverMessage(scores[0], scores[1]).encode())
            gameover.send(p1client)
            gameover.send(p2client)
            p1playagain = [None]
            p2playagain = [None]
            t1 = Thread(target= wait_play_again, args = (p1client, p1playagain))
            t2 = Thread(target = wait_play_again, args = (p2client, p2playagain))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            p1playagain = p1playagain[0]
            p2playagain = p2playagain[0]
            if p1playagain is None or not p1playagain or p2playagain is None or not p2playagain:
                keep_playing = False
                endgame = Packet(MSGID_ENDGAME)
                endgame.send(p1client)
                endgame.send(p2client)
                del games[p1name]
            else:
                newgame = Packet(MSGID_NEWGAME)
                newgame.send(p1client)
                newgame.send(p2client)
                game.reset()


    else:
        if playername in games:
            Packet.error(ERRID_NAMETAKEN, playername + " is already taken").send(client)
            return
        clients[playername] = client
        games[playername] = Game(6)
        Packet(MSGID_ROOMCREATED).send(client)
        res=Packet.receive(client)
        if is_disconnect(res, client, playername):
            del games[playername]
        elif is_packet_expected(res, client, MSGID_PLAYER2JOINED):
            pass
def accept_connections():
    while should_run:
        try:
            client, client_address = server.accept()
            print("%s:%s has connected"%client_address)
            Thread(target= handle_incoming_client, args=(client,)).start()
        except OSError:
            pass
if __name__ == "__main__":
    import tkinter as tk
    server.listen(5)
    print("Waiting for connection")
    Thread(target = accept_connections).start()
    root = tk.Tk()
    root.title("Dots and Boxes server")
    tk.Button(root, text = "Close the server", command = lambda: root.destroy()).pack()
    root.mainloop()
    should_run = False
    server.close()