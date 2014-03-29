#!/usr/bin/python

import httplib, urlparse, socket
from BeautifulSoup import *
import pdb

scanned = []
def request(host,path):
    # Meat method
    global scanned
    if path in scanned:
        return
    scanned.append(path)
    print (len(scanned)),
    def parse(result = None):
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
        to_scan = []
        for url in urls:
            if 'mailto' in url:
                continue
            p_url = urlparse.urlsplit(url)
            # Relative path, add additional info and reparse
            if p_url.netloc == '':
                target_url = urlparse.urljoin('http://'+host+path,p_url.path)
                to_scan.append(target_url)
            # keep it http and keep it on-target
            if host == p_url.netloc and 'http' == p_url.scheme:
                to_scan.append(url)
        for url in to_scan:
            p_url = urlparse.urlsplit(url)
            request(p_url.netloc,p_url.path)

    # follow redirects as long as they are within target scope
    def redirect(*args):
        location = r1.getheader('location')
        url = urlparse.urlsplit(location)
        path = url.path
        redir_host = url.netloc

        # don't go off-target, and don't move off http - we only were asked for http!
        if host == redir_host and url.scheme == 'http':
            request(host,path)
        else:
            # error out, it tried to redirect me away from target.
            pass
        
    def error(result):
        pass
    
    def apperror(result):
        print "The spider made a request the server couldn't handle -- this is probably a bug in the spider."

    def auth():
        pass
    
    ip = socket.gethostbyname_ex(host)
    conn = httplib.HTTPConnection(host)
    conn.request("GET", path)
    r1 = conn.getresponse()
    response_handlers = {
        301:redirect,
        302:redirect,
        307:redirect,
        200:parse,
        401:auth,
        403:auth,
        404:error,
        400:apperror
    }
    response_handlers[r1.status](r1) #this seems uglier than sin.

if __name__ == "__main__":
    request('asrcfederal.com','/')
