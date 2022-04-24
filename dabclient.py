from DABcommon import *
import tkinter as tk
import tkinter.messagebox
import tkinter.simpledialog
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread
board_size_px = 600
board_size_dots = 6
distance_between_dots = board_size_px/board_size_dots
dot_radius = 12
line_thickness = 10
click_area_size = int(line_thickness * 1.1)
COLOR_P1_LINE = '#0492CF'
COLOR_P1_FILL = '#67B0CF'
COLOR_P2_LINE = '#EE4035'
COLOR_P2_FILL = '#EE7E77'
startX = distance_between_dots/2
startY = distance_between_dots/2
def display_error_message(res):
    tk.messagebox.showerror("Error response from server", "%d: %s"%(res.msg["id"], res.msg["description"]))
def display_unexpected_message(res):
    tk.messagebox.showerror("Unexpected response from server", "%d, %s: %s"%(res.id, type(res.msg), json.dumps(res.msg)))
def ask_name_and_room(parent):
    root = tk.Toplevel(parent)
    tk.Label(root, text = "name:").pack()
    var_name = tk.StringVar()
    tk.Entry(root, textvariable = var_name).pack()
    var_room_name = tk.StringVar()
    tk.Entry(root, textvariable = var_room_name).pack()
    tk.Button(root, text = "enter", command = lambda: root.destroy()).pack()
    tk.Button(root, text = "Leave server", command = lambda: [var_name.set("!leave"), root.destroy()]).pack()
    root.protocol("WM_DELETE_WINDOW", lambda:[var_name.set("!leave"),root.destroy()])
    parent.wait_window(root)
    name = var_name.get()
    roomname = var_room_name.get()
    return name, roomname
class Client(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # self.window = tk.Tk()
        # self.window.title("Dots and boxes")
        parent.protocol("WM_DELETE_WINDOW", self.onclose)
        parent.bind("<Button-1>", self.click)
        self.canvas = tk.Canvas(self, width = board_size_px, height = board_size_px)
        self.canvas.pack()
        self.pack()
        self.game = Game(board_size_dots)
        self.socket = None
        self.waitingforplayer = False
        self.has_won_game = False
        self.is_player_one = False
        self.other_player_name = ""
        self.accept_thread = None
        self.is_closing = False
        self.canvas.after(50, self.ask_connect)
    def disconnect(self):
        if self.socket is not None:
            Packet(MSGID_DISCONNECT).send(self.socket)
            self.socket.close()
            self.socket = None
    def ask_connect(self):
        continue_asking = True
        while continue_asking:
            address_str = tk.simpledialog.askstring("Connect to", "Enter the IP address to connect to")
            if address_str is None:
                self.onclose()
                return
            if len(address_str) == 0:
                tk.messagebox.showwarning("No IP address", "Need to enter an IP address")
                continue
            else:
                address_str = address_str.split(":")
            serverhost = address_str[0]
            serverport = default_port
            if len(address_str) > 1:
                try:
                    serverport = int(address_str[1])
                    if serverport < 1 or serverport > 65535:
                        raise ValueError()
                except ValueError:
                    tk.messagebox.showwarning("Invalid IP Address", "Invalid port number: %s" % address_str[1])
                    continue
            try:
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.connect((serverhost, serverport))
                continue_asking = False
            except ConnectionRefusedError as e:
                tk.messagebox.showerror("Could not connect", "Could not connect to server:%s" % e)
                print(e)
        self.canvas.after(50, self.ask_join_or_create)
    def ask_join_or_create(self):
        self.waitingforplayer = False
        continue_asking = True
        while continue_asking:
            name, roomname = ask_name_and_room(self)
            if name == "":
                tk.messagebox.showwarning("Invalid name", "Name cannot be empty")
            elif name == "!leave":
                self.disconnect()
                self.canvas.after(50, self.ask_connect)
                return
            elif roomname != "":
                Packet(MSGID_CONNECT, ClientConnectMessage(name, roomname).encode()).send(self.socket)
                res = Packet.receive(self.socket)
                if res.id == MSGID_ERROR:
                    display_error_message(res)
                elif res.id == MSGID_ROOMJOINED:
                    tk.messagebox.showinfo("Joined the room", "Room %s has been joined" % roomname)
                    continue_asking = False
                    self.is_player_one = False
                    self.other_player_name = roomname
                else:
                    display_unexpected_message(res)
            else:
                Packet(MSGID_CONNECT, ClientConnectMessage(name, roomname).encode()).send(self.socket)
                res = Packet.receive(self.socket)
                if res.id == MSGID_ERROR:
                    display_error_message(res)
                elif res.id == MSGID_ROOMCREATED:
                    tk.messagebox.showinfo("Room created", "Room %s has successfully been created" % roomname)
                    self.waitingforplayer = True
                    continue_asking = False
                    self.is_player_one = True
                    self.other_player_name = None
                else:
                    display_unexpected_message(res)
        self.accept_thread = Thread(target=self.receive_messages)
        self.accept_thread.start()
        self.draw_board()
    def receive_messages(self):

        while True:
            res = Packet.receive(self.socket)
            if res.id == MSGID_ERROR:
                display_error_message(res)
            elif res.id == MSGID_PLAYER2JOINED:
                self.other_player_name = res.msg
                tk.messagebox.showinfo("Player 2 joined", "player %s joined your game"%res.msg)
                self.waitingforplayer = False
                self.draw_board()
            elif res.id == MSGID_TURN:
                self.handle_turn(res.msg)
            elif res.id == MSGID_GAMEOVER:
                p1score = res.msg["playerone"]
                p2score = res.msg["playertwo"]
                if (self.is_player_one and p1score > p2score) or (not self.is_player_one and p2score > p1score):
                    self.has_won_game = True
                self.draw_board()
                playagain = tk.messagebox.askyesno("Play again?", "Do you want to play again?")
                Packet(MSGID_PLAYAGAIN, playagain).send(self.socket)
            elif res.id == MSGID_ENDGAME:
                tk.messagebox.showinfo("Game ending", "Both players have not agreed to play again")
                self.onclose()
            elif res.id == MSGID_NEWGAME:
                tk.messagebox.showinfo("New game", "Both players have agreed to play a new game")
                self.reset()
            else:
                display_unexpected_message(res)
    def reset(self):
        self.game.reset()
        self.has_won_game = False
        self.draw_board()
    def draw_board(self):
        self.canvas.delete("all")
        for i in range(board_size_dots):
            a = i * distance_between_dots + distance_between_dots/2
            b = distance_between_dots/2
            self.canvas.create_line(a, b, a, board_size_px-b, fill = "gray", dash = (2,2))


            self.canvas.create_line(b, a, board_size_px-b, a, fill = "gray", dash = (2,2))
        index = -1
        for i in range(board_size_dots - 1):
            for j in range(board_size_dots -1):
                index += 1
                value = self.game.board.boxes[index]
                if value != 0:
                    x = startX + j * distance_between_dots
                    y = startY + i * distance_between_dots
                    c = COLOR_P1_FILL if value == 1 else COLOR_P2_FILL
                    self.canvas.create_rectangle(x, y, x + distance_between_dots, y + distance_between_dots, fill=c)
        index = -1
        for i in range(board_size_dots -1):
            for j in range(board_size_dots):
                index +=1
                value = self.game.board.columns[index]
                if value != 0:
                    x = startX + j * distance_between_dots
                    y = startY + i * distance_between_dots
                    c = COLOR_P1_LINE if value == 1 else COLOR_P2_LINE
                    self.canvas.create_line(x, y, x, y + distance_between_dots, fill = c, width = line_thickness)
        index = -1
        for i in range(board_size_dots):
            for j in range(board_size_dots -1):
                index += 1
                value = self.game.board.rows[index]
                if value != 0:
                    x = startX + j * distance_between_dots
                    y = startY + i * distance_between_dots
                    c = COLOR_P1_LINE if value == 1 else COLOR_P2_LINE
                    self.canvas.create_line(x, y, x + distance_between_dots, y, fill=c, width=line_thickness)
        for i in range(board_size_dots):
            for j in range(board_size_dots):
                x = i * distance_between_dots + startX
                y = j * distance_between_dots + startY
                self.canvas.create_oval(x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius, fill = "green", outline = "green")
        selfcolor = COLOR_P1_FILL if self.is_player_one else COLOR_P2_FILL
        othercolor = COLOR_P2_FILL if self.is_player_one else COLOR_P1_FILL
        if self.other_player_name is None:
            headertext = "Waiting for other player"
            headercolor = "#5B5B5B"
        elif self.game.is_game_over():
            if self.has_won_game:
                headertext = "You win"
            else:
                headertext = "You lose"
            headercolor = selfcolor
        elif self.is_player_one == self.game.playeroneturn:
            headertext = "Your turn"
            headercolor = selfcolor
        else:
            headertext = "Waiting for %s..."%self.other_player_name
            headercolor = othercolor
        self.canvas.create_text(board_size_px/2, 5, text = headertext, fill = headercolor, font = "cmr 15 bold", anchor = tk.N)
    def handle_turn(self, turn_msg):
        desync = self.game.playeroneturn != turn_msg["was_playerone_turn"]
        filledboxes = self.game.handle_turn(turn_msg["index"], turn_msg["is_row"])
        desync = desync or filledboxes != turn_msg["filled_boxes"]
        if desync:
            pass
        self.draw_board()

    def handle_own_turn(self, index, is_row):
        Packet(MSGID_TURN, ClientTurnMessage(index, is_row).encode()).send(self.socket)
        # res = Packet.receive(self.socket)
        # if res.id == MSGID_ERROR:
        #     display_error_message(res)
        # elif res.id != MSGID_TURN:
        #     display_unexpected_message(res)
        # else:
        #     self.handle_turn(res.msg)

    def click(self, event):
        x = event.x - startX
        y = event.y - startY
        if not self.waitingforplayer and self.is_player_one == self.game.playeroneturn:
            for i in range(board_size_dots):
                for j in range(board_size_dots - 1):
                    x1 = j * distance_between_dots + dot_radius
                    y1 = i * distance_between_dots - (click_area_size / 2)
                    x2 = x1 + distance_between_dots - (dot_radius * 2)
                    y2 = y1 + click_area_size
                    if x1 < x < x2 and y1 < y < y2:
                        index = j + i * (board_size_dots - 1)
                        self.handle_own_turn(index, True)
                        return
            for i in range(board_size_dots - 1):
                for j in range(board_size_dots):
                    x1 = j * distance_between_dots - (click_area_size / 2)
                    y1 = i * distance_between_dots + dot_radius
                    x2 = x1 + click_area_size
                    y2 = y1 + distance_between_dots - (dot_radius * 2)
                    if x1 < x < x2 and y1 < y < y2:
                        index = j + i * (board_size_dots)
                        self.handle_own_turn(index, False)
                        return
    def onclose(self):
        Packet(MSGID_DISCONNECT).send(self.socket)
        self.socket.close()
        self.parent.destroy()
if __name__== "__main__":
    root = tk.Tk()
    root.title("Dots and boxes")
    client = Client(root)
    client.mainloop()