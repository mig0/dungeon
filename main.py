#pgzero

import random
import pygame
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

def get_rel_map_cell_pos(c, pos):
	pos_x1, pos_y1 = get_map_cell_pos(*c)
	pos_x2, pos_y2 = pos
	return (pos_x1 + pos_x2, pos_y1 + pos_y2)

def get_rel_actor_pos(actor, pos):
	return get_rel_map_cell_pos(actor.c, pos)

def set_actor_coord(actor, cx, cy):
	actor.c = (cx, cy)
	actor.cx = cx
	actor.cy = cy
	actor.x, actor.y = get_map_cell_pos(cx, cy)

def create_actor(image_name, cx, cy):
	actor = Actor(image_name)
	set_actor_coord(actor, cx, cy)
	return actor

def move_map_actor(actor, diff_c):
	diff_cx, diff_cy = diff_c
	set_actor_coord(actor, actor.cx + diff_cx, actor.cy + diff_cy)

def get_all_neighbours(cx, cy, include_self=False):
	neighbours = []
	for dy in (-1, 0, +1):
		for dx in (-1, 0, +1):
			if dy == 0 and dx == 0 and not include_self:
				continue
			neighbours.append((cx + dx, cy + dy))
	return neighbours

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

mode = "start"
is_random_maze = False
is_barrel_puzzle = False
is_color_puzzle = False
is_four_rooms = False

game_time = 0
level_time = 0
idle_time = 0

last_autogeneration_time = 0

last_time_arrow_keys_processed = 0
pressed_arrow_keys = []
last_processed_arrow_keys = []

map = []  # will be generated
color_map = []
cells = {}  # will be generated
color_cells = []

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
current_room = None

def debug(level, str):
	if DEBUG_LEVEL < level:
		return
	print(str)

def debug_map(level, full=False, clean=False, combined=False, dual=False, endl=False):
	if DEBUG_LEVEL < level:
		return
	for cy in MAP_Y_RANGE if full else PLAY_Y_RANGE:
		if not combined:
			for cx in MAP_X_RANGE if full else PLAY_X_RANGE:
				print(CELL_FLOOR if clean and map[cy][cx] in CELL_FLOOR_ADDITIONS_RANDGEN else map[cy][cx], end="")
		if dual:
			print("    ", end="")
		if dual or combined:
			for cx in MAP_X_RANGE if full else PLAY_X_RANGE:
				cell_ch = CELL_FLOOR if clean and map[cy][cx] in CELL_FLOOR_ADDITIONS_RANDGEN else map[cy][cx]
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

def get_num_color_puzzle_values():
	return level["color_puzzle_values"] if "color_puzzle_values" in level else MAX_COLOR_PUZZLE_VALUES

def press_color_puzzle_cell(cx, cy):
	color_map[cy][cx] = (color_map[cy][cx] + 1) % get_num_color_puzzle_values()

def press_color_puzzle_neighbor_cells(cx, cy):
	for (nx, ny) in get_all_neighbors(cx, cy):
		press_color_puzzle_cell(nx, ny)

def get_color_puzzle_cell(cx, cy):
	return color_cells[color_map[cy][cx]]

def set_color_puzzle_vars(room):
	global color_puzzle_size_x, color_puzzle_size_y
	global color_puzzle_x1, color_puzzle_x2, color_puzzle_y1, color_puzzle_y2
	global color_puzzle_x_range, color_puzzle_y_range

	color_puzzle_size_x = level["color_puzzle_size"][0] if "color_puzzle_size" in level else DEFAULT_COLOR_PUZZLE_ROOM_SIZE_X[room] if room is not None else DEFAULT_COLOR_PUZZLE_PLAY_SIZE_X
	color_puzzle_size_y = level["color_puzzle_size"][1] if "color_puzzle_size" in level else DEFAULT_COLOR_PUZZLE_ROOM_SIZE_Y[room] if room is not None else DEFAULT_COLOR_PUZZLE_PLAY_SIZE_Y
	color_puzzle_x1 = room_x1 + int((room_size_x - color_puzzle_size_x) / 2)
	color_puzzle_x2 = color_puzzle_x1 + color_puzzle_size_x - 1
	color_puzzle_y1 = room_y1 + int((room_size_y - color_puzzle_size_y) / 2)
	color_puzzle_y2 = color_puzzle_y1 + color_puzzle_size_y - 1
	color_puzzle_x_range = range(color_puzzle_x1, color_puzzle_x2 + 1)
	color_puzzle_y_range = range(color_puzzle_y1, color_puzzle_y2 + 1)

def is_in_color_puzzle(cx, cy):
	return is_color_puzzle and cx in color_puzzle_x_range and cy in color_puzzle_y_range

def is_color_puzzle_plate(cx, cy):
	return is_in_color_puzzle(cx, cy) and (cx - color_puzzle_x1) % 2 == 1 and (cy - color_puzzle_y1) % 2 == 1

def is_color_puzzle_solved():
	for cy in color_puzzle_y_range:
		for cx in color_puzzle_x_range:
			if not is_color_puzzle_plate(cx, cy) and color_map[cy][cx] != COLOR_PUZZLE_VALUE_GREEN:
				return False
	return True

def set_room_vars(room):
	global room_size_x, room_size_y
	global room_x1, room_x2, room_y1, room_y2
	global room_x_range, room_y_range

	room_size_x = ROOM_SIZE_X[room] if room is not None else PLAY_SIZE_X
	room_size_y = ROOM_SIZE_Y[room] if room is not None else PLAY_SIZE_Y
	room_x1 = ROOM_X1[room] if room is not None else PLAY_X1
	room_x2 = ROOM_X2[room] if room is not None else PLAY_X2
	room_y1 = ROOM_Y1[room] if room is not None else PLAY_Y1
	room_y2 = ROOM_Y2[room] if room is not None else PLAY_Y2
	room_x_range = ROOM_X_RANGE[room] if room is not None else PLAY_X_RANGE
	room_y_range = ROOM_Y_RANGE[room] if room is not None else PLAY_Y_RANGE

def is_actor_in_room(actor):
	set_room_vars(current_room)

	return actor.cx >= room_x1 and actor.cx <= room_x2 and actor.cy >= room_y1 and actor.cy <= room_y2

def place_char_in_first_free_spot():
	set_room_vars(current_room)

	for cy in room_y_range:
		for cx in room_x_range:
			if map[cy][cx] not in CELL_CHAR_PLACE_OBSTACLES:
				for actor in enemies + barrels:
					if actor.cx == cx and actor.cy == cy:
						break
				else:
					set_actor_coord(char, cx, cy)
					return

	print("Was not able to find free spot for char, fix the level or a bug")
	if DEBUG_LEVEL:
		set_actor_coord(char, 0, 0)
	else:
		quit()

def get_random_floor_cell_type():
	return CELL_FLOOR_ADDITIONS_FREQUENT[randint(0, len(CELL_FLOOR_ADDITIONS_FREQUENT) - 1)]

def convert_to_floor_if_needed(cx, cy):
	if map[cy][cx] == CELL_BORDER or map[cy][cx] == CELL_INTERNAL1:
		map[cy][cx] = get_random_floor_cell_type()

def get_random_even_point(a1, a2):
	return a1 + randint(0, int((a2 - a1) / 2)) * 2

def generate_random_maze_room(x1, y1, x2, y2):
	if x2 - x1 <= 1 or y2 - y1 <= 1:
		return

	# select random point that will divide the area into 4 sub-areas
	random_x = get_random_even_point(x1 + 1, x2 - 1)
	random_y = get_random_even_point(y1 + 1, y2 - 1)

	# create the horizontal and vertical border wall via this point
	for x in range(x1, x2 + 1):
		map[random_y][x] = CELL_BORDER
	for y in range(y1, y2 + 1):
		map[y][random_x] = CELL_BORDER

	# select 3 random holes on the 4 just created border walls
	skipped_wall = randint(0, 3)
	if skipped_wall != 0: map[random_y][get_random_even_point(x1, random_x - 1)] = get_random_floor_cell_type()
	if skipped_wall != 1: map[get_random_even_point(y1, random_y - 1)][random_x] = get_random_floor_cell_type()
	if skipped_wall != 2: map[random_y][get_random_even_point(random_x + 1, x2)] = get_random_floor_cell_type()
	if skipped_wall != 3: map[get_random_even_point(random_y + 1, y2)][random_x] = get_random_floor_cell_type()

	# recurse into 4 sub-areas
	generate_random_maze_room(x1, y1, random_x - 1, random_y - 1)
	generate_random_maze_room(random_x + 1, y1, x2, random_y - 1)
	generate_random_maze_room(x1, random_y + 1, random_x - 1, y2)
	generate_random_maze_room(random_x + 1, random_y + 1, x2, y2)

def generate_barrel_room(x1, y1, x2, y2):
	global map

	num_barrels = level["num_barrels"] if "num_barrels" in level else DEFAULT_NUM_BARRELS

	def get_random_coords():
		return randint(x1, x2), randint(y1, y2)

	if False:
		for n in range(num_barrels):
			cx, cy = get_random_coords()
			barrel = create_actor("barrel", cx, cy)
			barrels.append(barrel)
		cx, cy = get_random_coords()
		map[cy][cx] = CELL_PORTAL
		cx, cy = get_random_coords()
		map[cy][cx] = CELL_BORDER

	# 0) initialize char position to None
	# 1) initialize entire room to BORDER
	for cy in range(y1, y2 + 1):
		for cx in range(x1, x2 + 1):
			map[cy][cx] = CELL_BORDER
	# 2) place room plates randomly or in good positions, as the number of barrels
	# 3) place room barrels into the place cells, one barrel per one plate
	for n in range(num_barrels):
		while True:
			cx, cy = get_random_coords()
			if map[cy][cx] != CELL_PLATE:
				map[cy][cx] = CELL_PLATE
				break
		barrel = create_actor("barrel", cx, cy)
		barrels.append(barrel)

	# 4) for each room barrel do:
	#    5) select one of 4 directions and place char to the "adjacent to barrel" cell (prefer empty cells)
	#    6) if the cell is not empty (BORDER), make it empty (FLOOR with additions)
	#    7) if the char position is not None, first create empty path to the selected adjacent cell
	#    8) for each move in random number of moves:
	#       9) either the move is push (only valid when char is adjacent to barrel), then pull the barrel
	#	   (make the cell empty if needed, check that there is no other barrel)
	#       10) or the move is free walk, then select one of 4 directions randomly (prefer empty cells)
	# 11) remember the char position, optionally try to move it as far left-top as possible

	while True:
		cx, cy = get_random_coords()
		if map[cy][cx] != CELL_PLATE:
			map[cy][cx] = get_random_floor_cell_type()
			break

def generate_room(room):
	global num_bonus_health, num_bonus_attack

	set_room_vars(room)

	if is_random_maze:
		generate_random_maze_room(room_x1, room_y1, room_x2, room_y2)

	if is_barrel_puzzle:
		generate_barrel_room(room_x1, room_y1, room_x2, room_y2)

	if is_color_puzzle:
		set_color_puzzle_vars(room)
		for cy in color_puzzle_y_range:
			for cx in color_puzzle_x_range:
				color_map[cy][cx] = COLOR_PUZZLE_VALUE_GREEN
				if is_color_puzzle_plate(cx, cy):
					map[cy][cx] = CELL_PLATE
					color_map[cy][cx] = COLOR_PUZZLE_VALUE_PLATE
		num_tries = 5
		while num_tries > 0:
			for n in range(color_puzzle_size_x * color_puzzle_size_y * 3):
				plate_cx = color_puzzle_x1 + randint(1, int(color_puzzle_size_x / 2)) * 2 - 1
				plate_cy = color_puzzle_y1 + randint(1, int(color_puzzle_size_y / 2)) * 2 - 1
				for i in range(randint(1, get_num_color_puzzle_values() - 1)):
					press_color_puzzle_neighbor_cells(plate_cx, plate_cy)
			if not is_color_puzzle_solved():
				break
			num_tries -= 1

	# generate enemies
	for i in range(level["num_enemies"] if "num_enemies" in level else DEFAULT_NUM_ENEMIES):
		positioned = False
		num_tries = 10000
		while not positioned and num_tries > 0:
			num_tries -= 1
			cx = randint(room_x1, room_x2)
			cy = randint(room_y1, room_y2)
			positioned = map[cy][cx] not in CELL_ENEMY_PLACE_OBSTACLES
			for other in (enemies + hearts + swords + barrels + [char]):
				if (cx, cy) == other.c:
					positioned = False
		if num_tries == 0:
			print("Was not able to find free spot for enemy in 10000 tries, positioning it anyway on an obstacle")
		enemy = create_actor("skeleton", cx, cy)
		enemy.health = randint(MIN_ENEMY_HEALTH, MAX_ENEMY_HEALTH)
		enemy.attack = randint(MIN_ENEMY_ATTACK, MAX_ENEMY_ATTACK)
		enemy.bonus = randint(0, 2)
		if enemy.bonus == BONUS_HEALTH:
			num_bonus_health += 1
		elif enemy.bonus == BONUS_ATTACK:
			num_bonus_attack += 1
		enemies.append(enemy)

def generate_map():
	global map, color_map, barrels, is_char_placed

	map = []
	for cy in range(0, MAP_SIZE_Y):
		if cy == 0 or cy == PLAY_SIZE_Y + 1:
			line = [CELL_BORDER] * MAP_SIZE_X
		elif cy == MAP_SIZE_Y - 1:
			line = [CELL_STATUS] * MAP_SIZE_X
		else:
			line = [CELL_BORDER]
			for cx in PLAY_X_RANGE:
				cell_type = get_random_floor_cell_type()
				if is_four_rooms and (cx == ROOM_BORDER_X or cy == ROOM_BORDER_Y):
					cell_type = CELL_BORDER
				line.append(cell_type)
			line.append(CELL_BORDER)
		map.append(line)

	barrels = []

	is_char_placed = False

	if is_color_puzzle:
		color_map = [[COLOR_PUZZLE_VALUE_OUTSIDE] * MAP_SIZE_X for y in range(0, MAP_SIZE_Y)]

	if is_four_rooms:
		for room in range(4):
			generate_room(room)
	else:
		generate_room(None)

	if not is_char_placed is None:
		place_char_in_first_free_spot()

def set_theme(theme_name):
	global cells, color_cells

	theme_prefix = theme_name + '/'
	cell0 = Actor(theme_prefix + 'status')
	cell1 = Actor(theme_prefix + 'border')
	cell2 = Actor(theme_prefix + 'floor')
	cell3 = Actor(theme_prefix + 'crack')
	cell4 = Actor(theme_prefix + 'bones')
	cell5 = Actor(theme_prefix + 'rocks')
	cell6 = Actor(theme_prefix + 'plate') if is_color_puzzle or is_barrel_puzzle else None
	cell7 = Actor(theme_prefix + 'portal') if is_barrel_puzzle else None

	if is_color_puzzle:
		gray_alpha_image = pygame.image.load('images/' + theme_prefix + 'floor_gray_alpha.png').convert_alpha()
		color_cells = []
		for color in COLOR_PUZZLE_RGB_VALUES:
			color_cell = pygame.Surface((CELL_W, CELL_H))
			color_cell.fill(color)
			color_cell.blit(gray_alpha_image, (0, 0))
			color_cells.append(color_cell)

	cells = {
		CELL_STATUS: cell0,
		CELL_BORDER: cell1,
		CELL_FLOOR:  cell2,
		CELL_CRACK:  cell3,
		CELL_BONES:  cell4,
		CELL_ROCKS:  cell5,
		CELL_PLATE:  cell6,
		CELL_PORTAL: cell7,
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

def reset_idle_time():
	global idle_time, last_autogeneration_time

	idle_time = 0
	last_autogeneration_time = 0

def init_new_level(offset=1):
	global level_idx, level, level_time, mode, is_game_won
	global is_random_maze, is_barrel_puzzle, is_color_puzzle
	global is_four_rooms, current_room
	global num_bonus_health, num_bonus_attack
	global enemies, hearts, swords, level_time

	if level_idx + offset < 0 or level_idx + offset > len(levels):
		print("Requested level is out of range")
		return

	stop_music()
	mode = "init"

	level_idx += offset
	if level_idx == len(levels):
		mode = "end"
		is_game_won = True
		start_music()
		return

	level = levels[level_idx]
	is_random_maze = "random_maze" in level
	is_barrel_puzzle = "barrel_puzzle" in level
	is_color_puzzle = "color_puzzle" in level
	is_four_rooms = "four_rooms" in level
	current_room = 0 if is_four_rooms else None

	char.health = level["char_health"]
	char.attack = INITIAL_CHAR_ATTACK

	hearts = []
	swords = []
	enemies = []
	num_bonus_health = 0
	num_bonus_attack = 0

	generate_map()
	set_theme(level["theme"])

	if "target" not in level:
		level["target"] = "default-level-target"

	level_time = 0
	reset_idle_time()
	reset_level_and_target_timer()

	mode = "game"
	start_music()

init_new_level()

def init_new_room():
	global current_room, mode

	if is_four_rooms:
		current_room += 1

	if not is_four_rooms or current_room == 4:
		init_new_level()
	else:
		place_char_in_first_free_spot()
		mode = "game"

def draw_map():
	for cy in range(len(map)):
		for cx in range(len(map[0])):
			cell_type = map[cy][cx]
			cell_types = [CELL_FLOOR if cell_type in CELL_FLOOR_ADDITIONS else cell_type]
			if cell_type in CELL_FLOOR_ADDITIONS:
				cell_types.append(cell_type)
			for cell_type in cell_types:
				if is_color_puzzle and cell_type == CELL_FLOOR and color_map[cy][cx] not in (COLOR_PUZZLE_VALUE_OUTSIDE, COLOR_PUZZLE_VALUE_PLATE):
					color_floor = get_color_puzzle_cell(cx, cy)
					screen.blit(color_floor, (CELL_W * cx, CELL_H * cy))
					continue
				cell = cells[cell_type]
				cell.left = CELL_W * cx
				cell.top = CELL_H * cy
				cell.draw()

def get_time_str(time):
	sec = int(time)
	min = sec / 60
	sec = sec % 60
	return "%d:%02d" % (min, sec) if min < 60 else "%d:%02d:%02d" % (min / 60, min % 60, sec)

def draw_status():
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
	if mode == "game" or mode == "end" or mode == "next":
		draw_map()
		draw_status()
		for barrel in barrels:
			barrel.draw()
		for enemy in killed_enemies:
			enemy.draw()
		for enemy in enemies:
			enemy.draw()
		for heart in hearts:
			heart.draw()
		for sword in swords:
			sword.draw()
		char.draw()
		for actor in enemies + [char]:
			if actor.health is None:
				continue
			screen.draw.text(str(actor.health), center=get_rel_actor_pos(actor, (-12, -CELL_H * 0.5 - 14)), color="#AAFF00", gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.8, fontsize=24)
			screen.draw.text(str(actor.attack), center=get_rel_actor_pos(actor, (+12, -CELL_H * 0.5 - 14)), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=0.8, fontsize=24)

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

def kill_enemy():
	enemy = killed_enemies.pop(0)

def on_key_down(key):
	global lang
	global is_move_animate_enabled

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
		return

	if keyboard.k_0:
		set_theme("classic")
	if keyboard.k_1:
		set_theme("ancient1")
	if keyboard.k_2:
		set_theme("modern1")
	if keyboard.k_3:
		set_theme("modern2")

	if keyboard.p:
		init_new_level(-1)
	if keyboard.r:
		init_new_level(0)
	if keyboard.n:
		init_new_level(+1)

	if keyboard.l:
		reset_level_and_target_timer()

	if keyboard.m:
		if is_music_enabled:
			disable_music()
		else:
			enable_music()
	if keyboard.a:
		is_move_animate_enabled = not is_move_animate_enabled

	if keyboard.q:
		quit()

	if keyboard.space and is_color_puzzle and map[char.cy][char.cx] == CELL_PLATE:
		press_color_puzzle_neighbor_cells(char.cx, char.cy)
		set_color_puzzle_vars(current_room)
		if is_color_puzzle_solved():
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

	room_enemies = [ enemy for enemy in enemies if is_actor_in_room(enemy) ]

	if "time_limit" in level and level_time > level["time_limit"]:
		loose_game()
	elif is_color_puzzle or char.health is None:
		pass
	elif not room_enemies and not killed_enemies and char.health > MIN_CHAR_HEALTH:
		win_room()
	elif char.health <= MIN_CHAR_HEALTH or "time_limit" in level and level_time > level["time_limit"]:
		loose_game()

def move_char(diff_x, diff_y):
	old_char_pos = char.pos

	move_map_actor(char, (diff_x, diff_y))

	# collision with enemies
	enemy_index = char.collidelist(enemies)
	if enemy_index == -1:
		new_char_pos = char.pos
		if is_move_animate_enabled:
			char.pos = old_char_pos
			animate(char, duration=ARROW_KEYS_RESOLUTION, pos=new_char_pos)
	else:
		enemy = enemies[enemy_index]
		enemy.health -= char.attack
		char.health -= enemy.attack
		enemy.pos = get_actor_pos(enemy)
		move_map_actor(char, (-diff_x, -diff_y))
		enemy.pos = get_rel_actor_pos(enemy, (diff_x * 12, diff_y * 12))
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

def update(dt):
	global level_title_timer, level_target_timer, num_bonus_health, num_bonus_attack
	global game_time, level_time, idle_time, last_autogeneration_time
	global last_time_arrow_keys_processed, last_processed_arrow_keys

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
		if map[char.cy + diff[1]][char.cx + diff[0]] not in CELL_CHAR_MOVE_OBSTACLES:
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
