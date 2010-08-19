#!/usr/bin/env python
from yobotclass import YobotAccount, YobotMessage, YobotCommand
import yobotproto
from yobotops import buddystatustostr
from time import time


class YCRequest(object):
    _type = 'yesno'
    title = ""
    header = ""
    message = ""
    modal = False
    acct = None
    @property
    def isYesNo(self):
        if self._type == 'yesno':
            return True
        return False
        
class BuddyAuthorize(YCRequest):
    def __init__(self, svc, buddy, acct):
        self.title = "Authorization Request"
        self.header = acct.name
        self.message = "Allow %s to add you to his/her list?" % (buddy,)
        self.name = buddy
        self.acct = acct
        self.svc = svc
    def respond(self, auth=False):
        if auth:
            self.svc.addreqAuthorize(self.acct, self.name)
            self.svc.addUser(self.acct, self.name)
        else:
            self.svc.addreqDeny(self.acct, self.name)
class ModelBase(object):
    _t = ()
    _d = {}
    
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
    def endAdd(self):
        "Override this"
    def beginRemove(self, index):
        "Override this"
    def endRemove(self):
        "Override this"
    
    def beginChildAdd(self, parent_index, child_index):
        "hack, override this"
    def beginChildRemove(self, parent_index, child_index):
        "hack, override this"
    def dataChanged(self, parent_index=None, child_index = None):
        "hack, override this"
        
    def _addItem(self, item, key):
        if item in self:
            print "item exists"
            return
        self.beginAdd(len(self._t))
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
    status = None
    status_message = None
    alias = None
    blist = None
    account =  None
    index = None
    icon = None
    def __init__(self, blist, name):
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
    account = None
    def __init__(self, account):
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
    blist = None
    index = 0
    _status = None
    _status_message = None
    
    def __init__(self, svc, user, passw, improto):
        "Needs service to interface with the outside world"
        self.svc = svc
        self.notifier = svc.accounts
        self.blist = YBuddylist(self)
        self.blist.beginChildAdd = self.notifier.beginChildAdd
        self.blist.beginChildRemove = self.notifier.beginChildRemove
        
        self._user = user
        self._passw = passw 
        self._improto = improto      
    def __eq__(self, other):
        return (self.improto == other.improto and
                self.user == other.user )
        
    def __hash__(self):
        return hash(self.user + str(self.improto))
    
    def addroom(self,room_name):
        for room in self._rooms:
            if room.name == room_name:
                return None
        room = _YobotRoom()
        room.name = room_name
        room.account = self
        self._rooms.append(room)
        return room
    
    def addUser(self, name):
        self.svc.addUser(self, name)
        
    def getBacklog(self, name, count):
        self.svc.getBacklog(self, name, count)
    
    def joinchat(self, room_name):
        self.svc.joinRoom(self, str(room_name))
        
    def leaveRoom(self, name):
        self.svc.leaveRoom(self, name)
            
    def connect(self):
        #assume we have an ID...
        self.svc.addAcct(self)
        print "adding self to connected list..."
        
    def fetchBuddies(self):
        self.svc.fetchBuddies(self)
        self.svc.fetchBuddyIcons(self)
        print "Fetching buddies.."
        
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
        
    
    def gotmsg(self, msg):
        """This should be overridden by the GUI"""
        print "gotmsg: msg"
        print msg
        if msg.yprotoflags & yobotproto.YOBOT_MSG_TYPE_CHAT:
            #find room...
            for room in self.rooms:
                if room.name == msg.name:
                    room.gotmsg(msg)
        elif msg.yprotoflags & yobotproto.YOBOT_MSG_ATTENTION:
            print msg.name, "Has buzzed you!!"
        elif msg.yprotoflags & yobotproto.YOBOT_MSG_TYPE_IM:
            print msg
            
    def _getBuddy(self, name):
        buddy = None
        if name in self.blist:
            #get buddy object
            buddy = self.blist.get(name)
        else:
            buddy = YBuddy(self.blist, name)
            self.blist.add(buddy)
        return buddy

        
    def gotBuddyStatus(self, name, status, text=None):
        if not name: #self:
            self.status = status
            self.status_message = text
            self.notifier.dataChanged(self.index)
            return
        
        print "adding buddy %s with status %d" % (name, status)
        buddy = self._getBuddy(name)
        #process events..
        buddy.status = status
        buddy.status_message = text if text else buddystatustostr(status)
        print buddy.status_message
        self.notifier.dataChanged(self.index, buddy.index)
    
    def gotBuddyIcon(self, name, icon_data):
        print "gotBuddyIcon"
        buddy = self._getBuddy(name)
        buddy.icon = icon_data
        self.notifier.dataChanged(self.index, buddy.index)
        
    #status getters and setters:
    def _status_set(self, status):
        self._status = status
        self.notifier.dataChanged(self.index)
    def _status_get(self):
        return self._status
    def _status_message_set(self, smessage):
        self._status_message_set = smessage
        self.notifier.dataChanged(self.index)
    def _status_message_get(self):
        return self._status_message
    status = property(fget=_status_get, fset=_status_set)
    status_message = property(fget=_status_message_get, fset=_status_message_set)
    #################### TREE STUFF ############################
    icon = None
    @property
    def parent(self):
        return -1
    @property
    def childCount(self):
        return len(self.blist)
    @property
    def name(self):
        return self._user
    
class _YobotRoom(object):
    users = []
    joined = False
    account = None
    name = None
    def __init__(self, name, account):
        self.name = name
        self.account = account
    
    def sendmsg(self, txt):
        if not self.joined:
            raise NotInRoom, "Not yet connected to room %s" % self.name
        self.account.sendchat(self, txt)
    
    def join(self):
        self.account.joinchat(self)
        
    def gotmsg(self, msg):
        print msg
    def __hash__(self):
        return hash(self.name)
    def __eq__(self, other):
        return self.name == other.name


