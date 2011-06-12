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
        self.search_url = "http://mp3realm.org/search?q=%s&bitrate=&dur=0&pp=50&page=%s"
        self.start_engine()


    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def load_gui(self):
		pass

    def search(self, query, page):
		try:
			q = re.sub(' ','+',query)
			data = get_url_data(self.search_url % (urllib.quote(q), self.current_page))
			print self.search_url % (urllib.quote(q), self.current_page)
			self.filter(data,query)
		except:
			gobject.idle_add(self.gui.throbber.hide)
			self.print_info(_('Mp3realm: Connexion failed...'))
			self.gui.throbber.hide()
			time.sleep(5)
			self.print_info("")
			  
    def filter(self,data,user_search):
		flag_found = False
		end_flag=True
		for line in data.readlines():
			## search link
			if 'loadAndPlay' in line:
				flag_found = True
				link = re.search('loadAndPlay\(\'(.*?)\'\)',line).group(1)
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
			self.print_info(_("mp3Realm: no results found for %s...") % user_search)
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
