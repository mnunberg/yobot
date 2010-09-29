#!/usr/bin/env python
import traceback
import os
import sys
import atexit

class _BlackHole(str):
    def __init__(self, *args, **kwargs):
        pass
    def __getattr__(self, name):
        return _BlackHole()
    def __setattr__(self, name, value):
        pass
    def __call__(self, *args, **kwargs):
        pass
    def __bool__(self):
        return False
    def __str__(self):
        return ""

class _LogMessage(object):
    title = ""
    body = ""
    def fmt_title(self, fmt):
        self.title = fmt + self.title + _TERM_RESET
    def fmt_body(self, fmt):
        self.body = fmt + self.body + _TERM_RESET
    
    def __str__(self):
        return "[%s]: %s" % (self.title, self.body)
try:
    assert sys.stdout.isatty()
    import colorama
except (ImportError, AssertionError),  e:
    print e, "warning.. fancy display will not be available"
    colorama = _BlackHole()

_prefix = ""
_title_color = ""
_TERM_RESET = str(colorama.Fore.RESET) + str(colorama.Back.RESET) + str(colorama.Style.RESET_ALL)

_stdout, _stderr = None, None

def init(prefix, title_color=""):
    global _prefix
    global _title_color
    global colorama
    global _TERM_RESET
    global _stdout
    global _stderr
    _stdout, _stderr = sys.stdout, sys.stderr
    
    try:
        print "initializing colorama"
        #on wine, colorama fails to work properly..
        colorama.init()
        log_debug("This is a debug message")
        log_info("This is an informational message")
        log_warn("This is a warning message")
        log_err("This is an error message")
        log_crit("This is a critical message")
        if not isinstance(colorama, _BlackHole):
            atexit.register(colorama.reset_all)
    except Exception, e:
        #reset stdout and stderr
        sys.stdout, sys.stderr = _stdout, _stderr
        colorama = _BlackHole()
        print "colorama failed! [%s]" % (str(e),)
        #_stdout.flush()
        _TERM_RESET = str(colorama.Fore.RESET) + str(colorama.Back.RESET) + str(colorama.Style.RESET_ALL)
    _prefix = prefix
    _title_color = getattr(colorama.Fore, title_color.upper(), "")
    
def setprefix(prefix):
    global _prefix
    _prefix = prefix
    
def _logwrap(*args):
    lm = _getbt(*args)
    lm.fmt_title(_title_color)
    return lm

def log_debug(*args):
    lm = _getbt(*args)
    lm.fmt_title(_title_color)
    lm.fmt_body(colorama.Style.DIM)
    print lm
    
def log_err(*args):
    lm = _getbt(*args)
    lm.fmt_body(colorama.Style.BRIGHT + colorama.Fore.RED)
    lm.fmt_title(_title_color)
    print lm
log_crit = log_err

def log_warn(*args):
    lm = _getbt(*args)
    lm.fmt_body(colorama.Style.DIM + colorama.Fore.YELLOW)
    lm.fmt_title(_title_color)
    print lm

def log_info(*args):
    lm = _getbt(*args)
    lm.fmt_title(_title_color)
    print lm


def change_output(fobj):
    if not (hasattr(fobj, "write") and hasattr(fobj, "flush")):
        print "fobj needs both write and flush methods! refusing to change"
        return False
    sys.stdout = sys.stderr = fobj
    return True

def _getbt(*args):
    #get traceback object..
    tb = traceback.extract_stack(limit=3)
    #print tb
    tb = tb[0]
    mname, lineno, fname, _ = tb
    mname = os.path.basename(mname)
    msg = " ".join([str(o) for o in args])
    msg = "%s:%d (%s): %s"  % (mname, lineno, fname, msg)
    tmp = _LogMessage()
    tmp.title = _prefix
    tmp.body = msg
    return tmp

if __name__ == "__main__":
    print "calling init"
    init("debug-debug", "red")
    log_info("hi")
    sys.stdout.flush()
    sys.exit(0)
