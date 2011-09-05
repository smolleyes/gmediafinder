#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import sys
import glib
import pango
import os
import thread
import threading
import random
import time
import gobject
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gtk.gdk
import urllib
import pygst
pygst.require("0.10")
import gst
import mechanize
import gdata
import math
## for win32...py2exe
import json
import gdata.youtube.service as yt_service
import gettext
import time
import locale
import Queue

if sys.platform == "win32":
    import win32api

## custom lib
try:
    import debrid as debrider
    from config import *
    from engines import Engines
    from functions import *
    from playlist import Playlist
    if sys.platform != "win32":
        from pykey import send_string
    import checklinks as checkLink
except:
    from GmediaFinder.config import *
    from GmediaFinder.engines import Engines
    from GmediaFinder.functions import *
    from GmediaFinder.playlist import Playlist
    if sys.platform != "win32":
        from GmediaFinder.pykey import send_string
    import GmediaFinder.debrid as debrider
    import GmediaFinder.checklinks as checkLink


class GsongFinder(object):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2
    BUFFERING = 3
    PREROLLING = 4
    def __init__(self):
        ## default search options
        self.is_playing = False
        self.is_paused = False
        self.duration = None
        self.time_label = gtk.Label("00:00 / 00:00")
        self.media_name = ""
        self.media_link = ""
        self.play_options = "continue"
        self.nbresults = 100
        self.user_search = ""
        self.fullscreen = False
        self.mini_player = True
        self.showed = True ## trayicon
        self.timer = 0
        self.settings_folder = None
        self.conf_file = None
        self.seeker_move = None
        self.active_downloads = 0
        self.thread_num = 0
        self.xsink = False
        self.file_tags = {}
        self.engine_list = {}
        self.engine = None
        self.conf=conf
        self.latest_engine = ""
        self.change_page_request = False
        self.tray = None
        self.download_pool = []
        self.media_bitrate= None
        self.media_codec= None
        self.playlist_mode = False
        self.play = False
        self._cbuffering = -1
        self.status = self.STOPPED
        self.target_status = self.STOPPED
        self.url_checker = checkLink.CheckLinkIntegrity()
        self.url_debrid = debrider.Debrid(self)

        ## gui
        self.gladeGui = gtk.glade.XML(glade_file, None ,APP_NAME)
        self.window = self.gladeGui.get_widget("main_window")
        self.window.set_title("Gmediafinder")
        self.window.set_resizable(1)
        self.set_window_position()
        self.show_thumbs_opt_toggle = self.gladeGui.get_widget("show_thumbs_opt")
        if self.conf['show_thumbs'] == "True" :
            self.show_thumbs_opt_toggle.set_active(1)
        self.img_path = img_path
        self.window.set_icon_from_file(os.path.join(self.img_path,'gmediafinder.png'))
        self.window.connect('key-press-event', self.onKeyPress)
    
        
        # options menu
        self.options_bar = self.gladeGui.get_widget("options_bar")
        self.search_box = self.gladeGui.get_widget("search_box")
        self.results_box = self.gladeGui.get_widget("results_box")
        self.quality_box = self.gladeGui.get_widget("quality_box")

        ## throbber
        self.throbber = self.gladeGui.get_widget("throbber_img")
        animation = gtk.gdk.PixbufAnimation(self.img_path+'/throbber.gif')
        self.throbber.set_from_animation(animation)

        ## notebooks
        self.notebook = self.gladeGui.get_widget("notebook")
        self.results_notebook = self.gladeGui.get_widget("results_notebook")
        self.video_cont = self.gladeGui.get_widget("video_cont")

        self.volume_btn = self.gladeGui.get_widget("volume_btn")
        self.down_btn = self.gladeGui.get_widget("down_btn")

        self.search_entry = self.gladeGui.get_widget("search_entry")
        self.stop_search_btn = self.gladeGui.get_widget("stop_search_btn")
        ## playlist
        self.playlists_xml = playlists_xml
        self.playlist_scrollbox = self.gladeGui.get_widget("playlist_scrollbox")
        ## history
        self.search_entry.connect('changed',self.__search_history)
        self.history_view = gtk.EntryCompletion()
        self.history_view.set_minimum_key_length(1)
        self.search_entry.set_completion(self.history_view)
        self.history_model = gtk.ListStore(gobject.TYPE_STRING)
        self.history_view.set_model(self.history_model)
        self.history_view.set_text_column(0)
        ## options box
        self.search_opt_box = self.gladeGui.get_widget("search_options_box")

        ## statbar
        self.statbar = self.gladeGui.get_widget("statusbar")
        ## info
        self.info_label = self.gladeGui.get_widget("info_label")

        ## downloads
        self.down_box = self.gladeGui.get_widget("down_box")
        self.down_menu_btn = self.gladeGui.get_widget("down_menu_btn")
        self.down_container = gtk.VBox(False, 5)
        self.down_scroll = gtk.ScrolledWindow()
        self.down_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.down_scroll.add_with_viewport(self.down_container)
        self.down_box.add(self.down_scroll)
        self.active_down_label = self.gladeGui.get_widget("active_down_label")
        self.path_btn = self.gladeGui.get_widget("select_path_btn")
        self.path_btn.set_current_folder(down_dir)
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
        ## seekbar infos
        self.media_name_label = self.gladeGui.get_widget("media_name")
        self.media_name_label.set_property('ellipsize', pango.ELLIPSIZE_END)
        self.media_codec_label = self.gladeGui.get_widget("media_codec")
        self.media_bitrate_label = self.gladeGui.get_widget("media_bitrate")

        ## visualisations
        try:
            self.vis = self.conf["visualisation"]
        except:
            self.conf["visualisation"] = vis
            self.vis = vis
            self.conf.write()
        combo = self.gladeGui.get_widget("vis_chooser")
        self.vis_selector = ComboBox(combo)
        self.vis_selector.setIndexFromString(self.vis)

        ##extras options
        self.downloads_check = self.gladeGui.get_widget("downloads_enabled")
        self.convert_check = self.gladeGui.get_widget("convert_enabled")
        self.warn_dialog = self.gladeGui.get_widget("warn_dialog")
        self.systray_check = self.gladeGui.get_widget("systray_enabled")
        self.down_dir = down_dir
        if downloads == 'True':
            self.downloads_check.set_active(1)
        if convert == 'True':
            self.convert_check.set_active(1)
        if systray == 'True':
            self.systray_check.set_active(1)

        ## SIGNALS
        dic = {"on_main_window_destroy_event" : self.exit,
        "on_quit_menu_activate" : self.exit,
        "on_pause_btn_clicked" : self.pause_resume,
        "on_down_btn_clicked" : self.download_file,
        "on_nextpage_btn_clicked" : self.change_page,
        "on_pageback_btn_clicked" : self.change_page,
        "on_search_entry_activate" : self.prepare_search,
        "on_shuffle_btn_toggled" : self.set_play_options,
        "on_repeat_btn_toggled" : self.set_play_options,
        "on_vol_btn_value_changed" : self.on_volume_changed,
        "on_vis_chooser_changed" : self.change_visualisation,
        "on_about_menu_clicked" : self.on_about_btn_pressed,
        "on_settings_menu_clicked" : self.on_settings_btn_pressed,
        "on_down_menu_btn_clicked" : self.show_downloads,
        "on_backtohome_btn_clicked" : self.show_home,
        "on_select_path_btn_file_set" : self.update_down_path,
        "on_main_window_configure_event" : self.save_position,
        "on_search_entry_icon_press" : self.clear_search_entry,
        "on_show_thumbs_opt_toggled" : self.on_gui_opt_toggled,
        "on_stop_search_btn_clicked": self.stop_threads,
        "on_downloads_enabled_toggled" : self.set_extras_options,
        "on_convert_enabled_toggled" : self.set_extras_options,
        "on_systray_enabled_toggled" : self.set_extras_options,
        "on_clear_history_btn_clicked" : self.clear_history,
         }
        self.gladeGui.signal_autoconnect(dic)
        self.window.connect('destroy', self.exit)

        ## finally setup the list
        self.model = gtk.ListStore(gtk.gdk.Pixbuf,str,object,object,object,str)
        self.treeview = gtk.TreeView()
        self.window.realize()
        self.odd = gtk.gdk.color_parse(str(self.window.style.bg[gtk.STATE_NORMAL]))
        self.even = gtk.gdk.color_parse(str(self.window.style.base[gtk.STATE_NORMAL]))
        self.treeview.set_model(self.model)

        rendererp = gtk.CellRendererPixbuf()
        pixcolumn = gtk.TreeViewColumn("",rendererp,  pixbuf=0)
        self.treeview.append_column(pixcolumn)

        rendertxt = gtk.CellRendererText()
        txtcolumn = gtk.TreeViewColumn("txt",rendertxt, markup=1)
        txtcolumn.set_cell_data_func(rendertxt, self.alternate_color)
        txtcolumn.set_title(_(' Results : '))
        self.treeview.append_column(txtcolumn)

        renderer = gtk.CellRendererText()
        pathColumn = gtk.TreeViewColumn("Link", renderer)
        self.treeview.append_column(pathColumn)

        qualityColumn = gtk.TreeViewColumn("Quality", renderer)
        self.treeview.append_column(qualityColumn)
        
        nameColumn = gtk.TreeViewColumn("Name", renderer)
        self.treeview.append_column(nameColumn)

        plugnameColumn = gtk.TreeViewColumn("Name", renderer)
        self.treeview.append_column(plugnameColumn)

        ## download treeview
        self.download_treestore = gtk.TreeStore(str,int,str,str,str,
                                                str,
                                                str,
                                                str,
                                                str,
                                                str,object)
        #name
        self.download_treeview = gtk.TreeView(self.download_treestore)
        self.download_treeview.set_headers_visible(False)
        self.download_tvcolumn = gtk.TreeViewColumn('Name')
        self.download_tvcolumn.set_max_width(450)
        self.download_tvcolumn.set_min_width(450)
        self.download_treeview.append_column(self.download_tvcolumn)
        cellrenderer_text = gtk.CellRendererText()
        cellrenderer_text.props.wrap_width = 430
        cellrenderer_text.props.wrap_mode = pango.WRAP_WORD
        self.download_tvcolumn.pack_start(cellrenderer_text, False)
        self.download_tvcolumn.add_attribute(cellrenderer_text, "text", 0)
        #progress
        self.download_progresscolumn = gtk.TreeViewColumn("Progress")
        self.download_progresscolumn.set_spacing(10)
        self.download_progresscolumn.set_min_width(50)
        
        self.download_treeview.append_column(self.download_progresscolumn)
        cellrenderer_progress = gtk.CellRendererProgress()
        self.download_progresscolumn.pack_start(cellrenderer_progress, True)
        self.download_progresscolumn.add_attribute(cellrenderer_progress, "value", 1)
        #size
        self.download_sizecolumn = gtk.TreeViewColumn('Downloaded')
        self.download_sizecolumn.set_spacing(10)
        self.download_sizecolumn.set_min_width(150)
        self.download_treeview.append_column(self.download_sizecolumn)
        cellrenderer_text = gtk.CellRendererText()
        self.download_sizecolumn.pack_start(cellrenderer_text, False)
        self.download_sizecolumn.add_attribute(cellrenderer_text, "text", 2)
        #speed
        self.download_ratecolumn = gtk.TreeViewColumn('Rate')
        self.download_ratecolumn.set_spacing(10)
        self.download_ratecolumn.set_min_width(70)
        self.download_treeview.append_column(self.download_ratecolumn)
        cellrenderer_text = gtk.CellRendererText()
        self.download_ratecolumn.pack_start(cellrenderer_text, False)
        self.download_ratecolumn.add_attribute(cellrenderer_text, "text", 3)
        #eta
        self.download_etacolumn = gtk.TreeViewColumn('Eta')
        self.download_etacolumn.set_min_width(70)
        self.download_etacolumn.set_spacing(20)
        self.download_treeview.append_column(self.download_etacolumn)
        cellrenderer_text = gtk.CellRendererText()
        self.download_etacolumn.pack_start(cellrenderer_text, False)
        self.download_etacolumn.add_attribute(cellrenderer_text, "text", 4)
        ## pausebtn
        self.download_pausecolumn = gtk.TreeViewColumn('Pause/resume')
        self.download_pausecolumn.set_min_width(20)
        self.download_pausecolumn.set_spacing(40)
        self.download_treeview.append_column(self.download_pausecolumn)
        self.download_pixrenderer = gtk.CellRendererPixbuf()
        self.download_pausecolumn.pack_start(self.download_pixrenderer, False)
        self.download_pausecolumn.add_attribute(self.download_pixrenderer, "stock-id", 5)
        ## signals
        self.download_treeview.connect_after('cursor-changed', self.on_pause_download,
                                                    self.download_pausecolumn)
        ## cancelbtn
        self.download_cancelcolumn = gtk.TreeViewColumn('Cancel')
        self.download_cancelcolumn.set_min_width(20)
        self.download_treeview.append_column(self.download_cancelcolumn)
        pixrenderer = gtk.CellRendererPixbuf()
        self.download_cancelcolumn.pack_start(pixrenderer, False)
        self.download_cancelcolumn.add_attribute(pixrenderer, "stock-id", 6)
        ## signals
        self.download_treeview.connect_after('cursor-changed', self.on_cancel_download,
                                                    self.download_cancelcolumn)
        
        ## removebtn
        self.download_removecolumn = gtk.TreeViewColumn('remove')
        self.download_removecolumn.set_min_width(20)
        self.download_treeview.append_column(self.download_removecolumn)
        pixrenderer = gtk.CellRendererPixbuf()
        self.download_removecolumn.pack_start(pixrenderer, False)
        self.download_removecolumn.add_attribute(pixrenderer, "stock-id", 7)
        ## signals
        self.download_treeview.connect_after('cursor-changed', self.on_remove_download,
                                                    self.download_removecolumn)
                                                    
        ## viewbtn
        self.download_viewcolumn = gtk.TreeViewColumn('view')
        self.download_viewcolumn.set_min_width(20)
        self.download_treeview.append_column(self.download_viewcolumn)
        pixrenderer = gtk.CellRendererPixbuf()
        self.download_viewcolumn.pack_start(pixrenderer, False)
        self.download_viewcolumn.add_attribute(pixrenderer, "stock-id", 8)
        ## viewbtn
        self.download_treeview.connect_after('cursor-changed', self.on_view_download,
                                                    self.download_viewcolumn)
        
        ## convertbtn
        self.download_convertcolumn = gtk.TreeViewColumn('convert')
        self.download_convertcolumn.set_min_width(20)
        self.download_treeview.append_column(self.download_convertcolumn)
        pixrenderer = gtk.CellRendererPixbuf()
        self.download_convertcolumn.pack_start(pixrenderer, False)
        self.download_convertcolumn.add_attribute(pixrenderer, "stock-id", 9)
        ## viewbtn
        self.download_treeview.connect_after('cursor-changed', self.on_convert_download,
                                                    self.download_convertcolumn)
        
        ## finalize
        self.down_container.add(self.download_treeview)
        
        
        ## setup the scrollview
        self.results_scroll = self.gladeGui.get_widget("results_scrollbox")
        self.columns = self.treeview.get_columns()
        if self.conf['show_thumbs'] == "False":
            self.columns[0].set_visible(0)
        self.columns[1].set_sort_column_id(1)
        self.columns[2].set_visible(0)
        self.columns[3].set_visible(0)
        self.columns[4].set_visible(0)
        self.columns[5].set_visible(0)
        self.results_scroll.add(self.treeview)
        self.results_scroll.connect_after('size-allocate', self.resize_wrap, self.treeview, self.columns[1], rendertxt)
        ## right click menu
        self.search_playlist_menu = gtk.Menu()
        getlink_item = gtk.ImageMenuItem(gtk.STOCK_COPY)
        getlink_item.get_children()[0].set_label(_('Copy file link'))
        addplaylist_item = gtk.ImageMenuItem(gtk.STOCK_EDIT)
        addplaylist_item.get_children()[0].set_label(_('Add to Library'))
        self.search_playlist_menu.append(getlink_item)
        self.search_playlist_menu.append(addplaylist_item)
        getlink_item.connect('activate', self._copy_link)
        addplaylist_item.connect('activate', self._add_to_playlist)
        ## connect treeview signals
        self.search_playlist_menu_active = False
        self.treeview.connect('row-activated',self.get_model)
        self.treeview.connect('button-press-event',self._show_search_playlist_menu)
        ## create the players
        self.player = gst.element_factory_make("playbin2", "player")
        audiosink = gst.element_factory_make("autoaudiosink")
        audiosink.set_property('async-handling', True)

        if sys.platform == "win32":
            self.videosink = gst.element_factory_make('dshowvideosink')
        else:
            self.videosink = gst.element_factory_make('xvimagesink')
        self.videosink.set_property('async', False)
        self.player.set_property("audio-sink", audiosink)
        self.player.set_property('video-sink', self.videosink)
        self.player.set_property('buffer-size', 1024000)
        #GST_PLAY_FLAG_DOWNLOAD = 1
        #self.player.set_property('flags',GST_PLAY_FLAG_DOWNLOAD)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)
        bus.connect("message::tag", self.bus_message_tag)
        bus.connect('message::buffering', self.on_message_buffering)

        ## engines
        self.dlg = self.gladeGui.get_widget("settings_dialog")
        self.engines_box = self.gladeGui.get_widget("engines_box")

        ## time
        self.timeFormat = gst.Format(gst.FORMAT_TIME)

        ## mini player
        self.miniPlayer = self.gladeGui.get_widget("mini-player")
        self.miniPlayer.set_size_request(width,40)
        self.miniPlayer.move(0,height-42)
        self.miniPlayer_init = False
        self.miniPlayer.set_keep_above(True)
        self.infobox = self.gladeGui.get_widget("btn_info_box")
        self.infobox_cont = self.gladeGui.get_widget("btn_infobox_cont")
        self.mini_infobox_cont = self.gladeGui.get_widget("mini_infobox_cont")
        ## btn box
        self.btn_box = self.gladeGui.get_widget("btn_box")
        self.btn_box_cont = self.gladeGui.get_widget("btn_box_cont")
        self.mini_btn_box_cont = self.gladeGui.get_widget("mini_btn_box_cont")
        
        self.mini_seekbox = self.gladeGui.get_widget("mini_seekbox_cont")
        
        ## create engines selector combobox
        box = self.gladeGui.get_widget("engine_selector_box")
        self.active_engines = create_comboBox()
        self.active_engines.connect("changed", self.set_engine)
        box.pack_start(self.active_engines, False,False,5)
        self.engine_selector = ComboBox(self.active_engines)
        self.engine_selector.append("")
        ## load playlists
        self.Playlist = Playlist(self)
        ## start gui
        self.window.show_all()
        self.throbber.hide()
        self.download_treeview.columns_autosize()
        ## start engines
        self.engines_client = Engines(self)

        ## engine selector (engines only with direct links)
        self.global_search = _("All")
        self.global_audio_search = _("All audios")
        self.global_video_search = _("All videos")

        for engine in sorted(self.engine_list):
            try:
                if getattr(self.engines_client, '%s' % engine).adult_content:
                    self.engine_selector.append(engine,True)
            except:
                self.engine_selector.append(engine)

        if ("Youtube" in self.engine_list):
            self.engine_selector.setIndexFromString("Youtube")
        else:
            self.engine_selector.select(0)
        self.engine_selector.append(self.global_search)
        self.engine_selector.append(self.global_audio_search)
        self.engine_selector.append(self.global_video_search)
        self.search_entry.grab_focus()

        ## load icons
        self.load_gui_icons()
        self.statbar.hide()
        
        ## check extra options
        if downloads == 'False':            
            self.down_btn.hide()
            self.down_menu_btn.hide()
            
        ## tray icon
        if systray == 'True':
            self.__create_trayicon()
        ## load download to resume
        #print self.search_engine.engine_type
        self.resume_downloads()
            
        ## start main loop
        gobject.threads_init()
        #THE ACTUAL THREAD BIT
        self.manager = FooThreadManager(20)
        self.mainloop = gobject.MainLoop(is_running=True)

    
    def on_pause_download(self, treeview, column):
        if self.download_treeview.get_cursor()[1] == column:
            # ici recup ligne selectionné
            l = self.return_selection(treeview)
            # get download instance
            download = l[-1]
            download.pause()
            
    def on_cancel_download(self, treeview, column):
        if self.download_treeview.get_cursor()[1] == column:
            # ici recup ligne selectionné
            l = self.return_selection(treeview)
            # get download instance
            download = l[-1]
            download.cancel()
            
    def on_convert_download(self, treeview, column):
        if self.download_treeview.get_cursor()[1] == column:
            # ici recup ligne selectionné
            l = self.return_selection(treeview)
            # get download instance
            download = l[-1]
            download.convert()
            
    def on_remove_download(self, treeview, column):
        if self.download_treeview.get_cursor()[1] == column:
            # ici recup ligne selectionné
            l = self.return_selection(treeview)
            # get download instance
            download = l[-1]
            download.remove_download()
            
    def on_view_download(self, treeview, column):
        if self.download_treeview.get_cursor()[1] == column:
            # ici recup ligne selectionné
            l = self.return_selection(treeview)
            # get download instance
            return self.show_folder(self.down_dir)
            
    def return_selection(self, treeview):
        sel              = self.download_treeview.get_selection()
        ( model,iter )   = sel.get_selected()
        return list(model[iter])
    
    def set_window_position(self):
        self.window.set_default_size(int(self.conf['window_state'][0]),int(self.conf['window_state'][1]))
        try:
            x,y = int(self.conf['window_state'][2]),int(self.conf['window_state'][3])
            if x == 0 or y == 0:
                self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
            else:
                self.window.move(x,y)
        except:
            self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
    
    def set_extras_options(self, widget):
        if ('convert' in widget.name):
            if widget.get_active():
                accept = warn_dialog(self.warn_dialog)
                if accept == 0:
                    convert = 'True'
                    self.conf['convert'] = True
                else:
                    widget.set_active(0)
            else:
                convert = 'False'
                self.conf['convert'] = False
                
        elif ('systray' in widget.name):
            if widget.get_active():
                systray = 'True'
                self.conf['systray'] = True
                if not self.tray:
                    self.__create_trayicon()
                else:
                    self.tray.set_visible(1)
            else:
                systray = 'False'
                self.conf['systray'] = False
                self.tray.set_visible(0)
        else:
            if widget.get_active():
                accept = warn_dialog(self.warn_dialog)
                if accept == 0:
                    self.down_btn.show()
                    self.down_menu_btn.show()
                    self.conf['downloads'] = True
                else:
                    widget.set_active(0)
            else:
                self.down_btn.hide()
                self.down_menu_btn.hide()
                self.conf['downloads'] = False
        ## save config
        self.conf.write()
    
    def on_gui_opt_toggled(self, widget):
        if widget.get_active():
            self.show_thumbs_opt = "True"
            self.columns[0].set_visible(1)
        else:
            self.show_thumbs_opt = "False"
            self.columns[0].set_visible(0)
        self.conf["show_thumbs"] = self.show_thumbs_opt
        self.conf.write()

    def clear_search_entry(self,widget,e,r):
        if e == gtk.ENTRY_ICON_SECONDARY:
            self.search_entry.set_text("")
        elif e == gtk.ENTRY_ICON_PRIMARY:
            self.prepare_search()
        self.search_entry.grab_focus()

    def alternate_color(self, column, cell, model, iter):
        if int((model.get_string_from_iter(iter).split(":")[0])) % 2:
            cell.set_property('background-gdk', self.odd)
            cell.set_property('cell-background-gdk', self.odd)
            cell.set_property('foreground-gdk', gtk.gdk.color_parse(str(self.window.style.fg[gtk.STATE_ACTIVE])))
        else:
            cell.set_property('background-gdk', self.even)
            cell.set_property('cell-background-gdk', self.even)
            cell.set_property('foreground-gdk', gtk.gdk.color_parse(str(self.window.style.fg[gtk.STATE_NORMAL])))

    def save_position(self,widget,e):
        self.x,self.y=self.window.get_position()

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
        vis = self.vis_selector.getSelected()
        visi = self.vis_selector.getSelectedIndex()
        if vis != "goom" and visi != 0 :
            self.vis = "libvisual_"+vis
        else:
            self.vis = vis
        self.conf["visualisation"] = vis
        self.conf.write()
        return self.vis

    def update_down_path(self,widget=None):
        self.conf["download_path"] = widget.get_current_folder()
        self.conf.write()
        self.down_dir = widget.get_current_folder()

    def set_engine(self,engine=None):
        self.quality_box.hide()
        global_search = False
        try:
            engine = engine.name
            self.engine = self.engine_selector.getSelected()
        except:
            self.engine = engine
            self.engine_selector.setIndexFromString(engine)
            global_search = True
        iter = self.engine_selector.getSelectedIndex()
        if iter == 0:
            self.engine = None
            return
        ## clean the gui options box and load the plugin gui
        for w in self.search_opt_box:
            self.search_opt_box.remove(w)
        ## do not set the engine if global search
        if self.engine == self.global_search or self.engine == self.global_video_search or self.engine == self.global_audio_search:
            return
        ## load the plugin
        self.search_engine = getattr(self.engines_client,'%s' % self.engine)
        #if not global_search:
        self.search_engine.load_gui()

    def show_downloads(self, widget):
        self.notebook.set_current_page(1)
        self.down_container.queue_draw()

    def show_home(self, widget):
        self.notebook.set_current_page(0)

    def get_model(self,widget=None,path=None,column=None):
        #if self.search_playlist_menu_active:
        #   return
        self.media_bitrate = ""
        self.media_codec = ""
        current_page = self.results_notebook.get_current_page()
        if int(current_page) == 1:
            self.playlist_mode = True
        else:
            self.playlist_mode = False
        if widget or not self.playlist_mode:
            selected = self.treeview.get_selection()
            self.selected_iter = selected.get_selected()[1]
            self.path = self.model.get_path(self.selected_iter)
            ## else extract needed metacity's infos
            self.media_thumb = self.model.get_value(self.selected_iter, 0)
            name = self.model.get_value(self.selected_iter, 4)
            self.media_name = decode_htmlentities(name)
            self.file_tags = {}
            self.media_markup = self.model.get_value(self.selected_iter, 1)
            self.media_plugname = self.model.get_value(self.selected_iter, 5)
            ## for global search
            if not self.engine_selector.getSelected() == self.media_plugname:
                self.set_engine(self.media_plugname)
            ## return only theme name and description then extract infos from hash
            self.media_link = self.model.get_value(self.selected_iter, 2)
            self.media_img = self.model.get_value(self.selected_iter, 0)
        else:
            selected = self.Playlist.treeview.get_selection()
            self.selected_iter = selected.get_selected()[1]
            self.path = self.Playlist.treestore.get_path(self.selected_iter)
            ## else extract needed metacity's infos
            self.media_thumb = self.Playlist.treestore.get_value(self.selected_iter, 0)
            name = self.Playlist.treestore.get_value(self.selected_iter, 0)
            self.media_name = decode_htmlentities(name)
            self.file_tags = {}
            self.media_markup = self.Playlist.treestore.get_value(self.selected_iter, 0)
            self.media_plugname = self.Playlist.treestore.get_value(self.selected_iter, 0)
            return self.Playlist.on_selected(self.Playlist.treeview)
        ## play in engine
        if not self.search_engine.engine_type == 'files':
            self.stop_play()
        thread.start_new_thread(self.search_engine.play,(self.media_link,))
        #self.search_engine.play(self.media_link)
        
    def prepare_search(self,widget=None):
        self.user_search = self.search_entry.get_text()
        self.latest_engine = self.engine_selector.getSelectedIndex()
        if self.latest_engine == 0:
            self.info_label.set_text(_("Please select a search engine..."))
            return
        if not self.user_search:
            if not self.search_engine.has_browser_mode:
                self.info_label.set_text(_("Please enter an artist/album or song name..."))
                return
        if not self.engine:
            self.info_label.set_text(_("Please select an engine..."))
            return
        self.change_page_request = False
        self.stop_threads()
        self.model.clear()
        self.changepage_btn.set_sensitive(0)
        self.pageback_btn.set_sensitive(0)
        self.__add_to_history()
        self.engine_list = self.engine_selector.get_list()
        if self.engine_selector.getSelected() == self.global_search:
            for engine in self.engine_list:
                try:
                    self.search_engine = getattr(self.engines_client,'%s' % engine)
                    self.search()
                except:
                    continue
            self.engine_selector.setIndexFromString(self.global_search)
        elif self.engine_selector.getSelected() == self.global_video_search:
            for engine in self.engine_list:
                try:
                    self.search_engine = getattr(self.engines_client,'%s' % engine)
                except:
                    continue
                if not self.search_engine.engine_type == "video":
                    continue
                try:
                    self.search()
                except:
                    continue
            self.engine_selector.setIndexFromString(self.global_video_search)
        elif self.engine_selector.getSelected() == self.global_audio_search:
            for engine in self.engine_list:
                try:
                    self.search_engine = getattr(self.engines_client,'%s' % engine)
                except:
                    continue
                if not self.search_engine.engine_type == "audio" or self.search_engine.name == "Jamendo":
                    continue
                try:
                    self.search()
                except:
                    continue
            self.engine_selector.setIndexFromString(self.global_audio_search)
        else:
            return self.search()

    def change_page(self,widget=None):
        if not self.changepage_btn.get_property("visible"):
            return
        try:
            name = widget.name
        except:
            name = ""
        self.model.clear()
        user_search = self.search_entry.get_text()
        engine = self.latest_engine
        if not user_search or user_search != self.user_search or not engine or engine != self.latest_engine:
            ## if engine doesn t have browser mode, start a new search
            if not self.search_engine.has_browser_mode:
                return self.prepare_search()
            else:
                return self.prepare_change_page(engine, user_search, name)
        else:
            return self.prepare_change_page(engine, user_search, name)
            
    def prepare_change_page(self, engine, user_search, name):
            self.engine_selector.select(self.latest_engine)
            if self.engine_selector.getSelected() == self.global_search:
                for engine in self.engine_list:
                    try:
                        self.search_engine = getattr(self.engines_client,'%s' % engine)
                    except:
                        continue
                    if self.search_engine.name == "Jamendo":
                        continue
                    try:
                        self.do_change_page(name)
                    except:
                        continue
            elif self.engine_selector.getSelected() == self.global_audio_search:
                for engine in self.engine_list:
                    try:
                        self.search_engine = getattr(self.engines_client,'%s' % engine)
                    except:
                        continue
                    if self.search_engine.engine_type == "video" or self.search_engine.name == "Jamendo":
                        continue
                    try:
                        self.do_change_page(name)
                    except:
                        continue
            elif self.engine_selector.getSelected() == self.global_video_search:
                for engine in self.engine_list:
                    try:
                        self.search_engine = getattr(self.engines_client,'%s' % engine)
                    except:
                        continue
                    if self.search_engine.engine_type == "audio":
                        continue
                    try:
                        self.do_change_page(name)
                    except:
                        continue
            return self.do_change_page(name)

    def do_change_page(self,name):
        if self.engine_selector.getSelected() == self.global_audio_search:
            if self.search_engine.engine_type == "video":
                return
        if name == "pageback_btn":
            if self.search_engine.current_page != 1:
                try:
                    self.search_engine.num_start = self.search_engine.num_start - self.search_engine.results_by_page
                except:
                    pass
                self.search_engine.current_page = self.search_engine.current_page - 1
        else:
            try:
                self.search_engine.num_start = self.search_engine.num_start + self.search_engine.results_by_page
            except:
                pass
            self.search_engine.current_page = self.search_engine.current_page + 1
        self.search(self.search_engine.current_page)

    def search(self,page=None):
        self.engine_selector.select(self.latest_engine)
        ## send request to the module, can pass type and order too...reset page start to inital state
        if not page:
            page = self.search_engine.main_start_page
            self.search_engine.current_page = self.search_engine.main_start_page
        ## check if first page then desactivate back page
        if page > 1:
            self.pageback_btn.set_sensitive(1)
        else:
            self.pageback_btn.set_sensitive(0)
            #thread.start_new_thread(self.search_engine.search,(self.user_search,page))
        self.add_thread(self.search_engine,self.user_search,page)

    def add_sound(self, name, media_link, img=None, quality_list=None, plugname=None,markup_src=None):
        if not img:
            img = gtk.gdk.pixbuf_new_from_file_at_scale(os.path.join(self.img_path,'sound.png'), 64,64, 1)
        if not name or not media_link or not img:
            return
        ## clean markup...
        try:
            n = decode_htmlentities(name)
            m = glib.markup_escape_text(n)
            markup = '<small><b>%s</b></small>' % m
        except:
            return
        if markup_src:
            markup = markup + markup_src
        iter = self.model.append()
        self.model.set(iter,
                        0, img,
                        1, markup,
                        2, media_link,
                        3, quality_list,
                        4, name,
                        5, plugname,
                        )

    def start_stop(self,widget=None):
        if widget:
            if not self.is_playing:
                return self.get_model()
            else:
                return self.stop_play()
        else:
            if self.play and self.active_link:
                if not self.is_playing:
                    return self.start_play(self.active_link)
                else:
                    return self.stop_play()

    def start_play(self,url):
		self.active_link = url
		self.play = True
		self.is_playing = True
		self.is_paused = False
		self.duration = None
		self.file_tags = {}
		#if not sys.platform == "win32":
			#if not self.vis_selector.getSelectedIndex() == 0 and not self.search_engine.engine_type == "video":
				#self.player.set_property('flags', "Render visualisation when no video is present")
				#self.vis = self.change_visualisation()
				#self.visual = gst.element_factory_make(self.vis,'visual')
				#self.player.set_property('vis-plugin', self.visual)
			#else:
				#if self.search_engine.engine_type == "video":
					#self.player.set_property('flags', "Render the video stream")
				#else:
					#self.player.set_property('flags', "Render the audio stream")
		self.play_btn_pb.set_from_pixbuf(self.stop_icon)
		self.pause_btn_pb.set_from_pixbuf(self.pause_icon)
		self.player.set_property("uri", url)
		self.movie_window.queue_draw()
		self.player.set_state(gst.STATE_PLAYING)
		self.play_thread_id = thread.start_new_thread(self.play_thread, ())

    def stop_play(self,widget=None):
        self.player.set_state(gst.STATE_NULL)
        self.play_btn_pb.set_from_pixbuf(self.play_icon)
        self.pause_btn_pb.set_from_pixbuf(self.pause_icon)
        self.is_playing = False
        self.is_paused = False
        self.duration = None
        self.play_thread_id = None
        self.play = False
        self.active_link = None
        self.update_time_label()
        #self.active_link = None
        self.movie_window.queue_draw()
        bit=_('Bitrate:')
        enc=_('Encoding:')
        play=_('Playing:')
        name = glib.markup_escape_text(self.media_name)
        gobject.idle_add(self.media_name_label.set_markup,'<small><b>%s</b></small>' % play)
        gobject.idle_add(self.media_bitrate_label.set_markup,'<small><b>%s </b></small>' % bit)
        gobject.idle_add(self.media_codec_label.set_markup,'<small><b>%s </b></small>' % enc)

    def play_thread(self):
		play_thread_id = self.play_thread_id
		while play_thread_id == self.play_thread_id:
			if play_thread_id == self.play_thread_id:
				if not self.seeker_move:
					self.update_time_label()
			time.sleep(1)

    def load_gui_icons(self):
        ## try to load and use the current gtk icon theme,
        ## if not possible, use fallback icons
        default_icon_theme = gtk.icon_theme_get_default()
        ## load desired icons if possible
        play_icon = default_icon_theme.lookup_icon("player_play",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        if play_icon:
            self.play_icon = play_icon.load_icon()

        stop_icon = default_icon_theme.lookup_icon("player_stop",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        if stop_icon:
            self.stop_icon = stop_icon.load_icon()

        pause_icon = default_icon_theme.lookup_icon("stock_media-pause",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        if pause_icon:
            self.pause_icon = pause_icon.load_icon()

        shuffle_icon = default_icon_theme.lookup_icon("stock_shuffle",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        if shuffle_icon:
            self.shuffle_icon = shuffle_icon.load_icon()

        loop_icon = default_icon_theme.lookup_icon("stock_repeat",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        if loop_icon:
            self.loop_icon = loop_icon.load_icon()

        pagen_icon = default_icon_theme.lookup_icon("next",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        if pagen_icon:
            self.page_next_icon = pagen_icon.load_icon()

        pagep_icon = default_icon_theme.lookup_icon("previous",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        if pagep_icon:
            self.page_prev_icon = pagep_icon.load_icon()
            
        clear_icon = default_icon_theme.lookup_icon("gtk-clear",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        if clear_icon:
            self.clear_icon = clear_icon.load_icon()
            
        fullscreen_pix = default_icon_theme.lookup_icon("gtk-fullscreen",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        self.fullscreen_pix = fullscreen_pix.load_icon()
        leave_fullscreen_pix = default_icon_theme.lookup_icon("gtk-leave-fullscreen",24,gtk.ICON_LOOKUP_USE_BUILTIN)
        self.leave_fullscreen_pix = leave_fullscreen_pix.load_icon()

        ## play
        self.play_btn = self.gladeGui.get_widget("play_btn")
        self.play_btn_pb = self.gladeGui.get_widget("play_btn_img")
        self.play_btn_pb.set_from_pixbuf(self.play_icon)
        self.play_btn.connect('clicked', self.start_stop)
        ## pause
        self.pause_btn = self.gladeGui.get_widget("pause_btn")
        self.pause_btn_pb = self.gladeGui.get_widget("pause_btn_img")
        self.pause_btn_pb.set_from_pixbuf(self.pause_icon)
        ## pages next/back
        self.changepage_btn = self.gladeGui.get_widget("nextpage_btn")
        self.changepage_pixb = self.gladeGui.get_widget("nextpage_pixb")
        self.changepage_pixb.set_from_pixbuf(self.page_next_icon)
        self.pageback_btn = self.gladeGui.get_widget("pageback_btn")
        self.pageback_pixb = self.gladeGui.get_widget("backpage_pixb")
        self.pageback_pixb.set_from_pixbuf(self.page_prev_icon)
        ## loop/shuffle
        self.shuffle_btn = self.gladeGui.get_widget("shuffle_btn")
        self.shuffle_pixb = self.gladeGui.get_widget("shuffle_btn_pixb")
        self.shuffle_pixb.set_from_pixbuf(self.shuffle_icon)
        self.loop_btn = self.gladeGui.get_widget("repeat_btn")
        self.loop_pixb = self.gladeGui.get_widget("repeat_btn_pixb")
        self.loop_pixb.set_from_pixbuf(self.loop_icon)
        ## paypalsupport img
        self.support_pixb = self.gladeGui.get_widget("paypal_img")
        pb = gtk.gdk.pixbuf_new_from_file(img_path+"/paypal.gif")
        self.support_pixb.set_from_pixbuf(pb)
        ## donate btn
        self.donate_pixb = self.gladeGui.get_widget("donate_img")
        pb = gtk.gdk.pixbuf_new_from_file(img_path+"/donate.gif")
        self.donate_pixb.set_from_pixbuf(pb)
        ## fullscreen btn
        self.fullscreen_btn = self.gladeGui.get_widget("fullscreen_btn")
        self.fullscreen_btn_pixb = self.gladeGui.get_widget("fullscreen_pix")
        self.fullscreen_btn_pixb.set_from_pixbuf(self.fullscreen_pix)
        self.fullscreen_btn.connect('clicked', self.set_fullscreen)
        self.fullscreen_btn.set_tooltip_text(_("enter fullscreen"))

        ## hide some icons by default
        self.changepage_btn.set_sensitive(0)
        self.pageback_btn.set_sensitive(0)
        self.stop_search_btn.set_sensitive(0)

    def on_message_buffering(self, bus, message):
		percent = message.parse_buffering()
		
		if math.floor(percent/5) > self._cbuffering:
			self._cbuffering = math.floor(percent/5)
			buffering = _('Buffering :')
			self.status = self.BUFFERING
			gobject.idle_add(self.media_name_label.set_markup,'<small><b>%s</b> %s%s</small>' % (buffering,percent,'%'))
		
		if percent == 100:
			if self.is_paused:
			    self.info_label.set_text('')
			    enc=_('Encoding:')
			    bit=_('Bitrate:')
			    play=_('Playing:')
			    name = glib.markup_escape_text(self.media_name)
			    gobject.idle_add(self.media_name_label.set_markup,'<small><b>%s</b> %s</small>' % (play,name))
			    self.media_bitrate_label.set_markup('<small><b>%s </b> %s</small>' % (bit,self.media_bitrate))
			    self.media_codec_label.set_markup('<small><b>%s </b> %s</small>' % (enc,self.media_codec))
			    self.status = self.PLAYING
			    self.pause_resume()
			self._cbuffering = -1
		elif self.status == self.BUFFERING:
			if not self.is_paused:
				self.pause_resume()
		
    def on_message(self, bus, message):
        if self.search_engine.engine_type == "video":
            self.videosink.set_property('force-aspect-ratio', True)
        
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.play_thread_id = None
            self.is_playing = False
            self.player.set_state(gst.STATE_NULL)
            self.pause_btn_pb.set_from_pixbuf(self.pause_icon)
            self.play_btn_pb.set_from_pixbuf(self.stop_icon)
            self.check_play_options()
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.play_thread_id = None
            self.is_playing = False
            self.pause_btn_pb.set_from_pixbuf(self.pause_icon)
            self.play_btn_pb.set_from_pixbuf(self.stop_icon)
            ## continue if continue option selected...
            if self.play_options == "continue":
                self.check_play_options()

    def pause_resume(self,widget=None):
        if not self.is_playing:
            return
        if not self.is_paused:
            self.pause_btn_pb.set_from_pixbuf(self.play_icon)
            self.player.set_state(gst.STATE_PAUSED)
            self.is_paused = True
        else:
            self.player.set_state(gst.STATE_PLAYING)
            self.pause_btn_pb.set_from_pixbuf(self.pause_icon)
            self.is_paused = False

    def set_play_options(self,widget):
		wname = widget.name
		wstate = widget.get_active()
		if wname == "shuffle_btn":
			if wstate:
				self.play_options = "shuffle"
				if not self.shuffle_btn.get_active():
					self.shuffle_btn.set_active(1)
				if self.loop_btn.get_active():
					self.loop_btn.set_active(0)
			else:
				if self.loop_btn.get_active():
					self.play_options = "loop"
				else:
					self.play_options = "continue"
		elif wname == "repeat_btn":
			if wstate:
				self.play_options = "loop"
				if not self.loop_btn.get_active():
					self.loop_btn.set_active(1)
				if self.shuffle_btn.get_active():
					self.shuffle_btn.set_active(0)
			else:
				if self.shuffle_btn.get_active():
					self.play_options = "shuffle"
				else:
					self.play_options = "continue"
		else:
			self.play_options = "continue"
		
    def check_play_options(self):
		self.stop_play()
		path = self.model.get_path(self.selected_iter)
		model = None
		treeview = None
		if path:
			model = self.model
			treeview = self.treeview
		else:
			model = self.Playlist.treestore
			path = model.get_path(self.selected_iter)
			treeview = self.Playlist.treeview
				
		if self.play_options == "loop":
			path = model.get_path(self.selected_iter)
			if path:
				treeview.set_cursor(path)
				self.get_model()
		elif self.play_options == "continue":
			## first, check if iter is still available (changed search while
			## continue mode for exemple..)
			## check for next iter
			try:
				if not model.get_path(self.selected_iter) == self.path:
					try:
						self.selected_iter = model.get_iter_first()
						if self.selected_iter:
							path = model.get_path(self.selected_iter)
							treeview.set_cursor(path)
							self.get_model()
					except:
						return
				else:
					try:
						self.selected_iter = model.iter_next(self.selected_iter)
						path = model.get_path(self.selected_iter)
						treeview.set_cursor(path)
						self.get_model()
					except:
						if not self.playlist_mode:
							self.load_new_page()
			except:
				if not self.playlist_mode:
					self.load_new_page()
		
		elif self.play_options == "shuffle":
			num = random.randint(0,len(model))
			self.selected_iter = model[num].iter
			path = model.get_path(self.selected_iter)
			treeview.set_cursor(path)
			self.get_model()
		
    def load_new_page(self):
        self.change_page_request=True
        self.change_page()

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
        if not self.is_paused:
            self.pause_resume()

    def update_time_label(self):
        """
        Update the time_label to display the current location
        in the media file as well as update the seek bar
        """
        if self.is_playing == False:
          adjustment = gtk.Adjustment(0, 0.00, 100.0, 0.1, 1.0, 1.0)
          self.seeker.set_adjustment(adjustment)
          gobject.idle_add(self.time_label.set_text,"00:00 / 00:00")
          return False
        
        ## update timer for mini_player and hide it if more than 5 sec
        ## without mouse movements
        self.timer += 1
        if self.fullscreen and self.mini_player and self.timer > 4:
            self.show_mini_player()
        
        ## disable screensaver
        if self.fullscreen == True and self.mini_player == False and self.timer > 55:
            if sys.platform == "win32":
                win32api.keybd_event(7,0,0,0)
            else:
                send_string('a')
            self.timer = 0
        
        if self.status == self.BUFFERING:
            return
        
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
            gobject.idle_add(self.time_label.set_text,current_position_formated + "/" + self.duration)
        
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
            self.videosink.set_xwindow_id(win_id)

    def on_drawingarea_clicked(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            return self.set_fullscreen()

    def set_fullscreen(self,widget=None):
        self.timer = 0
        if self.fullscreen :
            self.miniPlayer.hide()
            self.btn_box.reparent(self.btn_box_cont)
            self.infobox.reparent(self.infobox_cont)
            gobject.idle_add(self.search_box.show)
            gobject.idle_add(self.results_notebook.show)
            gobject.idle_add(self.control_box.show)
            gobject.idle_add(self.options_bar.show)
            self.window.window.set_cursor(None)
            gobject.idle_add(self.window.window.unfullscreen)
            gobject.idle_add(self.window.set_position,gtk.WIN_POS_CENTER)
            if sys.platform == 'win32':
                self.window.set_decorated(True)
            self.fullscreen = False
            gobject.idle_add(self.fullscreen_btn_pixb.set_from_pixbuf,self.fullscreen_pix)
            gobject.idle_add(self.fullscreen_btn_pixb.set_tooltip_text,_('enter fullscreen'))
        else:
            gobject.idle_add(self.search_box.hide)
            gobject.idle_add(self.results_notebook.hide)
            gobject.idle_add(self.options_bar.hide)
            self.btn_box.reparent(self.mini_btn_box_cont)
            self.infobox.reparent(self.mini_infobox_cont)
            pixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
            color = gtk.gdk.Color()
            cursor = gtk.gdk.Cursor(pixmap, pixmap, color, color, 0, 0)
            self.window.window.set_cursor(cursor)
            gobject.idle_add(self.control_box.hide)
            gobject.idle_add(self.window.window.fullscreen)
            if sys.platform == 'win32':
                self.window.set_decorated(False)
            self.fullscreen = True
            self.mini_player = False
            gobject.idle_add(self.fullscreen_btn_pixb.set_from_pixbuf,self.leave_fullscreen_pix)
            gobject.idle_add(self.fullscreen_btn_pixb.set_tooltip_text,_('leave fullscreen'))
        
    def on_drawingarea_realized(self, sender):
        if sys.platform == "win32":
            window = self.movie_window.get_window()
            window.ensure_native()
            self.videosink.set_xwindow_id(self.movie_window.window.handle)
        else:
            gobject.idle_add(self.videosink.set_xwindow_id,self.movie_window.window.xid)

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
        visible =  self.miniPlayer.get_property("visible")
        self.timer = 0
        if self.fullscreen and not self.mini_player and not visible:
            self.show_mini_player()

    def show_mini_player(self):
        self.timer = 0
        visible =  self.miniPlayer.get_property("visible")
        if self.mini_player and visible :
            gobject.idle_add(self.miniPlayer.hide)
            self.mini_player = False
            pixmap = gtk.gdk.Pixmap(None, 1, 1, 1)
            color = gtk.gdk.Color()
            cursor = gtk.gdk.Cursor(pixmap, pixmap, color, color, 0, 0)
            try:
                self.window.window.set_cursor(cursor)
            except:
                return
        else:
            if not visible:
                gobject.idle_add(self.miniPlayer.show)
            self.mini_player = True
            try:
                self.window.window.set_cursor(None)
            except:
                return

    def onKeyPress(self, widget, event):
        if self.search_entry.is_focus():
            return
        key = gtk.gdk.keyval_name(event.keyval)
        if key == 'f':
            return self.set_fullscreen()
        elif key == 'space':
            return self.pause_resume()
        elif key == 's':
            return self.stop_play()
        elif key == 'BackSpace':
            self.search_entry.set_text("")
            return self.search_entry.grab_focus()
        elif key == 'd':
            if self.notebook.get_current_page() == 0:
                gobject.idle_add(self.notebook.set_current_page,1)
                self.notebook.queue_draw()
            else:
                gobject.idle_add(self.notebook.set_current_page,0)

        # If user press Esc button in fullscreen mode
        if event.keyval == gtk.keysyms.Escape and self.fullscreen:
            return self.set_fullscreen()

    def on_volume_changed(self, widget, value=10):
        self.player.set_property("volume", float(value))
        return True

    def download_file(self,widget=None, link=None, name=None, codec=None, data=None, engine_type=None, engine_name=None):
		if not link:
			link = self.active_link
		if not name:
			name = self.media_name
		if not codec:
			codec = self.media_codec 
		download = FileDownloader(self, link, name, codec, data, engine_name, engine_type)
		download.start()
        
    def resume_downloads(self):
        for media in os.listdir(self.down_dir):
            try:
                if '.conf' in media:
                    conf = os.path.join(self.down_dir, media)
                    f = open('''%s''' % conf, 'r')
                    data = f.read()
                    f.close()
                    link = data.split(':::')[0]
                    name = data.split(':::')[1]
                    codec = data.split(':::')[2]
                    engine_type = data.split(':::')[3]
                    engine_name = data.split(':::')[4]
                    print engine_type
                    if str(engine_type) == 'files':
                        self.download_debrid(link)
                    else:
                        self.download_file(None,link, name, codec, None, engine_type, engine_name)
            except:
                continue
                
    def download_debrid(self, link):
        check = self.url_checker.check([link])
        if check != [link]:
            if check[0][1] == 0:
                self.info_label.set_text(_("This link has been removed or is expired...!"))
                return
            link   = check[0][0]
        thread = threading.Thread(target=self.url_debrid.debrid ,args=(link,))
        thread.start()
    
    def bus_message_tag(self, bus, message):
		codec = None
		self.audio_codec = None
		self.media_bitrate = None
		self.mode = None
		self.media_codec = None
		#we received a tag message
		taglist = message.parse_tag()
		self.old_name = self.media_name
		#put the keys in the dictionary
		for key in taglist.keys():
			#print key, taglist[key]
			if key == "preview-image" or key == "image":
				ipath="/tmp/temp.png"
				img = open(ipath, 'w')
				img.write(taglist[key])
				img.close()
				self.media_thumb = gtk.gdk.pixbuf_new_from_file_at_scale(ipath, 64,64, 1)
				self.model.set_value(self.selected_iter, 0, self.media_thumb)
			elif key == "bitrate":
				r = int(taglist[key]) / 1000
				self.file_tags[key] = "%sk" % r
			elif key == "channel-mode":
				self.file_tags[key] = taglist[key]
			elif key == "audio-codec":
				k = str(taglist[key])
				if not self.file_tags.has_key(key) or self.file_tags[key] == '':
					self.file_tags[key] = k
			elif key == "video-codec":
				k = str(taglist[key])
				if not self.file_tags.has_key(key) or self.file_tags[key] == '':
					self.file_tags[key] = k
			elif key == "container-format":
				k = str(taglist[key])
				if not self.file_tags.has_key(key) or self.file_tags[key] == '':
					self.file_tags[key] = k
			#print self.file_tags
		try:
			if self.file_tags.has_key('video-codec') and self.file_tags['video-codec'] != "":
				codec = self.file_tags['video-codec']
			else:
				codec = self.file_tags['audio-codec']
			if codec == "" and self.file_tags['container-format'] != "":
				codec = self.file_tags['container-format']
			if ('MP3' in codec or 'ID3' in codec):
					self.media_codec = 'mp3'
			elif ('XVID' in codec):
					self.media_codec = 'avi'
			elif ('MPEG-4' in codec or 'H.264' in codec or 'MP4' in codec):
					self.media_codec = 'mp4'
			elif ('WMA' in codec or 'ASF' in codec or 'Microsoft Windows Media 9' in codec):
					self.media_codec = 'wma'
			elif ('Quicktime' in codec):
					self.media_codec = 'mov'
			elif ('Vorbis' in codec or 'Ogg' in codec):
					self.media_codec = 'ogg'
			elif ('Sorenson Spark Video' in codec or 'On2 VP6/Flash' in codec):
					self.media_codec = 'flv'
			elif ('VP8' in codec):
				self.media_codec = 'webm'
			self.media_bitrate = self.file_tags['bitrate']
			self.mode = self.file_tags['channel-mode']
			self.model.set_value(self.selected_iter, 1, self.media_markup)
			self.file_tags = tags
		except:
			return
		

    def show_folder(self,path):
        if sys.platform == "win32":
            os.system('explorer %s' % path)
        else:
            os.system('xdg-open %s' % path)

    def on_about_btn_pressed(self, widget):
        dlg = self.gladeGui.get_widget("aboutdialog")
        dlg.set_version(VERSION)
        response = dlg.run()
        if response == gtk.RESPONSE_DELETE_EVENT or response == gtk.RESPONSE_CANCEL:
            dlg.hide()

    def on_settings_btn_pressed(self, widget):
        self.dlg.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        response = self.dlg.run()
        if response == False or response == True or response == gtk.RESPONSE_DELETE_EVENT:
            self.dlg.hide()

    def save_window_state(self):
        try:
            r,s,w,h = self.window.get_allocation()
            self.window.grab_focus()
            self.conf['window_state'] = (w,h,self.x,self.y)
            self.conf.write()
        except:
            return

    def exit(self,widget=None):
        """Stop method, sets the event to terminate the thread's main loop"""
        if self.player.set_state(gst.STATE_PLAYING):
            self.player.set_state(gst.STATE_NULL)
        ## save window state
        self.save_window_state()
        self.manager.stop_all_threads(block=True)
        for th in self.download_pool:
            if not th._stopevent.isSet():
                th.stop()
        self.mainloop.quit()

    def stop_threads(self, *args):
        #THE ACTUAL THREAD BIT
        self.manager.stop_all_threads()

    def add_thread(self, engine, query, page):
        #make a thread and start it
        thread_name = "Search thread %s,%s,%s" % (engine.name, query, page)
        args = (thread_name,self.info_label,engine,query,page,self.throbber,self.stop_search_btn)
        #THE ACTUAL THREAD BIT
        self.manager.make_thread(
                        self.thread_finished,
                        self.thread_progress,
                        *args)

    def thread_finished(self, thread):
        ## check automatic page change
        self.stop_search_btn.set_sensitive(0)
        if len(self.model) > 0:
            self.changepage_btn.set_sensitive(1)
            if self.change_page_request:
                ## wait for 10 seconds or exit
                try:
                    self.selected_iter = self.model.get_iter_first()
                    path = self.model.get_path(self.selected_iter)
                    self.treeview.set_cursor(path)
                    self.get_model()
                    self.change_page_request=False
                except:
                    self.change_page_request=False
                    return
        else:
            self.changepage_btn.set_sensitive(0)
        self.info_label.set_text("")


    def thread_progress(self, thread):
        pass
        
    
    def select_first_media(self):
        ## wait for 10 seconds or exit
        print len(self.model)
        try:
            self.selected_iter = self.model.get_iter_first()
            path = self.model.get_path(self.selected_iter)
            self.treeview.set_cursor(path)
            self.get_model()
        except:
            return
    
    def _show_search_playlist_menu(self,widget,event):
        if event.button == 3:
            self.search_playlist_menu_active = True
            self.search_playlist_menu.show_all()
            self.search_playlist_menu.popup(None, None, None, event.button, event.time)
        
    def _copy_link(self,widget=None,vid=None):
        self.search_playlist_menu_active = False
        link = self.media_link
        if self.search_engine.name == 'Youtube' and not vid:
            link = 'http://www.youtube.com/watch?v=%s' % self.media_link
        clipboard = gtk.Clipboard(gtk.gdk.display_get_default(), "CLIPBOARD")
        clipboard.set_text(link)
        print '%s copied to clipboard' % link
        
    def _add_to_playlist(self,widget):
        self.search_playlist_menu_active = False
        link = self.media_link
        if self.search_engine.name == 'Youtube':
            link = 'http://www.youtube.com/watch?v=%s' % self.media_link
        self.Playlist.add(self.media_name, link, self.active_link, self.media_plugname)
    
    def __create_trayicon(self):
        if gtk.check_version(2, 10, 0) is not None:
            self.log.debug("Disabled Tray Icon. It needs PyGTK >= 2.10.0")
            return
        self.tray = gtk.StatusIcon()
        self.tray.set_from_file(os.path.join(self.img_path,'gmediafinder.png'))
        self.tray.set_tooltip('Gmediafinder')
        self.tray.connect("activate", self.__on_trayicon_click)
        self.tray.connect("popup-menu", self.__show_tray_menu)
  
  
    def __on_trayicon_click(self, widget):
        if(self.showed is True):
            self.showed = False
            self.window.hide()
            self.save_window_state()
        else:
            self.showed = True
            self.window.show()
            self.set_window_position()
  
    def __show_tray_menu(self, widget, button, activate_time):
        menu = gtk.Menu()
        exit_item = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        menu.append(exit_item)
        exit_item.connect('activate', self.exit)
  
        menu.show_all()
        menu.popup(None, None, None, button, activate_time)
        
    def __add_to_history(self):
        search = self.search_entry.get_text()
        c = open(history_file,'r')
        t = c.readlines()
        c.close()
        inlist = False
        for i in t:
            if re.match(search, i.replace('\n','')):
                inlist = True
                break
        if inlist:
            return
        f = open(history_file,'ab')
        if len(t) >= int(max_history):
            del t[1]
            f.writelines(t)
        f.write("%s\n" % search)
        f.close()
    
    def __search_history(self, widget):
        search = self.search_entry.get_text()
        self.history_model.clear()
        for l in open(history_file,'r'):
            try:
                s = re.search('.*%s.*' % search,l).group()
                self.history_model.append([s])
            except:
                pass
    
    def clear_history(self, widget):
        search = self.search_entry.get_text()
        self.history_model.clear()
        f = open(history_file,'w')
        f.write(' ')
        f.close()

  
    def __close(self, widget, event=None):
        if self.minimize == 'on':
            self.showed = False
            self.hide()
            self.save_window_state()
        else:
            self.quit(widget)
        return True


class _IdleObject(gobject.GObject):
    """
    Override gobject.GObject to always emit signals in the main thread
    by emmitting on an idle handler
    """
    def __init__(self):
        gobject.GObject.__init__(self)

    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit,self,*args)

class _FooThread(threading.Thread, _IdleObject):
    """
    Cancellable thread which uses gobject signals to return information
    to the GUI.
    """
    __gsignals__ =  {
            "completed": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
            "progress": (
                gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [])        #percent complete
            }

    def __init__(self, *args):
        threading.Thread.__init__(self)
        _IdleObject.__init__(self)
        self.cancelled = False
        self.engine = args[2]
        self.query = args[3]
        self.page = args[4]
        self.name = args[0]
        self.info = args[1]
        self.throbber = args[5]
        self.stop_btn = args[6]
        self.setName("%s" % self.name)

    def cancel(self):
        """
        Threads in python are not cancellable, so we implement our own
        cancellation logic
        """
        self.cancelled = True

    def run(self):
        #print "Running %s" % str(self)
        gobject.idle_add(self.info.set_text,'')
        self.engine.thread_stop = False
        self.cancelled = False
        url = self.engine.get_search_url(self.query, self.engine.current_page)
        query = urlFetch(self.engine, url, self.query, self.engine.current_page)
        query.start()
        while 1:
            if self.engine.thread_stop == False and not self.cancelled:
                time.sleep(1)
                gobject.idle_add(self.throbber.show)
                gobject.idle_add(self.stop_btn.set_sensitive,1)
                values = {'engine': self.engine.name, 'query': self.query, 'page' : self.page}
                gobject.idle_add(self.info.set_text,_("Searching for %(query)s with %(engine)s (page: %(page)s)") % values)
                self.emit("progress")
            else:
                query.abort()
                self.engine.thread_stop = True
                break
        self.emit("completed")

class FooThreadManager:
    """
    Manages many FooThreads. This involves starting and stopping
    said threads, and respecting a maximum num of concurrent threads limit
    """
    def __init__(self, maxConcurrentThreads):
        self.maxConcurrentThreads = maxConcurrentThreads
        #stores all threads, running or stopped
        self.fooThreads = {}
        #the pending thread args are used as an index for the stopped threads
        self.pendingFooThreadArgs = []
        self.running = 0

    def _register_thread_completed(self, thread, *args):
        """
        Decrements the count of concurrent threads and starts any
        pending threads if there is space
        """
        throbber = args[5]
        del(self.fooThreads[args])
        self.running = len(self.fooThreads) - len(self.pendingFooThreadArgs)

        #print "%s completed. %s running, %s pending" % (thread, self.running, len(self.pendingFooThreadArgs))

        if self.running < self.maxConcurrentThreads:
            try:
                args = self.pendingFooThreadArgs.pop()
                #print "Starting pending %s" % self.fooThreads[args]
                self.fooThreads[args].start()
            except IndexError: pass
        if self.running == 0:
            gobject.idle_add(throbber.hide)

    def make_thread(self, completedCb, progressCb, *args):
        """
        Makes a thread with args. The thread will be started when there is
        a free slot
        """
        self.info = args[1]
        self.engine = args[2]
        self.query = args[3]
        self.page = args[4]
        self.throbber = args[5]
        self.stop_btn = args[6]
        self.running = len(self.fooThreads) - len(self.pendingFooThreadArgs)
        if args not in self.fooThreads:
            thread = _FooThread(*args)
            #signals run in the order connected. Connect the user completed
            #callback first incase they wish to do something
            #before we delete the thread
            thread.connect("completed", completedCb)
            thread.connect("completed", self._register_thread_completed, *args)
            thread.connect("progress", progressCb)
            #This is why we use args, not kwargs, because args are hashable
            self.fooThreads[args] = thread

            if self.running < self.maxConcurrentThreads:
                #print "Starting %s" % thread
                gobject.idle_add(self.throbber.show)
                gobject.idle_add(self.stop_btn.set_sensitive,1)
                self.fooThreads[args].start()
                values = {'engine': self.engine.name, 'query': self.query, 'page' : self.page}
                gobject.idle_add(self.info.set_text,_("Searching for %(query)s with %(engine)s (page: %(page)s)") % values)
            else:
                #print "Queing %s" % thread
                self.pendingFooThreadArgs.append(args)

    def stop_all_threads(self, block=False):
        """
        Stops all threads. If block is True then actually wait for the thread
        to finish (may block the UI)
        """
        for thread in self.fooThreads.values():
            thread.cancel()
            if block:
                if thread.isAlive():
                    thread.join()
                    


if __name__ == "__main__":
    app = GsongFinder()
    try:
        app.mainloop.run()
    except KeyboardInterrupt, errmsg:
        app.exit()
