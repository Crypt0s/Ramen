import re
import os
import sys
import loggingclass

INCLUDE = "+"
EXCLUDE = "-"
DONE    = "."

class RsyncGlob(loggingclass.LoggingClass):
    """
    A class that imitates rsync(1)'s way of include/exclude patterns.
    Similar to glob()/fnmatch(), but "*" doesn't match "/" - "**" does.
    See man rsync(1) for the exclude/include logic.
    The GlobChain class creates filter chains like rsync's.

    RsyncGlob(pattern), where <pattern> follows the rules in the rsync(1)
    man page. In particular, "/XYZ" matches only at the "root", and "XYZ/"
    matches only directories.

    NOTE: This class uses Unix file name conventions.
    It will be pretty simple to implement it for DOS/Windows though,
    if someone volunteers. 
    
    The following doctest example shows how the globbing works.
    Note that leading "/" are stripped for files.
    
>>> globs=(RsyncGlob("s*m"),RsyncGlob("s**m"),
...        RsyncGlob("s\*m"),RsyncGlob("/s*m"),
...        RsyncGlob("/s**m"),RsyncGlob("s\**m"))
>>> files=("spam","s/p/a/m","egg/spam","egg/sp/am","s*m","s*am") 
>>> def outh():
...     s="%10.10s" %""
...     for g in globs:
...         s=s+"%10.10s"%g.glob
...     return s
>>> def outf(f):
...     s="%10.10s" %f
...     for g in globs:
...         s=s+"%10.10s"%g.match(f)
...     return s
>>> def out():
...     print outh()
...     for f in files:
...         print outf(f)
>>> out()
                 s*m      s**m      s\*m      /s*m     /s**m     s\**m
      spam      True      True     False      True      True     False
   s/p/a/m     False      True     False     False      True     False
  egg/spam      True      True     False     False     False     False
 egg/sp/am     False      True     False     False     False     False
       s*m      True      True      True      True      True      True
      s*am      True      True     False      True      True      True
    """

    # This is applied before escaping re metachars
    __bksl_re = re.compile(r'(\\.)')

    # These are applied after escaping re metachars
    __star2_re = re.compile(r'(\\\*\\\*)')  # "**"
    __star_re = re.compile(r'(\\\*)')       # "*"
    __quest_re = re.compile(r'(\\\?)')      # "?"
    __slash_re = re.compile(r'/')           # "/"

    def __handle_stars(self, s):
        parts = self.__star2_re.split(s)

        # side effect: patterns containing "**" match complete path
        self.path_match = self.path_match or (len(parts) > 1)

        # Odd elements are '**' now.
        # Even elements must be checked for '*' and '?'  
        res = ""
        i = 0
        while i < len(parts):
            if parts[i] != "":
                tmp = self.__star_re.sub("[^/]*", parts[i])
                tmp = self.__quest_re.sub("[^/]", tmp)
                res = res + tmp
            if i < len(parts) - 1:
                res = res + ".*"
            i = i + 2
        return res


    def __init__(self, pat=""):
        
        self.type = None
        
        # patterns starting with +/-.
        if len(pat) > 1:
            if pat[:2] == "+ ":
                self.type = INCLUDE
                pat = pat[2:]
            elif pat[:2] == "- ":
                self.type = EXCLUDE
                pat = pat[2:]

        # patterns ending with "/" match only directories
        if len(pat) > 0 and pat.endswith("/"):
            self.dir_match = True
            pat = pat[:-1]
        else:
            self.dir_match = False
        
        self.glob = pat

        # patterns containing "/" match entire path,
        self.path_match = (pat.find("/") != -1)

        # patterns starting with "/" match only at root
        if len(pat) > 0 and pat[0] == "/":
            pat = pat[1:]
            top_match = True
        else:
            top_match = False

        # We transform the glob pattern into a regexp pattern now.
        # First, handle all characters escaped with backslashes.
        parts = self.__bksl_re.split(pat)
        
        i = 0
        self.pat = ""

        # Odd elements of parts are an escaped chars now.
        # Need to look for glob patterns in even elements.
        while i < len(parts):
            if parts[i] != "":
                # escape any remaining regexp metacharacters like "."
                s = re.escape(parts[i])
                # sort out "**" and "*"
                s = self.__handle_stars(s)
                self.pat = self.pat + s
            # Add back the escaped chars
            if (i < len(parts) - 1):
                self.pat = self.pat + parts[i+1]
            i = i+2

        self.pat = self.pat + "$"
        if top_match:
            self.pat = "^" + self.pat
        # Special case: '**/' matches empty string
        elif self.pat[:4] == r".*\/":
            self.pat = "(.*/|)" + self.pat[4:]

        self.logger.debug("regexp: %s -> (%s)" % (self, self.pat))
        self.re = re.compile(self.pat)


    def __str__(self):
        s = self.glob
        if self.dir_match: s = s + "/"

        if self.type:
            t = self.type
        else:
            t = " "
        if self.path_match:
            p="p"
        else:
            p=" "
        return "(%s)[%s%s]" % (s, t, p)


    def match(self, filename):

        if len(filename) > 0 and filename.endswith("/"):
            filename = filename [:-1]
        elif self.dir_match:
            return False

        if self.path_match:
            ret = self.re.search(filename) is not None
        else:
            ret = self.re.match(os.path.basename(filename)) is not None

        if ret:
            self.logger.debug("%s matches %s" % (filename, self))
        return ret


class GlobChain(loggingclass.LoggingClass):
    """
    A class that represents a chain of RsyncGlob filter rules.
    Filter rules are applied in order. The recurse() function can
    be used to filter directories recursively.

    doctest example:

>>> loggingclass.init_logging(level=loggingclass.DEBUG,
...     format="%(name)s[%(lineno)d]: %(message)s",
...     stream=sys.stdout)
>>>
>>> ch = GlobChain()
>>> ch.set_log_level(loggingclass.DEBUG)
>>>
>>> ch.exclude("+ spam/", "- /*/", "+ egg/", "- */", "+ \*", "- *")
GlobChain[251]: added rule: (spam/)[+ ]
GlobChain[251]: added rule: (/*/)[-p]
GlobChain[251]: added rule: (egg/)[+ ]
GlobChain[251]: added rule: (*/)[- ]
GlobChain[251]: added rule: (\*)[+ ]
GlobChain[251]: added rule: (*)[- ]
>>> for x in ("spam", "spam/", "egg",
...            "egg/", "*", "spam/egg",
...             "spam/egg/", "spam/*/egg", "spam/egg/*"):
...     xx = ch.match(x)
GlobChain[279]: exclude spam
GlobChain[279]: include spam/
GlobChain[279]: exclude egg
GlobChain[279]: exclude egg/
GlobChain[279]: include *
GlobChain[279]: exclude spam/egg
GlobChain[279]: include spam/egg/
GlobChain[279]: exclude spam/*/egg
GlobChain[279]: include spam/egg/*
    """

    __end_re = re.compile(r"/+$")

    def __init__(self):
        
        self._lst = []
 
    def _in_ex(self, x):
        if x == INCLUDE:
            return "include"
        elif x == EXCLUDE:
            return "exclude"
        else:
            return None
        
    def add(self, type, *args):
        """
        add(type, *args): add (a) new INCLUDE/EXCLUDE pattern rule(s).
        <type> is either INCLUDE or EXCLUDE, or the patterns must
        start with "+" or "-".
        +/- start character has precedence over <type>.
        """
        for x in args:
            # "!" resets the rule chain (why?)
            if (x == "!"):
                l = []
            else:    
                glb = RsyncGlob(x)
                if (glb.type == None):
                    if (type == None):
                        raise ValueError, "filter type is undefined for %s" % glb
                    else:
                        glb.type = type
                self.logger.info("added rule: %s" % glb)
                self._lst.append(glb)

    def exclude(self, *args):
        """
        exclude(*args): add (a) new EXCLUDE pattern rule(s)
        """
        self.add(EXCLUDE, *args)

    def include(self, *args):
        """
        include(*args): add (a) new INCLUDE pattern rule(s)
        """
        self.add(INCLUDE, *args)

    def match(self, path):
        """match(path): returns the result of the current filter chain for path.
        The rule chain is traversed until the first rule matches.
        If path is a directory, it should end in "/".
        """

        # Default is always INCLUDE
        ret = INCLUDE
        for glb in self._lst:
            if glb.match(path):
                ret = glb.type
                break

        self.logger.debug("%s %s" % (self._in_ex(ret), path))
        return ret

    def _recurse(self, top, dir, collector, *args):
    
        for f in os.listdir(os.path.join(top, dir)):
            rel = os.path.join(dir, f)
            isdir = os.path.isdir(os.path.join(top, rel))

            pat = rel
            if (isdir):
                pat = pat + "/"

            c = self.match(pat)

            collector(c, pat, *args)
            if c == EXCLUDE:
                continue

            if isdir:
                self._recurse(top, rel, collector, *args)

    def collect(self, c, x, *args):
        """
        Default collector function to use with recurse().
        """
        l = args[0]
        if c == INCLUDE:
            l.append(x)
        elif c == DONE:
            return l

    def recurse(self, dir, collector = None, *args):
        """
        recurse(self, dir, collector = None, *args)
        recursively descend <dir>. For each file or directory found,
        <collector> is called with arguments (c, x, *args), where
        <c> is the result of the test chain (or DONE when finished),
        <x> is the current path, and <*args> is the rest of the arguments
        of recurse().

        Directories for which the chain evaluates to EXCLUDE are never entered.
        
        When c == DONE, <collector> should return its final result. This will
        be the return value of recurse().

        If <collector> isn't set, a default collector function is used that
        returns a list of all files below <dir> for which c == INCLUDE.
        """

        if collector == None:
            collector = self.collect
            args = ([],)

        dir = self.__end_re.sub("", dir)
        if not os.path.isdir(dir):
            raise IOError, "%s is not a directory" % dir

        self._recurse(dir, "", collector, *args)
        ret = collector(DONE, None, *args)
        return ret

    def add_file(self, type, name):
        """
        add_file(type, name):
        Add a list of INCLUDE/EXCLUDE filter rules from a file.
        Used to implement --exclude-from, --include-from.
        """
        try:
            if name == "-":
                f = sys.stdin
            else:
                f = open(name, "r")

            for line in f.readlines():
                if line.endswith("\n"):
                    line = line[:-1]
                self.add(type, line)
        finally:
            if name != "-":
                f.close()

    _known_options = ("exclude=", "include=",
                      "exclude-from=", "include-from=")

    def options(self):
        return self._known_options
    
    def getopt(self, options):
        """
        getopt(options): parse getopt-style option pairs for filter rules.
        Parses all options "--exclude=", "--include=", "--exclude-from=",
        "--include-from=", leaving other options untouched.
        See rsync(1) for the option semantics.
        """
        hits = []
        for i in range(0, len(options)):
            (name, val) = options[i]
            hit = True
            if name == "--exclude":
                self.exclude(val)
            elif name == "--include":    
                self.include(val)
            elif name == "--exclude-from":
                self.add_file(EXCLUDE, val)
            elif name == "--include-from":
                self.add_file(INCLUDE, val)
            else:
                hit = False
            if hit:
                hits.append(i)

        hits.reverse()
        for i in hits:
            del options[i]
            

def print_matches():
    """
    Usage: rsyncmatch.py [--debug] [filter rules...] directory ... 

    Print list of files below <directory> that match the given rules.
    Rules are specified with "--exclude=", "--include=", "--exclude-from=",
    "--include-from=", see rsync(1) for rule semantics.
    """

    import getopt
    import logging

    loggingclass.init_logging()

    
    gl = GlobChain()
    (options, args) = getopt.gnu_getopt(sys.argv[1:], "",
                                        (gl._known_options) + ("debug",))
    gl.getopt(options)
    for x in options:
        if x[0] == "--debug":
            GlobChain().set_log_level(loggingclass.DEBUG)
            RsyncGlob().set_log_level(loggingclass.DEBUG)

    for dir in args:
        ls = gl.recurse(dir)
    
        print "List of include files below %s:" % dir
        for x in ls:
            print "   " + x


def _test():
    import doctest, rsyncmatch
    doctest.testmod(rsyncmatch)

if __name__ == "__main__":
    if sys.argv[1] == "--test":
        sys.argv = sys.argv[1:]
        _test()
    else:    
        print_matches()
