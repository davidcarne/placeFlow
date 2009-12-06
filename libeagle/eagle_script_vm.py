import re
import eagle_script_preprocessor
from eagle_object_types import *


def ident_cmd(scanner, token): return "IDENT_CMD", token.strip()
def numeric(scanner, token): 
	if "." in token:
		return "NUMERIC", float(token.strip())
	else:
		return "NUMERIC", int(token.strip())
def end_stmnt(scanner, token): return "END_STATEMENT",
def quoted_str(scanner, token): return "QUOTED_STR", token.strip()[1:-1].replace("''","'")
def point(scanner, token): 
	# strip parens + whitespace inside parens
	x,y = token.strip()[1:-1].strip().split()
	return "POINT", float(x), float(y)

class ParseError(Exception):
	pass


class UnterminatedInstruction(Exception):
	pass
	
def lexEagleScript(instr):
	scanner = re.Scanner([
		(r"[+-]?[0-9]+(\.[0-9]+)?", numeric),
		(r"[a-zA-Z0-9+-][\w/\[\]+,.-]*", ident_cmd),
		(r"'(?:[^']|'')*'", quoted_str),
		(r";", end_stmnt),
		(r"\(\s*[+-]?[0-9]+(\.[0-9]+)?\s+[+-]?[0-9]+(\.[0-9]+)?\s*\)", point),
		(r"\s+", None),
		])
 
	tokens, remainder = scanner.scan(instr)
	
	if (remainder):
		raise ParseError("Error, unidentifiable token at %s... [%s]" % (remainder[:60], tokens[-10:]))
		
	return tokens

def zeroCopyIter(list, start, end):
	while start < end:
		yield list[start]
		start += 1
		
	
def iterStatements(statements):
	l = len(statements)
	i = 0
	while i < l:
		end = statements.index(("END_STATEMENT",), i)
		yield zeroCopyIter(statements, i, end)
		i = end+1
	
class EagleScriptFileRunner(object):
	def __init__(self, script_filename):
		script_text = eagle_script_preprocessor.preprocess(open(script_filename).read())
		tokens = lexEagleScript(script_text)
		def _():
			return i.next()
			
		for i in iterStatements(tokens):
			first_opcode, cmd = _()
			if first_opcode != 'IDENT_CMD':
				raise ParseError("Statement did not start with keyword");
			self.stmt_dispatch(cmd, i)


def parseRotation(s):
	if not 'R' in s:
		raise ParseError("Rotation %s does not start with R/MR" % s)
	s = s.replace("R","")
	mirror = False
	if s.startswith('M'):
		mirror = True
		s = s[1:]
	return float(s)

def isKeyWord(x): return x[0] == "IDENT_CMD"
def isQuotedString(x): return x[0] == "QUOTED_STR"
def isNumeric(x): return x[0] == "NUMERIC"
def isPoint(x): return x[0] == "POINT"
type_quotedstr = isQuotedString
type_numeric = isNumeric
type_point = isPoint
type_keyword = isKeyWord

def _GD(x,f,default):
	if f(x[0]):
		n = x[0]
		del x[0]
		if (len(n) > 2):
			return n[1:]
		return n[1]
		
	return default
	
def CMDparseCreateWires(ti):
	# One wire cmd can have multiple segments [sigh]
	x = [i for i in ti]
	segs = []
	name = _GD(x,type_quotedstr,'')
	width = _GD(x,type_numeric,0) * 1000
	while x:
		if isPoint(x[0]):
			a,b = x[0][1:]
			a *= 1000
			b *= 1000
			segs.append((a,b))
		del x[0]
	
	wires = []
	for i in xrange(len(segs)-1):
		p0 = segs[i]
		p1 = segs[i+1]
		wires.append(EagleWire(name, width, *(p0 + p1)))
	
	return wires

def CMDparseCreateRect(ti):
	ti.next() # Skip orientation
	
	a,b = ti.next()[1:]
	a *= 1000
	b *= 1000
	ll = a,b
	
	a,b = ti.next()[1:]
	a *= 1000
	b *= 1000
	tr = a,b
	return EagleRect(ll,tr)
		
def CMDparseCreateSMD(ti):
	x = [i for i in ti]
	
	name = x[0][1]; x=x[1:]
	xw = x[0][1] * 1000; x=x[1:]
	yw = x[0][1] * 1000; x=x[1:]
	roundness = -x[0][1]; x=x[1:]
	rotation = parseRotation(x[0][1]); x=x[1:]
	_GD(x,type_keyword,'')
	_GD(x,type_keyword,'')
	_GD(x,type_keyword,'')
	x,y = x[0][1:3]
	x *= 1000
	y *= 1000
	return EagleSMD(name,x,y,xw,yw,rotation,roundness)