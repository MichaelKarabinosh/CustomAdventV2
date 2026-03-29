import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from pathlib import Path

INPUT_PATH = Path(__file__).resolve().parent.parent / "InputFile"

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
def read_input_lines():
    with INPUT_PATH.open("r") as f:
        return [line.strip() for line in f if line.strip()]


def build_simulation(input_lines):
    info = input_lines[0].split("|")
    gridx, gridy = map(int, info[0].strip().split("x"))
    days = int(info[3].strip())

    grid = create_grid(gridx, gridy)
    weeds = []

    for line in input_lines:
        info = line.split("|")
        init_x, init_y = map(int, info[1].strip().split(","))
        rel_list = create_infection(info[2].strip())
        weeds.append((init_y, init_x, rel_list))
        grid[init_y, init_x] = 1

    from collections import defaultdict

    initial_pattern_groups = defaultdict(list)
    for y, x, rel_list in weeds:
        pattern_key = tuple(sorted(rel_list))
        initial_pattern_groups[pattern_key].append((y, x))

    grids, weed_counts, new_masks, overlap_masks, growth_overlap_masks, pattern_history = simulate(grid, weeds, days)
    pattern_colors = generate_pattern_colors(initial_pattern_groups)
    growth_overlap_counts = [int(np.sum(mask)) for mask in growth_overlap_masks]

    return {
        "input_lines": input_lines.copy(),
        "grid_shape": grid.shape,
        "days": days,
        "grids": grids,
        "weed_counts": weed_counts,
        "growth_overlap_counts": growth_overlap_counts,
        "pattern_history": pattern_history,
        "pattern_colors": pattern_colors,
    }


INITIAL_INPUT_LINES = read_input_lines()
DEFAULT_RENDER_SETTINGS = {
    "trail_decay": 0.80,
    "trail_gain": 1.00,
    "bloom_strength": 1.00,
    "core_brightness": 1.00,
}

# ===============================
# GUI
# ===============================
def build_rgba_frame(grid, pattern_groups, pattern_colors, trail, render_settings):
    h, w = grid.shape
    img = np.zeros((h, w, 4), dtype=float)
    img[:, :, :3] = [0.01, 0.01, 0.03]
    img[:, :, 3] = 1.0

    trail_decay = render_settings["trail_decay"]
    trail_gain = render_settings["trail_gain"]
    bloom_strength = render_settings["bloom_strength"]
    core_brightness = render_settings["core_brightness"]

    trail *= trail_decay

    yy, xx = np.indices((h, w))
    screen_pattern = (
        0.55
        + 0.25 * np.sin((xx + yy) * 0.9)
        + 0.20 * np.sin((xx - yy) * 1.15)
    )
    screen_pattern = np.clip(screen_pattern, 0.45, 1.0)[..., None]

    for pattern_key, positions in pattern_groups.items():
        color = np.array(pattern_colors.get(pattern_key, [0.3, 0.8, 0.3]), dtype=float)
        color = np.clip(color * 1.1 + 0.08, 0, 1)

        if not positions:
            continue

        pos_arr = np.array(positions, dtype=int)
        ys, xs = pos_arr.T
        center_y = np.mean(ys)
        center_x = np.mean(xs)
        spread_y = max(1.0, np.max(np.abs(ys - center_y)))
        spread_x = max(1.0, np.max(np.abs(xs - center_x)))

        norm_y = (ys - center_y) / spread_y
        norm_x = (xs - center_x) / spread_x
        radial = np.sqrt(norm_x * norm_x + norm_y * norm_y)
        falloff = np.clip(1.12 - radial, 0, 1)
        falloff = 0.16 + 0.84 * (falloff ** 1.55)

        local_pattern = screen_pattern[ys, xs, 0]
        fill_strength = (0.20 + 0.62 * falloff) * (0.84 + 0.18 * local_pattern)
        img[ys, xs, :3] = np.maximum(
            img[ys, xs, :3],
            np.clip(color * fill_strength[:, None], 0, 1)
        )

        hot_strength = np.clip(falloff ** 2.8, 0, 1)
        trail[ys, xs, :3] += color * trail_gain * (0.05 + 0.16 * hot_strength)[:, None]

        core_index = np.argmin((ys - center_y) ** 2 + (xs - center_x) ** 2)
        cy, cx = ys[core_index], xs[core_index]
        img[cy, cx, :3] = np.maximum(
            img[cy, cx, :3],
            np.clip(color * (1.30 * core_brightness) + 0.20 * core_brightness, 0, 1)
        )
        trail[cy, cx, :3] += color * trail_gain * 0.24

    axial_glow = np.zeros_like(trail)
    axial_glow[1:, :, :] += trail[:-1, :, :] * 0.32
    axial_glow[:-1, :, :] += trail[1:, :, :] * 0.32
    axial_glow[:, 1:, :] += trail[:, :-1, :] * 0.32
    axial_glow[:, :-1, :] += trail[:, 1:, :] * 0.32

    diagonal_glow = np.zeros_like(trail)
    diagonal_glow[1:, 1:, :] += trail[:-1, :-1, :] * 0.22
    diagonal_glow[1:, :-1, :] += trail[:-1, 1:, :] * 0.22
    diagonal_glow[:-1, 1:, :] += trail[1:, :-1, :] * 0.22
    diagonal_glow[:-1, :-1, :] += trail[1:, 1:, :] * 0.22

    wide_glow = np.zeros_like(trail)
    wide_glow[2:, :, :] += trail[:-2, :, :] * 0.16
    wide_glow[:-2, :, :] += trail[2:, :, :] * 0.16
    wide_glow[:, 2:, :] += trail[:, :-2, :] * 0.16
    wide_glow[:, :-2, :] += trail[:, 2:, :] * 0.16

    far_glow = np.zeros_like(trail)
    far_glow[3:, :, :] += trail[:-3, :, :] * 0.07
    far_glow[:-3, :, :] += trail[3:, :, :] * 0.07
    far_glow[:, 3:, :] += trail[:, :-3, :] * 0.07
    far_glow[:, :-3, :] += trail[:, 3:, :] * 0.07

    bloom = trail * 0.62 + axial_glow + diagonal_glow + wide_glow + far_glow
    bloom *= bloom_strength
    bloom = bloom / (1.0 + 0.42 * bloom)
    textured_bloom = bloom * (0.82 + 0.22 * screen_pattern)

    soft_bloom = np.zeros_like(textured_bloom)
    soft_bloom[1:, :, :] += textured_bloom[:-1, :, :] * 0.10
    soft_bloom[:-1, :, :] += textured_bloom[1:, :, :] * 0.10
    soft_bloom[:, 1:, :] += textured_bloom[:, :-1, :] * 0.10
    soft_bloom[:, :-1, :] += textured_bloom[:, 1:, :] * 0.10

    combined = img[:, :, :3] + textured_bloom + soft_bloom
    combined = np.clip(combined, 0, 1.65)
    img[:, :, :3] = combined / (1.0 + 0.24 * combined)
    img[:, :, :3] = np.clip(img[:, :, :3], 0, 1)

    return img

class InfectionGUI:
    def __init__(self):
        self.original_input_lines = INITIAL_INPUT_LINES.copy()
        self.input_mtime = INPUT_PATH.stat().st_mtime
        self.reload_error = ""
        self.sim_data = build_simulation(self.original_input_lines)
        self.render_settings = DEFAULT_RENDER_SETTINGS.copy()
        self.index = 0
        self.running = False
        self.interval = 200
        self.trail = np.zeros((*self.sim_data["grid_shape"], 3))

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
            np.zeros((*self.sim_data["grid_shape"], 4)),
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
        self.ax_status = self.fig.add_axes([0.70, 0.30, 0.25, 0.08])
        self.ax_status.axis("off")
        self.status_text = self.ax_status.text(0, 0.8, "", fontsize=10)

        self.ax_art_title = self.fig.add_axes([0.70, 0.23, 0.25, 0.04])
        self.ax_art_title.axis("off")
        self.ax_art_title.text(0, 0.5, "Art Controls", fontsize=11, fontweight="bold")

        self.slider_trail_decay = Slider(
            plt.axes([0.73, 0.19, 0.19, 0.022]),
            "Decay", 0.60, 0.95, valinit=self.render_settings["trail_decay"]
        )
        self.slider_trail_gain = Slider(
            plt.axes([0.73, 0.16, 0.19, 0.022]),
            "Gain", 0.40, 2.00, valinit=self.render_settings["trail_gain"]
        )
        self.slider_bloom_strength = Slider(
            plt.axes([0.73, 0.13, 0.19, 0.022]),
            "Bloom", 0.40, 2.00, valinit=self.render_settings["bloom_strength"]
        )
        self.slider_core_brightness = Slider(
            plt.axes([0.73, 0.10, 0.19, 0.022]),
            "Core", 0.50, 2.00, valinit=self.render_settings["core_brightness"]
        )

        # ===============================
        # CONTROLS
        # ===============================
        button_y = 0.035
        button_h = 0.045

        self.btn_back5 = Button(plt.axes([0.06, button_y, 0.055, button_h]), "<<")
        self.btn_back1 = Button(plt.axes([0.125, button_y, 0.055, button_h]), "<")
        self.btn_pause = Button(plt.axes([0.19, button_y, 0.085, button_h]), "Play")
        self.btn_fwd1  = Button(plt.axes([0.285, button_y, 0.055, button_h]), ">")
        self.btn_fwd5  = Button(plt.axes([0.35, button_y, 0.055, button_h]), ">>")
        self.btn_day0 = Button(plt.axes([0.435, button_y, 0.075, button_h]), "Day 0")
        self.btn_reload = Button(plt.axes([0.52, button_y, 0.085, button_h]), "Reload")
        self.btn_restore = Button(plt.axes([0.615, button_y, 0.09, button_h]), "Original")

        self.slider = Slider(
            plt.axes([0.79, button_y, 0.17, button_h]),
            "Speed", 10, 1000, valinit=200
        )
        self.slider.label.set_fontsize(11)

        # ===============================
        # BINDINGS
        # ===============================
        self.btn_pause.on_clicked(self.toggle)
        self.btn_back1.on_clicked(lambda e: self.skip(-1))
        self.btn_fwd1.on_clicked(lambda e: self.skip(1))
        self.btn_back5.on_clicked(lambda e: self.skip(-5))
        self.btn_fwd5.on_clicked(lambda e: self.skip(5))
        self.btn_day0.on_clicked(self.reset_day)
        self.btn_reload.on_clicked(self.reload_input)
        self.btn_restore.on_clicked(self.restore_original)

        self.slider.on_changed(self.change_speed)
        self.slider_trail_decay.on_changed(lambda val: self.change_render_setting("trail_decay", val))
        self.slider_trail_gain.on_changed(lambda val: self.change_render_setting("trail_gain", val))
        self.slider_bloom_strength.on_changed(lambda val: self.change_render_setting("bloom_strength", val))
        self.slider_core_brightness.on_changed(lambda val: self.change_render_setting("core_brightness", val))

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
        if self.running:
            self.ani.event_source.start()
        else:
            self.ani.event_source.stop()
        self.btn_pause.label.set_text("Play" if not self.running else "Pause")
        self.fig.canvas.draw()

    def skip(self, amount):
        self.running = False
        self.ani.event_source.stop()
        self.index = max(0, min(len(self.sim_data["grids"]) - 1, self.index + amount))
        self.btn_pause.label.set_text("Play")
        self.draw_frame()

    def reset_day(self, event):
        self.running = False
        self.ani.event_source.stop()
        self.index = 0
        self.btn_pause.label.set_text("Play")
        self.draw_frame()

    def restore_original(self, event):
        was_running = self.running
        self.apply_simulation(build_simulation(self.original_input_lines), restart=True)
        self.reload_error = "Restored original setup"
        self.running = was_running
        if self.running:
            self.ani.event_source.start()
        else:
            self.ani.event_source.stop()
        self.btn_pause.label.set_text("Play" if not self.running else "Pause")
        self.draw_frame()

    def change_speed(self, val):
        self.interval = int(val)
        self.ani._interval = self.interval
        self.ani.event_source.stop()
        self.ani.event_source.interval = self.interval
        if self.running:
            self.ani.event_source.start()
        self.fig.canvas.draw()

    def change_render_setting(self, key, val):
        self.render_settings[key] = float(val)
        self.draw_frame()

    def apply_simulation(self, sim_data, restart=False):
        current_index = 0 if restart else min(self.index, len(sim_data["grids"]) - 1)
        self.sim_data = sim_data
        self.trail = np.zeros((*sim_data["grid_shape"], 3))
        self.index = current_index
        self.im.set_data(np.zeros((*sim_data["grid_shape"], 4)))
        self.ax_grid.set_xlim(-0.5, sim_data["grid_shape"][1] - 0.5)
        self.ax_grid.set_ylim(sim_data["grid_shape"][0] - 0.5, -0.5)
        self.ax_plot.cla()
        self.line, = self.ax_plot.plot([], [])
        self.ax_plot.set_title("Weed Growth")

    def reload_input(self, event=None):
        try:
            input_lines = read_input_lines()
        except Exception as exc:
            self.reload_error = f"Reload failed: {exc}"
            self.draw_frame()
            return

        if input_lines == self.sim_data["input_lines"]:
            self.reload_error = "InputFile unchanged"
            self.draw_frame()
            return

        try:
            sim_data = build_simulation(input_lines)
        except Exception as exc:
            self.reload_error = f"Reload failed: {exc}"
            self.draw_frame()
            return

        self.input_mtime = INPUT_PATH.stat().st_mtime
        was_running = self.running
        self.apply_simulation(sim_data)
        self.running = was_running
        if self.running:
            self.ani.event_source.start()
        else:
            self.ani.event_source.stop()
        self.reload_error = "Reloaded InputFile"
        self.btn_pause.label.set_text("Play" if not self.running else "Pause")
        self.draw_frame()

    def draw_frame(self):
        img = build_rgba_frame(
            self.sim_data["grids"][self.index],
            self.sim_data["pattern_history"][self.index],
            self.sim_data["pattern_colors"],
            self.trail,
            self.render_settings
        )

        self.im.set_data(img)
        self.ax_grid.set_title(f"Day {self.index}")

        self.line.set_data(range(self.index + 1),
                           self.sim_data["weed_counts"][:self.index + 1])

        self.ax_plot.set_xlim(0, max(10, self.index + 1))
        self.ax_plot.set_ylim(0, max(self.sim_data["weed_counts"][:self.index + 1]) * 1.1)

        first, second = compute_diffs(self.sim_data["weed_counts"], self.index)

        go_count = self.sim_data["growth_overlap_counts"][self.index]
        go_first, go_second = compute_diffs(self.sim_data["growth_overlap_counts"], self.index)

        left_text = (
            f"Weeds: {self.sim_data['weed_counts'][self.index]}\n"
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
        self.status_text.set_text(self.reload_error)

        self.fig.canvas.draw()

    def update(self, frame):
        if not self.running or self.index >= len(self.sim_data["grids"]):
            return
        self.draw_frame()
        self.index += 1


InfectionGUI()
