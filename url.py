import urllib
import urlparse

def urlencode(string):
    enc = urllib.urlencode({'':string})
    return enc.split('=',1)[1]

def urldecode(string):
    ret = {}
    for pair in string.split('&'):
        pair = pair.split('=',1)
        if len(pair) == 2:
            ret[urllib.unquote_plus(pair[0])] = urllib.unquote_plus(pair[1])
        else:
            print 'problem urldecoding ' + pair
    return ret

def is_absolute(url):
    return bool(urlparse.urlparse(url).netloc)
