
import re
import urllib
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup

try:
	from functions import *
except:
	from GmediaFinder.functions import *

class Skreemr(object):
    def __init__(self,gui):
        self.gui = gui
        self.name="Skreemr"
        self.main_start_page = 1
        self.current_page = 1
        self.num_start = 1
        self.search_url = "http://skreemr.com/results.jsp?q=%s&l=10&s=%s"
        self.start_engine()


    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def uniq(self,input):
        output = []
        for x in input:
            if x not in output:
                output.append(x)
        return output

    def get_newest_videos(self, page=1, sort_by="rating"):
        return self.filter(BROWSE_URL % (sort_by, page))

    def get_top_rated(self, page=1, sort_by="week"):
        return self.filter(TOP_RATED_URL % (sort_by, page))

    def get_most_viewed(self, page=1, sort_by="week"):
        return self.filter(MOST_VIEWED_URL % (sort_by, page))

    def search(self, query, page):
        if page == 1:
            self.num_start = 1
        data = get_url_data(self.search_url % (urllib.quote(query), self.num_start))
        return self.filter(data,query)
        
    def filter(self,data,query):
		soup = BeautifulStoneSoup(data.decode('utf-8'),selfClosingTags=['/>'])
		nlist = []
		link_list = []
		next_page = 1
		results_div = soup.find('p',attrs={'class':'counter'})
		try:
			results_count = results_div.findAll('b')[1].string
		except:
			self.gui.changepage_btn.hide()
			self.gui.informations_label.set_text(_("No results found for %s...") % (query))
			self.num_start = 0
			self.current_page = 1
			self.gui.search_btn.set_sensitive(1)
			return
		if results_count == 0 :
			self.gui.informations_label.set_text(_("no results for your search : %s ") % (query))
			self.gui.search_btn.set_sensitive(1)
			return
		else:
			values = {'page': self.current_page, 'query': user_search}
			self.gui.informations_label.set_text(_("%(total)s results found for your search %(query)s") % values)
			self.gui.search_btn.set_sensitive(1)
			self.gui.changepage_btn.set_sensitive(1)
		
		pagination_table = soup.find('div',attrs={'class':'previousnext'})
		if pagination_table:
			next_check = pagination_table.findAll('a')
			for a in next_check:
				l = str(a.string)
				if l == "Next>>":
					next_page = 1
			if next_page:
				values = {'page': self.current_page, 'query': user_search, 'total' : results_count}
				self.gui.informations_label.set_text(_("Results page %(page)s for %(query)s...(%(total)s results)") % values)
				self.num_start += 10
				self.current_page += 1
				self.gui.search_btn.set_sensitive(1)
				self.gui.changepage_btn.set_sensitive(1)
				self.gui.changepage_btn.show()
			else:
				self.gui.changepage_btn.hide()
				self.num_start = 0
				self.current_page = 1
				self.gui.informations_label.set_text(_("no more files found for %s...") % (query))
				self.gui.search_btn.set_sensitive(1)
				return

		flist = soup.findAll('a',href=True)
		for link in flist:
			try:
				url = re.search('a href="(http(\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv))"',str(link)).group(1)
				link = urllib2.unquote(url)
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


