import json
 
class DictionaryReader:
	def __init__(self):
		self.file = 'dictEntries.txt'
		self.dictionary = {}
		self.loadDict()
		
	def loadDict(self):
		with open(self.file, 'r') as f:
			s = f.read()
			self.dictionary = json.loads(s)
	
	def readEntry(self, entry):
		if entry in self.dictionary:
			return self.dictionary[entry]	