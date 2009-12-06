
# Agnostic whether parsed 

class EagleLayer(object):
	pass

class EagleRect(object):
	def __init__(self, ll, tr):
		self.ll = ll
		self.tr = tr
		
		
class EagleWire(object):
	def __init__(self, name, width, sx, sy, ex, ey):
		self.name = name
		self.width = width
		self.sx = sx
		self.sy = sy
		self.ex = ex
		self.ey = ey
	def __repr__(self):
		return "WIRE '%s' %f (%f, %f) (%f, %f)" % (
			self.name, self.width, self.sx, self.sy, self.ex, self.ey)
			
class EagleSMD(object):
	def __init__(self,name, x,y,xw,yw,rotation,roundness):
		self.name = name
		self.x = x
		self.y = y
		self.xw = xw
		self.yw = yw
		self.rotation = rotation
		self.roundness = roundness
		
	def __repr__(self):
		return "SMD '%s' (%6.2f, %6.2f) size (%5.3f, %5.3f) rot %f" % \
			(self.name, self.x, self.y, self.xw, self.yw, self.rotation)