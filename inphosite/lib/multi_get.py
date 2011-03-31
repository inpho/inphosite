from threading import Thread, enumerate
from urllib2 import urlopen, Request
from time import sleep

UPDATE_INTERVAL = 0.01

class URLThread(Thread):
    def __init__(self,url):
        super(URLThread, self).__init__()
        self.url = url
        self.response = None

    def run(self):
        self.request = Request(self.url, None, 
                                {'Referer' : 'http://inpho.cogs.indiana.edu'})
        self.request = urlopen(self.request)
        self.response = self.request.read()

def multi_get(uris,timeout=2.5):
    def alive_count(lst):
        alive = map(lambda x : 1 if x.isAlive() else 0, lst)
        return reduce(lambda a,b : a + b, alive)
    threads = [ URLThread(uri) for uri in uris ]
    for thread in threads:
        thread.start()
    while alive_count(threads) > 0 and timeout > 0.0:
        timeout = timeout - UPDATE_INTERVAL
        sleep(UPDATE_INTERVAL)
    return [ (x.url, x.response) for x in threads ]

