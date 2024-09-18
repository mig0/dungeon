from . import *

FIFTEEN_PUZZLE_VALUE_OUTSIDE = -1
CELL_FIFTEEN_FRAME = '~f'
CELL_FIFTEEN_VALUE = '~v'

class FifteenPuzzle(Puzzle):
	def init(self):
		self.fifteen_map = None
		self.area = Area()
		self.frame_image = None
		self.max_num = 0

	def on_set_theme(self):
		self.frame_image = self.Globals.load_theme_cell_image('floor_gray_frame')

	def on_create_map(self, map):
		super().on_create_map(map)
		self.fifteen_map = ndarray((MAP_SIZE_X, MAP_SIZE_X), dtype=int)
		self.fifteen_map.fill(FIFTEEN_PUZZLE_VALUE_OUTSIDE)

	def is_target_to_be_solved(self):
		return True

	def get_real_fifteen_map(self):
		return self.fifteen_map[ix_(self.area.x_range, self.area.y_range)]

	def is_in_area(self, cell):
		return self.Globals.is_cell_in_area(cell, self.area.x_range, self.area.y_range)

	def is_solved(self):
		real_fifteen_map = self.get_real_fifteen_map()
		for idx, num in enumerate(self.get_real_fifteen_map().transpose().flat):
			if num != idx + 1:
				return False
		return True

	def on_set_room(self, room):
		super().on_set_room(room)
		self.area.size_x = self.level["fifteen_puzzle_size"][0] if "fifteen_puzzle_size" in self.level else flags.ROOM_SIZE_X[room.idx] if room.idx is not None else PLAY_SIZE_X
		self.area.size_y = self.level["fifteen_puzzle_size"][1] if "fifteen_puzzle_size" in self.level else flags.ROOM_SIZE_Y[room.idx] if room.idx is not None else PLAY_SIZE_Y
		if self.area.size_x <= 1:
			self.area.size_x = 2
		if self.area.size_y <= 1:
			self.area.size_y = 2
		if self.area.size_x > self.room.size_x:
			self.area.size_x = self.room.size_x
		if self.area.size_y > self.room.size_y:
			self.area.size_y = self.room.size_y
		self.area.x1 = room.x1 + (room.size_x - self.area.size_x) // 2 + (room.size_x - self.area.size_x) % 2 * ((room.idx + 1 if room.idx is not None else 0) % 2)
		self.area.x2 = self.area.x1 + self.area.size_x - 1
		self.area.y1 = room.y1 + (room.size_y - self.area.size_y) // 2 + (room.size_y - self.area.size_y) % 2 * (1 - ((room.idx if room.idx is not None else 2) // 2) % 2)
		self.area.y2 = self.area.y1 + self.area.size_y - 1
		self.area.x_range = range(self.area.x1, self.area.x2 + 1)
		self.area.y_range = range(self.area.y1, self.area.y2 + 1)
		self.max_num = self.area.size_x * self.area.size_y

	def is_empty_cell(self, cell):
		return self.fifteen_map[cell] == self.max_num

	def get_empty_cell(self):
		return list(tuple(cell) for cell in argwhere(self.fifteen_map == self.max_num) if self.is_in_area(cell))[0]

	def get_cells_on_one_line_between_two_cells(self, cell1, cell2):
		cells = []
		if cell1 == cell2 or cell1[0] != cell2[0] and cell1[1] != cell2[1]:
			return cells

		diff = cell_direction(cell1, cell2)
		cell = cell1
		while cell != cell2:
			cell = apply_diff(cell, diff)
			cells.append(cell)
		return cells

	def swap(self, cell1, cell2):
		self.fifteen_map[cell1], self.fifteen_map[cell2] = self.fifteen_map[cell2], self.fifteen_map[cell1]

	def move(self, empty_cell, cell, neigh_only=False):
		if neigh_only:
			neighbors = self.Globals.get_actor_neighbors(char, self.area.x_range, self.area.y_range)
			if empty_cell not in neighbors:
				return
			self.swap(cell, empty_cell)
		else:
			last_cell = empty_cell
			for cell in self.get_cells_on_one_line_between_two_cells(empty_cell, cell):
				self.swap(last_cell, cell)
				last_cell = cell

	def press_char_cell(self):
		if self.fifteen_map[char.c] == FIFTEEN_PUZZLE_VALUE_OUTSIDE:
			return

		empty_cell = self.get_empty_cell()
		self.move(empty_cell, char.c, FIFTEEN_PUZZLE_MOVE_NEIGHBOUR_ONLY)

	def get_random_non_equal(self, range, n):
		r = n
		while r == n:
			r = randint(range.start, range.stop - 1)
		return r

	def scramble(self):
		# scramble by real moves
		num_moves_left = self.max_num * 12
		empty_cell = self.get_empty_cell()
		is_row = True
		while num_moves_left > 0:
			is_row = not is_row
			if is_row:
				cell = (empty_cell[0], self.get_random_non_equal(self.area.y_range, empty_cell[1]))
			else:
				cell = (self.get_random_non_equal(self.area.x_range, empty_cell[0]), empty_cell[1])
			self.move(empty_cell, cell)
			empty_cell = cell
			num_moves_left -= 1

	def generate_room(self):
		# create the solved position - populate numbers from 1 to max_num
		real_fifteen_map = arange(self.max_num).reshape(self.area.size_y, self.area.size_x)
		real_fifteen_map += 1
		self.fifteen_map[ix_(self.area.x_range, self.area.y_range)] = real_fifteen_map.transpose()
		# scramble fifteen map
		self.scramble()

		if self.is_solved():
			self.generate_room()

	def modify_cell_types_to_draw(self, cell, cell_types):
		if self.fifteen_map[cell] == FIFTEEN_PUZZLE_VALUE_OUTSIDE:
			return
		cell_types.append(CELL_FIFTEEN_FRAME)
		if self.is_empty_cell(cell):
			return
		cell_types.append(CELL_FIFTEEN_VALUE)

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_FIFTEEN_FRAME:
			return self.frame_image
		if cell_type == CELL_FIFTEEN_VALUE:
			return self.Globals.create_text_cell_image(str(self.fifteen_map[cell]), color='#FFFFC0', gcolor="#808040", owidth=1, ocolor="#404030")
		return None

	def on_press_key(self, keyboard):
		if keyboard.space:
			self.press_char_cell()
		return True

	def set_char_opacity_if_needed(self):
		char.set_default_opacity(MEMORY_PUZZLE_CHAR_OPACITY if self.fifteen_map[char.c] != FIFTEEN_PUZZLE_VALUE_OUTSIDE else 1)

	def on_update(self, level_time):
		self.set_char_opacity_if_needed()

	def finish(self):
		char.set_default_opacity(1)

