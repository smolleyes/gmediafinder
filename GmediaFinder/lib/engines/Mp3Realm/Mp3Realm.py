
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
        gtk.gdk.threads_enter()
        self.filter(data,query)
        gtk.gdk.threads_leave()
        
    def filter(self,data,user_search):
		d = unicode(data,errors='replace')
		soup = BeautifulStoneSoup(d.decode('utf-8'),selfClosingTags=['/>'])
		## reset the treeview
		nlist = []
		link_list = []
		files_count = None
		try:
			#search results div
			files_count = soup.findAll('div',attrs={'id':'searchstat'})[0].findAll('strong')[1].string
			if self.current_page != 1:
				self.gui.pageback_btn.show()
			else:
				self.gui.pageback_btn.hide()
		except:
			self.gui.info_label.set_text(_("No results found for %s...") % (user_search))
			self.gui.changepage_btn.hide()
			self.gui.throbber.hide()
			return
		
		if re.search(r'(\S*Aucuns resultats)', soup.__str__()):
			self.gui.changepage_btn.hide()
			self.current_page = 1
			self.gui.info_label.set_text(_("No results found for %s...") % (user_search))
			self.gui.throbber.hide()
			return

		self.gui.changepage_btn.show()
		
		flist = re.findall('(http://.*\S\.mp3|\.mp4|\.ogg|\.aac|\.wav|\.wma)', data.lower())
		for link in flist:
			if re.match('http://\'\+this', link) :
				continue
			try:
				link = urllib2.unquote(link)
				name = urllib2.unquote(os.path.basename(link.decode('UTF8')))
				nlist.append(name)
				link_list.append(link)
			except:
				continue
		## add to the treeview if ok
		i = 0
		for name in nlist:
			if name and link_list[i]:
				markup="<small><b>%s</b></small>" % name
				self.gui.add_sound(name, markup, link_list[i])
				i += 1
		self.gui.info_label.set_text("")
		self.gui.throbber.hide()
