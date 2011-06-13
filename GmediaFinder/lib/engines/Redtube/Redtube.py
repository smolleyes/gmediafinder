import re
import urllib
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
        self.thread_stop=False
        self.search_url = "http://www.redtube.com/%s?search=%s&page=%s"
        self.category_url = "http://www.redtube.com/redtube/%s?sorting=%s&page=%s"
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
        
        label = gtk.Label(_("Order by: "))
        self.gui.search_opt_box.pack_start(label,False,False,5)
        ## create orderby combobox
        cb = create_comboBox()
        self.orderbyOpt = {_("Most recent"):"new",_("Most viewed"):"mostviewed",
        _("Most rated"):"top",_("Most relevant"):"",
        }
        self.orderby = ComboBox(cb)
        for cat in self.orderbyOpt:
            self.orderby.append(cat)
        self.gui.search_opt_box.add(cb)
        self.gui.search_opt_box.show_all()
        self.orderby.select(0)
    
    def search(self, query, page):
        self.thread_stop=False
        choice = self.orderby.getSelected()
        orderby = self.orderbyOpt[choice]
        try:
            data = get_url_data(self.search_url % (orderby, urllib.quote(query), self.current_page))
            self.filter(data,query)
        except:
            self.print_info(_("%s: connexion failed...") %  self.name)
            time.sleep(5)
            self.thread_stop=True
    
    def play(self,link):
        data = get_url_data(link)
        for line in data.readlines():
            if 'mp4_url=' in line:
                link = urllib.unquote(re.search('mp4_url=(.*)&',line).group(1))
                self.gui.media_link = link
                break
        return self.gui.start_play(link)
        
    def filter(self,data,user_search):
        flag_found = False
        end_flag=True
        title=""
        markup=""
        link=""
        for line in data.readlines():
            if self.thread_stop == True:
                break
            ## search link
            if 'class="s"' in line:
                flag_found = True
                l = re.search('href=\"(.*?)\"',line).group(1)
                link = "http://www.redtube.com%s" % l
                title = re.search('title=\"(.*?)\"',line).group(1)
                markup="<small><b>%s</b></small>" % title
            elif 'class="t"' in line:
                img_link = re.search('src=\"(.*?)\"',line).group(1)
                img = download_photo(img_link)
                gobject.idle_add(self.gui.add_sound, title, markup, link, img, None, self.name)
            ## check for next page
            elif 'id="navNext"' in line:
                end_flag=False
            continue
            
        if flag_found:
            if end_flag:
                gobject.idle_add(self.gui.changepage_btn.hide)
            else:
                gobject.idle_add(self.gui.changepage_btn.show)
            if self.current_page != 1:
                gobject.idle_add(self.gui.pageback_btn.show)
            else:
                gobject.idle_add(self.gui.pageback_btn.hide)
        else:
            gobject.idle_add(self.gui.changepage_btn.hide)
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
