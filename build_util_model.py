import cPickle
from libeagle.eagle_centroidloader import EagleCentroidFile
from libeagle.eagle_library import EagleScriptLibraryFileImporter

from libeagle.eagle_bomloader import EagleBOMFile
from libplace.dnp_file import DNPFile
from libplace.ordering_file import OrderingFile
import gerberDRC as GD
import gerberDRC.util as GU
from libGLrender.renderLayer import point_project
import math

type_cache_map = {
			"BOM - Eagle" : "BOM",
			"Dimension" : "DIMENSION",
			"Centroid - Custom Eagle" : "CENTROID",
			"Shapes - Eagle LBR SCR" : "SHAPE",
			"TOP Silkscreen" : "BACKGROUND_POLY",
			"BOTTOM Silkscreen" : "BACKGROUND_POLY",
			"TOP Copper" : "BACKGROUND_POLY",
			"BOTTOM Copper" : "BACKGROUND_POLY",
			"Placement Order" : "PLACE_ORDER",
			"Do Not Populate list" : "DNP",
			}
			
valid_types = [
			"Unspecified", 
			"Dimension", 
			"TOP Silkscreen", 
			"BOTTOM Silkscreen", 
			"TOP Copper", 
			"BOTTOM Copper", 
			"Centroid - Custom Eagle",
			"BOM - Eagle",
			"Shapes - Eagle LBR SCR",
			"Placement Order",
			"Do Not Populate list"
			]
class ShapeFile(object):
	pass
	
class PolygonFile(object):
	def __init__(self, polys, bottom, visible, name):
		self.polys = polys
		self.bottom = bottom
		self.visible = visible
		self.name = name
		
class BuildProjectFile(object):
	def __init__(self, filename, filetype = None, cache = True, visible = False):
		self.__filename = filename
		self.__filetype = "Unspecified"
		self.__cache = cache
		self.visible = visible
		if not self.filetype:
			self.autodetect_filetype()
		
		self.file_object = None
		
	
	def setFilename(self, filename):
		self.__filename = filename
		self.file_object = None
		
	def getFilename(self):
		return self.__filename
	
	def setFiletype(self, filetype):
		self.__filetype = filetype
		self.file_object = None
		
	def getFiletype(self):
		return self.__filetype
	
	def setCache(self, cache):
		self.__cache = cache
		self.file_object = None
	
	def getCache(self):
		return self.__cache
	
	filename = property(getFilename, setFilename)
	filetype = property(getFiletype, setFiletype)
	cache = property(getCache, setCache)
	
	def __getstate__(self):
		x = {"_BuildProjectFile__filename" : self.__filename,
			 "_BuildProjectFile__filetype" : self.__filetype,
			 "_BuildProjectFile__cache"    : self.__cache,
			 "visible"  : self.visible}
			 
		if (self.cache): x["file_object"] = self.file_object
		else: x["file_object"] = None
		
		return x
		
	def autodetect_filetype(self):
		pass

	def parse_load(self):
		if (self.cache and self.file_object):
			return
			
		print "Parsing: %s" % self.filename
		
		if self.__filetype == "Centroid - Custom Eagle":
			self.file_object = EagleCentroidFile(self.filename)
		elif self.__filetype == "BOM - Eagle":
			self.file_object = EagleBOMFile(self.filename)
		elif self.__filetype == "Do Not Populate list":
			self.file_object = DNPFile(self.filename)
		elif self.__filetype == "Placement Order":
			self.file_object = OrderingFile(self.filename)
		elif self.__filetype == "Shapes - Eagle LBR SCR":
			scriptfile = EagleScriptLibraryFileImporter(self.filename)
			self.file_object = {}
			for name,val in scriptfile.subfiles.iteritems():
				if name.endswith("pac"):
					use_layers = [21,22,48,51,52]
					s = ShapeFile()
					s.name = val.name
					s.wires = []
					s.rects = []
					for li,lv in val.layers.iteritems():
						if li in use_layers:
							s.wires.extend(lv.wires)
							s.rects.extend(lv.rects)
					try:
						s.smds = val.layers[1].smds
					except KeyError:
						s.smds = None
					if not s.wires:
						print "Warning, %s contains no wires" % name
					self.file_object[val.name] = s
			
		elif "Silkscreen" in self.__filetype or "Copper" in self.__filetype:
			# Gerber loading is more complicated
			
			f = GD.parseFile(self.__filename)
			if (not f):
				print "Could not parse %s" % self.__filename
				return 
			
			p = GD.runRS274XProgram(f)
			if (not f):
				print "Could not create polygons for %s" % self.__filename
				return 
				
			polys = []
			for i in p.all:
				segs = i.getPolyData().segs
				s = []
				for j in xrange(len(segs)):
					a = segs[j]
					b = segs[(j+1)% len(segs)]
						
					slope = math.atan2(b.y - a.y, b.x-a.x)

					p = a.x, a.y
					
					pc = (a.x+b.x)/2.0, (b.y+a.y)/2
					r = math.sqrt((b.x-a.x)**2 + (b.y-a.y)**2) / 2
					
					s.append(p)
					if a.lt == GD.point_line.line_render_type_t.LR_ARC:
						for j in xrange(1,9):
							t = slope + math.pi/9.0 * j + math.pi
							s.append(point_project(pc, r, t))
					
					
				polys.append(s)
			self.file_object = PolygonFile(polys, "BOTTOM" in self.__filetype, self.visible, self.__filetype)





def readProject(filename):
	return cPickle.load(open(filename,"r"))
	
def writeProject(filename, project):
	cPickle.dump( project, open(filename,"w"), -1)


# Placements are (refdes, x, y, rot)
class BuildPlacement:
	def __init__(self, refdes, x, y, rot):
		self.x = x
		self.y = y
		self.rot = rot
		self.refdes = refdes
		self.done = False

# Groups are created by grouping (package, value, side), containing link to Shape
class BuildGroup:
	
	def __init__(self, value, package, bottom):
		self.value = value
		self.package = package
		self.bottom = bottom
		self.placements = []
		self.current_placement = None
		
	def totalUnplaced(self):
		return len( [i for i in self.placements if not i.done] )
	
	def morePlacements(self):
		return any(not i.done for i in self.placements[self.placements.index(self.current_placement)+1:])
	
	def done(self):
		return self.totalUnplaced() == 0
	
	def firstPlacement(self):
		for i in self.placements:
			if not i.done:
				self.current_placement = i
				break
				
	def nextPlacement(self):
		x = self.placements.index(self.current_placement) + 1
		x = self.placements[x:]
		for i in x:
			if not i.done:
				self.current_placement = i
				break
	
	def selectPlacement(self, placement):
		self.current_placement = placement
		
# Stores a list of BOM items, centroids for all refdes
# And shape for each component
# Also contains general polygon data for rendering board
# This class can be cached wholesale for multiple builds
# Save as a runtimeview file?
		
class BuildRuntime:
	def __init__(self, groups, layers, shapes):
		self.groups = [i for i in groups]
		self.current_group = groups[0]
		self.layers = layers
		self.shapes = shapes
		
	def selectGroup(self, group):
		self.current_group = group
		
	def nextPlacement(self, complete):
		self.current_group.current_placement.done = complete
		if (self.current_group.morePlacements()):
			self.current_group.nextPlacement()
			return
		
		
		# Find the next non-done group
		x = self.groups.index(self.current_group) + 1
		x = self.groups[x:]
		for i in x:
			if not i.done():
				self.current_group = i
				break
		self.current_group.firstPlacement()
				
		
	def moreGroups(self):
		return any(not i.done() for i in self.groups[self.groups.index(self.current_group)+1:])
	
	def morePlacementsGroups(self):
		return self.moreGroups() or self.current_group.morePlacements()
		
		
class BuildProject:
	def __init__(self):
		self.files = []
		
	def addFile(self, name):
		self.files.append(BuildProjectFile(name))
	
	def delFile(self, file):
		for n,i in enumerate(self.files):
			if i == file:
				del self.files[n]
				break
				
	# In preperation for a query run, preload
	# all files and create build table
	def loadFiles(self):
	
		
		for i in self.files:
			i.parse_load()
		
	
	def groupSort(self,a,b):
		if a.bottom != b.bottom:
			if a.bottom: return  1
			if b.bottom: return -1
		
		if (self.ordering):
			x = cmp(self.ordering.query(a.placements[0].refdes, a.package, a.value), 
						self.ordering.query(b.placements[0].refdes, b.package, b.value))
			if x: return x
			
		return cmp((a.package, a.value),(b.package, b.value))
		
		
		
	def genRuntimeModel(self):
		package_value_to_bomitem_map = {}
		refdes_to_centroid_map = {}
		
		refdes_DNP_list = []
		dnplist = None
		self.ordering = None
		layers = []
		shapes = {}
		# Build up global BOM list
		for i in self.files:
			if type_cache_map[i.filetype] == "BOM":
				for pkgval,bomitem_l in i.file_object.package_values.iteritems():
					try:
						ol = package_value_to_bomitem_map[pkgval]
					except KeyError:
						ol = []
					ol.extend(bomitem_l)
					package_value_to_bomitem_map[pkgval] = ol
					
					
			if type_cache_map[i.filetype] == "CENTROID":
				refdes_to_centroid_map.update(i.file_object.placements)
			
			if type_cache_map[i.filetype] == "DNP":
				dnplist = i.file_object
				
			if type_cache_map[i.filetype] == "PLACE_ORDER":
				self.ordering = i.file_object
				
			if type_cache_map[i.filetype] == "BACKGROUND_POLY":
				layers.append(i.file_object)
				
			if type_cache_map[i.filetype] == "SHAPE":
				shapes.update(i.file_object)
		
		# Build a list of all the build-group names
		groupKeys = set()
		for (pkg,value), bomitem_l in package_value_to_bomitem_map.iteritems():
			for j in bomitem_l:
				li = refdes_to_centroid_map[j.refdes]
				groupKeys.add( (pkg,value,li.on_bottom) )
		
		# Create those groups
		groups = {}
		for j in groupKeys:
			groups[j] = BuildGroup(j[1], j[0], j[2])
					
		# Fill placement groups	
		for (pkg,value), bomitem_l in package_value_to_bomitem_map.iteritems():
			for j in bomitem_l:
				li = refdes_to_centroid_map[j.refdes]
				if not dnplist or not dnplist.query(li.refdes, value):
					groups[(pkg,value,li.on_bottom)].placements.append(BuildPlacement(li.refdes, li.x, li.y, li.rotation))
				else:
					print "Excluding %s %s - %s, on DNP" % (pkg, value, li.refdes)
		errors = []
		
		# Only groups that have placements [DNP list filtering]
		groups = [i for i in groups.values() if i.placements]
		
		# Sort placement order
		groups.sort(self.groupSort)
			
		for i in groups:
			i.current_placement = i.placements[0]
		
		newshapes = {}
		for i in groups:
			try:
				newshapes[i.package] = shapes[i.package]
			except KeyError:
				print "No shape found for shape: %s" % i.package
				
		newshapes = shapes
		rtm = BuildRuntime(groups, layers, shapes)
		
		
		return rtm, errors