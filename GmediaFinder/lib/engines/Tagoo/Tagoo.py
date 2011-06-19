import gobject
import re
import urllib

try:
	from functions import *
except:
	from GmediaFinder.functions import *
	
class Tagoo(object):
    def __init__(self,gui):
        self.gui = gui
        self.type = "audio"
        self.current_page = 1
        self.main_start_page = 1
        self.name="Tagoo"
        self.thread_stop=False
        self.search_url = "http://tagoo.ru/en/search.php?for=audio&search=%s&page=%d&sort=date"
        self.start_engine()


    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def load_gui(self):
		pass

    def get_search_url(self,query,page):
        return self.search_url % (query,page)
        
    def filter(self,data,user_search):
        flag_found = False
        end_flag=False
        for line in data.readlines():
            if self.thread_stop == True:
                break
            ## search link
            if 'class="notfound_taggy searchstring' in line:
                end_flag=True
            elif 'href="' in line:
                try:
                    link = re.search('href="(((\S.*))(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv))"',line).group(1)
                    t = urllib.unquote(re.search('href="(((\S.*))(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv))"',line).group(3).split('/')[-1])
                    title = re.sub('_',' ',t)
                    flag_found = True
                    gobject.idle_add(self.gui.add_sound, title, link, None, None, self.name)
                except:
                   continue
            continue
            
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True

    def play(self,link):
		self.gui.media_link = link
		return self.gui.start_play(link)
		
    def print_info(self,msg):
		gobject.idle_add(self.gui.info_label.set_text,msg)
