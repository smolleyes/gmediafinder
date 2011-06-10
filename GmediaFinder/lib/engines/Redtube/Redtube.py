import re
import urllib
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup
import gobject

try:
	from functions import *
except:
	from GmediaFinder.functions import *

class Redtube(object):
    def __init__(self,gui):
        self.gui = gui
        self.name="Redtube"
        self.type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.search_url = "http://www.redtube.com/%s?search=%s&page=%s"
        self.category_url = "http://www.redtube.com/redtube/%s?sorting=%s&page=%s"
        self.start_engine()

    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def load_gui(self):
		## create categories combobox
        label = gtk.Label(_("Category: "))
        self.gui.search_opt_box.pack_start(label,False,False,5)
        cb = create_comboBox()
        self.category = ComboBox(cb)
        self.category.append("")
        self.catlist = {_("Amateur"):"amateur",_("Anal"):"anal",_("Asian"):"asian",
        _("Big tits"):"bigtits",_("Blowjob"):"blowjob",_("Cumshot"):"cumshot",
        _("Ebony"):"ebony",_("Facials"):"facials",_("Fetish"):"fetish",
        _("Gang bang"):"gangbang",_("Gay"):"gay",
        _("Group"):"group",_("Hentai"):"hentai",_("Interracial"):"interracial",
        _("Japanese"):"japanese",_("Latina"):"latina",
        _("Lesbian"):"lesbian",_("Masturbation"):"masturbation",_("Milf"):"milf",
        _("Mature"):"mature",_("Public"):"public",_("Squirting"):"squirting",
        _("Teens"):"teens",_("Wild & Crazy"):"wildcrazy"}
        catlist = sortDict(self.catlist)
        for cat in catlist:
			self.category.append(cat)
        self.gui.search_opt_box.add(cb)
        self.gui.search_opt_box.show_all()
        self.category.select(0)

    def search(self, query, page):
        data = get_url_data(self.search_url % ('new', urllib.quote(query), self.current_page))
        self.filter(data,query)
        
    def play(self,link):
		data = get_url_data(link)
		soup = BeautifulStoneSoup(data.decode('utf-8'),selfClosingTags=['/>'])
		data = soup.findAll('div',attrs={'id':'redtube_flv_player'})
		d = urllib2.unquote(str(data))
		try:
			link = re.search('mp4_url=(.*)&amp;',d).group(1)
			self.gui.media_link = link
			return self.gui.start_play(link)
		except:
			return
		
    def filter(self,data,user_search):
		d = unicode(data,errors='replace')
		soup = BeautifulStoneSoup(d.decode('utf-8'),selfClosingTags=['/>'])
		## reset the treeview
		nlist = []
		link_list = []
		img_list = []
		files_count = None
		try:
			#search results div
			count = soup.findAll('div',attrs={'class':'videosTable'})[0].findAll('h1')[0].string
			results_count = re.search('\((.*?)\)',count).group(1).replace(',','')
			if self.current_page != 1:
				gobject.idle_add(self.gui.pageback_btn.show)
			else:
				gobject.idle_add(self.gui.pageback_btn.hide)
		except:
			self.print_info(_("Redtube: No results for %s...") % user_search)
			gobject.idle_add(self.gui.changepage_btn.hide)
			gobject.idle_add(self.gui.throbber.hide)
			return
		
		if int(results_count) == 0:
			gobject.idle_add(self.gui.changepage_btn.hide)
			self.current_page = 1
			self.print_info(_("Redtube: No results for %s...") % user_search)
			gobject.idle_add(self.gui.throbber.hide)
			return
		
		flist = soup.findAll('div',attrs={'class':'video'})
		for video in flist:
			try:
				link = re.search('href="(.*?)"',str(video)).group(1)
				name = re.search('title="(.*?)"',str(video)).group(1).decode('UTF8')
				img_link = urllib2.unquote(re.search('src="(.*?)"',str(video)).group(1))
				img = download_photo(img_link)
				nlist.append(name)
				link_list.append(link)
				img_list.append(img)
			except:
				continue
		## add to the treeview if ok
		i = 0
		for name in nlist:
			if name and link_list[i]:
				markup="<small><b>%s</b></small>" % name
				gobject.idle_add(self.gui.add_sound,name, markup, 'http://www.redtube.com'+link_list[i], img_list[i],None,'Redtube')
				i += 1
				time.sleep(0.1)
		gobject.idle_add(self.gui.changepage_btn.show)
		self.print_info("")
		gobject.idle_add(self.gui.throbber.hide)

    def print_info(self,msg):
		gobject.idle_add(self.gui.info_label.set_text,msg)
