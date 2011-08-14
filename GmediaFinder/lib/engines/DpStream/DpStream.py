import re
import urllib, urllib2
import gobject
from time import sleep
from subprocess import Popen,PIPE,STDOUT
import mechanize

try:
    from functions import *
    from config import data_path
except:
    from GmediaFinder.functions import *
    from GmediaFinder.config import data_path

class DpStream(object):
    def __init__(self,gui):
        self.gui = gui
        self.name = "DpStream"
        self.engine_type = "video"
        self.current_page = 1
        self.main_start_page = 1
        self.num_start = 1
        self.thread_stop = False
        self.adult_content = True
        self.initialized = False
        self.valid_url = False
        self.has_browser_mode = True
        self.browser = mechanize.Browser()
        self.browser.addheaders = [('User-Agent','Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30')]
        self.search_url = "http://www.dpstream.net/index.php?action=rfilm&recherche=%s"
        self.category_url = "http://www.dpstream.net/?action=%s&p=--%s-%s-%s" ## search_type/page/cat/orderby
        self.index_url = "http://www.dpstream.net/?action=%s&p=-%s-%s--" # search_type/letter/page
        ## options labels
        self.search_type = _('Search type: ')
        self.order_label = _('Order by: ')
        self.index_label = _('Begin by: ')
        self.cat_label = _('Category: ')
        
        self.start_engine()
    
    def start_engine(self):
        self.gui.engine_list[self.name] = ''
    
    def load_gui(self):
        ## order by
        self.orderByOpt = {self.order_label:{_("Alphabetique"):0,
                        _("Chronologique"):1,
                        },
        }
        self.orderby = create_comboBox(self.gui, self.orderByOpt)
        self.orderby.setIndexFromString('Chronologique')
        
        ## create index combobox
        index = map(chr, range(97, 123))
        imap = {}
        imap[''] = ''
        imap['0..9'] = ''
        for l in index:
            imap[l] = ''
        self.indexOpt = {self.index_label:imap,
        }
        self.index = create_comboBox(self.gui, self.indexOpt)
        self.index.setIndexFromString('')
        ## cat index
        self.orderbyCat = {self.cat_label:{"":"",_("Tous"):0,_("Documentaire"):1,
                                            _("Spectacles"):2,_("Action"):3,
                                            _("Animation"):4,_("Aventure"):5,
                                            _("Biographie"):6,_("Catastrophe"):7,
                                            _("Comedie"):8,_("Conte"):9,
                                            _("Crime"):10,_("Dessin-anime"):11,
                                            _("Drame"):12,_("Espionnage"):13,
                                            _("Fantastique"):14,_("Guerre"):15,
                                            _("Histoire"):16,_("Horreur"):17,
                                            _("Musical"):18,_("Policier"):19,
                                            _("Romance"):20,_("Science-fiction"):21,
                                            _("Sport"):22,_("Thriller"):23,
                                            _("Western"):24,
            },
        }
        self.cat = create_comboBox(self.gui, self.orderbyCat)
        self.cat.setIndexFromString("Tous")
        
    
    def get_search_url(self,query,page):
        return self.search(query,page)
    
    def search(self,query,page=1):
        self.valid_url = False
        data = None
        if not self.initialized:
            self.browser.open('http://www.dpstream.net')
            self.initialized = True
        index = self.index.getSelected()
        order = self.orderby.getSelected()
        orderid = self.orderByOpt[self.order_label][order]
        catchoice = self.cat.getSelected()
        catid = self.orderbyCat[self.cat_label][catchoice]
        if index != '' and query == '':
            print self.index_url % ('film',index,page)
            data = self.browser.open(self.index_url % ('film',index,page))
        elif catchoice != '' and query == '':
            print self.category_url % ('film',page,catid,orderid)
            data = self.browser.open(self.category_url % ('film',page,catid,orderid))
        else:
            link = self.search_url % query.replace(' ','+')
            try:
                data = self.browser.open(link)
            except:
                self.print_info("Impossible de charger la page...")
                sleep(3)
                self.print_info("")
                return
        return data
    
    def play(self,link):
        print link
        self.valid_url = False
        self.media_link = ''
        self.print_info("Recherche des liens...")
        full_list, global_links , direct_links = self.get_stream_links(link) 
        if len(full_list) == 0:
            self.print_info("Aucun lien utilisable...")
            sleep(3)
            self.print_info("")
            return self.gui.start_play('http://')
        ## if we have only a direct link
        if len(direct_links) > 0:
            res = self.scan_direct_links(direct_links)
            if res == True:
                self.gui.media_link = self.media_link
                return self.gui.start_play(self.media_link)
            else:
                return self.gui.start_play('')
        ## else start scan
        else:
            for link in global_links:
                if self.valid_url:
                    break
                if len(global_links) == 0:
                    self.print_info("Aucun lien n'a pu etre utilise...")
                    sleep(3)
                    self.print_info("")
                    return self.gui.start_play('http://')
                else:
                    global_links.remove(link)
                    t, r, direct_links = self.get_stream_links(link)
                    res = self.scan_direct_links(direct_links)
                    if res == True:
                        self.gui.media_link = link
                        return self.gui.start_play(self.media_link)
                    else:
                        continue
    
    def get_stream_links(self,link):
        megavideo_links = []
        videobb_links = []
        global_links=[]
        try:
            data = self.browser.open(link)
        except:
            return
        for line in data.readlines():
            try:
                if 'href="film' in line and 'streaming' in line:
                    link = urllib.unquote(re.search('href="(.*?)"',line).group(1))
                    global_links.append('http://www.dpstream.net/' + link)
                elif 'http://www.videobb.com/e/' in line:
                    print line
                    link = urllib.unquote(re.search('value="(.*?)"',line).group(1))
                    videobb_links.append(link)
                elif 'megavideo' in line or 'MegaVideo' in line:
                    print line
                    link = urllib.unquote(re.search('src="(.*?)"',line).group(1))
                    megavideo_links.append(link)
                else:
                    continue
            except:
                continue
                
        full_list = global_links+videobb_links+megavideo_links
        direct_links = videobb_links+megavideo_links
        print 'FLISTTTT %s' % full_list
        return full_list, global_links, direct_links       
    
    
    def scan_direct_links(self,vid_list):
        vtype = ''
        vid = ''
        for link in vid_list:
            try:
                if 'videobb' in link:
                    self.print_info('Lien videobb detecte, analyse...')
                    vtype = 'videobb'
                    vid = link.split('/')[-1]
                elif 'megavideo' in link:
                    self.print_info('Lien megavideo detecte, analyse...')
                    vtype = 'mvvideo'
                    vid = link.split('=')[-1]
                else:
                    continue
            except:
                return False
            #print link
            #print vid
        if vid == '':
            return
        cmd = os.path.join(data_path,'scripts','get_stream.py -u http://www.megaskipper.com/%s.html?text=%s' % (vtype,vid))
        req = Popen(cmd,shell=True,stdout=PIPE, stderr=STDOUT)
        link, err = req.communicate()
        print link
        lineList = link.splitlines()
        print lineList
        try:
            link = lineList[-1]
        except:
            return False
        if self.start_link(link):
            return True
        else:
            return False
    
    def start_link(self, link):
        self.print_info("Lien Ok, Verification du flux, patience...")
        response = None
        try:
            request = urllib2.Request(link)
            request.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30')
            response = urllib2.urlopen(request)
        except:
            return False
        # check content type:
        content = response.info().getheader('Content-Type')
        print 'link content type: %s' % content
        if ('application/octet-stream' in content) or ('video/x-flv' in content):
            self.print_info("Flux valide!")
            sleep(2)
            self.print_info("")
            self.valid_url = True
            self.media_link = link
            return True
        else:
            self.print_info("Flux invalide!, analyse du lien suivant")
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
                if 'href="/film' in line or 'href="film' in line and 'streaming' in line:
                    img=None
                    flag_found = True
                    l = re.search('href="(.*?)"',line).group(1)
                    link = "http://www.dpstream.net/%s" % l
                    title = re.search('(.*)>(.*?)</a>',line).group(2).decode('ISO-8859-1').encode('utf-8')
                    histoire = re.search("montre\('(.*?)'\)",line).group(1)
                    if 'Aucun' in histoire:
                        img=None
                    else:
                        img_page='http://www.dpstream.net/histoire.php?url=%s' % histoire
                        data = get_url_data(img_page)
                        for line in data.readlines():
                            if 'img src=' in line:
                                pix = re.search('src="(.*?)"',line).group(1)
                                img = download_photo(pix)
                    gobject.idle_add(self.gui.add_sound, title, link, img, None, self.name)
            except:
                continue
        if not flag_found:
            self.print_info(_("%s: No results for %s...") % (self.name,user_search))
            time.sleep(5)
        self.thread_stop=True
    
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)

