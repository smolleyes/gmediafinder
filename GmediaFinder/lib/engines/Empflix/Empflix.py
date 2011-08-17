import re
import urllib
import gobject

try:
    from functions import *
except:
    from GmediaFinder.functions import *

class Empflix(object):
    def __init__(self,gui):
        self.gui = gui
        self.name="Empflix"
        self.engine_type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.adult_content=True
        self.has_browser_mode = False
        self.search_url = "http://www.empflix.com/advanced_search.php?page=%s&what=%s&sort=%s&sortDir=desc&per_page=1&Search=Search"
        self.category_url = "http://www.empflix.com/channels/new-%s-%s.html"
        ## options labels
        self.order_label = _("Order by: ")
        self.cat_label = _("Category: ")
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        ## create orderby combobox
        self.orderbyOpt = {self.order_label:{_("Most recent"):"date",_("Duration"):"length",
                                            _("Most rated"):"rating",_("Most relevant"):"relevance",
            },
        }
        self.orderby = create_comboBox(self.gui, self.orderbyOpt)
        self.orderby.setIndexFromString(_("Most relevant"))
    
    def get_search_url(self,query,page):
        choice = self.orderby.getSelected()
        orderby = self.orderbyOpt[self.order_label][choice]
        return self.search_url % (page,query,orderby)
    
    def play(self,link):
        data = get_url_data(link)
        for line in data.readlines():
            if '.flv?key=' in line:
                link = urllib.unquote(re.search('href="(.*?)"',line).group(1))
                self.gui.media_link = link
                break
        return self.gui.start_play(link)
        
    def filter(self,data,user_search):
        flag_found = False
        end_flag=True
        title=""
        markup=""
        link=""
        for line in data.readlines():
            if self.thread_stop == True:
                break
            try:
                if 'http://static.empflix.com/thumbs' in line:
                    img_link = re.search('src="(.*?)"',line).group(1)
                    img = download_photo(img_link)
                    title = re.search('alt=\"(.*?)\"',line).group(1)
                    link = re.search('http://www.empflix.com/videos/(.*?)"',line).group(0)
                    gobject.idle_add(self.gui.add_sound, title, link, img, None, self.name)
            except:
                continue
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
