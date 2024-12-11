from config import *

CELL_WALL   = '▓'
CELL_FLOOR  = '•'
CELL_CRACK  = '⦁'
CELL_BONES  = '⸗'
CELL_ROCKS  = '◦'
CELL_PLATE  = '⎵'
CELL_GATE0  = '★'
CELL_GATE1  = '☆'
CELL_START  = '►'
CELL_FINISH = '◄'
CELL_PORTAL = '𝟘'
CELL_SAND   = '⧛'
CELL_LOCK1  = '𝟙'
CELL_LOCK2  = '𝟚'
CELL_VOID   = '·'
CELL_DIR_L  = '←'
CELL_DIR_R  = '→'
CELL_DIR_U  = '↑'
CELL_DIR_D  = '↓'

CELL_SPECIAL0 = '0'
CELL_INTERNAL1 = '1'
CELL_OUTER_WALL = '▒'

CELL_WALLS = (CELL_WALL, CELL_OUTER_WALL)
CELL_FLOOR_TYPES_RANDGEN = (CELL_CRACK, CELL_BONES, CELL_ROCKS)
CELL_FLOOR_TYPES_FREQUENT = (*CELL_FLOOR_TYPES_RANDGEN, *((CELL_FLOOR,) * EMPTY_FLOOR_FREQUENCY))
CELL_FLOOR_TYPES = (*CELL_FLOOR_TYPES_RANDGEN, CELL_FLOOR)
CELL_FLOOR_EXTENSIONS = (*CELL_FLOOR_TYPES_RANDGEN, CELL_PLATE, CELL_START, CELL_FINISH, CELL_PORTAL, CELL_GATE0, CELL_GATE1, CELL_LOCK1, CELL_LOCK2, CELL_DIR_L, CELL_DIR_R, CELL_DIR_U, CELL_DIR_D)
CELL_ENEMY_PLACE_OBSTACLES = (*CELL_WALLS, CELL_PORTAL, CELL_START, CELL_FINISH, CELL_GATE0, CELL_GATE1, CELL_SAND, CELL_LOCK1, CELL_LOCK2, CELL_VOID)
CELL_CHAR_PLACE_OBSTACLES = (*CELL_WALLS, CELL_PLATE, CELL_PORTAL, CELL_GATE0, CELL_GATE1, CELL_SAND, CELL_LOCK1, CELL_LOCK2, CELL_VOID)
CELL_CHAR_MOVE_OBSTACLES  = (*CELL_WALLS, CELL_GATE0, CELL_LOCK1, CELL_LOCK2, CELL_VOID, CELL_DIR_L, CELL_DIR_R, CELL_DIR_U, CELL_DIR_D)

ACTOR_CHARS = {
	'heart':  '♥',
	'sword':  '⸸',
	'might':  '🖠',
	'key1':   '¹',
	'key2':   '²',
	'enemy':  '🕱',
	'barrel': '■',
	'char':   '☻',
}

ACTOR_ON_PLATE_CHARS = {
	'heart':  '♡',
	'sword':  '⸷',
	'might':  '🖞',
	'key1':   '₁',
	'key2':   '₂',
	'enemy':  '☠',
	'barrel': '□',
	'char':   '☺',
}

ACTOR_AND_PLATE_BY_CHAR = {v: (k, v != ACTOR_CHARS[k]) for k, v in {*ACTOR_CHARS.items(), *ACTOR_ON_PLATE_CHARS.items(),}}

LIFT_A = 'a'
LIFT_H = 'h'
LIFT_V = 'v'
LIFT_L = 'l'
LIFT_R = 'r'
LIFT_U = 'u'
LIFT_D = 'd'

LIFT_CHARS = {
	LIFT_A: '✥',
	LIFT_H: '↔',
	LIFT_V: '↕',
	LIFT_L: '←',
	LIFT_R: '→',
	LIFT_U: '↑',
	LIFT_D: '↓',
}

LIFT_TYPE_DIRECTIONS = {
	LIFT_A:  [(-1, 0), (+1, 0), (0, -1), (0, +1)],
	LIFT_H: [(-1, 0), (+1, 0)],
	LIFT_V: [(0, -1), (0, +1)],
	LIFT_L: [(-1, 0)],
	LIFT_R: [(+1, 0)],
	LIFT_U: [(0, -1)],
	LIFT_D: [(0, +1)],
}
LIFT_TYPES = *LIFT_TYPE_DIRECTIONS,

LIFT_TYPES_BY_CHAR = {v: k for k, v in LIFT_CHARS.items()}

MAX_COLOR_PUZZLE_VALUES = 6

COLOR_PUZZLE_VALUE_OUTSIDE = -1
COLOR_PUZZLE_VALUE_PLATE   = -2
COLOR_PUZZLE_VALUE_RED     = 0
COLOR_PUZZLE_VALUE_GREEN   = 1
COLOR_PUZZLE_VALUE_BLUE    = 2
COLOR_PUZZLE_VALUE_YELLOW  = 3
COLOR_PUZZLE_VALUE_CYAN    = 4
COLOR_PUZZLE_VALUE_PURPLE  = 5

IMAGES_DIR_PREFIX = 'images/'
DEFAULT_IMAGE_PREFIX = 'default/'
