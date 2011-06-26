import re
import urllib
import gobject

try:
    from functions import *
except:
    from GmediaFinder.functions import *

class Xvideos(object):
    def __init__(self,gui):
        self.gui = gui
        self.name="Xvideos"
        self.type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.thread_stop=False
        self.adult_content=True
        self.search_url = "http://www.xvideos.com/?k=%s"
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        ### create categories combobox
        #label = gtk.Label(_("Category: "))
        #self.gui.search_opt_box.pack_start(label,False,False,5)
        #cb = create_comboBox()
        #self.category = ComboBox(cb)
        #self.category.append("")
        #self.catlist = {_("Amateur"):"amateur",_("Anal"):"anal",_("Asian"):"asian",
        #_("Big tits"):"bigtits",_("Blowjob"):"blowjob",_("Cumshot"):"cumshot",
        #_("Ebony"):"ebony",_("Facials"):"facials",_("Fetish"):"fetish",
        #_("Gang bang"):"gangbang",_("Gay"):"gay",
        #_("Group"):"group",_("Hentai"):"hentai",_("Interracial"):"interracial",
        #_("Japanese"):"japanese",_("Latina"):"latina",
        #_("Lesbian"):"lesbian",_("Masturbation"):"masturbation",_("Milf"):"milf",
        #_("Mature"):"mature",_("Public"):"public",_("Squirting"):"squirting",
        #_("Teens"):"teens",_("Wild & Crazy"):"wildcrazy"}
        #catlist = sortDict(self.catlist)
        #for cat in catlist:
            #self.category.append(cat)
        #self.gui.search_opt_box.add(cb)
        #self.gui.search_opt_box.show_all()
        #self.category.select(0)
        pass
       
    
    def get_search_url(self,query,page):
        if page > 1:
        	query = '%s&p=%s' % (query, page-1)
        return self.search_url % (query)
    
    def play(self, link):
        data = get_url_data(link)
        for line in data.readlines():
            if 'flv_url=' in line:
                link = urllib.unquote(re.search('flv_url=([^&]*)', line).group(1))
                self.gui.media_link = link
                break
        return self.gui.start_play(link)
        
    def filter(self,data,user_search):
        flag_found = False      
        for line in data.readlines():
            if self.thread_stop == True:
                break
            ## search link
            if '"miniature"' in line:
                link = re.search('href=\"(.*?)\"', line).group(1)
                img = re.search('src=\"(.*?)\"', line).group(1)
                img = download_photo(img)
                continue
            if 'underline;">' in line:
                title = line.split('>')[1].split('<')[0]
                continue
            if 'ng>(' in line:
                duration = '  <small>%s</small>' % line.split('>')[1].split('<')[0]
                gobject.idle_add(self.gui.add_sound, title, link, img, None, self.name, duration)
                flag_found = True
                continue
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
