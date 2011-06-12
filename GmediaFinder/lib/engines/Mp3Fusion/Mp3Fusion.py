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
        self.search_url = "http://www.mp3fusion.net/music/%s-%s.html"
        self.start_engine()

    def start_engine(self):
        self.gui.engine_list[self.name] = ''

    def load_gui(self):
        pass

    def search(self, query, page):
        try:
            data = urllib2.urlopen(self.search_url % (urllib.quote(query), self.current_page))
            self.filter(data, query)
        except:
            self.print_info(_('Mp3Fusion: Connexion failed...'))
            gobject.idle_add(self.gui.throbber.hide)
            time.sleep(5)
            self.print_info("")
        
    def filter(self, data, user_search):
        flag_found = False
        gobject.idle_add(self.gui.changepage_btn.show)      
        for line in data.readlines():
            if 'line1' in line:
                flag_found = True
                url = line.split('"')[3]
                titre = line.split('>')[2].split('<')[0]
                if not titre: titre = url.split('/')[-1]
                markup="<small><b>%s</b></small>" % titre
                gobject.idle_add(self.gui.add_sound, titre, markup, url, None, None, self.name)
                continue
            if '>Next Result' in line and line.split('"')[1] == 'http://www.mp3fusion.net/music/.html':
                gobject.idle_add(self.gui.changepage_btn.hide)
                gobject.idle_add(self.gui.throbber.hide)
                self.print_info(_("Mp3Fusion: no more results found for %s...") % user_search)
                time.sleep(5)
                self.print_info('')
                break
        if flag_found:
            if self.current_page != 1:
                gobject.idle_add(self.gui.pageback_btn.show)
            else:
                gobject.idle_add(self.gui.pageback_btn.hide)
        else:
            gobject.idle_add(self.gui.changepage_btn.hide)
            self.print_info(_("Mp3Fusion: no results found for %s...") % user_search)
            gobject.idle_add(self.gui.throbber.hide)
            time.sleep(5)
            self.print_info('')
        gobject.idle_add(self.gui.throbber.hide)
        self.print_info('')
        
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
