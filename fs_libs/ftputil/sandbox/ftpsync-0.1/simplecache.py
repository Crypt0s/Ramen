import threading
import loggingclass
import time

class CacheEntry:
    """
    A class representing a cache entry.
    x = CacheEntry(<some object>)
    """

    def __init__(self, val):
        self.val = val
        self.stamp = time.time()

    def expired(self, period):
        """
        Boolean: returns true if the entry is older than period (in sec).
        """
        return time.time() - self.stamp > period

    def __cmp__(self, other):
        """
        CacheEntry objects can be compared by age.
        """
        return cmp(self.stamp, other.stamp)


class Cache(loggingclass.LoggingClass):
    """
    A simple cache implementation

    Usage: c = Cache(expire=<expire>, size=<size>, entryclass=CacheEntry)
    <expire>:   expiration time of entries in sec (default: 60)
    <size>:     max number of cache entries (default: 1000)
    <entryclass>: A class for the cache entries (default: CacheEntry)

    NOTE: EXPIRED ENTRIES WILL BE DELETED.
    Do not use this class (exclusively) to store valuable data.

    Entries are assigned and retrieved through indexing:
        cache[x] = val
        try:
           val = cache[x]
        except KeyError:
           print x, ": not in cache"
        cache.invalidate(x)

    doctest example:

>>> from time import sleep
>>> exp=2.0
>>> cache = Cache(size=10, expire=exp)
>>> for x in range(0, 10):
...     cache[x] = x*x
>>> print cache.contents()
[(0, 0), (1, 1), (2, 4), (3, 9), (4, 16), (5, 25), (6, 36), (7, 49), (8, 64), (9, 81)]
>>> for x in range(11, 20):
...     cache[x] = x*x
>>>
>>> # size exceeded - old elements will be deleted
>>> print cache.contents()
[(11, 121), (12, 144), (13, 169), (14, 196), (15, 225), (16, 256), (17, 289), (18, 324), (19, 361)]
>>> sleep(exp/2.)
>>> for x in range(0, 5):
...     cache[x] = x*x
>>> print cache.contents()
[(0, 0), (1, 1), (2, 4), (3, 9), (4, 16), (16, 256), (17, 289), (18, 324), (19, 361)]
>>> sleep(exp/2.+0.1)
>>>
>>> # elements 11 .. 20 will be expired
>>> print cache.contents()
[(0, 0), (1, 1), (2, 4), (3, 9), (4, 16)]
    """

    default_expire = 60
    default_size = 1000
    _to_shrink = 100      # No. of entries to delete in a _shrink() call

    def __init__(self, expire = default_expire, size = default_size,
                 entryclass = CacheEntry):
        self.__cache = {}
        self.__size = size
        self.expire = expire
        self.__lock = threading.Lock()
        self._entryclass = entryclass

    def _lock(self):
        self.__lock.acquire()

    def _unlock(self):
        self.__lock.release()

    def _invalidate(self, key):
        if self.__cache.has_key(key):
            del self.__cache[key]
            return True
        return False
        
    def len(self):
        """
        Return current number of cache entries.
        """
        return len(self.__cache)

    def invalidate(self, key):
        """
        Invalidate (delete) cache entry indexed by key
        """
        self._lock()
        try:
            if self._invalidate(key):
                self.logger.debug("element %s invalidated" % key)
        finally:
            self._unlock()

    def invalidate_all(self):
        """
        Clear cache completetly
        """
        self._lock()
        try:
            self.__cache.clear()
        finally:
            self._unlock()
        self.logger.info("cache cleared")

    def invalidate_some(self, func):
        """
        Invalidate all entries for which func(key,val) returns True
        """
        self._lock()
        try:
            for x in self.__cache.keys():
                if func(x, self.__cache[x].val):
                    self._invalidate(x)
                    self.logger.debug("element %s invalidated" % x)
        finally:
            self._unlock()
        
    def _expired(self, entry):
        return self.expire != 0 and entry.expired(self.expire)

    def __getitem__(self, key):
        """
        Implements x = cache[key].
        Will raise KeyError if the cache entry is expired.
        """
        ret = None
        self._lock()
        try:
            entry = self.__cache[key]
            if self._expired(entry):
                self._gc()
                raise KeyError
            else:
                ret = entry.val
        finally:
            self._unlock()

        return ret

    def __setitem__(self, key, val):

        """
        Implements cache[key] = y.
        """
        self._lock()
        try:
            self._invalidate(key)
            if self.len() >= self.__size:
                self._shrink()
            self.__cache[key] = self._entryclass(val)
        finally:
            self._unlock()

    def _shrink(self):
        # Must be called with lock held
        target = self.__size - min(self.__size/2, self._to_shrink)
        self.logger.debug("_shrink: trying to reduce size from %d to %d"
                          % (self.len(), target))

        self._gc()

        n = self.len() - target
        if n <= 0:
            return

        # sort entries by age and invalidate the n oldest
        keys = self.__cache.keys()
        keys.sort(lambda a, b, c=self.__cache: cmp(c[a], c[b]))

        self.logger.info("_shrink: invalidating %d entries" % n)
        for key in keys[:n]:
            self._invalidate(key)

    def _gc(self):
        # Must be called with lock held
        expired = []
        for key in self.__cache.keys():
            if self._expired(self.__cache[key]):
                expired.append(key)
        for key in expired:
            self._invalidate(key)
        self.logger.info("collecting garbage: %d items invalidated"
                         % len(expired))

    def contents(self):
        """
        returns a list of (key, val) tuples for all non-expired entries
        """
        self._lock()
        try:
            self._gc()
            ret = [(x, self.__cache[x].val) for x in self.__cache.keys()]
        finally:
            self._unlock()
        return ret


def _test():
    import doctest, simplecache
    doctest.testmod(simplecache)

if __name__ == "__main__":
    _test()
