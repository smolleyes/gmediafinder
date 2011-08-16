import re
import urllib, urllib2
import gobject
from time import sleep
from subprocess import Popen,PIPE
import thread

try:
    from functions import *
    from config import data_path
except:
    from GmediaFinder.functions import *
    from GmediaFinder.config import data_path

class StreamLol(object):
    def __init__(self,gui):
        self.gui = gui
        self.name = "StreamLol"
        self.engine_type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.num_start = 1
        self.thread_stop = False
        self.adult_content = True
        self.has_browser_mode = True
        self.search_url = "http://www.streamlol.com/search.php"
        self.category_url = "http://www.streamlol.com/%s-film-%s-%s.html"
        self.index_url = "http://www.streamlol.com/%s-film-commence-par-%s.html"
        ## options labels
        self.index_label = _("Commence par: ")
        self.cat_label = _("Categorie: ")
        
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        ## create index combobox
        index = map(chr, range(97, 123))
        imap = {}
        imap[''] = ''
        imap['0-9'] = ''
        for l in index:
            imap[l] = ''
        self.orderbyOpt = {self.index_label:imap,
        }
        self.orderby = create_comboBox(self.gui, self.orderbyOpt)
        self.orderby.setIndexFromString('')
        ## cat index
        self.orderbyCat = {self.cat_label:{"":"0 ",_("Action"):"1 action",_("Arts martiaux"):"3 arts-martiaux",
                                            _("Biographies"):"5 biopic",_("Documentaire"):"7 documentaire",
                                            _("Romance"):"9 romance",_("Thriller"):"11 thriller",
                                            _("Drame"):"13 drame",_("Espionnage"):"15 espionnage",
                                            _("Guerre"):"17 guerre",_("Animation"):"2 animation",
                                            _("Aventure"):"4 aventure",_("Comedie"):"6 comedie",
                                            _("Policier"):"8 policier",_("Science-fiction"):"10 science-fiction",
                                            _("Western"):"12 western",_("Epouvante"):"14 epouvante",
                                            _("Fantastique"):"16 fantastique",_("Musical"):"18 musical",
            },
        }
        self.cat = create_comboBox(self.gui, self.orderbyCat)
        self.cat.setIndexFromString("")
        
    
    def get_search_url(self,query,page):
        return self.search(query,page)
    
    def search(self,query,page=None):
        response = None
        index = self.orderby.getSelected()
        catchoice = self.cat.getSelected()
        fcat = self.orderbyCat[self.cat_label][catchoice]
        cat = fcat.split(' ')[1]
        catid = fcat.split(' ')[0]
        if index != '' and query == '':
            response = urllib2.urlopen(self.index_url % (page,index))
        elif catchoice != '' and query == '':
            response = urllib2.urlopen(self.category_url % (catid,cat,page))
        else:
            values = {'search' : query}
            data = urllib.urlencode(values)
            req = urllib2.Request(self.search_url, data)
            response = urllib2.urlopen(req)
        return response
    
    def play(self,link):
        print link
        self.print_info("Recherche des liens...")
        valid_link = False
        megavideo_links = []
        videobb_links = []
        videozer_links = []
        dlfree_links = []
        megaupload_links = []
        data = get_url_data(link)
        if not data:
            self.print_info("Aucun lien detecte...")
            sleep(3)
            self.print_info("")
            return self.gui.start_play('http://')
        for line in data.readlines():
            if 'sur-megaupload.html' in line:
                link = urllib.unquote(re.search('href=\'(.*?)\'',line).group(1))
                megaupload_links.append(link)
            elif 'sur-videobb.html' in line:
                link = urllib.unquote(re.search('href=\'(.*?)\'',line).group(1))
                videobb_links.append(link)
            elif 'sur-videozer.html' in line:
                link = urllib.unquote(re.search('href=\'(.*?)\'',line).group(1))
                videozer_links.append(link)
            elif 'sur-dl.free.fr.html' in line:
                link = urllib.unquote(re.search('href=\'(.*?)\'',line).group(1))
                dlfree_links.append(link)
            elif 'sur-megavideo.html' in line:
                link = urllib.unquote(re.search('href=\'(.*?)\'',line).group(1))
                megavideo_links.append(link)
                
        link_list = dlfree_links+megaupload_links+videobb_links+videozer_links+megavideo_links
        if len(link_list) == 0:
            self.print_info("Aucun lien utilisable...")
            sleep(3)
            self.print_info("")
            return self.gui.start_play('http://')
        for link in link_list:
            if len(link_list) == 0:
                self.print_info("Aucun lien n'a pu etre utilise...")
                sleep(3)
                self.print_info("")
                return self.gui.start_play('http://')
            if 'sur-megaupload.html' in link:
                self.print_info("lien megaupload dispo !")
                link = "http://www.streamlol.com/"+link
                data = get_url_data(link)
                ## get megaupload link
                for line in data.readlines():
                    if 'http://www.megaupload.com/?d=' in line:
                        url = ''
                        try:
                            url = re.search('href=\'(.*?)\'',line).group(1)
                        except:
                            url = re.search('href=\"(.*?)\""',line).group(1)
                        opener = urllib2.build_opener(urllib2.HTTPHandler)
                        req = urllib2.Request('http://88.191.131.140/index.php/index.php', 'link=%s&pass=&x=0&y=0' % url)
                        response = opener.open(req)
                        for line in response.readlines():
                            if '<p>Lien 1' in line:
                                try:
                                    link = re.search('href="(.*?)"',line).group(1)
                                except:
                                    continue
                if self.start_link(link) == True:
                    self.gui.media_link = link
                    return self.gui.start_play(link)
                else:
                    continue
            elif 'sur-videobb.html' in link:
                #for l in megavideo_links:
                self.print_info("lien videobb dispo !")
                link = "http://www.streamlol.com/"+link
                data = get_url_data(link)
                ## get megaupload link
                for line in data.readlines():
                    if 'name="movie"' in line:
                        vid = urllib.unquote(re.search('value="(.*?)"',line).group(1).split('/')[-1])
                        cmd = os.path.join(data_path,'scripts','get_stream.py -u http://www.megaskipper.com/videobb.html?text=%s' % vid)
                        req = Popen(cmd,shell=True,stdout=PIPE)
                        link, err = req.communicate()
                        lineList = link.splitlines()
                        link = lineList[-1]
                if self.start_link(link):
                    self.gui.media_link = link
                    return self.gui.start_play(link)
                else:
                    continue
            elif 'sur-videozer.html' in link:
                #for l in megavideo_links:
                self.print_info("lien videozer dispo !")
                link = "http://www.streamlol.com/"+link
                data = get_url_data(link)
                ## get megaupload link
                for line in data.readlines():
                    if 'name="movie"' in line:
                        vid = urllib.unquote(re.search('value="(.*?)"',line).group(1).split('/')[-1])
                        cmd = os.path.join(data_path,'scripts','get_stream.py -u http://www.megaskipper.com/videozer.html?text=%s' % vid)
                        req = Popen(cmd,shell=True,stdout=PIPE)
                        link, err = req.communicate()
                        lineList = link.splitlines()
                        link = lineList[-1]
                if self.start_link(link):
                    self.gui.media_link = link
                    return self.gui.start_play(link)
                else:
                    continue
            elif 'sur-dl.free.fr.html' in link:
                self.print_info("lien dl.free.fr dispo !")
                link = "http://www.streamlol.com/"+link
                data = get_url_data(link)
                ## get free.fr link
                for line in data.readlines():
                    if 'getfile.pl' in line:
                        link = urllib.unquote(re.search('href=\'(.*?)\'',line).group(1))
                        data = get_url_data(link)
                        for line in data.readlines():
                            if 'charger ce fichier' in line:
                                link = urllib.unquote(re.search('href=\"(.*?)\"',line).group(1))
                if self.start_link(link):
                    self.gui.media_link = link
                    print link
                    return self.gui.start_play(link)
                else:
                    continue
            elif 'sur-megavideo.html' in link:
                self.print_info("lien megavideo dispo !")
                link = "http://www.streamlol.com/"+link
                data = get_url_data(link)
                ## get megaupload link
                for line in data.readlines():
                    if 'name="movie"' in line:
                        vid = re.search('value="(.*?)"',line).group(1).split('/')[-1]
                        cmd = os.path.join(data_path,'scripts','get_stream.py -u http://www.megaskipper.com/mvvideo.html?text=%s' % vid)
                        req = Popen(cmd,shell=True,stdout=PIPE)
                        link, err = req.communicate()
                        lineList = link.splitlines()
                        link = lineList[-1]
                if self.start_link(link) == True:
                    self.gui.media_link = link
                    return self.gui.start_play(link)
                else:
                    continue
            link_list.remove(link)
    
    def start_link(self, link):
        self.print_info("Lien Ok, verification...")
        request = urllib2.Request(link)
        request.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30')
        response = urllib2.urlopen(request)
        # check content type:
        content = response.info().getheader('Content-Type')
        print content
        if ('application/octet-stream' in content) or ('video/x-flv' in content):
            self.print_info("Lien valide!, lecture...")
            sleep(2)
            self.print_info("")
            return True
        else:
            self.print_info("Lien invalide!, analyse du lien suivant")
            return False

                        
    def filter(self,data,user_search):
        flag_found = False
        end_flag=True
        title=""
        markup=""
        link=""
        img=""
        for line in data.readlines():
            if self.thread_stop:
                break
            ## search link
            try:
                if 'class="thumb"' in line:
                    flag_found = True
                    l = re.search('href=\"(.*?)\"',line).group(1)
                    link = "http://www.streamlol.com/%s" % l
                    m = re.search('regarder-(.*?)-film',line).group(1)
                    title = re.sub('-',' ',m)
                    #print title, link, img, self.name
                elif '<img onerror=' in line:
                    img_link = re.search('src=\"(.*?)\"',line).group(1)
                    img = download_photo(img_link)
                    gobject.idle_add(self.gui.add_sound, title, link, img, None, self.name)
                ## check for next page
                elif 'id="navNext"' in line:
                    end_flag=False
                continue
            except:
                continue
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)

