import re
import urllib
import gobject

try:
    from functions import *
except:
    from GmediaFinder.functions import *

class Redtube(object):
    def __init__(self,gui):
        self.gui = gui
        self.name="Redtube"
        self.engine_type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.adult_content=True
        self.has_browser_mode = False
        self.search_url = "http://www.redtube.com/%s?search=%s&page=%s"
        self.category_url = "http://www.redtube.com/redtube/%s?sorting=%s&page=%s"
        ## options labels
        self.order_label = _("Order by: ")
        
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        ## create orderby combobox
        self.orderbyOpt = {self.order_label:{_("Most recent"):"new",_("Most viewed"):"mostviewed",
                                            _("Most rated"):"top",_("Most relevant"):"",
            },
        }
        self.orderby = create_comboBox(self.gui, self.orderbyOpt)
        self.orderby.setIndexFromString(_("Most relevant"))
    
    def get_search_url(self,query,page):
        choice = self.orderby.getSelected()
        orderby = self.orderbyOpt[self.order_label][choice]
        return self.search_url % (orderby,query,page)
    
    def play(self,link):
        data = get_url_data(link)
        for line in data.readlines():
            if 'mp4_url=' in line:
                link = urllib.unquote(re.search('mp4_url=(.*)&',line).group(1))
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
            ## search link
            try:
                if 'class="t"' in line:
                    img_link = re.search('src=\"(.*?)\"',line).group(1)
                    img = download_photo(img_link)
                elif 'class="s"' in line:
                    flag_found = True
                    l = re.search('href=\"(.*?)\"',line).group(1)
                    link = "http://www.redtube.com%s" % l
                    title = re.search('title=\"(.*?)\"',line).group(1)
                    gobject.idle_add(self.gui.add_sound, title, link, img, None, self.name)
                ## check for next page
                elif 'id="navNext"' in line:
                    end_flag=False
                continue
            except:
                continue
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
