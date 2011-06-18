import re
import urllib
import gobject

try:
    from functions import *
except:
    from GmediaFinder.functions import *

class BurningCamel(object):
    def __init__(self,gui):
        self.gui = gui
        self.name="BurningCamel"
        self.type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.adult_content=True
        self.search_url = "http://www.burningcamel.com/search/results/page:%s/limit:36/sort:live/direction:desc/q:%s/matchMode:any/s:1/t:2/width:medium"
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        pass
        
    def get_search_url(self,query,page):
        return self.search_url % (page,query)
    
    def play(self,link):
        try:
            self.gui.media_link = link
            return self.gui.start_play(link)
        except:
            return
        
    def filter(self,data,user_search):
        flag = False
        flag_found = False
        title=""
        markup=""
        link=""
        for line in data.readlines():
            if self.thread_stop == True:
                break
            ## search link
            if not flag and 'leftcol' in line: flag = True
            if flag:
                if line.startswith('Event.observe'): continue
                if 'vid_dur' in line: vid_dur = line.split('>')[1].split('<')[0]
                if 'exbtn' in line: suffixe = line.split('_')[1]
                if '<img ' in line:
                    try:
                        split_line = line.split('"')
                        title = split_line[3]
                        thumb = split_line[5]
                        link = thumb.replace('_thumb.jpg','%slq.flv' % suffixe)
                        img = download_photo(thumb)
                    except:
                        continue
                    markup = "<small><b>%s</b> (%s)</small>" % (title, vid_dur)
                    gobject.idle_add(self.gui.add_sound, title, markup, link, img, None, self.name)
                    flag_found = True
                if '...' in line:
                    nb_page = line.split('...')[1].split('<')[0]
                    try:
                        if self.current_page == int(nb_page):
                            self.print_info(_("%s: No more results for %s...") % (self.name,user_search))
                            time.sleep(5)                      
                    except:
                        break
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
