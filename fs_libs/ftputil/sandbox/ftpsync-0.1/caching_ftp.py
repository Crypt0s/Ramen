from ftputil import FTPHost
from ftputil.ftp_error import PermanentError, InternalError
from loggingclass import LoggingClass
from simplecache import Cache
from casepath import CaseInsPath, CaseInsStat

class CachingFTPHost(FTPHost, LoggingClass):

    """
    This class is like ftputil.FTPHost, except that
    the working directory and directory contents are cached.
    This may speed up FTP operations significantly, especially
    when traversing trees and looking for stat() like information.

    However, cached information may be wrong in some cases.
    It is recommended to call host.invalidate_dir(<path>) after
    closing the ftp_file object associated with <path>.

    Constructor keywords "expire" and "size" are the same as for
    simplecache.Cache.

    Besides, this class adds a method check_case_insensitive() to cope
    with FTP servers that don't distinguish file names by case.

    """

    def __init__(self, *args, **kwargs):

        kw = {}
        if "expire" in kwargs:
            kw["expire"] = kwargs["expire"]
            del kwargs["expire"]
        if "size" in kwargs:
            kw["size"] = kwargs["size"]
            del kwargs["size"]
        self.cache = Cache(**kw)

        FTPHost.__init__(self, *args, **kwargs)
        self.CWD = None
        self.setcwd()

    def check_case_insensitive(self):
        """
        Check for server case-insensivity and 
        This function must be called with an established connection and
        with write permissions (like synchronize_times).
        
        """
        helper_name = "__CachingFtpHost_Helper__"
        try:
            self.mkdir(helper_name)
            self.lstat(helper_name) # exception if mkdir failed
            try:
                # if the server is case-insensitive, this will fail
                file = self.mkdir(helper_name.lower())
            except PermanentError:
                self.logger.warning("Server is case-insensitive")
                self.path = CaseInsPath(self)
                self._stat = CaseInsStat(self)
                self.cache.invalidate_all()
            else:
                self.logger.info("Server is case-sensitive")
        finally:
            self.rmdir(helper_name)

    def getcwd(self):
        """
        Return cached working directory.
        """
        return self.CWD

    def setcwd(self):
        """
        Update cached working directory.
        """
        self.CWD = self.path.normpath(FTPHost.getcwd(self))
        self.logger.info("New cwd: %s" % self.CWD)

    def chdir(self, path):
        FTPHost.chdir(self, path)
        self.setcwd()

    def _dir(self, path):

        path = self.path.normcase(path)
        try:
            lines = self.cache[path]
        except KeyError:
            self.logger.debug("cache miss: %s" % path)
            lines = FTPHost._dir(self, path)
            self.cache[path] = lines
        else:
            self.logger.debug("cache hit: %s" % path)
        return lines

    def _invalidate_dir(self, path):
        self.logger.debug("invalidating cache for %s" % path)
        self.cache.invalidate(
            self.path.normcase(
            self.path.dirname(self.path.abspath(path))))

    def file(self, path, mode='r'):
        path = self.path.abspath(path)
        ret = FTPHost.file(self, path, mode)
        if 'w' in mode:
            self._invalidate_dir(path)
        return ret

    def mkdir(self, path, mode=None):
        path = self.path.abspath(path)
        FTPHost.mkdir(self, path, mode)
        self._invalidate_dir(path)

    def rmdir(self, path):
        FTPHost.rmdir(self, path)
        self.cache.invalidate(self.path.normcase(
            self.path.abspath(path)))
        self._invalidate_dir(path)

    def remove(self, path):
        FTPHost.remove(self, path)
        self._invalidate_dir(path)

    def rename(self, source, target):
        FTPHost.rename(self, source, target)
        self._invalidate_dir(source)
        self._invalidate_dir(target)
