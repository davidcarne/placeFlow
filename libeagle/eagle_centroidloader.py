import math

# Centroid objects need to have properties for:
# Refdes
# X [mm]
# Y [mm]
# R [radians, CW]
# Side [top/bottom]
class Centroid_Eagle:
	def __init__(self, refdes, on_bottom, locx_um, locy_um, rotation_deg):
		self.__deg_rotation = float(rotation_deg)
		self.__locx_um = int(locx_um)
		self.__locy_um = int(locy_um)
		# Eagle unit seems to be 1/10 micron
		self.x = self.__locx_um/10000.0
		self.y = self.__locy_um/10000.0
		self.rotation = math.radians(self.__deg_rotation)
		self.on_bottom = bool(int(on_bottom))
		self.refdes = refdes

class EagleCentroidFile:
	def __init__(self, filename):
		f = open(filename)
		l = f.readlines()
		l = [i.split(",") for i in l if not i.startswith("#")]
		self.placements = {}
		for i in l:
			n = Centroid_Eagle(*i)
			self.placements[n.refdes] = n
		