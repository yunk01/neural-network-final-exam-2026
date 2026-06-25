from collections import deque
from pathlib import Path
from PIL import Image, ImageDraw
import csv


ROOT = Path(__file__).resolve().parent
MAZE_PATH = ROOT / "maze.jpg"
DEFAULT_GOAL = (450, 260)
WALKABLE_BRIGHTNESS = 80.0
TEXTURE_CLOSE_RADIUS = 1


def disk_offsets(radius):
    return [
        (dx, dy)
        for dy in range(-radius, radius + 1)
        for dx in range(-radius, radius + 1)
        if dx * dx + dy * dy <= radius * radius
    ]


def dilate(mask, radius):
    height, width = len(mask), len(mask[0])
    out = [[False] * width for _ in range(height)]
    offsets = disk_offsets(radius)
    for y, row in enumerate(mask):
        for x, value in enumerate(row):
            if not value:
                continue
            for dx, dy in offsets:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    out[ny][nx] = True
    return out


def erode(mask, radius, bounds):
    height, width = len(mask), len(mask[0])
    min_x, max_x, min_y, max_y = bounds
    out = [[False] * width for _ in range(height)]
    offsets = disk_offsets(radius)
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            out[y][x] = all(
                0 <= x + dx < width and 0 <= y + dy < height and mask[y + dy][x + dx]
                for dx, dy in offsets
            )
    return out


def close_texture_gaps(mask, radius, bounds):
    return erode(dilate(mask, radius), radius, bounds)


def tint_walkable(img, grid):
    out = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_pix = overlay.load()
    for y, row in enumerate(grid):
        for x, value in enumerate(row):
            if value:
                overlay_pix[x, y] = (0, 120, 255, 55)
    return Image.alpha_composite(out, overlay).convert("RGB")


def load_grid():
    img = Image.open(MAZE_PATH).convert("RGB")
    pix = img.load()
    width, height = img.size
    bright_points = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if sum(pix[x, y]) / 3.0 > 80.0
    ]
    min_x = min(p[0] for p in bright_points)
    max_x = max(p[0] for p in bright_points)
    min_y = min(p[1] for p in bright_points)
    max_y = max(p[1] for p in bright_points)
    raw_open_grid = [[False] * width for _ in range(height)]
    yellow_points = []
    for y in range(height):
        for x in range(width):
            r, g, b = pix[x, y]
            yellow = r > 190 and g > 190 and (int(r) + int(g) - 2 * int(b)) > 120
            bright = (r + g + b) / 3.0
            inside_maze = min_x <= x <= max_x and min_y <= y <= max_y
            raw_open_grid[y][x] = inside_maze and (yellow or bright > WALKABLE_BRIGHTNESS)
            if yellow:
                yellow_points.append((x, y))
    if not yellow_points:
        raise RuntimeError("No yellow start point was detected.")
    open_grid = close_texture_gaps(raw_open_grid, TEXTURE_CLOSE_RADIUS, (min_x, max_x, min_y, max_y))
    sx = round(sum(p[0] for p in yellow_points) / len(yellow_points))
    sy = round(sum(p[1] for p in yellow_points) / len(yellow_points))
    start = nearest_open(open_grid, (sx, sy))
    return img, open_grid, start


def nearest_open(grid, p, max_radius=60):
    width, height = len(grid[0]), len(grid)
    x0, y0 = p
    if 0 <= x0 < width and 0 <= y0 < height and grid[y0][x0]:
        return p
    for radius in range(1, max_radius + 1):
        best = None
        best_dist = None
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                x, y = x0 + dx, y0 + dy
                if 0 <= x < width and 0 <= y < height and grid[y][x]:
                    dist = dx * dx + dy * dy
                    if best is None or dist < best_dist:
                        best = (x, y)
                        best_dist = dist
        if best is not None:
            return best
    raise RuntimeError("No open point near the requested goal.")


def shortest_path(grid, start, goal):
    width, height = len(grid[0]), len(grid)
    q = deque([start])
    parent = {start: None}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            break
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] and (nx, ny) not in parent:
                parent[(nx, ny)] = (x, y)
                q.append((nx, ny))
    if goal not in parent:
        return None
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    return path


def save_overlay(img, path, start, goal, out_path, grid=None):
    out = tint_walkable(img, grid) if grid is not None else img.copy()
    draw = ImageDraw.Draw(out)
    if path:
        draw.line(path, fill=(255, 0, 0), width=3)
    for center, color in [(start, (0, 180, 0)), (goal, (0, 80, 255))]:
        x, y = center
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
    out.save(out_path)


def main():
    img, grid, start = load_grid()
    requested_goal = DEFAULT_GOAL
    goal = nearest_open(grid, requested_goal)
    path = shortest_path(grid, start, goal)
    out_png = Path("maze_path_overlay.png")
    save_overlay(img, path, start, goal, out_png, grid)
    with open("maze_result.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["start_x", "start_y", "requested_goal_x", "requested_goal_y", "goal_x", "goal_y", "reachable", "path_length_pixels"])
        writer.writerow([start[0], start[1], requested_goal[0], requested_goal[1], goal[0], goal[1], path is not None, 0 if path is None else len(path) - 1])
    if path is not None:
        with open("maze_path.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y"])
            writer.writerows(path)
    print(f"start={start}, requested_goal={requested_goal}, snapped_goal={goal}")
    print("reachable=", path is not None, "path_length_pixels=", 0 if path is None else len(path) - 1)


if __name__ == "__main__":
    main()
