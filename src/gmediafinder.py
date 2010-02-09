#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import sys, os, thread, threading, time
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
        gtk.gdk.threads_init()
        self.media_name = ""
        self.media_link = ""
        self.nbresults = 100
        self.user_search = ""
        self.down_dir = os.path.join(os.getenv('HOME'),"gmediafinder-downloads")
        self.engine_list = {'woonz.com':'','google.com':'','skreemr.com':'','findmp3s.com':''}
        self.engine = None
        self.search_option = "song_radio"
        self.banned_sites = ['worxpress','null3d','audiozen']
        self.search_requests = {'song_radio':'"Parent directory" (mp3 OR wma OR ogg OR wav OR mp4 OR aac) -html -htm -php -Bitrate',
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
        }
        self.gladeGui.signal_autoconnect(dic)
        self.window.connect('destroy', self.exit)
        
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
    
    def set_engine(self,widget=None):
        self.engine = self.engine_selector.get_active_text()
        self.changepage_btn.hide()
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
        
    def prepare_search(self,widget=None):
        self.search_thread_id = None
        self.user_search = self.search_entry.get_text()
        if not self.user_search:
            self.informations_label.set_text("Please enter an artist/album or song name...")
            return
        if not self.engine:
            self.informations_label.set_text("Please select an engine...")
            return
        self.main_engine = self.engine_selector.get_active_text()
        self.reset_pages()
        
        return self.get_page_links()
        
    def change_page(self,widget):
        user_search = self.search_entry.get_text()
        engine = self.engine_selector.get_active_text()
        if not user_search or user_search != self.user_search \
        or not engine or engine != self.main_engine:
            self.reset_pages()
            return self.prepare_search()
        else:
            return self.get_page_links()
        
    def reset_pages(self):
        self.changepage_btn.hide()
        if self.engine == "woonz.com":
            self.req_start = 1
        elif self.engine == "findmp3s.com":
            self.req_start = 1
        elif self.engine == "skreemr.com":
            self.req_start = 10
            self.page = 1
            
    ## main search to receive original search when requesting next pages...
    def get_page_links(self,widget=None):
        self.url = self.search()
        self.data = self.get_url_data(self.url)
        self.start_search()
        
    def search(self):
        self.model.clear()
        self.informations_label.set_text("Searching for %s with %s " % (self.user_search,self.engine))
        ## encode the name
        user_search = urllib2.quote(self.user_search)
        ## prepare the request
        if self.engine == None:
            self.informations_label.set_text("Please select a search engine...")
            return
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
        return url

    def get_url_data(self,url):
        user_agent =  'Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.2) Gecko/20100124 Ubuntu/9.10 (karmic) Firefox/3.6'
        headers =  { 'User-Agent' : user_agent , 'Accept-Language' : 'en-us' }
        ## start the request
        try:
            req = urllib2.Request(url,None,headers)
        except:
            return
        try:
            handle = urllib2.urlopen(req)
        except:
            return
        results = handle.read()
        return results
        
    def analyse_links(self):
        data = self.data
        url = self.url
        search_thread_id = self.search_thread_id
        gtk.gdk.threads_enter()
        self.informations_label.set_text("Searching for %s with %s" % (self.user_search,self.engine))
        gtk.gdk.threads_leave()
        time.sleep(0.2)
        
        if data:
            soup = BeautifulSoup(''.join(data))
            if self.engine == "google.com":
                while search_thread_id == self.search_thread_id:
                    try:
                        time.sleep(0.2)
                        alist = soup.findAll('a', href=True)
                        for a in alist:
                            url = a.attrMap['href']
                            if not url: continue
                            if re.search('href="(\S.*>Index of)', a.__str__()):
                                self.informations_label.set_text("Media files detected on : %s, scanning... " % (urllib2.unquote(url)))
                                verified_links = self.check_google_links(url)
                                if verified_links:
                                    slist = verified_links.findAll('a', href=True)
                                    ## if ok start the loop
                                    gtk.gdk.threads_enter()
                                    for s in slist:
                                        self.informations_label.set_text("Sound : %s" % s.string)
                                        print "scanning webpage : %s" % s.string
                                        try:
                                            req = re.search('(.*%s.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv)' % self.user_search.lower(), urllib2.unquote(s.__str__().lower())).group(1,2)
                                        except:
                                            continue 
                                        link = (url + s.attrMap['href'])
                                        name = urllib2.unquote(os.path.basename(link))
                                        self.add_sound(name, link)
                                    gtk.gdk.threads_leave()
                                else:
                                    continue
                            
                            self.search_thread_id = None
                    except:
                        pass
                self.informations_label.set_text("Scan terminated for your request : %s" % self.user_search)
            
            elif self.engine == "woonz.com":
                ## reset the treeview
                nlist = []
                link_list = []
                txt = soup.findAll('td')[0].__str__()
                try:
                    files_count = re.search('(([0-9]{1,})([^audio & music]))', txt).group()
                except:
                    self.informations_label.set_text("no results found for %s..." % (self.user_search))
                    self.search_thread_id = None
                    return
                
                self.informations_label.set_text("%s files found for %s" % (files_count, self.user_search))
                if re.search(r'(\S*no result found)', soup.__str__()):
                    self.changepage_btn.hide()
                    self.req_start = 1
                    self.informations_label.set_text("no more files found for %s..." % (self.user_search))
                    self.search_thread_id = None
                    return
                else:
                    self.informations_label.set_text("Results page %s for %s...(%s results)" % (self.req_start, self.user_search,files_count))
                    self.req_start += 1
                        
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
                ## l = ? and s = pages (10 results by page...)
                nlist = []
                link_list = []
                
                pagination_table = soup.findAll('table',attrs={'class':'pagination'})[0]
                if pagination_table:
                    next_check = pagination_table.findAll('a')
                    for a in next_check:
                        l = str(a.string)
                        if l == "Next":
                            next_page = 1
                    if next_page:
                        self.informations_label.set_text("Results page %s for %s...(Next page available)" % (self.req_start, self.user_search))
                        self.req_start += 1
                        self.changepage_btn.show()
                    else:
                        self.changepage_btn.hide()
                        self.req_start = 1
                        self.informations_label.set_text("no more files found for %s..." % (self.user_search))
                        self.search_thread_id = None
                        return
                
                alist = soup.findAll('a',href=True)
                for a in alist:
                    link = a.attrMap['href']
                    print link
                    try:
                        t = re.search('download.php\?name=(.*.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv)', link.lower()).group(1)
                        name = urllib2.unquote(t)
                        nlist.append(name)
                        link_list.append(link)
                    except:
                        pass
                ## add to the treeview if ok
                i = 0
                for name in nlist:
                    if name and link_list[i]:
                        self.add_sound(name, link_list[i])
                        i += 1
            
            elif self.engine == "skreemr.com":
                ## l = ? and s = pages (10 results by page...)
                nlist = []
                link_list = []
                
                files_count = soup.findAll('div',attrs={'class':'results'})[0]
                if files_count:
                    files_count = files_count.findAll('b')[1].string
                    self.informations_label.set_text("%s files found for %s" % (files_count, self.user_search))
                    if re.search(r'(\S*No results)', files_count.__str__()):
                        self.changepage_btn.hide()
                        self.req_start = 10
                        self.page = 1
                        self.informations_label.set_text("no more files found for %s..." % (self.user_search))
                        self.search_thread_id = None
                        return
                    else:
                        self.informations_label.set_text("Results page %s for %s...(%s results)" % (self.page, self.user_search,files_count))
                        self.req_start += 10
                        self.page += 1
                        self.changepage_btn.show()
                
                alist = soup.findAll('a',attrs={'class':'snap_noshots'})
                for a in alist:
                    link = a.attrMap['href']
                    print link
                    try:
                        t = re.search('(\S.*)(.mp3|.mp4|.ogg|.aac|.wav)', link.lower())
                        link =  ''.join(t.group(1,2))
                        name = urllib2.unquote(os.path.basename(link))
                        nlist.append(name)
                        link_list.append(link)
                    except:
                        pass
                ## add to the treeview if ok
                i = 0
                for name in nlist:
                    if name and link_list[i]:
                        self.add_sound(name, link_list[i])
                        i += 1
        
    def check_google_links(self,url):
        ## test the link for audio file on first scan
        subreq = self.get_url_data(url)
        try:
            subsoup = BeautifulSoup(''.join(subreq))
        except:
            return
        ## first check if content is readeable
        try:
            name = re.search('href="(\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv)"', urllib2.unquote(subsoup.__str__().lower())).group(1,2)
        except:
            return
        original_name = req = re.search('href="(\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv)"', urllib2.unquote(subsoup.__str__())).group(1,2)
        file = ''.join(original_name)
        print "file to test content-type: %s" % file
        try:
            coded_name = urllib2.quote(file)
            coded_link = os.path.join(url, coded_name)
            print coded_link
            req = urllib.urlopen(coded_link)
            req.close()
        except:
            return
        ## test headers
        type = req.headers.get("content-type")
        
        if re.search('audio', type):
            print "%s type detected ok, sounds from this website added to the playlist" % type
            return subsoup
        else:
            print "wrong media type %s, link to another webpage...website rejected" % type
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
    
    def search_thread(self):
        search_thread_id = self.search_thread_id
        gtk.gdk.threads_enter()
        self.informations_label.set_text("Searching...")
        gtk.gdk.threads_leave()
        time.sleep(0.2)
        while search_thread_id == self.search_thread_id:
            if search_thread_id == self.search_thread_id:
                try:
                    gtk.gdk.threads_enter()
                    print "here"
                    gtk.gdk.threads_leave()
                    time.sleep(0.2)
                except: 
                    break
                
    def start_search(self):
        self.search_thread_id = thread.start_new_thread(self.analyse_links, ())
    
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
                dur_int = self.player.query_duration(self.time_format, None)[0]
                if dur_int == -1:
                    dur_str = "unknown"
                else:
                    dur_str = self.convert_ns(dur_int)
                self.time_label.set_text("00:00 / 00:00")
                time.sleep(0.2)
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
        gtk.main_iteration()
        urllib.urlretrieve(url, self.down_dir+"/"+self.media_name,
        lambda nb, bs, fs, url=url: _reporthook(nb,bs,fs,url,self.media_name,self.progressbar))
        self.progressbar.hide()
        
    def exit(self,widget):
        gtk.main_quit()

def _reporthook(numblocks, blocksize, filesize, url, name, progressbar):
        #print "reporthook(%s, %s, %s)" % (numblocks, blocksize, filesize)
        #XXX Should handle possible filesize=-1.
        if filesize == -1:
            progressbar.set_text("Downloading %-66s" % name)
            progressbar.pulse()
            time.sleep(0.005)
            gtk.main_iteration()
        else:
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

