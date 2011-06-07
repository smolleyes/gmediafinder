import re
import urllib
from BeautifulSoup import BeautifulSoup, NavigableString, BeautifulStoneSoup
import gdata.youtube.service as yt_service

try:
	from functions import *
	from functions import download_photo
	from functions import ComboBox
	from functions import sortDict
except:
	from GmediaFinder.functions import *
	from GmediaFinder.functions import download_photo
	from GmediaFinder.functions import ComboBox
	from GmediaFinder.functions import sortDict

class Youtube(object):
    def __init__(self,gui):
        self.gui = gui
        self.current_page = 1
        self.main_start_page = 1
        self.num_start = 1
        self.results_by_page = 25
        self.name="Youtube"
        self.client = yt_service.YouTubeService()
        self.start_engine()
        ## the gui box to show custom filters/options
        self.opt_box = self.gui.gladeGui.get_widget("search_options_box")

    def start_engine(self):
		self.gui.engine_list[self.name] = ''
		
    def load_gui(self):
        label = gtk.Label(_("options: "))
        self.gui.search_opt_box.pack_start(label,False,False,5)
        ## create orderby combobox
        cb = create_comboBox()
        self.orderbyOpt = {_("Most relevant"):"relevance",
        _("Most recent"):"published",_("Most viewed"):"viewCount",
        _("Most rated"):"rating"
        }
        self.orderby = ComboBox(cb)
        for cat in self.orderbyOpt:
		    self.orderby.append(cat)
        self.gui.search_opt_box.add(cb)
        ## create categories combobox
        label = gtk.Label(_("Category: "))
        self.gui.search_opt_box.pack_start(label,False,False,5)
        cb = create_comboBox()
        self.category = ComboBox(cb)
        self.category.append("")
        self.catlist = {_("Sport"):"Sports",_("Films"):"Film",_("Cars"):"Autos",
        _("Music"):"Music",_("Technology"):"Tech",_("Animals"):"Animals",
        _("Travel"):"Travel",_("Games"):"Games",_("Comedy"):"Comedy",
        _("Peoples"):"People",_("News"):"News",
        _("Entertainement"):"Entertainment",_("Trailers"):"Trailers"}
        catlist = sortDict(self.catlist)
        for cat in catlist:
			self.category.append(cat)
        self.gui.search_opt_box.add(cb)
		
        self.gui.search_opt_box.show_all()
        self.gui.youtube_video_rate.show()
        self.orderby.select(0)
        self.category.select(0)

    def search(self,user_search,page):
		nlist = []
		link_list = []
		next_page = 0
		gtk.gdk.threads_enter()
		self.gui.changepage_btn.show()
		gtk.gdk.threads_leave()
		## prepare query
		query = yt_service.YouTubeVideoQuery()
		query.vq = user_search # the term(s) that you are searching for
		query.max_results = '25'
		#query.lr = 'fr'
		orderby = self.orderby.getSelected()
		query.orderby = self.orderbyOpt[orderby]
		cat = self.category.getSelected()
		if self.category.getSelectedIndex() != 0:
			query.categories.append('/%s' % self.catlist[cat])
		
		if self.current_page == 1:
			gtk.gdk.threads_enter()
			self.gui.pageback_btn.hide()
			gtk.gdk.threads_leave()
			self.num_start = 1
		else:
			gtk.gdk.threads_enter()
			self.gui.pageback_btn.show()
			gtk.gdk.threads_leave()
		query.start_index = self.num_start
		vquery = self.client.YouTubeQuery(query)
		self.filter(vquery,user_search)
		
    def filter(self,vquery,user_search):
		if not vquery :
			self.num_start = 1
			self.current_page = 1
			gtk.gdk.threads_enter()
			self.gui.changepage_btn.hide()
			self.pageback_btn.hide()
			self.gui.info_label.set_text(_("no more files found for %s ...") % (user_search))
			self.gui.throbber.hide()
			gtk.gdk.threads_leave()
			return
		
		if len(vquery.entry) == 0:
			gtk.gdk.threads_enter()
			self.gui.info_label.set_text(_("no results for %s ...") % (user_search))
			self.gui.throbber.hide()
			gtk.gdk.threads_leave()
			return
		
		gtk.gdk.threads_enter()
		for entry in vquery.entry:
			self.make_youtube_entry(entry)
		self.gui.throbber.hide()
		self.gui.info_label.set_text("")
		gtk.gdk.threads_leave()
		return
		

    def make_youtube_entry(self,video):
		#import pprint
		#pprint.pprint(video.__dict__)
		duration = video.media.duration.seconds
		calc = divmod(int(duration),60)
		seconds = int(calc[1])
		if seconds < 10:
			seconds = "0%d" % seconds
		duration = "%d:%s" % (calc[0],seconds)
		url = video.link[1].href
		thumb = video.media.thumbnail[-1].url
		count = 0
		try:
			count = video.statistics.view_count
		except:
			pass
		vid_id = os.path.basename(os.path.dirname(url))
		vid_pic = download_photo(thumb)
		title = video.title.text
		if not count:
			count = 0
		
		values = {'name': title, 'count': count, 'duration': duration}
		markup = _("<small><b>%(name)s</b></small>\n<small><b>view:</b> %(count)s		<b>Duration:</b> %(duration)s</small>") % values
		if not title or not url or not vid_pic:
			return
		self.gui.add_sound(title, markup, vid_id, vid_pic,None,self.name)
            






