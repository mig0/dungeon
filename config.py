TITLE = "Skull Labyrinth"
FPS = 30

DEBUG_LEVEL = 1  # 0 means no debug at all, 2 means more verbose
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

AUTOGENERATION_IDLE_TIME = 30
AUTOGENERATION_NEXT_TIME = 5
AUTOGENERATION_HEALTH = 2

CHAR_APPEARANCE_SCALE_DURATION = 1

ENEMY_BEAT_ANIMATION_TIME = 0.4
ENEMY_BEAT_OFFSET = 12

WIN_NEW_DELAY = 1.5

LEVEL_TITLE_TIME = 4
LEVEL_TARGET_TIME = 3

ENEMY_KILL_ANIMATION_TIME = 0.5
ENEMY_KILL_DELAY = 0.1

MAIN_COLOR_RGB_VALUES = ((255, 80, 80), (80, 255, 80), (80, 80, 255), (255, 255, 80), (255, 80, 255), (80, 255, 255))
MORE_COLOR_RGB_VALUES = ((228, 160, 80), (80, 228, 160), (160, 80, 228), (80, 80, 80), (160, 160, 160), (228, 228, 228), (160, 228, 80), (228, 80, 160), (80, 160, 228))
EXTENDED_COLOR_RGB_VALUES = (*MAIN_COLOR_RGB_VALUES, *MORE_COLOR_RGB_VALUES)

MEMORY_PUZZLE_OPEN_CELL2_TIME = 1
MEMORY_PUZZLE_REVEAL_FADE_TIME = 1.5
MEMORY_PUZZLE_CHAR_OPACITY = 0.4

FIFTEEN_PUZZLE_MOVE_NEIGHBOUR_ONLY = False

DEFAULT_NUM_ENEMIES = 5
DEFAULT_NUM_BARRELS = 4

DEFAULT_NUM_GATE_PUZZLE_GATES  = 5
DEFAULT_NUM_GATE_PUZZLE_PLATES = 3
MIN_GATE_PUZZLE_ATTACHED_GATES = 1
MAX_GATE_PUZZLE_ATTACHED_GATES = 3

# this controls status drop drawing; counted in cell widths
STATUS_DROP_X_SIZE = 1.8
STATUS_DROP_X_ACTOR_OFFSET = -0.3
STATUS_DROP_X_TEXT_OFFSET  = +0.4
