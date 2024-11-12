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

	def on_create_map(self, map):
		super().on_create_map(map)
		self.attached_plate_gates = {}

	def store_level(self, stored_level):
		stored_level["attached_plate_gates"] = self.attached_plate_gates

	def restore_level(self, stored_level):
		self.attached_plate_gates = stored_level["attached_plate_gates"]

	def get_passed_gates(self, start_cell, target_cell):
		passed_gates = []
		for cell in self.Globals.find_path(start_cell, target_cell) or ():
			if self.map[cell] == CELL_GATE1:
				passed_gates.append(cell)
		return passed_gates

	def toggle_gate(self, cx, cy):
		self.map[cx, cy] = CELL_GATE1 if self.map[cx, cy] == CELL_GATE0 else CELL_GATE0

	def press_plate(self):
		for gate in self.attached_plate_gates[char.c]:
			self.toggle_gate(*gate)

	def check_solution(self, finish_cell, plates, gates, depth=0, visited_plate_gate_states=None):
		if depth == 0:
			self.Globals.debug_map(2, descr="Checking solution for map")
			visited_plate_gate_states = {}

			# if plate is close to finish, fail such map immediately
			for cell in self.Globals.get_accessible_cells(finish_cell, gates):
				if self.map[cell] == CELL_PLATE:
					self.Globals.debug(3, "Fail map due to plate close to finish")
					return False

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

					solution = self.check_solution(finish_cell, plates, gates, depth + 1, visited_plate_gate_states)

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
				self.Globals.debug(3, "Used plates: %d of %d, Open gates: %d of %d, Passed gates: %d of %d, Num states: %d" % (len(used_plates), self.num_plates, len(open_gates), self.num_gates, len(passed_gates), self.num_gates, len(visited_plate_gate_states)))
				return \
					len(used_plates)  >= self.num_plates and \
					len(open_gates)   >= self.num_gates  and \
					len(passed_gates) >= self.num_gates
			else:
				return {
					'used_plates': used_plates,
					'open_gates': open_gates,
					'passed_gates': passed_gates,
				}

		return False if depth == 0 else None

	def generate_random_solvable_room(self, accessible_cells, finish_cell):
		orig_map = self.map.copy()
		orig_attached_plate_gates = self.attached_plate_gates.copy()

		self.num_plates = self.parse_config_num("num_plates", DEFAULT_NUM_GATE_PUZZLE_PLATES)
		self.num_gates  = self.parse_config_num("num_gates",  DEFAULT_NUM_GATE_PUZZLE_GATES)

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
			for p in range(self.num_plates):
				while True:
					cell = accessible_cells[randint(0, len(accessible_cells) - 1)]
					if self.map[cell] in CELL_CHAR_PLACE_OBSTACLES:
						continue
					self.map[cell] = CELL_PLATE
					plates.append(cell)
					break

			target_cells = [char.c, finish_cell, *plates]

			gates = []
			for g in range(self.num_gates):
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

			for plate in plates:
				gate_idxs = select_random_gates_attached_to_plate(len(gates))
				self.attached_plate_gates[plate] = [ gates[i] for i in gate_idxs ]

			self.Globals.debug(3, "Generating gate puzzle - tries left: %d" % num_tries)
			self.Globals.debug(3, "Attached plate gates: %s" % str(self.attached_plate_gates))
			if self.check_solution(finish_cell, plates, gates):
				break

			copyto(self.map, orig_map)
			self.attached_plate_gates = orig_attached_plate_gates
			num_tries -= 1
		else:
			print("Can't generate gate puzzle for %d plates and %d gates, sorry" % (self.num_plates, self.num_gates))
			quit()

	def generate_room(self):
		self.generate_random_solvable_room(self.accessible_cells, self.finish_cell)

	def on_press_key(self, keyboard):
		if keyboard.space and self.map[char.c] == CELL_PLATE:
			self.press_plate()
		return False

