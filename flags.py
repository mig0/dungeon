from constants import *

def round_odd(n):
	return (n - 1) // 2 * 2 + 1

class Flags:
	def parse_level(self, level):
		self.is_random_maze    = level.get("random_maze")
		self.is_spiral_maze    = level.get("spiral_maze")
		self.is_grid_maze      = level.get("grid_maze")
		self.is_four_rooms     = level.get("four_rooms")
		self.is_nine_rooms     = level.get("nine_rooms")
		self.is_cloud_mode     = level.get("cloud_mode")
		self.is_enemy_key_drop = level.get("enemy_key_drop")
		self.is_stopless       = level.get("stopless")
		self.has_start         = level.get("has_start")
		self.has_finish        = level.get("has_finish")

		self.is_any_maze = self.is_random_maze or self.is_spiral_maze or self.is_grid_maze

		if self.is_four_rooms:
			self.NUM_ROOMS = 4
			self.ROOM_SIZE_X = ROOM_4_SIZE_X
			self.ROOM_SIZE_Y = ROOM_4_SIZE_Y
			self.ROOM_X1 = ROOM_4_X1
			self.ROOM_X2 = ROOM_4_X2
			self.ROOM_Y1 = ROOM_4_Y1
			self.ROOM_Y2 = ROOM_4_Y2
			self.ROOM_X_RANGE = ROOM_4_X_RANGE
			self.ROOM_Y_RANGE = ROOM_4_Y_RANGE
			self.ROOM_BORDERS_X = ROOM_4_BORDERS_X
			self.ROOM_BORDERS_Y = ROOM_4_BORDERS_Y
		elif self.is_nine_rooms:
			self.NUM_ROOMS = 9
			self.ROOM_SIZE_X = ROOM_9_SIZE_X
			self.ROOM_SIZE_Y = ROOM_9_SIZE_Y
			self.ROOM_X1 = ROOM_9_X1
			self.ROOM_X2 = ROOM_9_X2
			self.ROOM_Y1 = ROOM_9_Y1
			self.ROOM_Y2 = ROOM_9_Y2
			self.ROOM_X_RANGE = ROOM_9_X_RANGE
			self.ROOM_Y_RANGE = ROOM_9_Y_RANGE
			self.ROOM_BORDERS_X = ROOM_9_BORDERS_X
			self.ROOM_BORDERS_Y = ROOM_9_BORDERS_Y
		else:
			self.NUM_ROOMS = 1
			self.ROOM_SIZE_X = [PLAY_SIZE_X]
			self.ROOM_SIZE_Y = [PLAY_SIZE_Y]
			self.ROOM_X1 = [PLAY_X1]
			self.ROOM_X2 = [PLAY_X2]
			self.ROOM_Y1 = [PLAY_Y1]
			self.ROOM_Y2 = [PLAY_Y2]
			self.ROOM_X_RANGE = [PLAY_X_RANGE]
			self.ROOM_Y_RANGE = [PLAY_Y_RANGE]
			self.ROOM_BORDERS_X = []
			self.ROOM_BORDERS_Y = []

		self.MULTI_ROOMS = self.NUM_ROOMS > 1

	def ROOM_SIZE(self, room_idx, request_odd=False):
		if request_odd:
			return (round_odd(self.ROOM_SIZE_X[room_idx]), round_odd(self.ROOM_SIZE_Y[room_idx]))
		return (self.ROOM_SIZE_X[room_idx], self.ROOM_SIZE_Y[room_idx])

flags = Flags()
