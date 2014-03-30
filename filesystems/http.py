#!/usr/bin/python

import httplib, urlparse, socket
import imp
from BTrees import OOBTree
import persistent
from BeautifulSoup import *
import pdb

# required
settings = imp.load_source('settings','fs_settings/http.py')
product = 'http'

class filesystem(persistent.Persistent):

    def __init__(self):
        self.scanned = []
        self.to_scan = []
        self.product = "http"

        # required
        self.root = OOBTree.OOBTree()


    def walk(self,url):
        # need to initialize here
        self.to_scan = [url]
        for url in self.to_scan:
            s_url = urlparse.urlsplit(url)
            yield self.__request(s_url.netloc,s_url.path)

    def __request(self, host,path):
        # Meat method
        if path in self.scanned:
            return
        self.scanned.append(path)
        self.host = host
        self.path = path
        print (len(self.scanned)),
        ip = socket.gethostbyname_ex(self.host)
        conn = httplib.HTTPConnection(self.host)
        conn.request("GET", path)
        self.r1 = conn.getresponse()
        response_handlers = {
            301:self.__redirect,
            302:self.__redirect,
            307:self.__redirect,
            200:self.__parse,
            401:self.__auth,
            403:self.__auth,
            404:self.__error,
            400:self.__apperror
        }
        return response_handlers[self.r1.status](self.r1) #this seems uglier than sin.
            
    def __parse(self,result = None):
        type = result.getheader('content-type')
        if 'text' not in type:
            return
        # Check to see if this was called from redirect
        soup = BeautifulSoup(result.read())
        urls = []
        # These two attributes are going to be the most reliable
        # TODO: I should let the tag attributes we want to pull urls out of be usr-defined in the fs settings.
        for tag in soup.findAll(href=True):
            urls.append(tag['href'])
        for tag in soup.findAll(src=True):
            urls.append(tag['src'])
        # OK, now see if the URL's match the target.
        # TODO: do we want to check if the url is on the same IP or not?
        for url in urls:
            if 'mailto:' in url[0:7]:
                urls.remove(url)
                continue
            p_url = urlparse.urlsplit(url)
            # Relative path, add additional info and reparse
            if p_url.netloc == '':
                target_url = urlparse.urljoin('http://'+self.host+self.path,p_url.path)
                self.to_scan.append(target_url)
            # keep it http and keep it on-target
            if self.host == p_url.netloc and 'http' == p_url.scheme:
                self.to_scan.append(url)
        print dir(self.r1)
        return (self.r1,urls)

    # follow redirects as long as they are within target scope
    def __redirect(self,*args):
        location = self.r1.getheader('location')
        url = urlparse.urlsplit(location)
        path = url.path
    def validate(self,target):
        # was a specific port specced for the target?  If not, asusme 80.
        # this is a user convenience snippet.
        try:
            getattr(target,'port')
        except:
            target.port = 80

        #nutz und boltz
        conn = httplib.HTTPConnection(target.host,target.port)
        try:
            conn.request("GET","/")
            response = conn.getresponse()
        except:
            return False
        return True
        redir_host = url.netloc
    
        # don't go off-target, and don't move off http - we only were asked for http!
        if self.host == redir_host and url.scheme == 'http':
            self.__request(self.host,path)
        else:
            # error out, it tried to redirect me away from target.
            pass
        
    def __error(self,result):
        pass
    
    def __apperror(self,result):
        print "The spider made a request the server couldn't handle -- this is probably a bug in the spider."
    
    def __auth(self):
        pass

    def stat(url):
        page = self.open(url)
        contents = page.read()
        size = len(contents)

        # kinda just assume...
        user, group = "www" #TODO: or whatever the username is in the basic auth section!!!

        chmod = #whatever the readonly everyone is

        # search for a datestamp with common regexes -- use the settings file to allow user to set these regexes
        # TODO: do that.

        #return the analog
        return (chmod,size)        


    def validate(self,target):
        # was a specific port specced for the target?  If not, asusme 80.
        # this is a user convenience snippet.
        try:
            getattr(target,'port')
        except:
            target.port = 80

        #nutz und boltz
        conn = httplib.HTTPConnection(target.host,target.port)
        try:
            conn.request("GET","/")
            response = conn.getresponse()
        except:
            return False
        return True

    def open(url):
        s_url = urlparse.urlsplit(url)
        conn = httplib.HTTPConnection(s_url.netloc)
        conn.request("GET", s_url.path)
        response = conn.getresponse()
        # this returns something close enough to a FP object to use in Ramen.
        return response.fp

   #required
    @property
    def w_root(self):
        # assume that if we are accessing the file tree in this manner that we must be intending to change it.
        self._p_changed = 1
        # Python returns refs (with the exception of several notable cases) so this should be fine.
        return self.root

if __name__ == "__main__":
    http = http_handler()
    gen = http.walk('http://asrcfederal.com/')
    gen.next()
    pdb.set_trace()