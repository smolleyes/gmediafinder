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
        self.local_engines_list = []
        for engine in os.listdir(constants.exec_path+'/lib/engines'):
            if os.path.isdir(os.path.join(constants.exec_path+'/lib/engines', engine)):
                self.local_engines_list.append(engine)
        # activated plugins list in the gmf config file
        self.load_plugins_conf()
        # create checkbtn of enabled plugins in the gui
        for engine in self.local_engines_list:
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
        setattr(self, '%s' % engine, init(self.gui))
        #try:
            #setattr(self, '%s' % engine, init(self.gui))
        #except:
            #return
                    
    def load_plugins_conf(self):
        try:
            for eng in self.gui.config["engines"]:
                self.engines_list.append(eng)
        except:
            ## add new engines key in the config file if not present
            ## disable YouPorn by default
            self.gui.config["engines"] = self.local_engines_list
            if ('YouPorn' in self.local_engines_list):
				self.gui.config["engines"].remove('YouPorn')
            self.gui.config.write()
            self.engines_list = self.local_engines_list
            
            
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
