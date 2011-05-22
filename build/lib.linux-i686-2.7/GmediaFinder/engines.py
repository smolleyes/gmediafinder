#!/usr/bin/env python

import os,sys
import gtk
from configobj import ConfigObj

## custom lib
try:
	import constants
except:
    from GmediaFinder import constants
    
class Engines(object):
	def __init__(self,gui):
		self.gui = gui
		self.engines_list = []
		self.load_engines()
	
	def load_engines(self):
		# local engines
		self.local_engines_list = os.listdir(constants.exec_path+'/lib/engines')
		# activated plugins list in the gmf config file
		self.load_plugins_conf()
		# create checkbuttons and activate it if the engine is in the config file...
		for engine in self.local_engines_list:
			if not os.path.isdir(os.path.join(constants.exec_path+'/lib/engines', engine)):
				continue
			checkbox = gtk.CheckButton(engine)
			checkbox.set_alignment(0, 0.5)
			self.gui.engines_box.pack_start(checkbox,False,False,5)
			checkbox.connect('toggled', self.change_engine_state)
			if any(x in engine for x in self.engines_list):
				checkbox.set_active(True)
				self.init_engine(engine)
			self.gui.engines_box.show_all()
		
	def init_engine(self,engine):
		modstr = "lib.engines.%s.%s" % (engine,engine)
		module = __import__(modstr, globals(), locals(), ['*'])
		init = getattr(module, '%s' % engine)
		try:
			setattr(self, '%s' % engine, init(self.gui))
		except:
			return
					
	def load_plugins_conf(self):
		try:
			self.engines_list = self.gui.config["engines"]
		except:
			## add new engines key in the config file if not present
			self.gui.config["engines"] = ""
			self.gui.config.write()
			
			
	def change_engine_state(self,widget):
		checked = widget.get_active()
		name = widget.child.get_text()
		if checked:
			if not any(x in name for x in self.engines_list):
				print "activating %s engine" % name
				self.engines_list.append(name)
				self.gui.config["engines"] = self.engines_list
				self.gui.config.write()
				self.init_engine(name)
				self.gui.engine_selector.append(name)
				self.gui.engine_selector.setIndexFromString(name)
		else:
			if any(x in name for x in self.engines_list):
				print "deactivating %s engine" % name
				self.engines_list.remove(name)
				self.gui.config["engines"] = self.engines_list
				self.gui.config.write()
				self.gui.engine_selector.setIndexFromString(name)
				self.gui.engine_selector.remove(self.gui.engine_selector.getSelectedIndex())
				self.gui.engine_selector.select(0)

