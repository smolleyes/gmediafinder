#-*- coding: UTF-8 -*-
import os
import gtk
import time
import re
import urllib2
import urllib
import html5lib
from html5lib import sanitizer, treebuilders, treewalkers, serializer, treewalkers
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

def clean_html(buf):
	"""Cleans HTML of dangerous tags and content."""
	buf = buf.strip()
	if not buf:
		return buf

	p = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"),
			tokenizer=sanitizer_factory)
	dom_tree = p.parseFragment(buf)

	walker = treewalkers.getTreeWalker("dom")
	stream = walker(dom_tree)

	s = serializer.htmlserializer.HTMLSerializer(
			omit_optional_tags=False,
			quote_attr_values=False)
	return s.render(stream).decode('UTF-8')

def sanitizer_factory(self,*args, **kwargs):
        san = sanitizer.HTMLSanitizer(*args, **kwargs)
        # This isn't available yet
        # san.strip_tokens = True
        return san
        
def download_photo(img_url):
	image_on_web = urllib.urlretrieve(img_url)
	try:
		pixb = gtk.gdk.pixbuf_new_from_file_at_size(image_on_web[0],100,100)
	except gobject.GError, error:
		return False
	return pixb

def get_codec(num):
    codec=None
    if re.match('5|34|35',num):
        codec = "flv"
    elif re.match('18|22|37|38',num):
        codec= "mp4"
    elif re.match('43|45',num):
        codec= "webm"
    elif re.match('17',num):
        codec= "3gp"
    return codec

class Downloader(threading.Thread):
    def __init__(self,gui,url, name, pbar, btnf, btn,btn_conv,btnstop,convert,label=''):
        threading.Thread.__init__(self)
        self.label = label
        self.gui = gui
        self._stopevent = threading.Event()
        print "thread %s" % name
        self.url = url
        self.name = name
        self.pbar = pbar
        self.btnf = btnf
        self.btn = btn
        self.btn_conv = btn_conv
        self.btnstop = btnstop
        self.convert_check = convert
        self.btnstop.connect('clicked', self.stop)
        
    def run(self,):
        i = 0
        while not self._stopevent.isSet():
            self.gui.active_downloads += 1
            self.gui.active_down_label.set_text(str(self.gui.active_downloads))
            ## download...
            try:
                start_time = time.time()
                urllib.urlretrieve(self.url, self.gui.down_dir+"/"+ self.name,
                lambda nb, bs, fs, url=self.url: self._reporthook(nb,bs,fs,start_time,self.url,self.name,self.pbar))
                self.btnf.show()
                if self.convert_check == 'True':
                    self.btn_conv.show()
                self.btn.show()
                self.btnstop.hide()
                self.decrease_down_count()
                self._stopevent.set()
                os.rename(self.gui.down_dir+"/"+ self.name,self.gui.down_dir+"/"+ self.label)
            except:
                self.pbar.set_text(_("Failed..."))
                self.btn.show()
                self.decrease_down_count()
                self.btnstop.hide()
                self._stopevent.set()
			

	
    def stop(self,widget=None):
		print "thread %s stopped" % self.name
		self._stopevent.set()
		self.decrease_down_count()
		os.remove(self.gui.down_dir+"/"+ self.name)
		self.gui.remove_download(widget)
    
    def decrease_down_count(self):
		if self.gui.active_downloads > 0:
			self.gui.active_downloads -= 1
			self.gui.active_down_label.set_text(str(self.gui.active_downloads))
	
    def _reporthook(self, numblocks, blocksize, filesize, start_time, url, name, progressbar):
		#print "reporthook(%s, %s, %s)" % (numblocks, blocksize, filesize)
		#XXX Should handle possible filesize=-1.
		if self._stopevent.isSet():
			self._reporthook(numblocks, blocksize, filesize, start_time, url, name, progressbar)
			pass
			
		if filesize == -1:
			gtk.gdk.threads_enter()
			progressbar.set_text(_("Downloading %-66s") % name)
			progressbar.set_pulse_step(0.2)
			progressbar.pulse()
			gtk.gdk.threads_leave()
		else:
			if numblocks != 0:
				try:
					percent = min((numblocks*blocksize*100)/filesize, 100)
					currently_downloaded = float(numblocks) * blocksize / (1024 * 1024) 
					kbps_speed = numblocks * blocksize / (time.time() - start_time)
					kbps_speed = kbps_speed / 1024
					total = float(filesize) / (1024 * 1024)
					values = {'downloaded': currently_downloaded, 'total': total}
					mbs = _('%(downloaded).02f MB of %(total).02f MB') % values
					e = _(' at %d Kb/s ') % kbps_speed
					e += calc_eta(start_time, time.time(), total, currently_downloaded)
				except:
					percent = 100
					return
				if percent < 100:
					gtk.gdk.threads_enter()
					progressbar.set_text("%s %3d%% %s" % (mbs,percent,e))
					progressbar.set_fraction(percent/100.0)
					gtk.gdk.threads_leave()
				else:
					progressbar.set_text(_("Download complete"))
					return

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
            for val in values:
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

def decode_htmlentities(text):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(text)
    text = p.save_end()
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
        try:
            t = urlretrieve(self.url, self.local, self._hook)
            f = open(self.local)
            self.engine.filter(f,self.query)
        except Abort, KeyBoardInterrupt:
            e = sys.exc_info()[1]
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
