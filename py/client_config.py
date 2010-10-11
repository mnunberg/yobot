#!/usr/bin/env python

config = None

import yobot_interfaces
import sys
import yobotops
from debuglog import log_debug, log_err, log_warn, log_crit, log_info


try:
    import json
except Exception, e:
    log_debug("Couldn't load json module: ", str(e))
    import simplejson
    json = simplejson
    
class ConfigLoadError(Exception): pass
class ConfigSaveError(Exception): pass

class acctlist(list):
    def append(self, obj):
        for a in self:
            if a["name"] == obj["name"] and a["improto"] == obj["improto"]:
                return
        list.append(self, obj)

class RingBuffer(list):
    def __init__(self, limit, l=list()):
        list.__init__(self, l)
        if limit < len(l): limit = len(l)
        self.limit = limit
        
    def append(self, obj):
        if not obj in self:
            if len(self) >= self.limit:
                self.pop(0)
            list.append(self,obj)
        else:
            i = self.index(obj)
            o = self.pop(i)
            list.append(self, o)
        
        
class ClientConfig(object):
    indent = 2
    def __init__(self, filename, autocreate = False):
        self.load(filename, autocreate)
        self.account_lookup_cache = {}
        self.do_autoconnect = False
    
    def load(self, filename, autocreate=False):
        self.filename = filename
        try:
            self._configroot = json.load(open(filename, "r"))
        except Exception, e:
            print "Couldn't load", self.filename
            if not autocreate:
                raise ConfigLoadError, str(e)
            else:
                print "Creating dummy config"
                self._configroot = {"_name":"yobot_config"}
        
        if not self.check_signature(self._configroot):
            raise ConfigLoadError, "Signature checking failed! need _name field in config root"
        
        self.globals = self._configroot.setdefault("globals", {})
        self.accounts = acctlist(self._configroot.setdefault("accounts", []))
        self._configroot["accounts"]=self.accounts
        
        if len(self.accounts):
            for a in self.accounts:
                if not hasattr(a, "__getitem__") or not hasattr(a, "__setitem__"):
                    raise ConfigLoadError, "Error parsing accounts! __get/setitem__ not supported"
                if not a.get("name", None) or not a.get("improto", None):
                    raise ConfigLoadError, "Missing values: name: %s improto %s" % (a.get("name", "<name>"), a.get("improto", "<proto>"))                
                
                #if someone knows a better, quicker way to do this, let me know
                if a.get("recent_contacts", []):
                    a["recent_contacts"] = RingBuffer(25, a["recent_contacts"][:])
                if a.get("recent_chats", []):
                    a["recent_chats"] = RingBuffer(25, a["recent_chats"][:])
    
    def get_account(self, acctobj, autoadd=False):
        """Return a config entry with the improto and name of this account object"""
        #first try the cache..
        try:
            ret = self.account_lookup_cache[acctobj]
            log_err(ret)
            return ret
        except KeyError, e:
            log_debug("account not in cache yet..", self.account_lookup_cache, e)
        for a in self.accounts:
            if a["name"] == acctobj.name and a["improto"] == yobotops.imprototostr(acctobj.improto):
                self.account_lookup_cache[acctobj] = a
                log_debug("added account %s to cache, calling again", a)
                return self.get_account(acctobj, autoadd)
        if autoadd:
            d = {"name":acctobj.name,
                 "improto":yobotops.imprototostr(acctobj.improto),
                 "password":"",
                 "autoconnect": False
            }
            self.accounts.append(d)
            self.account_lookup_cache[acctobj] = d
            return self.get_account(acctobj, autoadd=False)
            
        else:
            return {}
            
    def save(self, fatalerror=False):
        if self.globals.get("read_only", False):
            print "WARNING! read only requested, not saving"
            return False
        try:
            json.dump(self._configroot, open(self.filename, "w"), indent=self.indent)
        except Exception, e:
            if fatalerror:
                raise ConfigSaveError, str(e)
            else:
                print "Problem saving!", str(e)

    def check_signature(self, object):
        if not hasattr(object, "get"):
            return False
        _name = object.get("_name", False)
        if not _name:
            return False
        if not _name == "yobot_config":
            return False
        return True

if __name__ == "__main__":
    #ringbuffer test
    b = RingBuffer(20)
    for i in xrange(25):
        b.append(i)
    print b
