#!/usr/bin/env python
from yobotclass import YobotAccount, YobotMessage, YobotCommand
import yobotproto
from yobotops import buddystatustostr
from time import time
from debuglog import log_debug, log_err, log_warn, log_crit, log_info
import lxml.html

class YCRequest(object):
    def _initvars(self):
        self.isError = False
        self.title = ""
        self.primary = ""
        self.secondary = ""
        self.modal = False
        self.acct = None
        self.refid = 0
        self.options = [] #(option name, callback, type hint<constant>)

    def __init__(self, svc=None, evt=None, acct=None):
        self._initvars()
        self.evt = evt
        self.acct = acct
        self.svc = svc
        if evt:
            self._mkopts()
            self.refid = self.evt.reference
        
    def _mkopts(self):
        #use lxml
        evt = self.evt
        xmlstring = lxml.html.fromstring(evt.txt)
        #get the strings...
        self.title = xmlstring.attrib.get("title", "")
        self.primary = xmlstring.attrib.get("primary", "")
        self.secondary = xmlstring.attrib.get("secondary", "")
        for opt in xmlstring.iterchildren():
            optname = opt.attrib.get("text")
            if optname.startswith("_"):
                self.default_option = len(self.options) #current index
                optname = optname.strip("_")
            optret = opt.attrib.get("return")
            typehint = opt.attrib.get("typehint", "")
            optcb = lambda optret=optret: self.callback(optret)
            self.options.append((optname, optcb, typehint))
            
    def callback(self, ret):
        if not self.svc:
            log_warn("service was not specified")
            return
        cmd = YobotCommand()
        cmd.acctid = self.evt.objid
        cmd.cmd = yobotproto.YOBOT_CMD_PURPLE_REQUEST_GENERIC_RESPONSE
        cmd.data = str(ret)
        cmd.reference = self.evt.reference
        self.svc.sendSegment(cmd)
        log_info("send response - %s" % (cmd.reference,))
    def __str__(self):
        return "title: %s, options: %d" % (self.title, len(self.options))
        
class BuddyAuthorize(YCRequest):
    def __init__(self, svc, buddy, acct):
        self._initvars()
        self.acct = acct
        self.svc = svc
        self.title = "Authorization Request"
        self.primary = "Allow %s to add you to his/her list?" % (buddy,)
        self.name = buddy
        self.options.append(("Accept",
                            lambda: self.respond(auth=True),
                            yobotproto.YOBOT_ACTIONTYPE_OK))
        self.options.append(("Reject",
                             lambda: self.respond(auth=False),
                             yobotproto.YOBOT_ACTIONTYPE_CANCEL))
        
    def respond(self, auth=False):
        if auth:
            self.svc.addreqAuthorize(self.acct, self.name)
            self.svc.addUser(self.acct, self.name)
        else:
            self.svc.addreqDeny(self.acct, self.name)

class SimpleNotice(YCRequest):
    def __init__(self, account, txt, refid=0):
        if not txt:
            log_warn("no text")
            txt = ""
        log_debug(txt)
        self.refid = refid
        self._initvars()
        self.acct = account
        self.options.append(("Ok",
                             lambda: None,
                             yobotproto.YOBOT_ACTIONTYPE_OK))
        self._prettyformat(txt)
        
    def _prettyformat(self, txt):
        xmlstring = None
        if txt.strip().startswith("<"):
            xmlstring = lxml.html.fromstring(txt)
        else:
            self.primary = txt
            return
        self.title = xmlstring.attrib.get("title", "")
        self.primary = xmlstring.attrib.get("primary", "")
        self.secondary = xmlstring.attrib.get("secondary", "")
        for c in xmlstring.iterchildren():
            #FIXME: well.. we're throwing away the formatting.. but we don't *have*
            #to is the point..
            if c.tag == "formatted":
                self.secondary + "::" + c.text_content()
            elif c.tag == "entries":
                #parse..
                tmp = c.attrib.get("text", "")
                tmp = tmp.split(yobotproto.YOBOT_TEXT_DELIM)
                for s in tmp:
                    self.secondary += "::" + s + "\n"
        
        
class ModelBase(object):
    def _initvars(self):
        self._t = {}
        self._d = {}
    def __init__(self):
        self._initvars()
    
    def __iter__(self):
        return iter(self._t)
    def __getitem__(self, key):
        return self._t[key]
    def __contains__(self, item):
        return item in self._t
    def __len__(self):
        return len(self._t)
    
    def beginAdd(self, index):
        "Override this"
        log_err("override me")
        raise Exception()
    def endAdd(self):
        "Override this"
        log_err("Override me!")
        raise Exception()
    def beginRemove(self, index):
        "Override this"
        log_err("override me")
        raise Exception()
        
    def endRemove(self):
        print "endRemove"
        log_err("override me")
        raise Exception()
    def firstChildInserted(self, index):
        "override this"
        log_err("override me")
        raise Exception()
    def beginChildAdd(self, parent_index, child_index):
        "hack, override this"
        log_err("override me")
        raise Exception()
    def beginChildRemove(self, parent_index, child_index):
        "hack, override this"
        log_err("Override me")
        raise Exception()
    def dataChanged(self, parent_index, child_index):
        log_err("override me")
        raise Exception()
        "hack, override this"
        
    def _addItem(self, item, key):
        if item in self:
            log_warn( "item exists")
            return
        self.beginAdd(len(self._t))
        #log_debug("passing %d" % len(self._t))
        l = list(self._t)
        l.append(item)
        self._t = tuple(l)
        item.index = len(l)-1
        self._d[key] = item
        self.endAdd()
    def _removeItem(self, item, key):
        l = list(self._t)
        old_index = item.index
        self.beginRemove(old_index)
        l.remove(item)
        self._d.pop(key)
        if len(l):
            if len(l) == 1: #only a single item.. negative index will fail..
                l[0].index = 0
            else:
                for i in l[:old_index-1]:
                    i.index -= 1
        self._t = tuple(l)
        self.endRemove()
    def _getItem(self, key):
        return self._d.get(key, None)


class YBuddy(object):
    def _initvars(self):
        self.status = None
        self.status_message = None
        self.alias = None
        self.blist = None
        self.account =  None
        self.index = None
        self.icon = None

    def __init__(self, blist, name):
        self._initvars()
        self.name = name
        self.blist = blist
        self.account = blist.account #why not?
    def __str__(self):
        return self.name
    def __hash__(self):
        return hash(self.name)
    def __eq__(self, other):
        if type(other) == str:
            return self.name == other
        else:
            return self.name == other.name
    
    @property
    def parent(self):
        return self.account
    @property
    def childCount(self):
        return 0
    
class YBuddylist(ModelBase):
    def __init__(self, account):
        self._initvars()
        self.account = account
    def add(self, buddy):
        self._addItem(buddy, buddy.name)
    def remove(self, buddy):
        self._removeItem(buddy, buddy.name)
    def get(self, name):
        return self._getItem(name)
    def beginAdd(self, index):
        self.beginChildAdd(self.account.index, index)
    def beginRemove(self, index):
        self.beginChildRemove(self.account.index, index)
    
    
    
class YCAccount(YobotAccount):    
    def _initvars(self):
        super(YobotAccount, self)._initvars()
        self.blist = None
        self.index = 0
        self._status = None
        self._status_message = None
        self.icon = None

    def __init__(self, svc, user, passw, improto):
        self._initvars()
        "Needs service to interface with the outside world"
        self.svc = svc
        self.notifier = svc.accounts
        self.blist = YBuddylist(self)
        self.blist.beginChildAdd = self.notifier.beginChildAdd
        self.blist.beginChildRemove = self.notifier.beginChildRemove
        self.blist.endAdd = self.notifier.endAdd
        self.blist.endRemove = self.notifier.endRemove
        
        self._user = user
        self._passw = passw 
        self._improto = improto      
    def __eq__(self, other):
        return (self.improto == other.improto and
                self.user == other.user )
        
    def __hash__(self):
        return hash(self.user + str(self.improto))
    
    
    def addUser(self, name):
        self.svc.addUser(self, name)
        
    def delUser(self, name,):
        self.svc.delUser(self, name)
        self.blist.remove(self.blist.get(name))
        
    def getBacklog(self, name, count):
        self.svc.getBacklog(self, name, count)
    
    def joinchat(self, room_name):
        self.svc.joinRoom(self, str(room_name))
        
    def leaveRoom(self, name):
        self.svc.leaveRoom(self, name)
            
    def connect(self):
        #assume we have an ID...
        self.svc.addAcct(self)
        log_info( "adding self to connected list...")
        
    def disconnect(self, server=False):
        self.svc.disconnectAccount(self, server)
        
    def fetchBuddies(self):
        self.svc.fetchBuddies(self)
        self.svc.fetchBuddyIcons(self)
        log_info( "Fetching buddies..")
        
    def fetchRoomUsers(self, room):
        self.svc.fetchRoomUsers(self, room)
        
    def sendchat(self,room,txt):
        assert room in rooms
        self.sendmsg(room.name, txt, chat=True)
    
    def sendmsg(self, to, txt, chat=False):
        msg = YobotMessage()
        if chat:
            msg.yprotoflags = yobotproto.YOBOT_MSG_TYPE_CHAT
        else:
            msg.yprotoflags = yobotproto.YOBOT_MSG_TYPE_IM
        msg.yprotoflags |= yobotproto.YOBOT_MSG_TO_SERVER
        msg.txt = txt
        msg.acctid = self.id
        msg.time = time()
        msg.name = to
        self.svc.sendMsg(msg)
    
    def getOfflines(self):
        self.svc.getOfflines(self)
    
    def gotmsg(self, msg):
        """This should be overridden by the GUI"""
        log_debug( msg)
        if msg.yprotoflags & yobotproto.YOBOT_MSG_TYPE_CHAT:
            #find room...
            for room in self.rooms:
                if room.name == msg.name:
                    room.gotmsg(msg)
        elif msg.yprotoflags & yobotproto.YOBOT_MSG_ATTENTION:
            log_info( msg.name, "Has buzzed you!!")
        elif msg.yprotoflags & yobotproto.YOBOT_MSG_TYPE_IM:
            pass
        
    def _getBuddy(self, name):
        buddy = None
        if name in self.blist:
            #get buddy object
            buddy = self.blist.get(name)
        else:
            buddy = YBuddy(self.blist, name)
            self.blist.add(buddy)
            #log_warn("len is", len(self.blist))
            if len(self.blist) == 1: #new buddy just added
                log_debug("calling firstChildInserted")
                self.svc.accounts.firstChildInserted(self.index)
        return buddy

        
    def gotBuddyStatus(self, name, status, text=None):
        if not name: #self:
            self.status = status
            self.status_message = text
            self.notifier.dataChanged(self.index, -1)
            return
        
        log_info( "adding buddy %s with status %d" % (name, status))
        buddy = self._getBuddy(name)
        #process events..
        buddy.status = status
        buddy.status_message = text if text else buddystatustostr(status)
        log_info("status message", buddy.status_message)
        self.notifier.dataChanged(self.index, buddy.index)
        #hack, but maybe needed:
    def gotBuddyIcon(self, name, icon_data):
        log_debug("got buddy icon for", name)
        buddy = self._getBuddy(name)
        buddy.icon = icon_data
        self.notifier.dataChanged(self.index, buddy.index)
    def statusChange(self, status_int, status_message = ""):
        if status_int > yobotproto.PURPLE_STATUS_NUM_PRIMITIVES:
            log_err("requested status that doesn't exist")
            return
        self.svc.statusChange(self, status_int, status_message)
    #status getters and setters:
    def _status_set(self, status):
        self._status = status
        self.notifier.dataChanged(self.index, -1)
    def _status_get(self):
        return self._status
    def _status_message_set(self, smessage):
        self._status_message_set = smessage
        self.notifier.dataChanged(self.index, -1)
    def _status_message_get(self):
        return self._status_message
    status = property(fget=_status_get, fset=_status_set)
    status_message = property(fget=_status_message_get, fset=_status_message_set)
    #################### TREE STUFF ############################
    @property
    def parent(self):
        return None
    @property
    def childCount(self):
        return len(self.blist)
    @property
    def name(self):
        return self._user