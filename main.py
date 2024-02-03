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
MAX_GAME_BATTLES = 3

BONUS_NONE   = 0
BONUS_HEALTH = 1
BONUS_ATTACK = 2

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
mode = "start"

map = []  # will be generated
map_cells = []  # will be generated

enemies = []
hearts = []
swords = []

num_bonus_health = 0
num_bonus_attack = 0

killed_enemies = []

init_level_timer = 0

levels = [
	{
		"n": 1,
		"name": "First skeleton encounter",
		"num_enemies": 5,
		"theme": "classic",
		"char_health": 100,
	},
	{
		"n": 2,
		"name": "More skeletons...",
		"num_enemies": 10,
		"theme": "ancient1",
		"char_health": 150,
	},
	{
		"n": 3,
		"name": "Even more skeletons...",
		"num_enemies": 15,
		"theme": "modern1",
		"char_health": 200,
	},
	{
		"n": 4,
		"name": "Help me with skeletons!",
		"num_enemies": PLAY_MAP_SIZE_X * PLAY_MAP_SIZE_Y - 1,
		"theme": "modern2",
		"char_health": 10000,
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

def init_new_level(offset=1):
	global level_idx, level, mode, is_game_won, init_level_timer, num_bonus_health, num_bonus_attack, enemies, hearts, swords

	if level_idx + offset < 0 or level_idx + offset > len(levels):
		print("Requested level is out of range")
		return

	mode = "init"

	level_idx += offset
	if level_idx == len(levels):
		mode = "end"
		is_game_won = True
		return

	level = levels[level_idx]
	init_level_timer = 4 * 60  # 4 seconds

	char.health = level["char_health"]
	char.attack = INITIAL_CHAR_ATTACK

	hearts = []
	swords = []
	enemies = []
	num_bonus_health = 0
	num_bonus_attack = 0

	generate_map()
	set_theme(level["theme"])

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

	mode = "game"

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
	health_label = "HP:"
	health_value = str(char.health)
	attack_label = "AP:"
	attack_value = str(char.attack)
	screen.draw.text(health_label, center=(00000 + CELL_W * 0.5, POS_STATUS_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
	screen.draw.text(health_value, center=(00000 + CELL_W * 1.5, POS_STATUS_Y), color="#AAFF00", gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
	screen.draw.text(attack_label, center=(WIDTH - CELL_W * 1.5, POS_STATUS_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
	screen.draw.text(attack_value, center=(WIDTH - CELL_W * 0.5, POS_STATUS_Y), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
	status_heart.draw()
	screen.draw.text(str(num_bonus_health), center=(POS_CENTER_X - 1 * CELL_W / 2, POS_STATUS_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=1, fontsize=24)
	status_sword.draw()
	screen.draw.text(str(num_bonus_attack), center=(POS_CENTER_X + 2 * CELL_W / 2, POS_STATUS_Y), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=1, fontsize=24)

def draw():
	screen.fill("#2f3542")
	if mode == 'game' or mode == "end":
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
		for enemy in enemies:
			screen.draw.text(str(enemy.health), center=get_rel_actor_pos(enemy, (-12, -CELL_H * 0.5 - 14)), color="#AAFF00", gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.8, fontsize=24)
			screen.draw.text(str(enemy.attack), center=get_rel_actor_pos(enemy, (+12, -CELL_H * 0.5 - 14)), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=0.8, fontsize=24)

	if mode == "end":
		msg_surface = pygame.Surface((WIDTH, 80))
		msg_surface.set_alpha(50)
		msg_surface.fill((0, 0, 0))
		screen.blit(msg_surface, (0, POS_CENTER_Y - 40))
		screen.draw.text("Victory!" if is_game_won else "Defeat...", center=(POS_CENTER_X, POS_CENTER_Y), color='white', gcolor=("#008080" if is_game_won else "#800000"), owidth=0.8, ocolor="#202020", alpha=1, fontsize=60)

	if mode == "game" and init_level_timer > 0:
		msg_surface = pygame.Surface((WIDTH, 120))
		msg_surface.set_alpha(50)
		msg_surface.fill((0, 40, 40))
		screen.blit(msg_surface, (0, POS_CENTER_Y - 60))
		level_line_1 = "Level " + str(level["n"])
		level_line_2 = level["name"]
		screen.draw.text(level_line_1, center=(POS_CENTER_X, POS_CENTER_Y - 20), color='yellow', gcolor="#AAA060", owidth=1.2, ocolor="#404030", alpha=1, fontsize=50)
		screen.draw.text(level_line_2, center=(POS_CENTER_X, POS_CENTER_Y + 18), color='white', gcolor="#C08080", owidth=1.2, ocolor="#404030", alpha=1, fontsize=32)

def kill_enemy():
	enemy = killed_enemies.pop(0)

def on_key_down(key):
	if mode != "game" and mode != "end":
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

	diff = None

	if keyboard.right and char.cx < PLAY_MAP_SIZE_X:
		diff = (+1, 0)
		char.image = 'stand'
	elif keyboard.left and char.cx > 1:
		diff = (-1, 0)
		char.image = 'left'
	elif keyboard.down and char.cy < PLAY_MAP_SIZE_Y:
		diff = (0, +1)
	elif keyboard.up and char.cy > 1:
		diff = (0, -1)

	if diff:
		move_map_actor(char, diff)

	# collision with enemies
	enemy_index = char.collidelist(enemies)
	if enemy_index != -1:
		enemy = enemies[enemy_index]
		enemy.health -= char.attack
		char.health -= enemy.attack
		enemy.pos = get_actor_pos(enemy)
		if diff:
			move_map_actor(char, (-diff[0], -diff[1]))
			enemy.pos = get_rel_actor_pos(enemy, (diff[0] * 12, diff[1] * 12))
		if enemy.health > 0:
			animate(enemy, tween='bounce_end', duration=0.4, pos=get_actor_pos(enemy))
		else:
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

def check_victory():
	global mode

	if mode != "game":
		return

	if not enemies and not killed_enemies and char.health > MIN_CHAR_HEALTH:
		init_new_level()
	elif char.health <= MIN_CHAR_HEALTH:
		mode = "end"

def update(dt):
	global init_level_timer, num_bonus_health, num_bonus_attack

	if init_level_timer > 0:
		init_level_timer -= 1

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
