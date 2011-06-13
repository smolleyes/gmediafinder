import gobject
import re
import urllib

try:
	from functions import *
except:
	from GmediaFinder.functions import *

class Mp3Realm(object):
    def __init__(self,gui):
        self.gui = gui
        self.type = "audio"
        self.name="Mp3Realm"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.search_url = "http://mp3realm.org/search?q=%s&bitrate=&dur=0&pp=50&page=%s"
        self.start_engine()
    
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        pass
    
    def search(self, query, page):
        self.thread_stop=False
        try:
            q = re.sub(' ','+',query)
            data = get_url_data(self.search_url % (urllib.quote(q), self.current_page))
            self.filter(data,query)
        except:
            self.print_info(_('%s: Connexion failed...') % self.name)
            time.sleep(5)
            self.thread_stop=True
              
    def filter(self,data,user_search):
        flag_found = False
        end_flag=True
        for line in data.readlines():
            if self.thread_stop == True:
                break
            ## search link
            if 'loadAndPlay' in line:
                flag_found = True
                link = re.search('loadAndPlay\(\'((\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv))',line).group(1)
            ## search title
            elif 'search?q=lyrics:' in line:
                title = re.search('lyrics:(.*?)\'>',line).group(1)
                markup="<small><b>%s</b></small>" % title
                gobject.idle_add(self.gui.add_sound, title, markup, link, None, None, self.name)
            ## check for next page
            elif '<li class="currentpage"><b>%s</b>' % self.current_page in line:
                end_flag=False
            continue
            
        if flag_found:
            if end_flag:
                gobject.idle_add(self.gui.changepage_btn.hide)
            else:
                gobject.idle_add(self.gui.changepage_btn.show)
            if self.current_page != 1:
                gobject.idle_add(self.gui.pageback_btn.show)
            else:
                gobject.idle_add(self.gui.pageback_btn.hide)
        else:
            gobject.idle_add(self.gui.changepage_btn.hide)
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
            self.thread_stop=True
        self.thread_stop=True
        
    def play(self,link):
        self.gui.media_link = link
        return self.gui.start_play(link)
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
