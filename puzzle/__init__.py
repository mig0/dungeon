from constants import *
from cellactor import *
from objects import *
from flags import flags
from random import randint, random
from numpy import ndarray, arange, array_equal, ix_, argwhere, copyto

class Puzzle:
	@classmethod
	def config_name(cls):
		cls_lower_name = cls.__name__.lower()
		return None if cls == Puzzle else cls_lower_name[:cls_lower_name.rindex("puzzle")] + '_puzzle'

	def __init__(self, level, Globals):
		self.map = None
		self.room = None
		self.level = level
		self.Globals = Globals
		self.accessible_cells = None
		self.finish_cell = None
		self.config_name = self.__class__.config_name()
		self.config = {} if type(level.get(self.config_name)) != dict else dict(level[self.config_name])
		self.init()

	def init(self):
		pass

	def assert_config(self):
		return True

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

import os, pkgutil
for _, module, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
	__import__(__name__ + "." + module)

def create_puzzle(level, Globals):
	if not Puzzle.__subclasses__():
		print("Internal bug. Didn't find any Puzzle subclasses")
		quit()

	puzzle_class = Puzzle
	for cls in Puzzle.__subclasses__():
		if cls.config_name() in level:
			puzzle_class = cls

	puzzle = puzzle_class(level, Globals)

	if not puzzle.assert_config():
		print("Level #%s: Requested %s, but config is incompatible, so ignoring it" % (level.get("n"), puzzle.__class__.__name__))
		puzzle = Puzzle(level, Globals)

	return puzzle

