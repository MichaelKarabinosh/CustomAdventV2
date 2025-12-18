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

        x, y = map(int, grid_size.split("x"))
        initial_x, initial_y = map(int, initial_position.split(","))

        nums = pattern_draft.split(",")
        pattern = []
        for row in nums:
            pattern.append(row)

        rels = generate_relative_list(pattern)
        garden.append(([x, y], [initial_x, initial_y], rels, num_days))

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
    len_x = garden[0][0]
    len_y = garden[0][1]

    weeds_copy = set(weeds)
    for y, x in weeds:
        for rel_y, rel_x in rel_list:
            next_weed_y = y + rel_y
            next_weed_x = x + rel_x
            if 0 <= next_weed_y < len_y and 0 <= next_weed_x < len_x:
                weeds_copy.add((next_weed_y, next_weed_x))

    return weeds_copy


def part_one():
    counter = 0
    info = create_garden()

    for i in range(len(info)):
        days = info[i][3]

        # store weeds as y, x
        weeds_now = {(info[i][1][1], info[i][1][0])}
        rel_list = info[i][2]

        for day in range(days):
            prev_len = len(weeds_now)
            weeds_now = do_day(info[i], rel_list, weeds_now)
            if len(weeds_now) == prev_len:
                break

        counter += len(weeds_now)

    return counter

start_time = time.perf_counter()
print('Part One:', part_one())
end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"{elapsed_time:.4f} seconds")
