# Copyright (C) 2006-2013, Stefan Schwarzer <sschwarzer@sschwarzer.net>
# See the file LICENSE for licensing terms.

"""
ftp_stat_cache.py - cache for (l)stat data
"""

from __future__ import unicode_literals

import time

import ftputil.error
import ftputil.lrucache


# This module shouldn't be used by clients of the ftputil library.
__all__ = []


class StatCache(object):
    """
    Implement an LRU (least-recently-used) cache.

    `StatCache` objects have an attribute `max_age`. After this
    duration after _setting_ it a cache entry will expire. For
    example, if you code

    my_cache = StatCache()
    my_cache.max_age = 10
    my_cache["/home"] = ...

    the value my_cache["/home"] can be retrieved for 10 seconds. After
    that, the entry will be treated as if it had never been in the
    cache and should be fetched again from the remote host.

    Note that the `__len__` method does no age tests and thus may
    include some or many already expired entries.
    """

    # Disable "Badly implemented container" warning because of
    # "missing" `__delitem__`.
    # pylint: disable=incomplete-protocol

    # Default number of cache entries
    _DEFAULT_CACHE_SIZE = 5000

    def __init__(self):
        # Can be reset with method `resize`
        self._cache = ftputil.lrucache.LRUCache(self._DEFAULT_CACHE_SIZE)
        # Never expire
        self.max_age = None
        self.enable()

    def enable(self):
        """Enable storage of stat results."""
        self._enabled = True

    def disable(self):
        """
        Disable the cache. Further storage attempts with `__setitem__`
        won't have any visible effect.

        Disabling the cache only effects new storage attempts. Values
        stored before calling `disable` can still be retrieved unless
        disturbed by a `resize` command or normal cache expiration.
        """
        # `_enabled` is set via calling `enable` in the constructor.
        # pylint: disable=attribute-defined-outside-init
        self._enabled = False

    def resize(self, new_size):
        """
        Set number of cache entries to the integer `new_size`.
        If the new size is smaller than the current cache size,
        relatively long-unused elements will be removed.
        """
        self._cache.size = new_size

    def _age(self, path):
        """
        Return the age of a cache entry for `path` in seconds. If
        the path isn't in the cache, raise a `CacheMissError`.
        """
        try:
            return time.time() - self._cache.mtime(path)
        except ftputil.lrucache.CacheKeyError:
            raise ftputil.error.CacheMissError(
                    "no entry for path {0} in cache".format(path))

    def clear(self):
        """Clear (invalidate) all cache entries."""
        self._cache.clear()

    def invalidate(self, path):
        """
        Invalidate the cache entry for the absolute `path` if present.
        After that, the stat result data for `path` can no longer be
        retrieved, as if it had never been stored.

        If no stat result for `path` is in the cache, do _not_
        raise an exception.
        """
        #XXX To be 100 % sure, this should be `host.sep`, but I don't
        # want to introduce a reference to the `FTPHost` object for
        # only that purpose.
        assert path.startswith("/"), ("{0} must be an absolute path".
                                      format(path))
        try:
            del self._cache[path]
        except ftputil.lrucache.CacheKeyError:
            # Ignore errors
            pass

    def __getitem__(self, path):
        """
        Return the stat entry for the `path`. If there's no stored
        stat entry or the cache is disabled, raise `CacheMissError`.
        """
        if not self._enabled:
            raise ftputil.error.CacheMissError("cache is disabled")
        # Possibly raise a `CacheMissError` in `_age`
        if (self.max_age is not None) and (self._age(path) > self.max_age):
            self.invalidate(path)
            raise ftputil.error.CacheMissError(
                    "entry for path {0} has expired".format(path))
        else:
            #XXX I don't know if this may raise a `CacheMissError` in
            # case of race conditions. I prefer robust code.
            try:
                return self._cache[path]
            except ftputil.lrucache.CacheKeyError:
                raise ftputil.error.CacheMissError(
                        "entry for path {0} not found".format(path))

    def __setitem__(self, path, stat_result):
        """
        Put the stat data for the absolute `path` into the cache,
        unless it's disabled.
        """
        assert path.startswith("/")
        if not self._enabled:
            return
        self._cache[path] = stat_result

    def __contains__(self, path):
        """
        Support for the `in` operator. Return a true value, if data
        for `path` is in the cache, else return a false value.
        """
        try:
            # Implicitly do an age test which may raise `CacheMissError`.
            self[path]
        except ftputil.error.CacheMissError:
            return False
        else:
            return True

    #
    # The following methods are only intended for debugging!
    #
    def __len__(self):
        """
        Return the number of entries in the cache. Note that this
        may include some (or many) expired entries.
        """
        return len(self._cache)

    def __str__(self):
        """Return a string representation of the cache contents."""
        lines = []
        for key in sorted(self._cache):
            lines.append("{0}: {1}".format(key, self[key]))
        return "\n".join(lines)
