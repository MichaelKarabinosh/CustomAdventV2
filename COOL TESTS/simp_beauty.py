import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider, CheckButtons
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# ===============================
# INPUT
# ===============================
with open("../InputFile", "r") as f:
    INPUT_LINES = [line.strip() for line in f if line.strip()]

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

def generate_pattern_colors(pattern_groups):
    colors = {}
    for i, key in enumerate(pattern_groups.keys()):
        hue = i / max(1, len(pattern_groups))
        r = 0.5 + 0.5 * np.sin(2*np.pi*hue)
        g = 0.5 + 0.5 * np.sin(2*np.pi*(hue + 0.33))
        b = 0.5 + 0.5 * np.sin(2*np.pi*(hue + 0.66))
        colors[key] = [r, g, b]
    return colors


def simulate(grid, weeds, days):
    grids = []
    weed_counts = []

    new_masks = []
    overlap_masks = []
    growth_overlap_masks = []
    pattern_history = []

    grids.append(grid.copy())
    weed_counts.append(int(np.sum(grid)))
    new_masks.append(np.zeros_like(grid, dtype=bool))
    overlap_masks.append(np.zeros_like(grid, dtype=bool))
    growth_overlap_masks.append(np.zeros_like(grid, dtype=bool))

    from collections import defaultdict
    pattern_groups = defaultdict(list)

    for y, x, rel_list in weeds:
        pattern_key = tuple(sorted(rel_list))
        pattern_groups[pattern_key].append((y, x))

    pattern_history.append({k: v.copy() for k, v in pattern_groups.items()})

    for _ in range(days):
        new_grid = grid.copy()
        any_growth = False
        new_pattern_groups = defaultdict(list)

        for pattern_key, positions in pattern_groups.items():
            rel_list = list(pattern_key)

            mask = np.zeros_like(grid, dtype=bool)
            pos_arr = np.array(positions, dtype=int)
            ys, xs = pos_arr.T
            mask[ys, xs] = True

            growth_mask = np.zeros_like(grid, dtype=bool)

            for dx, dy in rel_list:
                shifted = np.roll(mask, shift=(-dy, dx), axis=(0, 1))

                if dy > 0:
                    shifted[-dy:, :] = False
                elif dy < 0:
                    shifted[:(-dy), :] = False

                if dx > 0:
                    shifted[:, :dx] = False
                elif dx < 0:
                    shifted[:, dx:] = False

                growth_mask |= shifted

            growth_mask &= (grid == 0)

            if np.any(growth_mask):
                any_growth = True
                ys, xs = np.where(growth_mask)
                new_pattern_groups[pattern_key].extend(zip(ys.tolist(), xs.tolist()))
                new_grid[growth_mask] = 1

            new_pattern_groups[pattern_key].extend(positions)

        if not any_growth:
            break

        grid = new_grid
        pattern_groups = new_pattern_groups

        grids.append(grid.copy())
        weed_counts.append(int(np.sum(grid)))
        new_masks.append(np.zeros_like(grid, dtype=bool))
        overlap_masks.append(np.zeros_like(grid, dtype=bool))
        growth_overlap_masks.append(np.zeros_like(grid, dtype=bool))
        pattern_history.append({k: v.copy() for k, v in pattern_groups.items()})

    return grids, weed_counts, new_masks, overlap_masks, growth_overlap_masks, pattern_history


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
# Use first line for grid size and days
info = INPUT_LINES[0].split("|")
gridx, gridy = map(int, info[0].strip().split("x"))
days = int(info[3].strip())

grid = create_grid(gridx, gridy)

# Each weed = (y, x, rel_list)
weeds = []

for line in INPUT_LINES:
    info = line.split("|")
    init_x, init_y = map(int, info[1].strip().split(","))
    rel_list = create_infection(info[2].strip())

    weeds.append((init_y, init_x, rel_list))
    grid[init_y, init_x] = 1

# GUI still expects one center
center_pos = weeds[0][:2]

from collections import defaultdict

initial_pattern_groups = defaultdict(list)
for y, x, rel_list in weeds:
    pattern_key = tuple(sorted(rel_list))
    initial_pattern_groups[pattern_key].append((y, x))

grids, weed_counts, new_masks, overlap_masks, growth_overlap_masks, pattern_history = simulate(grid, weeds, days)

pattern_colors = generate_pattern_colors(initial_pattern_groups)

growth_overlap_counts = [
    int(np.sum(mask)) for mask in growth_overlap_masks
]

# ===============================
# GUI
# ===============================
def build_rgba_frame(grid, pattern_groups, pattern_colors, trail):

    h, w = grid.shape
    img = np.zeros((h, w, 4), dtype=float)

    # 🌑 background
    img[:, :, :3] = [0.01, 0.01, 0.03]
    img[:, :, 3] = 1.0

    # ✨ trail decay (balanced)
    trail *= 0.75

    for pattern_key, positions in pattern_groups.items():
        color = np.array(pattern_colors.get(pattern_key, [0.3, 0.8, 0.3]))

        if not positions:
            continue

        pos_arr = np.array(positions, dtype=int)
        ys, xs = pos_arr.T

        # 🌟 MAIN DOTS (keep them bright)
        img[ys, xs, :3] = color
        img[ys, xs, 3] = 0.9

        # ✨ TRAIL (soft accumulation, not too strong)
        trail[ys, xs, :3] += color * 0.18

    # 💡 SOFT GLOW (vectorized, cheap)
    glow = np.zeros_like(trail)
    glow[1:, :, :] += trail[:-1, :, :] * 0.25
    glow[:-1, :, :] += trail[1:, :, :] * 0.25
    glow[:, 1:, :] += trail[:, :-1, :] * 0.25
    glow[:, :-1, :] += trail[:, 1:, :] * 0.25

    # 🎨 combine everything
    combined = img[:, :, :3] + trail[:, :, :3] + glow[:, :, :3]

    # ⚖️ soft cap (NOT full normalization)
    combined = np.clip(combined, 0, 1.2)
    img[:, :, :3] = combined / (1.0 + 0.2 * combined)

    return img

class InfectionGUI:
    def __init__(self):
        self.index = 0
        self.running = False
        self.interval = 200
        self.show_new = False
        self.show_overlap = False
        self.show_growth_overlap = False
        self.trail = np.zeros((grids[0].shape[0], grids[0].shape[1], 4))

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
            "black",  # 0 empty
            "#ff4500",  # 1 old
            "#ffff00",  # 2 new
            "#00ffff",  # 3 overlap
            "#ff00ff",  # 4 growth overlap
            "#ffffff"  # 5 center
        ])

        self.im = self.ax_grid.imshow(
            np.zeros((grids[0].shape[0], grids[0].shape[1], 4)),
            interpolation='nearest'
        )
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

        self.ani = FuncAnimation(
            self.fig,
            self.update,
            interval=self.interval,
            cache_frame_data=False
        )
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
        self.ani = FuncAnimation(
            self.fig,
            self.update,
            interval=self.interval,
            cache_frame_data=False
        )

    def toggle_options(self, label):
        status = self.check.get_status()
        self.show_new = status[0]
        self.show_overlap = status[1]
        self.show_growth_overlap = status[2]
        self.draw_frame()

    def draw_frame(self):
         # reset only at start

        img = build_rgba_frame(
            grids[self.index],
            pattern_history[self.index],
            pattern_colors,
            self.trail
        )

        self.im.set_data(img)
        self.ax_grid.set_title(f"Day {self.index}")

        self.line.set_data(range(self.index + 1),
                           weed_counts[:self.index + 1])

        self.ax_plot.set_xlim(0, max(10, self.index + 1))
        self.ax_plot.set_ylim(0, max(weed_counts[:self.index + 1]) * 1.1)

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