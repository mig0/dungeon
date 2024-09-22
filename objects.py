from cellactor import CellActor
from drop import Drop

class Area:
	# x1, y1, x2, y2, size_x, size_y, x_range, y_range, idx
	pass

char = CellActor('stand')

enemies = []
barrels = []
lifts = []

portal_destinations = {}

drop_heart = Drop('heart')
drop_sword = Drop('sword')
drop_key1  = Drop('key1')
drop_key2  = Drop('key2')

drops = (drop_heart, drop_sword, drop_key1, drop_key2)
