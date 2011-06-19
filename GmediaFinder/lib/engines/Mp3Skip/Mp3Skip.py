import gtk
import gobject
import time

class Mp3Skip(object):
    def __init__(self, gui):    
        self.gui = gui
        self.name="Mp3Skip"
        self.type = "audio"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.search_url = "http://mp3skip.com/mp3/%s.html"
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        pass
        
    def get_search_url(self,query,page):
        return self.search_url % query.replace(' ','_')
        
    def filter(self, data, user_search):
        flag = flag_found = flag_left = flag_right = False
        for line in data.readlines():
            try:
                if self.thread_stop == True:
                    break
                if '"left"' in line: 
                    flag_left = True
                    continue
                if flag_left:
                    kb = line.split('/>')[1]
                    flag_left = False
                if '"right_song"' in line:
                    flag_right = True
                    continue
                if flag_right:
                    titre = line.split('<b>')[1].split('</b>')[0].replace('mp3','')
                    print titre
                    flag_right = False
                if '>Download<' in line:
                    flag_found = True
                    url = line.split('"')[3]
                    gobject.idle_add(self.gui.add_sound, titre, url, None, None, self.name)
            except:
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

