#!/usr/bin/env python

config = None

import yobot_interfaces
import sys
import yobotops

try:
    import json
except Exception, e:
    print "Couldn't load json module: ", str(e)
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
        
class ClientConfig(object):
    indent = 2
    def __init__(self, filename, autocreate = False):
        self.load(filename, autocreate)
    
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
    
    def get_account(self, acctobj, autoadd=False):
        """Return a config entry with the improto and name of this account object"""
        for a in self.accounts:
            if a["name"] == acctobj.name and a["improto"] == yobotops.imprototostr(acctobj.improto):
                return a
        if autoadd:
            d = {"name":acctobj.name,
                 "improto":yobotops.imprototostr(acctobj.improto),
                 "password":acctobj.passw
            }
            self.accounts.append(d)
            return d
        else:
            return None
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