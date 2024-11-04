from . import *

class ColorPuzzle(Puzzle):
	def init(self):
		self.color_map = None
		self.cell_images = []

	def assert_config(self):
		return not flags.is_any_maze

	def has_plate(self):
		return True

	def is_target_to_be_solved(self):
		return True

	def on_set_theme(self):
		gray_tiles_image = self.Globals.load_theme_cell_image('floor_gray_tiles')
		self.cell_images = []
		for color in MAIN_COLOR_RGB_VALUES:
			color_cell_image = self.Globals.colorize_cell_image(gray_tiles_image, color)
			self.cell_images.append(color_cell_image)

	def on_set_room(self, room):
		super().on_set_room(room)
		super().set_area_from_config(request_odd_size=True, align_to_center=True)

	def on_create_map(self, map):
		super().on_create_map(map)
		self.color_map = ndarray((MAP_SIZE_X, MAP_SIZE_Y), dtype=int)
		self.color_map.fill(COLOR_PUZZLE_VALUE_OUTSIDE)

	def get_num_values(self):
		return self.config.get("num_values", MAX_COLOR_PUZZLE_VALUES)

	def increment_cell_color(self, cell):
		self.color_map[cell] = (self.color_map[cell] + 1) % self.get_num_values()

	def press_plate(self, cell):
		for neigh in self.Globals.get_all_neighbors(cell):
			self.increment_cell_color(neigh)
			if "is_extended" in self.config and (neigh[0] != cell[0] and neigh[1] != cell[1]) ^ (cell[0] % 3 != 0 or cell[2] % 3 != 0):
				self.increment_cell_color(neigh)

	def get_cell_image(self, cell):
		return self.cell_images[self.color_map[cell]]

	def is_plate(self, cell):
		return self.is_in_area(cell) and (cell[0] - self.area.x1) % 2 == 1 and (cell[1] - self.area.y1) % 2 == 1

	def is_solved(self):
		for cell in self.area.cells:
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
		for cell in self.area.cells:
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

	def press_cell(self, cell):
		if not self.is_in_area(cell):
			return False

		if self.map[cell] == CELL_PLATE:
			self.press_plate(cell)

		return True

	def on_press_key(self, keyboard):
		if keyboard.space and self.map[char.c] == CELL_PLATE:
			self.press_plate(char.c)

