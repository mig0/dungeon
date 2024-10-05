from . import *

MEMORY_PUZZLE_VALUE_OUTSIDE = -1
CELL_MEMORY_FRAME = '~f'
CELL_MEMORY_VALUE = '~v'
CELL_MEMORY_OPENC = '~o'

class MemoryPuzzle(Puzzle):
	def init(self):
		self.memory_map = None
		self.room_memory_pairs = {}
		self.cell_images = []
		self.use_colors = False
		self.level_time = 0
		self.is_revealed = self.config.get("is_revealed", False)
		self.reveal_time = self.config.get("reveal_time", 0)
		self.unset_open_cells()

	def assert_config(self):
		return not flags.is_any_maze

	def unset_open_cells(self):
		self.open_cell1 = None
		self.open_cell2 = None
		self.open_cell2_time = None

	def on_set_theme(self):
		gray_frame_image = self.Globals.load_theme_cell_image('floor_gray_frame')
		self.cell_images = [gray_frame_image]
		for color in MAIN_COLOR_RGB_VALUES:
			cell_image = self.Globals.colorize_cell_image(gray_frame_image, color)
			self.cell_images.append(cell_image)

	def on_set_room(self, room):
		super().on_set_room(room)
		super().set_area_from_config()
		self.use_colors = self.get_num_pairs() <= len(MAIN_COLOR_RGB_VALUES)
		self.unset_open_cells()

	def has_empty_central_cell(self):
		return self.area.size_x * self.area.size_y % 2 == 1

	def get_empty_central_cell(self):
		return ((self.area.x1 + self.area.x2) // 2, (self.area.y1 + self.area.y2) // 2) \
			if self.has_empty_central_cell() else None

	def is_empty_central_cell(self, cell):
		return cell == self.get_empty_central_cell()

	def get_num_pairs(self):
		return (self.area.size_x * self.area.size_y) // 2

	def on_create_map(self, map):
		super().on_create_map(map)
		self.memory_map = ndarray((MAP_SIZE_X, MAP_SIZE_X), dtype=int)
		self.memory_map.fill(MEMORY_PUZZLE_VALUE_OUTSIDE)
		self.room_memory_pairs.clear()

	def is_target_to_be_solved(self):
		return True

	def is_solved(self):
		return not self.room_memory_pairs[self.room.idx]

	def get_reveal_time_left(self):
		return self.reveal_time - self.level_time

	def is_time_to_reveal(self):
		return self.get_reveal_time_left() > 0

	def handle_open_cell2(self):
		pair_idx = self.memory_map[self.open_cell1]
		if self.memory_map[self.open_cell2] == pair_idx:
			self.memory_map[self.open_cell1] = MEMORY_PUZZLE_VALUE_OUTSIDE
			self.memory_map[self.open_cell2] = MEMORY_PUZZLE_VALUE_OUTSIDE
			del self.room_memory_pairs[self.room.idx][pair_idx]
		self.unset_open_cells()

	def press_cell(self, cell):
		if self.memory_map[cell] == MEMORY_PUZZLE_VALUE_OUTSIDE:
			return

		if self.is_time_to_reveal():
			# allow to cancel reveal_time (otherwise, would just return)
			self.reveal_time = self.level_time

		if self.open_cell2:
			# allow to cancel open_cell2_time (otherwise, would just return)
			self.handle_open_cell2()

		if self.open_cell1:
			if cell == self.open_cell1:
				self.open_cell1 = None
			else:
				self.open_cell2 = cell
		else:
			self.open_cell1 = cell

	def generate_room(self):
		memory_pairs = {}
		for cell1 in self.area.cells:
			if self.is_empty_central_cell(cell1):
				continue
			if self.memory_map[cell1] == MEMORY_PUZZLE_VALUE_OUTSIDE:
				self.Globals.debug(3, "Finding unused pair_ids for %s" % str(cell1))
				while True:
					pair_idx = randint(1, self.get_num_pairs())
					if pair_idx not in memory_pairs:
						break
				self.Globals.debug(3, "	%d" % pair_idx)
				self.memory_map[cell1] = pair_idx
				self.Globals.debug(3, "Finding unused pair cell for %s" % str(cell1))
				while True:
					pair_cx = randint(self.area.x_range.start, self.area.x_range.stop - 1)
					pair_cy = randint(self.area.y_range.start, self.area.y_range.stop - 1)
					cell2 = (pair_cx, pair_cy)
					if self.is_empty_central_cell(cell2):
						continue
					if self.memory_map[cell2] == MEMORY_PUZZLE_VALUE_OUTSIDE:
						break
				self.Globals.debug(3, "	%s" % str(cell2))
				self.memory_map[cell2] = pair_idx
				memory_pairs[pair_idx] = (cell1, cell2)  # or True
		self.room_memory_pairs[self.room.idx] = memory_pairs

		if self.room.idx in (0, None):
			self.Globals.set_char_cell(self.get_empty_central_cell())

	def get_reveal_fade_factor(self):
		if self.is_time_to_reveal() and self.get_reveal_time_left() < MEMORY_PUZZLE_REVEAL_FADE_TIME:
			return self.get_reveal_time_left() / MEMORY_PUZZLE_REVEAL_FADE_TIME
		return None

	def modify_cell_types_to_draw(self, cell, cell_types):
		if self.memory_map[cell] == MEMORY_PUZZLE_VALUE_OUTSIDE:
			return
		cell_types.append(CELL_MEMORY_FRAME)
		if not self.use_colors and (self.is_time_to_reveal() or cell == self.open_cell1 or cell == self.open_cell2 or self.is_revealed):
			cell_types.append(CELL_MEMORY_VALUE)
		if self.use_colors and self.is_revealed and (cell == self.open_cell1 or cell == self.open_cell2):
			cell_types.extend((CELL_MEMORY_OPENC, CELL_MEMORY_OPENC))

	def get_cell_image_to_draw(self, cell, cell_type):
		if cell_type == CELL_MEMORY_FRAME:
			if self.use_colors:
				value = self.memory_map[cell] if self.is_revealed or self.is_time_to_reveal() or cell in (self.open_cell1, self.open_cell2) else 0
				if (reveal_fade_factor := self.get_reveal_fade_factor()) is not None and random() >= reveal_fade_factor:
					value = 0
			else:
				value = 1 if cell == self.open_cell1 and self.is_revealed else 2 if cell == self.open_cell2 and self.is_revealed else 0
			return self.cell_images[value]
		if cell_type == CELL_MEMORY_VALUE:
			alpha = 1
			if (reveal_fade_factor := self.get_reveal_fade_factor()) is not None:
				alpha = reveal_fade_factor
			return self.Globals.create_text_cell_image(str(self.memory_map[cell]), alpha=alpha)
		if cell_type == CELL_MEMORY_OPENC:
			return self.cell_images[0]
		return None

	def on_press_key(self, keyboard):
		if keyboard.space:
			self.press_cell(char.c)

		if keyboard.kp_enter:
			self.reveal_time = self.level_time + 5

	def set_char_opacity_if_needed(self):
		if not self.use_colors:
			char.set_default_opacity(MEMORY_PUZZLE_CHAR_OPACITY if self.memory_map[char.c] != MEMORY_PUZZLE_VALUE_OUTSIDE else 1)

	def on_update(self, level_time):
		self.level_time = level_time

		self.set_char_opacity_if_needed()

		if self.open_cell2:
			if self.open_cell2_time:
				if level_time > self.open_cell2_time:
					self.handle_open_cell2()
			else:
				self.open_cell2_time = level_time + MEMORY_PUZZLE_OPEN_CELL2_TIME

	def finish(self):
		char.set_default_opacity(1)

