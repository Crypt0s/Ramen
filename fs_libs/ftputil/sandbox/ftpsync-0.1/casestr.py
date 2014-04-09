import sys
from types import IntType, StringType

class CaseInsStr(str):
    """
    A reimplementation of the standard string class 'str' which
    behaves in a case insensitive manner.

    See the python library documentation ("String methods") for
    documentation of the methods.

    The case-insensitivity is greedy, i.e. operations between 'str'
    and 'CaseInsStr' objects return 'CaseInsStr' objects.
    All methods inherited from 'str' which would normally return
    'str' objects return 'CaseInsStr', including lower() and upper().

    Use the str() method to convert to a normal, case-sensitive string.

    The string itself is not converted to lower or upper case.
"""

    def cast(self, str):
        """
        Cast a "str" object into a "CaseInsStr" object.
        """
        return CaseInsStr(str)

    def str(self):
        """
        Convert to case-sensitive 'str' object.
        """
        return self.__str__()

    def _lower(self):
        return str.lower(self)

    def __cmp__(self, other):
        """
        "CaseInsStr" objects can be compared with each other or with strings.
        Objects are compared case-insensitively.
        
>>> Spam = CaseInsStr("Spam")
>>> print "egg" < Spam, Spam >= "egg", "egg" < Spam.str(), Spam == "spam"
True True False True
>>> phrase = [CaseInsStr("Eric"), "the", "half", "a", "Bee"]
>>> phrase.sort()
>>> print phrase
['Bee', 'a', 'Eric', 'half', 'the']
        """
        ret = cmp(self._lower() , other.lower())
        return ret

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __lt__(self, other):
        return self.__cmp__(other) == -1

    def __le__(self, other):
        return self.__cmp__(other) != 1

    def __gt__(self, other):
        return self.__cmp__(other) == 1

    def __ge__(self, other):
        return self.__cmp__(other) != -1

    def __getitem__(self, n):
        return CaseInsStr(str.__getitem__(self, n))

    def __getslice__(self, i, j):
        return CaseInsStr(str.__getslice__(self, i, j))

    def __add__(self, other):
        """
>>> # concatenation
>>> print "The "+CaseInsStr("Lovely ")+"Spam" == "the LOVELY spam"
True
"""
        return CaseInsStr(str.__add__(self, other))

    def __radd__(self, other):
        return CaseInsStr(str.__add__(other, self))
 
    def __mul__(self, n):
        """
>>> print 4 * CaseInsStr("Spam!") +  CaseInsStr("Egg!") * 3
Spam!Spam!Spam!Spam!Egg!Egg!Egg!
"""
        return CaseInsStr(str.__mul__(self, n))
        
    def __rmul__(self, n):
        return CaseInsStr(str.__rmul__(self, n))

    def center(self, width):
        return CaseInsStr(str.center(self, width))
        
    def count(self, sub, *args, **kwargs):
        """
>>> print CaseInsStr(4*"SPAM!").count("spam")
4
"""
        return self._lower().count(sub.lower(), *args, **kwargs)
    
    def find(self, other):
        """
>>> Love = CaseInsStr("The Lovely Spam")
>>> print Love.find("spam"), Love.rfind("love"), Love.index("ELY")
11 4 7
"""
        return self._lower().find(other.lower())

    def index(self, other):
        return self._lower().index(other.lower())

    def join(self, seq):
        """
>>> print CaseInsStr("!").join(["spam", "Spam", "SPAM"])
spam!Spam!SPAM
>>> print CaseInsStr("!").join(["spam", "Spam", "SPAM"]).find("SPAM")
0
"""
        return CaseInsStr(str.join(self, seq))
        
    def ljust(self, width):
        return CaseInsStr(str.ljust(self, width))

    def replace(self, old, new, count=None):
        """
>>> # replace
>>> print CaseInsStr(4*"EGG!").replace("egg", "Spam", 3)
Spam!Spam!Spam!EGG!
"""
        if count is not None and (type(count) != IntType or count < 0):
            raise ValueError, count
        old = old.lower()
        lwr = self._lower()
        n = 0
        idx = 0
        ret = ""
        
        while True:
            i = lwr[idx:].find(old)
            if i == -1 or (count is not None and n >= count):
                break
            ret = ret + str.__getslice__(self, idx, idx+i) + new
            n = n + 1
            idx = idx + i + len(old)

        ret = ret + str.__getslice__(self, idx, sys.maxint)
        return CaseInsStr(ret)

    def startswith(self, other):
        return self._lower().startswith(other.lower())

    def endswith(self, other):
        return self._lower().endswith(other.lower())

    def rfind(self, other):
        return self._lower().rfind(other.lower())

    def rindex(self, other):
        return self._lower().rindex(other.lower())

    def rjust(self, width):
        return CaseInsStr(str.rjust(self, width))

    def split(self, sep=None, maxsplit=0):
        """
>>> print CaseInsStr("Fiddle de dum, fiddle de dee").split("DE", 2)
['Fiddle ', ' dum, fiddle ', ' dee']
"""
        if sep is None:
            return self.__str__().split(sep, maxsplit)

        if type(maxsplit) != IntType:
            raise TypeError, maxsplit
        if maxsplit < 0:
            raise ValueError, maxsplit

        ret = []
        last = 0
        while True:
            i = self[last:].find(sep)
            if i == -1 or (maxsplit > 0 and len(ret) == maxsplit):
                break
            ret = ret + [self[last:last+i]]
            last = last + i + len(sep)
        
        ret = ret + [self[last:]]
        return ret

    def rsplit(self, sep=None, maxsplit=0):
        """
>>> print CaseInsStr("spam and eggs AND bees And knights").rsplit("and", 2)
['spam and eggs ', ' bees ', ' knights']
"""
        if sep is None:
            return self.__str__().rsplit(sep, maxsplit)

        if type(maxsplit) != IntType:
            raise TypeError, maxsplit
        if maxsplit < 0:
            raise ValueError, maxsplit

        ret = []
        last = sys.maxint
        while True:
            i = self[:last].rfind(sep)
            if i == -1 or (maxsplit > 0 and len(ret) == maxsplit):
                break
            ret = [self[i+len(sep):last]] + ret
            last = i
        
        ret = [self[:last]] + ret
        return ret

    def splitlines(self, keepends=None):
        return [CaseInsStr(x)
                for x in str.splitlines(self, keepends)]

    def _stripchars(self, ch):
        if type(ch) is not StringType:
            raise TypeError, ch
        s = ""
        for x in ch:
            if x.isalpha():
                u = x.upper()
                l = x.lower()
                if l != u:
                    s = s + l + u
                    continue
            s = s + x
        return s

    def strip(self, *chars):
        """
        Stripped characters are case-insensitive:
>>> print CaseInsStr(" Spam and eggs ").strip("s ")
pam and egg
>>> print "'%s'" % CaseInsStr("  a  ").lstrip()
'a  '
"""
        if chars is () or chars[0] is None:
            return CaseInsStr(str.strip(self))
        else:
            return CaseInsStr(str.strip(self, self._stripchars(chars[0])))

    def lstrip(self, *chars):
        if chars is () or chars[0] is None:
            return CaseInsStr(str.lstrip(self))
        else:
            return CaseInsStr(str.lstrip(self, self._stripchars(chars[0])))

    def rstrip(self, *chars):
        if chars is () or chars[0] is None:
            return CaseInsStr(str.rstrip(self))
        else:
            return CaseInsStr(str.rstrip(self, self._stripchars(chars[0])))

    def swapcase(self):
        return CaseInsStr(str.swapcase(self))

    def title(self):
        return CaseInsStr(str.title(self))
    
    def translate(self):
        raise NotImplementedError, "translate() method not implemented"

    def lower(self):
        """
>>> Spam = CaseInsStr("Spam")
>>> print Spam.lower(), Spam.upper(), Spam.lower() == "SPAM", Spam.upper() == "spam"
spam SPAM True True
"""
        return CaseInsStr(self._lower())

    def upper(self):
        return CaseInsStr(self.__str__().upper())
    
    def zfill(self, width):
        return CaseInsStr(str.zfill(self, width))

def _test():
    import doctest, casestr
    doctest.testmod(casestr)

if __name__ == "__main__":
    _test()
