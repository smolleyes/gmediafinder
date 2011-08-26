import gobject
import time
import mechanize
import os

try:
    from functions import *
except:
    from GmediaFinder.functions import *
    
class NuttyMp3(object):
    def __init__(self, gui):    
        self.gui = gui
        self.name="NuttyMp3"
        self.engine_type = "audio"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.has_browser_mode = False
        self.order_label = _("Order by: ")
        self.duration_label = _("Duration: ")
        self.size_label = _("Size: ")
        self.bitrate_label = _("Bitrate: ")
        self.search_url = "http://www.nuttymp3.com/%s/%s/%s"
        self.browser = mechanize.Browser()
        self.browser.addheaders = []
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        self.order_list = { self.order_label:{ _("Relevance"):"download",
                                               _("Popularity"):"rate", _("Added date"):"date",
                                               _("Downloads"):"downloads", _("Bitrate"):"bitrate",
                                               _("Duration"):"duration", _("Size"):"size",
                                             },
                                             
                          }
        self.orderby = create_comboBox(self.gui, self.order_list)
        
    def get_search_url(self,query,page):              
        choice = self.orderby.getSelected()
        orderby = self.order_list[self.order_label][choice]
        if orderby == 'download':
            arg = orderby
        else:
            arg = 'sort/%s' % orderby
        return self.search_url % (arg, query, page)
        
    def filter(self, data, user_search):        
        flag = False
        flag_found = False
        for line in data.readlines():
            if self.thread_stop == True:
                break           
            if 'title="Download' in line:
                flag_found = True
                l = line.split('"')
                suff = l[7]
                titre = l[11].replace('Download','')
                name, ext = os.path.splitext(titre)
                url = 'http://www.nuttymp3.com%s' % suff
                continue
            if not flag and 'class="current last"' in line:
                self.print_info(_("%s: No results for %s...") % (self.name,user_search))
                time.sleep(5)
                self.print_info('')
                flag = True
                continue
            if '>Size:' in line:
                size = line.split('>')[3].split('<')[0]
                continue
            if '>Duration:' in line:
                dur = line.split('>')[3].split('<')[0]
                continue
            if '>Bitrate:' in line:
                bit = line.split('>')[3].split('<')[0]
                mark = '\n<small> <b>%s</b> %s   <b>%s</b> %s<b>   %s</b> %s</small>' % (self.duration_label, dur, self.bitrate_label, bit, self.size_label, size)
                gobject.idle_add(self.gui.add_sound, name, url, None, None, self.name, mark)               
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
        
    def play(self,link):
        self.browser.open(link)
        self.browser.select_form(nr=2)
        r = self.browser.submit()
        data = r.read()
        link = data.split("'")[1]
        self.gui.media_link = link
        return self.gui.start_play(link)
        
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
