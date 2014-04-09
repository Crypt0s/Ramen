import os
import sys
from loggingclass import LoggingClass, NOTICE
from rsyncmatch import GlobChain, EXCLUDE

class Synchronizer(LoggingClass):
    """
    A class for synchronizing directories between two file systems.

    Usage example:
    sync = Synchronizer(os, os, "/source", "/target")
    sync.sync("subdir")

    This will synchronize "/source/subdir" to "/target/subdir".
    """

    class SyncAction:
        """
        This "class" stores actions to be carried out.
        """
        def __init__(self):
            self.unl = []   # stuff to unlink
            self.cpy = []   # stuff to copy
            self.rmd = []   # stuff to rmdir
            self.mkd = []   # stuff to mkdir
            self.dsc = []   # dirs to descend into

    class FileSys:
        """
        A helper class for Synchronizer. Another abstraction layer above
        'os' and other filesystem access (e.g. FTP).
        
        It inherits most attributes from it's '_io' element (typically 'os').
        """

        def __init__(self, io, root):
            self._io = io
            self.root = root

        def open(self, *args):
            """
            Open a file on the file system.
            """
            if self._io == os:
                return open(*args)
            else:
                return self._io.open(*args)

        def eq(self, x, y):
            """
            Boolean: True if file names x and y are equal by this file
            system's rules. This refers mainly to case-sensitiveness.
            """
            ret = (self._io.path.normcase(x) == self._io.path.normcase(y))
            return ret

        def cmp(self, x, y):
            """
            Compare file names by this file system's rules.
            """
            ret = cmp(self._io.path.normcase(x), self._io.path.normcase(y))
            return ret

        def __getattr__(self, attr):
            return getattr(self._io, attr)


    def __init__(self, io_s, io_t, root_s, root_t, 
                 mode = "b", blocksize = 65536,
                 delete=False, delete_excluded=False,
                 dry_run=False):
        """
        io_s, io_t: "IO class" of the source and target, respectively.
           typically 'os' or an ftputil.FTPHost
        root_s, root_t: root directories for synchronization on source
           and target, respectively.
        mode: file open() mode (usually 'b')
        blocksize: block size for copying (default: 64kB)
        delete: whether to delete additional files on target (default: false)
        delete_excluded: whether to delete files which were excluded, similar
           to rsync's --delete-exluded option. See exclude() method.
        dry_run: whether anything should actually be done on the target.
        """

        self.io_s = self.FileSys(io_s, root_s)
        self.io_t = self.FileSys(io_t, root_t)
        self.mode = mode
        self.dry_run = dry_run
        self.blocksize = blocksize
        self.delete = delete
        self.delete_excluded = delete_excluded
        self.logger.info("options: delete=%s, delete-excluded=%s, dry-run=%s"
                         % (self.delete, self.delete_excluded, self.dry_run))
        return

    def _rm_rf(self, path):
        err = False
        for f in self.io_t.listdir(path):
            absl = self.io_t.path.join(path, f)
            if self.isdir(self.io_t, absl):
                try:
                    self._rm_rf(absl)
                except OSError:
                    self.logger.exception("rmdir %s" % absl)
                    err = sys.exc_info()[:2]
            else:
                self.logger.debug("delete %s" % absl)
                try:
                    if not self.dry_run:
                        self.io_t.unlink(absl)
                except OSError:
                    self.logger.exception("delete %s" % absl)
                    err = sys.exc_info()[:2]
        self.logger.debug("rmdir %s" % path)
        if not self.dry_run:
            self.io_t.rmdir(path)
        if err:
            raise err[0], err[1]
        
    def rm_rf(self, path):
        """
        Remove directory recursively.
        """
        absl=self.io_t.path.abspath(path)
        self._rm_rf(absl)

    def _pull(self, x, lst, eq):
        """
        x: file name
        lst: list of file names
        eq: function to check file name equality
        returns: true if file was matched
        side effects: removes all matching entries from lst
        """
        oldlen = len(lst)
        i = 0
        while i < len(lst):
            if eq(x, lst[i]):
                found = True
                del lst[i]
            i = i + 1
        return (len(lst) < oldlen)

    def exclude(self, dir, name, isdir):
        """
        (virtual): this implementation returns always False.
        dir: parent directory
        name: file name
        isdir: True iff name represents a directory itself
        returns: True if file is to be excluded.
        """
        return False

    def need_copy(self, src, tgt):
        """
        src, tgt: corresponding files on source and target
        returns: a "reason string" if src needs to be copied to tgt.
                 the emtpy string otherwise.
        This default implementation returns non-"" if the file
        sizes differ ("size"), or if src is newer than tgt ("date").
        """
        ret = ""
        stat_s = self.io_s.stat(src)
        stat_t = self.io_t.stat(tgt)
        if stat_s.st_size != stat_t.st_size:
            ret = "size"
            self.logger.debug("%s: sizes differ: %d %d" %
                              (tgt, stat_s.st_size, stat_t.st_size))
        elif (stat_s.st_mtime - stat_t.st_mtime > 0):
            ret = "date"
            self.logger.debug("%s: source is newer by %s s" %
                              (tgt, stat_s.st_mtime - stat_t.st_mtime))
        return ret
    
    def _make_pattern(self, path, isdir):
        if isdir:
            path = path + "/"
        return path

    def isdir(self, io, path):
        return io.path.isdir(path) and not io.path.islink(path)

    def copy(self, abs_s, abs_t):
        try:
            src = self.io_s.open(abs_s, "r" + self.mode)
            tgt = self.io_t.open(abs_t, "w" + self.mode)
            while True:
                buffer = src.read(self.blocksize)
                if not buffer: break
                tgt.write(buffer)
        except(IOError, OSError):
            self.logger.exception("error copying to %s" % abs_t)
            try:
                self.io_s.unlink(abs_t)
            except(IOError, OSError):
                self.logger.exception("error unlinking %s" % abs_t)
                pass

        try:
            src.close()
            tgt.close()
        except:
            pass

    def _unique(self, lst, eq):
        """
        Remove duplicate entries in list lst, using equality relation eq.
        """
        i = 0
        while i < len(lst):
            j = i + 1
            while j < len(lst):
                if eq(lst[i], lst[j]):
                    self.logger.warn("skipping %s (duplicate of %s)"
                                     % (lst[j], lst[i]))
                    del lst[j]
                else:
                    j = j + 1
            i = i + 1

    def sync(self, path, _top=True):
        """
        Main work horse of Synchorinzer class.
        Synchronize directory 'path' between source and target.

        Called recursively. Call with _top = True initially.
        """

        # All action items are recorded in this "todo" list.
        # Actions are only put into effect when the list is
        # complete.
        todo = self.SyncAction()
        # 'reason' is a map that stores the reasons why we transfer
        # files (regular files only). This is just informational.
        reason = {}

        path_s = self.io_s.path.join(self.io_s.root, path)
        path_t = self.io_t.path.join(self.io_t.root, path)

        if _top:
            self.logger.info("sync starting: %s -> %s" % (path_s, path_t))
        else:
            self.logger.debug("sync: %s -> %s" % (path_s, path_t))
        
        lst_s = self.io_s.listdir(path_s)
        try:
            lst_t = self.io_t.listdir(path_t)
        except OSError:
            if self.dry_run:
                lst_t = []
            else:
                raise

        # in case io_s or io_t are case-insensitive, remove duplicate
        # file names.
        self._unique(lst_s, self.io_t.eq)
        self._unique(lst_t, self.io_s.eq)

        for x in lst_s:

            abs_s = self.io_s.path.join(path_s, x)
            isdir_s = self.isdir(self.io_s, abs_s)
            
            if not isdir_s and not self.io_s.path.isfile(abs_s):
                self.logger.info("skipping non-file %s" %  abs_s)
                continue

            # This deletes x from lst_t. That enables us to simply
            # iterate over lst_t later to find files to be deleted.
            exists_t = self._pull(x, lst_t, self.io_t.eq)
            abs_t = self.io_t.path.join(path_t, x)
            if exists_t:
                isdir_t = self.isdir(self.io_t, abs_t)

            if self.exclude(path, x, isdir_s):
                self.logger.debug("exclude src %s/%s" % (path, x))
                if self.delete and self.delete_excluded and exists_t:
                    self.logger.log(NOTICE, "delete excluded %s/%s" % (path, x))
                    if isdir_t:
                        todo.rmd.append(x)
                    else:
                        todo.unl.append(x)
                continue    

            # Here we know: src exists and is not excluded.
            if isdir_s:
                todo.dsc.append(x)
            
            if exists_t:
                if isdir_s:
                    if not isdir_t:
                        todo.unl.append(x)
                        todo.mkd.append(x)
                else:
                    if isdir_t:
                        todo.rmd.append(x)
                        todo.cpy.append(x)
                        reason[x] = "type"
                    else:
                        rsn = self.need_copy(abs_s, abs_t)
                        if rsn:
                            todo.unl.append(x)
                            todo.cpy.append(x)
                            reason[x] = "%s" % rsn
            else:  # not exists_t
                if isdir_s:
                    todo.mkd.append(x)
                else:
                    reason[x] = "new"
                    todo.cpy.append(x)
        # for loop over lst_s ends

        if self.delete:

            # Anything now in lst_t didn't exist in src (see above)
            for x in lst_t:
                
                abs_t = self.io_t.path.join(path_t, x)
                isdir_t = self.isdir(self.io_t, abs_t)
            
                if self.exclude(path, x, isdir_t):
                    self.logger.debug("exclude tgt %s/%s" % (path, x))
                    if not self.delete_excluded:
                        continue
                    
                self.logger.info("delete %s/%s" % (path, x))
                if isdir_t:
                    todo.rmd.append(x)
                else:
                    todo.unl.append(x)

        # From here on ACTIONS ARE CARRIED OUT 
        # First all remove actions, than mkdir and copy
        for x in todo.rmd:
            try:
                self.logger.log(NOTICE, "rm -rf: %s/%s" % (path, x))
                self.rm_rf(self.io_t.path.join(path_t, x))
            except (OSError, IOError):
                self.logger.exception("failed to rmdir %s" % x)

        for x in todo.unl:
            try:
                self.logger.log(NOTICE, "delete: %s/%s" % (path, x))
                if not self.dry_run:
                    self.io_t.unlink(self.io_t.path.join(path_t, x))
            except (OSError, IOError):
                self.logger.exception("failed to unlink %s" % x)

        for x in todo.mkd:
            try:
                self.logger.log(NOTICE, "mkdir: %s/%s" % (path, x))
                if not self.dry_run:
                    self.io_t.mkdir(self.io_t.path.join(path_t, x))
            except (OSError, IOError):
                self.logger.exception("failed to mkdir %s" % x)
                self._pull(x, todo.dsc)

        for x in todo.cpy:
            self.logger.log(NOTICE, "copy: %s/%s (reason: %s)"
                 % (path, x, reason[x]))
            if not self.dry_run:
                self.copy(self.io_s.path.join(path_s, x),
                          self.io_s.path.join(path_t, x))

        # Finally, recurse.
        for x in todo.dsc:
            self.sync(self.io_s.path.join(path, x), False)

        if _top:
            self.logger.info("sync finshed: %s -> %s" % (path_s, path_t))

        
class RsyncSynchronizer(Synchronizer):
    """
    Special Synchronzer class that uses rsyncmatch.GlobChain
    for include/exclude logic.
    """
    def __init__(self, *args, **kwargs):
        Synchronizer.__init__(self, *args, **kwargs)
        self.globchain = GlobChain()

    def exclude(self, dir, name, isdir):
        path = self.io_s.path.join(dir, name)
        if isdir:
            path = path + "/"
        
        gl = self.globchain.match(path)
        return gl == EXCLUDE
