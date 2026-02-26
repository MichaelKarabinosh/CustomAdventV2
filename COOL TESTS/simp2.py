import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider, CheckButtons
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# ===============================
# INPUT
# ===============================
INPUT_LINE = "50x50 | 25,25 | 11000,00000,00W00,10000,00000 | 90"

# ===============================
# SIMULATION
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
    growth_overlap_masks = []

    for _ in range(days):
        growth_counter = np.zeros_like(grid)
        new_mask = np.zeros_like(grid)
        overlap_mask = np.zeros_like(grid)
        growth_overlap_mask = np.zeros_like(grid)

        weed_positions = np.argwhere(grid == 1)

        # Count growth attempts
        for y, x in weed_positions:
            for dx, dy in rel_list:
                ny = y - dy
                nx = x + dx
                if 0 <= ny < grid.shape[0] and 0 <= nx < grid.shape[1]:
                    growth_counter[ny, nx] += 1

        new_grid = grid.copy()

        # Apply growth
        for y in range(grid.shape[0]):
            for x in range(grid.shape[1]):
                if growth_counter[y, x] > 0:
                    if grid[y, x] == 1:
                        overlap_mask[y, x] = 1
                    else:
                        new_grid[y, x] = 1
                        if growth_counter[y, x] > 1:
                            growth_overlap_mask[y, x] = 1
                        else:
                            new_mask[y, x] = 1

        if np.array_equal(new_grid, grid):
            break

        grid = new_grid
        grids.append(grid.copy())
        weed_counts.append(int(np.sum(grid)))
        new_masks.append(new_mask.copy())
        overlap_masks.append(overlap_mask.copy())
        growth_overlap_masks.append(growth_overlap_mask.copy())

    return grids, weed_counts, new_masks, overlap_masks, growth_overlap_masks


def compute_diffs(data, index):
    if index < 1:
        return 0, 0
    first = data[index] - data[index-1]
    if index < 2:
        return first, 0
    second = data[index] - 2*data[index-1] + data[index-2]
    return first, second


# ===============================
# BUILD SIMULATION
# ===============================
info = INPUT_LINE.split("|")
gridx, gridy = map(int, info[0].strip().split("x"))
init_x, init_y = map(int, info[1].strip().split(","))
rel_list = create_infection(info[2].strip())
days = int(info[3].strip())

grid = create_grid(gridx, gridy)
grid[init_y, init_x] = 1

grids, weed_counts, new_masks, overlap_masks, growth_overlap_masks = simulate(grid, rel_list, days)
growth_overlap_counts = [
    int(np.sum(mask)) for mask in growth_overlap_masks
]

# ===============================
# GUI
# ===============================
class InfectionGUI:
    def __init__(self):
        self.index = 0
        self.running = False
        self.interval = 200
        self.show_new = False
        self.show_overlap = False
        self.show_growth_overlap = False

        self.fig = plt.figure(figsize=(16,9))
        # Auto fullscreen (works for most backends)
        manager = plt.get_current_fig_manager()
        try:
            manager.window.state('zoomed')  # Windows
        except:
            try:
                manager.full_screen_toggle()  # Mac/Linux
            except:
                pass

        # ===============================
        # MAIN GRID
        # ===============================
        self.ax_grid = self.fig.add_axes([0.05, 0.15, 0.60, 0.80])

        self.cmap = ListedColormap([
            "black",       # 0 empty
            "#ff4500",     # 1 old
            "#ffff00",     # 2 new
            "#00ffff",     # 3 overlap
            "#ff00ff"      # 4 growth overlap
        ])

        self.im = self.ax_grid.imshow(grids[0], cmap=self.cmap, vmin=0, vmax=4)
        self.ax_grid.set_xticks([])
        self.ax_grid.set_yticks([])
        self.ax_grid.set_title("Day 0")

        legend_elements = [
            Patch(facecolor="black", label="Empty"),
            Patch(facecolor="#ff4500", label="Old"),
            Patch(facecolor="#ffff00", label="New"),
            Patch(facecolor="#00ffff", label="Overlap"),
            Patch(facecolor="#ff00ff", label="Growth Overlap")
        ]
        self.ax_grid.legend(handles=legend_elements, loc="upper right")

        # ===============================
        # GRAPH
        # ===============================
        self.ax_plot = self.fig.add_axes([0.70, 0.62, 0.25, 0.26])
        self.line, = self.ax_plot.plot([], [])
        self.ax_plot.set_title("Weed Growth")

        # ===============================
        # TEXT
        # ===============================
        # Left stats
        self.ax_text = self.fig.add_axes([0.70, 0.40, 0.12, 0.14])
        self.ax_text.axis("off")
        self.text_display = self.ax_text.text(0, 0.5, "", fontsize=12)

        # Right stats
        self.ax_text_right = self.fig.add_axes([0.83, 0.40, 0.12, 0.14])
        self.ax_text_right.axis("off")
        self.ax_text_right_text = self.ax_text_right.text(0, 0.5, "", fontsize=12)

        # ===============================
        # CHECKBOX
        # ===============================
        self.ax_check = self.fig.add_axes([0.70, 0.30, 0.25, 0.12])
        self.check = CheckButtons(
            self.ax_check,
            ["Show New", "Show Overlap", "Show Growth Overlap"],
            [False, False, False]
        )

        # ===============================
        # CONTROLS
        # ===============================
        button_y = 0.03
        button_h = 0.05

        self.btn_back5 = Button(plt.axes([0.10, button_y, 0.05, button_h]), "<<")
        self.btn_back1 = Button(plt.axes([0.16, button_y, 0.05, button_h]), "<")
        self.btn_pause = Button(plt.axes([0.22, button_y, 0.08, button_h]), "Play")
        self.btn_fwd1  = Button(plt.axes([0.31, button_y, 0.05, button_h]), ">")
        self.btn_fwd5  = Button(plt.axes([0.37, button_y, 0.05, button_h]), ">>")
        self.btn_reset = Button(plt.axes([0.44, button_y, 0.08, button_h]), "Reset")

        self.slider = Slider(
            plt.axes([0.62, button_y, 0.30, button_h]),
            "Speed (ms)", 10, 1000, valinit=200
        )

        # ===============================
        # BINDINGS
        # ===============================
        self.btn_pause.on_clicked(self.toggle)
        self.btn_back1.on_clicked(lambda e: self.skip(-1))
        self.btn_fwd1.on_clicked(lambda e: self.skip(1))
        self.btn_back5.on_clicked(lambda e: self.skip(-5))
        self.btn_fwd5.on_clicked(lambda e: self.skip(5))
        self.btn_reset.on_clicked(self.reset)

        self.slider.on_changed(self.change_speed)
        self.check.on_clicked(self.toggle_options)

        self.ani = FuncAnimation(self.fig, self.update, interval=self.interval)
        self.draw_frame()
        plt.show()

    def toggle(self, event):
        self.running = not self.running
        self.btn_pause.label.set_text("Play" if not self.running else "Pause")

    def skip(self, amount):
        self.running = False
        self.index = max(0, min(len(grids)-1, self.index + amount))
        self.draw_frame()

    def reset(self, event):
        self.running = False
        self.index = 0
        self.draw_frame()

    def change_speed(self, val):
        self.interval = int(val)
        self.ani.event_source.stop()
        self.ani = FuncAnimation(self.fig, self.update, interval=self.interval)

    def toggle_options(self, label):
        status = self.check.get_status()
        self.show_new = status[0]
        self.show_overlap = status[1]
        self.show_growth_overlap = status[2]
        self.draw_frame()

    def draw_frame(self):
        base = grids[self.index].copy()

        if self.show_new and self.index > 0:
            prev = grids[self.index - 1]
            curr = grids[self.index]

            new_cells = (curr == 1) & (prev == 0)
            base[new_cells] = 2
        if self.show_overlap:
            base[overlap_masks[self.index] == 1] = 3
        if self.show_growth_overlap:
            base[growth_overlap_masks[self.index] == 1] = 4

        self.im.set_array(base)
        self.ax_grid.set_title(f"Day {self.index}")

        self.line.set_data(range(self.index+1),
                           weed_counts[:self.index+1])

        self.ax_plot.set_xlim(0, max(10, self.index+1))
        self.ax_plot.set_ylim(0, max(weed_counts[:self.index+1]) * 1.1)

        first, second = compute_diffs(weed_counts, self.index)

        go_count = growth_overlap_counts[self.index]
        go_first, go_second = compute_diffs(growth_overlap_counts, self.index)

        left_text = (
            f"Weeds: {weed_counts[self.index]}\n"
            f"First Diff: {first}\n"
            f"Second Diff: {second}"
        )

        right_text = (
            f"Growth Overlaps: {go_count}\n"
            f"First Diff: {go_first}\n"
            f"Second Diff: {go_second}"
        )

        self.text_display.set_text(left_text)
        self.ax_text_right_text.set_text(right_text)

        self.fig.canvas.draw_idle()

    def update(self, frame):
        if not self.running or self.index >= len(grids):
            return
        self.draw_frame()
        self.index += 1


InfectionGUI()