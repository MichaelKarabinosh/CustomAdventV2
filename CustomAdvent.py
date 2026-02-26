import copy
import math
from platform import win32_edition
import itertools
from math import gcd
import pprint

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

def convert_O_W(grid):
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == "O":
                grid[i][j] = "W"
    return grid

def do_day(rel_list, grid):
    overlap_counter = 0
    set_unique_weeds = {0}
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
                        if copied_array[i-positions_y][j+positions_x] == "O":
                            # print(i-positions_y, j+positions_x)
                            overlap_counter += 1
                        elif copied_array[i-positions_y][j+positions_x] == "X": copied_array[i - positions_y][j + positions_x] = "O"
    # print(print_grid(copied_array),'\n')
    copied_array = convert_O_W(copied_array)
    return copied_array,overlap_counter

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
        counter += row.count("O")
    return counter

# def line_key(p1, p2):
#     x1, y1 = p1
#     x2, y2 = p2
#
#     A = y2 - y1
#     B = x1 - x2
#     C = x2*y1 - x1*y2
#
#     g = gcd(gcd(abs(A), abs(B)), abs(C))
#     if g:
#         A //= g
#         B //= g
#         C //= g
#
#     # fix sign so representation is unique
#     if A < 0 or (A == 0 and B < 0):
#         A = -A
#         B = -B
#         C = -C
#     if A == 0 and B == 0 and C == 0:
#         return None
#
#     return (A, B, C)


# def sub_part_two(rel_list):
#     combos = list(itertools.combinations(rel_list, 2))
#     print(combos)
#     slope_set = set()
#     unique = set()
#     for combo in combos:
#         combo1, combo2 = combo
#         combo1x, combo1y = combo1
#         combo2x, combo2y = combo2
#         combo_x_updated = combo1x + combo2x
#         combo_y_updated = combo1y + combo2y
#         print(combo_x_updated, combo_y_updated,combo1x, combo1y, combo2x, combo2y)
#         if combo_x_updated != 0:
#             slope_set.add(combo_y_updated/combo_x_updated)
#         else:
#             slope_set.add('inf')
        # print(combo1, combo_updated,combo2)
        # all_lines = line_key(combo1, combo_updated)
        # if all_lines is not None:
        #     unique.add(line_key(combo1, combo_updated))
        # print(unique)

    # print(unique,len(unique))
    # print(slope_set, len(slope_set),"slopeset")

def do_one_line(line):
    num_weeds = [1]
    overlaps = []
    info = line.split("|")

    grid_size = info[0].strip()
    gridx,gridy = map(int, grid_size.split("x"))
    grid = create_grid(gridx,gridy)

    initial_pos = info[1].strip()
    initial_pos_x, initial_pos_y = map(int,initial_pos.split(","))
    grid[initial_pos_y][initial_pos_x] = "W"

    rel_list = create_infection(info[2].strip())
    num_days = int(info[3].strip())

    # print(print_grid(grid), "Day 0")
    # print("\n")

    for day in range(num_days):
        prev_weeds = count_weeds(grid)
        day_info = do_day(rel_list, grid)
        grid = day_info[0]
        num_overlaps = day_info[1]
        curr_weeds = count_weeds(grid)
        if curr_weeds == prev_weeds:
            break
        grid[initial_pos_y][initial_pos_x] = "L"
        print(print_grid(grid), "Day {}".format(day + 1))
        print('\n')
        grid[initial_pos_y][initial_pos_x] = "W"
        num_weeds.append(curr_weeds)
        overlaps.append(num_overlaps)
    return num_weeds[-1], num_weeds, overlaps

def create_diff_lists(orig):
    first_diff = []
    second_diff = []
    for i in range(len(orig)-1):
        first_diff.append(orig[i] - orig[i - 1])
    for i in range(len(first_diff)-1):
        second_diff.append(first_diff[i + 1] - first_diff[i])

    return first_diff, second_diff


def part_one_new():
    part_one_counter = 0
    for line in newlines:
        num_weeds, weeds_list, overlaps_list = do_one_line(line)
        # print('weeds', weeds_list,len(weeds_list))
        # print('GROWTH_overlaps', overlaps_list,len(overlaps_list))
        lists_weeds = create_diff_lists(weeds_list)
        lists_overlaps = create_diff_lists(overlaps_list)
        # print('first_diff_weeds', lists_weeds[0])
        print('second_diff_weeds', lists_weeds[1])
        # print('first_diff_GROWTH_overlaps', lists_overlaps[0])
        # print('second_diff_GROWTH_overlaps', lists_overlaps[1])
        print(line,'\n')

        part_one_counter += num_weeds
    return part_one_counter



def part_one():
    weeds_2 = []
    overlap_counter = 0
    total_weeds = 0
    arr = []
    for line in newlines:
        weeds_1 = [1]
        overlaps = []
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
        # print("\n")
        prev_weeds = 0
        for day in range(num_days):
            # print(rel_list)
            prev_weeds = count_weeds(grid)
            grid_sub = do_day(rel_list, grid)
            grid = grid_sub[0]
            overlaps.append(grid_sub[1])
            current_weeds = count_weeds(grid)
            if current_weeds == prev_weeds:
                break
            grid[initial_pos_y][initial_pos_x] = "L"
            # print(print_grid(grid), "Day {}".format(day + 1))
            # print('\n')
            grid[initial_pos_y][initial_pos_x] = "W"
            weeds_1.append(current_weeds)

        weeds_2.append((weeds_1,num_days))
        total_weeds += current_weeds
    return weeds_2,total_weeds,overlaps






def part_two(part_1): # IMPORTANT THAT CHAR MUST BE IN THE MIDDLE BECAUSE IF NOT DATA IS SKEWED
    p2_counter = 0
    part_1_0 = part_1[0]
    infection_counter = 1
    for row in part_1_0:
        weed_counts = row[0]
        days = row[1]
        roc_weeds = []
        for i in range(15):
            roc_weeds.append(weed_counts[i] - weed_counts[i-1])


        roc_roc_weeds = []
        for i in range(15):
            roc_roc_weeds.append((roc_weeds[i] - roc_weeds[i-1]))

        roc_roc_weeds = roc_roc_weeds[2:]
        # roc_weeds = roc_weeds[1:]

        print(weed_counts) # uncomment to view debug info on weed data
        # print(roc_weeds)
        print(roc_roc_weeds)
        print(part_1[2],'overlaps')
        print('index', infection_counter)
        infection_counter += 1
        print(max(roc_roc_weeds),'max')


        counter = 0
        for i in range(len(roc_roc_weeds)-3):
            if roc_roc_weeds[i] == roc_roc_weeds[i+1] == roc_roc_weeds[i+2] == roc_roc_weeds[i+3]:
                counter = i
                break

        # print(slope,'ho')
        a0, a1, a2 = weed_counts[counter], weed_counts[counter+1], weed_counts[counter+2]
        a = (a2 - 2 * a1 + a0) / 2
        b = a1 - a0 - a
        c = a0

        actual_days = days - counter
        # print(a,b,c) # uncomment to view quadratic

        num = a * (actual_days**2) + b*actual_days + c
        p2_counter += num
    return p2_counter

# part_one1 = part_one()
# weed_count = part_one1[1]
# print('Part One:',weed_count)
# print('Part Two:', int(part_two(part_one1)))
print(part_one_new(), 'Part One')