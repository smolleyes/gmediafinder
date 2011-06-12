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
        self.search_url = "http://tagoo.ru/en/search.php?for=audio&search=%s&page=%d&sort=date"
        self.start_engine()


    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def load_gui(self):
		pass

    def search(self, query, page):
        data = get_url_data(self.search_url % (urllib.quote(query), self.current_page))
        self.filter(data,query)
        
    def filter(self,data,user_search):
        flag_found = False
        end_flag=False
        for line in data.readlines():
            ## search link
            if 'class="notfound_taggy searchstring' in line:
				end_flag=True
            elif 'href="' in line:
                try:
                    link = re.search('href="(((\S.*))(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv))"',line).group(1)
                    t = urllib.unquote(re.search('href="(((\S.*))(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv))"',line).group(3).split('/')[-1])
                    title = re.sub('_',' ',t)
                    markup = "<small><b>%s</b></small>" % title
                    flag_found = True
                    gobject.idle_add(self.gui.add_sound, title, markup, link, None, None, self.name)
                except:
                   continue
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
            self.print_info(_("Tagoo: no results found for %s...") % user_search)
            gobject.idle_add(self.gui.throbber.hide)
            time.sleep(5)
            self.print_info('')
        gobject.idle_add(self.gui.throbber.hide)
        self.print_info('')

    def play(self,link):
		self.gui.media_link = link
		return self.gui.start_play(link)
		
    def print_info(self,msg):
		gobject.idle_add(self.gui.info_label.set_text,msg)
