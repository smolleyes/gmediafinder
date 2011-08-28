# -*- coding:Utf­8 ­-*-
import urllib
import urllib2
import urlparse
import os
import sys
import re

import checklinks as checkLink

class Debrid(object):
    def __init__(self):
        ## take an array of links as locked links (not verified yet)
        self.linkChecker = checkLink.CheckLinkIntegrity()
        

    def analyse_links(self, links):
        checked_links = self.linkChecker.check(links)
        return checked_links
