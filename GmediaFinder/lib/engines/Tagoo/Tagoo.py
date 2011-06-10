import gobject
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
		try:
			soup = BeautifulStoneSoup(data.decode('utf-8'),selfClosingTags=['/>'])
		except:
			self.print_info(_("Tagoo: Connexion failed..."))
			gobject.idle_add(self.gui.throbber.hide)
			time.sleep(5)
			self.gui.info_label.set_text("")
			return
		next_page = 1
		results_div = soup.find('div',attrs={'class':'resultinfo'})
		try:
			results_count = re.search('Found about (\d+)', str(results_div)).group(1)
		except:
			gobject.idle_add(self.gui.changepage_btn.hide)
			self.print_info(_("Tagoo: No results for %s...") % user_search)
			gobject.idle_add(self.gui.throbber.hide)
			time.sleep(5)
			self.print_info("")
			return
		if results_count == 0 :
			self.print_info(_("Tagoo: No results for %s ") % user_search)
			gobject.idle_add(self.gui.throbber.hide)
			time.sleep(5)
			self.print_info("")
			return

		gobject.idle_add(self.gui.changepage_btn.show)
		if self.current_page != 1:
			gobject.idle_add(self.gui.pageback_btn.show)
		else:
			gobject.idle_add(self.gui.pageback_btn.hide)
			
		flist = [ each.get('href') for each in soup.findAll('a',attrs={'class':'link'}) ]
		for link in flist:
			try:
				link = urllib2.unquote(link)
				name = urllib2.unquote(os.path.basename(link.decode('utf-8')))
				try:
					markup="<small><b>%s</b></small>" % name
					gobject.idle_add(self.gui.add_sound,name, markup, link, None, None, self.name)
					i += 1
				except:
					continue
			except:
				continue
		self.print_info("")
		gobject.idle_add(self.gui.throbber.hide)

    def play(self,link):
		self.gui.media_link = link
		return self.gui.start_play(link)
		
    def print_info(self,msg):
		gobject.idle_add(self.gui.info_label.set_text,msg)
