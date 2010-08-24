#!/usr/bin/env python
from yobotclass import YobotAccount
from twisted.internet import reactor, defer
from twisted.python.failure import Failure
from debuglog import log_debug, log_err, log_warn, log_crit, log_info

import random
import yobotproto

RESERVED_ID = -1
NO_MATCH=0
PASSWORD_MATCH=1<<0
USERPROTO_MATCH=1<<1

TABLE_ACCTID = 1
TABLE_USERPROTO = 2

class YAccountWrapper(object):
    """This is a wrapper class for YobotAccount which stores server-specific
    data"""
    _wrapped = None
    timeoutCb = None
    connectedCb = None
    def __init__(self, yobotaccount_instance):
        self._wrapped = yobotaccount_instance
    def __getattr__(self, name):
        try:
            #try to see if we have the attribute
            return super(YAccountWrapper, self).__getattr__(name)
        except AttributeError:
            return getattr(self._wrapped, name)
    
    def __setattr__(self, name, value):
        if hasattr(self._wrapped, name):
            self._wrapped.__setattr__(name, value)
        else:
            super(YAccountWrapper, self).__setattr__(name, value)

class AccountManager(object):
    _accounts = {} #acounts[user,protocol]->(<YobotAccount>,set([protocol instances,..]))
    _ids = {} #ids[id] -> """"" duplicate lookup
    
    _connections = {} #proto[<proto connection instance>]->set([acct ids,...])
    
    def byId(self, id):
        """->(account, protocol_instances)"""
        return self._ids.get(id, None)
        
    def byUserProto(self, user, improto):
        return self._accounts.get((user,improto), None)
        
    def _getacct(self, id=None, userproto=(None,None)):
        """-> (acct_entry, lookup_table) """
        #automatically raise KeyError if the account does not exit
        if id:
            acct_entry = self._ids[id]
            return (acct_entry, TABLE_ACCTID)
        elif userpass and userpass != (None, None):
            acct_entry = self._accounts[userproto]
            return (acct_entry, TABLE_USERPROTO)
        else:
            raise TypeError, "Need either an ID or a user,proto"

    def acctExists(self, ybacct):
        """uses the user,proto index 
        Returns [MATCH_TYPE, ]
        """
        ret = [NO_MATCH, None]
        acct_match = self.byUserProto(ybacct.user,ybacct.improto)
        if not acct_match:
            #no match at all
            log_info( "NO MATCH.. returning", ret)
            return ret
        ret[0] |= USERPROTO_MATCH
        ret[1] = acct_match
        
        if acct_match[0].passw == ybacct.passw:
            ret[0] |= PASSWORD_MATCH
        return ret
    
    def addAcct(self,reqhandler):
        acct = reqhandler.newacct
        res_type, acct_data = self.acctExists(acct)
        
        if res_type & (USERPROTO_MATCH|PASSWORD_MATCH):
            log_info( "FULL MATCH")
            #account exists, notify of existing ID
            reqhandler.handle_exists(acct_data)
            
        elif res_type & USERPROTO_MATCH:
            log_info( "USERPROTO MATCH")
            if acct_data[0].loggedin:
                reqhandler.handle_authfail(acct_data)
            else:
                reqhandler.handle_authwait(acct_data)
                #wait until an account has been authenticated
                
        elif res_type == NO_MATCH:
            log_info( "NO MATCH!!!")
            #Add to both our indices
            acct_data = self._accounts[acct.user,acct.improto] = [acct, set()]
            self._ids[acct.id] = acct_data
            reqhandler.handle_added(acct_data)
    
    def delAcct(self, id=None,userproto=None):
        """Deletes an account indexed by ID or (user,proto) pair. If the account
        exists, it will return the data portion of the entry. This will also
        delete the account from the connected protocol instances..
        Raises KeyError if something doesn't exist"""
        (acct, data) = None, None
        if id:
            log_debug("looking up ID")
            #get account from ID and remove from other dict:
            res = self._ids.pop(id)
            if res == RESERVED_ID:
                log_debug("Reserved ID")
                return None
            
            acct, data = res
            self._accounts.pop((acct.user,acct.improto))
        elif userproto:
            log_debug("looking up userproto")
            res = self._accounts.pop((userproto))
            assert res
            acct, data = res
            self._ids.pop(acct.id)
        else:
            log_err("oops.. neither id or userproto was specified")
            raise TypeError, "Must provide a (user,proto) or ID as a key"
        
        for conn in data:
            self._connections[conn].remove(acct.id)
        log_debug("done")
        
        
    def _update_both(self, acct, st, lookup_table):
        """Updates the *other* table"""
        if lookup_table == TABLE_ACCTID:
            #update the user,prot table:
            self._accounts[acct.user,acct.improto][1] = st
        elif lookup_table == TABLE_USERPROTO:
            self._ids[acct.id] = st

    
    def addConnection(self, connection, id=None, userproto=(None,None)):
        """Adds a connection to an account's data list"""
        ((acct, st),lookup_table) = self._getacct(id, userproto)        
        st.add(connection)
        
        self._update_both(acct, st, lookup_table)
        try:
            self._connections[connection].add(acct.id)
        except KeyError, e:
            self._connections[connection] = set()
            self._connections[connection].add(acct.id)
        
    def delConnection(self, connection, id=None, userproto=(None,None)):
        """Removes a connection from the account's data list"""
        #FIXME: accept iterables for id and userproto
        ((acct, st), lookup_table) = self._getacct(id, userproto)
        try:
            st.remove(connection)
        except KeyError, e:
            log_warn( e)
            return
        
        self._update_both(acct, st, lookup_table)
        
        try:
            self._connections[connection].remove(acct.id)
        except KeyError, e:
            log_warn( e)
            return
    
    def getConnectionData(self, connection):
        return self._connections.get(connection, None)
        

    def reserveId(self,bits):
        if bits > 31:
            return None
        for _ in range(1,10):
            tmp = random.getrandbits(bits)
            tmp = abs(tmp)
            if not self._ids.has_key(tmp):
                self._ids[tmp] = RESERVED_ID
                return tmp
        return None
    def unreserveId(self, id):
        tmp = self._ids.get(id, None)
        if not tmp:
            return
        if tmp != RESERVED_ID:
            raise KeyError, "This key is already in use!"
        
class AccountRemoved(Exception): pass
class AccountRequestHandler(object):
    """If the account already exists (user, password, and protocol match)
    then we will add the requesting client to the list of connected clients
    for the given account, and reply with the already existent ID of the account.
    
    If the account already exists, is authenticated, but has a *different*
    password, then we consider this an invalid login and notify the client of this
    
    If the account exits but is not yet authenticated, we schedule a retry to
    check whether the existing account has been authenticated or not. In other words
    we call a smaller version of ourself again.

    If the account does not yet exist, the mkacct request will be forwarded
    to libpurple
    
    We try to connect the account as soon as possible, and ever account addition
    will have a timeout of a minute to connect, after the timeout expires, the
    account is removed from both purple and our own list
    """
    def __init__(self, seg, proto, prpl, acct_mgr):
        self.seg = seg
        self.newacct = YAccountWrapper(seg.acct)
        self.proto = proto
        self.prpl = prpl
        self.acct_mgr = acct_mgr
        self.acct_mgr.addAcct(self)
        self.timedOut = False
        
    def handle_added(self,acct_data):
        existing_acct, _ = acct_data
        assert existing_acct == self.newacct
        #send out the connection request to purple:
        
        #tell purple to add the account... this is the raw message as received from the client
        self.prpl.sendPrefixed(self.seg.raw)
        
        #and "enable" (connect) it:
        self.prpl.sendCommand(yobotproto.YOBOT_CMD_ACCT_ENABLE,self.newacct.id)
        
        #setup a deferred... this will automatically remove the
        #account if we aren't connected in 30 seconds (the connected event
        #should cancel this...)
        self.acct_mgr.addConnection(self.proto, id=self.newacct.id)
        
        d = defer.Deferred()
        d.addErrback(self.rm_account)
        def _callTimeout():
            self.timedOut = True
            d.errback(AccountRemoved("Account authorization timed out"))
            
        t = reactor.callLater(10, _callTimeout)
        
        self.newacct.timeoutCb = t
        self.newacct.connectedCb = d
        
    def handle_authfail(self, null):
        #not using the existing account
        
        #notify the proto about the failed account request:
        self.proto.sendAccountEvent(yobotproto.YOBOT_EVENT_AUTH_FAIL,self.newacct.id,
                                     severity=yobotproto.YOBOT_CRIT)
        
    def handle_exists(self, acct_data):
        existing_acct, _ = acct_data
        
        #notify about the ID change
        self.proto.sendAccountEvent(yobotproto.YOBOT_EVENT_ACCT_ID_CHANGE,
                               self.newacct.id, severity=yobotproto.YOBOT_INFO,
                               txt=str(existing_acct.id))
        
        self.acct_mgr.addConnection(self.proto, id=existing_acct.id)
        #remove the ID that we got from the list...
        self.acct_mgr.unreserveId(self.newacct.id)
        
    def handle_authwait(acct_data):
        #here we relay on the callback timers in the acct object, added in
        #handle_added
        pending_acct, _ = acct_data
        assert (pending_acct.timeoutCb and pending_acct.connectedCb)
        def pending_succeeded(cbresult):
            #the account we were waiting on succeeded, this means that the
            #new account is NOT valid, call handle_authfail
            handle_authfail(None)
        def pending_failed(cbresult):
            #the acount we were waiting on didn't authorize, which means that
            #our new account might indeed work, try again
            self.handle_mkacct(self.obj, self.proto)
        
        pending_acct.connectedCb.addErrback(pending_failed)
        pending_acct.connectedCb.addCallback(pending_succeeded)                
        
    def rm_account(self, cbresult):
        log_debug( "rm_account...")
        #tell the client we've timed out
        if self.timedOut:
            log_debug( "sending event..")

            self.proto.sendAccountEvent(yobotproto.YOBOT_EVENT_LOGIN_TIMEOUT,
                                    self.newacct.id,severity=yobotproto.YOBOT_WARN,
                                    txt="Yobot Server did not get a response from purple")
            log_debug( "Sent event")
        
        #tell purple to forget about our account
        log_debug( "telling purple to remove the account...")
        self.prpl.sendCommand(yobotproto.YOBOT_CMD_ACCT_REMOVE,self.newacct.id)
        log_debug( "done")
        
        try:
            log_debug( "deleting account from relay...")
            self.acct_mgr.delAcct(id=self.newacct.id)
            log_debug( "done")
        except Exception,e:
            log_warn( err)
        
        log_info( "deleted account %d" % self.newacct.id)