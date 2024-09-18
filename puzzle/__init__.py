from constants import *
from cellactor import *
from objects import *
from flags import flags
from random import randint, random
from numpy import ndarray, arange, array_equal, ix_, argwhere, copyto

class Puzzle:
	def __init__(self, level, Globals):
		self.map = None
		self.room = None
		self.level = level
		self.Globals = Globals
		self.accessible_cells = None
		self.finish_cell = None
		self.init()

	def init(self):
		pass

	def is_long_generation(self):
		return False

	def is_finish_cell_required(self):
		return False

	def has_start(self):
		return False

	def has_finish(self):
		return self.is_finish_cell_required()

	def has_plate(self):
		return False

	def has_portal(self):
		return False

	def has_gate(self):
		return False

	def has_locks(self):
		return False

	def has_sand(self):
		return False

	def is_target_to_kill_enemies(self):
		return not self.has_finish()

	def is_target_to_be_solved(self):
		return False

	def on_set_theme(self):
		pass

	def on_create_map(self, map):
		self.map = map

	def on_set_room(self, room):
		self.room = room

	def set_finish_cell(self, accessible_cells, finish_cell):
		self.accessible_cells = accessible_cells
		self.finish_cell = finish_cell

	def generate_room(self):
		pass

	def on_generate_map(self):
		pass

	def is_solved(self):
		return False

	def store_level(self, stored_level):
		pass

	def restore_level(self, stored_level):
		pass

	def modify_cell_types_to_draw(self, cell, cell_types):
		pass

	def get_cell_image_to_draw(self, cell, cell_type):
		return None

	def on_press_key(self, keyboard):
		pass

	def on_update(self, level_time):
		pass

	def finish(self):
		pass

from .barrel    import BarrelPuzzle
from .color     import ColorPuzzle
from .fifteen   import FifteenPuzzle
from .gate      import GatePuzzle
from .lock      import LockPuzzle
from .memory    import MemoryPuzzle
from .rotatepic import RotatepicPuzzle
from .stoneage  import StoneagePuzzle
from .trivial   import TrivialPuzzle

def create_puzzle(level, Globals):
	is_any_maze = flags.is_random_maze or flags.is_spiral_maze or flags.is_grid_maze

	if level.get("barrel_puzzle") and not is_any_maze:
		puzzle_class = BarrelPuzzle
	elif level.get("color_puzzle") and not is_any_maze:
		puzzle_class = ColorPuzzle
	elif level.get("fifteen_puzzle") and not is_any_maze:
		puzzle_class = FifteenPuzzle
	elif level.get("gate_puzzle") and is_any_maze:
		puzzle_class = GatePuzzle
	elif level.get("lock_puzzle") and is_any_maze:
		puzzle_class = LockPuzzle
	elif level.get("memory_puzzle") and not is_any_maze:
		puzzle_class = MemoryPuzzle
	elif level.get("rotatepic_puzzle"):
		puzzle_class = RotatepicPuzzle
	elif level.get("stoneage_puzzle") and not is_any_maze:
		puzzle_class = StoneagePuzzle
	elif level.get("trivial_puzzle"):
		puzzle_class = TrivialPuzzle
	else:
		puzzle_class = Puzzle

	return puzzle_class(level, Globals)

