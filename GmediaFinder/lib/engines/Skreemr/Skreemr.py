
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
        self.type = "audio"
        self.results_by_page = 10
        self.main_start_page = 1
        self.current_page = 1
        self.num_start = 1
        self.search_url = "http://skreemr.com/results.jsp?q=%s&l=10&s=%s"
        self.start_engine()


    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def load_gui(self):
		pass

    def uniq(self,input):
        output = []
        for x in input:
            if x not in output:
                output.append(x)
        return output

    def search(self, query, page):
        if page == 1:
            self.num_start = 1
        data = get_url_data(self.search_url % (urllib.quote(query), self.num_start))
        self.filter(data,query)
        
    def filter(self,data,query):
		try:
			soup = BeautifulStoneSoup(data.decode('utf-8'),selfClosingTags=['/>'])
		except:
			return
		nlist = []
		link_list = []
		next_page = 1
		results_div = soup.find('p',attrs={'class':'counter'})
		try:
			results_count = results_div.findAll('b')[1].string
		except:
			gobject.idle_add(self.gui.changepage_btn.hide)
			self.print_info(_("Skreemr: No results found for %s...") % query)
			self.num_start = 1
			self.current_page = 1
			gobject.idle_add(self.gui.throbber.hide)
			time.sleep(5)
			self.print_info("")	
			return
		if results_count == 0 :
			self.print_info(_("Skreemr: No results found for %s ") % query)
			gobject.idle_add(self.gui.throbber.hide)
			time.sleep(5)
			self.print_info("")	
			return
		else:
			if self.current_page == 1:
				gobject.idle_add(self.gui.pageback_btn.hide)
			else:
				gobject.idle_add(elf.gui.pageback_btn.show)
		
		pagination_table = soup.find('div',attrs={'class':'previousnext'})
		if pagination_table:
			next_check = pagination_table.findAll('a')
			for a in next_check:
				l = str(a.string)
				if l == "Next>>":
					next_page = 1
			if next_page:
				gobject.idle_add(self.gui.changepage_btn.show)
			else:
				gobject.idle_add(self.gui.changepage_btn.hide)
				self.num_start = 0
				self.current_page = 1
				self.print_info(_("Skreemr: No results found for %s...") % query)
				gobject.idle_add(self.gui.throbber.hide)
				time.sleep(5)
				self.print_info("")	
				return

		flist = soup.findAll('a',href=True)
		for link in flist:
			try:
				url = re.search('a href="(http(\S.*)(.mp3|.mp4|.ogg|.aac|.wav|.wma|.wmv|.avi|.mpeg|.mpg|.ogv))"',str(link)).group(1)
				link = urllib2.unquote(url)
				name = urllib2.unquote(os.path.basename(link.decode('utf-8')))
				markup="<small><b>%s</b></small>" % name
				gobject.idle_add(self.gui.add_sound,name, markup, link_list, None, None, self.name)
			except:
				continue
		self.print_info("")
		gobject.idle_add(self.gui.throbber.hide)
		
    def print_info(self,msg):
		gobject.idle_add(self.gui.info_label.set_text,msg)

