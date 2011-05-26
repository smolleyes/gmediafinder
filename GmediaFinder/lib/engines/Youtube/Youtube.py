
import re
import urllib
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup

try:
	from functions import *
	from functions import YouTubeClient
	from functions import download_photo
except:
	from GmediaFinder.functions import *
	from GmediaFinder.functions import YouTubeClient
	from GmediaFinder.functions import download_photo

class Youtube(object):
    def __init__(self,gui):
        self.gui = gui
        self.current_page = 1
        self.main_start_page = 1
        self.num_start = 1
        self.name="Youtube"
        self.search_url = "http://tagoo.ru/en/search.php?for=audio&search=%s&page=%d&sort=date"
        self.youtube = YouTubeClient()
        self.start_engine()

    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def search(self, query, page):
        data = get_url_data(self.search_url % (urllib.quote(query), self.current_page))
        return self.filter(data,query)
        
    def filter(self,data,user_search):
		nlist = []
		link_list = []
		next_page = 0
		self.gui.changepage_btn.show()
		## get options
		params = None
		if self.gui.youtube_options.relevance_opt.get_active():
			params="&orderby=relevance"
		elif self.gui.youtube_options.recent_opt.get_active():
			params="&orderby=published"
		elif self.gui.youtube_options.viewed_opt.get_active():
			params="&orderby=viewCount"
		elif self.gui.youtube_options.rating_opt.get_active():
			params="&orderby=rating"
		
		if self.current_page == 1:
			self.num_start = 1
		else:
			self.num_start+=25
				
		vquery = self.youtube.search(user_search,self.num_start,params)
		if len(vquery) == 0:
			self.num_start = 1
			self.current_page = 1
			self.gui.search_btn.set_sensitive(1)
			self.gui.changepage_btn.hide()
			self.gui.informations_label.set_text(_("no more files found for %s...") % (user_search))
			self.gui.search_btn.set_sensitive(1)
			return
		self.gui.informations_label.set_text(_("Results page %s for %s...") % (self.current_page,user_search))
		self.num_start+=25
		self.current_page += 1
		
		for video in vquery:
			self.make_youtube_entry(video)
		self.gui.search_btn.set_sensitive(1)
		self.gui.changepage_btn.set_sensitive(1)

    def make_youtube_entry(self,video):
        url = video.link[1].href
        vid_id = os.path.basename(os.path.dirname(url))
        vid_pic = download_photo("http://i.ytimg.com/vi/%s/2.jpg" % vid_id)
        vid_title = video.title.text
        if not vid_title or not url or not vid_pic:
			return
        return self.gui.add_sound(vid_title, vid_id, vid_pic)
        
            






