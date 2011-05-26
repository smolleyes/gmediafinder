#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import sys
import os
import thread
import pango
import threading
import time
import gobject
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import urllib2
import urllib
import httplib
import socket
import pygst
pygst.require("0.10")
import gst
import re
import html5lib
import tempfile
import time
from html5lib import sanitizer, treebuilders, treewalkers, serializer, treewalkers
import traceback
from configobj import ConfigObj

from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup
import HTMLParser

## custom lib

from constants import *	
from engines import Engines
from functions import *

class GsongFinder(object):
    def __init__(self):
        ## default search options
        self.is_playing = False
        self.duration = None
        self.time_label = gtk.Label("00:00 / 00:00")
        self.media_name = ""
        self.media_link = ""
        self.nbresults = 100
        self.user_search = ""
        self.play_options = None
        self.fullscreen = False
        self.play_options = None
        self.mini_player = True
        self.timer = 0
        self.settings_folder = None
        self.conf_file = None
        self.seeker_move = None
        self.youtube_max_res = "320x240"
        self.active_downloads = 0
        self.thread_num = 0
        if sys.platform == "win32":
            from win32com.shell import shell, shellcon
            df = shell.SHGetDesktopFolder()
            pidl = df.ParseDisplayName(0, None,"::{450d8fba-ad25-11d0-98a8-0800361b1103}")[1]
            mydocs = shell.SHGetPathFromIDList(pidl)
            self.down_dir = os.path.join(mydocs,"gmediafinder-downloads")
            self.settings_folder = os.path.join(shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0),"gmediafinder")
        else:
            self.down_dir = os.path.join(os.getenv('HOME'),"gmediafinder-downloads")
            self.settings_folder = os.path.join(os.getenv('HOME'),".config/gmediafinder")

        ## conf file
        self.conf_file = os.path.join(self.settings_folder, 'gmediafinder_config')
        if not os.path.exists(self.settings_folder):
            os.mkdir(self.settings_folder)
            fd = os.open(self.conf_file, os.O_RDWR|os.O_CREAT)
            os.write(fd,"youtube_max_res=%s" % self.youtube_max_res)
            os.write(fd,"download_path=%s" % self.down_dir)
            os.close(fd)
        self.config = ConfigObj(self.conf_file,write_empty_values=True)
        try:
		    self.down_dir = self.config["download_path"]
        except:
			self.config["download_path"] = self.down_dir
			self.config.write()
        ## get default max_res for youtube videos
        try:
			self.youtube_max_res = self.config["youtube_max_res"]
        except:
			self.config["youtube_max_res"] = self.youtube_max_res
        self.engine_list = {}
        self.engine = None
        ## small config dir for downloads...
        if not os.path.exists(self.down_dir):
            os.mkdir(self.down_dir)
        ## Get Icons shown on buttons
        settings = gtk.settings_get_default()
        gtk.Settings.set_long_property(settings, "gtk-button-images", 1, "main")
        
        ## gui
        self.gladeGui = gtk.glade.XML(glade_file, None ,APP_NAME)
        self.window = self.gladeGui.get_widget("main_window")
        self.window.set_title("Gmediafinder")
        self.window.set_resizable(1)
        width = gtk.gdk.screen_width()
        height = gtk.gdk.screen_height()
        self.window.set_default_size((width - 250), (height - 100))
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.img_path = img_path
        self.window.set_icon_from_file(os.path.join(self.img_path,'gmediafinder.png'))
        self.window.connect('key-press-event', self.onKeyPress)
        ## informations
        self.top_infobox = self.gladeGui.get_widget("top_info")
        self.informations_label = self.gladeGui.get_widget("info_label")
        # options menu
        self.options_bar = self.gladeGui.get_widget("options_bar")
        self.search_box = self.gladeGui.get_widget("search_box")
        self.results_box = self.gladeGui.get_widget("results_box")
        ## notebook
        self.notebook = self.gladeGui.get_widget("notebook")
        
        ## youtube video quality choices
        self.res320 = self.gladeGui.get_widget("res1")
        self.res640 = self.gladeGui.get_widget("res2")
        self.res854 = self.gladeGui.get_widget("res3")
        self.res1280 = self.gladeGui.get_widget("res4")
        self.res1920 = self.gladeGui.get_widget("res5")
        
        # youtube search options
        self.youtube_options = self.gladeGui.get_widget("youtube_options")
        self.youtube_options.relevance_opt = self.gladeGui.get_widget("relevance_opt")
        self.youtube_options.recent_opt = self.gladeGui.get_widget("most_recent_opt")
        self.youtube_options.relevance_opt.set_active(True)
        self.youtube_options.viewed_opt = self.gladeGui.get_widget("most_viewed_opt")
        self.youtube_options.rating_opt = self.gladeGui.get_widget("rating_opt")
        ## video quality combobox
        youtube_quality_box = self.gladeGui.get_widget("youtube_quality_box")
        self.youtube_quality_model = gtk.ListStore(str)
        self.youtube_video_rate = gtk.ComboBox(self.youtube_quality_model)
        cell = gtk.CellRendererText()
        self.youtube_video_rate.pack_start(cell, True)
        self.youtube_video_rate.add_attribute(cell, 'text', 0)
        youtube_quality_box.add(self.youtube_video_rate)
        new_iter = self.youtube_quality_model.append()
        self.youtube_quality_model.set(new_iter,
                                0, _("Quality"),
                                )
        self.youtube_video_rate.connect('changed', self.on_youtube_video_rate_changed)
        
        ## control section
        self.play_btn = self.gladeGui.get_widget("play_btn")
        self.pause_btn = self.gladeGui.get_widget("pause_btn")
        self.volume_btn = self.gladeGui.get_widget("volume_btn")
        self.play_btn.connect('clicked', self.start_stop)
        self.down_btn = self.gladeGui.get_widget("down_btn")

        self.continue_checkbox = self.gladeGui.get_widget("continue_checkbox")
        self.continue_checkbox.set_active(1)
        self.play_options = "continue"
        self.loop_checkbox = self.gladeGui.get_widget("loop_checkbox")
        ## search bar
        self.search_entry = self.gladeGui.get_widget("search_entry")
        self.search_btn = self.gladeGui.get_widget("search_btn")
        self.changepage_btn = self.gladeGui.get_widget("changepage_btn")

        ## statbar
        self.statbar = self.gladeGui.get_widget("statusbar")
        
        ## downloads
        self.down_box = self.gladeGui.get_widget("down_box")
        self.down_container = gtk.VBox(False, 5)
        self.down_scroll = gtk.ScrolledWindow()
        self.down_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.down_scroll.add_with_viewport(self.down_container)
        self.down_box.add(self.down_scroll)
        self.active_down_label = self.gladeGui.get_widget("active_down_label")
        self.path_btn = self.gladeGui.get_widget("select_path_btn")
        self.path_btn.set_current_folder(self.down_dir)
        self.path_btn.connect('current-folder-changed',self.update_down_path)
         
        # video drawing
        self.video_box = self.gladeGui.get_widget("video_box")
        self.movie_window = self.gladeGui.get_widget("drawingarea")
        self.movie_window.set_flags(gtk.CAN_FOCUS)
        self.movie_window.unset_flags(gtk.DOUBLE_BUFFERED)
        self.movie_window.connect('realize', self.on_drawingarea_realized)
        self.window.connect('motion-notify-event', self.on_motion_notify)
        self.movie_window.connect('configure-event', self.on_configure_event)
        self.movie_window.connect('expose-event', self.on_expose_event)
        self.movie_window.connect('button-press-event', self.on_drawingarea_clicked)
        self.movie_window.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.pic_box = self.gladeGui.get_widget("picture_box")
        
        # seekbar and signals
        self.control_box = self.gladeGui.get_widget("control_box")
        self.seekbox = self.gladeGui.get_widget("seekbox")
        self.adjustment = gtk.Adjustment(0.0, 0.00, 100.0, 0.1, 1.0, 1.0)
        self.seeker = gtk.HScale(self.adjustment)
        self.seeker.set_draw_value(False)
        self.seeker.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        self.seekbox.add(self.seeker)
        self.seeker.connect("button-release-event", self.seeker_button_release_event)
        self.seeker.connect("button-press-event", self.seeker_block)
        #timer
        self.timerbox = self.gladeGui.get_widget("timer_box")
        self.timerbox.add(self.time_label)
        
        ## youtube client
        self.youtube = YouTubeClient()
        
        ## visualisations
        self.vis_selector = self.gladeGui.get_widget("vis_chooser")
        
        
        ## SIGNALS
        dic = {"on_main_window_destroy_event" : self.exit,
        "on_song_radio_toggled" : self.option_changed,
        "on_video_radio_toggled" :  self.option_changed,
        "on_img_radio_toggled" :  self.option_changed,
        "on_search_btn_clicked" : self.prepare_search,
        "on_engine_selector_changed" : self.set_engine,
        "on_quit_menu_activate" : self.exit,
        "on_pause_btn_clicked" : self.pause_resume,
        "on_down_btn_clicked" : self.download_file,
        "on_changepage_btn_clicked" : self.change_page,
        "on_search_entry_activate" : self.prepare_search,
        "on_continue_checkbox_toggled" : self.set_play_options,
        "on_loop_checkbox_toggled" : self.set_play_options,
        "on_vol_btn_value_changed" : self.on_volume_changed,
        "on_vis_chooser_changed" : self.change_visualisation,
        "on_about_menu_clicked" : self.on_about_btn_pressed,
        "on_settings_menu_clicked" : self.on_settings_btn_pressed,
        "on_down_menu_btn_clicked" : self.show_downloads,
        "on_home_menu_btn_clicked" : self.show_home,
        "on_select_path_btn_file_set" : self.update_down_path,
        "on_res1_toggled" : self.set_max_youtube_res,
        "on_res2_toggled" : self.set_max_youtube_res,
        "on_res3_toggled" : self.set_max_youtube_res,
        "on_res4_toggled" : self.set_max_youtube_res,
        "on_res5_toggled" : self.set_max_youtube_res,
         }
        self.gladeGui.signal_autoconnect(dic)
        self.window.connect('destroy', self.exit)

        ## finally setup the list
        self.model = gtk.ListStore(gtk.gdk.Pixbuf,str,object,object)
        self.treeview = gtk.TreeView()
        self.treeview.set_model(self.model)
        
        rendererp = gtk.CellRendererPixbuf()
        pixcolumn = gtk.TreeViewColumn("",rendererp,  pixbuf=0)
        self.treeview.append_column(pixcolumn)

        rendertxt = gtk.CellRendererText()
        txtcolumn = gtk.TreeViewColumn("txt",rendertxt, text=1)
        txtcolumn.set_title(_(' Results : '))
        self.treeview.append_column(txtcolumn)
        
        renderer = gtk.CellRendererText()
        pathColumn = gtk.TreeViewColumn("Link", renderer)
        self.treeview.append_column(pathColumn)
        
        qualityColumn = gtk.TreeViewColumn("Quality", renderer)
        self.treeview.append_column(qualityColumn)
        
        ## setup the scrollview
        self.results_scroll = self.gladeGui.get_widget("results_scrollbox")
        self.columns = self.treeview.get_columns()
        self.columns[1].set_sort_column_id(1)
        self.columns[2].set_visible(0)
        self.columns[3].set_visible(0)
        self.results_scroll.add(self.treeview)
        self.results_scroll.connect_after('size-allocate', self.resize_wrap, self.treeview, self.columns[1], rendertxt)
        ## connect treeview signals
        self.treeview.connect('cursor-changed',self.get_model)

        ## create the players
        self.player = gst.element_factory_make("playbin", "player")
        audiosink = gst.element_factory_make("autoaudiosink")
        self.vis = self.change_visualisation()
        if sys.platform == "win32":
            self.sink = gst.element_factory_make('d3dvideosink')
        else:
            self.sink = gst.element_factory_make('xvimagesink')
            if self.engine == "Youtube":
                self.sink.set_property('force-aspect-ratio', True)
        self.player.set_property("audio-sink", audiosink)
        self.player.set_property('video-sink', self.sink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)
        
        ## engines
        self.dlg = self.gladeGui.get_widget("settings_dialog")
        self.engines_box = self.gladeGui.get_widget("engines_box")

        ## time
        self.timeFormat = gst.Format(gst.FORMAT_TIME)

        ## start gui
        self.window.show_all()
        self.changepage_btn.hide()
        self.youtube_options.hide()
        self.youtube_video_rate.hide()
        self.youtube_video_rate.set_active(0)
        
        ## start engines
        combo = self.gladeGui.get_widget("engine_selector")
        self.engine_selector = ComboBox(combo)
        self.yt_client = yt_service.YouTubeService()
        self.engines_client = Engines(self)
        
        ## engine selector (engines only with direct links)
        for engine in self.engine_list:
            self.engine_selector.append(engine)
        self.engine_selector.select(0)
        
        ## start main loop
        gobject.threads_init()
        #gtk.gdk.threads_init()
        self.mainloop = gobject.MainLoop(is_running=True)
        self.mainloop.run()
        
        
    def resize_wrap(self, scroll, allocation, treeview, column, cell):
        otherColumns = (c for c in treeview.get_columns() if c != column)
        newWidth = allocation.width - sum(c.get_width() for c in otherColumns)
        newWidth -= treeview.style_get_property("horizontal-separator") * 4
        if cell.props.wrap_width == newWidth or newWidth <= 0:
                return
        if newWidth < 250:
                newWidth = 225
        cell.props.wrap_width = newWidth
        column.set_property('min-width', newWidth + 10)
        column.set_property('max-width', newWidth + 10)
        store = treeview.get_model()
        iter = store.get_iter_first()
        while iter and store.iter_is_valid(iter):
                store.row_changed(store.get_path(iter), iter)
                iter = store.iter_next(iter)
                treeview.set_size_request(0,-1)
        
    def change_visualisation(self, widget=None):
        vis = self.vis_selector.get_active_text()
        if vis == "":
            self.vis_selector.set_active(0)
            self.vis = "libvisual_jess"
        elif vis != "goom":
            self.vis = "libvisual_"+vis
        else:
            self.vis = vis
        return self.vis
        
    def update_down_path(self,widget=None):
		self.config["download_path"] = widget.get_current_folder()
		self.config.write()
		self.down_dir = widget.get_current_folder()

    def set_engine(self,widget=None):
        self.youtube_options.hide()
        self.youtube_video_rate.hide()
        self.engine = self.engine_selector.getSelected()
        self.changepage_btn.hide()
        iter = self.engine_selector.getSelectedIndex()
        if self.engine_selector.getSelected() == 0:
            self.engine = None
            return
        print _("%s engine selected") % self.engine
        if self.engine == "Youtube":
            self.youtube_options.show()
            self.youtube_video_rate.show()
            self.youtube_options.relevance_opt.set_active(1)

            
    def show_downloads(self, widget):
		self.notebook.set_current_page(1)
	
    def show_home(self, widget):
		self.notebook.set_current_page(0)
	
    def get_model(self,widget):
        selected = self.treeview.get_selection()
        self.iter = selected.get_selected()[1]
        self.path = self.model.get_path(self.iter)
        ## else extract needed metacity's infos
        self.media_name = self.model.get_value(self.iter, 1)
        ## return only theme name and description then extract infos from hash
        self.media_link = self.model.get_value(self.iter, 2)
        self.media_img = self.model.get_value(self.iter, 0)
        # print in the gui
        self.statbar.push(1,_("Playing : %s") % self.media_name)
        self.stop_play()
        ## check youtube quality
        if self.engine == "Youtube":
			self.load_youtube_res()
        else:
			self.start_play(self.media_link)

    def idle_add_lock(self, func, *args):
       return gobject.idle_add(with_lock, func, args)
       
    def timeout_add_lock(millisecs, func, *args):
       return gobject.timeout_add(millisecs, with_lock, func, args)
        
    def load_youtube_res(self,args=None):
		self.youtube_quality_model.clear()
		self.media_link,self.quality_list = self.get_quality_list(self.media_link)
		if not self.quality_list:
			return
		for rate in self.quality_list:
			new_iter = self.youtube_quality_model.append()
			self.youtube_quality_model.set(new_iter,
							0, rate,
							)
		self.set_default_youtube_video_rate()
		
    def set_default_youtube_video_rate(self,widget=None):
		active = self.youtube_video_rate.get_active()
		qn = 0
		## if there s only one quality available, read it...
		if active == -1:
			if len(self.quality_list) == 1:
				self.youtube_video_rate.set_active(0)
			for frate in self.quality_list:
				rate = frate.split('|')[0]
				h = int(rate.split('x')[0])
				dh = int(self.youtube_max_res.split('x')[0])
				if h > dh:
					qn+=1
					continue
				else:
					self.youtube_video_rate.set_active(qn)
			active = self.youtube_video_rate.get_active()
		else:
			if self.quality_list:
				active = self.youtube_video_rate.get_active()

    def on_youtube_video_rate_changed(self,widget):
		active = self.youtube_video_rate.get_active()
		if self.media_link:
			self.stop_play()
			try:
			    self.media_codec = self.quality_list[active].split('|')[1]
			except:
				pass
			self.start_play(self.media_link[active])

    def option_changed(self,widget):
        self.search_option = widget.name
        
    def get_quality_list(self,vid_id):
        links_arr = []
        quality_arr = []
        try:
			req = urllib2.Request("http://youtube.com/watch?v=" + urllib2.quote('%s' % vid_id))
			stream = urllib2.urlopen(req)
			contents = stream.read()
			## links list
			regexp1 = re.compile("fmt_stream_map=([^&]+)&")
			matches = regexp1.search(contents).group(1)
			fmt_arr = urllib2.unquote(matches).split(',')
			## quality_list
			regexp1 = re.compile("fmt_map=([^&]+)&")
			matches = regexp1.search(contents).group(1)
			quality_list = urllib2.unquote(matches).split(',')
			##
			stream.close()
			link_list = []
			for link in fmt_arr:
				res = link.split('|')[1]
				link_list.append(res)
			## remove flv links...
			i = 0
			for quality in quality_list:
				codec = get_codec(quality)
				if codec == "flv" and quality.split("/")[1] == "320x240" and re.search("18/320x240",str(quality_list)):
					i+=1
					continue
				elif codec == "flv" and quality.split("/")[1] != "320x240":
					i+=1
					continue
				else:
					links_arr.append(link_list[i])
					quality_arr.append(quality.split("/")[1] + "|%s" % codec)
					i+=1
        except:
		    print "removed %s" % vid_id
		    return
        return links_arr, quality_arr

    def prepare_search(self,widget=None):
        self.user_search = self.search_entry.get_text()
        self.main_engine = self.engine_selector.getSelectedIndex()
        if self.main_engine == 0:
			self.informations_label.set_text(_("Please select a search engine..."))
			self.search_btn.set_sensitive(1)
			return
        if not self.user_search:
            self.informations_label.set_text(_("Please enter an artist/album or song name..."))
            return
        if not self.engine:
            self.informations_label.set_text(_("Please select an engine..."))
            return
			
        return self.idle_add_lock(self.search,())

    def change_page(self,widget=None):
        user_search = self.search_entry.get_text()
        engine = self.engine_selector.getSelectedIndex()
        if not user_search or user_search != self.user_search \
        or not engine or engine != self.main_engine:
            return self.prepare_search()
        else:
            return self.idle_add_lock(self.search,(self.search_engine.current_page))

    def search(self,page=None):
		self.informations_label.set_text(_("Searching for %s with %s ") % (self.user_search,self.engine))
		self.model.clear()
		self.search_btn.set_sensitive(0)
		self.changepage_btn.set_sensitive(0)
		self.informations_label.set_text(_("Searching for %s with %s ") % (self.user_search,self.engine))
		self.search_engine = getattr(self.engines_client,'%s' % self.engine)
		## send request to the module, can pass type and order too...reset page start to inital state
		if not page:
			page = self.search_engine.main_start_page
			self.search_engine.current_page = self.search_engine.main_start_page
		thread.start_new_thread(self.search_engine.search,(self.user_search,page))


    def add_sound(self, name, media_link, img=None, quality_list=None):
        if not img:
            img = gtk.gdk.pixbuf_new_from_file_at_scale(os.path.join(self.img_path,'sound.png'), 64,64, 1)
        if not name or not media_link or not img:
            return
        self.iter = self.model.append()
        self.model.set(self.iter,
                        0, img,
                        1, name,
                        2, media_link,
                        3, quality_list,
                        )

    def start_stop(self,widget=None):
        url = self.media_link
        if url:
            if self.play_btn.get_label() == "gtk-media-play":
                self.statbar.push(1,_("Playing : %s") % self.media_name)
                return self.start_play(url)
            else:
                self.statbar.push(1,_("Stopped"))
                return self.stop_play(url)

    def start_play(self,url):
        self.active_link = url
        if not sys.platform == "win32":
            self.vis = self.change_visualisation()
            self.visual = gst.element_factory_make(self.vis,'visual')
            self.player.set_property('vis-plugin', self.visual)
        self.play_btn.set_label("gtk-media-stop")
        self.pause_btn.set_label("gtk-media-pause")
        self.player.set_property("uri", url)
        self.player.set_state(gst.STATE_PLAYING)
        self.play_thread_id = thread.start_new_thread(self.play_thread, ())
        self.is_playing = True

    def stop_play(self,widget=None):
        self.player.set_state(gst.STATE_NULL)
        self.play_btn.set_label("gtk-media-play")
        self.is_playing = False
        self.play_thread_id = None
        self.duration = None
        self.update_time_label()
        self.active_link = None

    def play_thread(self):
        play_thread_id = self.play_thread_id

        while play_thread_id == self.play_thread_id:
            if play_thread_id == self.play_thread_id:
                gtk.gdk.threads_enter()
                if not self.seeker_move:
                    self.update_time_label()
                gtk.gdk.threads_leave()
            time.sleep(1)

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.play_thread_id = None
            self.player.set_state(gst.STATE_NULL)
            self.play_btn.set_label("gtk-media-play")
            self.check_play_options()
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.play_thread_id = None
            self.player.set_state(gst.STATE_NULL)
            self.play_btn.set_label("gtk-media-play")
            ## continue if continue option selected...
            if self.play_options == "continue":
                self.check_play_options()

    def pause_resume(self,widget):
        if not self.is_playing:
			return
        if self.pause_btn.get_label() == "gtk-media-pause":
            self.pause_btn.set_label("gtk-media-play")
            self.player.set_state(gst.STATE_PAUSED)
        else:
            self.pause_btn.set_label("gtk-media-pause")
            self.player.set_state(gst.STATE_PLAYING)

    def set_play_options(self,widget):
        wname = widget.name
        wstate = widget.get_active()
        if wname == "continue_checkbox":
            if wstate:
                self.play_options = "continue"
                if self.loop_checkbox.get_active():
                    self.loop_checkbox.set_active(0)
        elif wname == "loop_checkbox":
            if wstate:
                self.play_options = "loop"
                if self.continue_checkbox.get_active():
                    self.continue_checkbox.set_active(0)

    def check_play_options(self):
        if self.play_options == "loop":
            path = self.model.get_path(self.iter)
            if path:
                self.treeview.set_cursor(path)
        elif self.play_options == "continue":
            iter = None
            ## first, check if iter is still available (changed search while
            ## continue mode for exemple..)
            if not self.model.get_path(self.iter) == self.path:
                try:
                    iter = self.model.get_iter_first()
                except:
                    return
                if iter:
                    path = self.model.get_path(iter)
                    self.treeview.set_cursor(path)
                return
            ## check for next iter
            try:
                iter = self.model.iter_next(self.iter)
            except:
                return
            if iter:
                path = self.model.get_path(iter)
                self.treeview.set_cursor(path)
            else:
                if not self.engine == "google.com":
                    ## try changing page
                    self.change_page()
                    ## wait for 10 seconds or exit
                    i = 0
                    while i < 10:
                        try:
                            iter = self.model.get_iter_first()
                        except:
                            continue
                        if iter:
                            path = self.model.get_path(iter)
                            self.treeview.set_cursor(path)
                            break
                        else:
                            i += 1
                            time.sleep(1)
    
    def convert_ns(self, t):
        # This method was submitted by Sam Mason.
        # It's much shorter than the original one.
        s,ns = divmod(t, 1000000000)
        m,s = divmod(s, 60)
        if m < 60:
            return "%02i:%02i" %(m,s)
        else:
            h,m = divmod(m, 60)
            return "%i:%02i:%02i" %(h,m,s)

    def seeker_button_release_event(self, widget, event):
        self.seeker_move = None 
        value = widget.get_value()
        if self.is_playing == True:
            duration = self.player.query_duration(self.timeFormat, None)[0] 
            time = value * (duration / 100)
            self.player.seek_simple(self.timeFormat, gst.SEEK_FLAG_FLUSH, time)

    def seeker_block(self,widget,event):
		self.seeker_move = 1
    
    def update_time_label(self): 
        """
        Update the time_label to display the current location
        in the media file as well as update the seek bar
        """ 
        if self.is_playing == False:
          adjustment = gtk.Adjustment(0, 0.00, 100.0, 0.1, 1.0, 1.0)
          self.seeker.set_adjustment(adjustment)
          self.time_label.set_text("00:00 / 00:00")
          return False
        
        ## update timer for mini_player and hide it if more than 5 sec 
        ## without mouse movements
        self.timer += 1
        if self.fullscreen == True and self.mini_player == True and self.timer > 5 :
            self.show_mini_player()
        
        if self.duration == None:
          try:
            self.length = self.player.query_duration(self.timeFormat, None)[0]
            self.duration = self.convert_ns(self.length)
          except gst.QueryError:
            self.duration = None
          
        if self.duration != None:
            try:
                self.current_position = self.player.query_position(self.timeFormat, None)[0]
            except gst.QueryError:
                return 0
            current_position_formated = self.convert_ns(self.current_position)
            self.time_label.set_text(current_position_formated + "/" + self.duration)
      
            # Update the seek bar
            # gtk.Adjustment(value=0, lower=0, upper=0, step_incr=0, page_incr=0, page_size=0)
            percent = (float(self.current_position)/float(self.length))*100.0
            adjustment = gtk.Adjustment(percent, 0.00, 100.0, 0.1, 1.0, 1.0)
            self.seeker.set_adjustment(adjustment)
      
        return True
    

    def on_sync_message(self, bus, message):
        if message.structure is None:
            return
        win_id = None
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            if sys.platform == "win32":
                win_id = self.movie_window.window.handle
            else:
                win_id = self.movie_window.window.xid
            gtk.gdk.threads_enter()
            self.sink.set_xwindow_id(win_id)
            gtk.gdk.threads_leave()
            
    def on_drawingarea_clicked(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            return self.set_fullscreen()
    
    def set_fullscreen(self,widget=None):
        if self.fullscreen :
            self.fullscreen = False
            self.top_infobox.show()
            self.search_box.show()
            self.results_box.show()
            self.statbar.show()
            self.control_box.show()
            self.options_bar.show()
            self.window.window.unfullscreen()
            self.window.set_position(gtk.WIN_POS_CENTER)
        else:
            self.top_infobox.hide()
            self.search_box.hide()
            self.results_box.hide()
            self.options_bar.hide()
            self.window.window.fullscreen()
            self.fullscreen = True
            self.mini_player = True
                
    def on_drawingarea_realized(self, sender):
        if sys.platform == "win32":
            window = self.movie_window.get_window()
            window.ensure_native()
            gtk.gdk.threads_enter()
            self.sink.set_xwindow_id(self.movie_window.window.handle)
            gtk.gdk.threads_leave()
        else:
			gtk.gdk.threads_enter()
			self.sink.set_xwindow_id(self.movie_window.window.xid)
			gtk.gdk.threads_leave()
            
    def on_expose_event(self, widget, event):
        x , y, width, height = event.area
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                                      pixmap, x, y, x, y, width, height)
        return False
        
    def on_configure_event(self, widget, event):
          global pixmap
   
          x, y, width, height = widget.get_allocation()
          pixmap = gtk.gdk.Pixmap(widget.window, width, height)
          pixmap.draw_rectangle(widget.get_style().black_gc,
                                True, 0, 0, width, height)
   
          return True
        
    def on_motion_notify(self, widget, event):
        h=gtk.gdk.screen_height()
        self.timer = 0
        if self.fullscreen and event.y >= h - 10:
            self.show_mini_player()
            time.sleep(0.5)
            
    def show_mini_player(self):
        if self.mini_player == True:
            self.statbar.hide()
            self.control_box.hide()
            self.options_bar.hide()
            self.mini_player = False
        else:
            self.statbar.show()
            self.control_box.show()
            self.mini_player = True
    
    def onKeyPress(self, widget, event):
        key = gtk.gdk.keyval_name(event.keyval)
        if key == 'F2':
            return self.set_fullscreen()

        # If user press Esc button in fullscreen mode
        if event.keyval == gtk.keysyms.Escape and self.fullscreen:
            return self.set_fullscreen()
    
    def on_volume_changed(self, widget, value=10):
        self.player.set_property("volume", float(value)) 
        return True
    
    def set_max_youtube_res(self, widget):
		if widget.get_active():
			print "here"
			self.youtube_max_res = widget.get_child().get_label()
			self.config["youtube_max_res"]=self.youtube_max_res
			## return a dic as conf
			try:
				self.config.write()
			except:
				print "Can't write to the %s config file..." % self.conf_file
		

    def download_file(self,widget):
        if self.engine == "Youtube":
			return self.geturl(self.active_link, self.media_codec)
        return self.geturl(self.active_link)

    def geturl(self, url, codec=None):
        if self.engine == "Youtube":
            name = self.media_name+".%s" % codec
        else:
            name = self.media_name
        if re.search('\/', name):
			name = re.sub('\/','-', name)
			self.media_name = name
	if re.search('\"', name):
			name = re.sub('\"','', name)
			self.media_name = name
        target = os.path.join(self.down_dir,name)
        if os.path.exists(target):
			ret = yesno(_("Download"),_("The file:\n\n%s \n\nalready exist, download again ?") % target)
			if ret == "No":
				return
        self.notebook.set_current_page(1)
        box = gtk.HBox(False, 5)
        vbox = gtk.VBox(False, 5)
        label = gtk.Label(name)
        label.set_alignment(0, 0.5)
        vbox.pack_start(label, False, False, 5)
        pbar = gtk.ProgressBar()
        pbar.set_size_request(400, 25)
        vbox.pack_end(pbar, False, False, 5)
        box.pack_start(gtk.image_new_from_pixbuf(self.media_img), False,False, 5)
        box.pack_start(vbox, False, False, 5)
        ## stop btn
        btnstop = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
        btnstop.add(image)
        box.pack_end(btnstop, False, False, 5)
        btnstop.set_tooltip_text(_("Stop Downloading"))
        self.down_container.pack_start(box, False ,False, 5)
        ## show folder button
        btnf = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON)
        btnf.add(image)
        box.pack_end(btnf, False, False, 5)
        btnf.set_tooltip_text("Show")
        ## convert button
        btn_conv = gtk.Button()
        if self.engine == "Youtube":
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_CONVERT, gtk.ICON_SIZE_BUTTON)
            btn_conv.add(image)
            box.pack_end(btn_conv, False, False, 5)
            btn_conv.set_tooltip_text(_("Convert to mp3"))
			## spinner
            throbber = gtk.Image()
            throbber.set_from_file(self.img_path+'/throbber.png')
            box.pack_end(throbber, False, False, 5)
		## clear button
        btn = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
        btn.add(image)
        box.pack_end(btn, False, False, 5)
        btn.set_tooltip_text(_("Remove"))
        
        box.show_all()
        btnf.hide()
        if self.engine == "Youtube":
			btn_conv.hide()
			throbber.hide()
			btn_conv.connect('clicked', self.extract_audio,self.media_name,codec,btn_conv,throbber)
        btn.hide()
        btnf.connect('clicked', self.show_folder, self.down_dir)
        btn.connect('clicked', self.remove_download)
        t = Downloader(self,url, name, pbar, btnf,btn,btn_conv,btnstop,name)
        t.start()
        
    def show_folder(self,widget,path):
        if sys.platform == "win32":
	    os.system('explorer %s' % path)
	else:
		os.system('xdg-open %s' % path)
        
    def remove_download(self, widget):
        ch = widget.parent
        ch.parent.remove(ch)
        
    def extract_audio(self,widget,name,codec,convbtn,throbber):
		convbtn.hide()
		self.animation = gtk.gdk.PixbufAnimation(self.img_path+'/throbber.gif')
		self.loader_pixbuf = throbber.get_pixbuf() # save the Image contents so we can set it back later
		throbber.set_from_animation(self.animation)
		throbber.show()
		src = os.path.join(self.down_dir,name+'.'+codec)
		target = os.path.join(self.down_dir,name+'.mp3')
		if os.path.exists(target):
			os.remove(target)
		self.statbar.push(1,_("Converting process started..."))
		if sys.platform != "linux2":
			ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(exec_path)),'ffmpeg\\ffmpeg.exe')
		else:
			ffmpeg_path = "/usr/bin/ffmpeg"
		(pid,t,r,s) = gobject.spawn_async([ffmpeg_path, '-i', src, '-f', 'mp3', '-ab', '192k', target],flags=gobject.SPAWN_DO_NOT_REAP_CHILD,standard_output = True, standard_error = True)
		data=(convbtn,throbber)
		gobject.child_watch_add(pid, self.task_done,data)
		
    def task_done(self,pid,ret,data):
                throbber=data[1]
                convbtn=data[0]
		throbber.set_from_pixbuf(self.loader_pixbuf)
		throbber.hide()
		convbtn.show()
		self.statbar.push(1,_("Audio file successfully created !"))
		while gtk.events_pending():
			gtk.main_iteration()
		time.sleep(5)
		if self.is_playing:
			self.statbar.push(1,_("Playing %s") % self.media_name)
		else:
			self.statbar.push(1,_("Stopped"))

		    
    def start_download(self, url, name, pbar, btnf, btn,btn_conv):
        self.active_downloads += 1
        self.active_down_label.set_text(str(self.active_downloads))
        ## download...
        try:
			start_time = time.time()
			urllib.urlretrieve(url, self.down_dir+"/"+ name,
			lambda nb, bs, fs, url=url: reporthook(nb,bs,fs,start_time,url,name,pbar))
			btnf.show()
			btn_conv.show()
			btn.show()
			return self.decrease_down_count()
        except:
			pbar.set_text(_("Failed..."))
			btn.show()
			return self.decrease_down_count()
    
    def decrease_down_count(self):
        if self.active_downloads > 0:
			self.active_downloads -= 1
			self.active_down_label.set_text(str(self.active_downloads))
        
    def on_about_btn_pressed(self, widget):
        dlg = self.gladeGui.get_widget("aboutdialog")
        #dlg.set_version(VERSION)
        response = dlg.run()
        if response == gtk.RESPONSE_DELETE_EVENT or response == gtk.RESPONSE_CANCEL:
            dlg.hide()
            
    def on_settings_btn_pressed(self, widget):
		#dlg.set_version(VERSION)
		if self.youtube_max_res == "320x240":
			self.res320.set_active(1)
		elif self.youtube_max_res == "640x320":
			self.res640.set_active(1)
		elif self.youtube_max_res == "854x480":
			self.res854.set_active(1)
		elif self.youtube_max_res == "1280x720":
			self.res1280.set_active(1)
		elif self.youtube_max_res == "1920x1080":
			self.res1920.set_active(1)
		self.dlg.set_position(gtk.WIN_POS_CENTER_ALWAYS)
		response = self.dlg.run()
		if response == False or response == True or response == gtk.RESPONSE_DELETE_EVENT:
			self.dlg.hide()

    def exit(self,widget):
        """Stop method, sets the event to terminate the thread's main loop"""
        if self.player.set_state(gst.STATE_PLAYING):
            self.player.set_state(gst.STATE_NULL)
        self.mainloop.quit()


if __name__ == "__main__":
    GsongFinder()
