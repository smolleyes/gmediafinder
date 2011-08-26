import gobject
import re
import urllib
import os

try:
	from functions import *
except:
	from GmediaFinder.functions import *

class Mp3Realm(object):
    def __init__(self,gui):
        self.gui = gui
        self.engine_type = "audio"
        self.name="Mp3Realm"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.has_browser_mode = False
        self.search_url = "http://mp3realm.org/search?q=%s&bitrate=&dur=0&pp=50&page=%s"
        self.start_engine()
    
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        pass
        
    def get_search_url(self,query,page):
        q = re.sub(' ','+',query)
        return self.search_url % (q,page)
              
    def filter(self,data,user_search):
        flag_found = False
        end_flag=True
        title=""
        markup=""
        link=""
        for line in data.readlines():
            if self.thread_stop:
                break
            ## search link
            if 'loadAndPlay' in line:
                flag_found = True
                try:
                    link = re.search('loadAndPlay\(\'((\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv))',line).group(1)
                except:
                    continue
            ## search title
            elif 'search?q=lyrics:' in line:
                title = re.search('lyrics:(.*?)\'>',line).group(1)
                name, ext = os.path.splitext(titre)
                gobject.idle_add(self.gui.add_sound, name, link, None, None, self.name)
            ## check for next page
            elif '<li class="currentpage"><b>%s</b>' % self.current_page in line:
                end_flag=False
            continue
            
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
            self.thread_stop=True
        self.thread_stop=True
        
    def play(self,link):
        self.gui.media_link = link
        return self.gui.start_play(link)
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
