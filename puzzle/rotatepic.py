from . import *

ROTATEPIC_PUZZLE_VALUE_OUTSIDE = -1
CELL_ROTATEPIC_BOX = '~b'

class RotatepicPuzzle(Puzzle):
	def init(self):
		self.rotatepic_map = None
		self.image = None
		self.draw_solved_mode = False

	def assert_config(self):
		return not flags.is_any_maze

	def on_create_map(self, map):
		super().on_create_map(map)
		self.rotatepic_map = ndarray((MAP_SIZE_X, MAP_SIZE_X), dtype=int)
		self.rotatepic_map.fill(ROTATEPIC_PUZZLE_VALUE_OUTSIDE)

	def is_target_to_be_solved(self):
		return True

	def get_real_rotatepic_map(self):
		return self.rotatepic_map[ix_(self.area.x_range, self.area.y_range)]

	def is_solved(self):
		real_rotatepic_map = self.get_real_rotatepic_map()
		for num in self.get_real_rotatepic_map().flat:
			if num != 0:
				return False
		return True

	def on_set_room(self, room):
		super().on_set_room(room)
		super().set_area_from_config(min_size=(1, 1), align_to_center=True)
		self.max_num = self.area.size_x * self.area.size_y
		self.is_shared_bg = self.level.get("bg_image") is not None
		if not self.is_shared_bg:
			self.image = self.Globals.load_image(self.config.get("image", "bg/stonehenge.jpg"), (self.area.size_x * CELL_W, self.area.size_y * CELL_H), self.config.get("image_crop", False))

	def rotate_cell(self, cell, delta=1):
		if self.rotatepic_map[cell] == ROTATEPIC_PUZZLE_VALUE_OUTSIDE:
			return

		self.rotatepic_map[cell] = (self.rotatepic_map[cell] + delta) % 4

	def press_char_cell(self, clockwise=True):
		self.rotate_cell(char.c, 1 if clockwise else -1)

	def scramble(self):
		for cell in self.area.cells:
			# make 0 to be twice less frequent than 1, 2 or 3
			delta = randint(1, 7) // 2
			self.rotate_cell(cell, delta)

	def generate_room(self):
		# create the solved position - populate boxes with 0
		real_rotatepic_map = ndarray((self.area.size_x, self.area.size_y), dtype=int)
		real_rotatepic_map.fill(0)
		self.rotatepic_map[ix_(self.area.x_range, self.area.y_range)] = real_rotatepic_map
		# scramble boxes
		self.scramble()

		if self.is_solved():
			self.generate_room()

	def modify_cell_types_to_draw(self, cell, cell_types):
		if self.rotatepic_map[cell] == ROTATEPIC_PUZZLE_VALUE_OUTSIDE:
			if self.is_shared_bg:
				cell_types.clear()
			return
		cell_types.append(CELL_ROTATEPIC_BOX)

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_ROTATEPIC_BOX:
			image = self.image if not self.is_shared_bg else self.Globals.get_bg_image()
			starting_cell = (self.area.x1, self.area.y1) if not self.is_shared_bg else (0, 0)
			rotate_angle = 0 if self.draw_solved_mode else self.rotatepic_map[cell] * 90
			return self.Globals.create_cell_subimage(image, cell, starting_cell, rotate_angle)
		return None

	def on_press_key(self, keyboard):
		if keyboard.space:
			self.press_char_cell()
		if keyboard.backspace:
			self.scramble()
		self.draw_solved_mode = keyboard.enter and not self.draw_solved_mode

	def set_char_opacity_if_needed(self):
		char.set_default_opacity(MEMORY_PUZZLE_CHAR_OPACITY if self.rotatepic_map[char.c] != ROTATEPIC_PUZZLE_VALUE_OUTSIDE else 1)

	def on_update(self, level_time):
		self.set_char_opacity_if_needed()

	def finish(self):
		char.set_default_opacity(1)

