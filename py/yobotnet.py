#!/usr/bin/env python

import yobotops
import yobotproto
import yobotclass
import random
import sys
from hashlib import sha1
from Queue import Queue

from twisted.application import service
from twisted.protocols.basic import Int16StringReceiver
from twisted.internet.protocol import Factory, Protocol, ServerFactory, ClientFactory
from twisted.internet import defer

from account import AccountManager, AccountRequestHandler, AccountRemoved
from msglogger import MessageLogger, CONV_TYPE_CHAT, CONV_TYPE_IM
import msglogger
from client_support import ModelBase, BuddyAuthorize, YCRequest, SimpleNotice
from debuglog import log_debug, log_err, log_warn, log_crit, log_info
import debuglog
import time

import yobot_interfaces

reactor = None

def get_rand(bits,st):
    if bits > 31:
        return None
    for _ in range(1,10):
        tmp = random.getrandbits(bits)
        tmp = abs(tmp)
        if tmp not in st:
            return tmp
    return None

class UnknownSegment(Exception): pass
class UnauthorizedTransmission(Exception): pass
class PurpleNotAvailable(Exception): pass

class YobotSegment(object):
    """Just a way to bind together the various protocol types for lower level
    functions.
    Instance variables `cmd', `msg', `evt', and `acct', which hold the
    corresponding YobotBase subclass instance that the decoded string has been
    resolved to. Usually only one of these will hold actual data and the rest
    will be set to None.
    `base' is a 'link' to whatever the main object is.
    A reference to the 'raw' undecoded string is contained in `raw'."""
    
    def __init__(self, msg):
        """takes a raw string and converts it to a python YobotSegment."""        
        for a in ("cmd", "msg", "evt", "acct", "base"):
            setattr(self, a, None)
        #something will 'stamp' our segment with the CID on which it was received
        self.cid = 0
        self.raw = msg
        
        decoded_segment = self._decode_segment(msg)
        
        self.commflags = decoded_segment.comm.flags
        self.reference = decoded_segment.comm.reference
        self.struct_type = decoded_segment.struct_type
        
        if self.struct_type in (yobotproto.YOBOT_PROTOCLIENT_YCMDI,
                                           yobotproto.YOBOT_PROTOCLIENT_YMSGI,
                                           yobotproto.YOBOT_PROTOCLIENT_YMKACCTI):
            self.cmd = yobotclass.YobotCommand(decoded_segment.cmdi)
            
        if self.struct_type == yobotproto.YOBOT_PROTOCLIENT_YMKACCTI:
            self.acct = yobotclass.YobotAccount(decoded_segment.mkaccti)
            self.base = self.acct
            
        elif self.struct_type == yobotproto.YOBOT_PROTOCLIENT_YMSGI:
            self.msg = yobotclass.YobotMessage(decoded_segment.msgi)
            self.msg.acctid = self.cmd.acctid
            self.base = self.msg
            
        elif self.struct_type == yobotproto.YOBOT_PROTOCLIENT_YEVTI:
            self.evt = yobotclass.YobotEvent(decoded_segment.evi)
            self.base = self.evt
            #some extra hack...
            if self.commflags & yobotproto.YOBOT_DATA_IS_BINARY:
                result = yobotproto.cdata(decoded_segment.rawdata,decoded_segment.evi.evt.len)
                self.evt.txt = result
            
        elif self.struct_type == yobotproto.YOBOT_PROTOCLIENT_YCMDI:
            self.base = self.cmd
            
        else:
            raise UnknownSegment, "Segment type %s is not supported" % self.struct_type
        self.base.commflags = self.commflags
        self.base.reference = self.reference
        
        
    def _decode_segment(self,msg):
        """prepare the string so it can be passed back into C for decoding.
        I need to get rid of this"""
        return yobotproto.yobot_protoclient_segment_decode_from_buf(msg, len(msg))
        
    def __str__(self):
        return str(self.base) if self.base else "<Unknown Segment>"
    

def getNameAndData(obj):
    """Parse certain events to extract the name and data portion -> (name, data)"""
    name, data = obj.evt.txt.split(str(yobotproto.YOBOT_TEXT_DELIM), 1)
    name = name.replace('\0', '')
    return (name, data)


#############################   PROTOCOLS   ##########################
class YobotNode(Int16StringReceiver):
    """
    Base yobot protocol class
    """
    def _initvars(self):
        self.registered = False
        self.cid = None
        
    def __init__(self):
        self._initvars()
        
    def stringReceived(self, msg):
        """
        We need some further decoding here before we use python...
        """
        obj = YobotSegment(msg)        
        assert obj        
        if not self.registered:
            self.factory.doRegister(self,obj)
        self.factory.dispatch(obj, self)

    segmentReceived = stringReceived
    
    def _encode_pycls(self,pycls):
        """
        Calls the object's .encode() method and returns a python string version
        """
        log_debug( pycls)
        ptr = pycls.encode()
        if not ptr:
            return
        plen = yobotproto.yobot_protoclient_getsegsize(ptr)
        
        if not plen or plen > yobotproto.YOBOT_MAX_COMMSIZE:
            return None #error
        return yobotproto.cdata(ptr,plen)
        
    def sendSegment(self, pycls):
        """
        Sends a protocol representation of a YobotBase subclass to the connection
        """
        msg = self._encode_pycls(pycls)
        if not msg:
            return
        self.transport.write(msg)
    
    def sendPrefixed(self, str):
        """Send a raw encoded protocol string"""
        self.sendString(str)
    
    #some convenience functions:
    def sendAccountEvent(self, event, id,severity=yobotproto.YOBOT_INFO, txt=None):
        "Convenicne function to send an event related to an account"
        log_debug("begin")
        evt = yobotclass.YobotEvent()
        evt.objid = id
        evt.objtype = yobotproto.YOBOT_PURPLE_ACCOUNT
        evt.severity = severity
        evt.txt = txt
        evt.event = event
        self.sendSegment(evt)
        log_debug( "done")
    
    def sendCommand(self, command, id, flags=0, txt=None):
        "Convenience function that sends a command"
        cmd = yobotclass.YobotCommand()
        cmd.cmd = command
        cmd.acctid = id
        cmd.commflags = flags
        cmd.data = txt
        self.sendSegment(cmd)
            
class YobotServer(YobotNode):
    def __init__(self):
        self._initvars()
        #keep an account reference for when
        #self.accounts = set()
        self.iconHash = set()
    def connectionLost(self, reason):
        """Does unregistration of the client"""
        self.factory.unregisterClient(self)
    

class YobotClient(YobotNode):
    def __init__(self):
        self._initvars()
    def connectionMade(self):
        """Request registration before we do anything else, this will also
        notify the rest of the stuff about our connection.. so we can send stuff"""
        self.factory.requestRegistration(self)
    def connectionLost(self, reason):
        log_err("lost agent server.. ")
        return
        if self.factory.reactor and self.factory.reactor.running:
            self.factory.reactor.stop()
        
class YobotPurple(YobotNode):
    def __init__(self):
        self._initvars()
    def connectionMade(self):
        "Tell the pool that we're the purple node"
        self.factory.setPurple(self)
        
    def connectionLost(self, reason):
        log_err("lost purple.. shutting down")
        if reactor.running: reactor.stop()


class PurpleQueue(object):
    """Asynchronous proxy class using Deferreds.
    Any attribute accessed is assumed to be a function. This function is dynamically
    returned and adds itself as a callback to a Deferred which will be called when
    the real purple class takes over"""
    def __init__(self):
        self.deferred = defer.Deferred()
    def __bool__(self):
        return False
    def __getattribute__(self, name):
        "Returns a wrapper function"
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            #craft a function to insert ourself as a callback for the deferred
            def fn(*args, **kwargs):
                def cb(purple):
                    log_debug("calling purple.%s()" % (name,))
                    getattr(purple, name)(*args, **kwargs)
                    return purple
                self.deferred.addCallback(cb)
            return fn
    def release(self, purple):
        """Call with the purple protocol class. All the queued functions will be
        called"""
        log_info("calling delayed queue purple protocol class methods")
        self.deferred.callback(purple)
        
############################    SERVICES    ############################

def mkDispatcher(tbl_name, attrs):
    """generates dispatchers"""
    def fn(cls, obj, proto):
        tbl = getattr(cls, tbl_name)
        #get required attribute:
        target = obj
        try:
            for attr in attrs.split("."):
                target = getattr(target, attr)
        except AttributeError, e:
            log_warn( e)
            return None
        f_name = tbl.get(target, None)
        if f_name:
            return getattr(cls, f_name)(obj, proto)
        else:
            return cls.unhandled(obj, proto)
            
    return fn


class YobotServiceBase(service.Service):
    def _initvars(self):
        self.handlers = {
            yobotproto.YOBOT_PROTOCLIENT_YEVTI : "handle_evt",
            yobotproto.YOBOT_PROTOCLIENT_YMKACCTI: "handle_mkacct",
            yobotproto.YOBOT_PROTOCLIENT_YMSGI : "handle_msg",
            yobotproto.YOBOT_PROTOCLIENT_YCMDI : "handle_cmd"
        }
        
    def __init__(self, svc):
        self._initvars()

    def doRegister(self, proto, *args):
        return NotImplemented
    
    def unhandled(self, obj, proto):
        log_warn("UNHANDLED", obj)
        return NotImplemented
    
    dispatch = mkDispatcher("handlers", "struct_type")
    
    for i in ("evt","msg","mkacct","cmd"):
        exec(("def handle_%s(self,obj,proto): log_warn(obj.base); return NotImplemented") % i)

class ClientAccountStore(ModelBase):
    """Stores and manages accounts for the client"""
    def __init__(self, svc):
        self._initvars()
        self.svc = svc
        #register ourselves only a single time:
        store = yobot_interfaces.component_registry.get_component("account-store")
        if not store:
            yobot_interfaces.component_registry.register_component("account-store", self)
            log_info("registered")
        else:
            return store
    def addAccount(self, acctid, acct):
        self._addItem(acct, acctid)
        self.svc._all_accounts.add(acct)
        log_debug( self._d)
    def delAccount(self, acctid):
        #we might be called twice.. do some checks..
        acct = self._getItem(acctid)
        if not acct:
            return None
        self._removeItem(acct, acctid)
        self.svc._all_accounts.remove(acct)
        return acct
    def getAccount(self, acctid):
        return self._getItem(acctid)
    def clear(self):
        for k in self._d.keys():
            self.delAccount(k)
            
###############################################################################
############################## CLIENT SERVICE #################################
###############################################################################
class YobotClientService(YobotServiceBase):
    """This deals with the client side of things. The account objects used here
    are a subclass of YobotAccount, and if you not the code here, we *Never* use
    the default YobotAccount, nor do we ever use the segment.acct object directly
    without first notifying the client to do the conversion. The subclassed account
    has a different __eq__ and __hash__ implementation, as well as contains the
    hooks for the UI"""
    def _initvars(self):
        YobotServiceBase._initvars(self)
            #accounts:
        self._all_accounts = set() #for both pending and connected accounts. disconnected accounts are removed
        self.pending_accounts = Queue(20)
        #accounts = {} #accounts[acctid]-><YobotAccount>
        self.cid = None #FIXME: do we really need this?
        self.id_pool = set() #pool of available IDs to use for an account
        self.uihooks = None #for the UI to implement hooks.. we should use Interfaces..
        self.yobot_server = None #our connection to the server, there's only one
        self.evthandlers = {
            yobotproto.YOBOT_EVENT_CLIENT_REGISTERED : "clientRegistered",
            yobotproto.YOBOT_EVENT_ACCT_ID_NEW : "gotNewId",
            yobotproto.YOBOT_EVENT_ACCT_ID_CHANGE: "changeId",
            
            yobotproto.YOBOT_EVENT_CONNECTED: "accountConnected",
            yobotproto.YOBOT_EVENT_CONNECTING: "connectProgress",
            
            yobotproto.YOBOT_EVENT_AUTH_FAIL: "accountConnectionRemoved",
            yobotproto.YOBOT_EVENT_LOGIN_ERR: "accountConnectionRemoved",
            yobotproto.YOBOT_EVENT_LOGIN_TIMEOUT: "accountConnectionRemoved",
            yobotproto.YOBOT_EVENT_ACCT_REMOVED: "accountConnectionRemoved",
            yobotproto.YOBOT_EVENT_DISCONNECTED: "accountConnectionRemoved",
            
            yobotproto.YOBOT_EVENT_USER_ADDREQ: "handle_request",
            yobotproto.YOBOT_EVENT_PURPLE_REQUEST_GENERIC: "handle_request",
            yobotproto.YOBOT_EVENT_PURPLE_NOTICE_GENERIC: "handle_request",
            yobotproto.YOBOT_EVENT_AGENT_NOTICE_GENERIC: "handle_request", 
            yobotproto.YOBOT_EVENT_ROOM_JOINED: "roomJoined",
            yobotproto.YOBOT_EVENT_ROOM_LEFT: "roomLeft",
            yobotproto.YOBOT_EVENT_ROOM_USER_JOIN: "chatUserEvent",
            yobotproto.YOBOT_EVENT_ROOM_USER_LEFT: "chatUserEvent"
            }
        for status in ("AWAY", "BRB", "BUSY", "OFFLINE", "ONLINE", "IDLE", "INVISIBLE",
                       "GOT_ICON"):
            self.evthandlers[getattr(yobotproto, "YOBOT_EVENT_BUDDY_" + status)] = "buddyEvent"
        
    def __init__(self, uihooks, reactor=None):
        self._initvars()
        self.uihooks = uihooks
        self.accounts = ClientAccountStore(self)
        self.reactor = reactor
    
##############################  YOBOT REGISTRATION    #######################
    def doRegister(self, proto, obj):
        """Check if this is a registration response from the server, if it is, then
        give ourselves the cid assigned by the server, otherwise lose the connection"""
        if (obj.struct_type == yobotproto.YOBOT_PROTOCLIENT_YEVTI and
            obj.base.event == yobotproto.YOBOT_EVENT_CLIENT_REGISTERED):
            proto.cid = obj.base.objid
            proto.registered = True
            log_info( "client received registration response with cid", proto.cid)
        else:
            log_err( "not expecting this...")
            proto.transport.loseConnection()
            
    def requestRegistration(self, proto):
        """
        Send a registration request to the server. To be used in connectionMade()
        """
        proto.sendCommand(yobotproto.YOBOT_CMD_CLIENT_REGISTER,0)
        self.yobot_server = proto
        
########################   YOBOT HANDLERS    ##############################
#since we aren't receiving any commands or mkacct object (for now), we aren't implementing their handlers.

    def handle_evt(self, obj, proto):
        log_info(obj.evt)
        self.dispatchEvent(obj, proto)
    def handle_msg(self,obj,proto):
        acct = self.accounts.getAccount(obj.msg.acctid)
        self.uihooks.gotmsg(acct, obj.msg)
##############################  UI EVENT OPS   #################################
    
    def handle_request(self, obj, proto):
        """Mainly for buddy auth requests but can also possibly be used for
        other stuff"""
        evt = obj.evt
        acct = self.accounts.getAccount(obj.evt.objid)
        if evt.event == yobotproto.YOBOT_EVENT_USER_ADDREQ:
            req = BuddyAuthorize(self, evt.txt, acct)
            self.uihooks.gotRequest(req)
        elif evt.event == yobotproto.YOBOT_EVENT_PURPLE_REQUEST_GENERIC:
            req = YCRequest(self, obj.evt, acct)
            log_warn(req)
            self.uihooks.gotRequest(req)
        elif evt.event in (yobotproto.YOBOT_EVENT_PURPLE_NOTICE_GENERIC,
                           yobotproto.YOBOT_EVENT_AGENT_NOTICE_GENERIC):
            #get the text..
            req = SimpleNotice(acct, obj.evt.txt, obj.evt.reference)
            self.uihooks.gotRequest(req)
        elif evt.event == yobotproto.YOBOT_EVENT_PURPLE_REQUEST_GENERIC_CLOSED:
            log_debug("closed")
            #get request id..
            refid = obj.evt.reference
            self.uihooks.delRequest(acct, refid)
            
    dispatchEvent = mkDispatcher("evthandlers", "evt.event")
    
    def clientRegistered(self, obj, proto):
        log_info( "client registered")
        self.uihooks.clientRegistered()

    def gotNewId(self, obj, proto):
        self.id_pool.add(obj.evt.objid)
        #find an account that's pending...
        acct = self.pending_accounts.get(block=False)
        if acct:
            log_info( "APPLYING GRANTED ID TO ACCOUNT")
            #assign it an ID...
            acct.changeid(self.id_pool.pop())
            self.accounts.addAccount(acct.id, acct)
            #send the request...
            proto.sendSegment(acct)
        
    def changeId(self, obj, proto):
        #get the old ID
        cur_id = obj.evt.objid
        new_id = int(obj.evt.txt)
        log_info( "cur_id:", cur_id, "new id:", new_id)
        acct = self.accounts.delAccount(cur_id)
        acct.changeid(new_id)
        self.accounts.addAccount(new_id, acct)
        #notify that we're connected, since in ID_CHANGE message is granted
        #only when the account is indeed authorized
        self.uihooks.accountConnected(self.accounts.getAccount(new_id))
    
    def accountConnected(self, obj, proto):
        self.uihooks.accountConnected(self.accounts.getAccount(obj.evt.objid))
        
    def connectProgress(self, obj, proto):
        self.uihooks.connectProgress(self.accounts.getAccount(obj.evt.objid), obj.evt.txt)
    
    def accountConnectionRemoved(self, obj, proto):
        acct = self.accounts.delAccount(obj.evt.objid)
        if not acct:
            return None
        if obj.evt.event != yobotproto.YOBOT_EVENT_ACCT_REMOVED:
            self.uihooks.accountConnectionFailed(acct, obj.evt.txt if obj.evt.txt else "Connection Removed")
        else:
            self.uihooks.accountConnectionRemoved(acct)
            
    def roomJoined(self, obj, proto):
        acct = self.accounts.getAccount(obj.evt.objid)
        self.uihooks.roomJoined(acct, obj.evt.txt)
        #self.fetchRoomUsers(self.accounts.getAccount(obj.evt.objid),obj.evt.txt)
    def roomLeft(self, obj, proto):
        acct = self.accounts.getAccount(obj.evt.objid)
        self.uihooks.roomLeft(acct, obj.evt.txt)
        
    def buddyEvent(self, obj, proto):
        #find account...
        log_info( "id: ", obj.evt.objid)
        acct = self.accounts.getAccount(obj.evt.objid)
        if not acct:
            log_warn( "Couldn't find account!")
        log_debug(acct)
        
        name, data = getNameAndData(obj)
        
        if name == "*":
            name = None
        if obj.evt.event == yobotproto.YOBOT_EVENT_BUDDY_GOT_ICON:            
            acct.gotBuddyIcon(name, data)
        else:
            acct.gotBuddyStatus(name, obj.evt.event, data)
            
    def chatUserEvent(self, obj, proto):
        evt = obj.evt
        joined = False if evt.event == yobotproto.YOBOT_EVENT_ROOM_USER_LEFT else True
            
        room, user = evt.txt.split(yobotproto.YOBOT_TEXT_DELIM, 1)
        log_info("room:", room, "user:", user)
        acct = self.accounts.getAccount(evt.objid)
        if not acct:
            log_warn( "couldn't find account")
            return
        
        if joined:
            self.uihooks.chatUserJoined(acct, room, user)
        else:
            self.uihooks.chatUserLeft(acct, room, user)
            
        log_info( obj.evt)
        
    def genericEvent(self, obj, proto):
        acct = self.accounts.getAccount(obj.evt.objid)
        self.uihooks.genericNotice(acct, obj.evt.txt if obj.evt.txt else "")
############################   UI REQUESTS API    #############################

    def sendSegment(self, seg):
        "need wrapper because runtime yobot_server is initially null"
        self.yobot_server.sendSegment(seg)
    def addAcct(self, acct):
        #add an account and request an ID..
        if acct in self._all_accounts:
            log_warn( "request already completed or pending.. not adding")
            return
        self.pending_accounts.put(acct)
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ACCT_ID_REQUEST,0)
        log_debug( "send account connect command for account %s" % (acct, ))
        
    def addreqAuthorize(self, acct, buddy):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_USER_AUTHORIZE_ADD_ACCEPT, acct.id,
                                      txt = buddy)
    def addreqDeny(self, acct, buddy):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_USER_AUTHORIZE_ADD_DENY, acct.id,
                                      txt = buddy)        
    def delAcct(self, acct):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ACCT_REMOVE, acct.id)
    def sendMsg(self, msg):
        self.yobot_server.sendSegment(msg)
    def joinRoom(self, acct, room_name):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ROOM_JOIN, acct.id,
                                      txt = room_name)
    def leaveRoom(self, acct, room_name):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ROOM_LEAVE, acct.id,
                                      txt = room_name)
    def addUser(self, acct, user_name):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_USER_ADD, acct.id,
                                      txt = user_name)
    def delUser(self, acct, user_name):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_USER_REMOVE, acct.id,
                                      txt = user_name)
    def ignoreUser(self, acct, user_name):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_USER_IGNORE, acct.id,
                                      txt = user_name)
    def fetchBuddies(self, acct):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_FETCH_BUDDIES, acct.id)
    def fetchRoomUsers(self, acct, room):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ROOM_FETCH_USERS, acct.id,
                                      txt = room)
    def fetchBuddyIcons(self, acct):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_FETCH_BUDDY_ICONS, acct.id)
    
    def getOfflines(self, acct):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_FETCH_OFFLINE_MSGS, acct.id)
    
    def getBacklog(self, acct, user, count):
        txt = user + yobotproto.YOBOT_TEXT_DELIM + str(count)
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_REQUEST_BACKLOG, acct.id,
                                      txt = txt)
    def statusChange(self, acct, status_int, status_message):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_STATUS_CHANGE, acct.id,
                                      txt = str(status_int) + yobotproto.YOBOT_TEXT_DELIM + status_message)
    def disconnectAccount(self, acct, server=False):
        if server:
            cmd = yobotproto.YOBOT_CMD_ACCT_REMOVE
        else:
            cmd = yobotproto.YOBOT_CMD_CLIENT_RMACCT
        self.yobot_server.sendCommand(cmd, acct.id)
    
    def disconnectAll(self):
        #implied, from server...
        for a in self.accounts:
            self.disconnectAccount(a, True)
###############################    PROTO FACTORY     ###########################
    def polishClientFactory(self, f):
        f.protocol = YobotClient
        f.dispatch = self.dispatch
        f.doRegister = self.doRegister
        f.reactor = self.reactor
        f.requestRegistration = self.requestRegistration
        #...    
###############################################################################
############################ AGENT SERVICE ####################################
###############################################################################

class YobotServerService(YobotServiceBase):
    def _initvars(self):
        YobotServiceBase._initvars(self)
        #should eventually be something that lets us hook up with libpurple
        self.prpl_server = PurpleQueue()
        #clients[cid] = <YobotServer>
        self.clients = {}
        self.requests = {} # requests[reqid] -> client_object
        self.accounts = AccountManager()
        self.logger = MessageLogger()
        self._purple_initvars()
        
    def __init__(self):
        self._initvars()
        def logTimer():
            self.logger.commit()
            reactor.callLater(45, logTimer)
        reactor.callLater(45, logTimer)
    """
    Common data available to all instances and services.
    What this actually means is that the IPC connection to libpurple as
    well as the individual clients connected to our server will be able to
    use a single pool of data defined here
    """
    
    def logHelper(self, obj):
        msg = obj.msg
        who, txt = (msg.who, msg.txt)
        txt = txt if txt else ""
        who = who if who else msg.name
        
        msgtype = None
        if msg.commflags &  yobotproto.YOBOT_MSG_TYPE_CHAT:
            msgtype = CONV_TYPE_CHAT
        elif msg.commflags & yobotproto.YOBOT_MSG_TYPE_IM:
            msgtype = CONV_TYPE_IM
        if not msgtype:
            return #system message, don't need to log it...
        
        #get account info:
        #FIXME: hack.. might want to see what purple does with its usersplit thingy
        acct, _ = self.accounts.byId(msg.acctid)
        if acct.improto == yobotproto.YOBOT_JABBER:
            name = msg.name.split("/", 1)[0]
        else:
            name = msg.name
        
        try:
            self.logger.logMsg(msgtype, acct.user, yobotops.imprototostr(acct.improto),
                               name, msg.txt, who, msg.time)
        except msglogger.IntegrityError, e:
            log_err(e)
    
    def relayOfflines(self, obj, proto):
        acct, _ = self.accounts.byId(obj.cmd.acctid)
        if not acct:
            log_err("account is none")
            return
        if not acct.lastClientDisconnected:
            log_info("not relaying offlines while other clients are still connected")
            return
        for msg in self.logger.getMsgs(acct.name, yobotops.imprototostr(acct.improto),
                                     timerange = (acct.lastClientDisconnected, time.time()),
                                     count=0):
            msg.acctid = obj.cmd.acctid
            msg.yprotoflags |= (yobotproto.YOBOT_BACKLOG|yobotproto.YOBOT_OFFLINE_MSG)
            proto.sendSegment(msg)
            print msg
        self.logger.dump()
            
        log_warn("done")
        log_info(acct.lastClientDisconnected)
        acct.lastClientDisconnected = 0
            
        
    def logRetriever(self, obj, proto):
        "A backlog request handler"
        #lookup account name..
        acct, _ = self.accounts.byId(obj.cmd.acctid)
        other_user, count = obj.cmd.data.split(str(yobotproto.YOBOT_TEXT_DELIM))
        count = int(count)
        for msg in self.logger.getMsgs(acct.name, yobotops.imprototostr(acct.improto), other_user, count=count):
            msg.yprotoflags |= yobotproto.YOBOT_BACKLOG
            msg.acctid = obj.cmd.acctid
            proto.sendSegment(msg)
    ########################    REGISTRATION    ############################
    def doRegister(self, proto, obj):
        """
        Server handler for client registration:
        if obj is a CMDI with its cmd.command == CLIENT_REGISTER, it will check
        to see whether it can allocate an ID, and change the state to registered,
        otherwise it will send back an event telling it that it couldn't assign an
        ID. Otherwise it will just send back a generic error saying that it got
        unexpected data. In both of these cases it will lose the connection
        """
        evt = yobotclass.YobotEvent()
        evt.objtype = yobotproto.YOBOT_CLIENT_INTERNAL
        evt.objid = 0
        dropconn = True
  
        if (obj.struct_type == yobotproto.YOBOT_PROTOCLIENT_YCMDI and
            obj.cmd.cmd == yobotproto.YOBOT_CMD_CLIENT_REGISTER):
            
            newcid = self._tryRegister(proto)
            
            if newcid:
                proto.cid = newcid
                proto.registered = True
                
                #add the client to our list of clients
                self.clients[newcid] = proto
                
                evt.event = yobotproto.YOBOT_EVENT_CLIENT_REGISTERED
                evt.objid = newcid
                evt.severity = yobotproto.YOBOT_INFO
                dropconn = False
                
            else:
                evt.event = yobotproto.YOBOT_EVENT_CLIENT_REGISTER_ID_UNAVAILABLE
                evt.severity = yobotproto.YOBOT_CLIENT_ERROR
                dropconn = True
        else:
            evt.event = yobotproto.YOBOT_EVENT_CLIENT_ERR_BADREQUEST
            evt.objtype = yobotproto.YOBOT_CLIENT_INTERNAL
            evt.severity = yobotproto.YOBOT_CLIENT_ERROR
            dropconn = True
        
        proto.sendSegment(evt)
        if dropconn:
            proto.transport.loseConnection()
                
    
    def _tryRegister(self,protocol):
        """
        Just generate a random CID
        """
        newcid = get_rand(16,self.clients.keys())
        if not newcid:
            return None
        else:
            log_info( "newcid:", newcid)
            return newcid
        
    def unregisterClient(self, proto):
        """
        Hook for connectionLost(). Removes the CID (if any) and its associated
        protocol instance from the table of clients
        """
        log_debug( "UNREGISTERING: ", proto.cid)
        #first remove it from the accounts list:
        acct_refs = self.accounts.getConnectionData(proto)
        if acct_refs:
            acct_refs = acct_refs.copy()
            for acctid in acct_refs:
                self.accounts.delConnection(proto, id = acctid)
        #finally, remove the client.. need to find a better way for this
        try:
            self.accounts._connections.pop(proto)
        except KeyError, e:
            log_warn( e, "don't care")
        log_info( "Unregistered connection from all accounts")
        
        try:
            self.clients.pop(proto.cid)
        except KeyError, e:
            log_warn( e, "(don't care)")
        
        log_debug( "CURRENT CONNECTIONS: ", self.clients)
        log_debug( "Connections: ", self.accounts._connections, "Accounts ", self.accounts._ids)
    
    
    #########################   HANDLERS    ####################################
    #event handlers for the YobotServer relay agent/bouncer
    
    def verifyObj(self, obj, proto):
        """Verify that the acct ID referenced in the incoming client message
        indeed belongs to the client"""
        acctid = 0
        if obj.cmd: acctid = obj.cmd.acctid
        elif obj.evt: acctid = obj.evt.objid
        
        if acctid != 0:
            acct_entry = self.accounts.byId(acctid)
            if not acct_entry:
                #Account doesn't exist.
                log_err( "verification failing.. no such account", acctid)
                return False
            
            _, protos = acct_entry
            if not protos:
                #there's no protocol instance currently connected
                log_err( "verification failing, no connected instances", acctid)
                return False
            
            if proto in protos:
                    #Account exits and has this CID in its list of clients
                    return True
                #Account exits but CID not found
            log_err( "verification failing, CID %d not in associated client list for account %d" % (proto.cid, acctid))
            return False
        
        #Account ID is the special value of 0
        return True
    
    #first the relatively easy ones...
    def handle_msg(self, obj, proto):
        """Relay the message to libpurple"""
        #Check to see whether we are allowed to send this message
        if not self.verifyObj(obj, proto):
            raise UnauthorizedTransmission
        if not self.prpl_server:
            raise PurpleNotAvailable, self.prpl_server
        #relay to purple..
        self.prpl_server.sendPrefixed(obj.raw)
        
        #now log the message:
        #self.logHelper(obj)
        
    def handle_mkacct(self, obj, proto):
        AccountRequestHandler(obj, proto, self.prpl_server, self.accounts)
                    
    def handle_cmd(self, obj, proto):
        """Handle account-related commands, otherwise we just relay to purple"""
        if not self.verifyObj(obj, proto):
            log_err("unauthorized transmission: client %d, account %d" %
                    (proto.cid, obj.cmd.acctid))
            return
            #raise UnauthorizedTransmission(
            #    "Client %d not authorized for account %d" %
            #    (proto.cid, obj.cmd.acctid))
        command = obj.cmd.cmd
        if command == yobotproto.YOBOT_CMD_ACCT_ID_REQUEST:
            new_id = self.accounts.reserveId(31)
            if not new_id:
                raise Exception("New ID cannot be allocated!!!!")
            proto.sendAccountEvent(yobotproto.YOBOT_EVENT_ACCT_ID_NEW, new_id)
        elif command == yobotproto.YOBOT_CMD_CLIENT_REGISTER:
            log_info( "not relaying registration command to purple..")
        elif command in (yobotproto.YOBOT_CMD_FETCH_BUDDIES,
                         yobotproto.YOBOT_CMD_ROOM_FETCH_USERS,
                         yobotproto.YOBOT_CMD_FETCH_BUDDY_ICONS):
            #generate reference..
            reference = get_rand(8,self.requests.keys())
            if not reference:
                log_err( "CAN'T ALLOCATE REQUEST ID!")
                return
            #generate new command..
            obj.cmd.reference = reference
            self.requests[reference] = proto
            #re-encode because we added a reference ID...
            self.prpl_server.sendSegment(obj.cmd)
        elif command == yobotproto.YOBOT_CMD_REQUEST_BACKLOG:
            self.logRetriever(obj, proto)
            
        elif command == yobotproto.YOBOT_CMD_CLIENT_RMACCT:
            self.accounts.delConnection(proto, id=obj.cmd.acctid)
            proto.sendAccountEvent(yobotproto.YOBOT_EVENT_DISCONNECTED,
                                   obj.cmd.acctid,
                                   txt=("Your location is no longer associated with "
                                   "this account, as you requested"))
        elif command == yobotproto.YOBOT_CMD_ACCT_REMOVE:
            try:
                _, protos = self.accounts.byId(obj.cmd.acctid)
                for p in protos:
                    addr = ":".join([str(c) for c in proto.transport.getPeer()])
                    p.sendAccountEvent(yobotproto.YOBOT_EVENT_AGENT_NOTICE_GENERIC,
                                       obj.cmd.acctid,
                                       txt=("Disconnect requested by client %d [%s]" %
                                            (proto.cid, addr)))
            except Exception, e:
                log_err(e)
                raise
            self.prpl_server.sendPrefixed(obj.raw)
        elif command == yobotproto.YOBOT_CMD_FETCH_OFFLINE_MSGS:
            #fetch messages from log
            self.relayOfflines(obj, proto)
           
        else:
            #relay to purple....
            self.prpl_server.sendPrefixed(obj.raw)
            
    ####################    PURPLE FUNCTIONS    ################################
    _dispatch_other = mkDispatcher("purple_handlers", "struct_type")
    purple_handle_evt = mkDispatcher("purple_eventhandlers", "evt.event")
    
    def purple_dispatch(self, obj, proto):
        if obj.commflags & (yobotproto.YOBOT_RESPONSE|yobotproto.YOBOT_RESPONSE_END):
            #lookup request and handle that...
            return self.purple_request_responder(obj, proto)
        else:
            return self._dispatch_other(obj, proto)
    def _purple_initvars(self):
        self.purple_handlers = {
            yobotproto.YOBOT_PROTOCLIENT_YEVTI : "purple_handle_evt",
            yobotproto.YOBOT_PROTOCLIENT_YMKACCTI : "purple_handle_mkacct",
            yobotproto.YOBOT_PROTOCLIENT_YMSGI : "purple_handle_msg"}
        
        self.purple_eventhandlers = {
            yobotproto.YOBOT_EVENT_DISCONNECTED : "purple_handle_acct_connection",
            yobotproto.YOBOT_EVENT_AUTH_FAIL: "purple_handle_acct_connection",
            yobotproto.YOBOT_EVENT_CONNECTED : "purple_handle_acct_connection",
            yobotproto.YOBOT_EVENT_LOGIN_ERR : "purple_handle_acct_connection",
            
            yobotproto.YOBOT_EVENT_BUDDY_GOT_ICON : "update_icon",
            yobotproto.YOBOT_EVENT_ROOM_USER_JOIN: "relay_event",
            yobotproto.YOBOT_EVENT_CONNECTING: "relay_event",
            yobotproto.YOBOT_EVENT_USER_ADDREQ: "relay_event",
            yobotproto.YOBOT_EVENT_ROOM_JOINED: "relay_event",
            yobotproto.YOBOT_EVENT_ROOM_LEFT: "relay_event", 
            yobotproto.YOBOT_EVENT_PURPLE_REQUEST_GENERIC: "relay_event",
            yobotproto.YOBOT_EVENT_PURPLE_NOTICE_GENERIC: "relay_event",
            yobotproto.YOBOT_EVENT_PURPLE_REQUEST_GENERIC_CLOSED: "relay_event",
            }
        for status in ("AWAY", "BRB", "BUSY", "OFFLINE", "ONLINE", "IDLE", "INVISIBLE"):
            self.purple_eventhandlers[getattr(yobotproto, "YOBOT_EVENT_BUDDY_" + status)] = "relay_event"
    
    
    def setPurple(self, proto):
        log_info("connected to purple server")
        self.prpl_server.release(proto)
        self.prpl_server = proto
        
    def purpleDoRegister(self, proto, obj):
        obj = obj.base
        if obj.struct_type == yobotproto.YOBOT_PROTOCLIENT_YEVTI:
            if obj.event == yobotproto.YOBOT_EVENT_CLIENT_REGISTERED:
                proto.registered = True
                log_info( "Purple is ", self.prpl_server, "REGISTERED!")
    
    
    def update_icon(self, obj, proto):
        _, data = getNameAndData(obj)
        cksum = sha1(data).digest()
        try:
            _, protos = self.accounts.byId(obj.evt.objid)
        except Exception, e:
            log_err(e)
            return
        for p in protos:
            if not cksum in p.iconHash:
                p.iconHash.add(cksum)
                p.sendPrefixed(obj.raw)
            else:
                log_debug("icon already in cache")
            
    def _relay_segment(self, obj, acctid):
        try:
            _, protos = self.accounts.byId(acctid)
        except Exception, e:
            log_err(e)
            return
        for p in protos:
            p.sendPrefixed(obj.raw)
    
    def purple_handle_msg(self, obj, proto):
        log_debug( obj.msg)
        self.logHelper(obj)
        #relay the message to all connected clients...
        self._relay_segment(obj, obj.cmd.acctid)
            
    def purple_handle_mkacct(self, obj, proto):
        pass
    
    def purple_handle_acct_connection(self, obj, proto):
        """This will handle account events coming from purple.."""
        evt = obj.evt
        log_info(evt)
        acct_id = evt.objid
        if evt.event in (yobotproto.YOBOT_EVENT_AUTH_FAIL,
                         yobotproto.YOBOT_EVENT_LOGIN_ERR,
                         yobotproto.YOBOT_EVENT_DISCONNECTED):
            #find account and trigger its errback:
            try:
                acct, _ = self.accounts.byId(acct_id)
            except TypeError:
                log_err("account does not exist (anymore)")
                return            
            try:
                acct.timeoutCb.cancel()
            except Exception, e:
                log_warn(e)
            
            #relay the segment now because the client/account lookup will be
            #broken after the account has been deleted:
            self._relay_segment(obj, acct_id)
            try:
                if not evt.event == yobotproto.YOBOT_EVENT_DISCONNECTED:
                    acct.connectedCb.errback(AccountRemoved("Login Failed"))
                else:
                    acct.connectedCb.errback(AccountRemoved("Disconnected"))
            except defer.AlreadyCalledError, e:
                log_err(e)
            return
        
        elif evt.event == yobotproto.YOBOT_EVENT_CONNECTED:
            acct, protos = self.accounts.byId(acct_id)
            if not acct:
                raise KeyError(
                    "account %d was connected but was not found in the accounts list" % (acct_id,))
            acct.timeoutCb.cancel()
            acct.connectedCb.callback(None)
            acct.loggedin = True
            
            #Assume that all connections remaining in the list have already been authenticated
            for p in protos:
                self.accounts.addAuthenticatedConnection(acct, p)
            log_info( "ACCOUNT %d connected!" % acct_id)
        else:
            log_info(evt)
        self._relay_segment(obj, acct_id)
        
        
    def purple_request_responder(self, obj, proto):
        """What we do here is simple.. look at the commflags for a "YOBOT_RESPONSE",
        and if so, relay the segment to the client"""
        #first get the type...
        if obj.commflags & yobotproto.YOBOT_RESPONSE_END:
            self.requests.pop(obj.reference, None)
            log_debug("request done.. removing..")
            return
        if not obj.commflags & yobotproto.YOBOT_RESPONSE:
            log_err("how the hell did this get here..")
            return
        client = self.requests.get(obj.reference, None)
        if not client:
            log_err("couldn't get client!")
            return
        #check that the client is associated with the account ID still (this is
        #a really paranoid provision, for e.g. a new client which has taken the
        #old id of the previous client....)
        
        #if not self.verifyObj(obj, client):
        #    raise UnauthorizedTransmission()
        #finally.. relay..
        log_debug(obj.evt)
        client.sendPrefixed(obj.raw)
        
    def relay_event(self, obj, proto):
        self._relay_segment(obj, obj.evt.objid)
        
    #####################FACTORY WRAPPERS###############################
    def getYobotServerFactory(self):
        f = ServerFactory()
        f.protocol = YobotServer
        f.dispatch = self.dispatch
        f.doRegister = self.doRegister
        f.unregisterClient = self.unregisterClient
        #...
        return f
    
    def getYobotPurpleFactory(self):
        f = ClientFactory()
        f.protocol = YobotPurple
        f.setPurple = self.setPurple
        f.doRegister = self.purpleDoRegister
        f.dispatch = self.purple_dispatch
        #...
        f.attempts = 0
        max_attempts = 5
        def clientConnectionFailed(connector, reason):
            log_err("Attempt %d/%d failed: %s" % (f.attempts, max_attempts, reason))
            if f.attempts < max_attempts:
                log_info("trying again in 1.5 secs")
                reactor.callLater(1.5, connector.connect)
                f.attempts += 1
        
        f.clientConnectionFailed = clientConnectionFailed
        return f

############## TESTING ################
def startup(args=sys.argv[1:]):
    import optparse
    parser = optparse.OptionParser()
    parser.add_option("-l", "--listen", help="listening address:port", default="localhost:7770", dest="listening_addrinfo")
    parser.add_option("-c", "--connect", help="purple address:port", default="localhost:7771", dest="purple_addrinfo")
    parser.add_option("-s", help="does nothing. for compatibility", action="store_true", dest="dummy")
    options, args = parser.parse_args(args)
    
    tmp = options.listening_addrinfo.rsplit(":", 1)
    assert len(tmp) >= 2
    listen_address = tmp[0]
    listen_port = int(tmp[1])
    
    tmp = options.purple_addrinfo.rsplit(":", 1)
    assert len(tmp) >= 2
    connect_address = tmp[0]
    connect_port = int(tmp[1])

    if True:
        debuglog.init("Agent", title_color="cyan")
        log_info( "INSTALLING REACTOR...")
        from twisted.internet import reactor as _reactor
        global reactor
        reactor = _reactor
        
        yobotproto.yobot_proto_setlogger("Agent")
        svc = YobotServerService()
        
        log_info("connecting to purple at %s:%d" % (connect_address, connect_port))
        reactor.connectTCP(connect_address, connect_port, svc.getYobotPurpleFactory())
        
        log_info("listening on %s:%d" % (listen_address, listen_port))
        reactor.listenTCP(listen_port, svc.getYobotServerFactory(), interface=listen_address)
        
        reactor.run()

if __name__ == "__main__":
    startup()