from constants import *
from random import randint

class Puzzle:
	def __init__(self, level, Globals):
		self.map = None
		self.room = None
		self.level = level
		self.Globals = Globals

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

	def generate_room(self, accessible_cells, finish_cell):
		pass

	def on_generate_map(self):
		pass

	def is_solved(self):
		return False

	def store_level(self, stored_level):
		pass

	def restore_level(self, stored_level):
		pass

	def get_cell_image_to_draw(self, cx, cy, cell_type):
		return None

	def on_press_key(self, keyboard):
		return False

from .barrel import *
from .color import *
from .gate import *
from .lock import *
from .stoneage import *

def create_puzzle(level, Globals):
	is_any_maze = "random_maze" in level or "spiral_maze" in level or "grid_maze" in level

	if "barrel_puzzle" in level and not is_any_maze:
		return BarrelPuzzle(level, Globals)

	if "color_puzzle" in level and not is_any_maze:
		return ColorPuzzle(level, Globals)

	if "gate_puzzle" in level and is_any_maze:
		return GatePuzzle(level, Globals)

	if "lock_puzzle" in level and is_any_maze:
		return LockPuzzle(level, Globals)

	if "stoneage_puzzle" in level and not is_any_maze:
		return StoneagePuzzle(level, Globals)

	return Puzzle(level, Globals)

