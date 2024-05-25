import sys
from constants import *
from cellactor import *

class Drop:
	def __init__(self, name):
		self.reset()
		self.name = name
		self.actor = CellActor(name)
		self.status_actor = CellActor(name, scale=0.7)

	def reset(self):
		self.active = False
		self.num_contained = 0
		self.num_collected = 0
		self.cells = []

	def has_instance(self, cell):
		return cell in self.cells

	def contain(self, actor):
		self.num_contained += 1

	def instantiate(self, actor):
		if isinstance(actor, tuple):
			cell = actor
		else:
			cell = actor.c
			self.num_contained -= 1
		self.cells.append(cell)

	def collect(self, curr_cell):
		for cell in self.cells:
			if cell == curr_cell:
				self.cells.remove(cell)
				self.num_collected += 1
				return True
		return False

	def consume(self):
		self.num_collected -= 1

	def draw_instances(self):
		for cell in self.cells:
			self.actor.c = cell
			self.actor.draw()

	def str(self):
		return "%s/%s" % (self.num_collected, self.num_contained + len(self.cells) + self.num_collected)

def draw_status_drops(screen, drops):
	active_drops = [ drop for drop in drops if drop.active ]
	n = len(active_drops)
	i = 0
	for drop in active_drops:
		pos_x = POS_CENTER_X + CELL_W * (i * STATUS_DROP_X_SIZE - n + 1)
		drop.status_actor.pos = (pos_x + CELL_W * STATUS_DROP_X_ACTOR_OFFSET, POS_STATUS_Y)
		drop.status_actor.draw()
		screen.draw.text(drop.str(), center=(pos_x + CELL_W * STATUS_DROP_X_TEXT_OFFSET, POS_STATUS_Y), color="#FFAA00", gcolor="#AA6600", owidth=1.2, ocolor="#404030", alpha=1, fontsize=24)
		i += 1
