from . import *

class GatePuzzle(Puzzle):
	def assert_config(self):
		return flags.is_any_maze

	def is_long_generation(self):
		return True

	def is_finish_cell_required(self):
		return True

	def has_plate(self):
		return True

	def has_gate(self):
		return True

	def get_passed_gates(self, start_cell, target_cell):
		passed_gates = []
		for cell in self.Globals.find_path(start_cell, target_cell) or ():
			if self.map[cell] == CELL_GATE1:
				passed_gates.append(cell)
		return passed_gates

	def get_num_plates(self):
		return self.level["num_gate_puzzle_plates"] if "num_gate_puzzle_plates" in self.level else DEFAULT_NUM_GATE_PUZZLE_PLATES

	def get_num_gates(self):
		return self.level["num_gate_puzzle_gates"] if "num_gate_puzzle_gates" in self.level else DEFAULT_NUM_GATE_PUZZLE_GATES

	def toggle_gate(self, cx, cy):
		self.map[cx, cy] = CELL_GATE1 if self.map[cx, cy] == CELL_GATE0 else CELL_GATE0

	def press_plate(self):
		for gate in self.attached_plate_gates[char.c]:
			self.toggle_gate(*gate)

	def check_solution(self, finish_cell, gates, depth=0, visited_plate_gate_states=None):
		if depth == 0:
			self.Globals.debug_map(2, descr="Map initially")
			visited_plate_gate_states = {}

		start_cell = char.c

		if self.Globals.is_path_found(start_cell, finish_cell):
			if depth == 0:
				return False
			else:
				return {
					'used_plates': [],
					'open_gates': [],
					'passed_gates': self.get_passed_gates(start_cell, finish_cell),
				}

		best_solution = None
		best_plate = None

		plates = [ *self.attached_plate_gates ]
		gate_states = tuple(self.map[gate] for gate in gates)

		for plate in plates:
			if start_cell != plate and self.Globals.is_path_found(start_cell, plate):
				plate_gate_states = (plate, gate_states)
				if plate_gate_states in visited_plate_gate_states:
					solution = visited_plate_gate_states[plate_gate_states]
				else:
					visited_plate_gate_states[plate_gate_states] = None
					char.c = plate
					self.press_plate()

					solution = self.check_solution(finish_cell, gates, depth + 1, visited_plate_gate_states)

					self.press_plate()
					char.c = start_cell
					visited_plate_gate_states[plate_gate_states] = solution

				if solution and (not best_solution or len(solution["used_plates"]) < len(best_solution["used_plates"]) \
						or len(solution["used_plates"]) == len(best_solution["used_plates"]) and best_plate not in solution["used_plates"]):
					best_solution = solution
					best_plate = plate

		if best_solution:
			used_plates = best_solution["used_plates"].copy()
			if best_plate not in used_plates:
				used_plates.append(best_plate)

			open_gates = best_solution["open_gates"].copy()
			for gate in self.attached_plate_gates[best_plate]:
				if self.map[gate] == CELL_GATE0 and gate not in open_gates:
					open_gates.append(gate)

			passed_gates = best_solution["passed_gates"].copy()
			for gate in self.get_passed_gates(start_cell, best_plate):
				if gate not in passed_gates:
					passed_gates.append(gate)

			if depth == 0:
				return \
					len(used_plates)  >= self.get_num_plates() and \
					len(open_gates)   >= self.get_num_gates()  and \
					len(passed_gates) >= self.get_num_gates()
			else:
				return {
					'used_plates': used_plates,
					'open_gates': open_gates,
					'passed_gates': passed_gates,
				}

		return False if depth == 0 else None

	def generate_random_solvable_room(self, accessible_cells, finish_cell):
		origin_map = self.map.copy()

		def select_random_gates_attached_to_plate(num_gates):
			num_attached_gates = randint(MIN_GATE_PUZZLE_ATTACHED_GATES, MAX_GATE_PUZZLE_ATTACHED_GATES)
			if num_attached_gates > num_gates:
				num_attached_gates = num_gates
			attached_gate_idxs = []
			while len(attached_gate_idxs) < num_attached_gates:
				gate_idx = randint(0, num_gates - 1)
				if gate_idx in attached_gate_idxs:
					continue
				attached_gate_idxs.append(gate_idx)
			return attached_gate_idxs

		num_tries = 100000
		while num_tries > 0:
			plates = []
			for p in range(self.get_num_plates()):
				while True:
					cell = accessible_cells[randint(0, len(accessible_cells) - 1)]
					if self.map[cell] in CELL_CHAR_PLACE_OBSTACLES:
						continue
					self.map[cell] = CELL_PLATE
					plates.append(cell)
					break

			target_cells = [char.c, finish_cell, *plates]

			gates = []
			for g in range(self.get_num_gates()):
				while True:
					cell = accessible_cells[randint(0, len(accessible_cells) - 1)]
					if self.map[cell] in CELL_CHAR_PLACE_OBSTACLES:
						continue
					if self.Globals.get_num_accessible_target_directions(cell, target_cells) < 2:
						continue
					target_cells.append(cell)
					self.map[cell] = CELL_GATE0 if randint(0, 1) == 0 else CELL_GATE1
					gates.append(cell)
					break

			self.attached_plate_gates = {}
			for plate in plates:
				gate_idxs = select_random_gates_attached_to_plate(len(gates))
				self.attached_plate_gates[plate] = [ gates[i] for i in gate_idxs ]

			self.Globals.debug_map(4, descr="Generating gate puzzle - tries left: %d" % num_tries)
			if self.check_solution(finish_cell, gates):
				break

			copyto(self.map, origin_map)
			num_tries -= 1
		else:
			print("Can't generate gate puzzle, sorry")
			quit()

	def generate_room(self):
		self.generate_random_solvable_room(self.accessible_cells, self.finish_cell)

	def on_press_key(self, keyboard):
		if keyboard.space and self.map[char.c] == CELL_PLATE:
			self.press_plate()
		return False

