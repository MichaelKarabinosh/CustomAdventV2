import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.widgets import Button, CheckButtons, Slider


INPUT_PATH = Path(__file__).resolve().parents[1] / "InputFile"


def parse_line(line):
    info = [part.strip() for part in line.split("|")]
    if len(info) != 4:
        raise ValueError(f"Invalid input line: {line}")

    gridx, gridy = map(int, info[0].split("x"))
    init_x, init_y = map(int, info[1].split(","))
    days = int(info[3])
    offsets = create_infection(info[2])
    return gridx, gridy, (init_y, init_x), offsets, days


def load_simulation_config(path):
    lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if not lines:
        raise ValueError(f"Input file is empty: {path}")

    gridx, gridy, center, offsets, days = parse_line(lines[0])
    centers = [center]
    patterns = [offsets]

    for line in lines[1:]:
        _, _, center, offsets, _ = parse_line(line)
        centers.append(center)
        patterns.append(offsets)

    return gridx, gridy, days, centers, patterns


def create_infection(pattern):
    lines = pattern.split(",")
    center_x = center_y = None

    for row_index, row in enumerate(lines):
        for col_index, value in enumerate(row):
            if value == "W":
                center_x = col_index
                center_y = row_index
                break
        if center_x is not None:
            break

    if center_x is None or center_y is None:
        raise ValueError(f"Pattern is missing W center: {pattern}")

    offsets = []
    for row_index, row in enumerate(lines):
        for col_index, value in enumerate(row):
            if value == "1":
                offsets.append((row_index - center_y, col_index - center_x))

    return np.array(offsets, dtype=np.int16)


def apply_shift(mask, row_shift, col_shift, target):
    height, width = mask.shape

    if row_shift >= 0:
        src_row = slice(0, height - row_shift)
        dst_row = slice(row_shift, height)
    else:
        src_row = slice(-row_shift, height)
        dst_row = slice(0, height + row_shift)

    if col_shift >= 0:
        src_col = slice(0, width - col_shift)
        dst_col = slice(col_shift, width)
    else:
        src_col = slice(-col_shift, width)
        dst_col = slice(0, width + col_shift)

    source_view = mask[src_row, src_col]
    if source_view.size == 0:
        return

    target[dst_row, dst_col] += source_view


def apply_shift_or(mask, row_shift, col_shift, target):
    height, width = mask.shape

    if row_shift >= 0:
        src_row = slice(0, height - row_shift)
        dst_row = slice(row_shift, height)
    else:
        src_row = slice(-row_shift, height)
        dst_row = slice(0, height + row_shift)

    if col_shift >= 0:
        src_col = slice(0, width - col_shift)
        dst_col = slice(col_shift, width)
    else:
        src_col = slice(-col_shift, width)
        dst_col = slice(0, width + col_shift)

    source_view = mask[src_row, src_col]
    if source_view.size == 0:
        return

    np.logical_or(target[dst_row, dst_col], source_view, out=target[dst_row, dst_col])


def simulate(shape, centers, patterns, days):
    height, width = shape
    family_layers = []
    center_positions = []

    for center_y, center_x in centers:
        if not (0 <= center_y < height and 0 <= center_x < width):
            raise ValueError(f"Starting weed {(center_x, center_y)} is outside the grid")

        layer = np.zeros((height, width), dtype=bool)
        layer[center_y, center_x] = True
        family_layers.append(layer)
        center_positions.append((center_y, center_x))

    grid = np.logical_or.reduce(family_layers) if family_layers else np.zeros((height, width), dtype=bool)

    grids = [grid.copy()]
    weed_counts = [int(grid.sum())]
    new_masks = [np.zeros((height, width), dtype=bool)]
    overlap_masks = [np.zeros((height, width), dtype=bool)]
    growth_overlap_masks = [np.zeros((height, width), dtype=bool)]

    for _ in range(days):
        attempts = np.zeros((height, width), dtype=np.uint16)
        next_layers = []
        changed = False

        for layer, offsets in zip(family_layers, patterns):
            family_reach = np.zeros((height, width), dtype=bool)
            for row_shift, col_shift in offsets:
                apply_shift(layer, int(row_shift), int(col_shift), attempts)
                apply_shift_or(layer, int(row_shift), int(col_shift), family_reach)

            next_layer = np.logical_or(layer, family_reach)
            if not changed and np.any(next_layer != layer):
                changed = True
            next_layers.append(next_layer)

        attempted = attempts > 0
        growth_overlap = (~grid) & (attempts > 1)
        overlap = grid & attempted
        new_cells = (~grid) & attempted

        family_layers = next_layers
        next_grid = np.logical_or.reduce(family_layers) if family_layers else np.zeros((height, width), dtype=bool)

        grids.append(next_grid.copy())
        weed_counts.append(int(next_grid.sum()))
        new_masks.append(new_cells)
        overlap_masks.append(overlap)
        growth_overlap_masks.append(growth_overlap)

        if not changed:
            break

        grid = next_grid

    return grids, weed_counts, new_masks, overlap_masks, growth_overlap_masks, center_positions


class InfectionGUI:
    def __init__(self, grids, weed_counts, new_masks, overlap_masks, growth_overlap_masks, center_positions):
        self.grids = grids
        self.weed_counts = weed_counts
        self.new_masks = new_masks
        self.overlap_masks = overlap_masks
        self.growth_overlap_masks = growth_overlap_masks
        self.center_positions = center_positions
        self.growth_overlap_counts = [int(mask.sum()) for mask in growth_overlap_masks]

        self.index = 0
        self.running = False
        self.interval = 200
        self.show_new = False
        self.show_overlap = False
        self.show_growth_overlap = False

        self.fig = plt.figure(figsize=(16, 9))
        manager = plt.get_current_fig_manager()
        try:
            manager.window.state("zoomed")
        except Exception:
            try:
                manager.full_screen_toggle()
            except Exception:
                pass

        self.ax_grid = self.fig.add_axes([0.05, 0.15, 0.60, 0.80])
        self.cmap = ListedColormap([
            "black",
            "#ff4500",
            "#ffff00",
            "#00ffff",
            "#ff00ff",
            "#ffffff",
        ])

        self.im = self.ax_grid.imshow(self.grids[0], cmap=self.cmap, vmin=0, vmax=5)
        self.ax_grid.set_xticks([])
        self.ax_grid.set_yticks([])
        self.ax_grid.set_title("Day 0")

        legend_elements = [
            Patch(facecolor="black", label="Empty"),
            Patch(facecolor="#ff4500", label="Old"),
            Patch(facecolor="#ffff00", label="New"),
            Patch(facecolor="#00ffff", label="Overlap"),
            Patch(facecolor="#ff00ff", label="Growth Overlap"),
            Patch(facecolor="#ffffff", label="Start Weed"),
        ]
        self.ax_grid.legend(handles=legend_elements, loc="upper right")

        self.ax_plot = self.fig.add_axes([0.70, 0.62, 0.25, 0.26])
        (self.line,) = self.ax_plot.plot([], [])
        self.ax_plot.set_title("Weed Growth")

        self.ax_text = self.fig.add_axes([0.70, 0.40, 0.12, 0.14])
        self.ax_text.axis("off")
        self.text_display = self.ax_text.text(0, 0.5, "", fontsize=12)

        self.ax_text_right = self.fig.add_axes([0.83, 0.40, 0.12, 0.14])
        self.ax_text_right.axis("off")
        self.ax_text_right_text = self.ax_text_right.text(0, 0.5, "", fontsize=12)

        self.ax_check = self.fig.add_axes([0.70, 0.30, 0.25, 0.12])
        self.check = CheckButtons(
            self.ax_check,
            ["Show New", "Show Overlap", "Show Growth Overlap"],
            [False, False, False],
        )

        button_y = 0.03
        button_h = 0.05

        self.btn_back5 = Button(plt.axes([0.10, button_y, 0.05, button_h]), "<<")
        self.btn_back1 = Button(plt.axes([0.16, button_y, 0.05, button_h]), "<")
        self.btn_pause = Button(plt.axes([0.22, button_y, 0.08, button_h]), "Play")
        self.btn_fwd1 = Button(plt.axes([0.31, button_y, 0.05, button_h]), ">")
        self.btn_fwd5 = Button(plt.axes([0.37, button_y, 0.05, button_h]), ">>")
        self.btn_reset = Button(plt.axes([0.44, button_y, 0.08, button_h]), "Reset")

        self.slider = Slider(
            plt.axes([0.62, button_y, 0.30, button_h]),
            "Speed (ms)",
            10,
            1000,
            valinit=200,
        )

        self.btn_pause.on_clicked(self.toggle)
        self.btn_back1.on_clicked(lambda event: self.skip(-1))
        self.btn_fwd1.on_clicked(lambda event: self.skip(1))
        self.btn_back5.on_clicked(lambda event: self.skip(-5))
        self.btn_fwd5.on_clicked(lambda event: self.skip(5))
        self.btn_reset.on_clicked(self.reset)

        self.slider.on_changed(self.change_speed)
        self.check.on_clicked(self.toggle_options)

        self.ani = FuncAnimation(self.fig, self.update, interval=self.interval)
        self.draw_frame()
        plt.show()

    def toggle(self, _event):
        self.running = not self.running
        self.btn_pause.label.set_text("Play" if not self.running else "Pause")

    def skip(self, amount):
        self.running = False
        self.index = max(0, min(len(self.grids) - 1, self.index + amount))
        self.draw_frame()

    def reset(self, _event):
        self.running = False
        self.index = 0
        self.draw_frame()

    def change_speed(self, value):
        self.interval = int(value)
        self.ani.event_source.stop()
        self.ani = FuncAnimation(self.fig, self.update, interval=self.interval)

    def toggle_options(self, _label):
        status = self.check.get_status()
        self.show_new = status[0]
        self.show_overlap = status[1]
        self.show_growth_overlap = status[2]
        self.draw_frame()

    def draw_frame(self):
        base = np.zeros_like(self.grids[self.index], dtype=np.uint8)
        base[self.grids[self.index]] = 1

        if self.show_new:
            base[self.new_masks[self.index]] = 2

        if self.show_overlap:
            base[self.overlap_masks[self.index]] = 3

        if self.show_growth_overlap:
            base[self.growth_overlap_masks[self.index]] = 4

        for center_y, center_x in self.center_positions:
            if self.grids[self.index][center_y, center_x]:
                base[center_y, center_x] = 5

        self.im.set_array(base)
        self.ax_grid.set_title(f"Day {self.index}")

        self.line.set_data(range(self.index + 1), self.weed_counts[: self.index + 1])
        self.ax_plot.set_xlim(0, max(10, self.index + 1))
        self.ax_plot.set_ylim(0, max(self.weed_counts[: self.index + 1]) * 1.1)

        first, second = compute_diffs(self.weed_counts, self.index)
        growth_overlap_count = self.growth_overlap_counts[self.index]
        go_first, go_second = compute_diffs(self.growth_overlap_counts, self.index)

        self.text_display.set_text(
            f"Weeds: {self.weed_counts[self.index]}\n"
            f"First Diff: {first}\n"
            f"Second Diff: {second}"
        )
        self.ax_text_right_text.set_text(
            f"Growth Overlaps: {growth_overlap_count}\n"
            f"First Diff: {go_first}\n"
            f"Second Diff: {go_second}"
        )

        self.fig.canvas.draw_idle()

    def update(self, _frame):
        if not self.running:
            return
        if self.index < len(self.grids) - 1:
            self.index += 1
            self.draw_frame()


def compute_diffs(data, index):
    if index < 1:
        return 0, 0
    first = data[index] - data[index - 1]
    if index < 2:
        return first, 0
    second = data[index] - 2 * data[index - 1] + data[index - 2]
    return first, second


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-gui", action="store_true", help="Run the simulation without opening the GUI")
    args = parser.parse_args()

    gridx, gridy, days, centers, patterns = load_simulation_config(INPUT_PATH)
    grids, weed_counts, new_masks, overlap_masks, growth_overlap_masks, center_positions = simulate(
        (gridy, gridx),
        centers,
        patterns,
        days,
    )

    if args.no_gui:
        print(f"frames={len(grids)} weeds={weed_counts[-1]}")
        return

    InfectionGUI(grids, weed_counts, new_masks, overlap_masks, growth_overlap_masks, center_positions)


if __name__ == "__main__":
    main()
