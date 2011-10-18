#-*- coding: UTF-8 -*-
#
# gmediafinder's player gui package
import gtk


## custom lib
try:
    from config import *
    from functions import *
except:
    from GmediaFinder.config import *
    from GmediaFinder.functions import *


class PlayerGui(object):
    def __init__(self,mainGui):
        self.mainGui = mainGui
        self.gladeGui = gtk.glade.XML(glade_file, None ,APP_NAME)
        self.duration = None
        self.time_label = gtk.Label("00:00 / 00:00")
        self.media_name = ""
        self.media_link = ""
        
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
        # volume
        self.volume_btn = self.gladeGui.get_widget("volume_btn")
        
        ## SIGNALS
        dic = {
        "on_pause_btn_clicked" : self.pause_resume,
        "on_shuffle_btn_toggled" : self.set_play_options,
        "on_repeat_btn_toggled" : self.set_play_options,
        "on_vol_btn_value_changed" : self.on_volume_changed,
         }
         self.gladeGui.signal_autoconnect(dic)
         
