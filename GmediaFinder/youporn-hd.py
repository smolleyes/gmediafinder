#!/usr/bin/env python

import html5lib
import mechanize
import re

URL = "http://youporn.com/"
ENTER_URL = "%s?user_choice=Enter" % URL
BROWSE_URL = "%sbrowse/%s?page=%s" % (URL, "%s", "%d")
TOP_RATED_URL = "%stop_rated/%s?page=%s" % (URL, "%s", "%d")
MOST_VIEWED_URL = "%smost_viewed/%s?page=%s" % (URL, "%s", "%d")
SEARCH_URL = "%ssearch/%s?query=%s&type=%s&page=%s" % (URL, "%s", "%s", "%s", "%d")

def _join_url(a, *p):
    path = a
    for b in p:
        if b.startswith('/'):
            path = b
        elif path == '' or path.endswith('/'):
            path +=  b
        else:
            path += '/' + b
    return path


class YouPorn(object):
    def __init__(self):
        self._browser = mechanize.Browser()
        self._browser.addheaders = []
        self._enter()

    def _enter(self):
        self._browser.open(ENTER_URL)

    @staticmethod
    def _filter_videos(soup):
        watch = lambda href: href and "/watch/" in href
        videos = []
        for a in soup.findAll("a", {"href":watch}):
            videos.append(_join_url(URL, a["href"]))
        return videos

    def get_newest_videos(self, page=1, sort_by="rating"):
        return self._filter_videos(html5lib.parse(self._browser.open(
            BROWSE_URL % (sort_by, page)), "beautifulsoup"))

    def get_top_rated(self, page=1, sort_by="week"):
        return self._filter_videos(html5lib.parse(self._browser.open(
            TOP_RATED_URL % (sort_by, page)), "beautifulsoup"))

    def get_most_viewed(self, page=1, sort_by="week"):
        return self._filter_videos(html5lib.parse(self._browser.open(
            MOST_VIEWED_URL % (sort_by, page)),"beautifulsoup"))

    def search(self, query, page=1, sort_by="relevance", type="straight"):
        print SEARCH_URL % (sort_by, query, type, page)
        return self._filter_videos(html5lib.parse(self._browser.open(
            SEARCH_URL % (sort_by, query, type, page)), "beautifulsoup"))
    
    def get_thumb_url(self,video):
		vid = re.search('(/watch/)(\S.*?)(\/)',video).group(2)
		id1 = vid[0:2]
		id2 = vid[2:4]
		thumb_url = "http://ss-2.youporn.com/screenshot/%s/%s/screenshot_multiple/%s/%s_multiple_1_extra_large.jpg" % (id1,id2,vid,vid)

    def download_video(self, url):
        soup = html5lib.parse(self._browser.open(url), "beautifulsoup")
        download = lambda href: "/download/" in href
        download_url = soup.find("a", {"href":download})["href"]
        self.get_thumb_url(url)
        self._browser.retrieve(download_url,
            self._browser.geturl().split("/")[-2] + ".mp4")


def main():
    youporn = YouPorn()
    for video in youporn.search("lela-star"):
        youporn.download_video(video)

if __name__ == "__main__":
    main()
