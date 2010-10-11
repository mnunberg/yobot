import yobotproto
import yobotops
import datetime
import time
from debuglog import log_debug, log_err, log_warn, log_crit, log_info
from yobotproto import (yobot_protoclient_cmd_encode,
                        yobot_protoclient_msg_encode,
                        yobot_protoclient_event_encode,
                        yobot_protoclient_mkacct_encode,
                        YOBOT_PROTOCLIENT_TO_BUF,
                        YOBOT_DATA_IS_BINARY,
                        yobotevent_internal,
                        yobotcmd_internal,
                        yobotmsg_internal,
                        yobot_cmdinfo,
                        yobot_msginfo,
                        yobot_mkacctinfo,
                        yobot_eventinfo)

class IMUnsupportedProtocol(Exception): pass
class NotConnected(Exception): pass
class NotInRoom(Exception): pass

class YobotBase(object):
    """Base class for all units of communication and interaction"""
    def _initvars(self):
        self.attr = "Hello"
        self.struct_type = None
        self.commflags = 0
        self.reference = 0
    def __new__(cls,*args,**kwargs):
        obj = kwargs.get("cast", None)
        if obj and isinstance(obj, cls):
            return obj
        else:
            return super(YobotBase,cls).__new__(cls)
    def encode(self):
        """To be sent to the server -- serializes the data"""
        return NotImplemented
    
    
class YobotCommand(YobotBase):
    """A command. Use this, along with a related YOBOT_CMD command. Some commands
    expect some data, while others don't"""
    def _initvars(self):
        super(YobotCommand, self)._initvars()
        self.cmd = None
        self.acctid = None
        self.data = None
        
    def __init__(self, cmdi=None, **kwargs):
        self._initvars()
        if not cmdi:
            return
        assert isinstance(cmdi,yobotcmd_internal)
        self.cmd = int(cmdi.cmd.command)
        self.acctid = int(cmdi.cmd.acct_id)
        self.data = cmdi.data
    
    def __str__(self):
        ret = "Command: "
        cmdstr = yobotops.cmdtostr(self.cmd)
        if cmdstr:
            ret += cmdstr
        else:
            ret += str(self.cmd)
            
        ret += " ID: %d" % (self.acctid,)
        
        if self.data:
            ret += " (%s)" % (self.data,)
        
        return ret
    
    def encode(self):
        if self.cmd is None or self.acctid is None:
            raise TypeError("need command and ID")
            
        dlen = 0
        if self.data and isinstance(self.data,str):
            dlen = len(self.data) + 1

        info = yobot_cmdinfo()
        info.command = self.cmd
        info.acctid = self.acctid
        info.data = self.data
        info.len = dlen
        info.commflags = self.commflags
        info.reference = self.reference
                        
        ptr = yobot_protoclient_cmd_encode(info, None, YOBOT_PROTOCLIENT_TO_BUF)
        log_debug( "encoding done")
        return ptr
    
class YobotEvent(YobotBase):
    """An event.. if you are writing a client-side application, you should never
    need to create an instance of an event, however reading it will be frequent.
    Like commands, events sometimes come with data after them.
    In practice: objid is always an account ID (except when dealing with registration
    of the client itself), severity isn't used by anything, and objtype is almost always
    an account"""
    def _initvars(self):
        super(YobotEvent, self)._initvars()
        self.event = None
        self.severity = None
        self.objid = None
        self.objtype = None
        self.txt = None

    def __init__(self, evi=None):
        self._initvars()
        if not evi:
            return

        assert isinstance(evi, yobotevent_internal)
        self.event = evi.evt.event
        self.severity = evi.evt.event_type
        self.objid = evi.evt.obj_id if evi.evt.obj_id else None
        self.objtype   = evi.evt.purple_type if evi.evt.purple_type else None
        self.txt = evi.data if evi.data else None
    def __str__(self):
        return "EVENT: %s OBJECT: %s MESSAGE: %s" % (
            yobotops.evttostr(self.event),
            str(self.objid),
            self.txt if not self.commflags & YOBOT_DATA_IS_BINARY else "<BINARY_DATA>")
        
    def encode(self):
        if self.event is None or self.objid is None:
            raise TypeError, "Can't send event without at least an ID and an event code"
        
        txtlen = 0
        if self.txt:
            txtlen = len(self.txt) + 1
        info = yobot_eventinfo()
        info.event = self.event
        info.purple_type = self.objtype
        info.acctid = long(self.objid)
        info.severity = self.severity
        info.len = txtlen
        info.data = self.txt
        ptr = yobot_protoclient_event_encode(info, None, YOBOT_PROTOCLIENT_TO_BUF)
        return ptr
    
    @property
    def acctid(self):
        return self.objid

class YobotMessage(YobotBase):
    """
    Class used for both incoming and outgoing messages
    prplmesgflags are special flags to be set by purple. You should not set them for
    outgoing messages. Try using the yprotoflags along wiht yobot constants instead.
    The name field is the name of the conversation. In a one-on-one chat, this is
    the name of the other buddy, and in a chatroom, this is the name of the room.
    The who field describes who has sent the message, and is always a username
    (unless it's a system message).
    Time is a unix timestamp as a 32 bit integer
    There are some convenience functions below.
    """
    def _initvars(self):
        super(YobotMessage, self)._initvars()
        self.prplmsgflags = 0
        self.time = 0
        self.name = ""
        self.txt = ""
        self.who = ""
        self.acctid = 0
        
    def __init__(self, ymi=None):
        self._initvars()
        if not ymi:
            return
        assert isinstance(ymi, yobotmsg_internal)
        self.prplmsgflags = ymi.yomsg.msgflags
        self.time = ymi.yomsg.msgtime #timestamp
        self.name = ymi.to
        self.txt = ymi.txt
        self.who = ymi.who if ymi.who else ""
    
    def __str__(self):
        retstr = ("FLAGS:" +
                  yobotops.prplmsgtostr(self.prplmsgflags) + " " +
                  yobotops.msgtostr(self.yprotoflags) + " ")
        
        #figure out the timestamp, if there is one:
        retstr += "[%s] " % (self.timeFmt,)
    
        if self.isServerMessage:
            retstr += "<SERVER MESSAGE>: "
        else:
            retstr += "%s <%s>: " % (self.name, str(self.who))
        
        retstr += self.txt
        return str(retstr)
    
    def encode(self):
        if not self.name or not self.acctid:
            raise TypeError("missing parmeters: name=%s, id=%s" % (self.name, self.acctid))
        info = yobotproto.yobot_msginfo()
        info.acctid = self.acctid
        info.to = str(self.name)
        info.txt = str(self.txt)
        info.who = str(self.who)
        info.msgtime = long(self.time) if self.time else long(time.time())
        info.commflags = self.yprotoflags
        info.purple_flags = self.prplmsgflags
        
        ptr = yobot_protoclient_msg_encode(info, None, YOBOT_PROTOCLIENT_TO_BUF)
        return ptr
    
    #for compatibility...
    def _yprotoflags_set(self, value):
        self.commflags |= value
    def _yprotoflags_get(self):
        return self.commflags
    yprotoflags = property(fget=_yprotoflags_get, fset=_yprotoflags_set)
    
    @property
    def isChat(self):
        return bool(self.yprotoflags & yobotproto.YOBOT_MSG_TYPE_CHAT)
    @property
    def isIm(self):
        return bool(self.yprotoflags & yobotproto.YOBOT_MSG_TYPE_CHAT)
    @property
    def isServerMessage(self):
        return bool(self.prplmsgflags & yobotproto.PURPLE_MESSAGE_SYSTEM)
    @property
    def isFromSelf(self):
        return bool(self.prplmsgflags & yobotproto.PURPLE_MESSAGE_SEND)
    @property
    def isFromOther(self):
        return bool(self.prplmsgflags & yobotproto.PURPLE_MESSAGE_RECV)
    @property
    def hasNick(self):
        return bool(self.prplmsgflags & yobotproto.PURPLE_MESSAGE_NICK)
    @property
    def timeFmt(self):
        retstr = ""
        if self.time:
            ts = datetime.datetime.fromtimestamp(self.time)
            retstr += "%02d:%02d:%02d" % (ts.hour,ts.minute,ts.second)
        else:
            retstr += "::"
        return retstr

        
def attr_getter(attr):
    def get_any(cls):
        return getattr(cls,attr)
    return get_any

class YobotAccount(YobotBase):
    """This is the bare-bones account class, and contains only information on the
    accounts login name (acct.user), protocol (acct.improto), and its assigned id
    (acct.acctid) -- and password.
    There are more extended subclasses in account.YAccountWrapper and client_support.YCAccount"""
    def _initvars(self):
        super(YobotAccount, self)._initvars()
        self._improto = None
        self._user = None
        self._passw = None
        self._id = None
        self._proxy_host = None
        self._proxy_type = None
        self._proxy_username = None
        self._proxy_password = None
        self._proxy_port = None
        
    def __init__(self, mkaccti=None, user=None, passw=None, id=None, improto=None,
                 proxy_host = None, proxy_port = None, proxy_username = None,
                 proxy_password = None, proxy_type = None):
        self._initvars()
        if mkaccti is not None:
            self._improto = mkaccti.yomkacct.improto
            self._user = mkaccti.user
            self._passw = mkaccti._pass
            self._id = mkaccti.yomkacct.id
            #no need for anything here to parse proxy information..
        else:
            self._improto = improto
            self._user = user
            self._passw = passw
            self._id = id
            self._proxy_host = proxy_host
            self._proxy_username = proxy_username
            self._proxy_password = proxy_password
            self._proxy_port = proxy_port
            self._proxy_type = proxy_type
        if not yobotops.imprototostr(self._improto):
            raise IMUnsupportedProtocol(self._improto)        

    for a in ("improto", "user", "passw", "id"):
        exec("%s=property(fget=attr_getter('_%s'))" % (a,a))
        
    def encode(self):
        if not self.user or not self.passw or not self.improto or not self.id:
            raise TypeError("missing parameters")
        info = yobot_mkacctinfo()
        info.user = self.user
        info.password = self.passw
        info.acctid = self.id
        info.improto = self.improto
        if self._proxy_host:
            proxy_info_xml = "<foo><proxy_info proxy_host='%s' " % (self._proxy_host)
            if self._proxy_port:
                proxy_info_xml += "proxy_port='%s' " % (str(self._proxy_port))
            if self._proxy_username:
                proxy_info_xml += "proxy_username='%s' " % (self._proxy_username)
                if self._proxy_password:
                    proxy_info_xml += "proxy_password='%s' " % (self._proxy_password)
            
            if self._proxy_type in ("socks4", "socks5", "http"):
                proxy_info_xml += "proxy_type='%d' " % (
                    getattr(yobotproto, "PURPLE_PROXY_" + self._proxy_type.upper()))
            else:
                log_warn("unknown proxy type", self._proxy_type)
                proxy_info_xml = ""
            
            if proxy_info_xml:
                proxy_info_xml += "/></foo>"
            info.attr_xml = proxy_info_xml
            log_debug(proxy_info_xml)
        else:
            log_err("proxy info is null?")
        ptr = yobot_protoclient_mkacct_encode(info, None, YOBOT_PROTOCLIENT_TO_BUF)
        return ptr
    
    def changeid(self, new_id):
        self._id = new_id
    
    def __str__(self):
        return "Account: name=%s protocol=%s" % (self.user,yobotops.imprototostr(self.improto))
        
    @property
    def name(self):
        return self._user