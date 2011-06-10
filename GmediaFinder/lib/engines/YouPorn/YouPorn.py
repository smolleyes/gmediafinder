#-*- coding: UTF-8 -*-

from html5lib import HTMLParser
from html5lib.treebuilders import getTreeBuilder
import mechanize
import re
from urlparse import urljoin
import urllib, urllib2
import gtk
import time
import gobject
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup

try:
	from functions import create_comboBox
	from functions import download_photo
	from functions import get_url_data
	from functions import ComboBox
except:
	from GmediaFinder.functions import create_comboBox
	from GmediaFinder.functions import download_photo
	from GmediaFinder.functions import get_url_data
	from GmediaFinder.functions import ComboBox
	

URL = "http://youporn.com/"
ENTER_URL = "%s?user_choice=Enter" % URL
BROWSE_URL = "%sbrowse/%s?page=%s" % (URL, "%s", "%d")
TOP_RATED_URL = "%stop_rated/%s?page=%s" % (URL, "%s", "%d")
MOST_VIEWED_URL = "%smost_viewed/%s?page=%s" % (URL, "%s", "%d")
SEARCH_URL = "%ssearch/%s?query=%s&type=%s&page=%s" % (URL, "%s", "%s", "%s", "%d")

class YouPorn(object):
    def __init__(self,gui):
        self.gui = gui
        self.name ="YouPorn"
        self.type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.search_url = "http://www.youporn.com/search/%s?query=%s&type=%s&page=%s"
        self.parser = HTMLParser(tree=getTreeBuilder('beautifulsoup'))
        self.browser = mechanize.Browser()
        self.browser.addheaders = []
        self.browser.open(ENTER_URL)
        self.start_engine()


    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def load_gui(self):
        label = gtk.Label(_("Order by: "))
        self.gui.search_opt_box.pack_start(label,False,False,5)
        ## create orderby combobox
        cb = create_comboBox()
        self.orderbyOpt = {_("Most recent"):"time",_("Most viewed"):"views",
        _("Most rated"):"rating",_("Duration"):"duration",
        _("Most relevant"):"Relevance",
        }
        self.orderby = ComboBox(cb)
        for cat in self.orderbyOpt:
		    self.orderby.append(cat)
        self.gui.search_opt_box.add(cb)
        self.gui.search_opt_box.show_all()
        self.orderby.select(0)

    def filter(self, url,query):
        soup = self.parser.parse(self.browser.open(url))
        vid_list = []
        nlist = []
        next_page = 1
        results_div = soup.find('p',attrs={'class':'showing'})
        try:
			res = results_div.findAll('span')[1].string
			results_count = re.sub(',','',res)
        except:
			self.print_info(_("Youporn: No results for %s...") % (query))
			self.num_start = 0
			self.current_page = 1
			gobject.idle_add(self.gui.throbber.hide)
			time.sleep(5)
			self.print_info("")	
			return
        if int(results_count) == 0 :
			self.print_info(_("Youporn: No results for %s ") % (query))
			gobject.idle_add(self.gui.throbber.hide)
			time.sleep(5)
			self.print_info("")	
			return

        try:
		    pagination_table = soup.findAll('div',attrs={'id':'pages'})[0]
        except:
			gobject.idle_add(self.gui.throbber.hide)
			gobject.idle_add(self.gui.changepage_btn.hide)
			return
        if pagination_table:
			next_check = pagination_table.findAll('a')
			for a in next_check:
				l = str(a.string)
				if l == "Suivant »":
					next_page = 1
			if next_page:
				if self.current_page == 1:
					gobject.idle_add(self.gui.pageback_btn.hide)
				else:
					gobject.idle_add(self.gui.pageback_btn.show)
			else:
				gobject.idle_add(self.gui.changepage_btn.hide)
				self.current_page = 1
				self.print_info(_("Youporn: no results for %s...") % query)
				gobject.idle_add(self.gui.throbber.hide)
				time.sleep(5)
				self.print_info("")	
				return
		
			linelist = soup.find('div', {'id': "video-listing"}).findAll('ul', {'class': "clearfix"})
			for videos in linelist:
				vidlist = videos.findAll('li')
				for video in vidlist:
					try:
						img_link = video.find('img').attrMap['src']
						img = download_photo(img_link)
						name = video.find('img').attrMap['alt']
						vid_link = video.find('a').attrMap['href']
						markup="<small><b>%s</b></small>" % name
						gobject.idle_add(self.gui.add_sound,name, markup, vid_link, img, None, 'YouPorn')
					except:
						continue
			self.print_info("")
			gobject.idle_add(self.gui.throbber.hide)

    def search(self, query, page=1, sort_by="time", type="straight"):
		choice = self.orderby.getSelected()
		orderby = self.orderbyOpt[choice]
		self.filter(self.search_url % (orderby, urllib.quote(query), type, page), query)
        
    def play(self,link):
		data = get_url_data('http://www.youporn.com'+link)
		soup = BeautifulStoneSoup(data.decode('utf-8'),selfClosingTags=['/>'])
		data = soup.find('div',attrs={'id':'download'})
		d = urllib2.unquote(str(data))
		try:
			link = re.search('(.*)href=\"(.*?)\">MP4',d).group(2)
			self.gui.media_link = link
			return self.gui.start_play(link)
		except:
			return
			
    def print_info(self,msg):
		gobject.idle_add(self.gui.info_label.set_text,msg)
