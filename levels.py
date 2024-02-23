from config import *

levels = [
	{
		"n": 1,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
#		"four_rooms": True,
		"random_maze": True,
		"char_health": 100,
	},
	{
		"n": 2,
		"num_enemies": 3,
		"theme": "ancient1",
		"music": "playful_sparrow",
		"four_rooms": True,
		"char_health": 150,
	},
	{
		"n": 3,
		"num_enemies": 0,
		"theme": "modern1",
		"music": "adventures",
		"barrel_puzzle": True,
		"num_barrels": 5,
		"char_health": None,
		"time_limit": 60,
		"target": 'level-target-kill-1-min',
	},
	{
		"n": 4,
		"num_enemies": 0,
		"theme": "modern1",
		"music": "valiant_warriors",
#		"four_rooms": True,
#		"color_puzzle_values": 4,
#		"color_puzzle_size": (7, 7),
		"color_puzzle": True,
		"time_limit": 80,
		"char_health": None,
		"target": 'complete-color-puzzle-green',
	},
	{
		"n": 5,
		"num_enemies": int(PLAY_SIZE_X * PLAY_SIZE_Y / 2),
		"theme": "modern2",
		"music": "breath",
		"char_health": 500,
	},
]
