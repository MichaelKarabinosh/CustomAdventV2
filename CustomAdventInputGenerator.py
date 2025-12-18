import random
import subprocess
import sys

def generate_grid_size():
    grid_size_1 = random.randint(60, 80)
    # grid_size_2 = grid_size_1 - random.randint(-5, 15)
    grid_size_2 = grid_size_1
    str1 = str(grid_size_1) + "x" + str(grid_size_2)
    return str1

def generate_position(grid_size_1, grid_size_2):
    position_x = random.randint(int(grid_size_1/2) - 5, int(grid_size_1/2) + 5)
    position_y = random.randint(int(grid_size_2/2) - 5, int(grid_size_2/2) + 5)
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

num_lines = 100
with open("InputFile", "r") as f:
    lines = f.readlines()
    remaining_lines = lines[num_lines:]
    with open('InputFile', 'w') as f:
        f.writelines(remaining_lines)
with open("InputFile", "a") as f:
    for i in range(0,num_lines):
        f.write(create_line() + "\n")


script_to_run = "CustomAdvent.py"
command = [sys.executable, script_to_run]

try:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    print("Output from the script:")
    arr = result.stdout
    print(arr)
    print("Script finished successfully")
except subprocess.CalledProcessError as e:
    print(f"Error: {e.stderr}")
except FileNotFoundError:
    print("file not found")

