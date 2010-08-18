#!/usr/bin/env python

import yobotops
import yobotproto
import yobotclass
import random
import os
import sys
from Queue import Queue

from twisted.application import service
from twisted.protocols.basic import Int16StringReceiver
from twisted.internet.protocol import Factory, Protocol, ServerFactory, ClientFactory
from twisted.internet import defer

from account import AccountManager, AccountRequestHandler, AccountRemoved
from msglogger import MessageLogger, CONV_TYPE_CHAT, CONV_TYPE_IM
from client_support import ModelBase, BuddyAuthorize


if __name__ == "__main__":
    print "INSTALLING REACTOR..."
    from twisted.internet import reactor

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
    functions"""
    struct_type = None
    commflags = 0
    cmd = None
    msg = None
    evt = None
    acct = None
    base = None
    #something will 'stamp' our segment with the CID on which it was received
    cid = 0
    raw = None
    reference = 0
    def __init__(self, msg):
        """takes a raw string and convers it to a python YobotSegment"""
        self.raw = msg
        
        decoded_segment = self._decode_segment(msg)
        
        self.commflags = decoded_segment.comm.flags
        self.reference = decoded_segment.comm.reference
        self.struct_type = decoded_segment.struct_type
        
        if self.struct_type in (yobotproto.YOBOT_PROTOCLIENT_YCMDI,
                                           yobotproto.YOBOT_PROTOCLIENT_YMSGI,
                                           yobotproto.YOBOT_PROTOCLIENT_YMKACCTI):
            self.cmd = yobotclass.YobotCommand(decoded_segment.cmdi)
            self.cmd.commflags = self.commflags
            
        if self.struct_type == yobotproto.YOBOT_PROTOCLIENT_YMKACCTI:
            self.acct = yobotclass.YobotAccount(decoded_segment.mkaccti)
            self.acct.commflags = self.commflags
            self.base = self.acct
            
        elif self.struct_type == yobotproto.YOBOT_PROTOCLIENT_YMSGI:
            self.msg = yobotclass.YobotMessage(decoded_segment.msgi)
            self.msg.commflags = self.commflags
            self.msg.acctid = self.cmd.acctid
            self.base = self.msg
            
        elif self.struct_type == yobotproto.YOBOT_PROTOCLIENT_YEVTI:
            self.evt = yobotclass.YobotEvent(decoded_segment.evi)
            self.evt.commflags = self.commflags
            self.base = self.evt
            #some extra hack...
            if self.commflags & yobotproto.YOBOT_DATA_IS_BINARY:
                result = yobotproto.cdata(decoded_segment.rawdata,decoded_segment.evi.evt.len)
                self.evt.txt = result
                open("icon_log", "wb").write(result)

                
            
        elif self.struct_type == yobotproto.YOBOT_PROTOCLIENT_YCMDI:
            self.base = self.cmd
            
        else:
            raise UnknownSegment, "Segment type %s is not supported" % self.struct_type

    def _decode_segment(self,msg):
        """prepare the string so it can be passed back into C for decoding.
        I need to get rid of this"""
        return yobotproto.yobot_protoclient_segment_decode_from_buf(msg, len(msg))
    
#############################   PROTOCOLS   ##########################
class YobotNode(Int16StringReceiver):
    """
    Base yobot protocol class
    """
    registered = False
    cid = None        
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
        print pycls
        ptr = pycls.encode()
        if not ptr:
            return
        plen = yobotproto.yobot_protoclient_getsegsize(ptr)
        
        if not plen or plen > yobotproto.YOBOT_MAX_COMMSIZE:
            return None #error
        return yobotproto.cdata(ptr,plen)
        
    def sendSegment(self, pycls):
        """
        Sends a protocol representation of a python class to the connection
        """
        msg = self._encode_pycls(pycls)
        if not msg:
            return
        self.transport.write(msg)
    
    def sendPrefixed(self, str):
        self.sendString(str)
    
    #some convenience functions:
    def sendAccountEvent(self, event, id,
                         severity=yobotproto.YOBOT_INFO, txt=None):
        print "sendAccountEvent"
        evt = yobotclass.YobotEvent()
        evt.objid = id
        evt.objtype = yobotproto.YOBOT_PURPLE_ACCOUNT
        evt.severity = severity
        evt.txt = txt
        evt.event = event
        self.sendSegment(evt)
        print "done"
    
    def sendCommand(self, command, id, flags=0, txt=None):
        cmd = yobotclass.YobotCommand()
        cmd.cmd = command
        cmd.acctid = id
        cmd.commflags = flags
        cmd.data = txt
        self.sendSegment(cmd)
            
class YobotServer(YobotNode):
    #keep an account reference for when
    accounts = set()
    def connectionLost(self, reason):
        """
        Does unregistration of the client
        """
        self.factory.unregisterClient(self)

class YobotClient(YobotNode):
    def connectionMade(self):
        """
        Request registration before we do anything else, this will also
        notify the rest of the stuff about our connection.. so we can send stuff
        """
        self.factory.requestRegistration(self)
    def connectionLost(self, reason):
        print "lost server.. shutting down"
        if self.factory.reactor and self.factory.reactor.running:
            self.factory.reactor.stop()
        
class YobotPurple(YobotNode):
    def connectionMade(self):
        "Tell the pool that we're the purple node"
        self.factory.setPurple(self)
        
    def connectionLost(self, reason):
        print "lost purple.. shutting down"
        if reactor.running:
            reactor.stop()
        
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
            print e
            return None
        
        f_name = tbl.get(target, None)
        if f_name:
            return getattr(cls, f_name)(obj, proto)
        else:
            return cls.unhandled(obj, proto)
            
    return fn


class YobotServiceBase(service.Service):    
    def doRegister(self, proto, *args):
        return NotImplemented
    
    def unhandled(self, obj, proto):
        print "UNHANDLED!!"
        if obj.evt:
            print obj.evt
        if obj.cmd:
            print obj.cmd
        if obj.msg:
            print obj.msg
        print obj
        return NotImplemented
    
    dispatch = mkDispatcher("handlers", "struct_type")
    
    for i in ("evt","msg","mkacct","cmd"):
        exec(("def handle_%s(self,obj,proto): print obj.base; return NotImplemented") % i)
    
    handlers = {
        yobotproto.YOBOT_PROTOCLIENT_YEVTI : "handle_evt",
        yobotproto.YOBOT_PROTOCLIENT_YMKACCTI: "handle_mkacct",
        yobotproto.YOBOT_PROTOCLIENT_YMSGI : "handle_msg",
        yobotproto.YOBOT_PROTOCLIENT_YCMDI : "handle_cmd"
    }
        

class ClientAccountStore(ModelBase):
    def __init__(self, svc):
        self.svc = svc
    """This is intended for fast access but really slow modification"""
    def addAccount(self, acctid, acct):
        self._addItem(acct, acctid)
        self.svc._all_accounts.add(acct)
        print self._d
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
    
    
class YobotClientService(YobotServiceBase):
    """This deals with the client side of things. The account objects used here
    are a subclass of YobotAccount, and if you not the code here, we *Never* use
    the default YobotAccount, nor do we ever use the segment.acct object directly
    without first notifying the client to do the conversion. The subclassed account
    has a different __eq__ and __hash__ implementation, as well as contains the
    hooks for the UI"""
    
    def __init__(self, uihooks, reactor=None):
        self.uihooks = uihooks
        self.accounts = ClientAccountStore(self)
        self.reactor = reactor
    #accounts:
    _all_accounts = set() #for both pending and connected accounts. disconnected accounts are removed
    pending_accounts = Queue(20)
    #accounts = {} #accounts[acctid]-><YobotAccount>
    cid = None #FIXME: do we really need this?
    id_pool = set() #pool of available IDs to use for an account
    uihooks = None #for the UI to implement hooks.. we should use Interfaces..
    yobot_server = None #our connection to the server, there's only one
    
##############################  YOBOT REGISTRATION    #######################
    def doRegister(self, proto, obj):
        """
        Check if this is a registration response from the server, if it is, then
        give ourselves the cid assigned by the server, otherwise lose the connection
        """
        if (obj.struct_type == yobotproto.YOBOT_PROTOCLIENT_YEVTI and
            obj.base.event == yobotproto.YOBOT_EVENT_CLIENT_REGISTERED):
            proto.cid = obj.base.objid
            proto.registered = True
            print "client received registration response with cid ", proto.cid
        else:
            print "not expecting this..."
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
        print obj.evt
        self.dispatchEvent(obj, proto)
    def handle_msg(self,obj,proto):
        acct = self.accounts.getAccount(obj.msg.acctid)
        self.uihooks.gotmsg(acct, obj.msg)
##############################  UI EVENT OPS   #################################
    
    def handle_request(self, obj, proto):
        """Mainly for buddy auth requests but can also possibly be used for
        other stuff"""
        evt = obj.evt
        if evt.event == yobotproto.YOBOT_EVENT_USER_ADDREQ:
            req = BuddyAuthorize(self, evt.txt, self.accounts.getAccount(obj.evt.objid))
            self.uihooks.gotRequest(req)
            
    dispatchEvent = mkDispatcher("evthandlers", "evt.event")
        
    def clientRegistered(self, obj, proto):
        print "client registered"
        self.uihooks.clientRegistered()

    def gotNewId(self, obj, proto):
        self.id_pool.add(obj.evt.objid)
        #find an account that's pending...
        acct = self.pending_accounts.get(block=False)
        if acct:
            print "APPLYING GRANTED ID TO ACCOUNT"
            #assign it an ID...
            acct.changeid(self.id_pool.pop())
            self.accounts.addAccount(acct.id, acct)
            #send the request...
            proto.sendSegment(acct)
        
    def changeId(self, obj, proto):
        #get the old ID
        cur_id = obj.evt.objid
        new_id = int(obj.evt.txt)
        print "cur_id: ", cur_id
        acct = self.accounts.delAccount(cur_id)
        acct.changeid(new_id)
        self.accounts.addAccount(new_id, acct)
        #notify that we're connected, since in ID_CHANGE message is granted
        #only when the account is indeed authorized
        self.uihooks.accountConnected(self.accounts.getAccount(new_id))
    
    def accountConnected(self, obj, proto):
        self.uihooks.accountConnected(self.accounts.getAccount(obj.evt.objid))
    
    def accountConnectionRemoved(self, obj, proto):
        acct = self.accounts.delAccount(obj.evt.objid)
        if not acct:
            return None
        if obj.evt.event != yobotproto.YOBOT_EVENT_ACCT_REMOVED:
            self.uihooks.accountConnectionFailed(acct)
        else:
            self.uihooks.accountConnectionRemoved(acct)
            
    def roomJoined(self, obj, proto):
        acct = self.accounts.getAccount(obj.evt.objid)
        self.uihooks.roomJoined(acct, obj.evt.txt)
        self.fetchRoomUsers(self.accounts.getAccount(obj.evt.objid),obj.evt.txt)
        
    def buddyEvent(self, obj, proto):
        #find account...
        print "id: ", obj.evt.objid
        acct = self.accounts.getAccount(obj.evt.objid)
        if not acct:
            print "Couldn't find account!!!! <buddyEvent>"
        print acct
        
        name, data = obj.evt.txt.split(str(yobotproto.YOBOT_TEXT_DELIM), 1)
        name = name.replace('\0', '')
        
        if name == "*":
            name = None
        if obj.evt.event == yobotproto.YOBOT_EVENT_BUDDY_GOT_ICON:            
            acct.gotBuddyIcon(name, data)
        else:
            acct.gotBuddyStatus(name, obj.evt.event, data)
            
    def chatUserEvent(self, obj, proto):
        evt = obj.evt
        joined = True
        if evt.event == yobotproto.YOBOT_EVENT_ROOM_USER_LEFT:
            joined = False
            
        room, user = evt.txt.split(yobotproto.YOBOT_TEXT_DELIM, 1)
        print "Room is", room
        print "User is", user
        acct = self.accounts.getAccount(evt.objid)
        if not acct:
            print "couldn't find account"
            return
        
        if joined:
            self.uihooks.chatUserJoined(acct, room, user)
        else:
            self.uihooks.chatUserLeft(acct, room, user)
            
        print obj.evt

    
    evthandlers = {
        yobotproto.YOBOT_EVENT_CLIENT_REGISTERED : "clientRegistered",
        yobotproto.YOBOT_EVENT_ACCT_ID_NEW : "gotNewId",
        yobotproto.YOBOT_EVENT_ACCT_ID_CHANGE: "changeId",
        
        yobotproto.YOBOT_EVENT_CONNECTED: "accountConnected",
        
        yobotproto.YOBOT_EVENT_AUTH_FAIL: "accountConnectionRemoved",
        yobotproto.YOBOT_EVENT_LOGIN_ERR: "accountConnectionRemoved",
        yobotproto.YOBOT_EVENT_LOGIN_TIMEOUT: "accountConnectionRemoved",
        yobotproto.YOBOT_EVENT_ACCT_REMOVED: "accountConnectionRemoved",
        yobotproto.YOBOT_EVENT_USER_ADDREQ: "handle_request",
        yobotproto.YOBOT_EVENT_ROOM_JOINED: "roomJoined",
        yobotproto.YOBOT_EVENT_ROOM_USER_JOIN: "chatUserEvent",
        yobotproto.YOBOT_EVENT_ROOM_USER_LEFT: "chatUserEvent"
        }
    for status in ("AWAY", "BRB", "BUSY", "OFFLINE", "ONLINE", "IDLE", "INVISIBLE",
                   "GOT_ICON"):
        evthandlers[getattr(yobotproto, "YOBOT_EVENT_BUDDY_" + status)] = "buddyEvent"
        

############################   UI REQUESTS API    #############################
    def addAcct(self, acct):
        #add an account and request an ID..
        if acct in self._all_accounts:
            print "request already completed or pending.. not adding"
            return
        self.pending_accounts.put(acct)
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ACCT_ID_REQUEST,0)
        print "send account connect command for account %s" % (acct, )
    
    def addreqAuthorize(self, acct, buddy):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_USER_AUTHORIZE_ADD_ACCEPT, acct.id,
                                      txt = buddy)
    def addreqDeny(self, acct, buddy):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_USER_AUTHORIZE_ADD_DENY, acct.id,
                                      txt = buddy)
        
        self.yobot_server.sendCommand(yobotproto.YOBOT)
    def delAcct(self, acct):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ACCT_REMOVE, acct.id)
    def sendMsg(self, msg):
        self.yobot_server.sendSegment(msg)
    def joinRoom(self, acct, room_name):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ROOM_JOIN, acct.id,
                                      txt=room_name)
    def leaveRoom(self, acct, room_name):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ROOM_LEAVE, acct.id,
                                      txt=room_name)
    def addUser(self, acct, user_name):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_USER_ADD, acct.id,
                                      txt=user_name)
    def ignoreUser(self, acct, user_name):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_USER_IGNORE, acct.id,
                                      txt=user_name)
    def fetchBuddies(self, acct):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_FETCH_BUDDIES, acct.id)
    def fetchRoomUsers(self, acct, room):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_ROOM_FETCH_USERS, acct.id,
                                      txt=room)
    def fetchBuddyIcons(self, acct):
        self.yobot_server.sendCommand(yobotproto.YOBOT_CMD_FETCH_BUDDY_ICONS, acct.id)
        
###############################    PROTO FACTORY     ###########################
    def getYobotClientFactory(self):
        f = ClientFactory()
        f.protocol = YobotClient
        f.dispatch = self.dispatch
        f.doRegister = self.doRegister
        f.reactor = self.reactor
        f.requestRegistration = self.requestRegistration
        #...
        return f
    
class YobotServerService(YobotServiceBase):
    def __init__(self):
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
    
    #should eventually be something that lets us hook up with libpurple
    prpl_server = None
    
    #clients[cid] = <YobotServer>
    clients = {}
    requests = {} # requests[reqid] -> client_object
    accounts = AccountManager()
    logger = MessageLogger()
    
    
    def logHelper(self, obj):
        """For inbound messages"""
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
        acct, _ = self.accounts.byId(msg.acctid)
        
        self.logger.logMsg(msgtype,
                           yobotops.imprototostr(acct.improto),
                           acct.user,
                           msg.name,
                           msg.txt,
                           who,
                           msg.time,)
    
    def logRetriever(self, obj, proto):
        "A backlog request handler"
        #lookup account name..
        acct, _ = self.accounts.byId(obj.cmd.acctid)
        other_user, count = obj.cmd.data.split(str(yobotproto.YOBOT_TEXT_DELIM))
        count = int(count)
        type, msgs = self.logger.getMsgs(acct.user, other_user, count)
        if not type:
            return
        if type == msglogger.CONV_TYPE_IM:
            type = yobotproto.YOBOT_MSG_TYPE_IM
        elif type == msglogger.CONV_TYPE_CHAT:
            type = yobotproto.YOBOT_MSG_TYPE_CHAT
        
        ym = yobotclass.YobotMessage()
        ym.acctid = obj.cmd.acctid
        ym.name = other_user
        ym.commflags = (type|yobotproto.YOBOT_BACKLOG)
        
        for msg in msgs:
            timestamp, who, body = msg
            ym.txt = body
            ym.who = who
            ym.time = timestamp
            proto.sendSegment(ym)
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
            print "newcid:", newcid
            return newcid
            
    def unregisterClient(self, proto):
        """
        Hook for connectionLost(). Removes the CID (if any) and its associated
        protocol instance from the table of clients
        """
        print "UNREGISTERING: ", proto.cid
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
            print e, "don't care"
        print "Unregistered connection from all accounts"
        
        try:
            self.clients.pop(proto.cid)
        except KeyError, e:
            print e, "(don't care)"
        
        print "CURRENT CONNECTIONS: ", self.clients
        print "Connections: ", self.accounts._connections, "Accounts ", self.accounts._ids
    
    
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
                print "verification failing.. no such account", acctid
                return False
            
            _, protos = acct_entry
            if not protos:
                #there's no protocol instance currently connected
                print "verification failing, no connected instances", acctid
                return False
            
            if proto in protos:
                    #Account exits and has this CID in its list of clients
                    return True
                #Account exits but CID not found
            print "verification failing, CID %d not in associated client list for account %d" % (proto.cid, acctid)
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
        self.logHelper(obj)
        
    def handle_mkacct(self, obj, proto):
        AccountRequestHandler(obj, proto, self.prpl_server, self.accounts)
                    
    def handle_cmd(self, obj, proto):
        """Handle account-related commands, otherwise we just relay to purple"""
        if not self.verifyObj(obj, proto):
            raise UnauthorizedTransmission(
                "Client %d not authorized for account %d" %
                (proto.cid, obj.cmd.acctid))
        command = obj.cmd.cmd
        if command == yobotproto.YOBOT_CMD_ACCT_ID_REQUEST:
            new_id = self.accounts.reserveId(31)
            if not new_id:
                raise Exception("New ID cannot be allocated!!!!")
            proto.sendAccountEvent(yobotproto.YOBOT_EVENT_ACCT_ID_NEW, new_id)
        elif command == yobotproto.YOBOT_CMD_CLIENT_REGISTER:
            print "not relaying registration command to purple.."
        elif command in (yobotproto.YOBOT_CMD_FETCH_BUDDIES,
                         yobotproto.YOBOT_CMD_ROOM_FETCH_USERS,
                         yobotproto.YOBOT_CMD_FETCH_BUDDY_ICONS):
            #generate reference..
            reference = get_rand(8,self.requests.keys())
            if not reference:
                print "CAN'T ALLOCATE REQUEST ID!"
                return
            #generate new command..
            obj.cmd.reference = reference
            self.requests[reference] = proto
            #re-encode because we added a reference ID...
            self.prpl_server.sendSegment(obj.cmd)
        elif command == yobotproto.YOBOT_CMD_REQUEST_BACKLOG:
            self.logRetriever(obj, proto)
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
    
    purple_handlers = {
        yobotproto.YOBOT_PROTOCLIENT_YEVTI : "purple_handle_evt",
        yobotproto.YOBOT_PROTOCLIENT_YMKACCTI : "purple_handle_mkacct",
        yobotproto.YOBOT_PROTOCLIENT_YMSGI : "purple_handle_msg"}
    
    purple_eventhandlers = {
        yobotproto.YOBOT_EVENT_DISCONNECTED : "purple_handle_acct_connection",
        yobotproto.YOBOT_EVENT_AUTH_FAIL: "purple_handle_acct_connection",
        yobotproto.YOBOT_EVENT_CONNECTED : "purple_handle_acct_connection",
        yobotproto.YOBOT_EVENT_LOGIN_ERR : "purple_handle_acct_connection",
        yobotproto.YOBOT_EVENT_BUDDY_GOT_ICON : "relay_event",
        yobotproto.YOBOT_EVENT_ROOM_USER_JOIN: "relay_event",
        yobotproto.YOBOT_EVENT_CONNECTING: "relay_event",
        yobotproto.YOBOT_EVENT_USER_ADDREQ: "relay_event",
        yobotproto.YOBOT_EVENT_ROOM_JOINED: "relay_event",
        }
    for status in ("AWAY", "BRB", "BUSY", "OFFLINE", "ONLINE", "IDLE", "INVISIBLE"):
        purple_eventhandlers[getattr(yobotproto, "YOBOT_EVENT_BUDDY_" + status)] = "relay_event"
    
    
    def setPurple(self, proto):
        self.prpl_server = proto
        
    def purpleDoRegister(self, proto, obj):
        obj = obj.base
        if obj.struct_type == yobotproto.YOBOT_PROTOCLIENT_YEVTI:
            if obj.event == yobotproto.YOBOT_EVENT_CLIENT_REGISTERED:
                proto.registered = True
                print "Purple is ", self.prpl_server, "REGISTERED!"
    
    
    
    def _relay_segment(self, obj, acctid):
        _, protos = self.accounts.byId(acctid)
        for p in protos:
            p.sendPrefixed(obj.raw)
    
    def purple_handle_msg(self, obj, proto):
        print "GOT MESSAGE"
        print obj.msg
        #relay the message to all connected clients...
        self._relay_segment(obj, obj.cmd.acctid)
            
    def purple_handle_mkacct(self, obj, proto):
        pass

    
    def purple_handle_acct_connection(self, obj, proto):
        """This will handle account events coming from purple.."""
        print "purple_handle_acct_connection"
        evt = obj.evt
        print evt
        acct_id = evt.objid
        if evt.event in (yobotproto.YOBOT_EVENT_AUTH_FAIL, yobotproto.YOBOT_EVENT_LOGIN_ERR):
            #find account and trigger its errback:
            acct, _ = self.accounts.byId(acct_id)
            if not acct:
                return
            #relay the segment now because the client/account lookup will be
            #broken after the account has been deleted:
            self._relay_segment(obj, acct_id)
            acct.timeoutCb.cancel()
            acct.connectedCb.errback(AccountRemoved("Login Failed"))
            return
        
        elif evt.event == yobotproto.YOBOT_EVENT_CONNECTED:
            acct, _ = self.accounts.byId(acct_id)
            if not acct:
                raise KeyError(
                    "account %d was connected but was not found in the accounts list" % (acct_id,))
            acct.timeoutCb.cancel()
            acct.connectedCb.callback(None)
            print "ACCOUNT %d connected!" % acct_id
        
        elif evt.event == yobotproto.YOBOT_EVENT_DISCONNECTED:
            #FIXME: HANDLE THIS
            print "DISCONNECTED..."
            return
        
        else:
            print evt
        self._relay_segment(obj, acct_id)
        
        
    def purple_request_responder(self, obj, proto):
        """What we do here is simple.. look at the commflags for a "YOBOT_RESPONSE",
        and if so, relay the segment to the client"""
        #first get the type...
        if obj.commflags & yobotproto.YOBOT_RESPONSE_END:
            self.requests.pop(obj.reference, None)
            print "request done.. removing.."
            return
        if not obj.commflags & yobotproto.YOBOT_RESPONSE:
            print "how the hell did this get here.."
            return
        client = self.requests.get(obj.reference, None)
        if not client:
            print "couldn't get client!"
            return
        #check that the client is associated with the account ID still (this is
        #a really paranoid provision, for e.g. a new client which has taken the
        #old id of the previous client....)
        
        #if not self.verifyObj(obj, client):
        #    raise UnauthorizedTransmission()
        #finally.. relay..
        print obj.evt
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
        return f

############## TESTING ################
if __name__ == "__main__":
    CLIENT, SERVER = [1,2]
    mode = None
    if sys.argv[1] == "-c":
        mode = CLIENT
    elif sys.argv[1] == "-s":
        mode = SERVER
        
    if mode == CLIENT:
        svc = YobotClientService()
        reactor.connectTCP("localhost", 7770, svc.getYobotClientFactory())
    elif mode == SERVER:
        svc = YobotServerService()
        reactor.connectTCP("localhost", 7771, svc.getYobotPurpleFactory())
        reactor.listenTCP(7770, svc.getYobotServerFactory())
        
    reactor.run()