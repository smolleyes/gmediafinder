#-*- coding: UTF-8 -*-

from html5lib import HTMLParser
from html5lib.treebuilders import getTreeBuilder
import mechanize
import re
from urlparse import urljoin
import urllib
import gtk
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup

try:
	from functions import download_photo
except:
	from GmediaFinder.functions import download_photo

URL = "http://youporn.com/"
ENTER_URL = "%s?user_choice=Enter" % URL
BROWSE_URL = "%sbrowse/%s?page=%s" % (URL, "%s", "%d")
TOP_RATED_URL = "%stop_rated/%s?page=%s" % (URL, "%s", "%d")
MOST_VIEWED_URL = "%smost_viewed/%s?page=%s" % (URL, "%s", "%d")
SEARCH_URL = "%ssearch/%s?query=%s&type=%s&page=%s" % (URL, "%s", "%s", "%s", "%d")

class YouPorn(object):
    def __init__(self,gui):
        self.gui = gui
        self.name="YouPorn"
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
		pass

    def filter(self, url,query):
        soup = self.parser.parse(self.browser.open(url))
        vid_list = []
        nlist = []
        next_page = 1
        results_div = soup.find('p',attrs={'class':'showing'})
        try:
			results_count = results_div.findAll('span')[1].string
        except:
			self.gui.changepage_btn.hide()
			self.gui.info_label.set_text(_("No results found for %s...") % (query))
			self.num_start = 0
			self.current_page = 1
			self.gui.changepage_btn.hide()
			self.gui.throbber.hide()
			return
        if results_count == 0 :
			self.gui.info_label.set_text(_("No results for your search %s ") % (query))
			self.gui.changepage_btn.hide()
			self.gui.throbber.hide()
			return

        try:
		    pagination_table = soup.findAll('div',attrs={'id':'pages'})[0]
        except:
			self.gui.throbber.hide()
			self.gui.changepage_btn.hide()
			return
        if pagination_table:
			next_check = pagination_table.findAll('a')
			for a in next_check:
				l = str(a.string)
				if l == "Suivant »":
					next_page = 1
			if next_page:
				if self.current_page != 1:
					self.gui.pageback_btn.show()
				else:
					self.gui.pageback_btn.hide()
				self.gui.changepage_btn.show()
			else:
				self.gui.changepage_btn.hide()
				self.current_page = 1
				self.gui.info_label.set_text(_("no more files found for %s...") % (query))
				self.gui.throbber.hide()
				return
        
        for l in soup.findAll('a', href=True):
			try:
			    u = re.search('/watch/.*"',str(l)).group(0)
			    vid_list.append(u)
			except:
				continue
				
        imglist = soup.find('div', {'id': "video-listing"}).findAll('img', {'num': "8"})
        img_list = []
        for t in imglist:
            img_link = t.attrMap['src']
            img = download_photo(img_link)
            img_list.append(img)
        
        videos = self.uniq(vid_list)
        i=0
        for link in videos:
			markup="<small><b>%s</b></small>" % link.split('/')[3]
			self.gui.add_sound(link.split('/')[3], markup, self.get_video_url(link), img_list[i])
			i+=1
        self.gui.changepage_btn.show()
        self.gui.info_label.set_text("")
        self.gui.throbber.hide()

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

    def search(self, query, page=1, sort_by="time", type="straight"):
        gtk.gdk.threads_enter()
        self.filter(self.search_url % (sort_by, urllib.quote(query), type, page), query)
        gtk.gdk.threads_leave()
        
    def get_video_url(self, url):
        try:
			download = lambda href: '/download/' in href
        except:
            return
        try:
			soup = self.parser.parse(self.browser.open(url))
        except:
			return
        try:
			down = soup.find('div', {'id': "download"}).findAll('a')[1]['href']
        except:
			down = soup.find('div', {'id': "download"}).findAll('a')[0]['href']
        return down
