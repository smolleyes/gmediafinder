
import re
import urllib
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup

try:
	from functions import *
except:
	from GmediaFinder.functions import *
	
class Tagoo(object):
    def __init__(self,gui):
        self.gui = gui
        self.current_page = 1
        self.main_start_page = 1
        self.name="Tagoo"
        self.search_url = "http://tagoo.ru/en/search.php?for=audio&search=%s&page=%d&sort=date"
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
		results_div = soup.find('div',attrs={'class':'resultinfo'})
		try:
			results_count = re.search('Found about (\d+)', str(results_div)).group(1)
		except:
			self.gui.changepage_btn.hide()
			self.gui.informations_label.set_text(_("No results found for %s...") % (user_search))
			self.gui.search_btn.set_sensitive(1)
			return
		if results_count == 0 :
			self.gui.informations_label.set_text(_("no results for your search : %s ") % (user_search))
			self.gui.search_btn.set_sensitive(1)
			return
		else:
			self.gui.informations_label.set_text(_("%s results found for your search : %s ") % (results_count, user_search))
			self.gui.search_btn.set_sensitive(1)
			self.gui.changepage_btn.set_sensitive(1)
		try:
		    pagination_table = soup.findAll('div',attrs={'class':'pages'})[0]
		except:
			return
		if pagination_table:
			next_check = pagination_table.findAll('a')
			for a in next_check:
				l = str(a.string)
				if l == "Next":
					next_page = 1
			if next_page:
				self.gui.informations_label.set_text(_("Results page %s for %s...(%s results)") % (self.current_page, user_search,results_count))
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

		flist = [ each.get('href') for each in soup.findAll('a',attrs={'class':'link'}) ]
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
				try:
				    self.gui.add_sound(name, link_list[i])
				    i += 1
				except:
					continue

