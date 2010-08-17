#!/usr/bin/env python


class PendingEvent(yobotclass.YobotEvent):
    depends = [] #another pevt
    def __init__(self, **fields_n_vals):
        """
        Sets up an event to be matched against in the event queue.
        The first argument is the kind of event to wait for (required).
        The fields_n_vals will affect the __eq__ method of this class
        based on how much information the caller wants to specify
        """
        #ensure the key pairs are acceptable for a YobotEvent instance:
        for k in fields_n_vals.keys():
            if not hasattr(self, k):
                raise AttributeError, "Requested %s from Event not found!" % k
        self.required = fields_n_vals
        
    def __eq__(self, other):
        for k, v in self.required.items():
            if getattr(other, k) != v:
                return False
        return True
    
    def encode(self):
        return NotImplemented
    
    def __hash__(self):
        return hash(frozenset(self.required.items()))


class WaitQueue(list):
    """
    A queue allowing multiple dependencies
    """
    depends = []
    children = []
    _open = False
    
    def _getopen(self):
        "Check whether we are cleared for sending"
        if len(self.depends) > 0:
            for dep in self.depends:
                if dep.open is False:
                    return False
                return True
        else:
            return self._open
    
    def _setopen(self, value):
        "Really only suitable for top level events"
        self._open = value
        if self.open:
            self.release()
            self._notifyChildren()
    
    open = property(fget=_getopen, fset=_setopen)        
    
    def _notifyChildren(self):
        """
        Notifies child dependencies that we're open,
        or lets them send out their own queues
        """
        if not self.open:
            return
        for child in self.children:
            child.release()
    
    def send(self, f):
        "Send a message if we're cleared. Otherwise queue"
        if self.open:
            f()
        else:
            self.append(f)
            
    def release(self):
        "Attempt to send queued messages"
        if self.open:
            while len(self):
                self.pop(0)()
    
    def addChild(self, child):
        self.children.append(child)
    
    def addParent(self, dep):
        self.depends.append(dep)

class QueueTable(dict):
    def addQueue(self, pevt, open=False):
        if self.get(pevt, None): return
        
        self[pevt] = WaitQueue()
        for dep in pevt.depends:
            d = self.get(dep, None)
            if not d:
                self.addQueue(dep)
                d = self[dep]
            d.addChild(self[pevt])
            self[pevt].addParent(d)
    
    def getQueue(self, pevt):
        q = self.get(pevt, None)
        if q:
            return q
        else:
            self.addQueue(pevt)
            

