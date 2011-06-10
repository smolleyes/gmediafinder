
import re
import urllib
import socket
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup

try:
	from functions import *
except:
	from GmediaFinder.functions import *

class Imusicz(object):
    def __init__(self,gui):
        self.gui = gui
        self.type = "audio"
        self.name="Imusicz"
        self.current_page = 1
        self.main_start_page = 1
        self.search_url = "http://imusicz.net/search/mp3/%s/%s.html"
        self.start_engine()


    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def load_gui(self):
		pass
        
    def search(self, query, page=1):
		timeout = 30
		socket.setdefaulttimeout(timeout)
		data = get_url_data(self.search_url % (page, urllib.quote(query)))
		self.filter(data,query)
		
    def filter(self,data,user_search):
		if not data:
			self.print_info(_("Imusicz: Connexion failed..."))
			gobject.idle_add(self.gui.throbber.hide)
			time.sleep(5)
			self.gui.info_label.set_text("")
			return
		d = unicode(data,errors='replace')
		soup = BeautifulStoneSoup(d.decode('utf-8'),selfClosingTags=['/>'],convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
		nlist = []
		link_list = []
		next_page = 1
		pagination_table = soup.find('table',attrs={'class':'pagination'})
		if pagination_table:
			next_check = pagination_table.findAll('a')
			for a in next_check:
				l = str(a.string)
				if l == "Next":
					next_page = 1
					if self.current_page != 1:
						gobject.idle_add(self.gui.pageback_btn.show)
					else:
						gobject.idle_add(self.gui.pageback_btn.hide)
			if next_page:
				gobject.idle_add(self.gui.changepage_btn.show)
			else:
				gobject.idle_add(self.gui.changepage_btn.hide)
				self.print_info(_("Imusicz: no more files found for %s...") % user_search)
				object.idle_add(self.gui.throbber.hide)
				time.sleep(5)
				self.print_info("")
				return

		flist = soup.findAll('td',attrs={'width':'75'})
		if len(flist) == 0:
			gobject.idle_add(self.gui.changepage_btn.hide)
			self.print_info(_("Imusicz: no files found for %s...") % user_search)
			gobject.idle_add(self.gui.throbber.hide)
			time.sleep(5)
			self.print_info("")
			return
		for link in flist:
			try:
				furl = re.search('a href="(http(\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv)(\S.*)redirect)"(\S.*)Download',str(link)).group(1)
				name = re.search('name=(\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv)',str(furl)).group(1)
				linkId= re.search('url=(\S.*)&amp',str(furl)).group(1)
				link = urllib2.unquote('http://imusicz.net/download.php?url='+linkId)
				name = BeautifulStoneSoup(name, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
				markup="<small><b>%s</b></small>" % name
				gobject.idle_add(self.gui.add_sound, name, markup, link_list, None, None, self.name)
			except:
				continue
		self.print_info("")
		gobject.idle_add(self.gui.throbber.hide)

    def play(self,link):
		self.gui.media_link = link
		return self.gui.start_play(link)
	
    def print_info(self,msg):
		gobject.idle_add(self.gui.info_label.set_text,msg)
