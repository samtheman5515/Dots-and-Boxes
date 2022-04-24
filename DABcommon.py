import json
default_port = 33001
class Board:
    def __init__(self, size_dots):
        self.size_dots = size_dots
        self.size_boxes = size_dots - 1
        self.rows = [0] * (self.size_dots * self.size_boxes)
        self.columns = [0] * (self.size_dots * self.size_boxes)
        self.boxes = [0] * (self.size_boxes * self.size_boxes)

    def attempt_fill(self, boxIndex, value):
        if self.boxes[boxIndex] == 0:
            r1 = boxIndex
            r2 = r1 + self.size_boxes
            c1 = boxIndex + int(boxIndex / self.size_boxes)
            c2 = c1 + 1
            if self.rows[r1] != 0 and self.rows[r2] != 0 and self.columns[c1] != 0 and self.columns[c2] != 0:
                self.boxes[boxIndex] = value
                return True
        return False

    def set_row(self, index, value):
        self.rows[index] = value
        res = []
        box1 = index
        box2 = index - self.size_boxes
        if box1 < len(self.boxes) and self.attempt_fill(box1, value):
            res.append(box1)
        if box2 >= 0 and self.attempt_fill(box2, value):
            res.append(box2)
        return res

    def set_column(self, index, value):
        self.columns[index] = value
        res = []
        box1 = index - int(index/self.size_dots)
        box2 = box1 - 1
        r = index % self.size_dots
        if r < self.size_boxes and self.attempt_fill(box1, value):
            res.append(box1)
        if r > 0 and self.attempt_fill(box2, value):
            res.append(box2)
        return res

    def clear(self):
        for i in range(len(self.columns)):
            self.columns[i] = 0
        for i in range(len(self.rows)):
            self.rows[i] = 0
        for i in range(len(self.boxes)):
            self.boxes[i] = 0
class Game:
    def __init__(self, board_size_dots):
        self.board = Board(board_size_dots)
        self.playeroneturn = True
    def calculate_scores(self):
        scores = [0,0]
        for box in self.board.boxes:
            if box == 1:
                scores[0] += 1
            elif box == 2:
                scores[1] += 1
        return scores
    def is_game_over(self):
        for box in self.board.boxes:
            if box == 0:
                return False
        return True
    def reset(self):
        self.board.clear()
        self.playeroneturn = True
    def handle_turn(self, index, is_row):
        value = 1 if self.playeroneturn else 2
        if is_row:
            if self.board.rows[index] != 0:
                return None
            filled_boxes = self.board.set_row(index, value)
        else:
            if self.board.columns[index] != 0:
                return None
            filled_boxes = self.board.set_column(index, value)
        points = len(filled_boxes)
        if points == 0:
            self.playeroneturn = not self.playeroneturn
        return filled_boxes
PACKET_ENCODING = "UTF-8"
MSGID_BADFORMAT = -1
MSGID_ERROR = 0
MSGID_CONNECT = 1
MSGID_DISCONNECT = 2
MSGID_ROOMCREATED = 3
MSGID_PLAYER2JOINED = 4
MSGID_ROOMJOINED = 5
MSGID_TURN = 6
MSGID_GAMEOVER = 7
MSGID_PLAYAGAIN = 8
MSGID_NEWGAME = 9
MSGID_ENDGAME = 10

ERRID_UNEXPECTED = 1
ERRID_NAMETAKEN = 2
ERRID_ROOMNOTFOUND = 3
ERRID_INVALIDMOVE = 4
class Packet:
    def __init__(self, id, msg = None):
        self.id = id
        self.msg = msg
    def __str__(self):
        return json.dumps({"id": self.id, "msg": self.msg})
    def __bytes__(self):
        return bytes(str(self), PACKET_ENCODING)
    def send(self, dst_socket):
        dst_socket.send(bytes(self))
    @staticmethod
    def decode(msg_bytes):
        msg = msg_bytes.decode(PACKET_ENCODING)
        try:
            obj = json.loads(msg)
            return Packet(obj["id"], obj["msg"])
        except json.decoder.JSONDecodeError:
            return Packet(MSGID_BADFORMAT, msg)
    @staticmethod
    def receive(src_socket, buffer_size = 1024):
        try:
            return Packet.decode(src_socket.recv(buffer_size))
        except ConnectionResetError:
            return Packet(MSGID_DISCONNECT)
    @staticmethod
    def error(id, description = None):
        return Packet(MSGID_ERROR, ErrorMessage(id, description).encode())
class Message:
    def encode(self):
        return {}
class ErrorMessage(Message):
    def __init__(self, id, description):
        self.id = id
        self.description = description
    def encode(self):
        return{"id":self.id, "description":self.description}
class ClientConnectMessage(Message):
    def __init__(self, playername, roomname):
        self.playername = playername
        self.roomname = roomname
    def encode(self):
        return{"player_name":self.playername, "room_name":self.roomname}
class ClientTurnMessage(Message):
    def __init__(self, index, is_row):
        self.index = index
        self.is_row = is_row
    def encode(self):
        return{"index": self.index, "is_row": self.is_row}
class ServerTurnMessage(Message):
    def __init__(self, index, is_row, was_playerone_turn, filled_boxes):
        self.index = index
        self.is_row = is_row
        self.was_playerone_turn = was_playerone_turn
        self.filled_boxes = filled_boxes
    def encode(self):
        return{"index":self.index, "is_row":self.is_row, "was_playerone_turn":self.was_playerone_turn, "filled_boxes":self.filled_boxes}
class ServerGameOverMessage(Message):
    def __init__(self, playerone_score, playertwo_score):
        self.playerone_score = playerone_score
        self.playertwo_score = playertwo_score
    def encode(self):
        return{"playerone":self.playerone_score, "playertwo":self.playertwo_score}