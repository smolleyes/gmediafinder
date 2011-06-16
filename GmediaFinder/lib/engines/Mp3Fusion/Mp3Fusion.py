import gobject
import urllib2
import urllib
import time

class Mp3Fusion(object):
    def __init__(self,gui):
        self.gui = gui
        self.type = "audio"
        self.name="Mp3Fusion"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.search_url = "http://www.mp3fusion.net/music/%s-%s.html"
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        pass
        
    def get_search_url(self,query,page):
        return self.search_url % (query,page)
        
    def filter(self, data, user_search):
        flag_found = False     
        for line in data.readlines():
            if self.thread_stop == True:
                break
            if 'line1' in line:
                flag_found = True
                url = line.split('"')[3]
                titre = line.split('>')[2].split('<')[0]
                if not titre: titre = url.split('/')[-1]
                markup="<small><b>%s</b></small>" % titre
                if self.thread_stop:
                    break
                gobject.idle_add(self.gui.add_sound, titre, markup, url, None, None, self.name)
                continue
            if '>Next Result' in line and line.split('"')[1] == 'http://www.mp3fusion.net/music/.html':
                self.print_info(_("%s: No results for %s...") % (self.name,user_search))
                time.sleep(5)
                break
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
        
    def play(self,link):
        try:
            data = urllib2.urlopen('http://www.mp3fusion.net/song.php?name='+link)
            for line in data.readlines():
                if 'file=' in line:
                    link = line.split('file=')[1].split('&')[0]
            self.gui.media_link = link
            return self.gui.start_play(link)
        except:
            return
        
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
