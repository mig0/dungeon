class Flags:
	def parse_level(self, level):
		self.is_random_maze    = level.get("random_maze")
		self.is_spiral_maze    = level.get("spiral_maze")
		self.is_grid_maze      = level.get("grid_maze")
		self.is_four_rooms     = level.get("four_rooms")
		self.is_cloud_mode     = level.get("cloud_mode")
		self.is_enemy_key_drop = level.get("enemy_key_drop")
		self.is_stopless       = level.get("stopless")
		self.has_start         = level.get("has_start")
		self.has_finish        = level.get("has_finish")

flags = Flags()
