#-*- coding: UTF-8 -*-
import gobject
import time
import os
import urllib
#regular expression
import re

PLUGIN_FREEBOXTV_LOCATION = "http://mafreebox.freebox.fr/freeboxtv/playlist.m3u"

try:
    from functions import *
except:
    from GmediaFinder.functions import *

class FreeboxTv(object):
    def __init__(self, gui):    
        self.gui = gui
        self.name="FreeboxTv"
        self.engine_type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.has_browser_mode = True
        self.search_url = None
        self.start_engine()
        self.order_label = _("Qualité: ")
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        self.order_list = { self.order_label:{ _("Standard"):"standard",
                                               _("HD"):"HD",
                                               _("Bas débit"):"bas débit",
                                             },
                                             
                          }
        self.orderby = create_comboBox(self.gui, self.order_list)
        
    def get_search_url(self,url,page):
        filehandle = urllib.urlopen(PLUGIN_FREEBOXTV_LOCATION)
        i = "o"
        d = {}
        while i <> "":
            if re.search ( '#EXTINF', i ):
                result = re.match('#EXTINF:0,([0-9]*) - (.*)',i)
                chan = "%05s" % result.group(1)
                # Get line with rtsp
                i = filehandle.readline()
                while not re.search('rtsp://', i):
                    i = filehandle.readline()
                d[chan + ' - ' + result.group(2)] = i[0:len(i)-1]
            i=filehandle.readline()
        return self.filter(d)
        
    def filter(self, playlist):       
        # recuperation des chaines dans le tableau lesFlux
        choice = self.orderby.getSelected()
        orderby = self.order_list[self.order_label][choice]
        keys = playlist.keys()
        keys.sort()
        for c_name in keys:
            if orderby in c_name:
                gobject.idle_add(self.gui.add_sound, c_name, playlist[c_name], None, None, self.name)               
        self.thread_stop=True
        
    def play(self,link):
        return self.gui.start_play(link)
        
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
        
