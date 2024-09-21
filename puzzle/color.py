from . import *

class ColorPuzzle(Puzzle):
	def init(self):
		self.color_map = None
		self.cell_images = []
		self.area = Area()

	def assert_config(self):
		return not flags.is_any_maze

	def has_plate(self):
		return True

	def is_target_to_be_solved(self):
		return True

	def on_set_theme(self):
		gray_tiles_image = self.Globals.load_theme_cell_image('floor_gray_tiles')
		self.cell_images = []
		for color in COLOR_PUZZLE_RGB_VALUES:
			color_cell_image = self.Globals.colorize_cell_image(gray_tiles_image, color)
			self.cell_images.append(color_cell_image)

	def on_set_room(self, room):
		super().on_set_room(room)
		self.area.size_x = self.level["color_puzzle_size"][0] if "color_puzzle_size" in self.level else flags.DEFAULT_PUZZLE_ROOM_SIZE_X(room.idx) if room.idx is not None else flags.DEFAULT_PUZZLE_PLAY_SIZE_X
		self.area.size_y = self.level["color_puzzle_size"][1] if "color_puzzle_size" in self.level else flags.DEFAULT_PUZZLE_ROOM_SIZE_Y(room.idx) if room.idx is not None else flags.DEFAULT_PUZZLE_PLAY_SIZE_Y
		self.area.x1 = room.x1 + int((room.size_x - self.area.size_x) / 2)
		self.area.x2 = self.area.x1 + self.area.size_x - 1
		self.area.y1 = room.y1 + int((room.size_y - self.area.size_y) / 2)
		self.area.y2 = self.area.y1 + self.area.size_y - 1
		self.area.x_range = range(self.area.x1, self.area.x2 + 1)
		self.area.y_range = range(self.area.y1, self.area.y2 + 1)

	def on_create_map(self, map):
		super().on_create_map(map)
		self.color_map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype=int)
		self.color_map.fill(COLOR_PUZZLE_VALUE_OUTSIDE)

	def get_num_values(self):
		return self.level["color_puzzle_values"] if "color_puzzle_values" in self.level else MAX_COLOR_PUZZLE_VALUES

	def press_cell(self, cell):
		self.color_map[cell] = (self.color_map[cell] + 1) % self.get_num_values()

	def press_plate(self, cell):
		for neigh in self.Globals.get_all_neighbors(cell):
			self.press_cell(neigh)
			if "color_puzzle_extended" in self.level and (neigh[0] != cell[0] and neigh[1] != cell[1]) ^ (cell[0] % 3 != 0 or cell[2] % 3 != 0):
				self.press_cell(neigh)

	def get_cell_image(self, cell):
		return self.cell_images[self.color_map[cell]]

	def is_in_area(self, cell):
		return self.Globals.is_cell_in_area(cell, self.area.x_range, self.area.y_range)

	def is_plate(self, cell):
		return self.is_in_area(cell) and (cell[0] - self.area.x1) % 2 == 1 and (cell[1] - self.area.y1) % 2 == 1

	def is_solved(self):
		for cell in product(self.area.x_range, self.area.y_range):
			if not self.is_plate(cell) and self.color_map[cell] != COLOR_PUZZLE_VALUE_GREEN:
				return False
		return True

	def store_level(self, stored_level):
		stored_level["color_map"] = self.color_map.copy()

	def restore_level(self, stored_level):
		self.color_map = stored_level["color_map"]

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_FLOOR and self.color_map[cell] not in (COLOR_PUZZLE_VALUE_OUTSIDE, COLOR_PUZZLE_VALUE_PLATE):
			return self.get_cell_image(cell)
		return None

	def generate_room(self):
		for cell in product(self.area.x_range, self.area.y_range):
			self.color_map[cell] = COLOR_PUZZLE_VALUE_GREEN
			if self.is_plate(cell):
				self.map[cell] = CELL_PLATE
				self.color_map[cell] = COLOR_PUZZLE_VALUE_PLATE
		num_tries = 5
		while num_tries > 0:
			for n in range(self.area.size_x * self.area.size_y * 3):
				plate_cx = self.area.x1 + randint(1, int(self.area.size_x / 2)) * 2 - 1
				plate_cy = self.area.y1 + randint(1, int(self.area.size_y / 2)) * 2 - 1
				for i in range(randint(1, self.get_num_values() - 1)):
					self.press_plate((plate_cx, plate_cy))
			if not self.is_solved():
				break
			num_tries -= 1

	def on_press_key(self, keyboard):
		if keyboard.space and self.map[char.c] == CELL_PLATE:
			self.press_plate(char.c)

