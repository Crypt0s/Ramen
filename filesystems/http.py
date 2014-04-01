#!/usr/bin/python

import httplib, urlparse, urllib, socket
import imp
from BTrees import OOBTree
import persistent
from BeautifulSoup import *
import time
import pdb

# required
settings = imp.load_source('settings','fs_settings/http.py')
product = 'http'

class filesystem(persistent.Persistent):

    def __init__(self,host):
        self.scanned = []
        self.to_scan = []
        self.product = "http"
        # required
        self.root = OOBTree.OOBTree()

        # Did we get a valid URL or not?
        if not host.startswith('http://'):
            host = 'http://' + host

        self.s_url = urlparse.urlsplit(host)
        if self.s_url.netloc == '':
            print "Bad hostname"
    
        self.host = self.s_url.netloc
        
    def walk(self,path):
        # need to initialize here
        self.to_scan = [path]
        while len(self.to_scan) > 0:
            print "going back for another round"
            for path in self.to_scan:
                self.to_scan.remove(path)
                #s_url = urlparse.urlsplit(url)
                yield self.__request(path)

    def __request(self,path):

        # Meat method
        #if path in self.scanned:
        #    return 

        self.scanned.append(path)

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
            404:self.__apperror,
            400:self.__apperror
        }
        print str(self.r1.status) + ' ' + path
        return response_handlers[self.r1.status](self.r1) #this seems uglier than sin.
            
    def __parse(self,result = None):
        type = result.getheader('content-type')
        if 'text' not in type:
            # return the result object.
            return (result, [])
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
            path = ''
            if 'mailto:' in url[0:7]:
                urls.remove(url)
                continue
            s_url = urlparse.urlsplit(url)
            # Relative path, add additional info and reparse
            # TODO: this could be written better
            if s_url.netloc == '':
                url = 'http://'+self.host+url
                s_url = urlparse.urlsplit(url)
                # TODO: all the url's are going to have ?'s in them!
                path = s_url.path
                path = urllib.url2pathname(path)
                path = urllib.pathname2url(path)

                path = path+'?'+s_url.query
            # keep it http and keep it on-target
            if self.host == s_url.netloc and 'http' == s_url.scheme and s_url.path:
                path = s_url.path
                path = urllib.url2pathname(path)
                path = urllib.pathname2url(path)

                path = path + '?' + s_url.query

            if path != '' and path != '?' and path not in self.scanned and path not in self.to_scan:
                self.to_scan.append(path)
        print len(self.to_scan)
        return (result,urls)

    # follow redirects as long as they are within target scope
    def __redirect(self,*args):
        location = self.r1.getheader('location')
        s_url = urlparse.urlsplit(location)
        path = s_url.path
        if self.host in s_url.netloc:
            return self.__request(path)


    def validate(self,target):
        # was a specific port specced for the target?  If not, asusme 80.
        # this is a user convenience snippet.
        try:
            getattr(self,'port')
        except:
            self.port = 80

        #nutz und boltz
        s_url = urlparse.urlsplit(self.host)
        conn = httplib.HTTPConnection(s_url.netloc,self.port)
        try:
            conn.request("GET","/")
            response = conn.getresponse()
        except:
            import traceback
            print traceback.format_exc()
            return False
        return True
        
    def __error(self,result):
        print result.status()
        return False
    
    def __apperror(self,result):
        #print "The spider made a request the server couldn't handle -- this is probably a bug in the spider."
        print result.status
        return False
    
    def __auth(self):
        return False

    def stat(url):
        #since we look at headers too, we start with a fresh request.
        s_url = urlparse.urlsplit(url)
        try:
            conn = httplib.HTTPConnection(s_url.netloc)
            request_time = time.time()
            conn.request("GET",s_url.path+'?'+s_url.query)
            response = conn.getresponse()
        except:
            return None

        st_size = response.length
        st_time = 0

        # Check for last-modified header
        headers = response.getheaders()
        for tuple in headers:
            if 'content-type' in tuple[0]:
                content_type = response.getheader('content-type')

            elif 'age' in tuple[0]:
                # we assume that it's in seconds.  Get the epoch time, subtract age header value, and save
                age = int(response.getheader('age'))
                # round it, because we assume that age is time in whole seconds.
                st_mtime = int(time.time()) - age

            elif 'date' in tuple[0]:
                longdate = response.getheader('date')
                server_time = time.mktime(time.strptime(longtime,'%a, %d %b %Y %H:%M:%S %Z'))                
                time_diff = server_time - request_time
                if time_diff > 60 or time_diff < 60:
                    print "The server's time is significantly different than ours. " + str(time_diff)

            # we prioritize last-modified time over age because it gives info down to the second.
            elif 'last-modified' in tuple[0]:                
                longdate = response.getheader('last-modified')
                st_mtime = time.mktime(time.strptime(longtime,'%a, %d %b %Y %H:%M:%S %Z'))
                break # get out of the loop ASAP -- this should be in the last element checked

# I generally Dont think that the code below is going to end up being a "good idea" without more than just regex. Think more on this.
#
#        # check inside page for a date:
#        if 'text' in content_type:
#            # The fp for socket will hang open and we can't close it and then read the buffer, and we can't trust that we won't hit a multi-gig file.
#            # Therefore, read one line at a time until we the end of the length, as determined by the HTTP response header.
#            fp = response.fp
#            bytes_read = 0
#
#            # if this part is erroring, then the last line contains some text but no \r\n
#            while bytes_read != st_size:
#                line = fp.readline()
#                bytes_read += len(line)
#                for regex_tuple in settings.regex_list:
#                    regex = regex_tuple[0]
#                    datefmt = regex_tuple[1]
#                    if regex.find(line):
#                        st_mtime = time.mktime(time.strptime(regex.group(0),datefmt)        
        if st_time == 0:
            st_time = request_time
#        else:
#            st_time = st_time - time_diff

        # kinda just assume...
        user, group = "www" #TODO: or whatever the username is in the basic auth section!!!

        # read, read, read perms
        chmod = 444

        #return the stat() analog
        return (chmod,None,None,None,user,group,st_size,request_time,st_mtime,None)


    def open(url):
        s_url = urlparse.urlsplit(url)
        conn = httplib.HTTPConnection(s_url.netloc)
        conn.request("GET", s_url.path+'?'+s_url.query)
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

# little unit test-ish thing
if __name__ == "__main__":
    fs = filesystem('http://www.asrcfederal.com')
    gen = fs.walk('/')
    while 1:
        try:
            gen.next()
        except:
            pdb.set_trace()
