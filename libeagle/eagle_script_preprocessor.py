import re

def preprocess(instr):
	# Dos line endings to UNIX
	instr = instr.replace("\r\n","\n")
	# Random \rs to UNIX line ending [old MAC encoding]
	instr = instr.replace("\r", "\n")
	
	# Strip escaped end-of-lines
	instr = instr.replace("\\\n","")
	
	# Strip comments
	l = instr.split("\n")
	l = [i for i in l if not i.startswith("#")]
	instr = "".join(l)
	
	return instr
	