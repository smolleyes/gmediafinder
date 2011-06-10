import gobject
import re
import urllib
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup

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
        data = get_url_data(self.search_url % (urllib.quote(query), self.current_page))
        self.filter(data,query)
        
    def filter(self,data,user_search):
		try:
			d = unicode(data,errors='replace')
		except:
			gobject.idle_add(self.gui.throbber.hide)
			self.print_info(_('Mp3realm: Connexion failed...'))
			self.gui.throbber.hide()
			time.sleep(5)
			self.print_info("")
			return
		soup = BeautifulStoneSoup(d.decode('utf-8'),selfClosingTags=['/>'])
		## reset the treeview
		nlist = []
		link_list = []
		files_count = None
		try:
			#search results div
			files_count = soup.findAll('div',attrs={'id':'searchstat'})[0].findAll('strong')[1].string
			if self.current_page != 1:
				gobject.idle_add(self.gui.pageback_btn.show)
			else:
				gobject.idle_add(self.gui.pageback_btn.hide)
		except:
			self.print_info(_("Mp3realm: No results found for %s...") % user_search)
			gobject.idle_add(self.gui.changepage_btn.hide)
			gobject.idle_add(self.gui.throbber.hide)
			return
		
		if re.search(r'(\S*Aucuns resultats)', soup.__str__()):
			gobject.idle_add(self.gui.changepage_btn.hide)
			self.current_page = 1
			self.print_info(_("Mp3realm: No results found for %s...") % user_search)
			gobject.idle_add(self.gui.throbber.hide)
			return

		gobject.idle_add(self.gui.changepage_btn.show)
		
		flist = re.findall('(http://.*\S\.mp3|\.mp4|\.ogg|\.aac|\.wav|\.wma)', data.lower())
		for link in flist:
			if re.match('http://\'\+this', link) :
				continue
			try:
				link = urllib2.unquote(link)
				name = urllib2.unquote(os.path.basename(link.decode('utf-8')))
				markup="<small><b>%s</b></small>" % name
				gobject.idle_add(self.gui.add_sound,name, markup, link,None,None,self.name)
			except:
				continue
		self.print_info("")
		gobject.idle_add(self.gui.throbber.hide)
		
    def play(self,link):
		self.gui.media_link = link
		return self.gui.start_play(link)
	
    def print_info(self,msg):
		gobject.idle_add(self.gui.info_label.set_text,msg)
