from eagle_script_vm import *
from eagle_object_types import *

class EagleLayerInstance(object):
	pass
	
# Importer tool to create layers on demand
# and allow easy creation of objects within layers
class EagleLayerImporter(object):
	def __init__(self):
		self.layers = {}
		
	def stmt_dispatch(self, cmd, ti):
		if cmd == "layer":
			layernum = ti.next()[1]
			try:
				self.cur_layer = self.layers[layernum]
			except KeyError:
				self.cur_layer = self.layers[layernum] = EagleLayerInstance()
				self.layer_new()
		else:
			self.layer_stmt_dispatch(cmd, ti)
		
# Subfile types found in the library
class EagleSymSubfileImporter(object):
	def __init__(self, name):
		self.name = name
		
	def stmt_dispatch(self, cmd, ti):
		pass
		
		
class EaglePacSubfileImporter(EagleLayerImporter):
	def __init__(self, name):
		EagleLayerImporter.__init__(self)
		self.name = name
		
	def layer_new(self):
		self.cur_layer.smds = {}
		self.cur_layer.wires = []
		self.cur_layer.rects = []
		
	def layer_stmt_dispatch(self, cmd, ti):
		if cmd == "smd":
			smd = CMDparseCreateSMD(ti)
			self.cur_layer.smds[smd.name] = smd
		
		if cmd == "wire":
			wires = CMDparseCreateWires(ti)
			for wire in wires:
				self.cur_layer.wires.append(wire)
	
		if cmd == "rect":
			rect = CMDparseCreateRect(ti)
			self.cur_layer.rects.append(rect)
	
class EagleDevSubfileImporter(object):
	def __init__(self, name):
		self.name = name
		
	def stmt_dispatch(self, cmd, ti):
		pass


# Library Script importer
# Differentiation is maintained because I may write a schematic
# board exporter at some point in the future
class EagleScriptLibraryFileImporter(EagleScriptFileRunner):
	def __init__(self, script_filename):
		self.current_subfile = None;
		self.subfiles = {}
		self.layer_names = {}
		EagleScriptFileRunner.__init__(self, script_filename)
		
		
	def stmt_dispatch(self,cmd, token_iterator):
	
		cmd = cmd.lower()
		if cmd == 'edit':
			token_type,token = token_iterator.next()
			if (token_type != "QUOTED_STR"):
				raise ParseError("Edit expects quoted string")
			
			print token
			name, type = token.rsplit(".",1)
			if type == "pac":
				self.current_subfile = EaglePacSubfileImporter(name)
			elif type == "dev":
				self.current_subfile = EagleDevSubfileImporter(name)
			elif type == "sym":
				self.current_subfile = EagleSymSubfileImporter(name)
			else:
				raise ParseError("Edit had unknown subfile type: %s" % token)
			self.subfiles[token] = self.current_subfile
			
		elif self.current_subfile:
			self.current_subfile.stmt_dispatch(cmd, token_iterator)
		# Handle layer commands with no subfile, aka, in global library scope
		elif cmd == 'layer':
			_,lnum = token_iterator.next()
			_,lname = token_iterator.next()
			self.layer_names[lnum]=lname
