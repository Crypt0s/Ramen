import getopt
import netrc   # for password retrieval from .netrc
import os
import sys
import termios # for getpass
import time
import traceback

import loggingclass

from caching_ftp import CachingFTPHost
from rsyncmatch import GlobChain
from sync import Synchronizer, RsyncSynchronizer

# Copied from Python library manual (termios)
def getpass(prompt = "Password: "):
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~termios.ECHO          # lflags
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        passwd = raw_input(prompt)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return passwd


def login_data(host):
    """
    Derive login data for different FTP host formats:
    
    "hostname": check .netrc file, try anonymous otherwise
    "user:pass@hostname": parse
    "user@hostname": parse and ask for password interactively
    """

    user = ""
    acct = ""
    passwd = ""

    at = host.find("@")
    if (at == -1):
        try:
            nrc = netrc.netrc()
            (user, acct, passwd) = \
                   nrc.authenticators(host)
        except (IOError, TypeError): # no netrc file or no entry in netrc
            pass
    else:
        user = host[:at]
        host = host[(at+1):]
        col = user.find(":")
        if (col == -1):
            passwd = getpass("password for ftp://%s%s: " % (user, host))
        else:
            passwd = user[(col+1):]
            user = user[:col]

    if (user == ""):
        user = "anonymous"
            
    return (host, user, passwd, acct)

def init_ftp(host, dir, **kw):
    """
    Set up an FTP session for synchronizing (upload).
    We must have write permissions in this case.
    """
    data = login_data(host)
    ftp = CachingFTPHost(*data, **kw)
    ftp.chdir(dir)
    ftp.synchronize_times()
    ftp.check_case_insensitive()
    return ftp


def start_logging(level, logfile):
    """
    Initialize a useful logging environment with logging to stderr,
    slightly more verbose to a log file, and suitable log levels.
    """
    loggingclass.init_logging(level)
    
    if level == loggingclass.DEBUG:
#        loggingclass.getLogger().setLevel(loggingclass.DEBUG)
        loggingclass.set_default_level(loggingclass.INFO)
        if logfile != "":
            loggingclass.init_logfile(logfile, level=loggingclass.DEBUG)
        loggingclass.set_class_level(RsyncSynchronizer, loggingclass.DEBUG)
        loggingclass.set_class_level(GlobChain, loggingclass.DEBUG)
        loggingclass.set_class_level(CachingFTPHost, loggingclass.INFO)
    else:
        if logfile != "":
            loggingclass.init_logfile(logfile, level=loggingclass.INFO)
        loggingclass.set_class_level(RsyncSynchronizer, loggingclass.INFO)
        loggingclass.set_class_level(CachingFTPHost, loggingclass.INFO)

def print_err():
    err = sys.exc_info()
    printit = True
    try:
        if parm.level != loggingclass.DEBUG:
            printit = False
    except:
        pass
    if printit:
        traceback.print_tb(err[2])
    sys.stderr.write("%s: %s\n" % (err[0], err[1]))

class _Params:
    """
    Class representing options and arguments for do_sync().
    """

    class UsageError(Exception):
        pass
    
    known = (list(GlobChain().options())
             + ["delete", "delete-excluded", "dry-run",
                "verbose", "quiet", "debug", "trace=",
                "cache-expire=", "cache-size="])

    def usage(self):
        sys.stderr.write("""\
Usage: %s [options] host source-dir target-dir
Known options: %s
""" % (sys.argv[0], ", ".join(["--" + x for x in self.known])))
        raise self.UsageError()

    def _setlevel(self, level, option=True):
        if self.level == -1:
            self.level = level
        elif option:
            sys.stderr.write("Only one of --quiet, --debug, --verbose may be specified\n")
            self.usage()

    def __init__(self):
        self.level = -1 
        self.dry_run = False
        self.delete = False
        self.delete_excluded = False
        self.logfile = ""
        self.expire = 300
        self.size = 2000
        
        try:
            (opts, args) = getopt.gnu_getopt(sys.argv[1:], "", self.known)
        except getopt.GetoptError:
            print_err()
            self.usage()

        for (o, v) in opts:
            if o == "--delete":
                self.delete = True
            elif o == "--delete-excluded":
                self.delete_excluded = True
            elif o == "--dry-run":
                self.dry_run = True
            elif o == "--verbose":
                self._setlevel(loggingclass.INFO)
            elif o == "--debug":
                self._setlevel(loggingclass.DEBUG)
            elif o == "--quiet":
                self._setlevel(loggingclass.WARNING)
            elif o == "--trace":
                self.logfile=v
            elif o == "--cache-expire":
                self.expire = int(v)
            elif o == "--cache-size":
                self.size = int(v)

        self._setlevel(loggingclass.NOTICE, option=False)
        if len(args) != 3:
            self.usage()
            
        (self.host, self.source, self.target) = args
        self.opts = opts


def _fix_source_n_target(parm):
    # rsync-like semantics for trailing slash in source dir
    if not os.path.isdir(parm.source):
        raise ValueError, "%s is not a directrory" % parm.source
    
    if parm.source.endswith(os.sep):
        parm.source = parm.source.rstrip(os.sep)
    else:
        parm.target = parm.ftp.path.join(parm.target,
                                         os.path.basename(parm.source))
        if not parm.ftp.path.exists(parm.target):
            parm.ftp.mkdir(parm.target)

def log_checkpoint(msg):
    loggingclass.getLogger().info(
        "%s %s %s" % (__file__, msg,
                      time.strftime("%Y-%m-%d, %H:%M", time.localtime())))
    
def do_sync(parm):
    
    start_logging(parm.level, parm.logfile)
    log_checkpoint("starting at")

    if parm.host == "localhost":
        parm.ftp = os
    else:
        parm.ftp = init_ftp(parm.host, parm.target,
                            expire=parm.expire, size=parm.size)

    _fix_source_n_target(parm)

    sync = RsyncSynchronizer(os, parm.ftp, parm.source, parm.target,
                             delete = parm.delete,
                             dry_run = parm.dry_run,
                             delete_excluded = parm.delete_excluded)
    
    sync.globchain.getopt(parm.opts)
    sync.sync("")
    
    log_checkpoint("finished at")

if __name__ == "__main__":
    try:
        parm = _Params()
        do_sync(parm)
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted.\n")
        sys.exit(0)
    except _Params.UsageError:
        sys.exit(129)
    except:
        print_err()
        sys.exit(130)
    else:
        sys.exit(0)
