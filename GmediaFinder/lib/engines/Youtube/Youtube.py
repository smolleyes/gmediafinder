
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
        self.client = gdata.youtube.service.YouTubeService()
        self.start_engine()

    def start_engine(self):
		self.gui.engine_list[self.name] = ''

    def search(self,user_search,page):
		nlist = []
		link_list = []
		next_page = 0
		self.gui.changepage_btn.show()
		## prepare query
		query = yt_service.YouTubeVideoQuery()
		query.vq = user_search # the term(s) that you are searching for
		query.max_results = '25'
		if self.gui.youtube_options.relevance_opt.get_active():
			query.orderby = 'relevance'
		elif self.gui.youtube_options.recent_opt.get_active():
			query.orderby = 'published'
		elif self.gui.youtube_options.viewed_opt.get_active():
			query.orderby = 'viewCount'
		elif self.gui.youtube_options.rating_opt.get_active():
			query.orderby = 'rating'
		
		if self.current_page == 1:
			self.num_start = 1
		else:
			self.num_start+=25
		query.start_index = self.num_start
		vquery = self.client.YouTubeQuery(query)
		
		if not vquery :
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
		
		for entry in vquery.entry:
			self.make_youtube_entry(entry)
		self.gui.search_btn.set_sensitive(1)
		self.gui.changepage_btn.set_sensitive(1)

    def make_youtube_entry(self,video):
		#import pprint
		#pprint.pprint(video.__dict__)
		url = video.link[1].href
		count = 0
		try:
			count = video.statistics.view_count
		except:
			pass
		vid_id = os.path.basename(os.path.dirname(url))
		vid_pic = download_photo("http://i.ytimg.com/vi/%s/2.jpg" % vid_id)
		vid_title = video.title.text
		if not vid_title or not url or not vid_pic:
			return
		self.gui.add_sound(vid_title, vid_id, vid_pic,None,count)
        
            






