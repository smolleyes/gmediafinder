#-*- coding: UTF-8 -*-
import os
import gtk
import time
import re
import urllib2
import urllib
import threading
import time
import gobject
import tempfile
import pango

import sys
from time import sleep
from threading import Thread
from urllib import urlretrieve

import HTMLParser
import htmlentitydefs
import htmllib
from subprocess import Popen,PIPE

try:
    from functions import *
    from config import data_path
    from config import _
except:
    from GmediaFinder.functions import *
    from GmediaFinder.config import data_path
    from GmediaFinder.config import _

HTMLParser.attrfind = re.compile(r'\s*([a-zA-Z_][-.:a-zA-Z_0-9]*)(\s*=\s*'r'(\'[^\']*\'|"[^"]*"|[^\s>^\[\]{}\|\'\"]*))?')

def get_url_data(url):
        user_agent = 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.608.0 Chrome/10.0.608.0 Safari/534.15'
        headers =  { 'User-Agent' : user_agent , 'Accept-Language' : 'fr-FR,fr;q=0.8,en-US;q=0.6,en;q=0.4' }
        ## start the request
        try:
            req = urllib2.Request(url,None,headers)
        except:
            return
        try:
            data = urllib2.urlopen(req)
        except:
            return

        return data
        
def download_photo(img_url):
    try:
        filename = os.path.basename(img_url)
        if sys.platform == "win32":
            file_path = os.path.join(tempfile.gettempdir(), filename)
        else:
            file_path = "/tmp/%s" % filename
        if os.path.exists(file_path) and not os.path.isdir(file_path):
            os.remove(file_path)
        p = urllib.urlretrieve(img_url, file_path)
        vid_pic = gtk.gdk.pixbuf_new_from_file(p[0])
        return vid_pic
    except:
        return None


def with_lock(func, args):
		gtk.gdk.threads_enter()
		try:
			return func(*args)
		finally:
			gtk.gdk.threads_leave()

def calc_eta(start, now, total, current):
		if total is None:
			return '--:--'
		dif = now - start
		if current == 0 or dif < 0.001: # One millisecond
			return '--:--'
		rate = float(current) / dif
		eta = long((float(total) - float(current)) / rate)
		(eta_mins, eta_secs) = divmod(eta, 60)
		if eta_mins > 99:
			return '--:--'
		values = {'min': eta_mins, 'sec': eta_secs}
		return _('%(min)02d:%(sec)02d') % values

import htmlentitydefs

def translate_html(text_html):
    code = htmlentitydefs.codepoint2name
    new_text = ""
    dict_code = dict([(unichr(key),value) for key,value in code.items()])
    for key in text_html:
#        key = unicode(key)
        if dict_code.has_key(key):
            new_text += "&%s;" % dict_code[key]
        else:
            new_text += key
    return new_text



def htmlentitydecode(s):
    # First convert alpha entities (such as &eacute;)
    # (Inspired from [url]http://mail.python.org/pipermail/python-list/2007-June/443813.html[/url])
    def entity2char(m):
        entity = m.group(1)
        if entity in htmlentitydefs.name2codepoint:
            return unichr(htmlentitydefs.name2codepoint[entity])
        return u" "  # Unknown entity: We replace with a space.
    expression = u'&(%s);' % u'|'.join(htmlentitydefs.name2codepoint)
    t = re.sub(expression, entity2char, s)


    # Then convert numerical entities (such as &#38;#233;)
    t = re.sub(u'&#38;#(d+);', lambda x: unichr(int(x.group(1))), t)

    # Then convert hexa entities (such as &#38;#x00E9;)
    return re.sub(u'&#38;#x(w+);', lambda x: unichr(int(x.group(1),16)), t)
		
def yesno(title,msg):
    dialog = gtk.MessageDialog(parent = None,
    buttons = gtk.BUTTONS_YES_NO,
    flags =gtk.DIALOG_DESTROY_WITH_PARENT,
    type = gtk.MESSAGE_QUESTION,
    message_format = msg
    )
    dialog.set_position("center")
    dialog.set_title(title)
    result = dialog.run()
    dialog.destroy()

    if result == gtk.RESPONSE_YES:
        return "Yes"
    elif result == gtk.RESPONSE_NO:
        return "No"
        
def error_dialog(message, parent = None):
    """
    Displays an error message.
    """

    dialog = gtk.MessageDialog(parent = parent, type = gtk.MESSAGE_ERROR, buttons = gtk.BUTTONS_OK, flags = gtk.DIALOG_MODAL)
    dialog.set_markup(message)
    dialog.set_position('center')

    result = dialog.run()
    dialog.destroy()

def sortDict(d):
    """ Returns the keys of dictionary d sorted by their values """
    items=d.items()
    backitems=[ [v[1],v[0]] for v in items]
    backitems.sort()
    return [ backitems[i][1] for i in range(0,len(backitems))]

def create_comboBox(gui=None,dic=None,combo=None,createLabel=True):
    model = gtk.ListStore(str,gtk.gdk.Color)
    combobox = gtk.ComboBox(model)
    cell = gtk.CellRendererText()
    combobox.pack_start(cell, True)
    combobox.add_attribute(cell, 'text', 0)
    combobox.add_attribute(cell, 'foreground-gdk', 1)
    cb=None
    
    if dic:
        target = gui.search_opt_box
        for key,values in dic.items():
            if createLabel:
                label = gtk.Label(key)
                target.pack_start(label,False,False,5)
            cb = ComboBox(combobox)
            dr = sorted(values.keys())
            for val in dr:
                cb.append(val)
            target.add(combobox)
            cb.select(0)
            target.show_all()
        if combo:
            return cb, combobox
        else:
            return cb
    return combobox


class ComboBox(object):
    def __init__(self,combobox):
        self.combobox = combobox
        self.model = self.combobox.get_model()

    def append(self,what,warn=False):
        if warn:
            color = gtk.gdk.color_parse("red")
            self.model.append([what, color])
        else:
            self.combobox.append_text(what)

    def remove(self,what):
        self.combobox.remove_text(what)

    def select(self,which):
        self.combobox.set_active(which)

    def getSelectedIndex(self):
        return self.combobox.get_active()

    def getSelected(self):
        return self.model[self.getSelectedIndex()][0]

    def setIndexFromString(self,usr_search):
        found = 0
        for item in self.model:
            iter = item.iter
            path = item.path
            name = self.model.get_value(iter, 0)
            if name == usr_search:
                found = 1
                self.select(path[0])
                break
            self.combobox.set_active(-1)
            
    def get_list(self):
        l = {}
        for item in self.model:
            iter = item.iter
            path = item.path
            name = self.model.get_value(iter, 0)
            if not name == "":
                l[name] = ''
        return l
        

def decode_htmlentities(text):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(text)
    try:
        text = p.save_end().decode('utf-8')
    except:
        return
    text = re.sub('&#_;','\'',text)
    text = re.sub('&# ;','\'',text)
    text = re.sub('&amp;','&',text)
    text = re.sub('_',' ',text)
    return text


# self._hook est appelé à chaque requete urllib
class Abort(Exception):
    pass

class urlFetch(Thread):
    def __init__(self, engine, url, query, page, local=tempfile.NamedTemporaryFile().name):
        Thread.__init__(self)
        self.url = url
        self.stop = False
        self.local = local
        self.engine = engine
        self.query = query
        self.page = page

    def _hook(self, *args):
        if self.stop:
            raise Abort
        #sys.stdout.write('search request stopped: %s,%s' % (self.engine,self.query))
        sys.stdout.flush()

    def run(self):
        if not isinstance(self.url, str):
            try:
                self.engine.filter(self.url,self.query)
            except:
                self.stop = True
                self.abort()
        else:
            try:
                t = urlretrieve(self.url, self.local, self._hook)
                f = open(self.local)
                self.engine.filter(f,self.query)
            except Abort, KeyBoardInterrupt:
                e = sys.exc_info()[1]
                if e != "":
                    print "<p>Error: %s</p>" % e
                print 'Aborted'
            except:
                try:
                    t = urllib2.urlopen(self.url)
                    self.engine.filter(t, self.query)
                except:
                    self.stop = True
                    raise


    def abort(self):
        self.stop = True


def get_redirect_link(link):
    request = urllib2.Request(link)
    opener = urllib2.build_opener()
    f = opener.open(request)
    return f.url

def warn_dialog(dialog):
    result = dialog.run()
    dialog.hide()
    return result
    
   
    
""" Inbox Files Downloader by maris@chown.lv. You are free do whatever You want with this code! """

import urllib2, urllib, cookielib, re, time, optparse, socket, os, sys

""" Poster lib for HTTP streaming upload, taken from http://atlee.ca/software/poster"""

import httplib, urllib2, socket

class FileDownloader(threading.Thread):
    """ Files downloader class """
    createdir = False
    urlopen = urllib2.urlopen
    cj = cookielib.LWPCookieJar()
    Request = urllib2.Request
    
    post_data = None
    download_items = []
    TIMEOUT = 15
    
    localheaders = { 'User-Agent' : 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.1.6' }
    
    def __init__(self, gui, url, name, codec, data=None, engine_name=None, engine_type=None):
        threading.Thread.__init__(self)
        self.gui = gui
        self._stopevent = threading.Event()
        self.url = url
        self.data = data # urllib request reply
        ## filenames
        if codec is None:
            codec = '.mpeg'
        self.codec = codec
        if not '.' in codec:
            self.codec = '.'+self.codec
        bad_char = ['\\','@',',','\'','\"','/']
        for char in bad_char:
            if char in name:
                name = name.replace(char,' ')
        self.basename = name
        self.decoded_name = name+"%s" % self.codec
        self.encoded_name = urllib.quote(self.decoded_name.encode('utf-8'))
        self.target = os.path.join(self.gui.down_dir,self.decoded_name)
        self.temp_name = self.decoded_name
        self.temp_file = os.path.join(self.gui.down_dir,self.temp_name)
        self.conf_temp_name = '.'+self.decoded_name+'.conf'
        self.conf_temp_file = os.path.join(self.gui.down_dir,self.conf_temp_name)
        self.engine = self.gui.search_engine
        if not engine_type:
            self.engine_type = self.engine.engine_type
        else:
            self.engine_type = engine_type
        if not engine_name: 
            self.engine_name = self.engine.name
        else:
            self.engine_name = engine_name
        
        self.createdir = False
        self.paused = False
        self.stopped = False
        self.canceled = False
        self.failed = False
        self.completed = False
        self.download_response = None
        self.target_opener = None
        self.start_time = None
        size_local = None
        self.localheaders = { 'User-Agent' : 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.1.6' }
        
        ## add thread to gui download pool
        self.gui.download_pool.append(self)
    
    def create_download_box(self):
        self.treeiter = self.gui.download_treestore.append(None, [self.decoded_name,0,_("Initializing download..."),'','','gtk-media-pause','gtk-cancel','gtk-clear','gtk-find','gtk-convert',self])
        # hide some icons
        self.gui.download_treestore.set_value(self.treeiter, 9, '')
        self.gui.download_treestore.set_value(self.treeiter, 7, '')
        
    def download(self, url, destination):
        self.increase_down_count()
        self.url = url
        self.target = destination
        self.gui.download_treestore.set_value(self.treeiter, 2,_("Starting download..."))
        resume = False
        if not self.data:
            try:
                req = urllib2.Request(url, headers = self.localheaders)
                self.gui.download_treestore.set_value(self.treeiter, 2,_("Sending download request..."))
                self.download_response = urllib2.urlopen(req, timeout=self.TIMEOUT)
            except :
                self.failed = True
                return False
        else:
            self.download_response = self.data
        headers = self.download_response.info()
        print "_____ Response Headers:\n %s" % headers
        if not headers.has_key('Content-Length'):
            print "content_length not available in headers..."
            self.failed = True
            return False
        elif int(headers['Content-Length']) == 0:
            print "content_length available but null..."
            self.failed = True
            return False
        ## response ok, start downloading checks
        if os.path.isfile(self.target) and float(headers['Content-Length']) == float(os.stat(self.target)[6]):
            self.gui.download_treestore.set_value(self.treeiter, 2,_("File already downloaded on disk..."))
            print "File already downloaded on disk...exit"
            self.completed = True
            return False
        elif os.path.isfile(self.temp_file):
            print "File is here but seems to be incomplete!"
            self.gui.download_treestore.set_value(self.treeiter, 2,_("File is here but seems to be incomplete!"))
            size_local = float(os.stat(self.temp_file)[6])
            size_on_server = float(headers['Content-Length'])
            print size_local, size_on_server
            if headers.has_key('Accept-Ranges') and headers['Accept-Ranges'] == 'bytes':
                print "Range request supported, trying to resume..."
                self.gui.download_treestore.set_value(self.treeiter, 2,_("Range request supported, trying to resume..."))
                try:
                    req = urllib2.Request(url, headers = self.localheaders)
                    req.add_header("range", "bytes=%d-%d"%(size_local,size_on_server))
                    self.download_response = urllib2.urlopen(req)
                    resume = True
                except:	
                    resume = False
                    self.temp_file += '.duplicate'
                    return False
            else:
                print "Range request not supported, redownloading file"
                self.gui.download_treestore.set_value(self.treeiter, 2, _("Range request not supported, redownloading file..."))
                os.unlink(self.temp_file)
                return False
        try:
            self.target_opener = open(self.temp_file, "ab")
        except IOError, errmsg:
            print errmsg
            if not os.path.exists(self.temp_file):
                self.target_opener = open(self.temp_file, "wb")
            else:
                print "%s" %(errmsg)
                self.failed = True
                return True ## return true but failed
        self.start_time = time.time()
        try:
            if resume:
                current_bytes = size_local
            else:
                current_bytes = 0
            while True:
                try:
                    if self.canceled:
                        break
                    if self._stopevent.isSet():
                        self.gui.download_treestore.set_value(self.treeiter, 2, _("download stopped..."))
                        break
                    read_start = time.time()
                    if not self.paused:
                        try:
                            bytes = self.download_response.read(102400)
                        except:
                            self.failed = True
                            print "no more data...incomplete stream"
                            break
                        current_bytes += 102400
                        time_diff = time.time() - read_start
                        if time_diff == 0:
                            time_diff = 1
                        troughput = round((float(102400/time_diff)/1024)/1024*1024,2)
                        procents = float((float(current_bytes)/float(headers['Content-Length']))*100)
                        length = round((float(int(headers['Content-Length'])/1024))/1024,2)
                        current = round(float(current_bytes / (1024 * 1024)),2)
                        #current = float(int(current_bytes) / (1024 * 1024),2)
                        total = float(int(headers['Content-Length']) / (1024 * 1024))
                        mbs = '%.02f of %.02f MB' % (current, length)
                        e = '%d Kb/s ' % troughput
                        eta = calc_eta(self.start_time, time.time(), total, current)
                        if '-' in eta:
                            eta = "00:00"
                        if procents < 100 and not self.paused:
                            self.gui.download_treestore.set_value(self.treeiter, 1, procents)
                            self.gui.download_treestore.set_value(self.treeiter, 2, mbs)
                            self.gui.download_treestore.set_value(self.treeiter, 3, e)
                            self.gui.download_treestore.set_value(self.treeiter, 4, eta)
                        elif procents == 100:
                            self.gui.download_treestore.set_value(self.treeiter, 1, 100)
                            self.gui.download_treestore.set_value(self.treeiter, 3, '')
                            self.gui.download_treestore.set_value(self.treeiter, 4, '')
                        try:
                            self.target_opener.write(bytes)
                        except:
                            self.failed = True
                            break
                    else:
                        sleep(1)
                except IOError, (errno, strerror):
                    print "I/O error(%s): %s" % (errno, strerror)
                    self.failed = True
                    break
                except:
                    self.failed = True
                    break
                if bytes == "":
                    print "%s Finished" % (self.target)
                    ## clean conf file
                    self.completed = True
                    break
            sys.stdout.write("\n")
        except KeyboardInterrupt, errmsg:
            print "KeyboardInterrupt Caught: %s" % (errmsg)
            print "Cleaning up"
            self.canceled = True
        return True
    
    def remove_download(self, widget=None):
        self.gui.download_treestore.remove(self.treeiter)
    
    def run(self):
        self.create_download_box()
        while not self._stopevent.isSet():
            ## download...
            self.gui.download_treestore.set_value(self.treeiter, 2, _("Starting download..."))
            try:
                self.start_time = time.time()
                self.check_target_file(self.temp_file)
                self.download(self.url, self.temp_file)
                if self.failed:
                    self.gui.download_treestore.set_value(self.treeiter, 2, _("Download error..."))
                    self.download_finished()
                elif self.canceled:
                    self.gui.download_treestore.set_value(self.treeiter, 2, _("Download canceled..."))
                    self.gui.download_treestore.set_value(self.treeiter, 8, '')
                    self.download_finished()
                ## already downloaded
                elif self.completed:
                    self.gui.download_treestore.set_value(self.treeiter, 2, _("Download complete..."))
                    self.gui.download_treestore.set_value(self.treeiter, 1, 100)
                    if self.engine_type == 'video':
                        self.gui.download_treestore.set_value(self.treeiter, 9, 'gtk-convert')
                    self.download_finished()
                else:
                    continue
            except:
                print "failed"
                self.failed = True
                self.gui.download_treestore.set_value(self.treeiter, 2, _("Download error..."))
                self.download_finished()
            
    def check_target_file(self,tmp_file):
        if not os.path.exists(self.conf_temp_file):
            f = open(self.conf_temp_file,'w')
            f.write(self.url+':::'+self.basename+':::'+self.codec+':::'+self.engine_type+':::'+self.engine_name)
            f.close()
        else:
            f = open(self.conf_temp_file,'r')
            data = f.read()
            f.close()
            link = data.split(':::')[0]
            name = data.split(':::')[1]
            codec = data.split(':::')[2]
            engine_type = data.split(':::')[3]
            engine_name = data.split(':::')[4]
            self.decoded_name = name+"%s" % codec
            self.encoded_name = urllib.quote(self.decoded_name.encode('utf-8'))
            self.target = os.path.join(self.gui.down_dir,self.decoded_name)
            self.temp_name = self.decoded_name
            self.temp_file = os.path.join(self.gui.down_dir,self.temp_name)
            self.conf_temp_name = '.'+self.decoded_name+'.conf'
            self.conf_temp_file = os.path.join(self.gui.down_dir,self.conf_temp_name)
            self.engine_type = engine_type
            self.engine_name = engine_name
            
    def download_finished(self):
        self.gui.download_treestore.set_value(self.treeiter, 5, '')
        self.gui.download_treestore.set_value(self.treeiter, 6, '')
        self.gui.download_treestore.set_value(self.treeiter, 7, 'gtk-clear')
        try:
            self.stop()
            self.engine.download_finished(self.url, self.target)
        except:
            self.stop()
        self.print_info('')
        self.gui.download_treestore.set_value(self.treeiter, 3, '')
        self.gui.download_treestore.set_value(self.treeiter, 4, '')
        gobject.idle_add(self.decrease_down_count)
    
    def cancel(self,widget=None):
        self.canceled = True
        self.gui.download_treestore.set_value(self.treeiter, 2, _("Cancelling download..."))
        
    def stop(self,widget=None):
        self._stopevent.set()
        self.stopped = True
        try:
            self.target_opener.close()
            self.download_response.close()
        except:
            print "target file do not exist or closed..."
        if self.completed:
            if os.path.exists(self.conf_temp_file):
                os.remove(self.conf_temp_file)
        elif self.canceled or self.failed:
            if os.path.exists(self.conf_temp_file):
                os.remove(self.conf_temp_file)
            if os.path.exists(self.temp_file):
                os.remove(self.temp_file)
    
    def pause(self):
        if not self.paused:
            self.paused = True
            self.gui.download_treestore.set_value(self.treeiter, 2, _("Download paused..."))
            self.decrease_down_count()
            self.gui.download_treestore.set_value(self.treeiter, 5, 'gtk-media-play')
        else:
            self.paused = False
            self.increase_down_count()
            self.gui.download_treestore.set_value(self.treeiter, 2, _("Resuming download..."))
            self.gui.download_treestore.set_value(self.treeiter, 5, 'gtk-media-pause')
    
    def convert(self):
        src = self.target
        target = src.replace(self.codec,'.mp3')
        if os.path.exists(target):
            os.remove(target)
        if sys.platform != "linux2":
            ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(config.exec_path)),'ffmpeg\\ffmpeg.exe').replace("\\","\\\\")
            target = target.replace("\\","\\\\")
            src = src.replace("\\","\\\\")
        else:
            ffmpeg_path = "/usr/bin/ffmpeg"
        self.print_info(_('Extracting audio...'))
        try:
            self.gui.throbber.show()
            (pid,t,r,s) = gobject.spawn_async([str(ffmpeg_path), '-i', str(src), '-f', 'mp3', '-ab', '192k', str(target)],flags=gobject.SPAWN_DO_NOT_REAP_CHILD,standard_output = True, standard_error = True)
            gobject.child_watch_add(pid, self.task_done)
        except:
            self.print_info(_('Extraction failed...'))
            sleep(4)
            self.print_info('')
            self.gui.throbber.hide()

    def task_done(self,pid,ret):
        self.gui.download_treestore.set_value(self.treeiter, 9, '')
        self.print_info('')
        self.gui.throbber.hide()

    
    def decrease_down_count(self):
        if self.gui.active_downloads > 0:
            self.gui.active_downloads -= 1
            gobject.idle_add(self.gui.active_down_label.set_text,str(self.gui.active_downloads))
            
    def increase_down_count(self):
        self.gui.active_downloads += 1
        gobject.idle_add(self.gui.active_down_label.set_text,str(self.gui.active_downloads))
        
    def print_info(self,msg):
        gobject.idle_add(self.gui.info_label.set_text,msg)
    
