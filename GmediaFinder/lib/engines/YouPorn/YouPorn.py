#-*- coding: UTF-8 -*-

import mechanize
import re
import urllib, urllib2
import gtk
import time
import gobject

try:
    from functions import create_comboBox
    from functions import download_photo
    from functions import get_url_data
    from functions import ComboBox
except:
    from GmediaFinder.functions import create_comboBox
    from GmediaFinder.functions import download_photo
    from GmediaFinder.functions import get_url_data
    from GmediaFinder.functions import ComboBox


URL = "http://youporn.com/"
ENTER_URL = "%s?user_choice=Enter" % URL
BROWSE_URL = "%sbrowse/%s?page=%s" % (URL, "%s", "%d")
TOP_RATED_URL = "%stop_rated/%s?page=%s" % (URL, "%s", "%d")
MOST_VIEWED_URL = "%smost_viewed/%s?page=%s" % (URL, "%s", "%d")
SEARCH_URL = "%ssearch/%s?query=%s&type=%s&page=%s" % (URL, "%s", "%s", "%s", "%d")

class YouPorn(object):
    def __init__(self,gui):
        self.gui = gui
        self.name ="YouPorn"
        self.type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.warn=True
        self.search_url = "http://www.youporn.com/search/%s?query=%s&type=%s&page=%s"
        self.browser = mechanize.Browser()
        self.browser.addheaders = []
        self.browser.open(ENTER_URL)
        self.start_engine()
    
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        label = gtk.Label(_("Order by: "))
        self.gui.search_opt_box.pack_start(label,False,False,5)
        ## create orderby combobox
        cb = create_comboBox()
        self.orderbyOpt = {_("Most recent"):"time",_("Most viewed"):"views",
        _("Most rated"):"rating",_("Duration"):"duration",
        _("Most relevant"):"relevance",
        }
        self.orderby = ComboBox(cb)
        for cat in self.orderbyOpt:
            self.orderby.append(cat)
        self.gui.search_opt_box.add(cb)
        self.gui.search_opt_box.show_all()
        self.orderby.select(0)
    
    def filter(self, url,query):
        data = self.browser.open(url)
        flag_found = False
        title=""
        markup=""
        link=""
        for line in data.readlines():
            if self.thread_stop == True:
                break
            ## search link
            if 'href="/watch' in line:
                flag_found = True
                l = re.search('href=\"(.*?)\"',line).group(1)
                link = "http://www.youporn.com%s" % l
            elif 'extra_large.jpg' in line:
                title = re.search('alt=\"(.*?)\"',line).group(1)
                markup="<small><b>%s</b></small>" % title
                img_link = re.search('src=\"(.*?)\"',line).group(1)
                try:
                    img = download_photo(img_link)
                except:
                    continue
                gobject.idle_add(self.gui.add_sound, title, markup, link, img, None, self.name)
            ## check for next page
            #elif 'id="navNext"' in line:
                #end_flag=False
            continue
            
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,query))
            time.sleep(5)
        self.thread_stop=True
        
    
    def search(self, query, page=1, sort_by="time", type="straight"):
        self.thread_stop=False
        choice = self.orderby.getSelected()
        orderby = self.orderbyOpt[choice]
        try:
            self.filter(self.search_url % (orderby, urllib.quote(query), type, page), query)
        except:
            self.print_info(_("%s: Connexion failed...") % self.name)
            time.sleep(5)
            self.thread_stop=True
            
    def play(self,link):
        data = self.browser.open(link)
        for line in data.readlines():
            if '>MP4' in line:
                link = re.search('(.*)href=\"(.*?)\">MP4',line).group(2)
                self.gui.media_link = link
                break
        return self.gui.start_play(link)
            
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
