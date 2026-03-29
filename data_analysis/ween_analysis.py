from pathlib import Path

import numpy as np


INPUT_PATH = Path(__file__).resolve().parents[1] / "InputFile"


def parse_line(line):
    info = [part.strip() for part in line.split("|")]
    if len(info) != 4:
        raise ValueError(f"Invalid input line: {line}")

    gridx, gridy = map(int, info[0].split("x"))
    init_x, init_y = map(int, info[1].split(","))
    days = int(info[3])
    offsets = create_infection(info[2])
    return (gridy, gridx), (init_y, init_x), offsets, days


def load_input_lines(path):
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def create_infection(pattern):
    rows = pattern.split(",")
    center_x = center_y = None

    for row_index, row in enumerate(rows):
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
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            if value == "1":
                offsets.append((row_index - center_y, col_index - center_x))

    return np.array(offsets, dtype=np.int16)


def shift_add(mask, row_shift, col_shift, target):
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


def simulate_weed_counts(shape, center, offsets, days):
    height, width = shape
    center_y, center_x = center

    if not (0 <= center_y < height and 0 <= center_x < width):
        raise ValueError(f"Starting weed {(center_x, center_y)} is outside the grid")

    grid = np.zeros((height, width), dtype=bool)
    grid[center_y, center_x] = True
    weed_counts = [1]

    for _ in range(days):
        attempts = np.zeros((height, width), dtype=np.uint16)
        for row_shift, col_shift in offsets:
            shift_add(grid, int(row_shift), int(col_shift), attempts)

        next_grid = grid | (attempts > 0)
        if np.array_equal(next_grid, grid):
            break

        grid = next_grid
        weed_counts.append(int(grid.sum()))

    return weed_counts


def create_diff_lists(values):
    first_diff = [values[index + 1] - values[index] for index in range(len(values) - 1)]
    second_diff = [first_diff[index + 1] - first_diff[index] for index in range(len(first_diff) - 1)]
    return first_diff, second_diff


def fit_quadratic_from_sequence(sequence, min_stable_run=3):
    _, second_diff = create_diff_lists(sequence)
    if len(second_diff) < min_stable_run:
        raise ValueError("Need more data points to detect a quadratic region")

    start_day = None
    for index in range(len(second_diff) - min_stable_run + 1):
        window = second_diff[index:index + min_stable_run]
        if all(value == window[0] for value in window):
            start_day = index
            break

    if start_day is None:
        raise ValueError("Quadratic region not found")

    days = np.array([start_day, start_day + 1, start_day + 2], dtype=float)
    values = np.array(sequence[start_day:start_day + 3], dtype=float)
    matrix = np.array([
        [days[0] ** 2, days[0], 1.0],
        [days[1] ** 2, days[1], 1.0],
        [days[2] ** 2, days[2], 1.0],
    ])
    a, b, c = np.linalg.solve(matrix, values)

    return a, b, c, start_day


def format_number(value):
    rounded = round(float(value))
    if abs(float(value) - rounded) < 1e-9:
        return str(int(rounded))
    return f"{float(value):.10g}"


def analyze_line(line):
    shape, center, offsets, days = parse_line(line)
    weed_counts = simulate_weed_counts(shape, center, offsets, days)
    first_diff, second_diff = create_diff_lists(weed_counts)
    a, b, c, start_day = fit_quadratic_from_sequence(weed_counts)

    print(f"weed counts: {weed_counts}")
    print(f"first diff weed counts: {first_diff}")
    print(f"second diff weed counts: {second_diff}")
    print(f"fitted quadratic: y = {format_number(a)}x^2 + {format_number(b)}x + {format_number(c)}")
    print(f"quadratic starts fitting on day: {start_day}")
    print(line)


def main():
    for index, line in enumerate(load_input_lines(INPUT_PATH)):
        if index > 0:
            print()
        analyze_line(line)


if __name__ == "__main__":
    main()
