# -*- coding:utf-8 -*-
import urlparse
import datetime
import time
import random
import urllib2
import socket


DEFAULT_DELAY = 5
DEFAULT_USER_AGENT = 'py_agent'
DEFAULT_RETRIES = 1
DEFAULT_TIMEOUT = 60


class Downloader:
    def __init__(self,
                 delay=DEFAULT_DELAY,
                 user_agent=DEFAULT_USER_AGENT,
                 proxies=None,
                 num_retries=DEFAULT_RETRIES,
                 timeout=DEFAULT_TIMEOUT,
                 cache=None):
        socket.setdefaulttimeout(timeout)
        self.throttle = Throttle(delay)
        self.delay = delay
        self.user_agent = user_agent
        self.proxies = proxies
        self.num_retries = num_retries
        self.cache = cache

    def __call__(self, url):
        result = None
        if self.cache:
            try:
                result = self.cache[url]
            except KeyError:
                pass
            else:
                if self.num_retries > 0 and 500 <= result['code'] < 600:
                    result = None
        if result is None:
            self.throttle.wait(url)
            proxy = random.choice(self.proxies) if self.proxies else None
            headers = {'User-agent': self.user_agent}
            result = self.download(url, headers, proxy, self.num_retries)
            if self.cache:
                self.cache[url] = result
        return result['html']

    def download(self, url, headers={}, proxy=None, num_retries=1, data=None):
        print 'Download:', url
        request = urllib2.Request(url, data, headers or {})
        opener = self.opener or urllib2.build_opener()
        if proxy:
            proxy_params = {urlparse.urlparse(url).scheme: proxy}
            opener.add_handler(urllib2.ProxyHandler(proxy_params))
        try:
            response = opener.open(request)
            html = response.read()
            code = response.code
        except Exception as e:
            print 'Download error', str(e)
            html = ''
            if hasattr(e, 'code'):
                code = e['code']
                if num_retries > 0 and 500 <= code < 600:
                    return self.download(url, headers, proxy, num_retries - 1,
                                         data)
                else:
                    code = None
        return {'html': html, 'code': code}


class Throttle:
    """ Add a delay between downloads to the same domain
    """

    def __init__(self, delay):
        self.delay = delay
        self.domains = {}

    def wait(self, url):
        # parse url into 6-tuple
        # scheme='http', netloc='www.cwi.nl:80', path='/%7Eguido/Python.html',
        # params='', query='', fragment=''
        domain = urlparse.urlparse(url).netloc
        lastaccess = self.domains.get(url)

        if self.delay > 0 and lastaccess is not None:
            sleep_secs = self.delay - (
                datetime.datetime.now() - lastaccess).second
            if sleep_secs > 0:
                time.sleep(sleep_secs)
        self.domains[domain] = datetime.datetime.now()