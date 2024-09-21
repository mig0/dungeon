from . import *

class StoneagePuzzle(Puzzle):
	def assert_config(self):
		return not flags.is_any_maze

	def has_finish(self):
		return True

	def has_start(self):
		return True

	def has_portal(self):
		return True

	def has_locks(self):
		return True

	def has_sand(self):
		return True

	def generate_room(self, room, accessible_cells, finish_cell):
		generate_random_solvable_stoneage_room()

	def generate_random_nonsolvable_room(self):
		self.Globals.replace_random_floor_cell(CELL_VOID, 70)
		self.Globals.replace_random_floor_cell(CELL_START, 1, self.Globals.set_char_cell)
		self.Globals.replace_random_floor_cell(CELL_FINISH)
		self.Globals.replace_random_floor_cell(CELL_SAND, 10)

		self.Globals.replace_random_floor_cell(CELL_PORTAL, 2, self.Globals.create_portal_pair, extra_num=1)
		self.Globals.replace_random_floor_cell(CELL_LOCK1, 1)
		self.Globals.replace_random_floor_cell(CELL_LOCK2, 1)
		drop_key1.instantiate(self.Globals.get_random_floor_cell())
		drop_key2.instantiate(self.Globals.get_random_floor_cell())

		self.Globals.replace_random_floor_cell(CELL_VOID, 5, self.Globals.create_lift, LIFT_A)
		self.Globals.replace_random_floor_cell(CELL_VOID, 2, self.Globals.create_lift, LIFT_H)
		self.Globals.replace_random_floor_cell(CELL_VOID, 2, self.Globals.create_lift, LIFT_V)
		self.Globals.replace_random_floor_cell(CELL_VOID, 1, self.Globals.create_lift, LIFT_L)
		self.Globals.replace_random_floor_cell(CELL_VOID, 1, self.Globals.create_lift, LIFT_R)
		self.Globals.replace_random_floor_cell(CELL_VOID, 1, self.Globals.create_lift, LIFT_U)
		self.Globals.replace_random_floor_cell(CELL_VOID, 1, self.Globals.create_lift, LIFT_D)

	def generate_random_solvable_room(self):
		while True:
			start_cell = self.Globals.get_random_floor_cell()
			finish_cell = self.Globals.get_random_floor_cell()
			if self.Globals.get_distance(start_cell, finish_cell) > self.Globals.get_max_room_distance() / 2:
				break

		self.map[start_cell] = CELL_START
		self.map[finish_cell] = CELL_FINISH
		self.Globals.set_char_cell(start_cell)

		self.Globals.replace_random_floor_cell(CELL_VOID, (self.room.x2 - self.room.x1 + 1) * (self.room.y2 - self.room.y1 + 1) - 2)
		char.c = start_cell
		self.Globals.generate_random_free_path(finish_cell, deviation=4)

		path_cells = self.Globals.find_path(start_cell, finish_cell)[:-1]
		for i in range(int(randint(0, 60) * len(path_cells) / 100), int(randint(40, 100) * len(path_cells) / 100)):
			self.map[path_cells[i]] = CELL_SAND

		self.Globals.replace_random_floor_cell(CELL_PORTAL, 1, self.Globals.create_portal_pair, extra_num=1)
		self.Globals.replace_random_floor_cell(CELL_LOCK1, 1)
		self.Globals.replace_random_floor_cell(CELL_LOCK2, 1)
		drop_key1.instantiate(self.Globals.get_random_floor_cell())
		drop_key2.instantiate(self.Globals.get_random_floor_cell())

	def generate_room(self):
		self.generate_random_solvable_room()

