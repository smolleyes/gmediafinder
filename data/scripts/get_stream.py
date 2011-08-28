#!/usr/bin/env python
import sys # kudos to Nicholas Herriot (see comments)
import gtk
import webkit
import warnings
import urllib
import re
from time import sleep
from optparse import OptionParser
 
warnings.filterwarnings('ignore')
 
class WebView(webkit.WebView):
	def get_html(self):
		self.execute_script('oldtitle=document.title;document.title=document.documentElement.innerHTML;')
		html = self.get_main_frame().get_title()
		self.execute_script('document.title=oldtitle;')
		return html
 
class Crawler(gtk.Window):
    def __init__(self, url):
        gtk.Window.__init__(self)
        self._url = url
    
    def crawl(self):
        view = WebView()
        view.load_uri(self._url)
        view.connect('document-load-finished', self._finished_loading)
        self.add(view)
        gtk.main()
    
    def _finished_loading(self, view, frame):
        d = urllib.unquote(view.get_html())
        data = re.sub('&quot;','"',d)
        try:
            link = re.search('clip":{"url":"(.*?)"',data).group(1)
        except:
            return
        print link
        gtk.main_quit()
 
def main():
    options = get_cmd_options()
    crawler = Crawler(options.url)
    crawler.crawl()

def get_cmd_options():
	"""
		gets and validates the input from the command line
	"""
	usage = "usage: %prog [options] args"
	parser = OptionParser(usage)
	parser.add_option('-u', '--url', dest = 'url', help = 'URL to fetch data from')
 
	(options,args) = parser.parse_args()
 
	if not options.url:
		print 'You must specify an URL.',sys.argv[0],'--help for more details' 
		exit(1)
 
	return options

if __name__ == '__main__':
	main()
