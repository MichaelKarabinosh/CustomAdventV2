import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider, CheckButtons
from matplotlib.colors import ListedColormap


# ===============================
# INPUT
# ===============================
INPUT_LINE = "500x500 | 250,250 | 10000,00000,00W01,0101111111100,00000 | 90"

# ===============================
# SIM
# ===============================
def create_grid(x, y):
    return np.zeros((y, x), dtype=int)

def create_infection(pattern):
    relative_list = []
    lines = pattern.split(",")
    cx = cy = 0

    for i in range(len(lines)):
        for j in range(len(lines[i])):
            if lines[i][j] == "W":
                cx = j
                cy = i

    for i in range(len(lines)):
        for j in range(len(lines[i])):
            if lines[i][j] == "1":
                relative_list.append((j - cx, cy - i))

    return relative_list

def simulate(grid, rel_list, days):
    grids = []
    weed_counts = []
    new_masks = []
    overlap_masks = []

    for _ in range(days):
        new_grid = grid.copy()
        new_mask = np.zeros_like(grid)
        overlap_mask = np.zeros_like(grid)

        weed_positions = np.argwhere(grid == 1)

        for y, x in weed_positions:
            for dx, dy in rel_list:
                ny = y - dy
                nx = x + dx
                if 0 <= ny < grid.shape[0] and 0 <= nx < grid.shape[1]:
                    if new_grid[ny, nx] == 1:
                        overlap_mask[ny, nx] = 1
                    elif new_grid[ny, nx] == 0:
                        new_mask[ny, nx] = 1
                    new_grid[ny, nx] = 1

        if np.array_equal(new_grid, grid):
            break

        grid = new_grid
        grids.append(grid.copy())
        weed_counts.append(int(np.sum(grid)))
        new_masks.append(new_mask.copy())
        overlap_masks.append(overlap_mask.copy())

    return grids, weed_counts, new_masks, overlap_masks

def compute_diffs(data, index):
    if index < 1:
        return 0, 0
    first = data[index] - data[index-1]
    if index < 2:
        return first, 0
    second = data[index] - 2*data[index-1] + data[index-2]
    return first, second

# ===============================
# BUILD SIM
# ===============================
info = INPUT_LINE.split("|")
gridx, gridy = map(int, info[0].strip().split("x"))
init_x, init_y = map(int, info[1].strip().split(","))
rel_list = create_infection(info[2].strip())
days = int(info[3].strip())

grid = create_grid(gridx, gridy)
grid[init_y, init_x] = 1

grids, weed_counts, new_masks, overlap_masks = simulate(grid, rel_list, days)

# ===============================
# GUI
# ===============================
class InfectionGUI:
    def __init__(self):
        self.index = 0
        self.running = True
        self.show_new = False
        self.show_overlap = False
        self.show_spiral = True
        self.theta = 0

        # speed system
        self.speed = 5          # default speed
        self.frame_counter = 0

        self.fig = plt.figure(figsize=(16,9))
        self.fig.patch.set_facecolor("#111111")

        self.fig.suptitle(
            "Michael's Awesome Sim",
            fontsize=22,
            color="white",
            fontweight="bold"
        )

        # ================= GRID =================
        self.ax_grid = self.fig.add_axes([0.05, 0.15, 0.55, 0.75])
        self.ax_grid.set_facecolor("black")

        self.cmap = ListedColormap([
            "black",
            "#ff4500",
            "#ffff00",
            "#00ffff"
        ])

        self.im = self.ax_grid.imshow(grids[0], cmap=self.cmap, vmin=0, vmax=3)
        self.ax_grid.set_xticks([])
        self.ax_grid.set_yticks([])
        self.ax_grid.set_title("Infection Spread", color="white")

        # ================= GRAPH =================
        self.ax_plot = self.fig.add_axes([0.65, 0.60, 0.30, 0.25])
        self.ax_plot.set_facecolor("#1a1a1a")
        self.line, = self.ax_plot.plot([], [], color="#00ff88", linewidth=2)
        self.ax_plot.set_title("Weed Growth", color="white")
        self.ax_plot.tick_params(colors='white')
        for spine in self.ax_plot.spines.values():
            spine.set_color("white")

        # ================= SPIRAL =================
        self.ax_spiral = self.fig.add_axes([0.65, 0.27, 0.30, 0.25])
        self.ax_spiral.set_facecolor("#1a1a1a")
        self.spiral_line, = self.ax_spiral.plot([], [], color="#ff00ff")
        self.ax_spiral.set_xticks([])
        self.ax_spiral.set_yticks([])
        self.ax_spiral.set_title("Fun Random Archimedes Spiral! :)", color="white")
        self.ax_spiral.set_aspect("equal")

        # ================= TEXT =================
        self.ax_text = self.fig.add_axes([0.65, 0.20, 0.30, 0.08])
        self.ax_text.axis("off")
        self.text_display = self.ax_text.text(
            0, 0.5, "", fontsize=12, color="white"
        )

        # ================= BUTTONS =================
        button_y = 0.05
        button_h = 0.045
        button_w = 0.06
        gap = 0.02
        start = 0.05

        self.btn_back = Button(
            plt.axes([start, button_y, button_w, button_h]),
            "<",
            color="#000000",
            hovercolor="#333333"
        )

        self.btn_pause = Button(
            plt.axes([start+button_w+gap, button_y, 0.085, button_h]),
            "Pause",
            color="#000000",
            hovercolor="#333333"
        )

        self.btn_forward = Button(
            plt.axes([start+button_w+gap+0.085+gap, button_y, button_w, button_h]),
            ">",
            color="#000000",
            hovercolor="#333333"
        )

        self.btn_reset = Button(
            plt.axes([start+button_w+gap+0.085+gap+button_w+gap, button_y, 0.085, button_h]),
            "Reset",
            color="#000000",
            hovercolor="#333333"
        )

        for btn in [self.btn_back, self.btn_pause, self.btn_forward, self.btn_reset]:
            btn.label.set_color("white")

        # ================= SPEED SLIDER =================
        self.slider = Slider(
            plt.axes([0.45, button_y, 0.35, button_h]),
            "Speed",
            1,
            20,
            valinit=5
        )

        self.slider.label.set_color("white")
        self.slider.valtext.set_color("white")
        self.slider.ax.set_facecolor("#000000")

        # ================= CHECKBOX =================
        self.check = CheckButtons(
            plt.axes([0.86, 0.05, 0.15, 0.12]),
            ["Show New", "Show Overlap", "Show Spiral"],
            [False, False, True]
        )

        # ================= EVENTS =================
        self.btn_pause.on_clicked(self.toggle)
        self.btn_back.on_clicked(lambda e: self.skip(-1))
        self.btn_forward.on_clicked(lambda e: self.skip(1))
        self.btn_reset.on_clicked(self.reset)
        self.slider.on_changed(self.change_speed)
        self.check.on_clicked(self.toggle_options)

        self.ani = FuncAnimation(self.fig, self.update, interval=30)
        plt.show()

    # ================= CONTROLS =================
    def toggle(self, event=None):
        self.running = not self.running
        self.btn_pause.label.set_text("Play" if not self.running else "Pause")

    def skip(self, amount):
        self.running = False
        self.index = max(0, min(len(grids)-1, self.index + amount))
        self.draw_frame()

    def reset(self, event=None):
        self.running = False
        self.index = 0
        self.theta = 0
        self.draw_frame()

    def change_speed(self, val):
        self.speed = int(val)

    def toggle_options(self, label):
        status = self.check.get_status()
        self.show_new = status[0]
        self.show_overlap = status[1]
        self.show_spiral = status[2]
        self.ax_spiral.set_visible(self.show_spiral)

    # ================= DRAW =================
    def draw_frame(self):
        base = grids[self.index].copy()

        if self.show_new:
            base[new_masks[self.index] == 1] = 2
        if self.show_overlap:
            base[overlap_masks[self.index] == 1] = 3

        self.im.set_array(base)
        self.ax_grid.set_title(f"Day {self.index}", color="white")

        self.line.set_data(range(self.index+1), weed_counts[:self.index+1])
        self.ax_plot.set_xlim(0, max(10, self.index+1))
        self.ax_plot.set_ylim(0, max(weed_counts[:self.index+1]) * 1.1)

        first, second = compute_diffs(weed_counts, self.index)
        self.text_display.set_text(
            f"Weeds: {weed_counts[self.index]}   "
            f"First: {first}   "
            f"Second: {second}"
        )

    # ================= UPDATE LOOP =================
    def update(self, frame):
        if self.running:
            self.frame_counter += 1
            if self.frame_counter >= self.speed:
                self.frame_counter = 0
                if self.index < len(grids):
                    self.draw_frame()
                    self.index += 1

        if self.show_spiral:
            self.theta += 0.1 * (21 - self.speed)
            t = np.linspace(0, self.theta, 500)
            r = 0.1 * t
            x = r*np.cos(t)
            y = r*np.sin(t)

            self.spiral_line.set_data(x, y)
            self.ax_spiral.set_xlim(-10, 10)
            self.ax_spiral.set_ylim(-10, 10)

InfectionGUI()