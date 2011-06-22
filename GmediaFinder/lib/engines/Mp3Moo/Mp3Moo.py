import gobject
import urllib2
import urllib
import time
    
class Mp3Moo(object):
    def __init__(self,gui):
        self.gui = gui
        self.type = "audio"
        self.name="Mp3Moo"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.search_url = "http://mp3moo.com/search/mp3/%s/%s.html"
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        pass
    
    def get_search_url(self,query,page):
        self.print_info(_('%s: Please wait, it can take longtime ...') % self.name)
        return self.search_url % (page,query)
        
    def filter(self, data, user_search):
        flag_found = False   
        for line in data.readlines():
            if self.thread_stop:
                break
            try:
                if 'prod_details' in line:
                    base_cut = line.split('url=')[1]
                    url = 'http://mp3moo.com/download.php?url=%s' % base_cut.split('"')[0]
                    titre = base_cut.split('>')[1].split('<')[0]
                    serveur = base_cut.split('>')[-1].rstrip()
                    eng= _('Engine: ')
                    markup = '\n<small><b>%s</b>%s</small>' % (eng,serveur.split('|')[0])
                    gobject.idle_add(self.gui.add_sound, titre, url, None, None, self.name,markup)
                    flag_found = True
                    continue
            except:
                continue
            if '>Next<' in line and self.search_url in line:
                self.print_info(_("%s: No results for %s...") % (self.name,user_search))
                time.sleep(5)
                break
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
        
    def play(self,link):
        try:
            self.gui.media_link = link
            return self.gui.start_play(link)
        except:
            return
        
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
   
