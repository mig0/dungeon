#pgzero

import random
import pygame

# game constants
TITLE = "Skull Labyrinth"
FPS = 30

PLAY_MAP_SIZE_X = 12
PLAY_MAP_SIZE_Y = 10
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

BONUS_NONE   = 0
BONUS_HEALTH = 1
BONUS_ATTACK = 2

ARROW_KEY_R = pygame.K_RIGHT
ARROW_KEY_L = pygame.K_LEFT
ARROW_KEY_D = pygame.K_DOWN
ARROW_KEY_U = pygame.K_UP

translations = {
	'en': {
		'level-label': "Level",
		'level-1-name': "First skeleton encounter",
		'level-2-name': "More skeletons...",
		'level-3-name': "Even more skeletons...",
		'level-4-name': "Help me with the skeletons!",
		'level-target-label': "Level target",
		'default-level-target': "Kill all enemies",
		'victory-text': "Victory!",
		'defeat-text': "Defeat...",
	},
	'ru': {
		'level-label': "Уровень",
		'level-1-name': "Первая встреча со скелетами",
		'level-2-name': "Больше скелетов",
		'level-3-name': "Еще больше скелетов...",
		'level-4-name': "Помогите мне со скелетами!",
		'level-target-label': "Цель уровня",
		'default-level-target': "Уничтожь всех врагов",
		'victory-text': "Победа!",
		'defeat-text': "Поражение...",
	},
	'he': {
		'level-label': "שלב",
		'level-1-name': "פגישה ראשונה עם שלדים",
		'level-2-name': "יותר שלדים",
		'level-3-name': "עוד יותר שלדים",
		'level-4-name': "עזרו לי עם השלדים!",
		'level-target-label': "מטרת השלב",
		'default-level-target': "תחסל את כל האויבים",
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

# game sprites
cell1 = None
cell2 = None
cell3 = None
cell4 = None
cell5 = None
cell6 = None

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

game_time = 0
last_time_arrow_keys_processed = 0

pressed_arrow_keys = []
last_processed_arrow_keys = []

map = []  # will be generated
map_cells = []  # will be generated

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
	},
	{
		"n": 4,
		"num_enemies": int(PLAY_MAP_SIZE_X * PLAY_MAP_SIZE_Y / 2),
		"theme": "modern2",
		"music": "breath",
		"char_health": 500,
	},
]
level = None
level_idx = -1

def generate_map():
	for y in range(MAP_SIZE_Y):
		if y == 0 or y == PLAY_MAP_SIZE_Y + 1:
			line = [4] * MAP_SIZE_X
		elif y == MAP_SIZE_Y - 1:
			line = [5] * MAP_SIZE_X
		else:
			line = [4]
			for x in range(PLAY_MAP_SIZE_X):
				cell_type = random.randint(0, 3 + EMPTY_FLOOR_FREQUENCY)
				if cell_type > 3: cell_type = 0
				line.append(cell_type)
			line.append(4)
		map.append(line)

def set_theme(theme_name):
	global cell1, cell2, cell3, cell4, cell5, cell6, map_cells

	theme_prefix = theme_name + '/'
	cell1 = Actor(theme_prefix + 'floor')
	cell2 = Actor(theme_prefix + 'crack')
	cell3 = Actor(theme_prefix + 'bones')
	cell4 = Actor(theme_prefix + 'rocks')
	cell5 = Actor(theme_prefix + 'border')
	cell6 = Actor(theme_prefix + 'status')

	map_cells = [ cell1, cell2, cell3, cell4, cell5, cell6 ]

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
	global level_idx, level, mode, is_game_won, num_bonus_health, num_bonus_attack, enemies, hearts, swords

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

	mode = "game"
	start_music()

init_new_level()

def draw_map():
	for i in range(len(map)):
		for j in range(len(map[0])):
			cell_type = map[i][j]
			cell_types = [0]
			if cell_type > 0:
				cell_types.append(cell_type)
			for cell_type in cell_types:
				map_cell = map_cells[cell_type]
				map_cell.left = CELL_W * j
				map_cell.top = CELL_H * i
				map_cell.draw()

def draw_status():
	status_heart.draw()
	screen.draw.text(str(num_bonus_health), center=(POS_CENTER_X - 1 * CELL_W / 2, POS_STATUS_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=1, fontsize=24)
	status_sword.draw()
	screen.draw.text(str(num_bonus_attack), center=(POS_CENTER_X + 2 * CELL_W / 2, POS_STATUS_Y), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=1, fontsize=24)

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

def check_victory():
	global mode, is_game_won

	if mode != "game":
		return

	if not enemies and not killed_enemies and char.health > MIN_CHAR_HEALTH:
		play_sound("finish")
		mode = "next"
		clock.schedule(init_new_level, 1.5)
	elif char.health <= MIN_CHAR_HEALTH:
		stop_music()
		mode = "end"
		is_game_won = False
		start_music()

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
	global game_time, last_time_arrow_keys_processed, last_processed_arrow_keys

	game_time += dt

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
