import posixpath
from ftputil import ftp_path, ftp_stat
from casestr import CaseInsStr

class BasePath(ftp_path._Path):
    """
    A reimplementation of ftputil.ftp_path._Path which is better suited
    as base class than the original _Path.
    """
    # ftputil.ftp_path._Path can't be inherited well because of the
    # direct posixpath assignments in ftputil.ftp_path._Path.__init__(),
    # which subclasses can't overload.

    # Here, dirname(), basename(), etc. are defined as methods which
    # can be overloaded in derived classes.

    # This class inherits _Path in order to avoid duplicating
    # code. Note that _Path.__init__() isn't called.

    def __init__(self, host, pp=posixpath):
        self.pp = pp
        self._host = host

    def dirname(self, *args):
        return self.pp.dirname(*args)

    def basename(self, *args):
        return self.pp.basename(*args)

    def isabs(self, *args):
        return self.pp.isabs(*args)

    def commonprefix(self, *args):
        return self.pp.commonprefix(*args)

    def join(self, *args):
        return self.pp.join(*args)

    def split(self, *args):
        return self.pp.split(*args)

    def splitdrive(self, *args):
        return self.pp.splitdrive(*args)

    def splitext(self, *args):
        return self.pp.splitext(*args)

    def normcase(self, *args):
        return self.pp.normcase(*args)

    def normpath(self, *args):
        return self.pp.normpath(*args)


class CaseInsPath(BasePath):
    """
    A "path" implementation that treats paths in a case-insensitive manner.
    The only difference to BasePath (and _Path) is that all
    returned strings are 'CaseInsStr' objects.
    """
    
    def dirname(self, path):
        return CaseInsStr(BasePath.dirname(self, path))

    def basename(self, path):
        return CaseInsStr(BasePath.basename(self, path))

    def abspath(self, path):
        return CaseInsStr(BasePath.abspath(self, path))

    def normpath(self, path):
        return CaseInsStr(BasePath.normpath(self, path))

    def normcase(self, path):
        return CaseInsStr(path.lower())

    def join(self, *args):
        return CaseInsStr(BasePath.join(self, *args))

    def split(self, *args):
        return [CaseInsStr(x)
                for x in BasePath.split(self, *args)]

    def splitext(self, *args):
        return [CaseInsStr(x)
                for x in BasePath.splitext(self, *args)]

    def splitdrive(self, *args):
        return [CaseInsStr(x)
                for x in BasePath.splitdrive(self, *args)]


class CaseInsStat(ftp_stat._Stat):
    """
    A class derived from _Stat that treats file names in a case insensitive
    manner.

    E.g. "Spam" will be found and stat'd in a directory listing "spam, eggs".
    """

    def _stat_candidates(self, lines, wanted_name):
        """Return candidate lines for further analysis."""
        ret =  [line
                for line in lines
                if CaseInsStr(line).find(wanted_name) != -1]
        return ret
        
    def _real_lstat(self, path,  _exception_for_missing_path=True):

        path = CaseInsStr(path)
        ret = ftp_stat._Stat._real_lstat(self, path,
                                         _exception_for_missing_path)
        return ret
