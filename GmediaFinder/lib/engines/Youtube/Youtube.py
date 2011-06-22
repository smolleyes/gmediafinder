import re
import urllib
import gdata.youtube.service as yt_service
import gobject

try:
    from functions import *
    from functions import download_photo
    from functions import ComboBox
    from functions import sortDict
except:
    from GmediaFinder.functions import *
    from GmediaFinder.functions import download_photo
    from GmediaFinder.functions import ComboBox
    from GmediaFinder.functions import sortDict

class Youtube(object):
    def __init__(self,gui):
        self.gui = gui
        self.current_page = 1
        self.main_start_page = 1
        self.type = "video"
        self.num_start = 1
        self.results_by_page = 25
        self.name="Youtube"
        self.client = yt_service.YouTubeService()
        self.youtube_max_res = "320x240"
        self.media_codec = None
        self.thread_stop= False
        ## the gui box to show custom filters/options
        self.opt_box = self.gui.gladeGui.get_widget("search_options_box")
        
        ## options labels
        self.order_label = _("Order by: ")
        self.category_label = _("Category: ")
        ## video quality combobox
        self.youtube_quality_box = self.gui.gladeGui.get_widget("quality_box")
        self.youtube_quality_model = gtk.ListStore(str)
        self.youtube_video_rate = gtk.ComboBox(self.youtube_quality_model)
        cell = gtk.CellRendererText()
        self.youtube_video_rate.pack_start(cell, True)
        self.youtube_video_rate.add_attribute(cell, 'text', 0)
        self.youtube_quality_box.add(self.youtube_video_rate)
        new_iter = self.youtube_quality_model.append()
        self.youtube_quality_model.set(new_iter,
                                0, _("Quality"),
                                )
        self.youtube_video_rate.connect('changed', self.on_youtube_video_rate_changed)

        ## youtube video quality choices
        self.res320 = self.gui.gladeGui.get_widget("res1")
        self.res640 = self.gui.gladeGui.get_widget("res2")
        self.res854 = self.gui.gladeGui.get_widget("res3")
        self.res1280 = self.gui.gladeGui.get_widget("res4")
        self.res1920 = self.gui.gladeGui.get_widget("res5")

        ## SIGNALS
        dic = {
        "on_res1_toggled" : self.set_max_youtube_res,
        "on_res2_toggled" : self.set_max_youtube_res,
        "on_res3_toggled" : self.set_max_youtube_res,
        "on_res4_toggled" : self.set_max_youtube_res,
        "on_res5_toggled" : self.set_max_youtube_res,
         }
        self.gui.gladeGui.signal_autoconnect(dic)
        ## start
        self.start_engine()

    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)

    def start_engine(self):
        self.gui.engine_list[self.name] = ''
        ## get default max_res for youtube videos
        try:
            self.youtube_max_res = self.gui.conf["youtube_max_res"]
        except:
            self.gui.conf["youtube_max_res"] = self.youtube_max_res

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

        self.youtube_video_rate.hide()
        self.youtube_video_rate.set_active(0)

    def load_gui(self):
        ## create orderby combobox
        cb = create_comboBox()
        self.orderbyOpt = {self.order_label:{_("Most relevant"):"relevance",
                                             _("Most recent"):"published",_("Most viewed"):"viewCount",
                                             _("Most rated"):"rating",
            },
        }
        self.orderby = create_comboBox(self.gui, self.orderbyOpt)
        
        ## create categories combobox
        self.category = ComboBox(cb)
        self.catlist = {self.category_label:{"":"",_("Sport"):"Sports",
                                             _("Films"):"Film",_("Cars"):"Autos",
                                             _("Music"):"Music",_("Technology"):"Tech",_("Animals"):"Animals",
                                             _("Travel"):"Travel",_("Games"):"Games",_("Comedy"):"Comedy",
                                             _("Peoples"):"People",_("News"):"News",
                                             _("Entertainement"):"Entertainment",_("Trailers"):"Trailers",
            },
        }
        self.category = create_comboBox(self.gui, self.catlist)
        self.orderby.setIndexFromString(_("Most relevant"))

    def set_max_youtube_res(self, widget):
        if widget.get_active():
            self.youtube_max_res = widget.get_child().get_label()
            self.gui.conf["youtube_max_res"] = self.youtube_max_res
            ## return a dic as conf
            try:
                self.gui.conf.write()
            except:
                print "Can't write to the %s config file..." % self.gui.conf_file

    def search(self,user_search,page):
        self.thread_stop=False
        nlist = []
        link_list = []
        next_page = 0
        ## prepare query
        query = yt_service.YouTubeVideoQuery()
        query.vq = user_search # the term(s) that you are searching for
        query.max_results = '25'
        #query.lr = 'fr'
        orderby = self.orderby.getSelected()
        query.orderby = self.orderbyOpt[self.order_label][orderby]
        cat = self.category.getSelected()
        if self.category.getSelectedIndex() != 0:
            query.categories.append('/%s' % self.catlist[self.category_label][cat])

        if self.current_page == 1:
            self.num_start = 1
        query.start_index = self.num_start
        vquery = self.client.YouTubeQuery(query)
        self.filter(vquery,user_search)

    def filter(self,vquery,user_search):
        if not vquery :
            self.num_start = 1
            self.current_page = 1
            self.print_info(_("%s: No results for %s ...") % (self.name,user_search))
            time.sleep(5)
            self.thread_stop=True

        if len(vquery.entry) == 0:
            self.print_info(_("%s: No results for %s ...") % (self.name,user_search))
            time.sleep(5)
            self.thread_stop=True

        for entry in vquery.entry:
            if not self.thread_stop:
                self.make_youtube_entry(entry)
            else:
                return
        self.thread_stop=True

    def play(self,link):
        self.load_youtube_res(link)
        active = self.youtube_video_rate.get_active()
        self.media_codec = self.quality_list[active].split('|')[1]
        return self.gui.start_play(self.media_link[active])

    def make_youtube_entry(self,video):
        duration = video.media.duration.seconds
        calc = divmod(int(duration),60)
        seconds = int(calc[1])
        if seconds < 10:
            seconds = "0%d" % seconds
        duration = "%d:%s" % (calc[0],seconds)
        url = video.link[1].href
        thumb = video.media.thumbnail[-1].url
        count = 0
        try:
            count = video.statistics.view_count
        except:
            pass
        vid_id = os.path.basename(os.path.dirname(url))
        vid_pic = download_photo(thumb)
        title = video.title.text
        if not count:
            count = 0

        values = {'name': title, 'count': count, 'duration': duration}
        markup = _("\n<small><b>view:</b> %(count)s        <b>Duration:</b> %(duration)s</small>") % values
        if not title or not url or not vid_pic:
            return
        gobject.idle_add(self.gui.add_sound,title, vid_id, vid_pic,None,self.name,markup)


    def load_youtube_res(self,link):
        gobject.idle_add(self.youtube_quality_model.clear)
        self.media_link,self.quality_list = self.get_quality_list(link)
        if not self.quality_list:
            return
        for rate in self.quality_list:
            new_iter = self.youtube_quality_model.append()
            self.youtube_quality_model.set(new_iter,
                            0, rate,
                            )
        self.set_default_youtube_video_rate()
        gobject.idle_add(self.youtube_video_rate.show)

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
                    gobject.idle_add(self.youtube_video_rate.set_active,qn)
            active = self.youtube_video_rate.get_active()
        else:
            if self.quality_list:
                active = self.youtube_video_rate.get_active()

    def on_youtube_video_rate_changed(self,widget):
        active = self.youtube_video_rate.get_active()
        if self.gui.is_playing:
            self.gui.stop_play()
            try:
                self.media_codec = self.quality_list[active].split('|')[1]
            except:
                pass
            self.gui.videosink.set_property('force-aspect-ratio', True)
            return self.gui.start_play(self.media_link[active])


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
            return
        return links_arr, quality_arr
