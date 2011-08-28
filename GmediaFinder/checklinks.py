#! /usr/bin/env python
# -*- coding:Utf­8 ­-*-
import urllib
import urllib2
import urlparse
import json
import os
import sys
import re

humanreadable = lambda s:[(s%1024**i and "%.1f"%(s/1024.0**i) or
								str(s/1024**i))+' '+x.strip()+'b'
								for i,x in enumerate(' kmgtpezy') 
								if s<1024**(i+1) or i==8][0]

class CheckLinkIntegrity(object):
    def __init__(self):
        self.liste_checked = []
        self.rapid_serveurs   = { 'megaupload'   : '4iidlag11',
                                  'rapidshare'   : '4iidlag11',
                                  'megavideo'    : '4iidlag11',
                                  'megaporn'     : '4iidlag11',
                                  'megashares'   : '3dljy11', 
                                  'mediafire'    : '3dljy11',
                                  'depositfiles' : '3dljy11',
                                  'easy-share'   : '3dljy11', 
                                  'fileserve'    : '4iidlag11', 
                                  'filesonic'    : '3dl098', 
                                  'filefactory'  : '4iidlag11', 
                                  'freakshare'   : '3dljy11',
                     	          'hotfile'      : '4iidlag11', 
                                  'turbobit'     : '4iidlag11',
                                  'uploading'    : '4iidlag11', 
                                  #'uploaded'     : '3dljy11', 
                                  'wupload'      : '4iidlag11', 
                                  '4shared'      : '3dljy11',
                     		    }
        self.serveurs = ['megaupload', 'rapidshare', 'filesonic', 'wupload', 'hotfile',
                         'megashares', 'depositfiles', '4shared', 'easy-share']
	# megaupload rapidshare filesonic wupload hotfile megashares depositfiles
	# 4shared 
    def check(self, link):
        for server in self.serveurs:
            if server in link[0]:
                print "Starting validity check for: %s \n" % link
                server = server.replace('-','_').replace('4','f')
                getattr(self, server)(link)
        return self.liste_checked
	        
    def get_http_data(self, url, data=None):
        if data is not None:
            data = urllib.urlencode(data)
        print url
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        return response
        print response.info()
        print response.geturl()
        print response.read()
    
    def easy_share(self, urls):
        self.liste_checked = []
        for link in urls:
            title = 0
            size  = 0
            flag = False
            try:
                resp = self.get_http_data(link)
            except urllib2.HTTPError, e:
                print e.code, e.msg, link
            except: raise
            else:
                for line in resp.readlines():
                    if 'You are requesting:' in line:
                        flag = True
                    if flag:
                        if 'txtgray' in line:
                            base  = line.split('<')
                            title = base[0]
                            size  = base[1].split('>')[1]
                            break
            self.liste_checked.append( [ link, title, size ] )
       
    def fshared(self, urls):
        self.liste_checked = []
        for link in urls:
            resp = self.get_http_data(link)
            title = 0
            size  = 0
            flag = False
            for line in resp.readlines():
                if 'boxdescrballoon' in line:
                    flag = True
                if flag:
                    if 'title' in line:
                        try:
                            size = re.search('<b>(.*?)</b>', line).group(1)
                        except: continue
                    elif 'fileNameTextSpan' in line:
                        title = line.split('>')[1].rstrip().replace('&amp;', '&')
                        break
            self.liste_checked.append( [ link, title, size ] )
    
    def depositfiles(self, urls):
        self.liste_checked = []
        for link in urls:
            resp = self.get_http_data(link)
            title = 0
            size  = 0
            for line in resp.readlines():
                if 'File name:' in line:
                    title = line.split('"')[1]
                elif 'File size' in line:
                    size = line.split('>')[2].split('<')[0].replace('&nbsp;','')
                    break
            self.liste_checked.append( [ link, title, size ] )
       
    def megashares(self, urls):
        self.liste_checked = []
        for link in urls:
            resp = self.get_http_data(link)
            title = 0
            size  = 0
            for line in resp.readlines():
                if 'black xxl' in line:
                    title = line.split('"')[5]
                elif '>Filesize:<' in line:
                    size = line.split('</strong>')[1].split('<')[0]
                    break              
            self.liste_checked.append( [ link, title, size ] )      	    
        
    # ------------ WITH API --------------- #
    def hotfile(self, urls):
        self.liste_checked = []
        def get(links):
            files = ''
            dic   = {}
            for link in links:
                files += ',%s' % link
                id = link.split('/')[4]
                dic[id] = link
            print dic
            url  = ' http://api.hotfile.com/?action=checklinks'
            url += '&fields=status,id,name,size'
            url += '&links=%s' % files[1:]
            resp = self.get_http_data(url)
            for dl in resp.read().rstrip().split('\n'):
                print dl
                title = 0
                size  = 0
                l_args = dl.split(',')
                print l_args
                link = dic[ l_args[1] ]
                if l_args[0] == '1':
                    title = l_args[2]
                    size  = humanreadable( int(l_args[3]) )
                self.liste_checked.append( [ link, title, size ] )
        get(urls)
    
    def wupload(self, urls):
        self.filesonic(urls, 'wupload')
    
    def filesonic(self, urls, server='filesonic'):
        self.liste_checked = []
        self.nums = ''
        def get_folder(link):
            l = []
            flag = False
            resp = self.get_http_data(link)
            for line in self.get_http_data(link).readlines():
                if 'Description:' in line:
                    flag = True
                    continue
                if flag:
                    if 'href="' in line:
                        l.append( line.split('"')[9] )
                    if '</tbody>' in line:
                        return l

        def iter_num(liste):
            for url in liste:                  
                luri = url.split('/')
                num  = luri[-1]
                if len(luri) > 5:
                    num  = luri[-2]
                self.nums += ','+num
       
        def get(links):
            for url in links:
                if '/folder/' in url:
                    iter_num( get_folder(url) )
                    continue
                iter_num([url])
            print self.nums[1:]
            url = 'http://api.%s.com/link?method=getInfo&ids=%s' % (server, self.nums[1:])
            response = self.get_http_data(url, None)
            dic_json = json.loads(response.read())
            
            for fichier in dic_json["FSApi_Link"]["getInfo"]["response"]["links"]:
                print 'fichier_________',fichier
                try:
                    link = fichier['url']
                    title = fichier['filename']
                    size = fichier['size']
                    size = humanreadable( int(size) )
                    print 'lns______',link, title, size
                except:
                    title = 0
                    size  = 0
                    link  = fichier['id']
                self.liste_checked.append( [ link, title, size ] )
        get(urls)
   
    def megaupload(self, urls):
        self.liste_checked = []
        def get(links):
            n    = 0
            data = {}
            for link in links:
                num = link.split('=')[1]
                data['id%s' % n] = num
                n += 1
            response = self.get_http_data('http://megaupload.com/mgr_linkcheck.php', data)
            dic_args = urlparse.parse_qs(response.read())
            print dic_args
            for idn in data: 
                print idn, dic_args[idn]
                title = 0
                size  = 0
                if dic_args[idn][0] == '0':
                    n = int(idn[-1])
                    print n
                    link = 'http://www.megaupload.com/?d=%s' % data[idn]
                    title = dic_args['n'][n]
                    size  = humanreadable( int(dic_args['s'][n]) )
                self.liste_checked.append( [ link, title, size  ] )
        get(urls)
	    
    def rapidshare(self, urls):
        self.liste_checked = []
        def get(links):
            files = ''
            fname = ''
            for link in links:
                base = link.replace('.html','').split('/')
                files += ',%s' % base[-2]
                fname += ',%s' % base[-1]
            data = { 'sub'       : 'checkfiles',
                     'files'     : files[1:],
                     'filenames' : fname[1:],
                   }
            print data
            response = self.get_http_data('https://api.rapidshare.com/cgi-bin/rsapi.cgi', data)
            #print response
            for dl in response.read().rstrip().split('\n'):
                print dl
                title = 0
                size  = 0
                l_args = dl.split(',')
                print l_args
                if l_args[4] == '1' and not l_args[0].startswith('ERROR:'):
                    link  = 'http://rapidshare.com/files/'+l_args[0]+'/'+l_args[1]+'.html'
                    title = l_args[1]
                    size  = humanreadable( int(l_args[2]) )
                self.liste_checked.append( [ link, title, size ] )
        get(urls)
        
	    
	    
#if __name__ == '__main__':
##link = ['http://www.megaupload.com/?d=W23DXOB9','http://www.megaupload.com/?d=WVGCW6Y9']
##link = ['http://rapidshare.com/files/136233047/RZA-RZA_As_Bobby_Digital_In_Stereo-1998-TMC.rar.html',
        ##'http://rapidshare.com/files/402112913/HMVECyper_-_The_RZA_Instrumentals__2010_.rar.html']
##link = ['http://www.filesonic.com/file/1472564264/VA-Reggaevol.01to37.part01.rar',
        ##'http://www.filesonic.com/file/1473702024/VA-Reggaevol.01to37.part02.rar']
##link = ['http://www.filesonic.fr/folder/10359291']
##link = ['http://www.wupload.com/folder/437369']
##link = [ 'http://hotfile.com/dl/14839164/3d6e68e/Bob_Marley_-_1970_African_Herbsman.zip.html',
##'http://hotfile.com/dl/107996922/0ce3a0a/Bob_Marley_Exodus_Documentary_BBC_Two_2007_06_03.avi.html']
###link = ['http://www.mediafire.com/?wjwnxybymqr']
##link = ['http://d01.megashares.com/index.php?d01=wmQUKpU',
        ##'http://d01.megashares.com/index.php?d01=wmQUK']
##link = ['http://depositfiles.com/files/y7pz4x9xo']
##link = ['http://www.4shared.com/file/urHfeeq9/bob_marley_-_1978_-_bob_marley.htm?aff=7637829',
        ##'http://www.4shared.com/audio/CEXBDdh2/Bob_Marley_-_Bad_Boys__Origina.htm?aff=7637829']
##link = ['http://www.easy-share.com/1911226540/Bob_Marley_vs_Lee_Scratch_Perry_The_Best_of_The_Upsetter_Years_1970_1971_by_eliel.viana.rar',
        ##'http://www.easy-share.com/1913442150/Bob']
##link = ['http://rapidshare.com/files/417197962/Rza_-_19-Odyssey.mp3.html']
#link_checker = CheckLinkIntegrity()
#print link_checker.check(link)

