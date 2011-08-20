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

import sys
from time import sleep
from threading import Thread
from urllib import urlretrieve

import HTMLParser
import htmlentitydefs
import htmllib
from subprocess import Popen,PIPE

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
    filename = os.path.basename(img_url)
    if sys.platform == "win32":
        file_path = os.path.join(tempfile.gettempdir(), filename)
    else:
        file_path = "/tmp/%s" % filename
    if os.path.exists(file_path) and not os.path.isdir(file_path):
        os.remove(file_path)
    p = urllib.urlretrieve(img_url, file_path)
    try:
        vid_pic = gtk.gdk.pixbuf_new_from_file_at_scale(p[0],100,100,1)
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
		return _('Remaining : %(min)02d:%(sec)02d') % values

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

def create_comboBox(gui=None,dic=None):
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
            label = gtk.Label(key)
            target.pack_start(label,False,False,5)
            cb = ComboBox(combobox)
            dr = sorted(values.keys())
            for val in dr:
                cb.append(val)
            target.add(combobox)
            cb.select(0)
            target.show_all()
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
    

def cancel():
    print "samereeeeeeeeeeeeee"    
    
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
    
    def __init__(self, gui, url, name, codec, data=None):
        threading.Thread.__init__(self)
        self.gui = gui
        self._stopevent = threading.Event()
        self.url = url
        self.data = data # urllib request reply
        ## filenames
        if not '.' in codec:
            codec = '.'+codec
        self.decoded_name = name+"%s" % codec
        self.encoded_name = urllib.quote(self.decoded_name.encode('utf-8'))
        self.target = os.path.join(self.gui.down_dir,self.decoded_name)
        self.temp_name = self.decoded_name
        self.temp_file = os.path.join(self.gui.down_dir,self.temp_name)
        self.conf_temp_name = '.'+self.decoded_name+'.conf'
        self.conf_temp_file = os.path.join(self.gui.down_dir,self.conf_temp_name)
        # progress bar and buttons
        box = gtk.HBox(False, 5)
        vbox = gtk.VBox(False, 5)
        label = gtk.Label(self.decoded_name)
        label.set_alignment(0, 0.5)
        label.set_line_wrap(True)
        vbox.pack_start(label, False, False, 5)
        self.pbar = gtk.ProgressBar()
        self.pbar.set_size_request(400, 25)
        try:
            box.pack_start(gtk.image_new_from_pixbuf(self.media_thumb), False,False, 5)
        except:
            pb = gtk.gdk.pixbuf_new_from_file_at_scale(os.path.join(self.gui.img_path,'sound.png'), 64,64, 1)
            box.pack_start(gtk.image_new_from_pixbuf(pb), False,False, 5)
        btnbox = gtk.HBox(False, 5)
        ## pause download button
        self.btnpause = gtk.Button()
        image = gtk.Image()
        image.set_from_pixbuf(self.gui.pause_icon)
        self.btnpause.add(image)
        btnbox.pack_start(self.btnpause, False, False, 5)
        self.btnpause.set_tooltip_text(_("Pause/Resume download"))
        ## stop btn
        self.btnstop = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.btnstop.add(image)
        btnbox.pack_start(self.btnstop, False, False, 5)
        self.btnstop.set_tooltip_text(_("Stop Downloading"))
        self.gui.down_container.pack_start(box, False ,False, 5)
        ## show folder button
        self.btnf = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.btnf.add(image)
        btnbox.pack_start(self.btnf, False, False, 5)
        self.btnf.set_tooltip_text(_("Show in folder"))
        ## clear button
        self.btn = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.btn.add(image)
        btnbox.pack_start(self.btn, False, False, 5)
        self.btn.set_tooltip_text(_("Remove"))
        ## convert button
        self.btn_conv = gtk.Button()
        if self.gui.search_engine.engine_type == "video":
            image = gtk.Image()
            image.set_from_stock(gtk.STOCK_CONVERT, gtk.ICON_SIZE_SMALL_TOOLBAR)
            self.btn_conv.add(image)
            btnbox.pack_start(self.btn_conv, False, False, 5)
            self.btn_conv.set_tooltip_text(_("Convert to mp3"))
            ## spinner
            self.throbber = gtk.Image()
            self.throbber.set_from_file(self.gui.img_path+'/throbber.png')
            btnbox.pack_start(self.throbber, False, False, 5)
        
        vbox.pack_start(btnbox, False, False, 0)
        vbox.pack_end(self.pbar, False, False, 5)
        box.pack_start(vbox, False, False, 5)

        gobject.idle_add(box.show_all)
        gobject.idle_add(self.btnf.hide)
        self.convert_check = False
        if self.gui.search_engine.engine_type == "video":
            gobject.idle_add(self.btn_conv.hide)
            gobject.idle_add(self.throbber.hide)
            self.convert_check = True
            self.btn_conv.connect('clicked', self.gui.extract_audio,self.target,self.btn_conv,self.throbber)
        gobject.idle_add(self.btn.hide)
        self.btnf.connect('clicked', self.gui.show_folder, self.gui.down_dir)
        self.btn.connect('clicked', self.remove_download)
        self.btnstop.connect('clicked', self.cancel)
        self.btnpause.connect('clicked', self.pause)
        gobject.idle_add(self.pbar.set_text,_("Waiting..."))
        
        self.createdir = False
        self.paused = False
        self.stopped = False
        self.canceled = False
        self.localheaders = { 'User-Agent' : 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/2008092313 Ubuntu/8.04 (hardy) Firefox/3.1.6' }
        
        ## add thread to gui download pool
        self.gui.download_pool.append(self)
    
    def download(self, url, destination):
        gobject.idle_add(self.pbar.set_text,_("Starting download..."))
        resume = False
        self.paused = False
        response = None
        if not self.data:
            try:
                req = urllib2.Request(url, headers = self.localheaders)
                gobject.idle_add(self.pbar.set_text,_("Sending download request..."))
                response = urllib2.urlopen(req, timeout=self.TIMEOUT)
            except :
                return self.cancel()
        else:
            response = self.data
        headers = response.info()
        if not headers.has_key('Content-Length'):
            print "content_length not available in headers..."
            return self.cancel()
        self.increase_down_count()
        if os.path.isfile(self.target) and float(headers['Content-Length']) == float(os.stat(self.target)[6]):
            os.unlink(self.target)
            self.check_target_file(self.temp_file)
        elif os.path.isfile(self.temp_file):
            gobject.idle_add(self.pbar.set_text,_("File is here but seems to be incomplete!"))
            size_local = float(os.stat(self.temp_file)[6])
            size_on_server = float(headers['Content-Length'])
            if headers['Accept-Ranges'] == 'bytes':
                gobject.idle_add(self.pbar.set_text,_("Range request supported, trying to resume..."))
                try:
                    req = urllib2.Request(url, headers = self.localheaders)
                    req.add_header("range", "bytes=%d-%d"%(size_local,size_on_server))
                    response = urllib2.urlopen(req)
                    resume = True
                except:	
                    resume = False
                    self.temp_file += '.duplicate'
                    return False
            else:
                gobject.idle_add(self.pbar.set_text,_("Range request not supported, redownloading file"))
                os.unlink(self.temp_file)
                return False
        try:
            f = open(self.temp_file, "ab")
        except IOError, errmsg:
            if not os.path.exists(self.temp_file):
                f = open(self.temp_file, "wb")
            else:
                print "%s" %(errmsg)
                response.close()
                return False
    
        try:
            if resume:
                current_bytes = size_local
            else:
                current_bytes = 0
            while True:
                try:
                    if self.canceled:
                        f.close()
                        response.close()
                        break
                    if self._stopevent.isSet():
                        gobject.idle_add(self.pbar.set_text,_("download stopped..."))
                        break
                    read_start = time.time()
                    if not self.paused:
                        bytes = response.read(102400)
                        current_bytes += 102400
                        time_diff = time.time() - read_start
                        if time_diff == 0:
                            time_diff = 1
                        troughput = round((float(102400/time_diff)/1024)/1024*1024,2)
                        procents = int((float(current_bytes)/float(headers['Content-Length']))*100)
                        length = round((float(int(headers['Content-Length'])/1024))/1024,2)
                        current = round((float(current_bytes/1024))/1024,2)
                        if procents < 100 and not self.paused:
                            gobject.idle_add(self.pbar.set_text,_("%3d%% %s of %s Mb at %s KB/s") % (procents, current, length,
                                                                            troughput))
                            gobject.idle_add(self.pbar.set_fraction,procents/100.0)
                        elif procents == 100:
                            gobject.idle_add(self.pbar.set_text,_("Download complete"))
                            gobject.idle_add(self.pbar.set_fraction,100/100.0)
                        f.write(bytes)
                    else:
                        sleep(1)
                except IOError, (errno, strerror):
                    print "I/O error(%s): %s" % (errno, strerror)
                if bytes == "":
                    print "%s Finished" % (self.target)
                    gtk.gdk.threads_enter()
                    os.unlink(self.conf_temp_file)
                    gtk.gdk.threads_leave()
                    break
            sys.stdout.write("\n")
        except KeyboardInterrupt, errmsg:
            print "KeyboardInterrupt Caught: %s" % (errmsg)
            print "Cleaning up"
            f.close()
            response.close()
        f.close()
        response.close()
        return True
    
    def remove_download(self, widget):
        ch = widget.parent
        ru = ch.parent.parent
        gobject.idle_add(ru.parent.remove,ru)    
    
    def run(self):
        while not self._stopevent.isSet():
            ## download...
            gobject.idle_add(self.pbar.set_text,_("Starting download..."))
            try:
                start_time = time.time()
                self.check_target_file(self.temp_file)
                self.download(self.url, self.temp_file)
                if self.canceled:
                    gobject.idle_add(self.pbar.set_text,_("Download canceled..."))
                    time.sleep(2)
                    os.remove(self.temp_file)
                    os.remove(self.conf_temp_file)
                else:
                    if self.stopped:
                        gobject.idle_add(self.pbar.set_text,_("Download error..."))
                    else:
                        gobject.idle_add(self.pbar.set_text,_("Download complete"))
                        if self.convert_check:
                            gobject.idle_add(self.btn_conv.show)
                gobject.idle_add(self.btnf.show)
                gobject.idle_add(self.btn.show)
                gobject.idle_add(self.btnstop.hide)
                gobject.idle_add(self.btnpause.hide)
                gobject.idle_add(self.pbar.set_fraction,100/100.0)
                self.stop()
            except KeyboardInterrupt, errmsg:
                gobject.idle_add(self.pbar.set_text,_("Failed..."))
                gobject.idle_add(self.btn.show)
                self.decrease_down_count()
                gobject.idle_add(self.btnstop.hide)
                gobject.idle_add(self.btnpause.hide)
                self.stop()
            
    def check_target_file(self,tmp_file):
        if not os.path.exists(self.conf_temp_file):
            f = open(self.conf_temp_file,'w')
            f.write(self.url)
            f.close()
        else:
            f = open(self.conf_temp_file,'r')
            self.url = f.read()
            f.close()
            
    def cancel(self,widget=None):
        self.canceled = True
        gobject.idle_add(self.pbar.set_text,_("Cancel downloading..."))
        self.stop()
        
    def stop(self,widget=None):
        gobject.idle_add(self.decrease_down_count)
        self._stopevent.set()
        self.stopped = True
    
    def pause(self,widget):
        if not self.paused:
            self.paused = True
            gobject.idle_add(self.pbar.set_text,_("download paused..."))
            self.decrease_down_count()
            image = gtk.Image()
            image.set_from_pixbuf(self.gui.play_icon)
            self.btnpause.set_image(image)
        else:
            self.paused = False
            self.increase_down_count()
            gobject.idle_add(self.pbar.set_text,_("Resuming download..."))
            image = gtk.Image()
            image.set_from_pixbuf(self.gui.pause_icon)
            self.btnpause.set_image(image)
    
    def decrease_down_count(self):
        if self.gui.active_downloads > 0:
            self.gui.active_downloads -= 1
            gobject.idle_add(self.gui.active_down_label.set_text,str(self.gui.active_downloads))
            
    def increase_down_count(self):
        self.gui.active_downloads += 1
        gobject.idle_add(self.gui.active_down_label.set_text,str(self.gui.active_downloads))
    
