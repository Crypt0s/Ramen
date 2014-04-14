#!/usr/bin/python

import httplib, urlparse, urllib, socket
import imp
from BTrees import OOBTree
import persistent
from BeautifulSoup import *
import time
import pdb

# required
if __name__ != "__main__":
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
        if path == '/':
            slash = ''
        else:
            slash = '/'

        conn.request("GET", slash+path)
        r1 = conn.getresponse()
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
        print str(r1.status) + ' ' + path
        r1.url = path
        return response_handlers[r1.status](r1) #this seems uglier than sin.
            
    def __parse(self,result = None):
        type = result.getheader('content-type')

        if type == None or 'text' not in type:
            # return the result object.
            return (result.url, [], [])
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
        valid_urls = []
        for url in urls:
            v_url = self.__validateURL(url)
            if v_url is not None:
                # See if it's not already marked for scanning
                if v_url not in self.scanned and v_url not in self.to_scan:
                    valid_urls.append(v_url)
                    self.to_scan.append(v_url)

        print len(self.to_scan)
        return (result.url,[],valid_urls)

    def __validateURL(self,url):
        # NO email addresses, please
        if 'mailto:' in url[0:7]:
            return None

        s_url = urlparse.urlsplit(url)
        # relative path
        if s_url.netloc == '':
            return url

        # not on the same domain.
        if s_url.netloc != self.host or s_url.scheme != 'http':
            return None

        # Build url query
        try:
            path = urllib.url2pathname(s_url.path)
            path = urllib.pathname2url(s_url.path)
            path = path + '?' + s_url.query
        except:
            # Must use that ISO format....for at least fark -- still testing
            path = urllib.quote(urllib.unquote(path).encode('iso-8859-1'))

        # strip "?" from the end
        if path[-1] == '?':
            return path[0:-1]          

    # follow redirects as long as they are within target scope
    def __redirect(self,r1):
        location = r1.getheader('location')
        s_url = urlparse.urlsplit(location)
        path = s_url.path
        if self.host in s_url.netloc:
            self.host = s_url.netloc
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
        conn = httplib.HTTPConnection(self.host,self.port)
        try:
            conn.request("GET","/")
            response = conn.getresponse()
        except:
            #import traceback
            #print traceback.format_exc()
            return ('',[],[])
        return True
        
    def __error(self,result):
        print result.status()
        return ('',[],[])
    
    def __apperror(self,result):
        #print "The spider made a request the server couldn't handle -- this is probably a bug in the spider."
        print result.status
        return ('',[],[])
    
    def __auth(self):
        return ('',[],[])

    def stat(self,url):
        print "stat"
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
        st_mtime = 0

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
                server_time = time.mktime(time.strptime(longdate,'%a, %d %b %Y %H:%M:%S %Z'))                
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
#        else:
#            st_time = st_time - time_diff

        # kinda just assume...
        user = "www" #TODO: or whatever the username is in the basic auth section!!!
        group = "www"
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
    fs = filesystem('http://www.asdf.com')
    gen = fs.walk('/')
    while 1:
        try:
            gen.next()
        except:
            pdb.set_trace()
