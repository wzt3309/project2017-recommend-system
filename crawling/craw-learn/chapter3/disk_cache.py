# -*- coding:utf-8 -*-
from datetime import datetime, timedelta
import urlparse
import re
import os
import shutil
import zlib
try:
    import cPickle as pickle
except:
    import pickle


DEFAULT_CACHE_DIR = 'cache'
DEFAULT_CACHE_EXPIRES = timedelta(days=30)
DEFAULT_FILENAME_REGEX = '[^0-9a-zA-z\-&%#@.,;_]'
DEFAULT_FILENAME_MAX_LEN = 255


class DiskCache:
    """
    Dictionary interface that stores cached
    values in the file system rather than in memory
    The file path is formed from URL, but best from hash key

    >>> cache = DiskCache()
    >>> url = 'http://example.webscraping.com'
    >>> result = {'html': '....'}
    >>> cache[url] = result
    >>> cache[url]['html'] == result['html']
    True
    >>> cache = DiskCache(expires=timedelta())
    >>> cache[url] = result
    >>> cache[url]
    Traceback (most recent call last):
     ...
    KeyError: 'http://example.webscraping.com has expired'
    >>> cache.clear()
    """
    def __init__(self,
                 cache_dir=DEFAULT_CACHE_DIR,
                 expires=DEFAULT_CACHE_EXPIRES,
                 compress=True):
        self.cache_dir = cache_dir
        self.expires = expires
        self.compress = compress

    def __getitem__(self, url):
        """Load data from disk for this URL
        """
        path = self.url_to_path(url)
        if os.path.exists(path):
            with open(path, "rb") as fp:
                data = fp.read()
                if self.compress:
                    data = zlib.decompress(data)
                result, timestamp = pickle.loads(data)
                if self.has_expired(timestamp):
                    raise KeyError(url + ' has expired')
                return result
        else:
            raise KeyError(url + ' does\'t exist')

    def __setitem__(self, url, result):
        """Save data to disk for this URL
        """
        path = self.url_to_path(url)
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)

        data = pickle.dumps((result, datetime.utcnow()))
        if self.compress:
            data = zlib.compress(data)
        with open(path, 'wb') as fp:
            fp.write(data)

    def __delitem__(self, url):
        """Remove the value at this key and any empty parent sub-directories
        """
        path = self.url_to_path(url)
        try:
            os.remove(path)
            os.removedirs(os.path.dirname(path))
        except OSError:
            pass

    def url_to_path(self, url):
        """Create system path for this URL
        """
        components = urlparse.urlsplit(url)
        path = components.path
        if not path:
            path = '/index.html'
        elif path.endswith('/'):
            path += 'index.html'
        filename = components.netloc + path + components.query
        filename = re.sub(DEFAULT_FILENAME_REGEX, '_', filename)
        # resize the length of filename
        filename = '/'.join(segment[:DEFAULT_FILENAME_MAX_LEN]
                            for segment in filename.split('/'))
        return os.path.join(self.cache_dir, filename)

    def has_expired(self, timestamp):
        """Return whether this timestamp has expired
        """
        return datetime.utcnow() >= timestamp + self.expires

    def clear(self):
        """Remove all the cached values
        """
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
