#pgzero

import random
import pygame

cell = Actor('marble')
cell1 = Actor('floor')
cell2 = Actor("crack")
cell3 = Actor("bones")
cell4 = Actor('rock')
cell5 = Actor('border')

# Игровое окно
PLAY_MAP_SIZE_X = 7
PLAY_MAP_SIZE_Y = 7
WHOLE_MAP_SIZE_X = PLAY_MAP_SIZE_X + 2
WHOLE_MAP_SIZE_Y = PLAY_MAP_SIZE_Y + 3
WIDTH = cell.width * WHOLE_MAP_SIZE_X
HEIGHT = cell.height * WHOLE_MAP_SIZE_Y

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

num_battles_won = 0
is_game_won = False
mode = "game"

TITLE = "WeCode и Драконы" # Заголовок окна игры
FPS = 30 # Количество кадров в секунду

my_map = [
	[5, 5, 5, 5, 5, 5, 5, 5, 5],
	[5, 1, 1, 4, 1, 1, 1, 1, 5],
	[5, 1, 1, 2, 1, 3, 1, 4, 5],
	[5, 1, 1, 1, 2, 1, 1, 1, 5],
	[5, 1, 3, 2, 1, 1, 3, 1, 5],
	[5, 1, 1, 1, 1, 3, 1, 1, 5],
	[5, 4, 1, 3, 1, 1, 2, 1, 5],
	[5, 1, 1, 1, 1, 4, 1, 1, 5],
	[5, 5, 5, 5, 5, 5, 5, 5, 5],
	[0, 0, 0, 0, 0, 0, 0, 0, 0],  # Строка со здоровьем и атакой
]
map_cells = [ cell, cell1, cell2, cell3, cell4, cell5 ]

# Главный герой
char = Actor('stand', topleft=(cell.width, cell.height))

enemies = []
hearts = []
swords = []   

def init_game():
	char.health = INITIAL_CHAR_HEALTH
	char.attack = INITIAL_CHAR_ATTACK
	# generate enemies
	for i in range(MAX_ENEMIES):
		positioned = False
		num_tries = 10000
		while not positioned and num_tries > 0:
			num_tries -= 1
			left = random.randint(1, 7) * cell.width
			top  = random.randint(1, 7) * cell.height
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

#Отрисовка карты
def map_draw():
	for i in range(len(my_map)):
		for j in range(len(my_map[0])):
			map_cell = map_cells[my_map[i][j]]
			map_cell.left = cell.width * j
			map_cell.top = cell.height * i
			map_cell.draw()
#Отрисовка
def draw():
	screen.fill("#2f3542")
	if mode == 'game' or mode == "end":
		map_draw()
		char.draw()
		screen.draw.text("HP:", center=(25, 475), color='white', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
		screen.draw.text(str(char.health), center=(75, 475), color="#AAFF00", gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
		screen.draw.text("AP:", center=(375, 475), color='white', gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
		screen.draw.text(str(char.attack), center=(425, 475), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
		for enemy in enemies:
			enemy.draw()
		for heart in hearts:
			heart.draw()
		for sword in swords:
			sword.draw()
		for enemy in enemies:
			screen.draw.text(str(enemy.health), center=(enemy.left + cell.width / 2, enemy.top - 34), color="#AAFF00", gcolor="#66AA00", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)
			screen.draw.text(str(enemy.attack), center=(enemy.left + cell.width / 2, enemy.top - 14), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=0.9, fontsize=24)

	# Окно победы или поражения
	if mode == "end":
		msg_surface = pygame.Surface((WIDTH, 60))
		msg_surface.set_alpha(50)
		msg_surface.fill((0, 0, 0))
		screen.blit(msg_surface, (0, HEIGHT / 2 - 30))
		screen.draw.text("Победа!" if is_game_won else "Поражение!", center=(WIDTH / 2, HEIGHT / 2), color='white', fontsize=46)

# Управление
def on_key_down(key):
#	if mode != "game":
#		return

	old_x = char.x
	old_y = char.y
	if keyboard.right and char.x + cell.width < WIDTH - cell.width:
		char.x += cell.width
		char.image = 'stand'
	elif keyboard.left and char.x - cell.width > cell.width:
		char.x -= cell.width
		char.image = 'left'
	elif keyboard.down and char.y + cell.height < HEIGHT - cell.height*2:
		char.y += cell.height
	elif keyboard.up and char.y - cell.height > cell.height:
		char.y -= cell.height

	# Столкновение с врагами
	enemy_index = char.collidelist(enemies)
	if enemy_index != -1:
		char.x = old_x
		char.y = old_y
		enemy = enemies[enemy_index]
		enemy.health -= char.attack
		char.health -= enemy.attack
		if enemy.health <= 0:
			# Выпадение бонусов при гибели врага
			if enemy.bonus == 1:
				heart = Actor('heart', center=enemy.pos)
				hearts.append(heart)
			elif enemy.bonus == 2:
				sword = Actor('sword', center=enemy.pos)
				swords.append(sword)
			enemies.pop(enemy_index)

# Логика победы или поражения
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

# Логика бонусов
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
