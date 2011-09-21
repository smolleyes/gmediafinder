import urllib2
import gobject
import json
import datetime
try:
    from functions import *
except:
    from GmediaFinder.functions import *


class Jamendo(object):
    def __init__(self,gui):
        self.gui = gui
        self.name = 'Jamendo'
        self.engine_type = "audio"
        self.options_dic = {}
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.has_browser_mode = True
        ## options labels
        self.order_label = _("Order by: ")
        self.tag_label = _("Tag: ")
        self.search_url = 'http://api.jamendo.com/get2/name+stream+album_name+artist_name+album_id+duration/track/json/track_album+album_artist/?n=20&pn=%s&order=%s_desc&tag_idstr=%s'       
        self.thumb_url = 'http://api.jamendo.com/get2/image/album/redirect/?id=%s&imagesize=100'
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):       
        self.order_list = {self.order_label:{_("Date of release"):"releasedate", _("Average rating"):"rating",
                                             _("Week rating"):"ratingweek", _("Month rating"):"ratingmonth",
                                             _("Listened"):"listened", _("Starred"):"starred", _("Tag relevant"):"weight",
                                            },
                           }
        self.orderby = create_comboBox(self.gui, self.order_list)
        try:
			data = urllib2.urlopen('http://www.jamendo.com/fr/tags')
        except:
			return
        self.order_tag = {self.tag_label: {"":""}, }
        for line in data.readlines():
            if 'g_tag_name' in line:
        	    l = re.findall('chargement de musique libre : ([^"]*)',line)
        	    for i in l:
        	    	self.order_tag[self.tag_label][i] = i
        self.ordertag = create_comboBox(self.gui, self.order_tag)
        self.orderby.setIndexFromString(_("Date of release"))
        self.ordertag.setIndexFromString(_("music"))
               
    def get_search_url(self,query,page):
        choice = self.orderby.getSelected()
        orderby = self.order_list[self.order_label][choice]
        tag = self.ordertag.getSelected()     
        return self.search_url % (page, orderby, tag)
    
    def play(self, link):      
        self.gui.media_link = link
        return self.gui.start_play(link)
        
    def filter(self,data,user_search):
        js = json.load(data)
        for i in js:
            if self.thread_stop == True:
                break
            duration = i[u'duration']
            artist = i['artist_name']
            name = i["name"]
            link = i["stream"]
            album = i['album_name']
            title = '%s - %s' % (artist, name)
            pic = self.thumb_url % i[u'album_id']
            tmp = get_redirect_link(pic)
            img = download_photo(tmp)
            mark = '\n<small><b>Duration: </b>%s  <b>Album: </b>%s</small>' % (str(datetime.timedelta(seconds=duration)),
                                                                                            album)
            gobject.idle_add(self.gui.add_sound, title, link, img, None, self.name, mark)
        self.thread_stop=True
        
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
