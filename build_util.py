#!/usr/bin/python

# drawtext.py

import optparse
import sys
from PySide import QtGui, QtCore, QtOpenGL
from libGLrender import renderLayer
from build_util_model import *
import math

from OpenGL import GL

from build_util_renderer import PrimaryRenderView, GenericRenderView, RenderModelAdaptor

### Group table view
class BuildGroupTableModelAdaptor(QtCore.QAbstractTableModel):
	def __init__(self, model, parent):
		QtCore.QAbstractTableModel.__init__(self, parent)
		self.model = model
		
	def data(self, index, role):
		if not index.isValid(): 
			return QtCore.QVariant()
			
		row = index.row()
		col = index.column()
		
		if (role == QtCore.Qt.BackgroundColorRole):
			unplace = self.model.groups[row].totalUnplaced()
			placed = len(self.model.groups[row].placements) - unplace
			
			if (placed == 0):
				return QtCore.QVariant(QtGui.QColor(0xFF,0x00,0x00))
			
			if (unplace == 0):
				return QtCore.QVariant(QtGui.QColor(0x00,0xFF,0x00))
				
			return QtCore.QVariant(QtGui.QColor(0xFF,0xFF,0x00))
				
		if (col == 0 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant(self.model.groups[row].value)
		
		if (col == 1 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant(self.model.groups[row].package)
			
		if (col == 2 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant(len(self.model.groups[row].placements))
			
		if (col == 3 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant("+" if self.model.groups[row].bottom else "")
		
		return QtCore.QVariant()	
		
		
	def headerData(self, index, orientation, role):
		headers = ["Value", "Package", "Count", "Side"]
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return QtCore.QVariant(headers[index])
			
		if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
			return QtCore.QVariant(str(index))	
			
		return QtCore.QVariant()
		
		
	def flags(self, index):
		if not index.isValid():
			return QtCore.Qt.ItemIsEnabled;
		
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
		
	def rowCount(self, parent):
		return len(self.model.groups)
		
	def columnCount(self, parent):
		return 4
	
	def setData(self, index, value, role):
		pass
		
		
		
		
### Group table view
class BuildPlacementTableModelAdaptor(QtCore.QAbstractTableModel):
	def __init__(self, model, parent):
		QtCore.QAbstractTableModel.__init__(self, parent)
		self.model = model
		
	def data(self, index, role):
		if not index.isValid(): 
			return QtCore.QVariant()
			
		row = index.row()
		col = index.column()
		placement = self.model.current_group.placements[row]
		
		if (role == QtCore.Qt.BackgroundColorRole):			
			if not placement.done:
				return QtCore.QVariant(QtGui.QColor(0xFF,0x00,0x00))
			
			return QtCore.QVariant(QtGui.QColor(0x00,0xFF,0x00))
		
		if (col == 0 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant(placement.refdes)
		
		if (col == 1 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant("%5.2f" % placement.x)
			
		if (col == 2 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant("%5.2f" % placement.y)
			
		if (col == 3 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant("%5.2f" % math.degrees(placement.rot))
		
		return QtCore.QVariant()	
		
		
	def headerData(self, index, orientation, role):
		headers = ["REFDES", "X", "Y", "R"]
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return QtCore.QVariant(headers[index])
			
		if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
			return QtCore.QVariant(str(index))	
			
		return QtCore.QVariant()
		
		
	def flags(self, index):
		if not index.isValid():
			return QtCore.Qt.ItemIsEnabled;
		
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
		
	def rowCount(self, parent):
		return len(self.model.current_group.placements)
		
	def columnCount(self, parent):
		return 4
	
	def setData(self, index, value, role):
		pass
		
				
## LHS Control Bar
class ControlBar(QtGui.QWidget):
	def __init__(self, model, parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.mw = parent
		self.model = model

		self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Ignored)
		layout = QtGui.QVBoxLayout()
		self.setLayout(layout)
		
		self.partTable = QtGui.QTableView()
		# Smaller text
		font = self.partTable.font()
		new_font = QtGui.QFont(font)
		new_font.setPointSize(int(0.8*new_font.pointSize()))
		self.partTable.setFont(new_font)

		self.__part_model_adaptor = BuildGroupTableModelAdaptor(model, self)
		
		# Set the table model
		self.partTable.setModel(self.__part_model_adaptor)
				
		# Configure table columns
		self.partTable.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
		self.partTable.setColumnWidth(1,90)
		self.partTable.setColumnWidth(2,40)
		self.partTable.setColumnWidth(3,40)
		
		# Configure selection behavior
		self.partTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.partTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.partTableSel = self.partTable.selectionModel()
		
		self.placeTable = QtGui.QTableView()
		
		
		self.__place_model_adaptor = BuildPlacementTableModelAdaptor(model, self)
		
		# Set the table model
		self.placeTable.setModel(self.__place_model_adaptor)
		self.placeTable.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
		self.placeTable.setColumnWidth(1,45)
		self.placeTable.setColumnWidth(2,45)
		self.placeTable.setColumnWidth(3,45)
		
		font = self.placeTable.font()
		new_font = QtGui.QFont(font)
		new_font.setPointSize(int(0.8*new_font.pointSize()))
		self.placeTable.setFont(new_font)
		self.placeTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.placeTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.placeTableSel = self.placeTable.selectionModel()

		
		
		
		self.pbNextPlace = QtGui.QPushButton("NEXT PLACEMENT\n[SPACE]");
		self.pbSkipPlacement = QtGui.QPushButton("SKIP PLACEMENT\n[TAB]");
		pbSkipGroup = QtGui.QPushButton("SKIP GROUP\n[ENTER]");
		font = pbSkipGroup.font()
		new_font = QtGui.QFont(font)
		new_font.setPointSize(2*new_font.pointSize())
		pbSkipGroup.setFont(new_font)
		self.pbNextPlace.setFont(new_font)
		self.pbSkipPlacement.setFont(new_font)
		layout.addWidget(self.partTable)
		layout.addWidget(self.placeTable)
		layout.addWidget(pbSkipGroup)
		layout.addWidget(self.pbNextPlace)
		layout.addWidget(self.pbSkipPlacement)
	
		self.connect(self.partTableSel, QtCore.SIGNAL("currentRowChanged(QModelIndex,QModelIndex)"), self.changePartSelection)
		self.connect(self.placeTableSel, QtCore.SIGNAL("currentRowChanged(QModelIndex,QModelIndex)"), self.changePlacementSelection)

		self.connect(self.pbNextPlace, QtCore.SIGNAL("clicked()"), self.nextPlacement)
		self.connect(self.pbSkipPlacement, QtCore.SIGNAL("clicked()"), self.skipPlacement)

		# Force update
		self.pushStateUpdate()
		
		
	def sizeHint(self):
			return QtCore.QSize(300, 10)
	
	def changePlacementSelection(self, current, previous):
		if not current.isValid():
			return
		self.model.current_group.selectPlacement(self.model.current_group.placements[current.row()])
		self.mw.updateRender()
		
	def changePartSelection(self, current, previous):
		if not current.isValid():
			return
		
		self.model.selectGroup(self.model.groups[current.row()])
		self.placeTableSel.select(QtCore.QModelIndex(), QtGui.QItemSelectionModel.Clear)

		self.__place_model_adaptor.reset()
		self.pushPlaceTableStateUpdate()
		self.mw.updateRender()
	
	def pushStateUpdate(self):
		self.pushPartTableStateUpdate()
		self.pushPlaceTableStateUpdate()
		self.mw.updateRender()

	def pushPartTableStateUpdate(self):
		partTableSelIndex = self.__part_model_adaptor.createIndex(self.model.groups.index(self.model.current_group), 0)
		self.partTableSel.select(partTableSelIndex, QtGui.QItemSelectionModel.ClearAndSelect | QtGui.QItemSelectionModel.Rows )
		self.partTable.scrollTo(partTableSelIndex)
		self.pbNextPlace.setEnabled(self.model.morePlacementsGroups())
		self.pbSkipPlacement.setEnabled(self.model.morePlacementsGroups())

	def pushPlaceTableStateUpdate(self):
		placeTableSelIndex = self.__place_model_adaptor.createIndex(
			self.model.current_group.placements.index(self.model.current_group.current_placement), 0)
			
		self.placeTableSel.select(placeTableSelIndex, QtGui.QItemSelectionModel.ClearAndSelect | QtGui.QItemSelectionModel.Rows )
		self.placeTable.scrollTo(placeTableSelIndex)
		self.pbNextPlace.setEnabled(self.model.morePlacementsGroups())
		self.pbSkipPlacement.setEnabled(self.model.morePlacementsGroups())

	def nextPlacement(self):
		lastGroup = self.model.current_group
		self.model.nextPlacement(True)
		if (self.model.current_group != lastGroup): self.__place_model_adaptor.reset()
		self.pushStateUpdate()
	
	def skipPlacement(self):
		lastGroup = self.model.current_group
		self.model.nextPlacement(False)
		if (self.model.current_group != lastGroup): self.__place_model_adaptor.reset()
		self.pushStateUpdate()	

class InfoPanel(QtGui.QWidget):
	def __init__(self, model, parent = None):
		QtGui.QWidget.__init__(self, parent)
		self.model = model
		vl = QtGui.QVBoxLayout()
		self.setLayout(vl)
		self.refdeslabel = QtGui.QLabel()
		self.packagelabel = QtGui.QLabel()
		self.valuelabel = QtGui.QLabel()
		
		f = self.valuelabel.font()
		nf = QtGui.QFont(f)
		nf.setPointSize(int(2*nf.pointSize()))
		self.refdeslabel.setFont(nf)
		self.packagelabel.setFont(nf)
		self.valuelabel.setFont(nf)		
		
		vl.addWidget(self.refdeslabel)
		vl.addWidget(self.packagelabel)
		vl.addWidget(self.valuelabel)
		vl.addStretch(10)
		
	def update(self):
		self.refdeslabel.setText( "REFDES: \t%s" %self.model.current_group.current_placement.refdes)
		self.packagelabel.setText("PACKAGE:\t%s" %self.model.current_group.package)
		self.valuelabel.setText(  "VALUE:  \t%s" %self.model.current_group.value)
		
class ViewWindow(QtGui.QWidget):
	def __init__(self, model, parent = None):
		QtGui.QWidget.__init__(self, parent)
		
		self.suppressupdates = True
		self.renderview = None
		self.model = model
		layout = QtGui.QHBoxLayout()
		
		self.setLayout(layout)
		layout.addWidget(ControlBar(model, self))
		vlayout = QtGui.QVBoxLayout()
		layout.addLayout(vlayout)
		
		# Two adaptors for two gui contexts
		self.rendermodel = RenderModelAdaptor(self.model)
		
		self.renderview = PrimaryRenderView( self.rendermodel, self)
		self.renderview.center = self.rendermodel.c
		self.renderview.scale = 0.45 / self.rendermodel.bbH

		self.renderview_zoomed = PrimaryRenderView( self.rendermodel, self, share=self.renderview)
		self.renderview_zoomed.disableMove = True
		self.renderview_zoomed.mode = "ZOOMED"
		
		self.infopanel = InfoPanel(model, self)
		self.splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
		self.hsplitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
		self.hsplitter.addWidget(self.infopanel)
		self.hsplitter.addWidget(self.renderview_zoomed)
		self.splitter.addWidget(self.hsplitter)
		self.splitter.addWidget(self.renderview)
		self.splitter.setSizes ([self.splitter.height()/4, self.splitter.height()*3/4])
		
		vlayout.addWidget(self.splitter)
		self.poslabel = QtGui.QLabel()
		self.poslabel.setFixedHeight(16)
		vlayout.addWidget(self.poslabel)
		
		self.suppressupdates = False
		self.updateRender()
		
	def sizeHint(self):
			return QtCore.QSize(1000, 600)

	def updateRender(self):
		if not self.suppressupdates:
			self.renderview.updateGL()
			self.renderview_zoomed.center = -self.model.current_group.current_placement.x,-self.model.current_group.current_placement.y
			self.renderview_zoomed.scale = min(0.35 / self.rendermodel.getCurrentShapeBB(), 0.20)
			self.renderview_zoomed.updateGL()
		
			self.infopanel.update()
		
	def renderMouseMoved(self, coords):
		self.poslabel.setText("Cursor Position: %6.3f %6.3f" % coords)
		
####################### Project #######################
### FileType cell editor
class FileTypeCellEditorFactory(QtGui.QItemEditorFactory):
	def createEditor(self, edtype, parent):
		cmb = QtGui.QComboBox(parent)
		for i in valid_types:
			cmb.addItem(i)
		return cmb

	def valuePropertyName(self, edtype):
		return "currentIndex"

### Model for the files table
class FileViewModelAdapter(QtCore.QAbstractTableModel):
	def __init__(self, model, parent):
		QtCore.QAbstractTableModel.__init__(self, parent)
		self.model = model
	
	def rowCount(self, parent):
		return len(self.model.files)
		
	def columnCount(self, parent):
		return 4
	
	def data(self, index, role):
		if not index.isValid(): 
			return QtCore.QVariant()
			
		row = index.row()
		col = index.column()
		
		# Filename column, display text
		if (col == 0 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant(self.model.files[row].filename)
		
		# Visible column
		if (col == 1 and role == QtCore.Qt.CheckStateRole):
			return QtCore.QVariant(QtCore.Qt.Checked if self.model.files[row].visible else QtCore.Qt.Unchecked)
		
		if (col == 2 and role == QtCore.Qt.CheckStateRole):
			return QtCore.QVariant(QtCore.Qt.Checked if self.model.files[row].cache else QtCore.Qt.Unchecked)

		if (col == 3 and role == QtCore.Qt.DisplayRole):
			return QtCore.QVariant(self.model.files[row].filetype)
		
		
		if (col == 3 and role == QtCore.Qt.EditRole):
			return QtCore.QVariant(valid_types.index(self.model.files[row].filetype))
	
		return QtCore.QVariant()

	# Callback to retrieve cell flags
	def flags(self, index):
		col = index.column()
		if not index.isValid():
			return QtCore.Qt.ItemIsEnabled;
		if col == 3:
			return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
			
		if col in [1,2]:
			return QtCore.Qt.ItemIsUserCheckable | \
				QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
			
		return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
	
	
	# Data setter - works on Visible, Cache and Type colums
	def setData(self, index, value, role):
		col = index.column()
		row = index.row()
		
		if (col == 1 and role == QtCore.Qt.CheckStateRole):
			self.model.files[row].visible = value.toBool()
			self.emit(QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)

		elif (col == 2 and role == QtCore.Qt.CheckStateRole):
			self.model.files[row].cache = value.toBool()
			self.emit(QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
		elif (col == 3 and role == QtCore.Qt.EditRole):
			self.model.files[row].filetype = valid_types[value.toInt()[0]]
			self.emit(QtCore.SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
		
	# Setup column headers
	def headerData(self, col, orientation, role):
		headers = ["Filename", "VIS", "SIP", "Type"]
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
			return QtCore.QVariant(headers[col])
		return QtCore.QVariant()
	
	# notify call for when changed
	def changed(self):
		self.reset()

# Main project window
class ProjectWindow(QtGui.QWidget):
	def __init__(self, parent = None, model = BuildProject(), projfile = None):
		QtGui.QWidget.__init__(self, parent)
		self.projfile = projfile
		self.model = model
		self.placementWindow = None
		
		pri_layout = QtGui.QHBoxLayout()
		self.setLayout(pri_layout)
		
		
		# Keep filetable around to force repaints
		self.__fileTable = QtGui.QTableView()
		
		# Save in a temporary variable to ensure adaptor is kept around
		# until window is gone
		self.__model_adaptor = FileViewModelAdapter(model, self)
		
		# Create a delegate for popup editors
		self.__ftype_delegate = QtGui.QItemDelegate()
		# Set a non-default factory to create the popup
		self.__ftype_factory = FileTypeCellEditorFactory()
		self.__ftype_delegate.setItemEditorFactory(self.__ftype_factory)
		self.__fileTable.setItemDelegateForColumn(3, self.__ftype_delegate)
		
		# Set the table model
		self.__fileTable.setModel(self.__model_adaptor)
		
		# Configure table columns
		self.__fileTable.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
		self.__fileTable.setColumnWidth(1,30)
		self.__fileTable.setColumnWidth(2,30)
		self.__fileTable.setColumnWidth(3,150)
		
		# Configure selection behavior
		self.__fileTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.__fileTable.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		
	
		# Button sidebar
		btnbar_layout = QtGui.QVBoxLayout()
		
		pbAddFile = QtGui.QPushButton("Add File")
		pbDelFile = QtGui.QPushButton("Delete File")
		pbSaveProject = QtGui.QPushButton("Save Project")
		pbGo = QtGui.QPushButton("Run Placement")
		btnbar_layout.addWidget(pbAddFile)
		btnbar_layout.addWidget(pbDelFile)
		btnbar_layout.addWidget(pbSaveProject)
		btnbar_layout.addWidget(pbGo)
		
		pri_layout.addWidget(self.__fileTable)
		pri_layout.addLayout(btnbar_layout)
		
		# Signals for button sidebar
		self.connect(pbAddFile, QtCore.SIGNAL("clicked()"), self.addFile)
		self.connect(pbDelFile, QtCore.SIGNAL("clicked()"), self.delFile)
		self.connect(pbSaveProject, QtCore.SIGNAL("clicked()"), self.saveProject)
		self.connect(pbGo, QtCore.SIGNAL("clicked()"), self.go)

	# Add File button handler
	def addFile(self):
		fileNames = QtGui.QFileDialog.getOpenFileNames()
		
		for i in xrange(fileNames.size()):
			self.model.addFile(str(fileNames[i]))
		self.__model_adaptor.changed()
	
	# Delete file button handler
	def delFile(self):
		selection = set([i.row() for i in self.__fileTable.selectedIndexes()])
		names = [self.model.files[i] for i in selection]
		for i in names:
			self.model.delFile(i)
		self.__model_adaptor.changed()
			
	# Save Project button handler
	def saveProject(self):
		self.model.loadFiles()
		
		if self.projfile: fileName = self.projfile
		else:
			sel = QtCore.QString("*.plproj")
			fileName = QtGui.QFileDialog.getSaveFileName(self, "", "", "*.plproj",sel)
			if not fileName: return
		writeProject(fileName, self.model)
	
	# Run placement button handler
	def go(self):
		if self.placementWindow:
			return

		self.model.loadFiles()
		rtm,errors = self.model.genRuntimeModel()
		
		if (errors):
			return
			
		self.placementWindow = ViewWindow(rtm)
		self.placementWindow.showMaximized()
		
	# Default window sizing
	def sizeHint(self):
		return QtCore.QSize(800, 400)
			

if not renderLayer.openGLok:
	app = QtGui.QApplication(sys.argv)
	QtGui.QMessageBox.critical(None, "Placement Utility",
                            "PyOpenGL must be installed to run this application.",
                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Default,
                            QtGui.QMessageBox.NoButton)
	sys.exit(1)

# Load application
app = QtGui.QApplication(sys.argv)

args = sys.argv
justrun = False
if "-justrun" in sys.argv: justrun = True

projfile = None
if len(sys.argv) != 1 and not sys.argv[-1].startswith('-'): projfile = sys.argv[-1]

if not projfile:
	project = BuildProject()
else:
	project = readProject(projfile)

if not justrun:
	projectWindow = ProjectWindow(None, project, projfile)
	projectWindow.show()
else:
	project.loadFiles()
	rtm,errors = project.genRuntimeModel()

	if (errors):
		print "".join(["%s\n" % i for i in errors])
		exit(1)
		
	placementWindow = ViewWindow(rtm)
	placementWindow.showMaximized()
	
	
	
app.exec_()