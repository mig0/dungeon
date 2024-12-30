import os
import filecmp
from glob import glob
from config import DATA_DIR

class RegenerateFile():
	def __init__(self, filename):
		self.file = None
		self.filename = filename
		self.new_filename = filename + ".new"
		self.file = open(self.new_filename, "w")
		if not self.file:
			print("Can't open file %s for writing" % self.new_filename)
			exit(2)

	def finalize(self):
		if not self.file:
			return
		self.file.close()
		if os.path.isfile(self.filename) and filecmp.cmp(self.filename, self.new_filename, shallow=False):
			os.remove(self.new_filename)
			print("File %s was not changed" % self.filename)
		else:
			os.rename(self.new_filename, self.filename)
			print("Generated new %s" % self.filename)

	def write(self, text):
		return self.file.write(text)

	def print(self, text, end='\n'):
		return self.write(text + end)

def get_dir_names(dirname, ext):
	prefix = DATA_DIR + '/' + dirname + '/'
	return sorted(filename.removeprefix(prefix).removesuffix(ext) for filename in glob(prefix + "*" + ext))

