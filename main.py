#pgzero

import random
import pygame
from numpy import ndarray
from copy import deepcopy
from random import randint
from constants import *
from translations import *

lang = 'en'

def autodetect_lang():
	global lang

	lang = 'en'
	try:
		import os
		if 'LANG' in os.environ:
			lang0 = (os.environ['LANG'])[0:2]
			if lang0 in translations:
				lang = lang0
	except:
		pass

def _(str_key):
	str = translations[lang][str_key] if str_key in translations[lang] else translations['en'][str_key] if str_key in translations['en'] else str_key
	if lang == 'he' and str_key in translations[lang]:
		str = str[::-1]
	return str

autodetect_lang()

def get_map_cell_pos(cx, cy):
	return (CELL_W * (cx + 0.5), CELL_H * (cy + 0.5))

def get_actor_pos(actor):
	return get_map_cell_pos(*actor.c)

def apply_diff(orig, diff):
	return (orig[0] + diff[0], orig[1] + diff[1])

def apply_map_cell_pos_diff(c, diff):
	return apply_diff(get_map_cell_pos(*c), diff)

def apply_actor_pos_diff(actor, pos):
	return apply_map_cell_pos_diff(actor.c, pos)

def set_actor_coord(actor, cx, cy):
	actor.c = (cx, cy)
	actor.cx = cx
	actor.cy = cy
	actor.x, actor.y = get_map_cell_pos(cx, cy)

def move_actor(actor, diff):
	set_actor_coord(actor, *apply_diff(actor.c, diff))

def create_actor(image_name, cx, cy):
	actor = Actor(image_name)
	set_actor_coord(actor, cx, cy)
	return actor

def get_actor_on_cell(cell, actors):
	for actor in actors:
		if cell == actor.c:
			return actor
	return None

def is_cell_in_actors(cell, actors):
	return get_actor_on_cell(cell, actors) is not None

def is_cell_in_area(cell, x_range, y_range):
	return cell[0] in x_range and cell[1] in y_range

def get_actor_neighbors(actor, x_range=None, y_range=None):
	neighbors = []
	for diff in ((-1, 0), (+1, 0), (0, -1), (0, +1)):
		neigh = apply_diff(actor.c, diff)
		if x_range is None or y_range is None or is_cell_in_area(neigh, x_range, y_range):
			neighbors.append(neigh)
	debug(3, "* get_actor_neighbors %s - %s" % (str(actor.c), neighbors))
	return neighbors

def get_all_neighbors(cx, cy, include_self=False):
	neighbors = []
	for dy in (-1, 0, +1):
		for dx in (-1, 0, +1):
			if dy == 0 and dx == 0 and not include_self:
				continue
			neighbors.append((cx + dx, cy + dy))
	return neighbors

# game sprites
char = create_actor('stand', 1, 1)

status_heart = Actor("heart", (POS_CENTER_X - 2 * CELL_W / 2, POS_STATUS_Y))
status_sword = Actor("sword", (POS_CENTER_X + 1 * CELL_W / 2, POS_STATUS_Y))

# game variables
is_game_won = False
is_music_enabled = True
is_music_started = False
is_sound_enabled = True
is_move_animate_enabled = True
is_level_intro_enabled = True

mode = "start"
is_random_maze = False
is_spiral_maze = False
is_grid_maze = False
is_any_maze = False
is_barrel_puzzle = False
is_color_puzzle = False
is_four_rooms = False
is_cloud_mode = False
is_gate_puzzle = False
is_stoneage_puzzle = False
has_start = False
has_finish = False

bg_image = None

game_time = 0
level_time = 0
idle_time = 0

last_autogeneration_time = 0

last_time_arrow_keys_processed = 0
pressed_arrow_keys = []
last_processed_arrow_keys = []

map = None  # will be generated
color_map = None
cell_images = {}  # will be generated
color_cell_images = []
revealed_map = None
theme_prefix = None

enemies = []
hearts = []
swords = []
barrels = []

num_bonus_health = 0
num_bonus_attack = 0

killed_enemies = []

level_title_timer = 0
level_target_timer = 0

from levels import levels
level = None
level_idx = -1

class Area:
	# x1, y1, x2, y2, size_x, size_y, x_range, y_range, idx
	pass

room = Area()
room_idx = None
color_puzzle = Area()

def debug(level, str):
	if DEBUG_LEVEL < level:
		return
	print(str)

def debug_map(level=0, descr=None, full=True, clean=True, combined=True, dual=False, endl=False):
	if DEBUG_LEVEL < level:
		return
	if descr:
		print(descr)
	for cy in MAP_Y_RANGE if full else PLAY_Y_RANGE:
		if not combined:
			for cx in MAP_X_RANGE if full else PLAY_X_RANGE:
				print(CELL_FLOOR if clean and map[cx, cy] in CELL_FLOOR_TYPES else map[cx, cy], end="")
		if dual:
			print("    ", end="")
		if dual or combined:
			for cx in MAP_X_RANGE if full else PLAY_X_RANGE:
				cell_ch = CELL_FLOOR if clean and map[cx, cy] in CELL_FLOOR_TYPES else map[cx, cy]
				if is_cell_in_actors((cx, cy), enemies):
					cell_ch = '&'
				if is_cell_in_actors((cx, cy), barrels):
					cell_ch = '*'
				if char.c is not None and is_cell_in_actors((cx, cy), [char]):
					cell_ch = '@'
				print(cell_ch, end="")
		print()
	if endl:
		print()

def get_theme_image_name(image_name):
	return theme_prefix + image_name

def create_theme_image(image_name):
	return Actor(get_theme_image_name(image_name))

def create_theme_actor(image_name, cell):
	return create_actor(get_theme_image_name(image_name), *cell)

def get_num_color_puzzle_values():
	return level["color_puzzle_values"] if "color_puzzle_values" in level else MAX_COLOR_PUZZLE_VALUES

def press_color_puzzle_cell(cx, cy):
	color_map[cx, cy] = (color_map[cx, cy] + 1) % get_num_color_puzzle_values()

def press_color_puzzle_plate(cx, cy):
	for (nx, ny) in get_all_neighbors(cx, cy):
		press_color_puzzle_cell(nx, ny)
		if "color_puzzle_extended" in level and (nx != cx and ny != cy) ^ (cx % 3 != 0 or cy % 3 != 0):
			press_color_puzzle_cell(nx, ny)

def get_color_puzzle_image(cx, cy):
	return color_cell_images[color_map[cx, cy]]

def set_color_puzzle():
	color_puzzle.size_x = level["color_puzzle_size"][0] if "color_puzzle_size" in level else DEFAULT_COLOR_PUZZLE_ROOM_SIZE_X[room.idx] if room is not None else DEFAULT_COLOR_PUZZLE_PLAY_SIZE_X
	color_puzzle.size_y = level["color_puzzle_size"][1] if "color_puzzle_size" in level else DEFAULT_COLOR_PUZZLE_ROOM_SIZE_Y[room.idx] if room is not None else DEFAULT_COLOR_PUZZLE_PLAY_SIZE_Y
	color_puzzle.x1 = room.x1 + int((room.size_x - color_puzzle.size_x) / 2)
	color_puzzle.x2 = color_puzzle.x1 + color_puzzle.size_x - 1
	color_puzzle.y1 = room.y1 + int((room.size_y - color_puzzle.size_y) / 2)
	color_puzzle.y2 = color_puzzle.y1 + color_puzzle.size_y - 1
	color_puzzle.x_range = range(color_puzzle.x1, color_puzzle.x2 + 1)
	color_puzzle.y_range = range(color_puzzle.y1, color_puzzle.y2 + 1)

def is_in_color_puzzle(cx, cy):
	return is_color_puzzle and cx in color_puzzle.x_range and cy in color_puzzle.y_range

def is_color_puzzle_plate(cx, cy):
	return is_in_color_puzzle(cx, cy) and (cx - color_puzzle.x1) % 2 == 1 and (cy - color_puzzle.y1) % 2 == 1

def is_color_puzzle_solved():
	for cy in color_puzzle.y_range:
		for cx in color_puzzle.x_range:
			if not is_color_puzzle_plate(cx, cy) and color_map[cx, cy] != COLOR_PUZZLE_VALUE_GREEN:
				return False
	return True

def is_barrel_puzzle_solved():
	room_barrels = [ barrel for barrel in barrels if is_actor_in_room(barrel) ]
	for barrel in room_barrels:
		if map[barrel.c] != CELL_PLATE:
			return False
	return True

def reveal_map_near_char():
	if not is_cloud_mode:
		return

	for (cx, cy) in get_all_neighbors(char.cx, char.cy, include_self=True):
		revealed_map[cx, cy] = True

def get_revealed_actors(actors):
	if not is_cloud_mode or level.get("actors_always_revealed", False):
		return actors

	revealed_actors = []
	for actor in actors:
		if revealed_map[actor.c]:
			revealed_actors.append(actor)
	return revealed_actors

def assert_room():
	if mode != 'game' and mode != 'init':
		print("Called room function when not inside game or init (mode=%s). Fix this bug" % mode)
		quit()

def set_room(idx):
	room.size_x = ROOM_SIZE_X[idx] if idx is not None else PLAY_SIZE_X
	room.size_y = ROOM_SIZE_Y[idx] if idx is not None else PLAY_SIZE_Y
	room.x1 = ROOM_X1[idx] if idx is not None else PLAY_X1
	room.x2 = ROOM_X2[idx] if idx is not None else PLAY_X2
	room.y1 = ROOM_Y1[idx] if idx is not None else PLAY_Y1
	room.y2 = ROOM_Y2[idx] if idx is not None else PLAY_Y2
	room.x_range = ROOM_X_RANGE[idx] if idx is not None else PLAY_X_RANGE
	room.y_range = ROOM_Y_RANGE[idx] if idx is not None else PLAY_Y_RANGE
	room.idx = idx

	if is_color_puzzle:
		set_color_puzzle()

def is_actor_in_room(actor):
	assert_room()

	return actor.cx >= room.x1 and actor.cx <= room.x2 and actor.cy >= room.y1 and actor.cy <= room.y2

def is_cell_in_room(cell):
	return is_cell_in_area(cell, room.x_range, room.y_range)

def get_distance(cx, cy, tx=None, ty=None):
	if type(cx) is tuple and type(cy) is tuple:
		return get_distance(*cx, *cy)
	return abs(tx - cx) + abs(ty - cy)

def is_cell_accessible(cx, cy, place=False):
	if map[cx, cy] in (CELL_CHAR_PLACE_OBSTACLES if place else CELL_CHAR_MOVE_OBSTACLES):
		return False
	for actor in enemies + barrels:
		if actor.cx == cx and actor.cy == cy:
			return False
	return True

def get_accessible_neighbors(cell, allow_closed_gate=False):
	neighbors = []
	if ALLOW_DIAGONAL_MOVES and False:
		directions = ((-1, -1), (0, -1), (+1, -1), (-1, 0), (+1, 0), (-1, +1), (0, +1), (+1, +1))
	else:
		directions = ((-1, 0), (+1, 0), (0, -1), (0, +1))
	for diff in directions:
		neigh = apply_diff(cell, diff)
		if is_cell_in_room(neigh) and (allow_closed_gate and map[neigh] == CELL_GATE0 or is_cell_accessible(*neigh)):
			neighbors.append(neigh)
	debug(3, "* get_accessible_neighbors %s - %s" % (str(cell), neighbors))
	return neighbors

def get_all_accessible_cells():
	accessible_cells = []
	unprocessed_cells = [char.c]
	while unprocessed_cells:
		cell = unprocessed_cells.pop(0)
		accessible_cells.append(cell)
		neigbours = get_accessible_neighbors(cell)
		for n in neigbours:
			if n not in accessible_cells and n not in unprocessed_cells:
				unprocessed_cells.append(n)
	return accessible_cells

def get_num_accessible_target_directions(start_cell, target_cells):
	num_accessible_directions = 0

	for neigh in get_accessible_neighbors(start_cell, allow_closed_gate=True):
		unprocessed_cells = [ neigh ]
		accessible_cells = [ start_cell, neigh ]

		while unprocessed_cells:
			cell = unprocessed_cells.pop(0)
			if cell in target_cells:
				num_accessible_directions += 1
				break
			for new_neigh in get_accessible_neighbors(cell, allow_closed_gate=True):
				if new_neigh in accessible_cells:
					continue
				accessible_cells.append(new_neigh)
				unprocessed_cells.append(new_neigh)

	return num_accessible_directions

def find_path(start_cell, target_cell, visited_cells=[]):
	visited_cells.append(start_cell)
	path_cells = None
	for neigh_cell in get_accessible_neighbors(start_cell):
		if neigh_cell == target_cell:
			path_cells = [target_cell]
			break
		if neigh_cell in visited_cells:
			continue
		path_cells = find_path(neigh_cell, target_cell, visited_cells)
		if path_cells:
			path_cells.insert(0, neigh_cell)
			break
	visited_cells.pop()
	return path_cells

def is_path_found(start_cell, target_cell):
	return find_path(start_cell, target_cell) is not None

def get_passed_gates(start_cell, target_cell):
	passed_gates = []
	for cell in find_path(start_cell, target_cell) or ():
		if map[cell] == CELL_GATE1:
			passed_gates.append(cell)
	return passed_gates

def set_char_cell(cell):
	global char_cell

	char_cell = cell

def place_char_in_closest_accessible_cell(c):
	best_distance = None
	best_cell = None
	for cell in get_all_accessible_cells():
		distance = get_distance(cell, c)
		if best_distance is None or distance < best_distance:
			best_distance = distance
			best_cell = cell
	set_actor_coord(char, *best_cell)

def place_char_in_first_free_spot():
	for cy in room.y_range:
		for cx in room.x_range:
			if is_cell_accessible(cx, cy, place=True):
				set_actor_coord(char, cx, cy)
				return

	print("Was not able to find free spot for char, fix the level or a bug")
	if DEBUG_LEVEL:
		set_actor_coord(char, 0, 0)
	else:
		quit()

def get_random_floor_cell_type():
	return CELL_FLOOR_TYPES_FREQUENT[randint(0, len(CELL_FLOOR_TYPES_FREQUENT) - 1)]

def convert_to_floor_if_needed(cx, cy):
	if map[cx, cy] == CELL_BORDER or map[cx, cy] == CELL_INTERNAL1:
		map[cx, cy] = get_random_floor_cell_type()

def get_num_gate_puzzle_plates():
	return level["num_gate_puzzle_plates"] if "num_gate_puzzle_plates" in level else DEFAULT_NUM_GATE_PUZZLE_PLATES

def get_num_gate_puzzle_gates():
	return level["num_gate_puzzle_gates"] if "num_gate_puzzle_gates" in level else DEFAULT_NUM_GATE_PUZZLE_GATES

def toggle_gate_puzzle_gate(cx, cy):
	map[cx, cy] = CELL_GATE1 if map[cx, cy] == CELL_GATE0 else CELL_GATE0

def press_gate_puzzle_plate():
	for gate in gate_puzzle_attached_plate_gates[char.c]:
		toggle_gate_puzzle_gate(*gate)

def check_gate_puzzle_solution(finish_cell, gates, depth=0, visited_plate_gate_states=None):
	global map

	if depth == 0:
		debug_map(2, descr="Map initially")
		visited_plate_gate_states = {}

	start_cell = char.c

	if is_path_found(start_cell, finish_cell):
		if depth == 0:
			return False
		else:
			return {
				'used_plates': [],
				'open_gates': [],
				'passed_gates': get_passed_gates(start_cell, finish_cell),
			}

	best_solution = None
	best_plate = None

	plates = [ *gate_puzzle_attached_plate_gates ]
	gate_states = tuple(map[gate] for gate in gates)

	for plate in plates:
		if start_cell != plate and is_path_found(start_cell, plate):
			plate_gate_states = (plate, gate_states)
			if plate_gate_states in visited_plate_gate_states:
				solution = visited_plate_gate_states[plate_gate_states]
			else:
				visited_plate_gate_states[plate_gate_states] = None
				set_actor_coord(char, *plate)
				press_gate_puzzle_plate()

				solution = check_gate_puzzle_solution(finish_cell, gates, depth + 1, visited_plate_gate_states)

				press_gate_puzzle_plate()
				set_actor_coord(char, *start_cell)
				visited_plate_gate_states[plate_gate_states] = solution

			if solution and (not best_solution or len(solution["used_plates"]) < len(best_solution["used_plates"]) \
					or len(solution["used_plates"]) == len(best_solution["used_plates"]) and best_plate not in solution["used_plates"]):
				best_solution = solution
				best_plate = plate

	if best_solution:
		used_plates = best_solution["used_plates"].copy()
		if best_plate not in used_plates:
			used_plates.append(best_plate)

		open_gates = best_solution["open_gates"].copy()
		for gate in gate_puzzle_attached_plate_gates[best_plate]:
			if map[gate] == CELL_GATE0 and gate not in open_gates:
				open_gates.append(gate)

		passed_gates = best_solution["passed_gates"].copy()
		for gate in get_passed_gates(start_cell, best_plate):
			if gate not in passed_gates:
				passed_gates.append(gate)

		if depth == 0:
			return \
				len(used_plates)  >= get_num_gate_puzzle_plates() and \
				len(open_gates)   >= get_num_gate_puzzle_gates()  and \
				len(passed_gates) >= get_num_gate_puzzle_gates()
		else:
			return {
				'used_plates': used_plates,
				'open_gates': open_gates,
				'passed_gates': passed_gates,
			}

	return False if depth == 0 else None

def generate_random_solvable_gate_room(accessible_cells, finish_cell):
	global map, gate_puzzle_attached_plate_gates

	origin_map = map.copy()

	def select_random_gates_attached_to_plate(num_gates):
		num_attached_gates = randint(MIN_GATE_PUZZLE_ATTACHED_GATES, MAX_GATE_PUZZLE_ATTACHED_GATES)
		if num_attached_gates > num_gates:
			num_attached_gates = num_gates
		attached_gate_idxs = []
		while len(attached_gate_idxs) < num_attached_gates:
			gate_idx = randint(0, num_gates - 1)
			if gate_idx in attached_gate_idxs:
				continue
			attached_gate_idxs.append(gate_idx)
		return attached_gate_idxs

	num_tries = 100000
	while num_tries > 0:
		plates = []
		for p in range(get_num_gate_puzzle_plates()):
			while True:
				cell = accessible_cells[randint(0, len(accessible_cells) - 1)]
				if map[cell] in CELL_CHAR_PLACE_OBSTACLES:
					continue
				map[cell] = CELL_PLATE
				plates.append(cell)
				break

		target_cells = [char.c, finish_cell, *plates]

		gates = []
		for g in range(get_num_gate_puzzle_gates()):
			while True:
				cell = accessible_cells[randint(0, len(accessible_cells) - 1)]
				if map[cell] in CELL_CHAR_PLACE_OBSTACLES:
					continue
				if get_num_accessible_target_directions(cell, target_cells) < 2:
					continue
				target_cells.append(cell)
				map[cell] = CELL_GATE0 if randint(0, 1) == 0 else CELL_GATE1
				gates.append(cell)
				break

		gate_puzzle_attached_plate_gates = {}
		for plate in plates:
			gate_idxs = select_random_gates_attached_to_plate(len(gates))
			gate_puzzle_attached_plate_gates[plate] = [ gates[i] for i in gate_idxs ]

		debug_map(4, descr="Generating gate puzzle - tries left: %d" % num_tries)
		if check_gate_puzzle_solution(finish_cell, gates):
			break

		map = origin_map.copy()
		num_tries -= 1
	else:
		print("Can't generate gate puzzle, sorry")
		quit()

def get_random_even_point(a1, a2):
	return a1 + randint(0, int((a2 - a1) / 2)) * 2

def generate_random_maze_area(x1, y1, x2, y2):
	if x2 - x1 <= 1 or y2 - y1 <= 1:
		return

	# select random point that will divide the area into 4 sub-areas
	random_x = get_random_even_point(x1 + 1, x2 - 1)
	random_y = get_random_even_point(y1 + 1, y2 - 1)

	# create the horizontal and vertical border wall via this point
	for x in range(x1, x2 + 1):
		map[x, random_y] = CELL_BORDER
	for y in range(y1, y2 + 1):
		map[random_x, y] = CELL_BORDER

	# select 3 random holes on the 4 just created border walls
	skipped_wall = randint(0, 3)
	if skipped_wall != 0: map[get_random_even_point(x1, random_x - 1), random_y] = get_random_floor_cell_type()
	if skipped_wall != 1: map[random_x, get_random_even_point(y1, random_y - 1)] = get_random_floor_cell_type()
	if skipped_wall != 2: map[get_random_even_point(random_x + 1, x2), random_y] = get_random_floor_cell_type()
	if skipped_wall != 3: map[random_x, get_random_even_point(random_y + 1, y2)] = get_random_floor_cell_type()

	# recurse into 4 sub-areas
	generate_random_maze_area(x1, y1, random_x - 1, random_y - 1)
	generate_random_maze_area(random_x + 1, y1, x2, random_y - 1)
	generate_random_maze_area(x1, random_y + 1, random_x - 1, y2)
	generate_random_maze_area(random_x + 1, random_y + 1, x2, y2)

def generate_grid_maze():
	for cy in room.y_range:
		for cx in room.x_range:
			if (cx - room.x1 - 1) % 2 == 0 and (cy - room.y1 - 1) % 2 == 0:
				map[cx, cy] = CELL_BORDER

def generate_spiral_maze():
	if randint(0, 1) == 0:
		pointer = (room.x1 - 1, room.y1 + 1)
		steps = ((1, 0), (0, 1), (-1, 0), (0, -1))
		len = [room.x2 - room.x1, room.y2 - room.y1]
	else:
		pointer = (room.x1 + 1, room.y1 - 1)
		steps = ((0, 1), (1, 0), (0, -1), (-1, 0))
		len = [room.y2 - room.y1, room.x2 - room.x1]

	dir = 0

	while len[dir % 2] > 0:
		step = steps[dir]
		for i in range(len[dir % 2]):
			pointer = apply_diff(pointer, step)
			map[pointer] = CELL_BORDER

		if dir % 2 == 0:
			len[0] -= 2
			len[1] -= 2
		dir = (dir + 1) % 4

def generate_random_maze_room():
	generate_random_maze_area(room.x1, room.y1, room.x2, room.y2)

def generate_random_free_path(target_c, level=0):
	global map

	place_char_in_closest_accessible_cell(target_c)

	if char.c == target_c:
		return True

	ox, oy = char.c
	tx, ty = target_c

	debug(2, "* [%d] generating free path from (%d, %d) to (%d, %d)" % (level, ox, oy, tx, ty))

	accessible_cells = get_all_accessible_cells()
	weighted_neighbors = []
	for cell in get_actor_neighbors(char, room.x_range, room.y_range):
		if cell in accessible_cells:
			continue
		if is_cell_in_actors(cell, barrels):
			continue
		cx, cy = cell
		weight = randint(0, 30)
		weight += (1000 - get_distance(cx, cy, tx, ty)) * 10
		weighted_neighbors.append((weight, cell))

	neighbors = [n[1] for n in sorted(weighted_neighbors, reverse=True)]

	if not neighbors:
		debug(2, "* [%d] failed to generate free path from (%d, %d) to (%d, %d)" % (level, ox, oy, tx, ty))
		return False

	for neigh in neighbors:
		if map[neigh] != CELL_BORDER:
			print("BUG!")
			return False
		convert_to_floor_if_needed(*neigh)
		set_actor_coord(char, cx, cy)
		debug(3, "* [%d] trying to move to %s" % (level, str(neigh)))
		debug_map(3, full=True, clean=True, combined=True)
		is_path_found = generate_random_free_path(target_c, level + 1)
		if is_path_found:
			debug(2, "* [%d] successfully generated free path from (%d, %d) to (%d, %d)" % (level, ox, oy, tx, ty))
			debug_map(2, full=True, clean=True, combined=True)
			return True
		map[neigh] = CELL_BORDER

	set_actor_coord(char, ox, oy)

	return False

def create_barrel(cell):
	global barrels

	barrel = create_theme_actor("barrel", cell)
	barrels.append(barrel)

def pull_barrel_randomly(barrel, visited_cell_pairs, num_moves):
	idx = barrels.index(barrel)
	weighted_neighbors = []
	# sort 4 barrel directions to place char to the "adjacent to barrel" cell for a pull (prefer empty cells)
	for c in get_actor_neighbors(barrel, room.x_range, room.y_range):
		if (c, char.c) in visited_cell_pairs:
			continue
		cx, cy = c
		if is_cell_in_actors(c, barrels):
			continue
		new_cx = cx + cx - barrel.cx
		new_cy = cy + cy - barrel.cy
		if new_cx not in room.x_range or new_cy not in room.y_range:
			continue
		if is_cell_in_actors((new_cx, new_cy), barrels):
			continue
		weight = randint(0, 30)
		if map[cx, cy] != CELL_BORDER:
			weight += 20
		if map[cx, cy] == CELL_PLATE:
			weight += 4
		if map[new_cx, new_cy] != CELL_BORDER:
			weight += 10
		if map[new_cx, new_cy] == CELL_PLATE:
			weight += 2
		weighted_neighbors.append((weight, c))

	neighbors = [n[1] for n in sorted(weighted_neighbors, reverse=True)]

	if not neighbors:
		# can't find free neighbor for barrel, stop
		debug(2, "barrel #%d - failed to find free neighbor for barrel %s (%d left)" % (idx, barrel.c, num_moves))
		return False

	for neighbor in neighbors:
		cx, cy = neighbor

		# if the cell is not empty (BORDER), make it empty (FLOOR with additions)
		was_border1_replaced = False
		if map[cx, cy] == CELL_BORDER:
			convert_to_floor_if_needed(cx, cy)
			was_border1_replaced = True
		barrel_cx = barrel.cx
		barrel_cy = barrel.cy
		new_char_cx = cx + (cx - barrel_cx)
		new_char_cy = cy + (cy - barrel_cy)
		debug(2, "barrel #%d - neighbor %s, next cell (%d, %d)" % (idx, neighbor, new_char_cx, new_char_cy))
		debug_map(2, full=True, clean=True, dual=True)
		was_border2_replaced = False
		if map[new_char_cx, new_char_cy] == CELL_BORDER:
			convert_to_floor_if_needed(new_char_cx, new_char_cy)
			was_border2_replaced = True

		# if the char position is not None, first create random free path to the selected adjacent cell
		old_char_c = char.c
		if char.c is None:
			set_actor_coord(char, cx, cy)
		if generate_random_free_path(neighbor):
			# pull the barrel to the char
			set_actor_coord(barrel, char.cx, char.cy)
			set_actor_coord(char, new_char_cx, new_char_cy)

			visited_cell_pairs.append((neighbor, char.c))

			if num_moves <= 1:
				return True

			if pull_barrel_randomly(barrel, visited_cell_pairs, num_moves - 1):
				return True
			else:
				debug(2, "barrel #%d - failed to pull barrel (%d moves left)" % (idx, num_moves - 1))
		else:
			debug(2, "barrel #%d - failed to generate random free path to neighbor %s" % (idx, neighbor))

		# can't create free path for char or can't pull barrel, restore the original state
		char.c = old_char_c
		set_actor_coord(barrel, barrel_cx, barrel_cy)
		if was_border1_replaced:
			map[cx, cy] = CELL_BORDER
		if was_border2_replaced:
			map[new_char_cx, new_char_cy] = CELL_BORDER

	return False

def generate_random_solvable_barrel_room():
	global map

	num_barrels = level["num_barrels"] if "num_barrels" in level else DEFAULT_NUM_BARRELS

	def get_random_cell():
		return (randint(room.x1, room.x2), randint(room.y1, room.y2))

	# 0) initialize char position to None
	char.c = None

	# 1) initialize entire room to BORDER
	for cy in room.y_range:
		for cx in room.x_range:
			map[cx, cy] = CELL_BORDER

	# 2) place room plates randomly or in good positions, as the number of barrels
	# 3) place room barrels into the place cells, one barrel per one plate
	for n in range(num_barrels):
		while True:
			cell = get_random_cell()
			if map[cell] != CELL_PLATE:
				map[cell] = CELL_PLATE
				break
		create_barrel(cell)

	# 4) for each room barrel do:
	for barrel in barrels:
		debug(2, "barrel #%d - starting (%d, %d)" % (barrels.index(barrel), barrel.cx, barrel.cy))
		visited_cell_pairs = [(barrel.c, char.c)]
		# 5) make random moves for the barrel until possible
		num_moves = randint(10, 80)
		pull_barrel_randomly(barrel, visited_cell_pairs, num_moves)
		debug(2, "barrel #%d - finished (%d, %d)" % (barrels.index(barrel), barrel.cx, barrel.cy))

	# 11) remember the char position, optionally try to move it as far left-top as possible
	if char.c is None:
		print("Failed to generate random solvable barrel room")
		if DEBUG_LEVEL:
			return
		else:
			quit()

	while True:
		for c in get_actor_neighbors(char, room.x_range, room.y_range):
			cx, cy = c
			if cx > char.cx or cy > char.cy:
				continue
			if not map[cx, cy] in CELL_CHAR_MOVE_OBSTACLES:
				set_actor_coord(char, cx, cy)
				if room.idx:
					set_char_cell(char.c)
				break
		else:
			break

def generate_random_nonsolvable_stoneage_room():
	global map

	def get_random_floor_cell():
		while True:
			cell = randint(room.x1, room.x2), randint(room.y1, room.y2)
			if map[cell] in CELL_FLOOR_TYPES:
				return cell

	def replace_random_floor_cell(cell_type, num=1, callback=None, extra=None):
		for n in range(num):
			cell = get_random_floor_cell()
			map[cell] = cell_type
			if callback:
				if extra:
					callback(cell, extra)
				else:
					callback(cell)

	replace_random_floor_cell(CELL_VOID, 70)
	replace_random_floor_cell(CELL_PORTAL, 3)
	replace_random_floor_cell(CELL_START, 1, set_char_cell)
	replace_random_floor_cell(CELL_FINISH)
	replace_random_floor_cell(CELL_GATE0, 3)
	replace_random_floor_cell(CELL_GATE1, 3)
	replace_random_floor_cell(CELL_SAND, 10)
	replace_random_floor_cell(CELL_LIFT, 5)
	replace_random_floor_cell(CELL_LIFTH, 2)
	replace_random_floor_cell(CELL_LIFTV, 2)
	replace_random_floor_cell(CELL_LIFTU)
	replace_random_floor_cell(CELL_LIFTD)
	replace_random_floor_cell(CELL_LIFTL)
	replace_random_floor_cell(CELL_LIFTR)

def get_lift_target(cell, diff):
	cell_type = map[cell]
	if cell_type not in LIFT_TYPES or diff not in LIFT_TYPE_DIRECTIONS[cell_type]:
		return None
	returned_cell = None
	while True:
		next_cell = apply_diff(cell, diff)
		if not is_cell_in_room(next_cell) or map[next_cell] != CELL_VOID:
			return returned_cell
		returned_cell = cell = next_cell

def create_enemy(cx, cy, health=None, attack=None, bonus=None):
	global num_bonus_health, num_bonus_attack

	enemy = create_actor("skeleton", cx, cy)
	enemy.health = health if health is not None else randint(MIN_ENEMY_HEALTH, MAX_ENEMY_HEALTH)
	enemy.attack = attack if attack is not None else randint(MIN_ENEMY_ATTACK, MAX_ENEMY_ATTACK)
	enemy.bonus  = bonus  if bonus  is not None else randint(0, 2)
	if enemy.bonus == BONUS_HEALTH:
		num_bonus_health += 1
	elif enemy.bonus == BONUS_ATTACK:
		num_bonus_attack += 1
	return enemy

def generate_room(idx):
	set_room(idx)

	if is_barrel_puzzle or is_gate_puzzle:
		draw()
		pygame.display.flip()

	if is_random_maze:
		generate_random_maze_room()

	if is_spiral_maze:
		generate_spiral_maze()

	if is_grid_maze:
		generate_grid_maze()

	if is_stoneage_puzzle:
		generate_random_nonsolvable_stoneage_room()

	if is_barrel_puzzle:
		generate_random_solvable_barrel_room()

	if has_finish or is_gate_puzzle:
		set_actor_coord(char, room.x1, room.y1)
		if room.idx == 0:
			set_char_cell(char.c)
		accessible_cells = get_all_accessible_cells()
		accessible_cells.pop(0)  # remove char cell
		finish_cell = accessible_cells.pop()
		map[finish_cell] = CELL_FINISH

	if is_gate_puzzle:
		generate_random_solvable_gate_room(accessible_cells, finish_cell)

	if is_color_puzzle:
		for cy in color_puzzle.y_range:
			for cx in color_puzzle.x_range:
				color_map[cx, cy] = COLOR_PUZZLE_VALUE_GREEN
				if is_color_puzzle_plate(cx, cy):
					map[cx, cy] = CELL_PLATE
					color_map[cx, cy] = COLOR_PUZZLE_VALUE_PLATE
		num_tries = 5
		while num_tries > 0:
			for n in range(color_puzzle.size_x * color_puzzle.size_y * 3):
				plate_cx = color_puzzle.x1 + randint(1, int(color_puzzle.size_x / 2)) * 2 - 1
				plate_cy = color_puzzle.y1 + randint(1, int(color_puzzle.size_y / 2)) * 2 - 1
				for i in range(randint(1, get_num_color_puzzle_values() - 1)):
					press_color_puzzle_plate(plate_cx, plate_cy)
			if not is_color_puzzle_solved():
				break
			num_tries -= 1

	# generate enemies
	for i in range(level["num_enemies"] if "num_enemies" in level else DEFAULT_NUM_ENEMIES):
		positioned = False
		num_tries = 10000
		while not positioned and num_tries > 0:
			num_tries -= 1
			cx = randint(room.x1, room.x2)
			cy = randint(room.y1, room.y2)
			positioned = map[cx, cy] not in CELL_ENEMY_PLACE_OBSTACLES
			for other in (enemies + hearts + swords + barrels + [char]):
				if (cx, cy) == other.c:
					positioned = False
		if num_tries == 0:
			print("Was not able to find free spot for enemy in 10000 tries, positioning it anyway on an obstacle")
		enemies.append(create_enemy(cx, cy))

def generate_map():
	global map, color_map

	# currently python3-numpy-1.24.4 has a bug that requires copy() call here
	map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype=str).copy()
	for cy in MAP_Y_RANGE:
		for cx in MAP_X_RANGE:
			if cx == 0 or cx == PLAY_SIZE_X + 1 or cy == 0 or cy == PLAY_SIZE_Y + 1:
				cell_type = CELL_BORDER
			else:
				if is_four_rooms and (cx == ROOM_BORDER_X or cy == ROOM_BORDER_Y):
					cell_type = CELL_BORDER
				else:
					cell_type = get_random_floor_cell_type()
			map[cx, cy] = cell_type

	if is_color_puzzle:
		color_map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype=int)
		color_map.fill(COLOR_PUZZLE_VALUE_OUTSIDE)

	if is_four_rooms:
		for idx in range(4):
			generate_room(idx)
	else:
		generate_room(None)

def set_theme(theme_name):
	global cell_images, status_image, cloud_image, color_cell_images
	global theme_prefix

	theme_prefix = theme_name + '/'
	image1 = create_theme_image('border')
	image2 = create_theme_image('floor')
	image3 = create_theme_image('crack')
	image4 = create_theme_image('bones')
	image5 = create_theme_image('rocks')
	image6 = create_theme_image('plate') if is_color_puzzle or is_barrel_puzzle or is_gate_puzzle else None
	image7 = create_theme_image('start') if has_start or is_stoneage_puzzle else None
	image8 = create_theme_image('finish') if has_finish or is_stoneage_puzzle or is_gate_puzzle else None
	image9 = create_theme_image('portal') if is_stoneage_puzzle else None
	image10 = create_theme_image('gate0') if is_stoneage_puzzle or is_gate_puzzle else None
	image11 = create_theme_image('gate1') if is_stoneage_puzzle or is_gate_puzzle else None
	image12 = create_theme_image('sand') if is_stoneage_puzzle else None
	image13 = Actor(theme_prefix + 'lift') if is_stoneage_puzzle else None
	image14 = Actor(theme_prefix + 'lifth') if is_stoneage_puzzle else None
	image15 = Actor(theme_prefix + 'liftv') if is_stoneage_puzzle else None
	image16 = Actor(theme_prefix + 'liftu') if is_stoneage_puzzle else None
	image17 = Actor(theme_prefix + 'liftd') if is_stoneage_puzzle else None
	image18 = Actor(theme_prefix + 'liftl') if is_stoneage_puzzle else None
	image19 = Actor(theme_prefix + 'liftr') if is_stoneage_puzzle else None
	status_image = create_theme_image('status')
	cloud_image = create_theme_image('cloud') if is_cloud_mode and not bg_image else None

	if is_color_puzzle:
		gray_alpha_image = pygame.image.load('images/' + theme_prefix + 'floor_gray_alpha.png').convert_alpha()
		color_cell_images = []
		for color in COLOR_PUZZLE_RGB_VALUES:
			color_cell_image = pygame.Surface((CELL_W, CELL_H))
			color_cell_image.fill(color)
			color_cell_image.blit(gray_alpha_image, (0, 0))
			color_cell_images.append(color_cell_image)

	cell_images = {
		CELL_BORDER: image1,
		CELL_FLOOR:  image2,
		CELL_CRACK:  image3,
		CELL_BONES:  image4,
		CELL_ROCKS:  image5,
		CELL_PLATE:  image6,
		CELL_START:  image7,
		CELL_FINISH: image8,
		CELL_PORTAL: image9,
		CELL_GATE0:  image10,
		CELL_GATE1:  image11,
		CELL_SAND:   image12,
		CELL_LIFT:   image13,
		CELL_LIFTH:  image14,
		CELL_LIFTV:  image15,
		CELL_LIFTU:  image16,
		CELL_LIFTD:  image17,
		CELL_LIFTL:  image18,
		CELL_LIFTR:  image19,
	}

def start_music():
	global is_music_started

	if mode != "game" and mode != "end":
		print("Called start_music outside of game or end")
		return

	is_music_started = True

	if is_music_enabled:
		track = level["music"] if mode == "game" else "victory" if is_game_won else "defeat"
		music.play(track)

def stop_music():
	global is_music_started

	is_music_started = False

	if is_music_enabled:
		music.stop()

def enable_music():
	global is_music_enabled

	if is_music_enabled:
		return

	is_music_enabled = True

	if is_music_started:
		start_music()

def disable_music():
	global is_music_enabled, is_music_started

	if not is_music_enabled:
		return

	if is_music_started:
		stop_music()
		is_music_started = True

	is_music_enabled = False

def play_sound(name):
	if not is_sound_enabled:
		return

	sound = getattr(sounds, name)
	sound.play()

def reset_level_and_target_timer():
	global level_title_timer, level_target_timer

	level_title_timer = 4 * 60  # 4 seconds
	level_target_timer = 3 * 60  # 3 seconds

def clear_level_and_target_timer():
	global level_title_timer, level_target_timer

	level_title_timer = 0
	level_target_timer = 0

def reset_idle_time():
	global idle_time, last_autogeneration_time

	idle_time = 0
	last_autogeneration_time = 0

def init_new_level(offset=1, reload_stored=False):
	global level_idx, level, level_time, mode, is_game_won
	global is_random_maze, is_spiral_maze, is_grid_maze, is_any_maze
	global is_stoneage_puzzle, is_barrel_puzzle, is_color_puzzle
	global is_gate_puzzle
	global has_start, has_finish
	global bg_image
	global is_cloud_mode, revealed_map
	global is_four_rooms, char_cell, room_idx
	global num_bonus_health, num_bonus_attack
	global enemies, barrels, killed_enemies, hearts, swords, level_time
	global map, color_map, stored_level

	if reload_stored and offset != 0:
		print("Can't reload a non-current level")
		quit()

	if level_idx + offset < 0 or level_idx + offset > len(levels):
		print("Requested level is out of range")
		return

	stop_music()
	clear_level_and_target_timer()
	mode = "init"

	level_idx += offset
	if level_idx == len(levels):
		mode = "end"
		is_game_won = True
		start_music()
		return

	level = levels[level_idx]
	is_random_maze = "random_maze" in level
	is_spiral_maze = "spiral_maze" in level
	is_grid_maze = "grid_maze" in level
	is_any_maze = is_random_maze or is_spiral_maze or is_grid_maze
	is_stoneage_puzzle = "stoneage_puzzle" in level and not is_any_maze
	is_barrel_puzzle = "barrel_puzzle" in level and not is_any_maze and not is_stoneage_puzzle
	is_color_puzzle = "color_puzzle" in level and not is_any_maze and not is_barrel_puzzle and not is_stoneage_puzzle
	is_four_rooms = "four_rooms" in level
	is_cloud_mode = "cloud_mode" in level
	is_gate_puzzle = "gate_puzzle" in level and is_any_maze
	has_start = "has_start" in level
	has_finish = "has_finish" in level

	bg_image = None
	if "bg_image" in level:
		bg_image = pygame.image.load(level["bg_image"]).convert()
		bg_image = pygame.transform.scale(bg_image, (MAP_W, MAP_H))

	char_cell = None
	char.health = level["char_health"]
	char.attack = INITIAL_CHAR_ATTACK

	hearts = []
	swords = []
	barrels = []
	enemies = []
	killed_enemies = []
	num_bonus_health = 0
	num_bonus_attack = 0

	set_theme(level["theme"])
	if reload_stored:
		map = stored_level["map"]
		color_map = stored_level["color_map"]
		for enemy_info in stored_level["enemy_infos"]:
			enemies.append(create_enemy(*enemy_info))
		for barrel_cell in stored_level["barrel_cells"]:
			create_barrel(barrel_cell)
	else:
		generate_map()

	if "target" not in level:
		level["target"] = "default-level-target"

	level_time = 0
	reset_idle_time()
	if is_level_intro_enabled:
		reset_level_and_target_timer()

	room_idx = 0 if is_four_rooms else None
	set_room(room_idx)

	if reload_stored:
		char_cell = stored_level["char_cell"]
	if char_cell:
		set_actor_coord(char, *char_cell)
	else:
		place_char_in_first_free_spot()

	if is_cloud_mode:
		revealed_map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype=bool)
		revealed_map.fill(False)
	reveal_map_near_char()

	mode = "game"
	start_music()

	stored_level = {
		"map": map.copy(),
		"color_map": color_map.copy() if is_color_puzzle else None,
		"char_cell": char.c,
		"enemy_infos": tuple((enemy.cx, enemy.cy, enemy.health, enemy.attack, enemy.bonus) for enemy in enemies),
		"barrel_cells": tuple(barrel.c for barrel in barrels),
	}

def init_new_room():
	global room_idx, mode

	if is_four_rooms:
		room_idx += 1

	if not is_four_rooms or room_idx == 4:
		init_new_level()
	else:
		set_room(room_idx)
		place_char_in_first_free_spot()
		reveal_map_near_char()
		mode = "game"

def draw_map():
	for cy in range(len(map[0])):
		for cx in range(len(map)):
			cell_type = map[cx, cy]
			cell_types = [cell_type]
			if cell_type in CELL_FLOOR_EXTENSIONS and cell_type != CELL_FLOOR:
				cell_types.insert(0, CELL_FLOOR)
			for cell_type in cell_types:
				if is_cloud_mode and not revealed_map[cx, cy]:
					if bg_image:
						continue
					cell_image = cloud_image
				elif cell_type == CELL_VOID:
					continue
				elif is_color_puzzle and cell_type == CELL_FLOOR and color_map[cx, cy] not in (COLOR_PUZZLE_VALUE_OUTSIDE, COLOR_PUZZLE_VALUE_PLATE):
					color_floor = get_color_puzzle_image(cx, cy)
					screen.blit(color_floor, (CELL_W * cx, CELL_H * cy))
					continue
				elif cell_type in cell_images:
					cell_image = cell_images[cell_type]
				else:
					screen.draw.text(cell_type, center=get_map_cell_pos(cx, cy), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=1, fontsize=48)
					continue
				cell_image.left = CELL_W * cx
				cell_image.top = CELL_H * cy
				cell_image.draw()

def get_time_str(time):
	sec = int(time)
	min = sec / 60
	sec = sec % 60
	return "%d:%02d" % (min, sec) if min < 60 else "%d:%02d:%02d" % (min / 60, min % 60, sec)

def draw_status():
	cy = MAP_SIZE_Y
	for cx in MAP_X_RANGE:
		status_image.left = CELL_W * cx
		status_image.top = CELL_H * cy
		status_image.draw()
	status_heart.draw()
	screen.draw.text(str(num_bonus_health), center=(POS_CENTER_X - 1 * CELL_W / 2, POS_STATUS_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=1, fontsize=24)
	status_sword.draw()
	screen.draw.text(str(num_bonus_attack), center=(POS_CENTER_X + 2 * CELL_W / 2, POS_STATUS_Y), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=1, fontsize=24)
	if mode == "game":
		color, gcolor = ("#60C0FF", "#0080A0") if "time_limit" not in level else ("#FFC060", "#A08000") if level["time_limit"] - level_time > CRITICAL_REMAINING_LEVEL_TIME else ("#FF6060", "#A04040")
		time_str = get_time_str(level_time if "time_limit" not in level else level["time_limit"] - level_time)
		screen.draw.text(time_str, midright=(WIDTH - 20, POS_STATUS_Y), color=color, gcolor=gcolor, owidth=1.2, ocolor="#404030", alpha=1, fontsize=27)

def draw_central_flash():
	msg_surface = pygame.Surface((WIDTH, 120))
	msg_surface.set_alpha(50)
	msg_surface.fill((0, 40, 40))
	screen.blit(msg_surface, (0, POS_CENTER_Y - 60))

def draw():
	screen.fill("#2f3542")
	if bg_image:
		screen.blit(bg_image, (MAP_POS_X1, MAP_POS_Y1))
	if mode == "game" or mode == "end" or mode == "next":
		visible_barrels = get_revealed_actors(barrels)
		visible_enemies = get_revealed_actors(enemies)
		draw_map()
		draw_status()
		for barrel in visible_barrels:
			barrel.draw()
		for enemy in killed_enemies:
			enemy.draw()
		for enemy in visible_enemies:
			enemy.draw()
		for heart in hearts:
			heart.draw()
		for sword in swords:
			sword.draw()
		char.draw()
		for actor in visible_enemies + [char]:
			if actor.health is None:
				continue
			screen.draw.text(str(actor.health), center=apply_diff(actor.pos, (-12, -CELL_H * 0.5 - 14)), color="#AAFF00", gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.8, fontsize=24)
			screen.draw.text(str(actor.attack), center=apply_diff(actor.pos, (+12, -CELL_H * 0.5 - 14)), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=0.8, fontsize=24)

	if mode == "end":
		end_line = _('victory-text') if is_game_won else _('defeat-text')
		draw_central_flash()
		screen.draw.text(end_line, center=(POS_CENTER_X, POS_CENTER_Y), color='white', gcolor=("#008080" if is_game_won else "#800000"), owidth=0.8, ocolor="#202020", alpha=1, fontsize=60)

	if mode == "game" and level_title_timer > 0:
		draw_central_flash()
		level_line_1 = _('level-label') + " " + str(level["n"])
		level_line_2 = _('level-' + str(level["n"]) + '-name')
		screen.draw.text(level_line_1, center=(POS_CENTER_X, POS_CENTER_Y - 20), color='yellow', gcolor="#AAA060", owidth=1.2, ocolor="#404030", alpha=1, fontsize=50)
		screen.draw.text(level_line_2, center=(POS_CENTER_X, POS_CENTER_Y + 18), color='white', gcolor="#C08080", owidth=1.2, ocolor="#404030", alpha=1, fontsize=32)
	elif mode == "game" and level_target_timer > 0:
		target_line = _('level-target-label') + ": " + _(level["target"])
		draw_central_flash()
		screen.draw.text(target_line, center=(POS_CENTER_X, POS_CENTER_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=1, fontsize=40)

	if mode == "init":
		screen.fill("#a8b6b7")
		screen.draw.text(_("Initializing level…"), center=(POS_CENTER_X, POS_CENTER_Y), color='#FFFFFF', gcolor="#88AA66", owidth=1.2, ocolor="#404030", alpha=1, fontsize=80)

def kill_enemy():
	enemy = killed_enemies.pop(0)

def on_key_down(key):
	global lang
	global is_move_animate_enabled, is_level_intro_enabled, is_sound_enabled

	reset_idle_time()

	if mode != "game" and mode != "end" and mode != "next":
		return

	if keyboard.rshift:
		if keyboard.e:
			lang = 'en'
		if keyboard.r:
			lang = 'ru'
		if keyboard.h:
			lang = 'he'

		if keyboard.l:
			is_level_intro_enabled = not is_level_intro_enabled
			if is_level_intro_enabled:
				reset_level_and_target_timer()
			else:
				clear_level_and_target_timer()
		return

	if keyboard.k_0:
		set_theme("classic")
	if keyboard.k_1:
		set_theme("ancient1")
	if keyboard.k_2:
		set_theme("modern1")
	if keyboard.k_3:
		set_theme("modern2")
	if keyboard.k_4:
		set_theme("stoneage1")
	if keyboard.k_5:
		set_theme("stoneage2")

	if keyboard.p:
		init_new_level(-1)
	if keyboard.r:
		init_new_level(0, bool(keyboard.lalt))
	if keyboard.n:
		init_new_level(+1)

	if keyboard.l:
		reset_level_and_target_timer()

	if keyboard.m:
		if is_music_enabled:
			disable_music()
		else:
			enable_music()

	if keyboard.s:
		is_sound_enabled = not is_sound_enabled

	if keyboard.a:
		is_move_animate_enabled = not is_move_animate_enabled

	if keyboard.q:
		quit()

	if keyboard.space and is_color_puzzle and map[char.c] == CELL_PLATE:
		press_color_puzzle_plate(*char.c)
		if is_color_puzzle_solved():
			win_room()

	if keyboard.space and is_gate_puzzle and map[char.c] == CELL_PLATE:
		press_gate_puzzle_plate()

def loose_game():
	global mode, is_game_won

	stop_music()
	mode = "end"
	is_game_won = False
	start_music()

def win_room():
	global mode

	play_sound("finish")
	mode = "next"
	clock.schedule(init_new_room, 1.5)

def check_victory():
	if mode != "game":
		return

	if "time_limit" in level and level_time > level["time_limit"]:
		loose_game()
	elif char.health is not None and char.health <= MIN_CHAR_HEALTH:
		loose_game()
	elif is_barrel_puzzle:
		if is_barrel_puzzle_solved():
			win_room()
	elif has_finish or is_gate_puzzle:
		if map[char.c] == CELL_FINISH:
			win_room()
	elif is_stoneage_puzzle or is_color_puzzle:
		pass
	elif not sum(1 for enemy in enemies if is_actor_in_room(enemy)) and not killed_enemies:
		win_room()

def move_char(diff_x, diff_y):
	diff = (diff_x, diff_y)
	undo_diff = (-diff_x, -diff_y)

	old_char_pos = char.pos
	old_char_cell = char.c
	# try to move forward, and prepare to cancel if the move is impossible
	move_actor(char, diff)

	# collision with enemies
	enemy_index = char.collidelist(enemies)
	if enemy_index >= 0:
		enemy = enemies[enemy_index]
		enemy.health -= char.attack
		char.health -= enemy.attack
		enemy.pos = get_actor_pos(enemy)
		# can't move if we face enemy, cancel the move
		move_actor(char, undo_diff)
		# animate beat or kill
		enemy.pos = apply_actor_pos_diff(enemy, (diff_x * 12, diff_y * 12))
		if enemy.health > 0:
			play_sound("beat")
			animate(enemy, tween='bounce_end', duration=0.4, pos=get_actor_pos(enemy))
		else:
			play_sound("kill")
			enemies.remove(enemy)
			# fallen bonuses upon enemy death
			if enemy.bonus == BONUS_HEALTH:
				heart = create_actor('heart', *enemy.c)
				hearts.append(heart)
			elif enemy.bonus == BONUS_ATTACK:
				sword = create_actor('sword', *enemy.c)
				swords.append(sword)
			enemy.angle = (randint(-1, 1) + 2) * 90
			killed_enemies.append(enemy)
			clock.schedule(kill_enemy, 0.3)
		return

	# collision with barrels
	barrel_index = char.collidelist(barrels)
	if barrel_index >= 0:
		barrel = barrels[barrel_index]
		if not is_cell_accessible(barrel.cx + diff_x, barrel.cy + diff_y):
			# can't push, cancel the move
			move_actor(char, undo_diff)
			return
		else:
			# can push, animate the push
			old_barrel_pos = barrel.pos
			move_actor(barrel, diff)
			new_barrel_pos = barrel.pos
			if is_move_animate_enabled:
				barrel.pos = old_barrel_pos
				animate(barrel, duration=ARROW_KEYS_RESOLUTION, pos=new_barrel_pos)

	# can move, animate the move
	animate_time_factor = 1

	# process lift movement if available
	if lift_target := get_lift_target(old_char_cell, diff):
		distance = get_distance(old_char_cell, lift_target)
		for i in range(1, distance):
			move_actor(char, diff)
		map[lift_target] = map[old_char_cell]
		map[old_char_cell] = CELL_VOID
		if is_move_animate_enabled:
			pass
		animate_time_factor = distance - (distance - 1) / 2

	new_char_pos = char.pos
	if is_move_animate_enabled:
		char.pos = old_char_pos
		animate(char, duration=animate_time_factor * ARROW_KEYS_RESOLUTION, pos=new_char_pos)

	if map[old_char_cell] == CELL_SAND:
		map[old_char_cell] = CELL_VOID

	reveal_map_near_char()

def update(dt):
	global level_title_timer, level_target_timer, num_bonus_health, num_bonus_attack
	global game_time, level_time, idle_time, last_autogeneration_time
	global last_time_arrow_keys_processed, last_processed_arrow_keys

	if mode == 'start':
		init_new_level()
		return

	game_time += dt
	level_time += dt
	idle_time += dt

	if level_title_timer > 0:
		level_title_timer -= 1
	elif level_target_timer > 0:
		level_target_timer -= 1

	if char.health is not None and (
		last_autogeneration_time == 0 and idle_time >= AUTOGENERATION_IDLE_TIME or
		last_autogeneration_time != 0 and idle_time >= last_autogeneration_time + AUTOGENERATION_NEXT_TIME
	):
		char.health += AUTOGENERATION_HEALTH
		if char.health > level["char_health"]:
			char.health = level["char_health"]
		last_autogeneration_time = idle_time

	check_victory()

	for i in range(len(hearts)):
		if char.colliderect(hearts[i]):
			char.health += BONUS_HEALTH_VALUE
			hearts.pop(i)
			num_bonus_health -= 1
			break

	for i in range(len(swords)):
		if char.colliderect(swords[i]):
			char.attack += BONUS_ATTACK_VALUE
			swords.pop(i)
			num_bonus_attack -= 1
			break

	keys = pygame.key.get_pressed()
	for key in (ARROW_KEY_R, ARROW_KEY_L, ARROW_KEY_D, ARROW_KEY_U):
		if keys[key] and key not in pressed_arrow_keys:
			pressed_arrow_keys.append(key)
			reset_idle_time()
		if not keys[key] and key in pressed_arrow_keys and key in last_processed_arrow_keys:
			pressed_arrow_keys.remove(key)

	if game_time - last_time_arrow_keys_processed < ARROW_KEYS_RESOLUTION:
		return

	last_time_arrow_keys_processed = game_time
	last_processed_arrow_keys = []

	def set_arrow_key_to_process(key, diff):
		if not ALLOW_DIAGONAL_MOVES and last_processed_arrow_keys:
			return
		pressed_arrow_keys.remove(key)
		if map[char.cx + diff[0], char.cy + diff[1]] not in CELL_CHAR_MOVE_OBSTACLES or get_lift_target(char.c, diff):
			last_processed_arrow_keys.append(key)

	for key in list(pressed_arrow_keys):
		if key == ARROW_KEY_R and key not in last_processed_arrow_keys and ARROW_KEY_L not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (+1, +0))
		if key == ARROW_KEY_L and key not in last_processed_arrow_keys and ARROW_KEY_R not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (-1, +0))
		if key == ARROW_KEY_D and key not in last_processed_arrow_keys and ARROW_KEY_U not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (+0, +1))
		if key == ARROW_KEY_U and key not in last_processed_arrow_keys and ARROW_KEY_D not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (+0, -1))

	diff_x = 0
	diff_y = 0

	if ARROW_KEY_R in last_processed_arrow_keys:
		diff_x += 1
		char.image = 'stand'
	if ARROW_KEY_L in last_processed_arrow_keys:
		diff_x -= 1
		char.image = 'left'
	if ARROW_KEY_D in last_processed_arrow_keys:
		diff_y += 1
	if ARROW_KEY_U in last_processed_arrow_keys:
		diff_y -= 1

	if diff_x or diff_y:
		move_char(diff_x, diff_y)
