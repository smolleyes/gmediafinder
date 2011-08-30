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
        self.serveurs = ['megaupload', 'rapidshare', 'filesonic', 'wupload', 'hotfile',
                         'megashares', 'depositfiles', '4shared', 'easy-share', 'fileserve',
                         'mediafire', 'filefactory']
	
    def check(self, link, callback=None):
        '''
        @link = [url, url, ...]
        @callback = function to call for each link
        '''
        self.liste_checked = []
        link = [ i for i in link if i ]
        flag = True
        print 'in link checker', link
        for server in self.serveurs:
            if server in link[0]:
                flag = False
                server = server.replace('-','_').replace('4','f')
                getattr(self, server)(link, callback)
        if flag: # server not supported
            try:
                callback( link )
            except:
                pass
            return link # retourne liste d'origine si serveur pas supporté
        return self.liste_checked # peut retourner une liste vide si aucun lien valide
	        
    def add_link(self, link, callback):
        '''
        @link = [link, name, size, server] or [link, 0, 0, server]
        @callback = function to call with link
        '''
        self.liste_checked.append( link )
        print '__________add_link', link, callback
        try:
            callback(link)
        except:
            print 'no callback requested'
    
    def get_http_data(self, url, data=None):
        '''
        @url = url
        @data = dictionnary of url arguments
        '''
        if data is not None:
            data = urllib.urlencode(data)
        print url
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        return response
        print response.info()
        print response.geturl()
        print response.read()
    
    def filefactory(self, urls, callback):
        # A revoir !!!
        self.liste_checked = []
        found = []
        flag  = False
        links = '\n'.join(urls)
        data  = { 'func' : 'links',
                  'links': links }
        resp = self.get_http_data('http://www.filefactory.com/tool/links.php', data)
        for line in resp.readlines():
            if 'Available Files' in line:
                flag = True
            if flag:
                if 'href' in line:
                    print line
                    link  = line.split('"')[1]
                    linkc = '%s/' % '/'.join(link.split('/')[0:5])
                    title = line.split('>')[1].split('<')[0]
                    print link, title
                    found.append(linkc)
                elif re.search('<td>([0-9]*.*?)</td>', line):
                    size = re.search('<td>([0-9]*.*?)</td>', line).group(1)
                    print '__________size_________',size
                    self.add_link( [ link, title, size, 'filefactory' ], callback)
                elif '</table>' in line:
                    break
        for no_found in [i for i in urls if i not in found ]:
                print '____no found', no_found
                self.add_link( [ no_found, 0, 0, 'filefactory' ], callback)
    
    def mediafire(self, urls, callback):
        self.liste_checked = []
        for link in urls:
            title = 0
            size  = 0
            resp = self.get_http_data(link)
            for line in resp.readlines():
                if 'download_file_title' in line:
                    gg    = re.search('download_file_title[^>]*>(.*?)<div[^>]*>(.*?)<',line)
                    title = gg.group(1)
                    size  = gg.group(2)
                    break
            self.add_link( [ link, title, size, 'mediafire' ], callback)
    
    def fileserve(self, urls, callback):
        self.liste_checked = []
        for link in urls:
            title = 0
            size  = 0
            resp = self.get_http_data(link)
            for line in resp.readlines():
                if 'readonly' in line:
                    try:
                        base  = line.split('<br/>')
                        size  = base[1]
                        title = base[0].split('<b>')[1]
                        break
                    except: pass
            self.add_link( [ link, title, size, 'fileserve' ], callback)           
            
            
    def easy_share(self, urls, callback):
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
            self.add_link( [ link, title, size, 'easy-share' ], callback)
       
    def fshared(self, urls, callback):
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
            self.add_link( [ link, title, size, '4shared' ], callback)
    
    def depositfiles(self, urls, callback):
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
            self.add_link( [ link, title, size, 'depositfiles' ], callback)
       
    def megashares(self, urls, callback):
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
            self.add_link( [ link, title, size, 'megashares' ], callback)      	    
        
    # ------------ WITH API --------------- #
    def hotfile(self, urls, callback):
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
                self.add_link( [ link, title, size, 'hotfile' ], callback)
        get(urls)
    
    def wupload(self, urls, callback):
        self.filesonic(urls, callback, 'wupload')
    
    def filesonic(self, urls, callback, server='filesonic'):
        # a voir histoire de .fr .com pour filesonic
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
                    link  = fichier['url']
                    #link  = fichier['url'].replace('.fr/','.com/')
                    title = fichier['filename']
                    size  = fichier['size']
                    size  = humanreadable( int(size) )
                    print 'lns______',link, title, size
                except:
                    title = 0
                    size  = 0
                    link  = fichier['id']
                self.add_link( [ link, title, size, server ], callback)
        get(urls)
    
    def megaupload(self, urls, callback):
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
                self.add_link( [ link, title, size, 'megaupload'  ], callback)
        get(urls)
	    
    def rapidshare(self, urls, callback):
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
                self.add_link( [ link, title, size, 'rapidshare' ], callback)
        get(urls)
	    
	    
	    
if __name__ == '__main__':
    def my_callback(link):
        print '____in my callback ___', link
    
    link = ['http://www.megaupload.com/?d=W23DXOB9','http://www.megaupload.com/?d=WVGCW6Y9']
    link = ['http://rapidshare.com/files/136233047/RZA-RZA_As_Bobby_Digital_In_Stereo-1998-TMC.rar.html',
            'http://rapidshare.com/files/402112913/HMVECyper_-_The_RZA_Instrumentals__2010_.rar.html']
    link = ['http://www.filesonic.com/file/1472564264/VA-Reggaevol.01to37.part01.rar',
            'http://www.filesonic.com/file/1473702024/VA-Reggaevol.01to37.part02.rar']
    link = ['http://www.filesonic.fr/folder/10359291']
    link = ['http://www.wupload.com/folder/437369']
    link = [ 'http://hotfile.com/dl/14839164/3d6e68e/Bob_Marley_-_1970_African_Herbsman.zip.html',
    'http://hotfile.com/dl/107996922/0ce3a0a/Bob_Marley_Exodus_Documentary_BBC_Two_2007_06_03.avi.html']
    #link = ['http://www.mediafire.com/?wjwnxybymqr']
    link = ['http://d01.megashares.com/index.php?d01=wmQUKpU',
            'http://d01.megashares.com/index.php?d01=wmQUK']
    link = ['http://depositfiles.com/files/y7pz4x9xo']
    link = ['http://www.4shared.com/file/urHfeeq9/bob_marley_-_1978_-_bob_marley.htm?aff=7637829',
            'http://www.4shared.com/audio/CEXBDdh2/Bob_Marley_-_Bad_Boys__Origina.htm?aff=7637829']
    link = ['http://www.easy-share.com/1911226540/Bob_Marley_vs_Lee_Scratch_Perry_The_Best_of_The_Upsetter_Years_1970_1971_by_eliel.viana.rar',
            'http://www.easy-share.com/1913442150/Bob']
    link_checker = CheckLinkIntegrity()
    print link_checker.check(link, my_callback)
    
