from cellactor import CellActor
from drop import Drop

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

from cursor import Cursor

cursor = Cursor('cursor')
