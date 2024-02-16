#pgzero

import random
import pygame
from copy import deepcopy

# game constants
TITLE = "Skull Labyrinth"
FPS = 30

PLAY_MAP_SIZE_X = 11
PLAY_MAP_SIZE_Y = 11
MAP_SIZE_X = PLAY_MAP_SIZE_X + 2
MAP_SIZE_Y = PLAY_MAP_SIZE_Y + 3

CELL_W = 64
CELL_H = 64
WIDTH = CELL_W * MAP_SIZE_X
HEIGHT = CELL_H * MAP_SIZE_Y
POS_CENTER_X = WIDTH / 2
POS_CENTER_Y = HEIGHT / 2
POS_STATUS_Y = HEIGHT - CELL_H / 2

MIN_ENEMY_HEALTH = 5
MAX_ENEMY_HEALTH = 15
MIN_ENEMY_ATTACK = 5
MAX_ENEMY_ATTACK = 10
MIN_CHAR_HEALTH = 0
#INITIAL_CHAR_HEALTH = 100
INITIAL_CHAR_ATTACK = 5
BONUS_HEALTH_VALUE = 7
BONUS_ATTACK_VALUE = 7
EMPTY_FLOOR_FREQUENCY = 3  # 0 means empty floor is as frequent as non empty
ARROW_KEYS_RESOLUTION = 0.18
ALLOW_DIAGONAL_MOVES = True
CRITICAL_REMAINING_LEVEL_TIME = 20

BONUS_NONE   = 0
BONUS_HEALTH = 1
BONUS_ATTACK = 2

ARROW_KEY_R = pygame.K_RIGHT
ARROW_KEY_L = pygame.K_LEFT
ARROW_KEY_D = pygame.K_DOWN
ARROW_KEY_U = pygame.K_UP

CELL_FLOOR = 0
CELL_CRACK = 1
CELL_BONES = 2
CELL_ROCKS = 3
CELL_PLATE = 4
CELL_BORDER = 5
CELL_STATUS = 6

CELL_FLOOR_ADDITIONS_RANDGEN = (CELL_CRACK, CELL_BONES, CELL_ROCKS)
CELL_FLOOR_ADDITIONS_FREQUENT = (*CELL_FLOOR_ADDITIONS_RANDGEN, *((CELL_FLOOR,) * EMPTY_FLOOR_FREQUENCY))
CELL_FLOOR_ADDITIONS = (*CELL_FLOOR_ADDITIONS_RANDGEN, CELL_PLATE)

COLOR_PUZZLE_SIZE_X = 11
COLOR_PUZZLE_SIZE_Y = 11
NUM_COLOR_PUZZLE_VALUES = 6

COLOR_MAP_SOLVED = [[1] * COLOR_PUZZLE_SIZE_X for y in range(COLOR_PUZZLE_SIZE_Y)]

COLOR_PUZZLE_X1 = int((PLAY_MAP_SIZE_X - COLOR_PUZZLE_SIZE_X) / 2) + 1
COLOR_PUZZLE_X2 = int((PLAY_MAP_SIZE_X - COLOR_PUZZLE_SIZE_X) / 2) + COLOR_PUZZLE_SIZE_X
COLOR_PUZZLE_Y1 = int((PLAY_MAP_SIZE_Y - COLOR_PUZZLE_SIZE_Y) / 2) + 1
COLOR_PUZZLE_Y2 = int((PLAY_MAP_SIZE_Y - COLOR_PUZZLE_SIZE_Y) / 2) + COLOR_PUZZLE_SIZE_Y

COLOR_PUZZLE_X_RANGE = range(COLOR_PUZZLE_X1, COLOR_PUZZLE_X2 + 1)
COLOR_PUZZLE_Y_RANGE = range(COLOR_PUZZLE_Y1, COLOR_PUZZLE_Y2 + 1)

translations = {
	'en': {
		'level-label': "Level",
		'level-1-name': "First skeleton encounter",
		'level-2-name': "More skeletons...",
		'level-3-name': "Even more skeletons...",
		'level-4-name': "Solve color puzzle!",
		'level-5-name': "Help me with the skeletons!",
		'level-target-label': "Level target",
		'default-level-target': "Kill all enemies",
		'level-target-kill-1-min': "Kill all enemies in 1 minute",
		'complete-color-puzzle-green': "Make all floor green",
		'victory-text': "Victory!",
		'defeat-text': "Defeat...",
	},
	'ru': {
		'level-label': "Уровень",
		'level-1-name': "Первая встреча со скелетами",
		'level-2-name': "Больше скелетов",
		'level-3-name': "Еще больше скелетов...",
		'level-4-name': "Реши головоломку с цветами!",
		'level-5-name': "Помогите мне со скелетами!",
		'level-target-label': "Цель уровня",
		'default-level-target': "Уничтожь всех врагов",
		'level-target-kill-1-min': "Уничтожь всех врагов за 1 минуту",
		'complete-color-puzzle-green': "Сделай весь пол зелёным",
		'victory-text': "Победа!",
		'defeat-text': "Поражение...",
	},
	'he': {
		'level-label': "שלב",
		'level-1-name': "פגישה ראשונה עם שלדים",
		'level-2-name': "יותר שלדים",
		'level-3-name': "עוד יותר שלדים",
		'level-4-name': "תפתור מסימת הצבעים!",
		'level-5-name': "עזרו לי עם השלדים!",
		'level-target-label': "מטרת השלב",
		'default-level-target': "תחסל את כל האויבים",
		'level-target-kill-1-min': "תחסל את כל האויבים בדקה אחת",
		'complete-color-puzzle-green': "תעשה את כל הרצפה ירוקה",
		'victory-text': "נצחון!",
		'defeat-text': "הפסד...",
	},
}

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

def get_map_cell_pos(x, y):
	return (CELL_W * (x + 0.5), CELL_H * (y + 0.5))

def get_actor_pos(actor):
	return get_map_cell_pos(*actor.c)

def get_rel_map_cell_pos(c, pos):
	pos_x1, pos_y1 = get_map_cell_pos(*c)
	pos_x2, pos_y2 = pos
	return (pos_x1 + pos_x2, pos_y1 + pos_y2)

def get_rel_actor_pos(actor, pos):
	return get_rel_map_cell_pos(actor.c, pos)

def set_actor_coord(actor, x, y):
	actor.c = (x, y)
	actor.cx = x
	actor.cy = y
	actor.x, actor.y = get_map_cell_pos(x, y)

def create_actor(image_name, x, y):
	actor = Actor(image_name)
	set_actor_coord(actor, x, y)
	return actor

def move_map_actor(actor, c):
	x, y = c
	set_actor_coord(actor, actor.cx + x, actor.cy + y)

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
is_color_puzzle = False

game_time = 0
level_time = 0
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

num_bonus_health = 0
num_bonus_attack = 0

killed_enemies = []

level_title_timer = 0
level_target_timer = 0

levels = [
	{
		"n": 1,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"char_health": 100,
	},
	{
		"n": 2,
		"num_enemies": 10,
		"theme": "ancient1",
		"music": "playful_sparrow",
		"char_health": 150,
	},
	{
		"n": 3,
		"num_enemies": 15,
		"theme": "modern1",
		"music": "adventures",
		"char_health": 200,
		"time_limit": 60,
		"target": 'level-target-kill-1-min',
	},
	{
		"n": 4,
		"num_enemies": 0,
		"theme": "modern1",
		"music": "valiant_warriors",
		"color_puzzle": True,
		"time_limit": 80,
		"char_health": None,
		"target": 'complete-color-puzzle-green',
	},
	{
		"n": 5,
		"num_enemies": int(PLAY_MAP_SIZE_X * PLAY_MAP_SIZE_Y / 2),
		"theme": "modern2",
		"music": "breath",
		"char_health": 500,
	},
]
level = None
level_idx = -1

def get_color_puzzle_cell_value(cx, cy):
	return color_map[cy - COLOR_PUZZLE_Y1][cx - COLOR_PUZZLE_X1]

def set_color_puzzle_cell_value(cx, cy, n):
	color_map[cy - COLOR_PUZZLE_Y1][cx - COLOR_PUZZLE_X1] = n

def press_color_puzzle_cell(cx, cy):
	set_color_puzzle_cell_value(cx, cy, (get_color_puzzle_cell_value(cx, cy) + 1) % NUM_COLOR_PUZZLE_VALUES)

def press_color_puzzle_neighbour_cells(cx, cy):
	for (nx, ny) in get_all_neighbours(cx, cy):
		press_color_puzzle_cell(nx, ny)

def get_color_puzzle_cell(cx, cy):
	return color_cells[get_color_puzzle_cell_value(cx, cy)]

def is_in_color_puzzle(cx, cy):
	return is_color_puzzle and cx in COLOR_PUZZLE_X_RANGE and cy in COLOR_PUZZLE_Y_RANGE

def is_color_puzzle_plate(cx, cy):
	return is_in_color_puzzle(cx, cy) and (cx - COLOR_PUZZLE_X1) % 2 == 1 and (cy - COLOR_PUZZLE_Y1) % 2 == 1

def generate_map():
	global map, color_map

	map = []
	for cy in range(0, MAP_SIZE_Y):
		if cy == 0 or cy == PLAY_MAP_SIZE_Y + 1:
			line = [CELL_BORDER] * MAP_SIZE_X
		elif cy == MAP_SIZE_Y - 1:
			line = [CELL_STATUS] * MAP_SIZE_X
		else:
			line = [CELL_BORDER]
			for cx in range(1, MAP_SIZE_X - 1):
				cell_type = CELL_FLOOR_ADDITIONS_FREQUENT[random.randint(0, len(CELL_FLOOR_ADDITIONS_FREQUENT) - 1)]
				if is_color_puzzle_plate(cx, cy):
					cell_type = CELL_PLATE
				line.append(cell_type)
			line.append(CELL_BORDER)
		map.append(line)

	if is_color_puzzle:
		color_map = deepcopy(COLOR_MAP_SOLVED)
		num_tries = 5
		while num_tries > 0:
			for n in range(COLOR_PUZZLE_SIZE_X * COLOR_PUZZLE_SIZE_Y * 3):
				plate_cx = COLOR_PUZZLE_X1 + random.randint(1, int(COLOR_PUZZLE_SIZE_X / 2)) * 2 - 1
				plate_cy = COLOR_PUZZLE_Y1 + random.randint(1, int(COLOR_PUZZLE_SIZE_Y / 2)) * 2 - 1
				for i in range(random.randint(1, NUM_COLOR_PUZZLE_VALUES - 1)):
					press_color_puzzle_neighbour_cells(plate_cx, plate_cy)
			if color_map != COLOR_MAP_SOLVED:
				break
			num_tries -= 1

def set_theme(theme_name):
	global cells, color_cells

	theme_prefix = theme_name + '/'
	cell1 = Actor(theme_prefix + 'floor')
	cell2 = Actor(theme_prefix + 'crack')
	cell3 = Actor(theme_prefix + 'bones')
	cell4 = Actor(theme_prefix + 'rocks')
	cell5 = Actor(theme_prefix + 'plate') if is_color_puzzle else None
	cell6 = Actor(theme_prefix + 'border')
	cell7 = Actor(theme_prefix + 'status')

	if is_color_puzzle:
		gray_alpha_image = pygame.image.load('images/' + theme_prefix + 'floor_gray_alpha.png').convert_alpha()
		color_cells = []
		for color in ((255, 80, 80), (80, 255, 80), (80, 80, 255), (255, 255, 80), (80, 255, 255), (255, 80, 255)):
			color_cell = pygame.Surface((CELL_W, CELL_H))
			color_cell.fill(color)
			color_cell.blit(gray_alpha_image, (0, 0))
			color_cells.append(color_cell)

	cells = {
		CELL_FLOOR: cell1,
		CELL_CRACK: cell2,
		CELL_BONES: cell3,
		CELL_ROCKS: cell4,
		CELL_PLATE: cell5,
		CELL_BORDER: cell6,
		CELL_STATUS: cell7,
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

def init_new_level(offset=1):
	global level_idx, level, level_time, mode, is_color_puzzle, is_game_won
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
	is_color_puzzle = "color_puzzle" in level

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

	# generate enemies
	for i in range(level["num_enemies"]):
		positioned = False
		num_tries = 10000
		while not positioned and num_tries > 0:
			num_tries -= 1
			x = random.randint(1, PLAY_MAP_SIZE_X)
			y = random.randint(1, PLAY_MAP_SIZE_Y)
			positioned = True
			for other in (enemies + hearts + swords + [char]):
				if (x, y) == other.c:
					positioned = False
		if num_tries == 0:
			print("Was not able to find free spot for enemy in 10000 tries, positioning it anyway on an obstacle")
		enemy = create_actor("skeleton", x, y)
		enemy.health = random.randint(MIN_ENEMY_HEALTH, MAX_ENEMY_HEALTH)
		enemy.attack = random.randint(MIN_ENEMY_ATTACK, MAX_ENEMY_ATTACK)
		enemy.bonus = random.randint(0, 2)
		if enemy.bonus == BONUS_HEALTH:
			num_bonus_health += 1
		elif enemy.bonus == BONUS_ATTACK:
			num_bonus_attack += 1
		enemies.append(enemy)

	reset_level_and_target_timer()
	level_time = 0

	mode = "game"
	start_music()

init_new_level()

def draw_map():
	for cy in range(len(map)):
		for cx in range(len(map[0])):
			cell_type = map[cy][cx]
			cell_types = [CELL_FLOOR if cell_type in CELL_FLOOR_ADDITIONS else cell_type]
			if cell_type in CELL_FLOOR_ADDITIONS:
				cell_types.append(cell_type)
			for cell_type in cell_types:
				if is_in_color_puzzle(cx, cy) and cell_type == CELL_FLOOR and not is_color_puzzle_plate(cx, cy):
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

	if keyboard.space and is_color_puzzle_plate(char.cx, char.cy):
		press_color_puzzle_neighbour_cells(char.cx, char.cy)

def loose_game():
	global mode, is_game_won

	stop_music()
	mode = "end"
	is_game_won = False
	start_music()

def win_level():
	global mode

	play_sound("finish")
	mode = "next"
	clock.schedule(init_new_level, 1.5)

def check_victory():
	if mode != "game":
		return

	if "time_limit" in level and level_time > level["time_limit"]:
		loose_game()
	elif is_color_puzzle:
		if color_map == COLOR_MAP_SOLVED:
			win_level()
	elif not enemies and not killed_enemies and char.health > MIN_CHAR_HEALTH:
		win_level()
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
			enemy.angle = (random.randint(-1, 1) + 2) * 90
			killed_enemies.append(enemy)
			clock.schedule(kill_enemy, 0.3)

def update(dt):
	global level_title_timer, level_target_timer, num_bonus_health, num_bonus_attack
	global game_time, level_time, last_time_arrow_keys_processed, last_processed_arrow_keys

	game_time += dt
	level_time += dt

	if level_title_timer > 0:
		level_title_timer -= 1
	elif level_target_timer > 0:
		level_target_timer -= 1

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
		if not keys[key] and key in pressed_arrow_keys and key in last_processed_arrow_keys:
			pressed_arrow_keys.remove(key)

	if game_time - last_time_arrow_keys_processed < ARROW_KEYS_RESOLUTION:
		return

	last_time_arrow_keys_processed = game_time
	last_processed_arrow_keys = []

	def set_arrow_key_to_process(key, condition=True):
		if not ALLOW_DIAGONAL_MOVES and last_processed_arrow_keys:
			return
		pressed_arrow_keys.remove(key)
		if condition:
			last_processed_arrow_keys.append(key)

	for key in list(pressed_arrow_keys):
		if key == ARROW_KEY_R and key not in last_processed_arrow_keys and ARROW_KEY_L not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, char.cx < PLAY_MAP_SIZE_X)
		if key == ARROW_KEY_L and key not in last_processed_arrow_keys and ARROW_KEY_R not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, char.cx > 1)
		if key == ARROW_KEY_D and key not in last_processed_arrow_keys and ARROW_KEY_U not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, char.cy < PLAY_MAP_SIZE_Y)
		if key == ARROW_KEY_U and key not in last_processed_arrow_keys and ARROW_KEY_D not in last_processed_arrow_keys:
			set_arrow_key_to_process(key, char.cy > 1)

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
