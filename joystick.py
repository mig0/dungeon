import pygame
from pgzero.constants import keys

DEBUG_PRESSES = False

BUTTON_NAMES = {
	0:  'ACTIVATE',
	1:  'CANCEL',
	2:  'INTERACT',
	3:  'SELECT',
	4:  'SHARE',
	5:  'SYSTEM',
	6:  'OPTIONS',
	9:  'LSHIFT',
	10: 'RSHIFT',
	11: 'PLAY',
	12: 'STOP',
	13: 'PREV',
	14: 'NEXT',
}

# these used for motion unless modifier is pressed
BUTTON_NAMES_REQUIRING_MODIFIER = [
	'PLAY',
	'STOP',
	'PREV',
	'NEXT',
]

MODIFIER_BUTTONS = {
	'LSHIFT': 9,
	'RSHIFT': 10,
}

MODIFIER_AXES = {
	'LCTRL': 4,
	'RCTRL': 5,
}

STICK_AXES = {
	'LEFT_X':  0,
	'LEFT_Y':  1,
	'RIGHT_X': 2,
	'RIGHT_Y': 3,
}

MODIFIER_AXIS_SENSITIVITY = 0.2
STICK_AXIS_SENSITIVITY = 0.5

joysticks = []

class Joystick():
	def __init__(self, joystick):
		self.joystick = joystick

		names = list(BUTTON_NAMES.values()) + [*MODIFIER_AXES,] + [*STICK_AXES,]
		self.is_pressed = dict((name, False) for name in names)
		self.hidden_press = dict((button_name, False) for button_name in BUTTON_NAMES_REQUIRING_MODIFIER)

	@classmethod
	def find(cls, joystick):
		for j in joysticks:
			if j.joystick == joystick:
				return j
		return None

	@classmethod
	def register(cls, joystick):
		if cls.find(joystick) is not None:
			return
		joystick.init()
		joystick = Joystick(joystick)
		joysticks.append(joystick)

	@classmethod
	def unregister(cls, joystick):
		joystick.quit()
		joystick = Joystick.find(joystick)
		if joystick is not None:
			joysticks.remove(joystick)

	def _is_button_pressed(self, button):
		return self.joystick.get_button(button)

	def _is_modifier_axis_pressed(self, axis):
		return self.joystick.get_axis(axis) > -1 + MODIFIER_AXIS_SENSITIVITY

	def _is_stick_axis_pressed(self, axis):
		value = self.joystick.get_axis(axis)
		return 1 if value > +STICK_AXIS_SENSITIVITY else -1 if value < -STICK_AXIS_SENSITIVITY else False

	def capture_pressed_state(self):
		self.old_is_pressed = self.is_pressed.copy()
		for button, button_name in BUTTON_NAMES.items():
			self.is_pressed[button_name] = self._is_button_pressed(button)
		for modifier, axis in MODIFIER_AXES.items():
			self.is_pressed[modifier] = self._is_modifier_axis_pressed(axis)
		for stick, axis in STICK_AXES.items():
			self.is_pressed[stick] = self._is_stick_axis_pressed(axis)

	def is_any_modifier_pressed(self, modifiers=('LCTRL', 'RCTRL', 'LSHIFT', 'RSHIFT')):
		for name in modifiers:
			if self.is_pressed[name]:
				return True
		return False

	def was_pressed(self, name):
		return not self.old_is_pressed[name] and self.is_pressed[name]

	def was_released(self, name):
		return self.old_is_pressed[name] and not self.is_pressed[name]

	def when_stick_pressed(self, axis, ret1, ret2):
		if self.is_pressed[axis] == False:
			return None
		return ret1 if self.is_pressed[axis] == -1 else ret2

def scan_active_joysticks():
	dead_joysticks = [ j.joystick for j in joysticks ]
	for i in range(pygame.joystick.get_count()):
		joystick = pygame.joystick.Joystick(i)
		Joystick.register(joystick)
		if joystick in dead_joysticks:
			dead_joysticks.remove(joystick)

	for joystick in dead_joysticks:
		Joystick.unregister(joystick)

def scan_joysticks_and_state():
	scan_active_joysticks()

	for joystick in joysticks:
		joystick.capture_pressed_state()

PRESSED_NAME_KEYS = {
	'ACTIVATE': keys.SPACE,
	'CANCEL':   keys.ESCAPE,
	'INTERACT': keys.RETURN,
	'SELECT':   keys.M,
	'LSHIFT':   keys.LSHIFT,
	'RSHIFT':   keys.RSHIFT,
	'PREV':     keys.P,
	'NEXT':     keys.N,
	'PLAY':     keys.R,
	'STOP':     keys.Q,
	'LCTRL':    keys.LCTRL,
	'RCTRL':    keys.RCTRL,
}

def emulate_joysticks_press_key(keyboard):
	if not joysticks:
		return False

	pressed_names  = set()
	released_names = set()
	for joystick in joysticks:
		for button, button_name in BUTTON_NAMES.items():
			may_hide_press = button_name in BUTTON_NAMES_REQUIRING_MODIFIER
			if joystick.was_pressed(button_name):
				if may_hide_press and not joystick.is_any_modifier_pressed():
					joystick.hidden_press[button_name] = True
				else:
					pressed_names.add(button_name)
			if joystick.was_released(button_name):
				if may_hide_press and joystick.hidden_press[button_name]:
					joystick.hidden_press[button_name] = False
				else:
					released_names.add(button_name)

		for modifier, axis in MODIFIER_AXES.items():
			if joystick.was_pressed(modifier):
				pressed_names.add(modifier)
			if joystick.was_released(modifier):
				released_names.add(modifier)

	for name in pressed_names:
		keyboard._press(PRESSED_NAME_KEYS[name])
	for name in released_names:
		keyboard._release(PRESSED_NAME_KEYS[name])

	if DEBUG_PRESSES and (pressed_names or released_names):
		print("Pressed:", pressed_names or {}, "Released:", released_names or {})

	return pressed_names or released_names

ARROW_KEY_BUTTON_PAIRS = (
	('r', 'NEXT'),
	('l', 'PREV'),
	('u', 'PLAY'),
	('d', 'STOP'),
)

def get_joysticks_arrow_keys():
	arrow_keys = []
	if not joysticks:
		return arrow_keys

	def add_arrow_key(arrow_key):
		if arrow_key is not None and arrow_key not in arrow_keys:
			arrow_keys.append(arrow_key)

	for arrow_key, button_name in ARROW_KEY_BUTTON_PAIRS:
		for joystick in joysticks:
			if joystick.is_pressed[button_name] and not joystick.is_any_modifier_pressed():
				add_arrow_key(arrow_key)

			add_arrow_key(joystick.when_stick_pressed('LEFT_X', 'l', 'r'))
			add_arrow_key(joystick.when_stick_pressed('LEFT_Y', 'u', 'd'))

	return arrow_keys
