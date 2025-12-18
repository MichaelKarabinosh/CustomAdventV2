import time

newlines = []
with open('InputFile', 'r') as file:
    for line in file:
        newlines.append(line.strip("\n"))

def create_garden():
    garden = []
    for line in newlines:
        information = line.split('|')
        grid_size = information[0].strip()
        initial_position = information[1].strip()
        pattern_draft = information[2].strip()
        num_days = int(information[3].strip())

        x,y = map(int, grid_size.split("x"))
        initial_x, initial_y = map(int,initial_position.split(","))

        nums = pattern_draft.split(",")
        pattern = []
        for list in nums:
            pattern.append(list)
        rels = generate_relative_list(pattern)
        garden.append(([x,y], [initial_x,initial_y], rels, num_days))
    return garden

def generate_relative_list(pattern):
    rel_list = []
    length_y = len(pattern)
    length_x = len(pattern[0])
    for y in range(length_y):
        for x in range(length_x):
            if pattern[y][x] == "W":
                start_y = y
                start_x = x


    for y in range(length_y):
        for x in range(length_x):
            if pattern[y][x] == "1":
                rel_list.append((y - start_y, x - start_x))
    return rel_list

def do_day(garden, rel_list, weeds):
    len_y = int(garden[0][0][1])
    len_x = int(garden[0][0][0])
    weeds_copy = set(weeds)
    for y,x in weeds:
        for rel_y,rel_x in rel_list:
            next_weed_y = y + rel_y
            next_weed_x = x + rel_x
            if 0 <= next_weed_y < len_y and 0 <= next_weed_x < len_x:
                weeds_copy.add((next_weed_y, next_weed_x))
    # print(weeds_copy)
    return weeds_copy

def part_one():
    counter = 0
    info = create_garden()
    for i in range(len(newlines)):
        days = info[i][3]
        weeds = {(info[i][1][1],info[i][1][0])}
        weeds_now = set(weeds)
        rel_list = info[i][2]
        for day in range(days):
            weeds_prev_len = len(weeds)
            weeds_now = do_day(info, rel_list, weeds_now)
            # print(weeds_now)
            weeds_now_len = len(weeds_now)
            # print(weeds_now_len)
            if weeds_prev_len == weeds_now_len:
                break
        counter += weeds_now_len
    return counter


start_time = time.perf_counter()
print('Part One:', part_one())
end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"Function 'part_one' took {elapsed_time:.4f} seconds to run.")
