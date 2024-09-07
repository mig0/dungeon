import os
import random
import pygame
import pgzero
from numpy import ndarray, chararray
from copy import deepcopy
from random import randint
from constants import *
from translations import *
from cellactor import *
from objects import *
from drop import draw_status_drops
from flags import flags
from puzzle import create_puzzle

lang = 'en'

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

is_game_won = False
is_music_enabled = True
is_music_started = False
is_sound_enabled = True
is_move_animate_enabled = True
is_level_intro_enabled = True

mode = "start"

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

level_title_timer = 0
level_target_timer = 0

level = None
level_idx = -1

room = Area()
room_idx = None

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
				cell = (cx, cy)
				print(CELL_FLOOR if clean and map[cell] in CELL_FLOOR_TYPES else map[cell], end="")
		if dual:
			print("    ", end="")
		if dual or combined:
			for cx in MAP_X_RANGE if full else PLAY_X_RANGE:
				cell = (cx, cy)
				cell_ch = CELL_FLOOR if clean and map[cell] in CELL_FLOOR_TYPES else map[cell] or ' '
				if drop := get_drop_on_cell(cell):
					cell_ch = ACTOR_CHARS[drop.name]
				if is_cell_in_actors(cell, enemies):
					cell_ch = ACTOR_CHARS['enemy']
				if is_cell_in_actors(cell, barrels):
					cell_ch = ACTOR_CHARS['barrel']
				if lift := get_actor_on_cell(cell, lifts):
					cell_ch = LIFT_CHARS[lift.type]
				if char.c is not None and char.c == cell:
					cell_ch = ACTOR_CHARS['char']
				print(cell_ch, end="")
		print()
	if endl:
		print()

def is_cell_in_map(cell):
	return is_cell_in_area(cell, MAP_X_RANGE, MAP_Y_RANGE)

def is_inner_wall(cell):
	if map[cell] not in CELL_WALLS:
		return False

	for neigh in get_all_neighbors(*cell):
		if is_cell_in_map(neigh) and map[neigh] not in CELL_WALLS:
			return False
	return True

def convert_inner_walls():
	for cy in MAP_Y_RANGE:
		for cx in MAP_X_RANGE:
			if is_inner_wall((cx, cy)):
				map[cx, cy] = CELL_INNER_WALL

def get_theme_image_name(image_name):
	for full_image_name in (theme_prefix + image_name, DEFAULT_IMAGE_PREFIX + image_name):
		if os.path.isfile(IMAGES_DIR_PREFIX + full_image_name + '.png'):
			debug(2, "Found image %s" % full_image_name)
			return full_image_name

	print("Unable to find image %s in neither %s nor %s" % (image_name, theme_prefix, DEFAULT_IMAGE_PREFIX))
	quit()

def load_theme_cell_image(image_name):
	return pygame.image.load(IMAGES_DIR_PREFIX + get_theme_image_name(image_name) + '.png').convert_alpha()

def colorize_cell_image(image, color, alpha=1):
	cell_surface = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA, 32)
	cell_surface.fill((*color, alpha * 255))
	cell_surface.blit(image, (0, 0))
	return cell_surface

def create_text_cell_image(text, color='#E0E0E0', gcolor="#408080", owidth=1.2, ocolor="#004040", alpha=1, fontsize=48):
	cell_surface = pygame.Surface((CELL_W, CELL_H), pygame.SRCALPHA, 32)
	pgzero.ptext.draw(text, surf=cell_surface, center=cell_to_pos((0, 0)), color=color, gcolor=gcolor, owidth=owidth, ocolor=ocolor, alpha=alpha, fontsize=fontsize)
	return cell_surface

def is_cell_occupied_except_char(cell):
	if is_cell_in_actors(cell, enemies + barrels):
		return True

	return get_drop_on_cell(cell) is not None

def is_cell_occupied(cell):
	return is_cell_occupied_except_char(cell) or char.c == cell

def is_cell_occupied_for_enemy(cell):
	return map[cell] in CELL_ENEMY_PLACE_OBSTACLES or is_cell_occupied(cell)

def create_theme_image(image_name):
	return CellActor(get_theme_image_name(image_name))

def create_theme_actor(image_name, cell):
	return create_actor(get_theme_image_name(image_name), cell)

def reveal_map_near_char():
	if not flags.is_cloud_mode:
		return

	for (cx, cy) in get_all_neighbors(char.cx, char.cy, include_self=True):
		revealed_map[cx, cy] = True

def get_revealed_actors(actors):
	if not flags.is_cloud_mode or level.get("actors_always_revealed", False):
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

	puzzle.on_set_room(room)

def get_max_room_distance():
	return get_distance((room.x1, room.y1), (room.x2, room.y2))

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

def get_accessible_cells(start_cell):
	accessible_cells = []
	unprocessed_cells = [start_cell]
	while unprocessed_cells:
		cell = unprocessed_cells.pop(0)
		accessible_cells.append(cell)
		neigbours = get_accessible_neighbors(cell)
		for n in neigbours:
			if n not in accessible_cells and n not in unprocessed_cells:
				unprocessed_cells.append(n)
	return accessible_cells

def get_accessible_cell_distances(start_cell):
	accessible_cells = []
	accessible_cell_distances = {start_cell: 0}
	unprocessed_cells = [start_cell]
	while unprocessed_cells:
		cell = unprocessed_cells.pop(0)
		accessible_distance = accessible_cell_distances[cell]
		accessible_cells.append(cell)
		neigbours = get_accessible_neighbors(cell)
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

def find_path(start_cell, target_cell):
	accessible_cell_distances = get_accessible_cell_distances(start_cell)
	accessible_distance = accessible_cell_distances.get(target_cell)
	if accessible_distance is None:
		return None
	path_cells = [target_cell]
	current_cell = target_cell
	while accessible_distance > 1:
		accessible_distance -= 1
		for neigh_cell in get_accessible_neighbors(current_cell):
			neigh_distance = accessible_cell_distances.get(neigh_cell)
			if neigh_distance == accessible_distance:
				current_cell = neigh_cell
				path_cells.insert(0, neigh_cell)
				break
	return path_cells

def is_path_found(start_cell, target_cell):
	return target_cell in get_accessible_cells(start_cell)

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
	char.c = best_cell

def place_char_in_first_free_spot():
	for cy in room.y_range:
		for cx in room.x_range:
			if is_cell_accessible(cx, cy, place=True):
				char.c = (cx, cy)
				return

	print("Was not able to find free spot for char, fix the level or a bug")
	if DEBUG_LEVEL:
		char.c = (0, 0)
	else:
		quit()

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

def create_portal_pair(cell1, cell2):
	if cell1 == cell2:
		print("BUG: Portal pair can't be the same cell, exiting")
		quit()

	portal_destinations[cell1] = cell2
	portal_destinations[cell2] = cell1

def create_lift(cell, type):
	global lifts

	image_name = "lift" + type
	lift = create_theme_actor(image_name, cell)
	lift.type = type
	lifts.append(lift)

def get_lift_target(cell, diff):
	lift = get_actor_on_cell(cell, lifts)
	if not lift or diff not in LIFT_TYPE_DIRECTIONS[lift.type]:
		return None
	returned_cell = None
	while True:
		next_cell = apply_diff(cell, diff)
		if not is_cell_in_room(next_cell) or map[next_cell] != CELL_VOID or is_cell_in_actors(next_cell, lifts):
			return returned_cell
		returned_cell = cell = next_cell

def create_enemy(cell, health=None, attack=None, drop=None):
	global enemies

	enemy = create_actor("skeleton", cell)
	enemy.health = health if health is not None else randint(MIN_ENEMY_HEALTH, MAX_ENEMY_HEALTH)
	enemy.attack = attack if attack is not None else randint(MIN_ENEMY_ATTACK, MAX_ENEMY_ATTACK)
	enemy.drop   = drop   if drop   is not None else (None, drop_heart, drop_sword)[randint(0, 2)]
	if enemy.drop:
		enemy.drop.contain(enemy)
	enemies.append(enemy)

class Globals:
	get_actor_neighbors = get_actor_neighbors
	get_all_neighbors = get_all_neighbors
	debug = debug
	debug_map = debug_map
	convert_inner_walls = convert_inner_walls
	load_theme_cell_image = load_theme_cell_image
	colorize_cell_image = colorize_cell_image
	create_text_cell_image = create_text_cell_image
	is_cell_occupied = is_cell_occupied
	get_max_room_distance = get_max_room_distance
	is_actor_in_room = is_actor_in_room
	get_distance = get_distance
	get_all_accessible_cells = get_all_accessible_cells
	get_num_accessible_target_directions = get_num_accessible_target_directions
	find_path = find_path
	is_path_found = is_path_found
	set_char_cell = set_char_cell
	get_random_floor_cell_type = get_random_floor_cell_type
	convert_to_floor_if_needed = convert_to_floor_if_needed
	generate_random_free_path = generate_random_free_path
	create_barrel = create_barrel
	get_random_floor_cell = get_random_floor_cell
	replace_random_floor_cell = replace_random_floor_cell
	create_portal_pair = create_portal_pair
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
		if room.idx == 0:
			set_char_cell(char.c)
		accessible_cells = get_all_accessible_cells()
		accessible_cells.pop(0)  # remove char cell
		finish_cell = accessible_cells.pop()
		map[finish_cell] = CELL_FINISH

	puzzle.generate_room(accessible_cells, finish_cell)

	# generate enemies
	for i in range(level["num_enemies"] if "num_enemies" in level else DEFAULT_NUM_ENEMIES):
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
	for cy in MAP_Y_RANGE:
		for cx in MAP_X_RANGE:
			if cx == 0 or cx == PLAY_SIZE_X + 1 or cy == 0 or cy == PLAY_SIZE_Y + 1:
				cell_type = CELL_WALL
			else:
				if flags.is_four_rooms and (cx == ROOM_BORDER_X or cy == ROOM_BORDER_Y):
					cell_type = CELL_WALL
				else:
					cell_type = get_random_floor_cell_type()
			map[cx, cy] = cell_type

	puzzle.on_create_map(map)

	if flags.is_four_rooms:
		for idx in range(4):
			generate_room(idx)
	else:
		generate_room(None)

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
	status_image = create_theme_image('status')
	cloud_image = create_theme_image('cloud') if flags.is_cloud_mode and not bg_image else None

	puzzle.on_set_theme()

	inner_wall_image = load_theme_cell_image('wall')
	inner_wall_image.fill((50, 50, 50), special_flags=pygame.BLEND_RGB_SUB)

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
		CELL_INNER_WALL: inner_wall_image,
	}

	for barrel in barrels:
		barrel.image = get_theme_image_name('barrel')

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
	global puzzle
	global bg_image
	global revealed_map
	global char_cell, room_idx
	global enemies, barrels, killed_enemies, lifts
	global level_time
	global map, stored_level

	if reload_stored and offset != 0:
		print("Can't reload a non-current level")
		quit()

	if level_idx + offset < 0 or level_idx + offset > len(LEVELS):
		print("Requested level is out of range")
		return

	stop_music()
	clear_level_and_target_timer()
	mode = "init"

	level_idx += offset
	if level_idx == len(LEVELS):
		mode = "end"
		is_game_won = True
		start_music()
		return

	level = LEVELS[level_idx]

	flags.parse_level(level)

	puzzle = create_puzzle(level, Globals)

	bg_image = None
	if "bg_image" in level:
		bg_image = pygame.image.load(level["bg_image"]).convert()
		bg_image = pygame.transform.scale(bg_image, (MAP_W, MAP_H))

	char_cell = None
	char.health = level["char_health"]
	char.attack = INITIAL_CHAR_ATTACK

	barrels.clear()
	enemies.clear()
	lifts.clear()
	killed_enemies.clear()

	for drop in drops:
		drop.reset()

	set_theme(level["theme"])
	if reload_stored:
		map = stored_level["map"]
		for enemy_info in stored_level["enemy_infos"]:
			create_enemy(*enemy_info)
		for barrel_cell in stored_level["barrel_cells"]:
			create_barrel(barrel_cell)
		for lift_info in stored_level["lift_infos"]:
			create_lift(*lift_info)
		puzzle.restore_level(stored_level)
	else:
		if puzzle.is_long_generation():
			draw()
			pygame.display.flip()
		generate_map()

	for drop in drops:
		drop.active = drop.num_contained > 0

	if "target" not in level:
		level["target"] = "default-level-target"

	level_time = 0
	reset_idle_time()
	if is_level_intro_enabled:
		reset_level_and_target_timer()

	room_idx = 0 if flags.is_four_rooms else None
	set_room(room_idx)

	if reload_stored:
		char_cell = stored_level["char_cell"]
	if char_cell:
		char.c = char_cell
	else:
		place_char_in_first_free_spot()

	if flags.is_cloud_mode:
		revealed_map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype=bool)
		revealed_map.fill(False)
	reveal_map_near_char()

	char.reset_inplace_animation()
	if map[char.c] == CELL_START:
		char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(0, 1), angle=(180, 720), flip=(True, True, 1))

	mode = "game"
	start_music()

	stored_level = {
		"map": map.copy(),
		"char_cell": char.c,
		"enemy_infos": tuple((enemy.c, enemy.health, enemy.attack, enemy.drop) for enemy in enemies),
		"barrel_cells": tuple(barrel.c for barrel in barrels),
		"lift_infos": tuple((lift.c, lift.type) for lift in lifts),
	}
	puzzle.store_level(stored_level)

def init_new_room():
	global room_idx, mode

	if flags.is_four_rooms:
		room_idx += 1

	if not flags.is_four_rooms or room_idx == 4:
		init_new_level()
	else:
		set_room(room_idx)
		place_char_in_first_free_spot()
		reveal_map_near_char()
		char.reset_inplace()
		mode = "game"

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
					print("Bug. Got null cell image at %s cell_type=%s" % (cell, cell_type))
					quit()
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
		for lift in lifts:
			lift.draw()
		for drop in drops:
			drop.draw_instances()
		for barrel in visible_barrels:
			barrel.draw()
		for enemy in killed_enemies:
			enemy.draw()
		for enemy in visible_enemies:
			enemy.draw()
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

		if keyboard.s:
			flags.is_stopless = not flags.is_stopless

		if keyboard.d:
			debug_map()

		return

	if keyboard.f1:
		set_theme("default")
	if keyboard.f2:
		set_theme("classic")
	if keyboard.f3:
		set_theme("ancient1")
	if keyboard.f4:
		set_theme("modern1")
	if keyboard.f5:
		set_theme("modern2")
	if keyboard.f6:
		set_theme("stoneage1")
	if keyboard.f7:
		set_theme("stoneage2")
	if keyboard.f8:
		set_theme("minecraft")
	if keyboard.f9:
		set_theme("moss")

	if keyboard.f11:
		pygame.display.toggle_fullscreen()
		# workaround for pygame bug similar to #2380; this set_mode should not be needed
		if not pygame.display.is_fullscreen():
			pygame.display.set_mode((WIDTH, HEIGHT))
	if keyboard.f12:
		pygame.mouse.set_visible(not pygame.mouse.get_visible())

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

	if mode == "next":
		return

	if keyboard.p:
		init_new_level(-1)
	if keyboard.r:
		init_new_level(0, bool(keyboard.lalt))
	if keyboard.n:
		init_new_level(+1)

	if keyboard.space and map[char.c] == CELL_PORTAL:
		teleport_char()

	if puzzle.on_press_key(keyboard):
		if puzzle.is_solved():
			win_room()

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
	elif puzzle.is_target_to_be_solved():
		if puzzle.is_solved():
			win_room()
	elif flags.has_finish or puzzle.has_finish():
		if map[char.c] == CELL_FINISH:
			char.activate_inplace_animation(level_time, CHAR_APPEARANCE_SCALE_DURATION, scale=(1, 0))
			win_room()
	elif not puzzle.is_target_to_kill_enemies():
		pass
	elif not sum(1 for enemy in enemies if is_actor_in_room(enemy)) and not killed_enemies:
		win_room()

def teleport_char():
	if map[char.c] != CELL_PORTAL:
		print("Called teleport_char not on CELL_PORTAL")
		quit()

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
		if drop.collect(char.c):
			if drop.name == 'heart':
				char.health += BONUS_HEALTH_VALUE
			if drop.name == 'sword':
				char.attack += BONUS_ATTACK_VALUE

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

def move_char(diff_x, diff_y):
	global last_move_diff

	diff = (diff_x, diff_y)
	undo_diff = (-diff_x, -diff_y)

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
			char.move(undo_diff)
			last_move_diff = diff
			char.pos = old_char_pos
			char.animate(get_move_animate_duration(old_char_cell), on_finished=continue_move_char)
			return

	# collision with enemies
	enemy = get_actor_on_cell(char.c, enemies)
	if enemy:
		enemy.health -= char.attack
		char.health -= enemy.attack
		# can't move if we face enemy, cancel the move
		char.move(undo_diff)
		# animate beat or kill
		if enemy.health > 0:
			enemy.move_pos((diff_x * ENEMY_BEAT_OFFSET, diff_y * ENEMY_BEAT_OFFSET))
			play_sound("beat")
			enemy.animate(ENEMY_BEAT_ANIMATION_TIME, 'bounce_end')
		else:
			play_sound("kill")
			enemies.remove(enemy)
			# fallen drops upon enemy death
			if enemy.drop:
				enemy.drop.instantiate(enemy)
			enemy.activate_inplace_animation(level_time, ENEMY_KILL_ANIMATION_TIME, angle=(0, (-90, 90)[randint(0, 1)]), opacity=(1, 0.3), scale=(1, 0.8))
			killed_enemies.append(enemy)
			clock.schedule(kill_enemy, ENEMY_KILL_ANIMATION_TIME + ENEMY_KILL_DELAY)
		return

	# collision with barrels
	barrel = get_actor_on_cell(char.c, barrels)
	if barrel:
		if not is_cell_accessible(barrel.cx + diff_x, barrel.cy + diff_y):
			# can't push, cancel the move
			char.move(undo_diff)
			return
		else:
			# can push, animate the push
			old_barrel_pos = barrel.pos
			barrel.move(diff)
			if is_move_animate_enabled:
				barrel.pos = old_barrel_pos
				barrel.animate(ARROW_KEYS_RESOLUTION)

	# can move, animate the move
	new_char_pos = char.pos

	# process lift movement if available
	if lift_target := get_lift_target(old_char_cell, diff):
		lift = get_actor_on_cell(old_char_cell, lifts)
		lift.move(diff)
		for i in range(1, distance):
			char.move(diff)
			lift.move(diff)
		if is_move_animate_enabled:
			lift.pos = old_char_pos
			lift.animate(animate_time_factor * ARROW_KEYS_RESOLUTION)

	leave_cell(old_char_cell)

	if is_move_animate_enabled:
		animate_duration = get_move_animate_duration(old_char_cell)
		prepare_enter_cell(animate_duration)
		char.pos = old_char_pos
		char.animate(animate_duration, on_finished=enter_cell)
	else:
		enter_cell()

	reveal_map_near_char()

def can_move(diff):
	dest_cell = apply_diff(char.c, diff)

	if not is_cell_in_room(dest_cell):
		return False

	return map[dest_cell] not in CELL_CHAR_MOVE_OBSTACLES \
		or map[dest_cell] == CELL_LOCK1 and drop_key1.num_collected > 0 \
		or map[dest_cell] == CELL_LOCK2 and drop_key2.num_collected > 0 \
		or is_cell_in_actors(dest_cell, lifts) \
		or get_lift_target(char.c, diff)

def update(dt):
	global level_title_timer, level_target_timer
	global game_time, level_time, idle_time, last_autogeneration_time
	global last_time_arrow_keys_processed, last_processed_arrow_keys, last_processed_arrow_diff

	if mode == 'start':
		init_new_level()
		return

	game_time += dt
	level_time += dt
	idle_time += dt

	for actor in active_inplace_animation_actors:
		actor.update_inplace_animation(level_time)

	puzzle.on_update(level_time)

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

	if char.is_animated():
		return

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
