import pygame
from config import *

MAP_SIZE_X = PLAY_SIZE_X + 2
MAP_SIZE_Y = PLAY_SIZE_Y + 2

WIDTH = CELL_W * MAP_SIZE_X
HEIGHT = CELL_H * (MAP_SIZE_Y + 1)
POS_CENTER_X = WIDTH / 2
POS_CENTER_Y = HEIGHT / 2
POS_STATUS_Y = HEIGHT - CELL_H / 2

BONUS_NONE   = 0
BONUS_HEALTH = 1
BONUS_ATTACK = 2

ARROW_KEY_R = pygame.K_RIGHT
ARROW_KEY_L = pygame.K_LEFT
ARROW_KEY_D = pygame.K_DOWN
ARROW_KEY_U = pygame.K_UP

CELL_BORDER = '#'
CELL_FLOOR  = '.'
CELL_CRACK  = ','
CELL_BONES  = ':'
CELL_ROCKS  = ';'
CELL_PLATE  = '_'
CELL_PORTAL = 'O'
CELL_INTERNAL1 = '1'

CELL_FLOOR_ADDITIONS_RANDGEN = (CELL_CRACK, CELL_BONES, CELL_ROCKS)
CELL_FLOOR_ADDITIONS_FREQUENT = (*CELL_FLOOR_ADDITIONS_RANDGEN, *((CELL_FLOOR,) * EMPTY_FLOOR_FREQUENCY))
CELL_FLOOR_ADDITIONS = (*CELL_FLOOR_ADDITIONS_RANDGEN, CELL_PLATE, CELL_PORTAL)
CELL_ENEMY_PLACE_OBSTACLES = (CELL_BORDER, CELL_PORTAL)
CELL_CHAR_PLACE_OBSTACLES = (CELL_BORDER, CELL_PORTAL, CELL_PLATE)
CELL_CHAR_MOVE_OBSTACLES  = (CELL_BORDER)

PLAY_X1 = 1
PLAY_X2 = PLAY_X1 + PLAY_SIZE_X - 1
PLAY_Y1 = 1
PLAY_Y2 = PLAY_Y1 + PLAY_SIZE_Y - 1

PLAY_X_RANGE = range(PLAY_X1, PLAY_X2 + 1)
PLAY_Y_RANGE = range(PLAY_Y1, PLAY_Y2 + 1)

MAP_X_RANGE = range(0, MAP_SIZE_X)
MAP_Y_RANGE = range(0, MAP_SIZE_Y)

ROOM_SIZE_X = [
	int(PLAY_SIZE_X / 2),
	PLAY_SIZE_X - int(PLAY_SIZE_X / 2) - 1,
	int(PLAY_SIZE_X / 2),
	PLAY_SIZE_X - int(PLAY_SIZE_X / 2) - 1,
]
ROOM_SIZE_Y = [
	int(PLAY_SIZE_Y / 2),
	int(PLAY_SIZE_Y / 2),
	PLAY_SIZE_Y - int(PLAY_SIZE_Y / 2) - 1,
	PLAY_SIZE_Y - int(PLAY_SIZE_Y / 2) - 1,
]

ROOM_X1 = [
	PLAY_X1,
	PLAY_X1 + ROOM_SIZE_X[0] + 1,
	PLAY_X1,
	PLAY_X1 + ROOM_SIZE_X[0] + 1,
]
ROOM_X2 = [
	PLAY_X1 + ROOM_SIZE_X[0] - 1,
	PLAY_X2,
	PLAY_X1 + ROOM_SIZE_X[0] - 1,
	PLAY_X2,
]
ROOM_Y1 = [
	PLAY_Y1,
	PLAY_Y1,
	PLAY_Y1 + ROOM_SIZE_Y[0] + 1,
	PLAY_Y1 + ROOM_SIZE_Y[0] + 1,
]
ROOM_Y2 = [
	PLAY_Y1 + ROOM_SIZE_Y[0] - 1,
	PLAY_Y1 + ROOM_SIZE_Y[0] - 1,
	PLAY_Y2,
	PLAY_Y2,
]

ROOM_X_RANGE = [
	range(ROOM_X1[0], ROOM_X2[0] + 1),
	range(ROOM_X1[1], ROOM_X2[1] + 1),
	range(ROOM_X1[2], ROOM_X2[2] + 1),
	range(ROOM_X1[3], ROOM_X2[3] + 1),
]
ROOM_Y_RANGE = [
	range(ROOM_Y1[0], ROOM_Y2[0] + 1),
	range(ROOM_Y1[1], ROOM_Y2[1] + 1),
	range(ROOM_Y1[2], ROOM_Y2[2] + 1),
	range(ROOM_Y1[3], ROOM_Y2[3] + 1),
]

ROOM_BORDER_X = ROOM_X2[0] + 1
ROOM_BORDER_Y = ROOM_X2[0] + 1

MAX_COLOR_PUZZLE_VALUES = 6

COLOR_PUZZLE_VALUE_OUTSIDE = -1
COLOR_PUZZLE_VALUE_PLATE   = -2
COLOR_PUZZLE_VALUE_RED     = 0
COLOR_PUZZLE_VALUE_GREEN   = 1
COLOR_PUZZLE_VALUE_BLUE    = 2
COLOR_PUZZLE_VALUE_YELLOW  = 3
COLOR_PUZZLE_VALUE_CYAN    = 4
COLOR_PUZZLE_VALUE_PURPLE  = 5

DEFAULT_COLOR_PUZZLE_PLAY_SIZE_X = int((PLAY_SIZE_X - 1) / 2) * 2 + 1
DEFAULT_COLOR_PUZZLE_PLAY_SIZE_Y = int((PLAY_SIZE_Y - 1) / 2) * 2 + 1

DEFAULT_COLOR_PUZZLE_ROOM_SIZE_X = [
	int((ROOM_SIZE_X[0] - 1) / 2) * 2 + 1,
	int((ROOM_SIZE_X[1] - 1) / 2) * 2 + 1,
	int((ROOM_SIZE_X[2] - 1) / 2) * 2 + 1,
	int((ROOM_SIZE_X[3] - 1) / 2) * 2 + 1,
]
DEFAULT_COLOR_PUZZLE_ROOM_SIZE_Y = [
	int((ROOM_SIZE_Y[0] - 1) / 2) * 2 + 1,
	int((ROOM_SIZE_Y[1] - 1) / 2) * 2 + 1,
	int((ROOM_SIZE_Y[2] - 1) / 2) * 2 + 1,
	int((ROOM_SIZE_Y[3] - 1) / 2) * 2 + 1,
]
