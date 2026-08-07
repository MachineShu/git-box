import random
import tkinter as tk
from tkinter import messagebox


CELL_SIZE = 30
COLUMNS = 10
ROWS = 20
SIDEBAR_WIDTH = 150
TICK_MS = 500

SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}

COLORS = {
    "I": "#00bcd4",
    "O": "#f6c343",
    "T": "#9c27b0",
    "S": "#4caf50",
    "Z": "#e53935",
    "J": "#3f51b5",
    "L": "#ff8f00",
}


class Tetris:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Tetris")
        self.root.resizable(False, False)

        width = COLUMNS * CELL_SIZE + SIDEBAR_WIDTH
        height = ROWS * CELL_SIZE
        self.canvas = tk.Canvas(root, width=width, height=height, bg="#121212", highlightthickness=0)
        self.canvas.pack()

        self.board = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.game_over = False
        self.paused = False

        self.current = self.new_piece()
        self.next_piece = self.new_piece()

        self.bind_keys()
        self.draw()
        self.tick()

    def bind_keys(self):
        self.root.bind("<Left>", lambda _event: self.move(-1, 0))
        self.root.bind("<Right>", lambda _event: self.move(1, 0))
        self.root.bind("<Down>", lambda _event: self.move(0, 1))
        self.root.bind("<Up>", lambda _event: self.rotate())
        self.root.bind("<space>", lambda _event: self.hard_drop())
        self.root.bind("p", lambda _event: self.toggle_pause())
        self.root.bind("r", lambda _event: self.restart())

    def new_piece(self):
        shape = random.choice(list(SHAPES))
        matrix = [row[:] for row in SHAPES[shape]]
        return {
            "shape": shape,
            "matrix": matrix,
            "x": COLUMNS // 2 - len(matrix[0]) // 2,
            "y": 0,
        }

    def cells_for(self, piece):
        cells = []
        for y, row in enumerate(piece["matrix"]):
            for x, occupied in enumerate(row):
                if occupied:
                    cells.append((piece["x"] + x, piece["y"] + y))
        return cells

    def is_valid(self, piece):
        for x, y in self.cells_for(piece):
            if x < 0 or x >= COLUMNS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x]:
                return False
        return True

    def move(self, dx, dy):
        if self.game_over or self.paused:
            return
        moved = {**self.current, "x": self.current["x"] + dx, "y": self.current["y"] + dy}
        if self.is_valid(moved):
            self.current = moved
            self.draw()
            return True
        if dy:
            self.lock_piece()
        return False

    def rotate(self):
        if self.game_over or self.paused:
            return
        matrix = self.current["matrix"]
        rotated = [list(row) for row in zip(*matrix[::-1])]
        candidate = {**self.current, "matrix": rotated}

        for offset in (0, -1, 1, -2, 2):
            kicked = {**candidate, "x": candidate["x"] + offset}
            if self.is_valid(kicked):
                self.current = kicked
                self.draw()
                return

    def hard_drop(self):
        if self.game_over or self.paused:
            return
        while self.move(0, 1):
            self.score += 2
        self.draw()

    def toggle_pause(self):
        if self.game_over:
            return
        self.paused = not self.paused
        self.draw()

    def lock_piece(self):
        for x, y in self.cells_for(self.current):
            if y < 0:
                self.end_game()
                return
            self.board[y][x] = self.current["shape"]

        cleared = self.clear_lines()
        self.add_score(cleared)

        self.current = self.next_piece
        self.next_piece = self.new_piece()
        if not self.is_valid(self.current):
            self.end_game()
        self.draw()

    def clear_lines(self):
        remaining = [row for row in self.board if any(cell is None for cell in row)]
        cleared = ROWS - len(remaining)
        new_rows = [[None for _ in range(COLUMNS)] for _ in range(cleared)]
        self.board = new_rows + remaining
        self.lines += cleared
        self.level = self.lines // 10 + 1
        return cleared

    def add_score(self, cleared):
        if cleared == 0:
            return
        rewards = {1: 100, 2: 300, 3: 500, 4: 800}
        self.score += rewards.get(cleared, 0) * self.level

    def tick(self):
        if not self.game_over and not self.paused:
            self.move(0, 1)
        speed = max(80, TICK_MS - (self.level - 1) * 35)
        self.root.after(speed, self.tick)

    def restart(self):
        self.board = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.game_over = False
        self.paused = False
        self.current = self.new_piece()
        self.next_piece = self.new_piece()
        self.draw()

    def end_game(self):
        self.game_over = True
        self.draw()
        messagebox.showinfo("Game Over", f"Final score: {self.score}")

    def draw_cell(self, x, y, color):
        x1 = x * CELL_SIZE
        y1 = y * CELL_SIZE
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#242424")
        self.canvas.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3, outline="#ffffff", stipple="gray75")

    def draw(self):
        self.canvas.delete("all")
        self.draw_board()
        self.draw_sidebar()
        if self.paused:
            self.draw_center_text("PAUSED")
        if self.game_over:
            self.draw_center_text("GAME OVER")

    def draw_board(self):
        for y in range(ROWS):
            for x in range(COLUMNS):
                cell = self.board[y][x]
                if cell:
                    self.draw_cell(x, y, COLORS[cell])
                else:
                    x1 = x * CELL_SIZE
                    y1 = y * CELL_SIZE
                    self.canvas.create_rectangle(
                        x1,
                        y1,
                        x1 + CELL_SIZE,
                        y1 + CELL_SIZE,
                        fill="#181818",
                        outline="#242424",
                    )

        for x, y in self.cells_for(self.current):
            if y >= 0:
                self.draw_cell(x, y, COLORS[self.current["shape"]])

    def draw_sidebar(self):
        left = COLUMNS * CELL_SIZE
        self.canvas.create_rectangle(left, 0, left + SIDEBAR_WIDTH, ROWS * CELL_SIZE, fill="#202020", outline="")
        self.canvas.create_text(left + 20, 35, anchor="w", fill="#f5f5f5", font=("Arial", 18, "bold"), text="TETRIS")
        self.canvas.create_text(left + 20, 85, anchor="w", fill="#d0d0d0", font=("Arial", 12), text=f"Score: {self.score}")
        self.canvas.create_text(left + 20, 115, anchor="w", fill="#d0d0d0", font=("Arial", 12), text=f"Level: {self.level}")
        self.canvas.create_text(left + 20, 145, anchor="w", fill="#d0d0d0", font=("Arial", 12), text=f"Lines: {self.lines}")
        self.canvas.create_text(left + 20, 200, anchor="w", fill="#f5f5f5", font=("Arial", 12, "bold"), text="Next")

        matrix = self.next_piece["matrix"]
        color = COLORS[self.next_piece["shape"]]
        start_x = left + 45
        start_y = 230
        preview_size = 20
        for y, row in enumerate(matrix):
            for x, occupied in enumerate(row):
                if occupied:
                    x1 = start_x + x * preview_size
                    y1 = start_y + y * preview_size
                    self.canvas.create_rectangle(
                        x1,
                        y1,
                        x1 + preview_size,
                        y1 + preview_size,
                        fill=color,
                        outline="#303030",
                    )

        help_text = "Keys\n\nLeft/Right\nDown\nUp rotate\nSpace drop\nP pause\nR restart"
        self.canvas.create_text(left + 20, 355, anchor="nw", fill="#bdbdbd", font=("Arial", 11), text=help_text)

    def draw_center_text(self, text):
        board_width = COLUMNS * CELL_SIZE
        y = ROWS * CELL_SIZE // 2
        self.canvas.create_rectangle(24, y - 42, board_width - 24, y + 42, fill="#000000", outline="#555555")
        self.canvas.create_text(board_width // 2, y, fill="#ffffff", font=("Arial", 24, "bold"), text=text)


def main():
    root = tk.Tk()
    Tetris(root)
    root.mainloop()


if __name__ == "__main__":
    main()
