import re

class DNPFile(object):
	def __init__(self, filename):
		lines = open(filename).readlines()
		self.valuem_dnp = []
		self.refdesm_dnp = []
		
		for i in lines:
			if i.startswith('#'): continue
			
			typ, rec = i.split(None, 1)
			
			m = re.compile('^' + rec.strip() + '$', re.IGNORECASE)
			if typ.lower() == "value": self.valuem_dnp.append(m)
			if typ.lower() == "refdes": self.refdesm_dnp.append(m)
		
	def query(self, refdes, value):
		if any([i.match(value.strip()) for i in self.valuem_dnp]): return True
		if any([i.match(refdes.strip()) for i in self.refdesm_dnp]): return True
		return False