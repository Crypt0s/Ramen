from logging import *
import sys

NOTICE = (INFO+WARNING)/2
_default_level = NOTICE
_default_format = "%(filename)s:%(name)s[%(lineno)d]: %(message)s"

def set_default_level(level):
    """
    Set the default log level for classes for which set_class_level()
    or instance.set_log_level() was never called.
    Default: NOTICE.
    Call early - only affects class loggers created after the call.
    """
    global _default_level
    _default_level = level

def _class_logger(cls):
    nm ="_" + cls.__name__ + "__logger"
    try:
        lg = getattr(cls, nm)
    except AttributeError:
        lg = getLogger(cls.__name__)
        lg.setLevel(_default_level)
        setattr(cls, nm, lg)
    return lg

def set_class_level(cls, level):
    """
    Set the log level for this class.
    level: one of the levels defined in the logging module.
    Side effects: Sets the log level for _any object_ of this class.
    """
    lg = _class_logger(cls)
    lg.setLevel(level)

class LoggingClass:

    """
    A base class for classes using for easy use of the "logging" module.

    Instances of derived classes have a "logger" attribute
    that represents a class-specific logging.Logger object.

    The "name" of the class-specific logger will be the class name.
    Log levels etc. can be set on a class-specific basis.

    CAUTION: The "logger" attribute is resolved through __getattr__().
    The "__logger" attribute should work independently of __getattr__().

    Usage (doctest):

>>> class LogTest(LoggingClass):
...     def info(self):
...         self.logger.info("This is an info.")
...     def error(self):
...         self.logger.error("This is an error!")
...
>>> init_logging(level=INFO,
...              format="%(name)s[%(lineno)d]: %(message)s", stream=sys.stdout)
>>> logtest = LogTest()
>>> logtest.info()
>>> logtest.error()
LogTest[5]: This is an error!
>>> LogTest().set_log_level(INFO)
>>> logtest.info()
LogTest[3]: This is an info.

    """

    # We can't simply define a "logger" attribute because we
    # want class-specific loggers.

    # The attribute name is constructed such that self.__logger
    # will work in derived classes.

    def __getattr__(self, attr):
        """
        Resolves the "logger" attribute.
        Call this when redefining __getattr__() in derived classes!
        """
        if attr == "logger":
            return _class_logger(self.__class__)
        raise AttributeError, ("'LoggingClass' object has no attribute '%s'"
                               % attr)

    def set_log_level(self, level):
        """
        Set the log level for this class.
        level: one of the levels defined in the logging module.
        Sets the log level for _any object_ of this class.
        """
        return set_class_level(self.__class__, level)


def init_logging(level=NOTICE, format=_default_format, stream=sys.stderr):
    """Initialize a basic logging setup."""
    
    handler = StreamHandler(stream)
    handler.setFormatter(Formatter(format))
    handler.setLevel(level)

    getLogger().addHandler(handler)

def init_logfile(file, level=INFO, format=_default_format):

    handler = FileHandler(file)
    handler.setFormatter(Formatter(format))
    handler.setLevel(level)
    
    getLogger().addHandler(handler)

def _test():
    import doctest, loggingclass
    doctest.testmod(loggingclass)

if __name__ == "__main__":
    _test()
