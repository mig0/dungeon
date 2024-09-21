from . import *

class TrivialPuzzle(Puzzle):
	def assert_config(self):
		return True

	def is_finish_cell_required(self):
		return True

