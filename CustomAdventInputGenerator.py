import random
import subprocess
import sys
from itertools import combinations

def generate_grid_size():
    grid_size_1 = random.randint(55, 85)
    grid_size_2 = grid_size_1 - random.randint(-5, 15)
    # grid_size_2 = grid_size_1
    str1 = str(grid_size_1) + "x" + str(grid_size_2)
    return str1

def generate_position(grid_size_1, grid_size_2):
    position_x = random.randint(int(grid_size_1/2) - 3, int(grid_size_1/2) + 3)
    position_y = random.randint(int(grid_size_2/2) - 3, int(grid_size_2/2) + 3)
    return str(position_x) + "," +  str(position_y)

def weighted_infection():
    return random.random() > 0.74


def generate_pattern():
    super_str = ""
    for i in range(5):
        str = ""
        for j in range(5):
            if j == 2 and i == 2:
                str += "W"
            elif weighted_infection():
                str += "1"
            else:
                str += "0"
        super_str += str + ","
    return super_str[:-1]

def generate_days():
    if random.random() > 0.7:
        return random.randint(int(1e8),int(1e11))
    return random.randint(25, 125)


def create_line():
    line = ""
    grid_size = generate_grid_size()
    posx,posy = map(int,grid_size.split("x"))
    line += str(grid_size) + " |"
    line += " " + str(generate_position(posx, posy)) + " |"
    line += " " + generate_pattern() + " |"
    line += " " + str(generate_days())
    return line

def create_line_semi(pattern):
    line = ""
    grid_size = "81x81"
    line += str(grid_size) + " |"
    line += " " + "40,40" + " |"
    line += " " + pattern + " |"
    line += " " + "100"
    return line



# (row==2, col==2) ---> index 12
CENTER_INDEX = 12


positions = [i for i in range(25) if i != CENTER_INDEX]

def index_to_rowcol(i):
    return divmod(i, 5)

def make_pattern(one_positions):
    grid = [["0"] * 5 for _ in range(5)]

    grid[2][2] = "W"

    # olace the 3 1s
    for idx in one_positions:
        r, c = index_to_rowcol(idx)
        grid[r][c] = "1"

    return ",".join("".join(row) for row in grid)

patterns = []

for combo in combinations(positions, 3):
    patterns.append(make_pattern(combo))

print(len(patterns))  # 2024



num_lines = 2024
with open("InputFile", "r") as f:
    lines = f.readlines()
    remaining_lines = lines[num_lines:]
    with open('InputFile', 'w') as f:
        f.writelines(remaining_lines)
with open("InputFile", "a") as f:
    for i in range(0,num_lines):
        f.write(create_line_semi(patterns[i]) + "\n")
# uncomment below to automatically execute code
#
# script_to_run = "CustomAdvent.py"
# command = [sys.executable, script_to_run]
#
# try:
#     result = subprocess.run(command, check=True, capture_output=True, text=True)
#     print("Output from the script:")
#     arr = result.stdout
#     print(arr)
#     print("Script finished successfully")
# except subprocess.CalledProcessError as e:
#     print(f"Error: {e.stderr}")
# except FileNotFoundError:
#     print("file not found")

