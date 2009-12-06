openGLok = True

try:
    from OpenGL import GL
except:
	openGLok = False

import math

def point_project((x,y),r,a):
	return (x + math.cos(a) * r,y + math.sin(a) * r)
pp = point_project

def line2Polygon(line, facet_steps):
	ps = line.sx, line.sy
	pe = line.ex, line.ey

	slope =math.atan2(line.ey - line.sy, line.ex-line.sx)
	slope90CCW = slope + math.pi/2
	
	r = line.width/2
	
	
	for i in xrange(0,facet_steps+1):
		t = slope90CCW + math.pi/facet_steps * i
		yield pp(ps, r, t)
	
	
	for i in xrange(0,facet_steps+1):
		t = slope90CCW + math.pi/facet_steps * i + math.pi
		yield pp(pe, r, t)
	
# lines duck-type must conform to:
#    list of objects w/properties:
#			sx, sy, ex, ey (coords)
#           width
def linesLayerCreator(lines, rects):
	p = []
	for i in lines:
		p.append([j for j in line2Polygon(i,4)])
		
		
	for i in rects:
		p.append([i.ll, (i.ll[0], i.tr[1]), i.tr, (i.tr[0], i.ll[1])])
	
	return RenderLayer(p)
	
class RenderLayer:
	def __init__(self, polygon_list):
		self.polygon_list = polygon_list
		self.prepared = False
		
	def prepareDisplayLists(self):
	
		self.dl = GL.glGenLists(1)
		GL.glNewList(self.dl, GL.GL_COMPILE)
		for i in self.polygon_list:
			GL.glBegin(GL.GL_POLYGON)
			for x,y in i:
				GL.glVertex2f(x/1000.0,y/1000.0)
			GL.glEnd()
			
			GL.glBegin(GL.GL_LINE_LOOP)
			for x,y in i:
				GL.glVertex2f(x/1000.0,y/1000.0)
			GL.glEnd()
		GL.glEndList()
		
	def render(self):
		if not self.prepared:
			self.prepareDisplayLists()
			self.prepared = True
		GL.glCallList(self.dl)
