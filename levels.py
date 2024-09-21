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
		"target": "reach-finish",
		"char_health": 100,
		"gate_puzzle": {
			"num_gates": 2,
			"num_plates": 2,
		},
	},
	{
		"n": 2.2,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"random_maze": True,
		"target": "reach-finish",
		"char_health": 100,
		"gate_puzzle": {
			"num_gates": 4,
			"num_plates": 4,
		},
	},
	{
		"n": 2.3,
		"num_enemies": 5,
		"theme": "classic",
		"music": "a_new_path",
		"spiral_maze": True,
		"target": "reach-finish",
		"char_health": 100,
		"cloud_mode": True,
		"gate_puzzle": {
			"num_gates": 6,
			"num_plates": 4,
		},
	},
	{
		"n": 3.1,
		"num_enemies": 0,
		"theme": "modern1",
		"music": "adventures",
		"four_rooms": True,
		"char_health": None,
		"target": 'complete-color-puzzle-green',
		"color_puzzle": {
			"num_values": 2,
		},
	},
	{
		"n": 3.2,
		"num_enemies": 5,
		"theme": "modern1",
		"music": "valiant_warriors",
		"time_limit": 60,
		"char_health": 100,
		"target": 'complete-color-puzzle-green',
		"color_puzzle": {
			"num_values": 4,
			"size": (9, 9),
		},
	},
	{
		"n": 3.3,
		"num_enemies": 5,
		"theme": "modern1",
		"music": "adventures",
		"time_limit": 120,
		"char_health": 100,
		"target": 'complete-color-puzzle-green',
		"color_puzzle": {
			"num_values": 6,
			"size": (11, 11),
		},
	},
	{
		"n": 4.1,
		"num_enemies": 3,
		"theme": "modern2",
		"music": "breath",
		"char_health": 100,
		"target": 'complete-barrel-puzzle',
		"barrel_puzzle": {
			"num_barrels": 2,
		},
	},
	{
		"n": 4.2,
		"num_enemies": 5,
		"theme": "modern2",
		"music": "breath",
		"char_health": 100,
		"target": 'complete-barrel-puzzle',
		"barrel_puzzle": {
			"num_barrels": 5,
		},
	},
	{
		"n": 4.3,
		"num_enemies": 7,
		"theme": "modern2",
		"music": "breath",
		"char_health": 150,
		"target": 'complete-barrel-puzzle',
		"barrel_puzzle": {
			"num_barrels": 7,
		},
	},
	{
		"n": 5.1,
		"num_enemies": 3,
		"theme": "ancient1",
		"music": "breath",
		"random_maze": True,
		"char_health": 100,
		"target": "reach-finish",
		"lock_puzzle": {
			"min_locks": 2,
			"max_locks": 3,
		},
	},
	{
		"n": 5.2,
		"num_enemies": 5,
		"theme": "ancient1",
		"music": "breath",
		"random_maze": True,
		"char_health": 100,
		"target": "reach-finish",
		"lock_puzzle": {
			"min_locks": 3,
			"max_locks": 5,
		},
	},
	{
		"n": 5.3,
		"theme": "ancient1",
		"music": "breath",
		"random_maze": True,
		"enemy_key_drop": True,
		"char_health": 150,
		"target": "reach-finish",
		"lock_puzzle": {
			"min_locks": 5,
			"max_locks": 7,
		},
	},
	{
		"n": 6.1,
		"theme": "modern1",
		"music": "epic_cinematic_trailer",
		"num_enemies": 0,
		"char_health": None,
		"target": "complete-memory-puzzle",
		"memory_puzzle": {
			"size": (5, 3),
			"reveal_time": 10,
		},
	},
	{
		"n": 6.2,
		"theme": "stoneage1",
		"music": "stoneage/08_the_golden_valley",
		"has_start": True,
		"has_finish": True,
		"num_enemies": 0,
		"char_health": None,
		"target": "complete-memory-puzzle",
		"memory_puzzle": {
			"size": (3, 4),
		},
	},
	{
		"n": 6.3,
		"theme": "classic",
		"music": "epic_cinematic_trailer",
		"four_rooms": True,
		"num_enemies": 2,
		"char_health": 100,
		"target": "complete-memory-puzzle",
		"memory_puzzle": {
		},
	},
	{
		"n": 6.4,
		"theme": "ancient1",
		"music": "warfare",
		"nine_rooms": True,
		"time_limit": 150,
		"num_enemies": 0,
		"char_health": None,
		"target": "complete-memory-puzzle",
		"memory_puzzle": {
			"size": (3, 3),
			"reveal_time": 8,
		},
	},
	{
		"n": 6.5,
		"theme": "moss",
		"music": "forest_walk",
		"num_enemies": 0,
		"time_limit": 300,
		"char_health": None,
		"target": "complete-memory-puzzle-revealed-5-min",
		"memory_puzzle": {
			"is_revealed": True,
		},
	},
	{
		"n": 7.1,
		"theme": "default",
		"music": "stoneage/01_stardust_falling",
		"num_enemies": 0,
		"char_health": None,
		"target": "solve-fifteen-puzzle",
		"fifteen_puzzle": {
			"size": (3, 2),
		},
	},
	{
		"n": 7.2,
		"theme": "moss",
		"music": "forest_walk",
		"nine_rooms": True,
		"num_enemies": 0,
		"char_health": None,
		"target": "solve-fifteen-puzzle",
		"fifteen_puzzle": {
		},
	},
	{
		"n": 7.3,
		"theme": "stoneage1",
		"music": "film",
		"four_rooms": True,
		"num_enemies": 0,
		"char_health": None,
		"target": "solve-fifteen-puzzle",
		"fifteen_puzzle": {
			"size": (4, 4),
		},
	},
	{
		"n": 7.4,
		"theme": "stoneage2",
		"music": "stoneage/08_the_golden_valley.mp3",
		"num_enemies": 15,
		"char_health": 200,
		"has_start": True,
		"has_finish": True,
		"target": "solve-fifteen-puzzle",
		"fifteen_puzzle": {
			"size": (7, 7),
		},
	},
	{
		"n": 8.1,
		"theme": "default",
		"music": "forest_walk",
		"bg_image": "pictures/danik-lion-motocycle.jpg",
		"bg_image_crop": True,
		"num_enemies": 0,
		"char_health": None,
		"target": "solve-rotatepic-puzzle",
		"rotatepic_puzzle": {
			"size": (8, 8),
		},
	},
	{
		"n": 8.2,
		"theme": "default",
		"music": "stoneage/01_stardust_falling",
		"has_start": True,
		"has_finish": True,
		"num_enemies": 10,
		"char_health": 150,
		"target": "solve-rotatepic-puzzle",
		"rotatepic_puzzle": {
			"size": (7, 7),
			"image": "pictures/danik-lion-irisha-square.jpg",
		},
	},
	{
		"n": 8.3,
		"theme": "default",
		"music": "forest_walk",
		"num_enemies": 0,
		"char_health": None,
		"target": "solve-rotatepic-puzzle",
		"rotatepic_puzzle": {
			"image": "pictures/danik-lego-tiger.jpg",
			"image_crop": True,
		},
	},
	{
		"n": 8.4,
		"theme": "default",
		"music": "stoneage/01_stardust_falling",
		"bg_image": "pictures/danik-lion-irisha-cafe.jpg",
#		"bg_image_crop": True,
		"num_enemies": 0,
		"char_health": None,
		"target": "solve-rotatepic-puzzle",
		"rotatepic_puzzle": {
			"size": (9, 9),
		},
	},
	{
		"n": 9.1,
		"theme": "default",
		"music": "stoneage/01_stardust_falling",
		"num_enemies": 0,
		"char_health": None,
		"target": "reach-finish",
		"portal_puzzle": {
			"num_portals_per_hall": 2,
		},
	},
	{
		"n": 9.2,
		"theme": "stoneage2",
		"music": "stoneage/08_the_golden_valley.mp3",
		"has_start": True,
		"has_finish": True,
		"num_enemies": 5,
		"char_health": 100,
		"target": "reach-finish",
		"portal_puzzle": {
			"num_portals_per_hall": 3,
		},
	},
	{
		"n": 9.3,
		"theme": "moss",
		"music": "forest_walk",
		"num_enemies": 10,
		"char_health": 150,
		"target": "reach-finish",
		"portal_puzzle": {
		},
	},
	{
		"n": 10.1,
		"theme": "stoneage1",
		"music": "stoneage/01_stardust_falling",
		"bg_image": "bg/remains_of_a_threat.jpg",
		"char_health": 100,
		"target": "reach-finish",
		"stoneage_puzzle": {
		},
	},
	{
		"n": 11.1,
		"theme": "stoneage1",
		"music": "stoneage/08_the_golden_valley.mp3",
		"char_health": 40,
		"target": "reach-finish",
		"trivial_puzzle": True,
	},
]
