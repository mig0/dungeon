import os
from filetools import get_dir_names
from config import DATA_DIR

PUZZLE_INFO_DIR = DATA_DIR + "/info/puzzles"

class PuzzleInfo:
	def die(self, error):
		print("PuzzleInfo for %s: %s" % (self.name, error))
		quit()

	def __init__(self, name):
		self.name = name
		self.filename = "%s/%s.txt" % (PUZZLE_INFO_DIR, name)
		if not os.path.isfile(self.filename):
			self.die("No required file %s found" % self.filename)
		file = open(self.filename, "r")
		self.title = file.readline().rstrip("\n")
		if self.title == "\n" or file.readline() != "\n":
			self.die("Invalid format: first line must be title, second line empty")

		self.goal = "Unspecified Goal"
		self.paragraphs = []
		paragraph = ""
		while line := file.readline():
			line = line.rstrip("\n")
			if line.startswith("Goal: "):
				self.goal = line[6:]
			elif line == "":
				if paragraph != "":
					self.paragraphs.append(paragraph)
					paragraph = ""
			else:
				if paragraph != "":
					paragraph += "\n"
				paragraph += line
		if paragraph != "":
			self.paragraphs.append(paragraph)

	def get_title(self):
		return self.title

	def get_description(self):
		return "\n\n".join(self.paragraphs)

	def get_goal(self):
		return self.goal

	def get_hypertext(self):
		return "### %s\n\n%s\n\nGoal: %s\n\n" % \
			(self.get_title(), self.get_description(), self.get_goal())

	def get_html(self):
		return '<h1>%s</h1>\n\n<p>%s\n</p>\n\n<p class="goal">%s</p>' % \
			(self.get_title(), "\n</p>\n\n<p>".join(self.paragraphs), self.get_goal())

def get_all_puzzleinfo_objects():
	all_names = get_dir_names(PUZZLE_INFO_DIR, ".txt")
	return (PuzzleInfo(name) for name in all_names)
