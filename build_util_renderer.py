
from PySide import QtGui, QtCore, QtOpenGL
from libGLrender.renderLayer import RenderLayer, linesLayerCreator
from build_util_model import *
import math
from itertools import chain
from OpenGL import GL

class RenderUnit(object):
	pass

class RenderModelAdaptor(object):
	def __init__(self, model):
		self.model = model
		self.layers = []
		self.shapes = {}
		
		for i in self.model.shapes.itervalues():
			if not i.wires and not i.rects: continue
			
			r = RenderUnit()
			r.ro = linesLayerCreator(i.wires, i.rects)
			r.name = i.name
			
			# Calculate max distance from center
			r.bb = max([j.sx for j in i.wires] + 
					   [j.sy for j in i.wires] + 
					   [j.ex for j in i.wires] + 
					   [j.ey for j in i.wires] + 
					   [j.ll[0] for j in i.rects] + 
					   [j.ll[1] for j in i.rects] + 
					   [j.tr[0] for j in i.rects] + 
					   [j.tr[1] for j in i.rects])/1000.0
					   
			self.shapes[i.name] = r
			
		coords = []
		for i in self.model.layers:
			l = RenderUnit()
			l.ro = RenderLayer(i.polys)
			for j in i.polys:
				coords.extend(j)
						
				for k in j:
					if k[0] >2000000000.0 or k[1]>2000000000.0:
						print i.name, i.bottom, k
				
			l.bottom = i.bottom
			l.name = i.name
			self.layers.append(l)
		

		cx = (max((i[0] for i in coords )) +  min((i[0] for i in coords )))/2
		cy = (max((i[1] for i in coords )) +  min((i[1] for i in coords )))/2
		self.c = -cx/1000.0, -cy/1000.0
		
		self.bbW = max((abs(i[0]-cx) for i in coords ))/1000.0
		self.bbH = max((abs(i[1]-cy) for i in coords ))/1000.0
		
	def getCurrentShapeBB(self):
		try:
			shape = self.shapes[self.model.current_group.package]
		except KeyError:
			return 10
		
		return shape.bb
		
	def draw(self, view):
		
		# Draw background layers
		for i in self.layers:
			if "Copper" in i.name:
				GL.glColor3f(0.3,0.3,0.3)

			if "Silkscreen" in i.name:
				GL.glColor3f(0.5,0.5,0.5)
				
			if i.bottom == self.model.current_group.bottom:
				i.ro.render()
		
		# Draw all parts
		for i in self.model.groups:
			# Only render the right side
			if i.bottom != self.model.current_group.bottom:
				continue
				
			# Render the current group later
			if i != self.model.current_group:
				# See if we can find a shape for the model
				try:
					shape = self.shapes[i.package]
				except KeyError:
					continue
				
				for j in i.placements:
					GL.glPushMatrix()
					GL.glTranslatef(j.x,j.y,0)
					GL.glRotatef(math.degrees(j.rot),0,0,1)
					if j.done:
						GL.glColor3f(0,0.7,0)
					else:	
						GL.glColor3f(0,0.0,0.7)
							
					shape.ro.render()
					GL.glPopMatrix()
					
		# Draw the current placement group
		try:
			shape = self.shapes[self.model.current_group.package]
		except KeyError:
			shape = None
		if shape:
			for i in self.model.current_group.placements:
				GL.glPushMatrix()
				GL.glTranslatef(i.x,i.y,0)
				GL.glRotatef(math.degrees(i.rot),0,0,1)
				if i.done:
					GL.glColor3f(0,1,0)
				elif self.model.current_group.current_placement == i:
					GL.glColor3f(1,1,0)
				# If render all, then draw in dim-red, else, draw blue
				elif view.mode == "ALL":	
					GL.glColor3f(1,0,0)
				else:
					GL.glColor3f(0,0,1)
					
					
						
				shape.ro.render()
				GL.glPopMatrix()
				
				
		if view.mode == "ALL":			
			# Draw the current-part crosshairs
			GL.glColor3f(1,1,0)
			GL.glBegin(GL.GL_LINES)
			x = self.model.current_group.current_placement.x
			y = self.model.current_group.current_placement.y
			GL.glVertex2f(-1000,y)
			GL.glVertex2f(x-1.5*self.getCurrentShapeBB(), y)
			GL.glVertex2f(x+1.5*self.getCurrentShapeBB(), y)
			GL.glVertex2f(1000,y)
			
			GL.glVertex2f(x,-1000)
			GL.glVertex2f(x, y-1.5*self.getCurrentShapeBB())
			GL.glVertex2f(x, y+1.5*self.getCurrentShapeBB())
			GL.glVertex2f(x,1000)
			GL.glEnd()
		
		
		
		
		
		
		

## Render Window
class GenericRenderView(QtOpenGL.QGLWidget):
	def __init__(self, model, parent=None, shareWidget=None):
		QtOpenGL.QGLWidget.__init__(self, parent, shareWidget)
		self.mode = "ALL"
		self.mw = parent
		self.model = model
		self.center = (-3,-3) # in mm
		
		self.scale = 0.04 # percentage/mm
		self.setMinimumSize(QtCore.QSize(100,100))
		self.resizeGL(self.width(), self.height())
		self.setMouseTracking(True)
		self.updateGL()
		
	def initializeGL(self):
		self.qglClearColor(QtGui.QColor(0,0,0))
		GL.glShadeModel(GL.GL_SMOOTH)

	def paintGL(self):
		GL.glClear(GL.GL_COLOR_BUFFER_BIT)
		GL.glLoadIdentity()

		GL.glScalef(self.scale, self.scale, self.scale)
		GL.glTranslatef(self.center[0], self.center[1], 0)

		self.model.draw(self)
	

	def pixelCoord2Board(self, (x,y)):
		x /= float(self.width())
		y /= float(self.height())
		
		# Convert into unscaled / untranslated projection coords
		x = x * self.vw - self.vw/2
		y = -y * self.vh + self.vh/2
		
		x /= self.scale
		y /= self.scale
		
		x -= self.center[0]
		y -= self.center[1]
		return x,y
		
	def boardCoord2Pixel(self, (x,y)):
		return x,y
		
		
	def resizeGL(self, width, height):
		if (width <1 or height < 1):
			return
			
		side = float(min(width, height))
		GL.glViewport(0, 0, width, height)
		
		self.vw = width / side
		self.vh = height / side
		GL.glMatrixMode(GL.GL_PROJECTION)
		GL.glLoadIdentity()
		GL.glOrtho(-self.vw/2, self.vw/2, -self.vh/2, self.vh/2, -1, 1)
		
		GL.glMatrixMode(GL.GL_MODELVIEW)

# Main window [interactive]
class PrimaryRenderView(GenericRenderView):
	def __init__(self, model, parent, share=None):
		GenericRenderView.__init__(self, model, parent, shareWidget=share)
		self.disableMove = False
		
	def mousePressEvent(self, event):
		self.md = self.pixelCoord2Board((event.x(), event.y()))
		
		
	def mouseMoveEvent(self, event):
		if self.disableMove: return
		if event.buttons() & QtCore.Qt.LeftButton:
			ox, oy = self.md
			nx, ny = self.pixelCoord2Board((event.x(), event.y()))
			
			cx,cy = self.center
			self.center = cx + nx - ox, cy + ny - oy
			self.updateGL()
		
		self.mw.renderMouseMoved(self.pixelCoord2Board((event.x(), event.y())))
		
	def wheelEvent(self, event):

		ox, oy = self.pixelCoord2Board((event.x(), event.y()))
			
		n = 1 if event.delta() > 0 else -1
		s  = 1.5 ** n
		self.scale = self.scale * s
		
		
		if self.disableMove: 
			self.updateGL()
			return
		
		# Recenter, eagle-style zooming
		nx, ny = self.pixelCoord2Board((event.x(), event.y()))
		cx,cy = self.center
		self.center = cx + nx - ox, cy + ny - oy
		self.updateGL()
			
		