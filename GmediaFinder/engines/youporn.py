#!/usr/bin/env python

from html5lib import HTMLParser
from html5lib.treebuilders import getTreeBuilder
import mechanize
import re
from urlparse import urljoin
import urllib

URL = "http://youporn.com/"
ENTER_URL = "%s?user_choice=Enter" % URL
BROWSE_URL = "%sbrowse/%s?page=%s" % (URL, "%s", "%d")
TOP_RATED_URL = "%stop_rated/%s?page=%s" % (URL, "%s", "%d")
MOST_VIEWED_URL = "%smost_viewed/%s?page=%s" % (URL, "%s", "%d")
SEARCH_URL = "%ssearch/%s?query=%s&type=%s&page=%s" % (URL, "%s", "%s", "%s", "%d")

class YouPorn(object):
    def __init__(self):
        self.parser = HTMLParser(tree=getTreeBuilder('beautifulsoup'))
        self.browser = mechanize.Browser()
        self.browser.addheaders = []
        self.browser.open(ENTER_URL)


    def filter(self, url): 
        soup = self.parser.parse(self.browser.open(url))
        vid_list = []
        for l in soup.findAll('a', href=True):
			try:
			    u = re.search('/watch/.*"',str(l)).group(0)
			    vid_list.append(u)
			except:
				continue
				
        imglist = soup.findAll('img',attrs={'class': 'video-thumb'})
        img_list = []
        for t in imglist:
            img = t.attrMap['src']
            img_list.append(img)
        return self.uniq(vid_list), img_list


    def uniq(self,input):
        output = []
        for x in input:
            if x not in output:
                output.append(x)
        return output

    def get_newest_videos(self, page=1, sort_by="rating"):
        return self.filter(BROWSE_URL % (sort_by, page))

    def get_top_rated(self, page=1, sort_by="week"):
        return self.filter(TOP_RATED_URL % (sort_by, page))

    def get_most_viewed(self, page=1, sort_by="week"):
        return self.filter(MOST_VIEWED_URL % (sort_by, page))

    def search(self, query, page=1, sort_by="relevance", type="straight"):
        return self.filter(SEARCH_URL % (sort_by, urllib.quote(query), type, page))
          
    def get_video_url(self, url):
        try:
			download = lambda href: '/download/' in href
        except:
            return
        try:
			soup = self.parser.parse(self.browser.open(url))
        except:
			return
        download_url = soup.find('a', {'href': download})['href']
        return download_url
            

