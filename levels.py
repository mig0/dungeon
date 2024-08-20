from config import *

levels = [
	{
		"n": 1.1,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"random_maze": True,
		"char_health": 100,
	},
	{
		"n": 1.2,
		"num_enemies": 0,
		"theme": "modern1",
		"music": "inspire",
		"time_limit": 30,
		"spiral_maze": True,
		"char_health": None,
		"target": 'reach-finish-30-sec',
		"has_finish": True,
	},
	{
		"n": 1.3,
		"num_enemies": 5,
		"theme": "classic",
		"music": "playful_sparrow",
		"random_maze": True,
		"four_rooms": True,
		"char_health": 200,
	},
	{
		"n": 1.4,
		"num_enemies": 20,
		"theme": "classic",
		"music": "valiant_warriors",
		"time_limit": 60,
		"char_health": 250,
		"target": 'kill-all-1-min',
		"bg_image": "bg/stonehenge.jpg",
		"cloud_mode": True,
	},
	{
		"n": 2.1,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"random_maze": True,
		"gate_puzzle": True,
		"num_gate_puzzle_gates": 2,
		"num_gate_puzzle_plates": 2,
		"target": "reach-finish",
		"char_health": 100,
	},
	{
		"n": 2.2,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"random_maze": True,
		"gate_puzzle": True,
		"num_gate_puzzle_gates": 4,
		"num_gate_puzzle_plates": 4,
		"target": "reach-finish",
		"char_health": 100,
	},
	{
		"n": 2.3,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"spiral_maze": True,
		"gate_puzzle": True,
		"num_gate_puzzle_gates": 6,
		"num_gate_puzzle_plates": 4,
		"target": "reach-finish",
		"char_health": 100,
		"cloud_mode": True,
	},
	{
		"n": 3.1,
		"num_enemies": 0,
		"theme": "modern1",
		"music": "adventures",
		"four_rooms": True,
		"color_puzzle_values": 2,
		"color_puzzle": True,
		"char_health": None,
		"target": 'complete-color-puzzle-green',
	},
	{
		"n": 3.2,
		"num_enemies": 5,
		"theme": "modern1",
		"music": "valiant_warriors",
		"color_puzzle_values": 4,
		"color_puzzle_size": (9, 9),
		"color_puzzle": True,
		"time_limit": 60,
		"char_health": 100,
		"target": 'complete-color-puzzle-green',
	},
	{
		"n": 3.3,
		"num_enemies": 5,
		"theme": "modern1",
		"music": "adventures",
		"color_puzzle_values": 6,
		"color_puzzle_size": (11, 11),
		"color_puzzle": True,
		"time_limit": 120,
		"char_health": 100,
		"target": 'complete-color-puzzle-green',
	},
	{
		"n": 4.1,
		"num_enemies": 3,
		"num_barrels": 2,
		"theme": "modern2",
		"music": "breath",
		"barrel_puzzle": True,
		"char_health": 100,
		"target": 'complete-barrel-puzzle',
	},
	{
		"n": 4.2,
		"num_enemies": 5,
		"num_barrels": 5,
		"theme": "modern2",
		"music": "breath",
		"barrel_puzzle": True,
		"char_health": 100,
		"target": 'complete-barrel-puzzle',
	},
	{
		"n": 4.3,
		"num_enemies": 7,
		"num_barrels": 7,
		"theme": "modern2",
		"music": "breath",
		"barrel_puzzle": True,
		"char_health": 150,
		"target": 'complete-barrel-puzzle',
	},
	{
		"n": 5.1,
		"num_enemies": 3,
		"theme": "ancient1",
		"music": "breath",
		"random_maze": True,
		"lock_puzzle": True,
		"min_locks": 2,
		"max_locks": 3,
		"char_health": 100,
		"target": "reach-finish",
	},
	{
		"n": 5.2,
		"num_enemies": 5,
		"theme": "ancient1",
		"music": "breath",
		"random_maze": True,
		"lock_puzzle": True,
		"min_locks": 3,
		"max_locks": 5,
		"char_health": 100,
		"target": "reach-finish",
	},
	{
		"n": 5.3,
		"theme": "ancient1",
		"music": "breath",
		"lock_puzzle": True,
		"random_maze": True,
		"min_locks": 5,
		"max_locks": 7,
		"enemy_key_drop": True,
		"char_health": 100,
		"target": "reach-finish",
	},
	{
		"n": 0.1,
		"theme": "stoneage1",
		"music": "stoneage/01_stardust_falling",
		"stoneage_puzzle": True,
		"bg_image": "bg/remains_of_a_threat.jpg",
		"char_health": 100,
		"target": "reach-finish",
	},
]
