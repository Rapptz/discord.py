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
		print(entry)
		if entry in self.dictionary:
			while entry in self.dictionary:
				entry = self.dictionary[entry]
			return entry
		else:
			return 'None'
		
	def commandReader(self, params):
		return self.readEntry('.'.join(params))
