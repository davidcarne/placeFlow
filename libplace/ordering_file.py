import re


class OrderingFile(object):
	def __init__(self, filename):
		lines = open(filename).readlines()
		self.valuem_dnp = []
		self.refdesm_dnp = []
		self.packagem_dnp = []
		self.cache = {}
		self.wildcard = len(lines)+1
		
		for n,i in enumerate(lines):
			if not i.strip(): continue
			
			if i.startswith('#'): continue
			
			try:
				typ, rec = i.split(None, 1)
			except ValueError:
				typ = i
				rec = None
				
			if typ.strip() == "*":
				self.wildcard = n
				continue
				
			m = re.compile('^' + rec.strip() + '$', re.IGNORECASE)
			
			if typ.lower() == "value": self.valuem_dnp.append((m,n))
			if typ.lower() == "refdes": self.refdesm_dnp.append((m,n))
			if typ.lower() == "package": self.packagem_dnp.append((m,n))

	def query(self, *args):
		r = self.query_(*args)
		return r
		
	def query_(self, refdes, package, value):
		try:
			return self.cache[(refdes, package, value)]
		except KeyError:
			pass
		
		for i,n in self.refdesm_dnp:
			if i.match(refdes):
				self.cache[(refdes, package, value)] = n
				return n
		
		for i,n in self.packagem_dnp:
			if i.match(package):
				self.cache[(refdes, package, value)] = n
				return n
				
		for i,n in self.valuem_dnp:
			if i.match(value):
				self.cache[(refdes, package, value)] = n
				return n
		
		self.cache[(refdes, package, value)] = self.wildcard
		return self.wildcard