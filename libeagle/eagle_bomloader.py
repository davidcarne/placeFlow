class EagleBOMLineItem:
	def __init__(self, refdes, value, device, package, description):
		self.refdes = refdes
		self.value = value
		self.device = device
		self.package = package
		self.description = description
		

class EagleBOMFile:
	def __init__(self, filename):
		f = open(filename)
		
		# Skip description and blank line
		l = f.readlines()[2:]
		
		# Not fixed width, nor delimited, so use header to determine column positions
		bom_header = l[0]
		value_start = bom_header.index("Value")
		device_start = bom_header.index("Device")
		package_start = bom_header.index("Package")
		description_start = bom_header.index("Description")
		
		# Parse the part lines
		self.parts={}
		bom_lines = l[1:]
		for i in bom_lines:
			refdes = i[:value_start].strip()
			value = i[value_start:device_start].strip()
			device = i[device_start:package_start].strip()
			package = i[package_start:description_start].strip()
			description = i[description_start:].strip()
			
			self.parts[refdes] = EagleBOMLineItem(refdes, value, device, package, description)
		
		# Generate a mapping of (package, value) to LineItem
		self.package_values = {}
		for i in self.parts.itervalues():
			key = (i.package, i.value)
			try:
				self.package_values[key].append(i)
			except KeyError:
				self.package_values[key] = [i]
			