from . import *

MAX_SOLUTION_DEPTH = 500

class BarrelPuzzle(Puzzle):
	def init(self):
		self.solution_mode = False

	def assert_config(self):
		return not flags.is_any_maze

	def has_plate(self):
		return True

	def is_long_generation(self):
		return True

	def is_target_to_be_solved(self):
		return True

	def get_room_barrels(self):
		return [ barrel for barrel in barrels if self.Globals.is_actor_in_room(barrel) ]

	def find_solution(self, init=True):
		if init:
			self.solution = []
			self.char_cell = char.c
			self.plate_cells = [tuple(cell) for cell in argwhere(self.map == CELL_PLATE) ]
			self.plate_cells.sort()
			self.barrel_cells = [ barrel.c for barrel in self.get_room_barrels() ]
			self.barrel_cells.sort()
			self.visited_positions = []

		if len(self.solution) >= MAX_SOLUTION_DEPTH:
			return False

		accessible_cells = self.Globals.get_accessible_cells(self.char_cell, self.barrel_cells)
		accessible_cells.sort()

		position_id = [ *accessible_cells, *self.barrel_cells, ]
		if position_id in self.visited_positions:
			return False
		self.visited_positions.append(position_id)

#		if all(cell in self.barrel_cells for cell in self.plate_cells):
		if self.plate_cells == self.barrel_cells:
			return True

		accessible_cells_near_barrels = [ (cell, barrel_cell) for cell in accessible_cells for barrel_cell in self.barrel_cells if get_distance(cell, barrel_cell) == 1 ]

		for cell, barrel_cell in accessible_cells_near_barrels:
			next_barrel_cell = apply_diff(barrel_cell, cell_diff(cell, barrel_cell))
			if not self.is_in_room(next_barrel_cell) or self.map[next_barrel_cell] in CELL_CHAR_MOVE_OBSTACLES or next_barrel_cell in self.barrel_cells:
				continue

			char_path = self.Globals.find_path(self.char_cell, cell, self.barrel_cells)

			old_barrel_cells = [ *self.barrel_cells ]
			self.barrel_cells.remove(barrel_cell)
			self.barrel_cells.append(next_barrel_cell)
			self.barrel_cells.sort()
			old_char_cell = self.char_cell
			self.char_cell = barrel_cell

			self.solution.append(char_path + [barrel_cell])
			if self.find_solution(init=False):
				return True
			self.solution.pop()

			self.barrel_cells = old_barrel_cells
			self.char_cell = old_char_cell

		return False

	def on_generate_map(self):
		self.Globals.convert_inner_walls(CELL_VOID if "bg_image" in self.level else None)

	def pull_barrel_randomly(self, barrel, visited_cell_pairs, num_moves):
		idx = barrels.index(barrel)
		weighted_neighbors = []
		# sort 4 barrel directions to place char to the "adjacent to barrel" cell for a pull (prefer empty cells)
		for c in self.Globals.get_actor_neighbors(barrel, self.room.x_range, self.room.y_range):
			if (c, char.c) in visited_cell_pairs:
				continue
			cx, cy = c
			if is_cell_in_actors(c, barrels):
				continue
			new_cx = cx + cx - barrel.cx
			new_cy = cy + cy - barrel.cy
			if new_cx not in self.room.x_range or new_cy not in self.room.y_range:
				continue
			if is_cell_in_actors((new_cx, new_cy), barrels):
				continue
			weight = randint(0, 30)
			if self.map[cx, cy] not in CELL_WALLS:
				weight += 20
			if self.map[cx, cy] == CELL_PLATE:
				weight += 4
			if self.map[new_cx, new_cy] not in CELL_WALLS:
				weight += 10
			if self.map[new_cx, new_cy] == CELL_PLATE:
				weight += 2
			weighted_neighbors.append((weight, c))

		neighbors = [n[1] for n in sorted(weighted_neighbors, reverse=True)]

		if not neighbors:
			# can't find free neighbor for barrel, stop
			self.Globals.debug(2, "barrel #%d - failed to find free neighbor for barrel %s (%d left)" % (idx, barrel.c, num_moves))
			return False

		for neighbor in neighbors:
			cx, cy = neighbor

			# if the cell is not empty (WALL), make it empty (FLOOR with additions)
			was_wall1_replaced = False
			if self.map[cx, cy] == CELL_WALL:
				self.Globals.convert_to_floor_if_needed(cx, cy)
				was_wall1_replaced = True
			barrel_cx = barrel.cx
			barrel_cy = barrel.cy
			new_char_cx = cx + (cx - barrel_cx)
			new_char_cy = cy + (cy - barrel_cy)
			self.Globals.debug(2, "barrel #%d - neighbor %s, next cell (%d, %d)" % (idx, neighbor, new_char_cx, new_char_cy))
			self.Globals.debug_map(2, full=True, clean=True, dual=True)
			was_wall2_replaced = False
			if self.map[new_char_cx, new_char_cy] == CELL_WALL:
				self.Globals.convert_to_floor_if_needed(new_char_cx, new_char_cy)
				was_wall2_replaced = True

			# if the char position is not None, first create random free path to the selected adjacent cell
			old_char_c = char.c
			if char.c is None:
				char.c = (cx, cy)
			if self.Globals.generate_random_free_path(neighbor):
				# pull the barrel to the char
				barrel.c = char.c
				char.c = (new_char_cx, new_char_cy)

				visited_cell_pairs.append((neighbor, char.c))

				if num_moves <= 1:
					return True

				if self.pull_barrel_randomly(barrel, visited_cell_pairs, num_moves - 1):
					return True
				else:
					self.Globals.debug(2, "barrel #%d - failed to pull barrel (%d moves left)" % (idx, num_moves - 1))
			else:
				self.Globals.debug(2, "barrel #%d - failed to generate random free path to neighbor %s" % (idx, neighbor))

			# can't create free path for char or can't pull barrel, restore the original state
			char.c = old_char_c
			barrel.c = (barrel_cx, barrel_cy)
			if was_wall1_replaced:
				self.map[cx, cy] = CELL_WALL
			if was_wall2_replaced:
				self.map[new_char_cx, new_char_cy] = CELL_WALL

		return False

	def generate_random_solvable_room(self):
		num_barrels = self.config.get("num_barrels", DEFAULT_NUM_BARRELS)

		def get_random_cell():
			return (randint(self.room.x1, self.room.x2), randint(self.room.y1, self.room.y2))

		# 0) initialize char position to None
		char.c = None

		# 1) initialize entire room to WALL
		for cy in self.room.y_range:
			for cx in self.room.x_range:
				self.map[cx, cy] = CELL_WALL

		# 2) place room plates randomly or in good positions, as the number of barrels
		# 3) place room barrels into the place cells, one barrel per one plate
		for n in range(num_barrels):
			while True:
				cell = get_random_cell()
				if self.map[cell] != CELL_PLATE:
					self.map[cell] = CELL_PLATE
					break
			self.Globals.create_barrel(cell)

		# 4) for each room barrel do:
		for barrel in barrels:
			self.Globals.debug(2, "barrel #%d - starting (%d, %d)" % (barrels.index(barrel), barrel.cx, barrel.cy))
			visited_cell_pairs = [(barrel.c, char.c)]
			# 5) make random moves for the barrel until possible
			num_moves = randint(10, 80)
			self.pull_barrel_randomly(barrel, visited_cell_pairs, num_moves)
			self.Globals.debug(2, "barrel #%d - finished (%d, %d)" % (barrels.index(barrel), barrel.cx, barrel.cy))

		# 11) remember the char position, optionally try to move it as far left-top as possible
		if char.c is None:
			print("Failed to generate random solvable barrel room")
			if DEBUG_LEVEL:
				return
			else:
				quit()

		while True:
			for c in self.Globals.get_actor_neighbors(char, self.room.x_range, self.room.y_range):
				cx, cy = c
				if cx > char.cx or cy > char.cy:
					continue
				if not self.map[c] in CELL_CHAR_MOVE_OBSTACLES:
					char.c = c
					if self.room.idx:
						self.Globals.set_char_cell(c)
					break
			else:
				break

	def generate_room(self):
		self.generate_random_solvable_room()

	def is_solved(self):
		for barrel in self.get_room_barrels():
			if self.map[barrel.c] != CELL_PLATE:
				return False
		return True

	def on_press_key(self, keyboard):
		if keyboard.kp_enter:
			solution = self.find_solution()
			self.solution = [cell for cells in self.solution for cell in cells]
			self.solution_time = 0
			self.solution_mode = True
		else:
			self.solution_mode = False

	def on_update(self, level_time):
		if self.solution_mode:
			if level_time > self.solution_time:
				if self.solution:
					new_cell = self.solution[0]
					dx, dy = cell_diff(char.c, new_cell)
					self.Globals.move_char(dx, dy)
					if char.c == new_cell:
						self.solution.pop(0)
						if not self.solution:
							self.solution_mode = False
					self.solution_time = level_time + 0.3
