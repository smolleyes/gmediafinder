import re
import urllib2
import gobject,glib
import json

try:
    from functions import *
except:
    from GmediaFinder.functions import *

class DailyMotion(object):
    def __init__(self,gui):
        self.gui = gui
        self.name = 'DailyMotion'
        self.engine_type = "video"
        self.options_dic = {}
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.has_browser_mode = False
        ## options labels
        self.order_label = _("Order by: ")
        self.filters_label = _("Filters: ")
        self.search_url = 'https://api.dailymotion.com/videos?%ssort=%s&page=%s&limit=25&search=%s&fields=embed_url,thumbnail_medium_url,title,views_total,duration'
        
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        self.order_list = {self.order_label:{_("Most relevant"):"relevance",_("Most recent"):"recent",_("Most viewed"):"visited",_("Most rated"):"rated"}}
        self.orderby = create_comboBox(self.gui, self.order_list)
        self.filters_list = {self.filters_label:{"":"",_("HD"):"hd"}}
        self.filters = create_comboBox(self.gui, self.filters_list)
        
    def get_search_url(self,query,page):
        choice = self.orderby.getSelected()
        orderby = self.order_list[self.order_label][choice]
        choice = self.filters.getSelected()
        f=''
        if choice != "":
            filters = self.filters_list[self.filters_label][choice]
            f = 'filters=%s&' % filters
        return self.search_url % (f,orderby,page,query)
    
    def play(self,link):
        try:
            data = get_url_data(link)
            data = urllib2.urlopen(link)
            j_data = data.read().split('info =')[1].split(';')[0]
            js = json.loads(j_data)
            link = js['stream_url']
            self.gui.media_link = link
            return self.gui.start_play(link)
        except:
            return
        
    def filter(self,data,user_search):
        js = json.load(data)
        l = js['list']
        for dic in l:
            if self.thread_stop == True:
                break
            title = dic['title']
            link = dic['embed_url']+'&cache=0'
            img_link = dic['thumbnail_medium_url']
            duration = dic['duration']
            calc = divmod(int(duration),60)
            seconds = int(calc[1])
            if seconds < 10:
                seconds = "0%d" % seconds
            duration = "%d:%s" % (calc[0],seconds)
            total = dic['views_total']
            img = download_photo(img_link)
            markup = _("\n<small><b>views:</b> %s        <b>Duration:</b> %s</small>") % (total, duration)
            gobject.idle_add(self.gui.add_sound, title, link, img, None, self.name, markup)
        if js['has_more'] != 'true':
            self.print_info(_("%s: No more results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
        
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)

