import copy

newlines = []
with open('InputFile', 'r') as file:
    for line in file:
        newlines.append(line.strip("\n"))

def create_grid(x,y):
    big_grid = []
    for i in range(y):
        y_axis = []
        for j in range(x):
            y_axis.append("X")
        big_grid.append(y_axis)
    return big_grid

def create_infection(infection_pattern):
    relative_list = []
    initial_pos_x, initial_pos_y = 0,0
    y_lines = infection_pattern.split(",")
    for i in range(len(y_lines)): # find rel pos of weed
        line = y_lines[i]
        for j in range(len(line)):
            if line[j] == "W":
                initial_pos_x = j + 1
                initial_pos_y = i + 1

    for i in range(len(y_lines)): # create relative list of weed positions
        line = y_lines[i]
        for j in range(len(line)):
            if line[j] == "1":
                found_pos_x = j + 1
                found_pos_y = i + 1
                relative_list.append([found_pos_x-initial_pos_x, initial_pos_y-found_pos_y])

    return relative_list

def do_day(rel_list, grid):
    copied_array = copy.deepcopy(grid)
    for i in range(len(grid)):
        row = grid[i]
        for j in range(len(row)):
            if row[j] == "W":
                for positions in rel_list:
                    positions_x = positions[0]
                    positions_y = positions[1]
                    # print(positions_x, positions_y)
                    if (len(grid)-1 >= i - positions_y >= 0) and (len(row)-1 >= j + positions_x >= 0):
                        copied_array[i-positions_y][j+positions_x] = "W"
    return copied_array

def print_grid(grid):
    result_strings = []
    for row in grid:
        row_str = " ".join(map(str, row))
        result_strings.append(row_str)
    final_string = "\n".join(result_strings)
    return final_string

def count_weeds(grid):
    counter = 0
    for row in grid:
        counter += row.count("W")
    return counter


def part_one():
    total_weeds = 0
    for line in newlines:
        info = line.split("|")
        grid_size = info[0].strip()
        grid1,grid2 = map(int,grid_size.split("x"))
        grid = create_grid(grid1,grid2)

        initial_pos = info[1].strip()
        initial_pos_x, initial_pos_y = map(int,initial_pos.split(","))
        grid[initial_pos_y][initial_pos_x] = "W"

        rel_list = create_infection(info[2].strip())
        num_days = int(info[3].strip())
        # print(print_grid(grid), "Day 0")
        prev_weeds = 0
        for day in range(num_days):
            # print(rel_list)
            prev_weeds = count_weeds(grid)
            grid = do_day(rel_list, grid)
            current_weeds = count_weeds(grid)
            if current_weeds == prev_weeds:
                break
        total_weeds += current_weeds
    return total_weeds
        # print(print_grid(grid), "Day {}".format(day+1))
        # print('\n')
print('Part One:', part_one())

