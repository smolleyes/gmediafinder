#-*- coding: UTF-8 -*-

import re
import urllib
import gobject

try:
    from functions import *
except:
    from GmediaFinder.functions import *

class PornHub(object):
    def __init__(self,gui):
        self.gui              = gui
        self.name             = "PornHub"
        self.engine_type      = "video"
        self.current_page     = 1
        self.main_start_page  = 1
        self.thread_stop      = False
        self.adult_content    = True
        self.has_browser_mode = False
        self.search_url       = "http://www.pornhub.com/video/search?search=%s&o=%s&page=%s"
        self.category_url     = "http://www.empflix.com/channels/new-%s-%s.html"
        ## options labels
        self.order_label      = _("Order by: ")
        self.cat_label        = _("Category: ")
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        ## create orderby combobox
        self.orderbyOpt = {self.order_label:{  _("Most recent"):"mr",_("Most viewed"):"mv",
                                               _("Top rated"):"tr",_("Longest"):"lg",
                                            },
                           }
        self.orderby = create_comboBox(self.gui, self.orderbyOpt)
        self.orderby.setIndexFromString(_("Most recent"))
    
    def get_search_url(self,query,page):
        choice  = self.orderby.getSelected()
        orderby = self.orderbyOpt[self.order_label][choice]
        return self.search_url % (urllib.quote_plus(query),orderby,page)
    
    def play(self,link):
        data = get_url_data(link)
        for line in data.readlines():
            if '"video_url"' in line:
                link = urllib.unquote(line.split('"')[3])
                self.gui.media_link = link
                break
        return self.gui.start_play(link)
        
    def filter(self,data,user_search):
        flag_found = False
        end_flag   = True
        title      = ""
        markup     = ""
        link       = ""
        for line in data.readlines():
            if self.thread_stop == True:
                break
            if 'class="img"' in line:
                flag_found = True
                title      = line.split('"')[3]
                link       = line.split('"')[1]
                print link
            if flag_found:
                if 'startThumbChange' in line:
                    img_link = line.split('"')[1]
                    img      = download_photo(img_link)
                    gobject.idle_add(self.gui.add_sound, title, link, img, None, self.name)
                if 'Our Friends' in line:
                    break
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
