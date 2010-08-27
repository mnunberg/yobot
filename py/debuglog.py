#!/usr/bin/env python
import traceback
import os
import sys

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

def init(prefix, title_color=""):
    colorama.init()
    global _prefix
    global _title_color
    _title_color = getattr(colorama.Fore, title_color.upper(), "")
    _prefix = prefix
    
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