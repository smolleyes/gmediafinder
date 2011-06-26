import re
import urllib
import gobject

try:
    from functions import *
except:
    from GmediaFinder.functions import *

class SunPorno(object):
    def __init__(self,gui):
        self.gui = gui
        self.name="SunPorno"
        self.type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.order_label = _("Order by: ")
        self.thread_stop=False
        self.adult_content=True
        self.search_url = "http://www.sunporno.com/search/%s/page%s.html?sort=%s"
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        self.order_list = { self.order_label:{ _("Relevance"):"relevance",
                                               _("Rating"):"top-rated",
                                               _("Added date"):"most-recent",
                                               _("View count"):"most-viewed",
                                             },
                                             
                          }
        self.orderby = create_comboBox(self.gui, self.order_list)
    
    def get_search_url(self,query,page):            
        choice = self.orderby.getSelected()
        orderby = self.order_list[self.order_label][choice]
        return self.search_url % (query, page, orderby)
    
    def play(self,link):
        data = get_url_data(link)
        for line in data.readlines():
            if "'file'" in line:
                link = line.split("'")[3]
                self.gui.media_link = link
                break
        return self.gui.start_play(link)
        
    def filter(self,data,user_search):
        flag_found = False
        for line in data.readlines():
            duration=""
            if self.thread_stop == True:
                break
            ## search link
            if 'startm' in line:
                link = re.search('href=\"([^"]*)', line).group(1)
                img_url = re.search('src=\"([^"]*)', line).group(1)
                continue
            if '</span></a>' in line:
                title = line.split('>')[1].split('<')[0]
                continue
            if 'star_on' in line:
                duration = line.split('>')[3].split('<')[0]
                continue
            if 'views</span>' in line:
                date = line.split('>')[2].split('<')[0]
                mark = '\n<span size="x-small"><b>Duration:</b>  <b>Posted:</b> %s</span>' % (date)
                img = download_photo(img_url)
                gobject.idle_add(self.gui.add_sound, title, link, img, None, self.name, mark)
                flag_found = True
                continue
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
