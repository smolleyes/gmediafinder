

import re
import urllib
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup

try:
	from functions import *
except:
	from GmediaFinder.functions import *

class Dilandau(object):
    def __init__(self,gui):
        self.gui = gui
        self.name="Dilandau"
        self.current_page = 1
        self.main_start_page = 1
        self.search_url = "http://fr.dilandau.com/telecharger_musique/%s-%d.html"
        self.start_engine()


    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def search(self, query, page):
        data = get_url_data(self.search_url % (urllib.quote(query), self.current_page))
        return self.filter(data,query)
        
    def filter(self,data,user_search):
		soup = BeautifulStoneSoup(data.decode('utf-8'),selfClosingTags=['/>'])
		nlist = []
		link_list = []
		next_page = 1
		try:
			pagination_table = soup.findAll('div',attrs={'class':'pages'})[0]
		except:
			self.gui.changepage_btn.hide()
			self.gui.informations_label.set_text(_("no files found for %s...") % (user_search))
			self.gui.search_btn.set_sensitive(1)
			self.gui.changepage_btn.hide()
			return
		if pagination_table:
			next_check = pagination_table.findAll('a',attrs={'class':'pages'})
			for a in next_check:
				l = str(a.string)
				if l == "Suivante >>":
					next_page = 1
			if next_page:
				values = {'page': self.current_page, 'query': user_search}
				self.gui.informations_label.set_text(_("Results page %(page)s for %(query)s...(Next page available)") % values)
				self.current_page += 1
				self.gui.changepage_btn.show()
				self.gui.search_btn.set_sensitive(1)
				self.gui.changepage_btn.set_sensitive(1)
			else:
				self.gui.changepage_btn.hide()
				self.current_page = 1
				self.gui.informations_label.set_text(_("no more files found for %s...") % (user_search))
				self.gui.search_btn.set_sensitive(1)
				return

		flist = [ each.get('href') for each in soup.findAll('a',attrs={'class':'button download_button'}) ]
		for link in flist:
			try:
				link = urllib2.unquote(link)
				name = urllib2.unquote(os.path.basename(link.decode('utf-8')))
				nlist.append(name)
				link_list.append(link)
			except:
				continue
		## add to the treeview if ok
		i = 0
		for name in nlist:
			if name and link_list[i]:
				self.gui.add_sound(name, link_list[i])
				i += 1


