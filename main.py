import os
import io
import random
import pygame
import pgzero
import builtins
from pgzero.constants import keys
from numpy import ndarray, chararray, array, any
from copy import deepcopy
from random import randint, choice
from constants import *
from leveltools import *
from translations import *
from cellactor import *
from objects import *
from drop import draw_status_drops
from flags import flags
from puzzle import create_puzzle
from sizetools import *
from joystick import scan_joysticks_and_state, emulate_joysticks_press_key, get_joysticks_arrow_keys

lang = 'en'

def die(error):
	print(error)
	quit()

def autodetect_lang():
	global lang

	lang = 'en'
	try:
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

def load_map(filename_or_stringio):
	global map

	is_stringio = type(filename_or_stringio) == io.StringIO
	filename = "<from-string>" if is_stringio else filename_or_stringio

	def print_error(error):
		print("File %s: %s. Ignoring map file" % (filename, error))
		if is_stringio:
			print(filename_or_stringio.getvalue())
		enemies.clear()
		barrels.clear()
		set_char_cell(None, 0)

	if is_stringio:
		file = filename_or_stringio
		if DEBUG_LEVEL >= 2:
			print(filename_or_stringio.getvalue())
	else:
		try:
			file = open(filename, "r")
		except:
			print_error("Failed to open")
			return

	words = file.readline().split(" ")
	if len(words) <= 1:
		print_error("Invalid signature line, no expected space")
		return
	if words[0] != '#' or words[1] != 'Dungeon':
		print_error("Invalid signature line, no expected '# Dungeon'")
		return
	size_str = words[-1].rstrip("\n")
	sizes = size_str.split("x")
	if len(sizes) != 2 or not sizes[0].isdigit() or not sizes[1].isdigit():
		print_error("Invalid signature line, invalid size '%s'" % size_str)
		return
	size_x = int(sizes[0])
	size_y = int(sizes[1])
	if size_x != MAP_SIZE_X or size_y != MAP_SIZE_Y:
		print_error("Invalid size %dx%d instead of %dx%d" % (size_x, size_y, MAP_SIZE_X, MAP_SIZE_Y))
		return

	orig_map = map.copy()

	set_char_cell(None, 0)

	special_cells = []
	for y in range(0, size_y):
		line = file.readline()
		if line == '':
			map = orig_map.copy()
			print_error("Failed to read map line #%d" % (y + 1))
			return
		line = line.rstrip("\n")
		for x in range(0, size_x):
			if len(line) <= x:
				map = orig_map.copy()
				print_error("Failed to read char #%d in map line #%d" % (x + 1, y + 1))
				return
			ch = line[x]
			cell = (x, y)
			if ch == CELL_START:
				set_char_cell(cell, 0)
			if ch in LIFT_TYPES_BY_CHAR:
				create_lift(cell, LIFT_TYPES_BY_CHAR[ch])
				ch = CELL_VOID
			if ch in ACTOR_AND_PLATE_BY_CHAR:
				actor_name, is_plate = ACTOR_AND_PLATE_BY_CHAR[ch]
				ch = CELL_PLATE if is_plate else CELL_FLOOR
				if actor_name == "key1":
					drop_key1.instantiate(cell)
				if actor_name == "key2":
					drop_key2.instantiate(cell)
				if actor_name == "enemy":
					create_enemy(cell)
				if actor_name == "barrel":
					create_barrel(cell)
				if actor_name == "char":
					set_char_cell(cell, 0)
			if ch.isdigit():
				special_cells.append(cell)
			map[x, y] = ch

	special_cell_values = []
	for cell in special_cells:
		line = file.readline()
		if line == '':
			map = orig_map.copy()
			print_error("Failed to read value for special map cell %s" % str(cell))
			return
		special_cell_values.append([cell, line.rstrip("\n")])

	extra_values = []
	while True:
		line = file.readline()
		if line == '':
			break
		extra_values.append(line.rstrip("\n"))

	file.close()

	return (special_cell_values, extra_values)

def is_cell_in_area(cell, x_range, y_range):
	return cell[0] in x_range and cell[1] in y_range

# get 4 neughbour cells for cell
def get_cell_neighbors(cell, x_range=None, y_range=None):
	neighbors = []
	for diff in ((-1, 0), (+1, 0), (0, -1), (0, +1)):
		neigh = apply_diff(cell, diff)
		if x_range is None or y_range is None or is_cell_in_area(neigh, x_range, y_range):
			neighbors.append(neigh)
	debug(3, "* get_cell_neighbors %s - %s" % (str(cell), neighbors))
	return neighbors

# get 4 neughbour cells for actor
def get_actor_neighbors(actor, x_range=None, y_range=None):
	return get_cell_neighbors(actor.c, x_range, y_range)

# get 8 or 9 neughbour cells for cell
def get_all_neighbors(cell, include_self=False):
	neighbors = []
	for dy in (-1, 0, +1):
		for dx in (-1, 0, +1):
			if dy == 0 and dx == 0 and not include_self:
				continue
			neighbors.append(apply_diff(cell, (dx, dy)))
	return neighbors

is_game_won = False
is_music_enabled = True
is_music_started = False
is_sound_enabled = True
is_move_animate_enabled = True
is_level_intro_enabled = True

mode = "start"
is_main_screen = True

puzzle = None

bg_image = None

game_time = 0
level_time = 0
idle_time = 0

last_autogeneration_time = 0

last_time_arrow_keys_processed = 0
pressed_arrow_keys = []
last_processed_arrow_keys = []
last_processed_arrow_diff = (0, 0)

map = None  # will be generated
cell_images = {}  # will be generated
revealed_map = None
theme_prefix = None

def get_drop_on_cell(cell):
	for drop in drops:
		if drop.has_instance(cell):
			return drop
	return None

killed_enemies = []

level_title_time = 0
level_goal_time = 0

level = None

room = Area()
enter_room_idx = None

status_message = None
status_message2 = None
status_message2_time = 0

def set_status_message(msg=None):
	global status_message
	status_message = msg

def set_status_message2(msg=None, duration=10):
	global status_message2, status_message2_time
	status_message2 = msg
	status_message2_time = level_time + (duration if duration is not None else 1000000)

def get_bg_image():
	return bg_image

def debug(level, str, depth=None):
	if DEBUG_LEVEL < level:
		return
	if depth is not None:
		print(" " * depth, end="")
	print(str)

def debug_map(level=0, descr=None, full_format=False, full=True, clean=True, combined=True, dual=False, endl=False):
	if DEBUG_LEVEL < level:
		return
	if descr:
		print(descr)
	if full_format:
		full = True
		combined = True
		dual = False
		print("# Dungeon %s anonymous map %dx%d" % (puzzle.__class__.__name__ if puzzle else "non-puzzle", MAP_SIZE_X, MAP_SIZE_Y))
	for cy in MAP_Y_RANGE if full else PLAY_Y_RANGE:
		if not combined:
			for cx in MAP_X_RANGE if full else PLAY_X_RANGE:
				cell = (cx, cy)
				print(CELL_FLOOR if clean and map[cell] in CELL_FLOOR_TYPES else map[cell], end="")
		if dual:
			print("    ", end="")
		if dual or combined:
			for cx in MAP_X_RANGE if full else PLAY_X_RANGE:
				cell = (cx, cy)
				cell_ch = CELL_FLOOR if clean and map[cell] in CELL_FLOOR_TYPES else map[cell]
				actor_chars = ACTOR_ON_PLATE_CHARS if cell_ch == CELL_PLATE else ACTOR_CHARS
				if drop := get_drop_on_cell(cell):
					cell_ch = actor_chars[drop.name]
				if is_cell_in_actors(cell, enemies):
					cell_ch = actor_chars['enemy']
				if is_cell_in_actors(cell, barrels):
					cell_ch = actor_chars['barrel']
				if lift := get_actor_on_cell(cell, lifts):
					cell_ch = LIFT_CHARS[lift.type]
				if char.c is not None and char.c == cell:
					cell_ch = actor_chars['char']
				print(cell_ch, end="")
		print()
	if full_format:
		for extra_value in puzzle.get_map_extra_values() if puzzle else ():
			line = ' '.join(builtins.map(str, extra_value)) if hasattr(extra_value, '__iter__') else str(extra_value)
			print(line)
	if endl:
		print()

def is_cell_in_map(cell):
	return is_cell_in_area(cell, MAP_X_RANGE, MAP_Y_RANGE)

def is_outer_wall(cell):
	if map[cell] not in CELL_WALLS:
		return False

	for neigh in get_all_neighbors(cell):
		if is_cell_in_map(neigh) and map[neigh] not in CELL_WALLS:
			return False
	return True

def replace_outer_walls(*cell_types):
	for cy in MAP_Y_RANGE:
		for cx in MAP_X_RANGE:
			if map[cx, cy] == CELL_OUTER_WALL:
				map[cx, cy] = choice(cell_types)

def convert_outer_walls(cell_type=None):
	for cy in MAP_Y_RANGE:
		for cx in MAP_X_RANGE:
			if is_outer_wall((cx, cy)):
				map[cx, cy] = CELL_OUTER_WALL

	if cell_type is not None:
		replace_outer_walls(*cell_type)

def convert_outer_floors(cell_type=None):
	floor_cells_to_convert = set()
	for cy in (0, MAP_SIZE_Y - 1):
		for cx in (0, MAP_SIZE_X - 1):
			if map[cx, cy] in CELL_FLOOR_TYPES:
				floor_cells_to_convert.update(get_accessible_cells((cx, cy)))
	for cell in floor_cells_to_convert:
		map[cell] = CELL_OUTER_WALL

	if cell_type is not None:
		replace_outer_walls(cell_type)

def get_theme_image_name(image_name):
	for full_image_name in (theme_prefix + image_name, DEFAULT_IMAGE_PREFIX + image_name):
		if os.path.isfile(IMAGES_DIR_PREFIX + full_image_name + '.png'):
			debug(2, "Found image %s" % full_image_name)
			return full_image_name

	die("Unable to find image %s in neither %s nor %s" % (image_name, theme_prefix, DEFAULT_IMAGE_PREFIX))

def load_image(image_name, size, do_crop=False):
	image = pygame.image.load(image_name).convert()
	if do_crop:
		# image=300x400 size=100x200 -> cropped=200x400
		# image=300x400 size=200x100 -> cropped=300x150
		w = image.get_width()
		h = image.get_height()
		if w * size[1] > h * size[0]:
			crop_w = size[0] * h // size[1]
			crop_h = h
			crop_x = (w - crop_w) // 2
			crop_y = 0
		else:
			crop_w = w
			crop_h = size[1] * w // size[0]
			crop_x = 0
			crop_y = (h - crop_h) // 2
		cropped_image = pygame.Surface((crop_w, crop_h), pygame.SRCALPHA, 32)
		cropped_image.blit(image, (-crop_x, -crop_y))
		image = cropped_image
	return pygame.transform.scale(image, size)

def load_theme_cell_image(image_name):
	return pygame.image.load(IMAGES_DIR_PREFIX + get_theme_image_name(image_name) + '.png').convert_alpha()

def colorize_cell_image(image, color, alpha=1):
	cell_surface = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA, 32)
	cell_surface.fill((*color, alpha * 255))
	cell_surface.blit(image, (0, 0))
	return cell_surface

def create_cell_subimage(image, cell, starting_cell=(0, 0), rotate_angle=0):
	cell_surface = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA, 32)
	cell = apply_diff(cell, starting_cell, subtract=True)
	cell_surface.blit(image, (-cell[0] * CELL_W, -cell[1] * CELL_H))
	if rotate_angle != 0:
		cell_surface = pygame.transform.rotate(cell_surface, rotate_angle)
	return cell_surface

def create_text_cell_image(text, color='#E0E0E0', gcolor="#408080", owidth=1.2, ocolor="#004040", alpha=1, fontsize=48):
	cell_surface = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA, 32)
	pgzero.ptext.draw(text, surf=cell_surface, center=cell_to_pos((0, 0)), color=color, gcolor=gcolor, owidth=owidth, ocolor=ocolor, alpha=alpha, fontsize=fontsize)
	return cell_surface

def get_fade_text_factor(fade_out_time, fade_duration=2, rest_duration=0):
	if level_time > fade_out_time + rest_duration:
		return None
	if level_time > fade_out_time:
		return 0
	if level_time > fade_out_time - fade_duration:
		return (fade_out_time - level_time) / fade_duration
	return 1

def is_portal_destination(cell):
	return cell in {v: k for k, v in portal_destinations.items()}

def is_cell_occupied_except_char(cell):
	if is_cell_in_actors(cell, enemies + barrels):
		return True

	return get_drop_on_cell(cell) is not None

def is_cell_occupied(cell):
	return is_cell_occupied_except_char(cell) or char.c == cell

def is_cell_occupied_for_enemy(cell):
	return map[cell] in CELL_ENEMY_PLACE_OBSTACLES or is_cell_occupied(cell) or is_portal_destination(cell)

def create_theme_image(image_name):
	return CellActor(get_theme_image_name(image_name))

def create_theme_actor(image_name, cell):
	return create_actor(get_theme_image_name(image_name), cell)

def reveal_map_near_char():
	if not flags.is_cloud_mode:
		return

	for cell in get_all_neighbors(char.c, include_self=True):
		revealed_map[cell] = True

def get_revealed_actors(actors):
	if not flags.is_cloud_mode or level.get("actors_always_revealed", False):
		return actors

	revealed_actors = []
	for actor in actors:
		if revealed_map[actor.c]:
			revealed_actors.append(actor)
	return revealed_actors

def assert_room():
	if mode != "game" and mode != "init" and mode != "next":
		die("Called room function when not inside game or init (mode=%s). Fix this bug" % mode)

def set_room(idx):
	room.size = flags.ROOM_SIZE(idx)
	room.size_x = flags.ROOM_SIZE_X[idx]
	room.size_y = flags.ROOM_SIZE_Y[idx]
	room.x1 = flags.ROOM_X1[idx]
	room.x2 = flags.ROOM_X2[idx]
	room.y1 = flags.ROOM_Y1[idx]
	room.y2 = flags.ROOM_Y2[idx]
	room.x_range = flags.ROOM_X_RANGE[idx]
	room.y_range = flags.ROOM_Y_RANGE[idx]
	room.idx = idx

	puzzle.on_set_room(room)

# only to be used by puzzle's restore_level
def advance_room():
	if room.idx + 1 >= flags.NUM_ROOMS:
		return False
	set_room(room.idx + 1)
	return True

def enter_room(idx):
	global mode, char_cells

	set_room(idx)
	set_status_message()
	set_status_message2()

	place_char_in_room()
	char_cells[idx] = char.c  # needed for Alt-R

	reveal_map_near_char()

	char.reset_inplace()
	char.reset_inplace_animation()
	if map[char.c] == CELL_START:
		char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(0, 1), angle=(180, 720), flip=(True, True, 1))

	cursor.reset()

	mode = "game"

	puzzle.on_enter_room()

def get_max_room_distance():
	return get_distance((room.x1, room.y1), (room.x2, room.y2))

def is_actor_in_room(actor):
	assert_room()

	return actor.cx >= room.x1 and actor.cx <= room.x2 and actor.cy >= room.y1 and actor.cy <= room.y2

def get_actors_in_room(actors):
	return [actor for actor in actors if is_actor_in_room(actor)]

def is_cell_in_room(cell):
	return is_cell_in_area(cell, room.x_range, room.y_range)

accessible_obstacles = None

def start_accessible_obstacles():
	global accessible_obstacles
	accessible_obstacles = set()

def clear_accessible_obstacles():
	global accessible_obstacles
	accessible_obstacles0 = accessible_obstacles
	accessible_obstacles = None
	return accessible_obstacles0

def is_cell_accessible(cell, obstacles=None, place=False, allow_enemy=False):
	is_cell_blocked = map[cell] in (CELL_CHAR_PLACE_OBSTACLES if place else CELL_CHAR_MOVE_OBSTACLES)
	if obstacles is not None:
		if accessible_obstacles is not None and cell in obstacles:
			accessible_obstacles.add(cell)
		return False if is_cell_blocked or cell in obstacles else True
	if is_cell_blocked:
		return False
	for actor in barrels if allow_enemy else barrels + enemies:
		if actor.c == cell:
			return False
	return True

def get_accessible_neighbors(cell, obstacles=None, allow_enemy=False, allow_closed_gate=False):
	neighbors = []
	if ALLOW_DIAGONAL_MOVES and False:
		directions = ((-1, -1), (0, -1), (+1, -1), (-1, 0), (+1, 0), (-1, +1), (0, +1), (+1, +1))
	else:
		directions = ((-1, 0), (+1, 0), (0, -1), (0, +1))
	for diff in directions:
		neigh = apply_diff(cell, diff)
		if is_cell_in_room(neigh) and (allow_closed_gate and map[neigh] == CELL_GATE0 or is_cell_accessible(neigh, obstacles, allow_enemy=allow_enemy)):
			neighbors.append(neigh)
	debug(3, "* get_accessible_neighbors %s - %s" % (str(cell), neighbors))
	return neighbors

def get_accessible_cells(start_cell, obstacles=None):
	accessible_cells = []
	unprocessed_cells = [start_cell]
	while unprocessed_cells:
		cell = unprocessed_cells.pop(0)
		accessible_cells.append(cell)
		neigbours = get_accessible_neighbors(cell, obstacles)
		for n in neigbours:
			if n not in accessible_cells and n not in unprocessed_cells:
				unprocessed_cells.append(n)
	return accessible_cells

def get_accessible_cell_distances(start_cell, obstacles=None):
	accessible_cells = []
	accessible_cell_distances = {start_cell: 0}
	unprocessed_cells = [start_cell]
	while unprocessed_cells:
		cell = unprocessed_cells.pop(0)
		accessible_distance = accessible_cell_distances[cell]
		accessible_cells.append(cell)
		neigbours = get_accessible_neighbors(cell, obstacles)
		for n in neigbours:
			if n not in accessible_cells and n not in unprocessed_cells:
				unprocessed_cells.append(n)
				accessible_cell_distances[n] = accessible_distance + 1
	return accessible_cell_distances

def get_all_accessible_cells():
	return get_accessible_cells(char.c)

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

def find_path(start_cell, target_cell, obstacles=None):
	if start_cell == target_cell:
		return []
	accessible_cell_distances = get_accessible_cell_distances(start_cell, obstacles)
	accessible_distance = accessible_cell_distances.get(target_cell)
	if accessible_distance is None:
		return None
	path_cells = [target_cell]
	current_cell = target_cell
	while accessible_distance > 1:
		accessible_distance -= 1
		for neigh_cell in get_accessible_neighbors(current_cell, obstacles):
			neigh_distance = accessible_cell_distances.get(neigh_cell)
			if neigh_distance == accessible_distance:
				current_cell = neigh_cell
				path_cells.insert(0, neigh_cell)
				break
	return path_cells

def is_path_found(start_cell, target_cell, obstacles=None):
	return target_cell in get_accessible_cells(start_cell, obstacles)

def set_char_cell(cell, room_idx=None):
	global char_cells

	char_cells[room.idx if room_idx is None else room_idx] = cell

def get_closest_accessible_cell(start_cell, target_cell):
	accessible_cells = get_accessible_cells(start_cell)
	return min(accessible_cells, key=lambda cell: get_distance(cell, target_cell))

def get_topleft_accessible_cell(start_cell):
	return get_closest_accessible_cell(start_cell, (0, 0))

def place_char_in_closest_accessible_cell(target_cell):
	char.c = get_closest_accessible_cell(char.c, target_cell)

def place_char_in_topleft_accessible_cell():
	char.c = get_topleft_accessible_cell(char.c)

def place_char_in_first_free_spot():
	for cell in room.cells:
		if is_cell_accessible(cell, place=True):
			char.c = cell
			return

	if lifts:
		char.c = get_actors_in_room(lifts)[0].c
		return

	print("Was not able to find free spot for char, fix the level or a bug")
	if DEBUG_LEVEL:
		char.c = (0, 0)
	else:
		quit()

def place_char_in_room():
	if char_cells[room.idx]:
		char.c = char_cells[room.idx]
	else:
		place_char_in_first_free_spot()

def get_random_floor_cell_type():
	return CELL_FLOOR_TYPES_FREQUENT[randint(0, len(CELL_FLOOR_TYPES_FREQUENT) - 1)]

def convert_to_floor_if_needed(cx, cy):
	if map[cx, cy] in (*CELL_WALLS, CELL_VOID, CELL_INTERNAL1):
		map[cx, cy] = get_random_floor_cell_type()

def get_random_even_point(a1, a2):
	return a1 + randint(0, int((a2 - a1) / 2)) * 2

def generate_random_maze_area(x1, y1, x2, y2):
	if x2 - x1 <= 1 or y2 - y1 <= 1:
		return

	# select random point that will divide the area into 4 sub-areas
	random_x = get_random_even_point(x1 + 1, x2 - 1)
	random_y = get_random_even_point(y1 + 1, y2 - 1)

	# create the horizontal and vertical wall via this point
	for x in range(x1, x2 + 1):
		map[x, random_y] = CELL_WALL
	for y in range(y1, y2 + 1):
		map[random_x, y] = CELL_WALL

	# select 3 random holes on the 4 just created wall walls
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
				map[cx, cy] = CELL_WALL

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
			map[pointer] = CELL_WALL

		if dir % 2 == 0:
			len[0] -= 2
			len[1] -= 2
		dir = (dir + 1) % 4

def generate_random_maze_room():
	generate_random_maze_area(room.x1, room.y1, room.x2, room.y2)

def generate_random_free_path(target_c, deviation=0, level=0):
	global map

	if randint(0, deviation) == 0:
		place_char_in_closest_accessible_cell(target_c)

	if char.c == target_c:
		return True

	ox, oy = char.c
	tx, ty = target_c

	debug(2, "* [%d] generating free path from (%d, %d) to (%d, %d)" % (level, ox, oy, tx, ty))

	max_distance = get_max_room_distance()

	accessible_cells = get_all_accessible_cells()
	weighted_neighbors = []
	for cell in get_actor_neighbors(char, room.x_range, room.y_range):
		if cell in accessible_cells:
			continue
		if is_cell_in_actors(cell, barrels):
			continue
		cx, cy = cell
		weight = randint(0, max_distance)
		weight -= get_distance(cx, cy, tx, ty)
		if map[cell] in CELL_FLOOR_TYPES:
			weight -= randint(0, max_distance)
		weighted_neighbors.append((weight, cell))

	neighbors = [n[1] for n in sorted(weighted_neighbors, reverse=True)]

	if not neighbors:
		debug(2, "* [%d] failed to generate free path from (%d, %d) to (%d, %d)" % (level, ox, oy, tx, ty))
		return False

	for neigh in neighbors:
		old_cell_type = map[neigh]
		if old_cell_type not in (*CELL_WALLS, CELL_VOID):
			print("BUG!")
			return False
		convert_to_floor_if_needed(*neigh)
		char.c = neigh
		debug(3, "* [%d] trying to move to %s" % (level, str(neigh)))
		debug_map(3, full=True, clean=True, combined=True)
		is_path_found = generate_random_free_path(target_c, deviation, level + 1)
		if is_path_found:
			debug(2, "* [%d] successfully generated free path from (%d, %d) to (%d, %d)" % (level, ox, oy, tx, ty))
			if level == 0:
				debug_map(2, full=True, clean=True, combined=True)
			return True
		map[neigh] = old_cell_type

	char.c = (ox, oy)

	return False

def create_barrel(cell):
	global barrels

	barrel = create_theme_actor("barrel", cell)
	barrels.append(barrel)

def get_random_floor_cell():
	while True:
		cell = randint(room.x1, room.x2), randint(room.y1, room.y2)
		if map[cell] in CELL_FLOOR_TYPES:
			return cell

def replace_random_floor_cell(cell_type, num=1, callback=None, extra=None, extra_num=None):
	for n in range(num):
		cell = get_random_floor_cell()
		map[cell] = cell_type
		extra_cells = []
		if extra_num:
			for i in range(extra_num):
				extra_cell = get_random_floor_cell()
				map[extra_cell] = cell_type
				extra_cells.append(extra_cell)
		if callback:
			if extra is not None:
				callback(cell, extra, *extra_cells)
			else:
				callback(cell, *extra_cells)

def create_portal(cell, dst_cell):
	if cell == dst_cell:
		die("BUG: Portal destination can't be the same cell %s, exiting" % str(cell))

	map[cell] = CELL_PORTAL
	portal_destinations[cell] = dst_cell

def create_portal_pair(cell1, cell2):
	create_portal(cell1, cell2)
	create_portal(cell2, cell1)

def create_lift(cell, type, surface=None):
	global lifts

	image_name = "lift" + type
	lift = create_actor(surface, cell) if surface else create_theme_actor(image_name, cell)
	lift.type = type
	lifts.append(lift)

def get_lift_target(cell, diff):
	lift = get_actor_on_cell(cell, lifts)
	if not lift or diff not in LIFT_TYPE_DIRECTIONS[lift.type]:
		return None
	while True:
		next_cell = apply_diff(cell, diff)
		if not is_cell_in_room(next_cell) or map[next_cell] != CELL_VOID or is_cell_in_actors(next_cell, lifts):
			return cell if cell != lift.c else None
		cell = next_cell

def get_lift_target_at_neigh(lift, neigh):
	return get_lift_target(lift.c, cell_diff(lift.c, neigh))

def create_enemy(cell, health=None, attack=None, drop=None):
	global enemies

	enemy = create_actor("skeleton", cell)
	enemy.power  = health if char.power else None
	enemy.health = None if char.power else health if health is not None else randint(MIN_ENEMY_HEALTH, MAX_ENEMY_HEALTH)
	enemy.attack = None if char.power else attack if attack is not None else randint(MIN_ENEMY_ATTACK, MAX_ENEMY_ATTACK)
	enemy.drop   = None if char.power else drop   if drop   is not None else (None, drop_heart, drop_sword)[randint(0, 2)]
	if enemy.drop:
		enemy.drop.contain(enemy)
	enemies.append(enemy)

class Globals:
	is_cell_in_area = is_cell_in_area
	get_actor_neighbors = get_actor_neighbors
	get_all_neighbors = get_all_neighbors
	set_status_message = set_status_message
	set_status_message2 = set_status_message2
	get_bg_image = get_bg_image
	debug = debug
	debug_map = debug_map
	is_cell_in_map = is_cell_in_map
	convert_outer_walls = convert_outer_walls
	convert_outer_floors = convert_outer_floors
	load_image = load_image
	load_theme_cell_image = load_theme_cell_image
	colorize_cell_image = colorize_cell_image
	create_cell_subimage = create_cell_subimage
	create_text_cell_image = create_text_cell_image
	get_fade_text_factor = get_fade_text_factor
	is_cell_occupied = is_cell_occupied
	advance_room = advance_room
	get_max_room_distance = get_max_room_distance
	is_actor_in_room = is_actor_in_room
	is_cell_in_room = is_cell_in_room
	get_actors_in_room = get_actors_in_room
	start_accessible_obstacles = start_accessible_obstacles
	clear_accessible_obstacles = clear_accessible_obstacles
	get_accessible_neighbors = get_accessible_neighbors
	get_accessible_cells = get_accessible_cells
	get_all_accessible_cells = get_all_accessible_cells
	get_num_accessible_target_directions = get_num_accessible_target_directions
	find_path = find_path
	is_path_found = is_path_found
	set_char_cell = set_char_cell
	place_char_in_topleft_accessible_cell = place_char_in_topleft_accessible_cell
	get_random_floor_cell_type = get_random_floor_cell_type
	convert_to_floor_if_needed = convert_to_floor_if_needed
	generate_random_free_path = generate_random_free_path
	create_barrel = create_barrel
	get_random_floor_cell = get_random_floor_cell
	replace_random_floor_cell = replace_random_floor_cell
	create_portal = create_portal
	create_portal_pair = create_portal_pair
	create_lift = create_lift
	get_lift_target_at_neigh = get_lift_target_at_neigh
	create_enemy = create_enemy

def generate_room(idx):
	set_room(idx)

	if flags.is_random_maze:
		generate_random_maze_room()

	if flags.is_spiral_maze:
		generate_spiral_maze()

	if flags.is_grid_maze:
		generate_grid_maze()

	accessible_cells = None
	finish_cell = None
	if flags.has_finish or puzzle.is_finish_cell_required():
		char.c = (room.x1, room.y1)
		set_char_cell(char.c)
		if flags.has_start:
			map[char.c] = CELL_START
		accessible_cells = get_all_accessible_cells()
		accessible_cells.pop(0)  # remove char cell
		finish_cell = accessible_cells.pop()
		map[finish_cell] = CELL_FINISH
		puzzle.set_finish_cell(accessible_cells, finish_cell)

	puzzle.generate_room()

	# generate enemies
	if char.power:
		return
	for i in range(level["num_enemies"] if "num_enemies" in level else DEFAULT_NUM_ENEMIES):
		place_char_in_room()
		num_tries = 10000
		while num_tries > 0:
			cx = randint(room.x1, room.x2)
			cy = randint(room.y1, room.y2)
			if not is_cell_occupied_for_enemy((cx, cy)):
				break
			num_tries -= 1
		if num_tries == 0:
			print("Was not able to find free spot for enemy in 10000 tries, positioning it anyway on an obstacle")
		create_enemy((cx, cy))

def generate_map():
	global map

	map = chararray((MAP_SIZE_X, MAP_SIZE_Y), itemsize=5, unicode=True)
	bw = 0 if flags.MULTI_ROOMS and not puzzle.has_border() else 1
	for cy in MAP_Y_RANGE:
		for cx in MAP_X_RANGE:
			if cx == PLAY_X1 - bw or cx == PLAY_X2 + bw or cy == PLAY_Y1 - bw or cy == PLAY_Y2 + bw:
				cell_type = CELL_WALL
			else:
				if cx in flags.ROOM_BORDERS_X or cy in flags.ROOM_BORDERS_Y:
					cell_type = CELL_WALL
				else:
					cell_type = get_random_floor_cell_type()
			map[cx, cy] = cell_type

	if "map_file" in level or "map_string" in level:
		if ret := load_map(level.get("map_file") or io.StringIO(level["map_string"])):
			if flags.MULTI_ROOMS:
				print("Ignoring multi-room level config when loading map")
			puzzle.on_create_map(map)
			set_room(0)
			puzzle.on_load_map(*ret)
			return

	puzzle.on_create_map(map)

	for idx in range(flags.NUM_ROOMS):
		generate_room(idx)

	puzzle.on_generate_map()

def set_theme(theme_name):
	global cell_images, status_image, cloud_image
	global barrels
	global theme_prefix

	theme_prefix = theme_name + '/'
	image1 = create_theme_image('wall')
	image2 = create_theme_image('floor')
	image3 = create_theme_image('crack')
	image4 = create_theme_image('bones')
	image5 = create_theme_image('rocks')
	image6 = create_theme_image('plate')  if puzzle.has_plate() else None
	image7 = create_theme_image('start')  if flags.has_start or puzzle.has_start() else None
	image8 = create_theme_image('finish') if flags.has_finish or puzzle.has_finish() else None
	image9 = create_theme_image('portal') if puzzle.has_portal() else None
	image10 = create_theme_image('gate0') if puzzle.has_gate() else None
	image11 = create_theme_image('gate1') if puzzle.has_gate() else None
	image12 = create_theme_image('sand')  if puzzle.has_sand() else None
	image13 = create_theme_image('lock1') if puzzle.has_locks() else None
	image14 = create_theme_image('lock2') if puzzle.has_locks() else None
	image15 = create_theme_image('dirl')  if puzzle.has_dirs() else None
	image16 = create_theme_image('dirr')  if puzzle.has_dirs() else None
	image17 = create_theme_image('diru')  if puzzle.has_dirs() else None
	image18 = create_theme_image('dird')  if puzzle.has_dirs() else None
	status_image = create_theme_image('status')
	cloud_image = create_theme_image('cloud') if flags.is_cloud_mode and not bg_image else None

	puzzle.on_set_theme()

	outer_wall_image = load_theme_cell_image('wall')
	outer_wall_image.fill((50, 50, 50), special_flags=pygame.BLEND_RGB_SUB)

	cell_images = {
		CELL_WALL:   image1,
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
		CELL_LOCK1:  image13,
		CELL_LOCK2:  image14,
		CELL_DIR_L:  image15,
		CELL_DIR_R:  image16,
		CELL_DIR_U:  image17,
		CELL_DIR_D:  image18,
		CELL_OUTER_WALL: outer_wall_image,
	}

	for barrel in barrels:
		barrel.image = get_theme_image_name("barrel")

	for lift in lifts:
		if lift.image:
			lift.image = get_theme_image_name("lift" + lift.type)

	for drop in drops:
		drop.set_image(get_theme_image_name(drop.name))

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

def reset_level_title_and_goal_time():
	global level_title_time, level_goal_time

	level_title_time = level_time + LEVEL_TITLE_TIME
	level_goal_time = level_title_time + LEVEL_GOAL_TIME

def clear_level_title_and_goal_time():
	global level_title_time, level_goal_time

	level_title_time = 0
	level_goal_time = 0

def reset_idle_time():
	global idle_time, last_autogeneration_time

	idle_time = 0
	last_autogeneration_time = 0

def init_new_level(offset=1, config=None, reload_stored=False):
	global level, level_time, mode, is_game_won
	global puzzle
	global bg_image
	global revealed_map
	global char_cells, enter_room_idx
	global enemies, barrels, killed_enemies, lifts
	global level_time
	global map, stored_level

	if config and offset != 0:
		die("Can't reload a non-current level")

	if reload_stored and offset != 0:
		die("Can't reload a non-current level")

	if not is_main_screen and is_level_out_of_range(offset):
		print("Requested level is out of range")
		return

	if puzzle:
		mode = "finish"
		puzzle.finish()

	stop_music()
	clear_level_title_and_goal_time()
	mode = "init"

	level = config if config else set_level(offset)
	if not level:
		mode = "end"
		is_game_won = True
		start_music()
		return

	flags.parse_level(level)

	char_cells = [None] * flags.NUM_ROOMS
	char.power  = level.get("char_power")
	char.health = level.get("char_health")
	char.attack = None if char.power else INITIAL_CHAR_ATTACK

	barrels.clear()
	enemies.clear()
	lifts.clear()
	killed_enemies.clear()
	portal_destinations.clear()

	puzzle = create_puzzle(level, Globals)

	set_map_size(level.get("map_size", DEFAULT_MAP_SIZE), puzzle.has_border())
	import_size_constants()
	import_size_constants(puzzle)

	flags.apply_sizes()

	bg_image = None
	if "bg_image" in level:
		bg_image = load_image(level["bg_image"], (MAP_W, MAP_H), level.get("bg_image_crop", False))

	for drop in drops:
		# should be called after set_map_size()
		drop.reset()

	theme_name = stored_level["theme_name"] if reload_stored else level["theme"]
	set_theme(theme_name)

	if reload_stored:
		map = stored_level["map"]
		puzzle.on_create_map(map)
		for enemy_info in stored_level["enemy_infos"]:
			create_enemy(*enemy_info)
		for barrel_cell in stored_level["barrel_cells"]:
			create_barrel(barrel_cell)
		for lift_info in stored_level["lift_infos"]:
			create_lift(*lift_info)
		for portal_cell, dst_cell in stored_level["portal_destinations"].items():
			create_portal(portal_cell, dst_cell)
		for drop in drops:
			drop.restore(stored_level["drop_infos"][drop.name])
		set_room(0)
		puzzle.restore_level(stored_level)
	else:
		if puzzle.is_long_generation():
			draw()
			pygame.display.flip()
		generate_map()

	for drop in drops:
		drop.active = drop.num_total > 0

	if "goal" not in level:
		level["goal"] = "default-level-goal"

	level_time = 0
	reset_idle_time()
	if is_level_intro_enabled:
		reset_level_title_and_goal_time()

	if reload_stored:
		char_cells = stored_level["char_cells"]

	if flags.is_cloud_mode:
		revealed_map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype=bool)
		revealed_map.fill(False)

	enter_room_idx = 0
	enter_room(enter_room_idx)

	start_music()

	stored_level = {
		"map": map.copy(),
		"char_cells": char_cells.copy(),
		"enemy_infos": tuple((enemy.c, enemy.power or enemy.health, enemy.attack, enemy.drop) for enemy in enemies),
		"barrel_cells": tuple(barrel.c for barrel in barrels),
		"lift_infos": tuple((lift.c, lift.type) for lift in lifts),
		"portal_destinations": dict(portal_destinations),
		"drop_infos": dict([(drop.name, drop.store()) for drop in drops]),
		"theme_name": theme_name,
	}
	puzzle.store_level(stored_level)

def init_new_room():
	global enter_room_idx

	if not flags.MULTI_ROOMS or enter_room_idx == flags.NUM_ROOMS - 1:
		init_new_level()
	else:
		enter_room_idx += 1
		enter_room(enter_room_idx)

def init_main_screen():
	global is_main_screen

	is_main_screen = True
	reset_level()
	config = {
		"n": 0,
		"num_enemies": 3,
		"theme": "ancient2",
		"music": "valiant_warriors",
		"char_health": 100,
		"use_clock": True,
		"goal": 'select-level',
		"random_maze": True,
		"mainscreen_puzzle": {},
	}
	init_new_level(0, config)

def draw_map():
	for cy in range(len(map[0])):
		for cx in range(len(map)):
			cell = (cx, cy)
			cell_type = map[cx, cy]
			cell_types = [cell_type]
			if cell_type in CELL_FLOOR_EXTENSIONS and cell_type != CELL_FLOOR:
				cell_types.insert(0, CELL_FLOOR)
			puzzle.modify_cell_types_to_draw(cell, cell_types)
			for cell_type in cell_types:
				if flags.is_cloud_mode and not revealed_map[cell]:
					if bg_image:
						continue
					cell_image = cloud_image
				elif cell_type == CELL_VOID:
					continue
				elif cell_image0 := puzzle.get_cell_image_to_draw(cell, cell_type):
					cell_image = cell_image0
				elif cell_type in cell_images:
					cell_image = cell_images[cell_type]
				else:
					cell_image = create_text_cell_image(cell_type)

				if not cell_image:
					debug_map()
					die("Bug. Got null cell image at %s cell_type=%s" % (cell, cell_type))
				elif cell_image.__class__.__name__ == 'CellActor':
					cell_image.c = cell
					cell_image.draw()
				else:
					screen.blit(cell_image, (CELL_W * cx, CELL_H * cy))

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

	draw_status_drops(screen, drops)

	status_message_to_draw = None
	status_message_alpha = 1
	if status_message2 is not None:
		if (alpha := get_fade_text_factor(status_message2_time, STATUS_MESSAGE2_FADE_DURATION, STATUS_MESSAGE2_REST_DURATION)) is not None:
			status_message_to_draw = status_message2
			status_message_alpha = alpha
		else:
			set_status_message2()
	elif status_message is not None:
		status_message_to_draw = status_message
	if status_message_to_draw is not None:
		screen.draw.text(status_message_to_draw, midleft=(20, POS_STATUS_Y), color="#FFF0A0", gcolor="#A09060", owidth=1.2, ocolor="#303020", alpha=status_message_alpha, fontsize=26)

	if mode == "game":
		color, gcolor = ("#60C0FF", "#0080A0") if "time_limit" not in level else ("#FFC060", "#A08000") if level["time_limit"] - level_time > CRITICAL_REMAINING_LEVEL_TIME else ("#FF6060", "#A04040")
		time_str = get_time_str(level_time if "time_limit" not in level else level["time_limit"] - level_time)
		screen.draw.text(time_str, midright=(WIDTH - 20, POS_STATUS_Y), color=color, gcolor=gcolor, owidth=1.2, ocolor="#404030", alpha=1, fontsize=27)

main_screen_color = array((80, 80, 80))

def advance_main_screen_color():
	global main_screen_color
	step = array(choice(((1, 1, -2), (1, -2, 1), (-2, 1, 1), (-1, -1, 2), (-1, 2, -1), (2, -1, -1)))) * randint(1, 2)
	main_screen_color += step
	if any(main_screen_color >= 256) or any(main_screen_color < 0):
		main_screen_color -= step
		advance_main_screen_color()

def draw_central_flash(full=False, color=(0, 40, 40)):
	surface = pygame.Surface((MAP_W, MAP_H if full else 120))
	surface.set_alpha(50)
	surface.fill(color)
	screen.blit(surface, (0, POS_CENTER_Y - surface.get_height() / 2))

def draw_actor_hint(actor, hint, pos_diff, colors):
	screen.draw.text(str(hint), center=apply_diff(actor.pos, pos_diff), color=colors[0], gcolor=colors[1], owidth=1.2, ocolor=colors[2], alpha=0.8, fontsize=24)

def draw():
	if mode == "start":
		return
	screen.fill("#2f3542")
	if bg_image:
		screen.blit(bg_image, (MAP_POS_X1, MAP_POS_Y1))
	if mode == "game" or mode == "end" or mode == "next":
		visible_barrels = get_revealed_actors(barrels)
		visible_enemies = get_revealed_actors(enemies)
		draw_map()
		draw_status()
		for lift in lifts:
			lift.draw()
		for drop in drops:
			drop.draw_instances(draw_actor_hint)
		for barrel in visible_barrels:
			barrel.draw()
		for enemy in killed_enemies:
			enemy.draw()
		for enemy in visible_enemies:
			enemy.draw()
		char.draw()
		for actor in visible_enemies + [char]:
			if actor.power:
				draw_actor_hint(actor, actor.power, (0, -CELL_H * 0.5 - 14), CHAR_POWER_COLORS if actor == char else ENEMY_POWER_COLORS)
			elif actor.health is not None:
				draw_actor_hint(actor, actor.health, (-12, -CELL_H * 0.5 - 14), ACTOR_HEALTH_COLORS)
				draw_actor_hint(actor, actor.attack, (+12, -CELL_H * 0.5 - 14), ACTOR_ATTACK_COLORS)
		cursor.draw()

	puzzle.on_draw(mode)

	if mode == "end":
		end_line = _('victory-text') if is_game_won else _('defeat-text')
		draw_central_flash()
		screen.draw.text(end_line, center=(POS_CENTER_X, POS_CENTER_Y), color='white', gcolor=("#008080" if is_game_won else "#800000"), owidth=0.8, ocolor="#202020", alpha=1, fontsize=60)

	if is_main_screen:
		advance_main_screen_color()
		draw_central_flash(True, tuple(main_screen_color))

	if mode == "game" and level_title_time > 0:
		draw_central_flash()
		level_line_1 = _("Main Screen") if level["n"] == 0 else _('level-label') + " " + str(level["n"])
		level_line_2 = _(level.get("name", 'level-' + str(level["n"]) + '-name'))
		screen.draw.text(level_line_1, center=(POS_CENTER_X, POS_CENTER_Y - 14), color='yellow', gcolor="#AAA060", owidth=1.2, ocolor="#404030", alpha=1, fontsize=50)
		screen.draw.text(level_line_2, center=(POS_CENTER_X, POS_CENTER_Y + 21), color='white', gcolor="#C08080", owidth=1.2, ocolor="#404030", alpha=1, fontsize=32)
	elif mode == "game" and level_goal_time > 0:
		goal_line = _(level["goal"])
		draw_central_flash()
		screen.draw.text(goal_line, center=(POS_CENTER_X, POS_CENTER_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=1, fontsize=40)

	if mode == "init":
		screen.fill("#a8b6b7")
		screen.draw.text(_("Initializing level…"), center=(POS_CENTER_X, POS_CENTER_Y), color='#FFFFFF', gcolor="#88AA66", owidth=1.2, ocolor="#404030", alpha=1, fontsize=80)

def kill_enemy_cleanup():
	killed_enemies.pop(0)

def handle_press_key():
	global is_main_screen
	global lang
	global is_move_animate_enabled, is_level_intro_enabled, is_sound_enabled

	# apply workaround for the invalid syntax keyboard.return in python
	keyboard.enter = keys.RETURN in keyboard._pressed

	keyboard.shift = keyboard.lshift or keyboard.rshift
	keyboard.ctrl  = keyboard.lctrl  or keyboard.rctrl
	keyboard.alt   = keyboard.lalt   or keyboard.ralt

	if mode == "game" and is_main_screen and keyboard._pressed \
		and not (keyboard.ctrl or keyboard.escape or keyboard.right or keyboard.left or keyboard.up or keyboard.down):
		is_main_screen = False
		init_new_level()
		return

	reset_idle_time()

	if mode != "game" and mode != "end" and mode != "next":
		return

	if keyboard.escape and not cursor.is_active():
		init_main_screen()
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
				reset_level_title_and_goal_time()
			else:
				clear_level_title_and_goal_time()

		if keyboard.s:
			flags.is_stopless = not flags.is_stopless

		if keyboard.d:
			debug_map(full_format=not keyboard.ralt, clean=not keyboard.rctrl)

		return

	if keyboard.f1:
		set_theme("default")
	if keyboard.f2:
		set_theme("classic")
	if keyboard.f3:
		set_theme("ancient1")
	if keyboard.f4:
		set_theme("ancient2")
	if keyboard.f5:
		set_theme("modern1")
	if keyboard.f6:
		set_theme("modern2")
	if keyboard.f7:
		set_theme("minecraft")
	if keyboard.f8:
		set_theme("moss"      if not keyboard.shift else "stoneage3")
	if keyboard.f9:
		set_theme("stoneage1" if not keyboard.shift else "stoneage4")
	if keyboard.f10:
		set_theme("stoneage2" if not keyboard.shift else "stoneage5")

	if keyboard.f11:
		pygame.display.toggle_fullscreen()
		# workaround for pygame bug similar to #2380; this set_mode should not be needed
		if not pygame.display.is_fullscreen():
			pygame.display.set_mode((WIDTH, HEIGHT))
	if keyboard.f12:
		pygame.mouse.set_visible(not pygame.mouse.get_visible())

	if keyboard.l:
		reset_level_title_and_goal_time()

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

	if mode == "next" or is_main_screen:
		return

	if keyboard.p:
		offset = get_prev_level_group_offset() if keyboard.lctrl else get_prev_level_offset()
		init_new_level(offset)
	if keyboard.r:
		offset = get_curr_level_group_offset() if keyboard.lctrl else 0
		init_new_level(offset, reload_stored=keyboard.lalt and not keyboard.lctrl)
	if keyboard.n:
		offset = get_next_level_group_offset() if keyboard.lctrl else get_next_level_offset()
		init_new_level(offset)

	if keyboard.w:
		win_room()

	if keyboard.o:
		set_status_message2("Hello, world!", 5)

	if keyboard.space and cursor.is_char_selected() and map[char.c] == CELL_PORTAL:
		teleport_char()

	cursor_was_active = cursor.is_active()

	if keyboard.enter:
		if not cursor.is_active():
			cursor.toggle()
		else:
			if not puzzle.press_cell(cursor.c):
				cursor.toggle()

	if keyboard.space or keyboard.escape:
		if not cursor.is_char_selected():
			cursor.reset()

	if DEBUG_LEVEL > 0 and cursor_was_active and not cursor.is_active():
		set_status_message2()

	if keyboard.home:
		puzzle.press_cell(cursor.selected_actor.c, 1)
	if keyboard.end:
		puzzle.press_cell(cursor.selected_actor.c, 3)
	if keyboard.insert:
		puzzle.press_cell(cursor.selected_actor.c, 2)
	if keyboard.delete:
		puzzle.press_cell(cursor.selected_actor.c, 6)
	if keyboard.pageup:
		puzzle.press_cell(cursor.selected_actor.c, 4)
	if keyboard.pagedown:
		puzzle.press_cell(cursor.selected_actor.c, 5)

	puzzle.on_press_key(keyboard)

def on_key_down(key):
	handle_press_key()

def on_mouse_down(pos, button):
	if mode != "game":
		return

	if cursor.is_active():
		cursor.toggle()
	cell = pos_to_cell(pos)
	puzzle.press_cell(cell, button)

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
	clock.schedule(init_new_room, WIN_NEW_DELAY)

def check_victory():
	if mode != "game":
		return

	if "time_limit" in level and level_time > level["time_limit"] or char.health is not None and char.health <= 0 or char.power is not None and char.power <= 0:
		loose_game()
		return

	status_messages = []
	can_win = True
	goal_achieved = False

	if puzzle.is_goal_to_be_solved():
		if puzzle.is_solved():
			goal_achieved = True
			status_messages.append("Puzzle solved!")
		else:
			can_win = False
			status_messages.append("Solve puzzle!")

	if is_main_screen:
		status_messages.append("Press Enter to continue")
	elif puzzle.is_goal_to_kill_enemies():
		if not sum(1 for enemy in enemies if is_actor_in_room(enemy)) and not killed_enemies:
			goal_achieved = True
			status_messages.append("All enemies killed!")
		else:
			can_win = False
			status_messages.append("Kill all enemies!")

	if level.get("disable_win"):
		can_win = False

	if flags.has_finish or puzzle.has_finish():
		if map[char.c] == CELL_FINISH and can_win:
			char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(1, 0))
			win_room()
		else:
			status_messages.append("Reach finish!")
	elif goal_achieved and can_win:
		win_room()

	if status_messages:
		set_status_message(" ".join(status_messages))

def teleport_char():
	if map[char.c] != CELL_PORTAL:
		die("Called teleport_char not on CELL_PORTAL")

	if char._scale != 0:
		char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(1, 0), angle=(0, 540), on_finished=teleport_char)
	else:
		char.c = portal_destinations[char.c]
		char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(0, 1), angle=(540, 0))

def leave_cell(old_char_cell):
	if map[old_char_cell] == CELL_SAND:
		map[old_char_cell] = CELL_VOID

def prepare_enter_cell(animate_duration):
	# prepare drop disappear if any
	for drop in drops:
		if drop.has_instance(char.c):
			drop.disappear(char.c, level_time, animate_duration)

def enter_cell():
	# collect drop if any
	for drop in drops:
		if (args := drop.collect(char.c)) is not None:
			if drop.name == 'heart' and not char.power:
				char.health += BONUS_HEALTH_VALUE
			if drop.name == 'sword' and not char.power:
				char.attack += BONUS_ATTACK_VALUE
			if drop.name == 'might' and char.power:
				op, factor = args
				if op == '×': char.power *= factor
				if op == '÷': char.power //= factor
				if op == '+': char.power += factor
				if op == '-': char.power -= factor

	if map[char.c] == CELL_PORTAL:
		teleport_char()
	elif map[char.c] == CELL_LOCK1:
		map[char.c] = CELL_FLOOR
		drop_key1.consume()
	elif map[char.c] == CELL_LOCK2:
		map[char.c] = CELL_FLOOR
		drop_key2.consume()

last_move_diff = None

def continue_move_char():
	diff_x, diff_y = last_move_diff
	last_move_diff = None
	move_char(diff_x, diff_y)

def get_move_animate_duration(old_char_cell):
	distance = get_distance(old_char_cell, char.c)
	animate_time_factor = distance - (distance - 1) / 2
	return animate_time_factor * ARROW_KEYS_RESOLUTION

def activate_beat_animation(actor, diff, tween):
	actor.move_pos((diff[0] * ENEMY_BEAT_OFFSET, diff[1] * ENEMY_BEAT_OFFSET))
	actor.animate(ENEMY_BEAT_ANIMATION_TIME, tween)

def kill_enemy(enemy):
	play_sound("kill")
	enemies.remove(enemy)
	# fallen drops upon enemy death
	if enemy.drop:
		enemy.drop.instantiate(enemy)
	enemy.activate_inplace_animation(level_time, ENEMY_KILL_ANIMATION_TIME, angle=(0, (-90, 90)[randint(0, 1)]), opacity=(1, 0.3), scale=(1, 0.8))
	killed_enemies.append(enemy)
	clock.schedule(kill_enemy_cleanup, ENEMY_KILL_ANIMATION_TIME + ENEMY_KILL_DELAY)

def beat_or_kill_enemy(enemy, diff):
	if enemy.power is None or char.power is None:
		die("Called beat_or_kill_enemy in power mode")

	enemy.health -= char.attack
	# can't move if we face enemy, cancel the move
	char.move(diff, undo=True)
	# animate beat or kill
	if enemy.health > 0:
		play_sound("beat")
		activate_beat_animation(enemy, diff, 'decelerate')
	else:
		kill_enemy(enemy)
	activate_beat_animation(char, diff, 'bounce_end')

def move_char(diff_x, diff_y):
	global last_move_diff

	diff = (diff_x, diff_y)

	old_char_pos = char.pos
	old_char_cell = char.c

	# try to move forward, and prepare to cancel if the move is impossible
	char.move(diff)

	if flags.is_stopless:
		is_jumped = False
		while map[char.c] in CELL_FLOOR_TYPES and not is_cell_occupied_except_char(char.c) and can_move(diff):
			char.move(diff)
			is_jumped = True
		if is_move_animate_enabled and is_jumped and is_cell_occupied_except_char(char.c) and last_move_diff is None:
			# undo one step
			char.move(diff, undo=True)
			last_move_diff = diff
			char.pos = old_char_pos
			char.animate(get_move_animate_duration(old_char_cell), on_finished=continue_move_char)
			return

	should_pull = flags.allow_barrel_pull and keyboard.shift
	pull_barrel_cell = None
	if should_pull:
		if not is_cell_accessible(char.c):
			# can't pull into obstacle
			char.move(diff, undo=True)
			return
		pull_barrel_cell = apply_diff(old_char_cell, diff, subtract=True)

	# collision with enemies
	enemy = get_actor_on_cell(char.c, enemies)
	if enemy:
		if char.power is None:
			char.health -= enemy.attack
			beat_or_kill_enemy(enemy, diff)
			return
		else:
			if char.power >= enemy.power:
				char.power += enemy.power
				kill_enemy(enemy)
			else:
				char.power = 0
				# we die, cancel move
				char.move(diff, undo=True)
				return

	# collision with barrels
	barrel = get_actor_on_cell(pull_barrel_cell or char.c, barrels)
	if barrel:
		next_barrel_cell = apply_diff(barrel.c, diff)
		if not is_cell_accessible(next_barrel_cell, allow_enemy=True):
			# can't push, cancel the move
			char.move(diff, undo=True)
			return
		else:
			# if enemy is in the next barrel cell, possibly don't move; beat or kill it
			if enemy := get_actor_on_cell(next_barrel_cell, enemies):
				if char.power is None:
					beat_or_kill_enemy(enemy, diff)
					activate_beat_animation(barrel, diff, 'bounce_end')
					return
				else:
					# in power mode unconditionally kill enemy using barrel
					kill_enemy(enemy)

			# can push, animate the push
			barrel.move_animated(diff, enable_animation=is_move_animate_enabled)

	# can move, animate the move
	new_char_pos = char.pos

	# process lift movement if available
	if lift_target := get_lift_target(old_char_cell, diff):
		distance = get_distance(old_char_cell, lift_target)
		for i in range(1, distance):
			char.move(diff)
		lift = get_actor_on_cell(old_char_cell, lifts)
		lift.move_animated(target=lift_target, enable_animation=is_move_animate_enabled, on_finished=activate_cursor_after_lift_movement)

	leave_cell(old_char_cell)

	if is_move_animate_enabled:
		animate_duration = get_move_animate_duration(old_char_cell)
		prepare_enter_cell(animate_duration)
		char.pos = old_char_pos
		char.animate(animate_duration, on_finished=enter_cell)
	else:
		enter_cell()

	reveal_map_near_char()

def activate_cursor_after_lift_movement():
	if not cursor.is_lift_selected():
		return
	lift = cursor.selected_actor
	if lift.type in (LIFT_L, LIFT_R, LIFT_U, LIFT_D):
		cursor.toggle()

def move_selected_lift(diff):
	lift = cursor.selected_actor
	if lift_target := get_lift_target(lift.c, diff):
		for actor in [lift, char] if char.c == lift.c else [lift]:
			actor.move_animated(target=lift_target, enable_animation=is_move_animate_enabled, on_finished=activate_cursor_after_lift_movement)

def can_move(diff):
	dest_cell = apply_diff(cursor.selected_actor.c, diff)

	if not is_cell_in_room(dest_cell):
		return False

	if cursor.is_active():
		return True

	if cursor.is_lift_selected():
		return map[dest_cell] == CELL_VOID and not is_cell_in_actors(dest_cell, lifts)

	return (
		map[dest_cell] not in CELL_CHAR_MOVE_OBSTACLES
		or map[dest_cell] == CELL_LOCK1 and drop_key1.num_collected > 0
		or map[dest_cell] == CELL_LOCK2 and drop_key2.num_collected > 0
		or map[dest_cell] == CELL_DIR_L and diff != (+1, 0)
		or map[dest_cell] == CELL_DIR_R and diff != (-1, 0)
		or map[dest_cell] == CELL_DIR_U and diff != (0, +1)
		or map[dest_cell] == CELL_DIR_D and diff != (0, -1)
		or is_cell_in_actors(dest_cell, lifts)
		or get_lift_target(char.c, diff)
	)

def get_char_image_name(is_left):
	return "left" if is_left ^ (not flags.allow_barrel_pull or not keyboard.lshift) else "stand"

ARROW_KEY_CODE = {
	'r': pygame.K_RIGHT,
	'l': pygame.K_LEFT,
	'd': pygame.K_DOWN,
	'u': pygame.K_UP,
}

def update(dt):
	global level_title_time, level_goal_time
	global game_time, level_time, idle_time, last_autogeneration_time
	global last_time_arrow_keys_processed, last_processed_arrow_keys, last_processed_arrow_diff

	if mode == "start":
		init_main_screen()
		return

	game_time += dt
	level_time += dt
	idle_time += dt

	for actor in active_inplace_animation_actors:
		actor.update_inplace_animation(level_time)

	puzzle.on_update(level_time)

	if level_title_time < level_time:
		level_title_time = 0
	if level_goal_time < level_time:
		level_goal_time = 0

	if char.health is not None and (
		last_autogeneration_time == 0 and idle_time >= AUTOGENERATION_IDLE_TIME or
		last_autogeneration_time != 0 and idle_time >= last_autogeneration_time + AUTOGENERATION_NEXT_TIME
	):
		char.health += AUTOGENERATION_HEALTH
		if char.health > level["char_health"]:
			char.health = level["char_health"]
		last_autogeneration_time = idle_time

	check_victory()

	if DEBUG_LEVEL > 0 and cursor.is_active():
		set_status_message2(str(cursor.c))

	if char.is_animated():
		return

	scan_joysticks_and_state()

	if emulate_joysticks_press_key(keyboard):
		handle_press_key()
		return

	keys = pygame.key.get_pressed()
	joistick_arrow_keys = get_joysticks_arrow_keys()
	for key in ('r', 'l', 'd', 'u'):
		is_key_pressed = keys[ARROW_KEY_CODE[key]] or key in joistick_arrow_keys
		if is_key_pressed and key not in pressed_arrow_keys:
			pressed_arrow_keys.append(key)
			reset_idle_time()
		if not is_key_pressed and key in pressed_arrow_keys and key in last_processed_arrow_keys:
			pressed_arrow_keys.remove(key)

	if game_time - last_time_arrow_keys_processed < ARROW_KEYS_RESOLUTION:
		return

	last_time_arrow_keys_processed = game_time
	last_processed_arrow_keys = []
	last_processed_arrow_diff = (0, 0)

	def set_arrow_key_to_process(key, diff):
		global last_processed_arrow_keys, last_processed_arrow_diff
		if not ALLOW_DIAGONAL_MOVES and last_processed_arrow_keys:
			return
		pressed_arrow_keys.remove(key)
		next_diff = apply_diff(last_processed_arrow_diff, diff)
		if can_move(next_diff):
			last_processed_arrow_keys.append(key)
			last_processed_arrow_diff = next_diff

	for key in list(pressed_arrow_keys):
		if key == 'r' and key not in last_processed_arrow_keys and 'l' not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (+1, +0))
		if key == 'l' and key not in last_processed_arrow_keys and 'r' not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (-1, +0))
		if key == 'd' and key not in last_processed_arrow_keys and 'u' not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (+0, +1))
		if key == 'u' and key not in last_processed_arrow_keys and 'd' not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, (+0, -1))

	diff_x = 0
	diff_y = 0

	if 'r' in last_processed_arrow_keys:
		diff_x += 1
		if cursor.is_char_selected():
			char.image = get_char_image_name(True)
	if 'l' in last_processed_arrow_keys:
		diff_x -= 1
		if cursor.is_char_selected():
			char.image = get_char_image_name(False)
	if 'd' in last_processed_arrow_keys:
		diff_y += 1
	if 'u' in last_processed_arrow_keys:
		diff_y -= 1

	if diff_x or diff_y:
		diff = (diff_x, diff_y)
		if cursor.is_active():
			cursor.move_animated(diff, enable_animation=is_move_animate_enabled)
		elif cursor.is_lift_selected():
			move_selected_lift(diff)
		else:
			move_char(diff_x, diff_y)

Globals.move_char = move_char
