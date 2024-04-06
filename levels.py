from config import *

levels = [
	{
		"n": 0,
		"num_enemies": 0,
		"theme": "stoneage1",
		"music": "stoneage/01_stardust_falling",
		"spiral_maze": True,
		"stoneage_puzzle": True,
		"gate_puzzle": True,
		"bg_image": "bg/remains_of_a_threat.jpg",
		"char_health": None,
	},
	{
		"n": 1,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"random_maze": True,
#		"portal_end": True,
#		"cloud_mode": True,
		"char_health": 100,
	},
	{
		"n": 2,
		"num_enemies": 3,
		"theme": "ancient1",
		"music": "playful_sparrow",
		"four_rooms": True,
		"time_limit": 60,
		"char_health": 150,
		"target": 'level-target-kill-1-min',
		"bg_image": "bg/stonehenge.jpg",
		"cloud_mode": True,
	},
	{
		"n": 3,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"random_maze": True,
		"gate_puzzle": True,
#		"portal_end": True,
#		"four_rooms": True,
		"target": "reach-portal",
		"char_health": 100,
	},
	{
		"n": 4,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"grid_maze": True,
		"four_rooms": True,
		"portal_end": True,
#		"cloud_mode": True,
		"char_health": 100,
	},
	{
		"n": 5,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"spiral_maze": True,
		"four_rooms": True,
		"portal_end": True,
		"target": "reach-portal",
		"char_health": 100,
	},
	{
		"n": 6,
		"num_enemies": 0,
		"theme": "modern1",
		"music": "adventures",
		"four_rooms": True,
		"color_puzzle_values": 3,
		"color_puzzle": True,
		"char_health": None,
		"target": 'complete-color-puzzle-green',
#		"cloud_mode": True,
	},
	{
		"n": 7,
		"num_enemies": 0,
		"num_enemies": 6,
		"theme": "modern1",
		"music": "valiant_warriors",
#		"four_rooms": True,
#		"color_puzzle_values": 4,
		"color_puzzle_size": (9, 9),
		"color_puzzle": True,
		"time_limit": 80,
		"char_health": None,
		"char_health": 100,
		"target": 'complete-color-puzzle-green',
#		"cloud_mode": True,
	},
	{
		"n": 8,
		"num_enemies": 0,
		"num_barrels": 10,
		"theme": "modern1",
		"music": "adventures",
#		"random_maze": True,
#		"four_rooms": True,
		"barrel_puzzle": True,
		"char_health": 150,
#		"cloud_mode": True,
#		"actors_always_revealed": True,
	},
	{
		"n": 9,
		"num_enemies": int(PLAY_SIZE_X * PLAY_SIZE_Y / 2),
		"theme": "modern2",
		"music": "breath",
		"char_health": 500,
#		"cloud_mode": True,
	},
]
