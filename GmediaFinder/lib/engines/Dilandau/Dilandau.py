import urllib2
import gtk
import gobject
import time
    
class Dilandau(object):
    def __init__(self, gui):    
        self.gui = gui
        self.name="Dilandau"
        self.type = "audio"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.search_url = "http://fr.dilandau.com/telecharger_musique/%s-%s.html"
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        pass
    
    def search(self, query, page):
        self.thread_stop=False
        try:
            data = urllib2.urlopen(self.search_url % (query.replace(' ','-'), self.current_page))
            self.filter(data, query)
        except:
            self.print_info(_('Dilandau: Connexion failed...'))
            gobject.idle_add(self.gui.throbber.hide)
            time.sleep(5)
            self.thread_stop=True
        
    def filter(self, data, user_search):
        flag = False
        flag_found = False
        gobject.idle_add(self.gui.changepage_btn.show)      
        for line in data.readlines():
            if self.thread_stop == True:
                break
            if 'var playlist' in line: flag = True
            if 'id="body_file_list"' in line: flag = False
            if flag:
                if 'title :' in line:
                    titre = line.split('"')[1]
                elif 'file : ' in line:
                    flag_found = True
                    url = line.split('"')[1]
                    if not titre: titre = url.split('/')[-1]
                    markup="<small><b>%s</b></small>" % titre
                    gobject.idle_add(self.gui.add_sound, titre, markup, url, None, None, self.name)
                continue
            if 'class="next_page inactive"' in line:
                gobject.idle_add(self.gui.changepage_btn.hide)
                gobject.idle_add(self.gui.throbber.hide)
                self.print_info(_("Dilandau: no more results found for %s...") % user_search)
                time.sleep(5)
                self.print_info('')
        if flag_found:
            if self.current_page != 1:
                gobject.idle_add(self.gui.pageback_btn.show)
            else:
                gobject.idle_add(self.gui.pageback_btn.hide)
        else:
            gobject.idle_add(self.gui.changepage_btn.hide)
            self.print_info(_("Dilandau: no results found for %s...") % user_search)
            gobject.idle_add(self.gui.throbber.hide)
            time.sleep(5)
        self.thread_stop=True
        
    def play(self,link):
        self.gui.media_link = link
        return self.gui.start_play(link)
        
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
    
