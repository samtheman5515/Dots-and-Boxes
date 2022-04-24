from tkinter import *
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
class DotsAndBoxes:
    def __init__(self):
        self.window = Tk()
        self.window.title("Dots and boxes.")
        self.canvas = Canvas(self.window, width = 600, height = 600)
        self.canvas.pack()
        self.window.bind("<Button-1>", self.click)
        self.playeroneturn = True
        self.playeronescore = 0
        self.playertwoscore = 0
        self.rows = [0] * (board_size_dots * (board_size_dots - 1))
        self.columns = [0] * (board_size_dots * (board_size_dots -1))
        self.boxes = [0] * ((board_size_dots -1) * (board_size_dots-1))
        self.play_again()
    def attempt_fill(self, boxIndex, value):
        if self.boxes[boxIndex] == 0:
            r1 = boxIndex
            r2 = r1 + board_size_dots - 1
            c1 = boxIndex + int(boxIndex/(board_size_dots-1))
            c2 = c1 + 1
            if self.rows[r1] != 0 and self.rows[r2] != 0 and self.columns[c1] != 0 and self.columns[c2] != 0:
                self.boxes[boxIndex] = value
                return True
        return False
    def set_row(self, index, value):
        self.rows[index] = value
        res = []
        box1 = index
        box2 = index - (board_size_dots-1)
        if box1 < len(self.boxes) and self.attempt_fill(box1, value):
            res.append(box1)
        if box2 >= 0 and self.attempt_fill(box2, value):
            res.append(box2)
        return res
    def set_column(self, index, value):
        self.columns[index] = value
        res = []
        box1 = index - int(index/board_size_dots)
        box2 = box1 - 1
        r = index % board_size_dots
        if r < board_size_dots -1 and self.attempt_fill(box1, value):
            res.append(box1)
        if r > 0 and self.attempt_fill(box2, value):
            res.append(box2)
        return res
    def play_again(self):
        for i in range (len(self.columns)):
            self.columns[i] = 0
        for i in range (len(self.rows)):
            self.rows[i] = 0
        for i in range (len(self.boxes)):
            self.boxes[i] = 0
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
                value = self.boxes[index]
                if value != 0:
                    x = startX + j * distance_between_dots
                    y = startY + i * distance_between_dots
                    c = COLOR_P1_FILL if value == 1 else COLOR_P2_FILL
                    self.canvas.create_rectangle(x, y, x + distance_between_dots, y + distance_between_dots, fill=c)
        index = -1
        for i in range(board_size_dots -1):
            for j in range(board_size_dots):
                index +=1
                value = self.columns[index]
                if value != 0:
                    x = startX + j * distance_between_dots
                    y = startY + i * distance_between_dots
                    c = COLOR_P1_LINE if value == 1 else COLOR_P2_LINE
                    self.canvas.create_line(x, y, x, y + distance_between_dots, fill = c, width = line_thickness)
        index = -1
        for i in range(board_size_dots):
            for j in range(board_size_dots -1):
                index += 1
                value = self.rows[index]
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
        turntext = "Turn: Player " + ("1" if self.playeroneturn else "2")
        textcolor = COLOR_P1_FILL if self.playeroneturn else COLOR_P2_FILL
        self.canvas.create_text(board_size_px/2, 5, text = turntext, fill = textcolor, font = "cmr 15 bold", anchor = N)
    def handle_turn(self, index, is_row):
        value = 1 if self.playeroneturn else 2
        if is_row:
            if self.rows[index] != 0:
                return
            filled_boxes = self.set_row(index, value)
        else:
            if self.columns[index] != 0:
                return
            filled_boxes = self.set_column(index, value)
        points = len(filled_boxes)
        if points == 0:
            self.playeroneturn = not self.playeroneturn
        elif self.playeroneturn:
            self.playeronescore += points
        else:
            self.playertwoscore += points
        self.draw_board()

    def click(self, event):
        x = event.x-startX
        y= event.y-startY
        for i in range(board_size_dots):
            for j in range(board_size_dots-1):
                x1 = j*distance_between_dots + dot_radius
                y1 = i* distance_between_dots - (click_area_size/2)
                x2 = x1+distance_between_dots -(dot_radius * 2)
                y2 = y1+click_area_size
                if x1 < x < x2 and y1 < y < y2:
                    index = j + i * (board_size_dots -1)
                    self.handle_turn(index, True)
                    return
        for i in range(board_size_dots-1):
            for j in range(board_size_dots):
                x1 = j*distance_between_dots - (click_area_size/2)
                y1 = i* distance_between_dots + dot_radius
                x2 = x1 +click_area_size
                y2 = y1 + distance_between_dots - (dot_radius *2)
                if x1 < x < x2 and y1 < y < y2:
                    index = j + i * (board_size_dots)
                    self.handle_turn(index, False)
                    return
app = DotsAndBoxes()
app.window.mainloop()