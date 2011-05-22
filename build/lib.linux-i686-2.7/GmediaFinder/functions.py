#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import gtk
import time
import re

def _get_codec(num):
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

def _reporthook(numblocks, blocksize, filesize, start_time, url, name, progressbar):
        #print "reporthook(%s, %s, %s)" % (numblocks, blocksize, filesize)
        #XXX Should handle possible filesize=-1.
    if filesize == -1:
        gtk.gdk.threads_enter()
        progressbar.set_text(_("Downloading %-66s") % name)
        progressbar.set_pulse_step(0.2)
        progressbar.pulse()
        gtk.gdk.threads_leave()
        time.sleep(0.1)
    else:
        if numblocks != 0:
            try:
                percent = min((numblocks*blocksize*100)/filesize, 100)
                currently_downloaded = float(numblocks) * blocksize / (1024 * 1024) 
                kbps_speed = numblocks * blocksize / (time.time() - start_time)
                kbps_speed = kbps_speed / 1024
                total = float(filesize) / (1024 * 1024)
                mbs = '%.02f MB of %.02f MB' % (currently_downloaded, total)
                e = ' at %d Kb/s ' % kbps_speed
                e += calc_eta(start_time, time.time(), total, currently_downloaded)
            except:
                percent = 100
                return
            if percent < 100:
                gtk.gdk.threads_enter()
                progressbar.set_text("%s %3d%% %s" % (mbs,percent,e))
                progressbar.set_fraction(percent/100.0)
                gtk.gdk.threads_leave()
                time.sleep(0.1)
            else:
                progressbar.set_text(_("Download complete"))
                return

def _with_lock(func, args):
		gtk.threads_enter()
		try:
			return func(*args)
		finally:
			gtk.threads_leave()

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
		return ' Restant : %02d:%02d' % (eta_mins, eta_secs)
		
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

try:
  from xml.etree import cElementTree as ElementTree
except ImportError:
  try:
    import cElementTree as ElementTree
  except ImportError:
    from elementtree import ElementTree


class YouTubeClient:

    users_feed = "http://gdata.youtube.com/feeds/users"
    std_feeds = "http://gdata.youtube.com/feeds/standardfeeds"
    video_name_re = re.compile(r', "t": "([^"]+)"')
    
    def _request(self, feed, *params):
        service = gdata.service.GDataService(server="gdata.youtube.com")
        return service.Get(feed % params)
    
    def search(self, query, page_index, params):
        url = "http://gdata.youtube.com/feeds/api/videos?q=%s&start-index=%s&max-results=25%s" % (query, page_index, params)
        return self._request(url).entry

    def get_thumbnails(self, video):
        doc = video._ToElementTree()
        urls = {}
        for c in doc.findall(".//{http://search.yahoo.com/mrss/}group"):
            for cc in c.findall("{http://search.yahoo.com/mrss/}thumbnail"):
                width = int(cc.get("width"))
                height = int(cc.get("height"))
                size = (width, height)
                url = cc.get("url")
                if size not in urls:
                    urls[size] = [url,]
                else:
                    urls[size].append(url)
        return urls

    def get_largest_thumbnail(self, video):
        thumbnails = self.get_thumbnails(video)
        sizes = thumbnails.keys()
        sizes.sort()
        return thumbnails[sizes[-1]][0]




class ComboBox(object):
    def __init__(self,combobox):
        self.combobox = combobox
        self.model = self.combobox.get_model()

    def append(self,what):
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
