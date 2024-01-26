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

CELL_W = 50
CELL_H = 50
WIDTH = CELL_W * MAP_SIZE_X
HEIGHT = CELL_H * MAP_SIZE_Y

MIN_ENEMY_HEALTH = 10
MAX_ENEMY_HEALTH = 20
MIN_ENEMY_ATTACK = 5
MAX_ENEMY_ATTACK = 10
MIN_CHAR_HEALTH = 0
INITIAL_CHAR_HEALTH = 100
INITIAL_CHAR_ATTACK = 5
BONUS_HEALTH = 7
BONUS_ATTACK = 7
MAX_ENEMIES = 5
MAX_GAME_BATTLES = 3
CENTER_X = WIDTH / 2
STATUS_Y = HEIGHT - CELL_H / 2

# game sprites
cell1 = Actor('floor')
cell2 = Actor("crack")
cell3 = Actor("bones")
cell4 = Actor('rock')
cell5 = Actor('border')
cell6 = Actor('marble')

char = Actor('stand', topleft=(CELL_W, CELL_H))

# game variables
num_battles_won = 0
is_game_won = False
mode = "game"

my_map = []  # will be generated
map_cells = [ cell1, cell2, cell3, cell4, cell5, cell6 ]

enemies = []
hearts = []
swords = []

def generate_map():
	for y in range(MAP_SIZE_Y):
		if y == 0 or y == PLAY_MAP_SIZE_Y + 1:
			line = [4] * MAP_SIZE_X
		elif y == MAP_SIZE_Y - 1:
			line = [5] * MAP_SIZE_X
		else:
			line = [4]
			for x in range(PLAY_MAP_SIZE_X):
				line.append(random.randint(0, 3))
			line.append(4)
		my_map.append(line)

def init_game():
	char.health = INITIAL_CHAR_HEALTH
	char.attack = INITIAL_CHAR_ATTACK
	generate_map()
	# generate enemies
	for i in range(MAX_ENEMIES):
		positioned = False
		num_tries = 10000
		while not positioned and num_tries > 0:
			num_tries -= 1
			left = random.randint(1, 7) * CELL_W
			top  = random.randint(1, 7) * CELL_H
			positioned = True
			for other in (enemies + hearts + swords + [char]):
				if left == other.left and top == other.top:
					positioned = False
		if num_tries == 0:
			print("Was not able to find free spot for enemy in 10000 tries, positioning it anyway on an obstacle")
		enemy = Actor("skeleton", topleft=(left, top))
		enemy.health = random.randint(MIN_ENEMY_HEALTH, MAX_ENEMY_HEALTH)
		enemy.attack = random.randint(MIN_ENEMY_ATTACK, MAX_ENEMY_ATTACK)
		enemy.bonus = random.randint(0, 2)
		enemies.append(enemy)

init_game()

def draw_map():
	for i in range(len(my_map)):
		for j in range(len(my_map[0])):
			map_cell = map_cells[my_map[i][j]]
			map_cell.left = CELL_W * j
			map_cell.top = CELL_H * i
			map_cell.draw()

def draw_status():
	health_label = "HP:"
	health_value = str(char.health)
	attack_label = "AP:"
	attack_value = str(char.attack)
	screen.draw.text(health_label, center=(00000 + CELL_W * 0.5, STATUS_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
	screen.draw.text(health_value, center=(00000 + CELL_W * 1.5, STATUS_Y), color="#AAFF00", gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
	screen.draw.text(attack_label, center=(WIDTH - CELL_W * 1.5, STATUS_Y), color='#FFFFFF', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
	screen.draw.text(attack_value, center=(WIDTH - CELL_W * 0.5, STATUS_Y), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)

def draw():
	screen.fill("#2f3542")
	if mode == 'game' or mode == "end":
		draw_map()
		draw_status()
		char.draw()
		for enemy in enemies:
			enemy.draw()
		for heart in hearts:
			heart.draw()
		for sword in swords:
			sword.draw()
		for enemy in enemies:
			screen.draw.text(str(enemy.health), center=(enemy.left + CELL_W / 2, enemy.top - 34), color="#AAFF00", gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
			screen.draw.text(str(enemy.attack), center=(enemy.left + CELL_W / 2, enemy.top - 14), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)

	if mode == "end":
		msg_surface = pygame.Surface((WIDTH, 60))
		msg_surface.set_alpha(50)
		msg_surface.fill((0, 0, 0))
		screen.blit(msg_surface, (0, HEIGHT / 2 - 30))
		screen.draw.text("Победа!" if is_game_won else "Поражение!", center=(WIDTH / 2, HEIGHT / 2), color='white', fontsize=46)

def on_key_down(key):
#	if mode != "game":
#		return

	old_x = char.x
	old_y = char.y
	if keyboard.right and char.x + CELL_W < WIDTH - CELL_W:
		char.x += CELL_W
		char.image = 'stand'
	elif keyboard.left and char.x - CELL_W > CELL_W:
		char.x -= CELL_W
		char.image = 'left'
	elif keyboard.down and char.y + CELL_H < HEIGHT - CELL_H*2:
		char.y += CELL_H
	elif keyboard.up and char.y - CELL_H > CELL_H:
		char.y -= CELL_H

	# collision with enemies
	enemy_index = char.collidelist(enemies)
	if enemy_index != -1:
		char.x = old_x
		char.y = old_y
		enemy = enemies[enemy_index]
		enemy.health -= char.attack
		char.health -= enemy.attack
		if enemy.health <= 0:
			# fallen bonuses upon enemy death
			if enemy.bonus == 1:
				heart = Actor('heart', center=enemy.pos)
				hearts.append(heart)
			elif enemy.bonus == 2:
				sword = Actor('sword', center=enemy.pos)
				swords.append(sword)
			enemies.pop(enemy_index)

def check_victory():
	global mode, num_battles_won, is_game_won

	if mode != "game":
		return

	if enemies == [] and char.health > MIN_CHAR_HEALTH:
		num_battles_won += 1
		char.health = INITIAL_CHAR_HEALTH
		if num_battles_won >= MAX_GAME_BATTLES:
			is_game_won = True
			mode = "end"
		else:
			init_game()
	elif char.health <= MIN_CHAR_HEALTH:
		is_game_won = False
		mode = "end"

def update(dt):
	check_victory()
	for i in range(len(hearts)):
		if char.colliderect(hearts[i]):
			char.health += BONUS_HEALTH
			hearts.pop(i)
			break

	for i in range(len(swords)):
		if char.colliderect(swords[i]):
			char.attack += BONUS_ATTACK
			swords.pop(i)
			break
