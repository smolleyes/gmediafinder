
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
		return self.filter(data,query)
		
    def filter(self,data,user_search):
		if not data:
			print "timeout..."
			return
		soup = BeautifulStoneSoup(data.encode('utf-8'),selfClosingTags=['/>'],convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
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
						self.gui.pageback_btn.show()
					else:
						self.gui.pageback_btn.hide()
			if next_page:		
				values = {'page': self.current_page, 'query': user_search}
				#self.gui.informations_label.set_text(_("Results page %(page)s for %(query)s...(Next page available)") % values)
				self.gui.changepage_btn.show()
			else:
				self.gui.changepage_btn.hide()
				#self.gui.informations_label.set_text(_("no more files found for %s...") % (user_search))
				return

		flist = soup.findAll('td',attrs={'width':'75'})
		if len(flist) == 0:
			self.gui.changepage_btn.hide()
			#self.gui.informations_label.set_text(_("no files found for %s...") % (user_search))
			return
		for link in flist:
			try:
				furl = re.search('a href="(http(\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv)(\S.*)redirect)"(\S.*)Download',str(link)).group(1)
				name = re.search('name=(\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv)',str(furl)).group(1)
				linkId= re.search('url=(\S.*)&amp',str(furl)).group(1)
				link = urllib2.unquote('http://imusicz.net/download.php?url='+linkId)
				name = BeautifulStoneSoup(name, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
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


