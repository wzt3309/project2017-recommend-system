# -*- coding:utf-8 -*-
import urllib2
import re
import urlparse
import datetime
import time


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


def download(url, user_agent='my_agent', num_retries=2):
    print 'Download:', url
    # set User_agent to prevent be denied by Web server
    headers = {'User-agent': user_agent}
    request = urllib2.Request(url, headers=headers)
    try:
        html = urllib2.urlopen(request).read()
        # html is decode by utf-8, so need to change it to unicode first
        # then encode as system coding
        # GB2312 or GBK can't encode all character so need codec gb18030
        # html = unicode(html, 'utf-8').encode('gb18030')
    except urllib2.URLError as e:
        print 'Download Error:', e.reason
        html = None
        if num_retries > 0:
            # recursively retry 5xx HTTP errors
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download(url, num_retries - 1)
    return html


def link_crawler(seed_url, link_regex, delay=3, max_depth=2):
    """Crawl from the given seed URL following links matched link_regex
    """
    crawl_queue = [seed_url]
    has_crawled = {seed_url: 0}
    throttle = Throttle(delay)
    while crawl_queue:
        url = crawl_queue.pop()
        depth = has_crawled[url]
        if depth != max_depth:
            throttle.wait(url)
            html = download(url)
            for link in get_links(html):
                if re.match(link_regex, link):
                    if link not in has_crawled:
                        # judge the link if is relate to url or root
                        base = url
                        # relate to root
                        if link[0] == '/':
                            base = urlparse.urlparse(
                                url).scheme + "://" + urlparse.urlparse(
                                    url).netloc
                            link = link.lstrip('/')
                        if base[-1] != '/':
                            base = base + "/"
                        link = urlparse.urljoin(base, link)
                        crawl_queue.append(link)
                        has_crawled[link] = depth + 1


def get_links(html):
    """Return a list of links from html
    """
    webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
    return webpage_regex.findall(html)


def call_back(url):
    print "Callback", url


if __name__ == '__main__':
    """test simple crawler
    url = 'http://www.acfun.cn/v/list96/index.htm#page=1'
    link_regex = '/v/ac\d+'
    link_crawler(url, link_regex)
    """

    """the content load by js so we can't get video by this way
    from bs4 import BeautifulSoup
    broken_html = '<ul class=country><li>Area<li>Population</ul>'
    soup = BeautifulSoup(broken_html, 'html.parser')
    fixed_html = soup.prettify()
    print fixed_html
    url = 'http://www.acfun.cn/v/list96/index.htm#page=1'
    html = download(url)
    soup = BeautifulSoup(html, 'html.parser')
    print type(soup)
    fixed_html = soup.prettify('gb18030')
    print type(fixed_html)
    div0list_video = soup.find('div', attrs={'id': 'list-video'})
    print type(div0list_video)
    lis0list_video = div0list_video.find_all('li')
    list_video = []
    for li in lis0list_video:
        video = {}
        href = li.find('a', attrs={'class': 'fl img-wp'})['href']
        title = li.find('b', attrs={'class': 'text-over'}).find('a')['title']
        video['href'] = href
        video['title'] = title
        list_video.append(video)

    print list_video
    """

    """ callback funcion
    links = []
    links.extend(call_back('jj') or [])
    print links
    """
