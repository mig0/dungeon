import pygame
from pgzero.actor import Actor, POS_TOPLEFT, ANCHOR_CENTER, transform_anchor
from pgzero.animation import *
from typing import Union, Tuple
from constants import CELL_W, CELL_H

MAX_ALPHA = 255  # based on pygame

NONE_CELL = (-1000, -1000)

active_inplace_animation_actors = []

def cmp(n1, n2):
	return 1 if n1 > n2 else 0 if n1 == n2 else -1

def product(x_range, y_range):
	return ((x, y) for x in x_range for y in y_range)

def apply_diff(orig, diff, subtract=False):
	factor = -1 if subtract else 1
	return (orig[0] + diff[0] * factor, orig[1] + diff[1] * factor)

def cell_diff(cell1, cell2):
	return (cell2[0] - cell1[0], cell2[1] - cell1[1])

def cell_direction(cell1, cell2):
	return (cmp(cell2[0], cell1[0]), cmp(cell2[1], cell1[1]))

def cell_to_pos(cell):
	return (CELL_W * (cell[0] + 0.5), CELL_H * (cell[1] + 0.5))

@tweener
def example(n):
	return n

class CellActor(Actor):
	def __init__(self, image:Union[str, pygame.Surface], pos=POS_TOPLEFT, anchor=ANCHOR_CENTER, scale=None, **kwargs):
		self._cell = None
		self._default_opacity = 1.0
		self.reset_inplace()
		self.unset_inplace_animation()
		self._unset_animation()

		image_str = None
		if isinstance(image, str):
			image_str = image
		super().__init__(image_str, pos, anchor, **kwargs)
		if isinstance(image, pygame.Surface):
			self._orig_surf = image
			self._update_pos()
		if scale is not None:
			self._scale = scale
			self.transform_surf()

	@property
	def c(self):
		return None if self._cell == NONE_CELL else self._cell

	@property
	def cx(self):
		return self._cell[0]

	@property
	def cy(self):
		return self._cell[1]

	@c.setter
	def c(self, cell):
		self._cell = NONE_CELL if cell is None else cell
		self.x, self.y = self.get_pos()

	def set_image(self, image):
		if self.image != image:
			self.image = image
			self.transform_surf()

	def get_pos(self):
		return cell_to_pos(self._cell)

	def sync_pos(self):
		self.pos = get_pos(self)

	def apply_pos_diff(self, diff, subtract=False):
		return apply_diff(cell_to_pos(self.c), diff, subtract)

	def move_pos(self, diff, undo=False):
		self.pos = self.apply_pos_diff(diff, undo)

	def move(self, diff, undo=False):
		self.c = apply_diff(self.c, diff, undo)

	def transform_surf(self):
		self._surf = self._orig_surf
		p = self.pos

		if self._scale != 1:
			size = self._orig_surf.get_size()
			self._surf = pygame.transform.scale(self._surf, (int(size[0] * self._scale), int(size[1] * self._scale)))
		if self._flip and (self._flip[0] or self._flip[1]):
			self._surf = pygame.transform.flip(self._surf, *self._flip)
		if self._angle != 0.0:
			self._surf = pygame.transform.rotate(self._surf, self._angle)

		alpha = int(self._opacity * MAX_ALPHA + 0.5)
		if alpha != MAX_ALPHA:
			alpha_img = pygame.Surface(self._surf.get_size(), pygame.SRCALPHA)
			alpha_img.fill((255, 255, 255, alpha))
			alpha_img.blit(self._surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
			self._surf = alpha_img

		self.width, self.height = self._surf.get_size()
		w, h = self._orig_surf.get_size()
		ax, ay = self._untransformed_anchor
		anchor = transform_anchor(ax, ay, w, h, self._angle)
		self._anchor = (anchor[0] * self._scale, anchor[1] * self._scale)

		self.pos = p

	def reset_inplace(self):
		self._opacity = self._default_opacity
		self._scale = 1.0
		self._angle = 0.0
		self._flip  = None
		if hasattr(self, '_orig_surf'):
			self.transform_surf()

	def is_inplace_animation_active(self):
		return self._inplace_animation_active

	def unset_inplace_animation(self, hard=True):
		if self in active_inplace_animation_actors:
			active_inplace_animation_actors.remove(self)
		self._inplace_animation_active  = False
		self._inplace_animation_opacity = None
		self._inplace_animation_scale   = None
		self._inplace_animation_angle   = None
		self._inplace_animation_flip    = None
		self._inplace_animation_tween   = None
		self._inplace_animation_start_time  = None
		self._inplace_animation_duration    = None
		self._inplace_animation_on_finished = None

	def reset_inplace_animation(self, hard=True):
		self.unset_inplace_animation()
		is_changed = False
		if self._opacity != self._default_opacity:
			self._opacity = self._default_opacity
			is_changed = True
		if self._scale != 1:
			self._scale = 1
			is_changed = True
		if self._angle != 0:
			self._angle = 0
			is_changed = True
		if self._angle is not None:
			self._flip = None
			is_changed = True
		if is_changed:
			self.transform_surf()

	def activate_inplace_animation(self, start_time, duration, opacity:Tuple[float, float]=None, scale:Tuple[float, float]=None, angle:Tuple[float, float]=None, flip:Tuple[bool, bool, int]=None, tween="linear", on_finished=None):
		self.unset_inplace_animation()

		is_defined = False
		if opacity:
			self._inplace_animation_opacity = opacity
			self._opacity = opacity[0]
			is_defined = True
		if scale:
			self._inplace_animation_scale = scale
			self._scale = scale[0]
			is_defined = True
		if angle:
			self._inplace_animation_angle = angle
			self._angle = angle[0]
			is_defined = True
		if flip and (flip[0] or flip[1]):
			self._inplace_animation_flip = flip
			is_defined = True
		if not is_defined:
			print("activate_inplace_animation called without opacity, scale or angle or flip, skipping")
			return

		self._inplace_animation_tween       = tween
		self._inplace_animation_start_time  = start_time
		self._inplace_animation_duration    = duration
		self._inplace_animation_on_finished = on_finished

		self.transform_surf()

		self._inplace_animation_active = True
		active_inplace_animation_actors.append(self)

	def update_inplace_animation(self, time):
		if not self.is_inplace_animation_active():
			return

		if self._inplace_animation_start_time == 0:
			self._inplace_animation_start_time = time

		factor = (time - self._inplace_animation_start_time) / self._inplace_animation_duration
		if factor > 1:
			factor = 1
		if factor < 0:
			factor = 0
		factor = TWEEN_FUNCTIONS[self._inplace_animation_tween](factor)

		if self._inplace_animation_opacity:
			self._opacity = self._inplace_animation_opacity[0] + factor * (self._inplace_animation_opacity[1] - self._inplace_animation_opacity[0])
		if self._inplace_animation_scale:
			self._scale   = self._inplace_animation_scale[0]   + factor * (self._inplace_animation_scale[1]   - self._inplace_animation_scale[0])
		if self._inplace_animation_angle:
			self._angle   = self._inplace_animation_angle[0]   + factor * (self._inplace_animation_angle[1]   - self._inplace_animation_angle[0])
		if self._inplace_animation_flip:
			self._flip = [ False, False ]
			if self._inplace_animation_flip[0] and int((0.999 if factor > 0.999 else factor) * self._inplace_animation_flip[2]) % 2 == self._inplace_animation_flip[2] % 2:
				self._flip[0] = True
			if self._inplace_animation_flip[1] and int((0.999 if factor > 0.999 else factor) * self._inplace_animation_flip[2]) % 2 == self._inplace_animation_flip[2] % 2:
				self._flip[1] = True

		self.transform_surf()

		if factor == 1:
			on_finished = self._inplace_animation_on_finished
			self.unset_inplace_animation()
			if on_finished:
				on_finished()

	def _unset_animation(self, on_finished=None):
		self.animation = None
		if on_finished:
			on_finished()

	def animate(self, duration, tween="linear", pos=None, on_finished=None):
		if pos is None:
			pos = self.get_pos()
		self.animation = animate(self, tween=tween, duration=duration, pos=pos, on_finished=lambda: self._unset_animation(on_finished))

	def is_animated_external(self):
		return self.animation is not None

	def is_animated(self):
		return self.is_inplace_animation_active() or self.is_animated_external()

	def set_default_opacity(self, default_opacity):
		is_default_opacity = self._opacity == self._default_opacity
		self._default_opacity = default_opacity
		if is_default_opacity and self._opacity != self._default_opacity:
			self._opacity = self._default_opacity
			self.transform_surf()

def create_actor(image_name, cell):
	actor = CellActor(image_name)
	actor.c = cell
	return actor

def get_actor_on_cell(cell, actors):
	for actor in actors:
		if cell == actor.c:
			return actor
	return None

def is_cell_in_actors(cell, actors):
	return get_actor_on_cell(cell, actors) is not None

