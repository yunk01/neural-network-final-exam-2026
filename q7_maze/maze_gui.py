from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from PIL import ImageDraw, ImageTk

from maze_solver import DEFAULT_GOAL, load_grid, nearest_open, shortest_path


OUTPUT_PATH = Path(__file__).resolve().parent / "maze_interactive_result.png"


class MazeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Maze shortest path")

        self.base_img, self.grid, self.start = load_grid()
        self.current_goal = None
        self.current_path = None
        self.current_img = self.base_img.copy()
        self.tk_img = None

        self.canvas = tk.Canvas(
            root,
            width=self.base_img.width,
            height=self.base_img.height,
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 6))
        self.canvas.bind("<Button-1>", self.on_click)

        self.status = tk.StringVar()
        self.status_label = tk.Label(root, textvariable=self.status, anchor="w")
        self.status_label.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10)

        tk.Button(root, text="Reset", command=self.reset).grid(row=2, column=0, sticky="ew", padx=(10, 4), pady=10)
        tk.Button(root, text="Save result", command=self.save_result).grid(row=2, column=1, sticky="ew", padx=4, pady=10)
        tk.Button(root, text="Quit", command=root.destroy).grid(row=2, column=2, sticky="ew", padx=(4, 10), pady=10)

        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.columnconfigure(2, weight=1)

        self.solve_and_render(DEFAULT_GOAL, "Default target")

    def draw_solution(self, goal=None, path=None):
        img = self.base_img.copy()
        draw = ImageDraw.Draw(img)
        if path:
            draw.line(path, fill=(255, 0, 0), width=3)
        for center, color in [(self.start, (0, 180, 0)), (goal, (0, 80, 255))]:
            if center is None:
                continue
            x, y = center
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
        return img

    def show_image(self):
        self.tk_img = ImageTk.PhotoImage(self.current_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def solve_and_render(self, requested_goal, source_label):
        try:
            goal = nearest_open(self.grid, requested_goal)
        except RuntimeError as exc:
            self.current_goal = None
            self.current_path = None
            self.current_img = self.draw_solution()
            self.show_image()
            self.status.set(f"{source_label}: clicked={requested_goal}, no open point nearby ({exc})")
            return

        path = shortest_path(self.grid, self.start, goal)
        self.current_goal = goal
        self.current_path = path
        self.current_img = self.draw_solution(goal, path)
        self.show_image()

        if path is None:
            self.status.set(f"{source_label}: clicked={requested_goal}, snapped={goal}, unreachable")
        else:
            self.status.set(
                f"{source_label}: clicked={requested_goal}, snapped={goal}, "
                f"reachable, path length={len(path) - 1} pixels"
            )

    def on_click(self, event):
        self.solve_and_render((event.x, event.y), "Mouse target")

    def reset(self):
        self.solve_and_render(DEFAULT_GOAL, "Default target")

    def save_result(self):
        self.current_img.save(OUTPUT_PATH)
        messagebox.showinfo("Saved", f"Saved to:\n{OUTPUT_PATH}")


def main():
    root = tk.Tk()
    MazeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
