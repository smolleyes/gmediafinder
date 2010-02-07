#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import sys, os, thread, time
import gobject
import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import urllib
import urllib2
import socket
import pygst
pygst.require("0.10")
import gst
import re

from BeautifulSoup import BeautifulSoup

## custom lib
import constants

gtk.gdk.threads_init()

# timeout in seconds
timeout = 10
socket.setdefaulttimeout(timeout)

class GsongFinder(object):
    def __init__(self):
        ## default search options
        self.media_name = ""
        self.media_link = ""
        self.nbresults = 100
        self.req_start = 1
        self.user_search = ""
        self.down_dir = os.path.join(os.getenv('HOME'),"gmediafinder-downloads")
        self.engine_list = {'woonz.com':'','google.com':'','skreemr.com':'','findmp3s.com':''}
        self.engine = None
        self.search_option = "song_radio"
        self.banned_sites = ['worxpress','null3d','audiozen']
        self.search_requests = {'song_radio':'"parent directory" (mp3|wma|ogg|wav|mp4|aac) -html -htm -pl -php -asp -pls -m3u -downloads -links',
                                'video_radio' : 'intitle:index.of   "Parent directory"   "Last modified" "Description"  "Size" (avi|ogv|mpg|mpeg|wmv|mp4) -html -htm -php -asp -txt -pls',
                                'img_radio':'intitle:index.of   "Parent directory"   "Last modified" "Description"  "Size" (png|jpeg|jpg|svg|gif) -html -htm -php -asp -txt -pls',
                                }
        ## small config dir for downloads...
        if not os.path.exists(self.down_dir):
            os.mkdir(self.down_dir)
        ## gui
        self.gladeGui = gtk.glade.XML(constants.glade_file, None ,constants.app_name)
        self.window = self.gladeGui.get_widget("main_window")
        self.window.set_title("Gmediafinder")
        self.window.set_resizable(1)
        self.window.set_default_size(600, 600)
        self.window.set_position("center")
        
        ## informations
        self.informations_label = self.gladeGui.get_widget("info_label")
        
        ## search options
        self.options_box = self.gladeGui.get_widget("options_box")
        self.option_songs = self.gladeGui.get_widget("song_radio")
        self.option_videos = self.gladeGui.get_widget("video_radio")
        self.option_songs.set_active(True)
        self.option_images = self.gladeGui.get_widget("img_radio")
        ## engine selector (engines only with direct links)
        self.engine_selector = self.gladeGui.get_widget("engine_selector")
        self.engine_selector.set_active(0)
        for engine in self.engine_list:
            self.engine_selector.append_text(engine)
        
        ## control section
        self.play_btn = self.gladeGui.get_widget("play_btn")
        self.pause_btn = self.gladeGui.get_widget("pause_btn")
        self.volume_btn = self.gladeGui.get_widget("volume_btn")
        self.play_btn.connect('clicked', self.start_stop)
        self.time_label = self.gladeGui.get_widget("time_label")
        self.time_label.set_text("00:00 / 00:00")
        self.down_btn = self.gladeGui.get_widget("down_btn")
        ## search bar
        self.search_entry = self.gladeGui.get_widget("search_entry")
        self.search_btn = self.gladeGui.get_widget("search_btn")
        self.changepage_btn = self.gladeGui.get_widget("changepage_btn")
        
        ## statbar
        self.statbar = self.gladeGui.get_widget("statusbar")
        
        # progressbar
        self.progressbar = self.gladeGui.get_widget("progressbar")
        
        ## SIGNALS
        dic = {"on_main_window_destroy" : gtk.main_quit,
        "on_song_radio_toggled" : self.option_changed,
        "on_video_radio_toggled" :  self.option_changed,
        "on_img_radio_toggled" :  self.option_changed,
        "on_search_btn_clicked" : self.get_page_links,
        "on_engine_selector_changed" : self.set_engine,
        "on_quit_menu_activate" : gtk.main_quit,
        "on_pause_btn_clicked" : self.pause_resume,
        "on_down_btn_clicked" : self.download_file,
        "on_changepage_btn_clicked" : self.get_page_links,
        }
        self.gladeGui.signal_autoconnect(dic)
        self.window.connect('destroy', gtk.main_quit)
        
        ## finally setup the list
        self.model = gtk.ListStore(str,str)
        self.treeview = gtk.TreeView()
        self.treeview.set_model(self.model)
        renderer = gtk.CellRendererText()
        titleColumn = gtk.TreeViewColumn("Name", renderer, text=0)
        titleColumn.set_min_width(200)
        pathColumn = gtk.TreeViewColumn("Link", renderer, text=0)

        self.treeview.append_column(titleColumn)
        self.treeview.append_column(pathColumn)

        ## setup the scrollview
        self.results_scroll = self.gladeGui.get_widget("results_scrollbar")
        self.columns = self.treeview.get_columns()
        self.columns[0].set_sort_column_id(1)
        self.columns[1].set_visible(0)
        self.results_scroll.add(self.treeview)
        ## connect treeview signals 
        self.treeview.connect('cursor-changed',self.get_model)
        
        ## create the player
        
        self.player = gst.element_factory_make("playbin2", "player")
        sink = gst.element_factory_make("autoaudiosink")
        self.player.set_property("audio-sink", sink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        ## time
        self.time_format = gst.Format(gst.FORMAT_TIME)
        
        ## start gui
        self.window.show_all()
        self.progressbar.hide()
        self.changepage_btn.hide()
        ## start main loop
        gtk.main()
    
    def set_engine(self,widget):
        self.engine = self.engine_selector.get_active_text()
        iter = self.engine_selector.get_active_iter()
        if self.engine == "Select an engine":
            self.engine = None
            return
        print "%s engine selected" % self.engine
        
    def get_model(self,widget):
        selected = self.treeview.get_selection()
        self.iter = selected.get_selected()[1]
        ## else extract needed metacity's infos
        self.media_name = self.model.get_value(self.iter, 0)
        ## return only theme name and description then extract infos from hash
        self.media_link = self.model.get_value(self.iter, 1)
        # print in the gui
        self.statbar.push(1,"Selected media : %s" % self.media_name)
        self.start_stop()
    
    def option_changed(self,widget):
        self.search_option = widget.name
        
    def get_page_links(self,widget=None):
        url = self.search()
        link_liste = self.analyse_links(url)
        if link_liste:
            ## start scanning files
            if self.search_option == "song_radio":
                self.search_songs(link_liste)
        
    def search(self):
        self.user_search = self.search_entry.get_text()
        self.informations_label.set_text("Searching for %s with %s " % (self.user_search,self.engine))
        if self.user_search:
            ## encode the name
            user_search = urllib2.quote(self.user_search)
            ## prepare the request
            if self.engine == None:
                self.informations_label.set_text("Please select a search engine...")
                return
            gtk.main_iteration()
            urlopt = ""
            baseurl = ""
            if self.engine == "google.com":
                baseurl = "http://www.google.com/search?hl=en&num=100&q="
                urlopt = urllib.quote(self.search_requests[self.search_option]) +'%20'+user_search
                url = baseurl + urlopt
            elif self.engine == "woonz.com":
                url = "http://woonz.com/mp3.php?q=%s&s=1&p=%s" % (user_search,self.req_start)
            elif self.engine == "findmp3s.com":
                url = "http://findmp3s.com/search/mp3/%s/%s.html" % (self.req_start,user_search)
            elif self.engine == "skreemr.com":
                ## l= ? and s = pages (10 results by page...)
                url = "http://skreemr.com/results.jsp?q=%s&l=10&s=%s" % (user_search,self.req_start)
            
            print url
            ## 1 for first resquest to not test content type
            return self.get_url_data(url,1)
        else:
            self.informations_label.set_text("Please enter some text to search...")
            return
            
    def get_url_data(self,url,base=None):
        gtk.main_iteration()
        user_agent =  'Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.2) Gecko/20100124 Ubuntu/9.10 (karmic) Firefox/3.6'
        headers =  { 'User-Agent' : user_agent , 'Accept-Language' : 'en-us' }
        ## start the request
        try:
            req = urllib2.Request(url,None,headers)
            gtk.main_iteration()
        except:
            return
        try:
            handle = urllib2.urlopen(req)
            gtk.main_iteration()
        except:
            return
        results = handle.read()
            
        if results:
            gtk.main_iteration()
            ## test the link for audio file on first scan
            if not base and self.engine == "google.com":
                try:
                    t = re.search('href="(\S.*)(.mp3|.mp4|.ogg|.aac|.wav)"', results).group(1,2)
                except:
                    return
                if t:
                    ## test the file for audio type
                    print "testing content type..."
                    file = ''.join(t)
                    try:
                        req = urllib.urlopen(url + '/' + file)
                        req.close()
                    except:
                        return
                    
                    type = req.headers.get("content-type")

                    if re.search('audio', type):
                        print "%s type detected ok, sounds from this website added to the playlist" % type
                        return results
                    else:
                        print "wrong media type %s, link to another webpage...website rejected" % type
                        return
            return results
        
    def analyse_links(self,data):
        liste = []
        if data:
            soup = BeautifulSoup(''.join(data))
            if self.engine == "google.com":
                alist = soup.findAll('a', href=True)
                for a in alist:
                    value = a.attrMap['href']
                    if re.search(r'\bIndex of\b', a.__str__()):
                        liste.append(value)
                if len(liste) > 0:
                    return liste
            elif self.engine == "woonz.com":
                ## reset the treeview
                nlist = []
                link_list = []
                txt = soup.findAll('td')[0].__str__()
                files_count = re.search('(([0-9]{1,})([^audio & music]))', txt).group()
                if files_count:
                    self.informations_label.set_text("%s files found for %s" % (files_count, self.user_search))
                    ## check if there s some results since pagination system sucks...
                    if re.search(r'(\S*no result found)', soup.__str__()):
                        self.changepage_btn.hide()
                        self.req_start = 1
                        self.informations_label.set_text("no more files found for %s..." % (self.user_search))
                        return
                    else:
                        self.informations_label.set_text("Results page %s for %s..." % (self.req_start, self.user_search))
                        self.req_start += 1 
                        
                self.model.clear()
                self.changepage_btn.show()
                alist = soup.findAll('a',href=True)
                #count_req = soup.findAll('td',attrs{'align':'left'})
                #print count_req
                for a in alist:
                    name = None
                    link = None
                    #print a.attrs
                    #print dir(a)
                    
                    ## search songg class for name
                    if a.has_key('class'):
                        if a['class'] == "songg":
                            name = str(a.next.string).strip()
                            nlist.append(name)
                    ## row for download is Download...
                    if a.string == "Download":
                        l = a.attrs[0][1]
                        link = "http://www.woonz.com/" + l
                        link_list.append(link)
                ## add to the treeview if ok
                i = 0
                for name in nlist:
                    if name and link_list[i]:
                        self.add_sound(name, link_list[i])
                        i += 1
                    
            elif self.engine == "findmp3s.com":
                print value
            elif self.engine == "skreemr.com":
                ## l = ? and s = pages (10 results by page...)
                ## reset the treeview
                self.model.clear()
                nlist = []
                link_list = []
                files_count = soup.findAll('div',attrs={'class':'results'})[0]
                if files_count:
                    files_count = files_count.findAll('b')[1].string
                    self.informations_label.set_text("%s files found for %s" % (files_count, self.user_search))
                    if files_count > 10:
                        self.changepage_btn.show()
                alist = soup.findAll('a',attrs={'class':'snap_noshots'})
                for a in alist:
                    link = a.attrMap['href']
                    try:
                        t = re.search('(\S.*)(.mp3|.mp4|.ogg|.aac|.wav)', link.lower())
                        link =  ''.join(t.group(1,2))
                        name = urllib2.unquote(os.path.basename(link))
                        nlist.append(name)
                        link_list.append(link)
                        gtk.main_iteration()
                    except:
                        pass
                ## add to the treeview if ok
                i = 0
                for name in nlist:
                    if name and link_list[i]:
                        self.add_sound(name, link_list[i])
                        i += 1

            
    def search_songs(self,liste):
        self.model.clear()
        for url in liste:
            self.informations_label.set_text("Searching for %s on page :\n%s" % (self.user_search,url))
            gtk.main_iteration()
            data = self.get_url_data(url)
            if data:
                try:
                    soup = BeautifulSoup(''.join(data))
                except:
                    pass
                alist = soup.findAll('a', href=True)
                for ref in alist:
                    gtk.main_iteration()
                    value = ref.attrMap['href']
                    exp_reg = re.compile("(.mp3|.mp4|.ogg|.aac|.wav)$")
                    if re.search(exp_reg, value) and re.search(self.user_search, value.lower()):
                        link = os.path.join(url,value)
                        name = os.path.basename(link)
                        name = urllib.unquote(name)
                        self.add_sound(name,link)

        self.informations_label.set_text("Search terminated for %s" % self.user_search)
        return
    
    def add_sound(self, name, link):
        self.iter = self.model.append()
        self.model.set(self.iter,
                       0, name,
                       1, link,
                       )
    
    def search_videos(self,liste):
        self.model.clear()
        for url in liste:
            data = self.get_url_data(url)
            if data:
                try:
                    soup = BeautifulSoup(''.join(data))
                except:
                    continue
                alist = soup.findAll('a', href=True)
                for ref in alist:
                    value = ref.attrMap['href']
                    value = urllib.unquote(value)
                    exp_reg = re.compile("(.avi|.mpg|.mpeg|.wmv|.mp4|.mkv)$")
                    if re.search(exp_reg, value):
                        link = os.path.join(url,value)
                        name = os.path.basename(link)
                        self.iter = self.model.append()
                        self.model.set(self.iter,
                                        0, name,
                                        1, link,
                                        )
        return
    
    def start_stop(self,widget=None):
        url = self.media_link
        if url:
            if self.play_btn.get_label() == "gtk-media-play":
                self.play_btn.set_label("gtk-media-stop")
                self.player.set_property("uri", url)
                self.player.set_state(gst.STATE_PLAYING)
                self.play_thread_id = thread.start_new_thread(self.play_thread, ())
            else:
                self.play_thread_id = None
                self.player.set_state(gst.STATE_NULL)
                self.play_btn.set_label("gtk-media-play")
                self.time_label.set_text("00:00 / 00:00")

    def play_thread(self):
        play_thread_id = self.play_thread_id
        gtk.gdk.threads_enter()
        self.time_label.set_text("00:00 / 00:00")
        gtk.gdk.threads_leave()

        while play_thread_id == self.play_thread_id:
            try:
                time.sleep(0.2)
                dur_int = self.player.query_duration(self.time_format, None)[0]
                dur_str = self.convert_ns(dur_int)
                gtk.gdk.threads_enter()
                self.time_label.set_text("00:00 / " + dur_str)
                gtk.gdk.threads_leave()
                break
            except:
                pass
                
        time.sleep(0.2)
        while play_thread_id == self.play_thread_id:
            pos_int = self.player.query_position(self.time_format, None)[0]
            pos_str = self.convert_ns(pos_int)
            if play_thread_id == self.play_thread_id:
                gtk.gdk.threads_enter()
                self.time_label.set_text(pos_str + " / " + dur_str)
                gtk.gdk.threads_leave()
            time.sleep(1)
            
    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.play_thread_id = None
            self.player.set_state(gst.STATE_NULL)
            self.play_btn.set_label("gtk-media-play")
            self.time_label.set_text("00:00 / 00:00")
        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.play_thread_id = None
            self.player.set_state(gst.STATE_NULL)
            self.play_btn.set_label("gtk-media-play")
            self.time_label.set_text("00:00 / 00:00")
            
    def pause_resume(self,widget):
        if self.pause_btn.get_label() == "gtk-media-pause":
                self.pause_btn.set_label("gtk-media-play")
                self.player.set_state(gst.STATE_PAUSED)
        else:
            self.pause_btn.set_label("gtk-media-pause")
            self.player.set_state(gst.STATE_PLAYING)
            
    def convert_ns(self, time_int):
        time_int = time_int / 1000000000
        time_str = ""
        if time_int >= 3600:
            _hours = time_int / 3600
            time_int = time_int - (_hours * 3600)
            time_str = str(_hours) + ":"
        if time_int >= 600:
            _mins = time_int / 60
            time_int = time_int - (_mins * 60)
            time_str = time_str + str(_mins) + ":"
        elif time_int >= 60:
            _mins = time_int / 60
            time_int = time_int - (_mins * 60)
            time_str = time_str + "0" + str(_mins) + ":"
        else:
            time_str = time_str + "00:"
        if time_int > 9:
            time_str = time_str + str(time_int)
        else:
            time_str = time_str + "0" + str(time_int)
            
        return time_str
    
    
    
    def download_file(self,widget):
        print "downloading %s" % self.media_link
        return self.geturl(self.media_link)

    def geturl(self,url):
        self.progressbar.show()
        urllib.urlretrieve(url, self.down_dir+"/"+self.media_name,
        lambda nb, bs, fs, url=url: _reporthook(nb,bs,fs,url,self.media_name,self.progressbar))
            

def _reporthook(numblocks, blocksize, filesize, url, name, progressbar):
        #print "reporthook(%s, %s, %s)" % (numblocks, blocksize, filesize)
        #XXX Should handle possible filesize=-1.
        if numblocks != 0:
            try:
                percent = min((numblocks*blocksize*100)/filesize, 100)
            except:
                percent = 100
            if percent < 100:
                time.sleep(0.005)
                progressbar.set_text("Downloading %-66s%3d%% done" % (name, percent))
                progressbar.set_fraction(percent/100.0)
                gtk.main_iteration_do(False)
            else:
                progressbar.hide()
                return
        return

if __name__ == "__main__":
    GsongFinder()
    gtk.main()

