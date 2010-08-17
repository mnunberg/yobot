#!/usr/bin/python
import socket
import os
import select
import collections
import yobotops
import yobotproto
import yobotclass
import random
import re

MSG_RE=re.compile(
        r"^\s*(?P<acct_id>\d+)\s*\[(?P<to>[^]]+)\]\s*(?P<msg>.+)$",
        re.S|re.I)

_acctlist = None

def setacctlist(d):
    global _acctlist
    _acctlist = d

def _cmd_join(paramlist):
    acct_id = paramlist[0]
    room = " ".join(paramlist[1:])
    acct = _acctlist[acct_id]
    if not acct:
        return "no such account\n"
    
    acct.joinroom(room)
    return "join request to %s\n" % (paramlist[0],)

def _cmd_msg(paramlist):
    m = MSG_RE.match(" ".join(paramlist))
    if not m:
        return "bad command"
    acct_id = int(m.group("acct_id"))
    to = m.group("to")
    msg = m.group("msg")
    
    acct = _acctlist[int(acct_id)]
    if not acct:
        print _acctlist
        return "no such account\n"
    acct.sendmsg(to,msg)
    return "send message request to %s\n" % (paramlist[0],)

def _cmd_acct(paramlist):
    global _acctlist
    acct_id, action = paramlist[0:2]
    print action

    if action == "connect":
        if not _acctlist[acct_id]:
            print "ACCTLIST:", _acctlist
            return "no such account\n"
        _acctlist[acct_id].connect()
        return "connect request to account %s\n" % (acct_id,)
    
    elif action == "add":
        print "add"
        if not len(paramlist[2:]) >= 3:
            return False
        user, pw, proto = paramlist[2:5]
        protocode = None
        for s, p in (
            ("yahoo",yobotproto.YOBOT_YAHOO),
            ("aim", yobotproto.YOBOT_AIM),
            ("msn", yobotproto.YOBOT_MSN),
            ("irc", yobotproto.YOBOT_IRC),):
            if s in proto.lower():
                protocode = p
        if not protocode:
            return ("protocol %s not supported!" % (proto,))
        
        acct_id = int(acct_id)
        used_ids = _acctlist.iterkeys()
        if not (acct_id in range(1,256) and acct_id not in used_ids):
            #find a new account number!
            acct_id = None
            for _ in range(1,10):
                tmp = random.randint(1,256)
                if tmp not in used_ids:
                    acct_id = tmp
                    break
            if not acct_id:
                return "too many accounts!\n"
        
        acct = yobotclass.YobotAccount(user,pw,protocode,acct_id)
        _acctlist[acct_id] = acct
        return "add request account [%d] user %s pass %s proto %s\n DONE" % (acct_id,user,pw,str(proto),)
        

_cmdtable = collections.defaultdict(lambda: None)
_cmdtable["join"] = (_cmd_join, 2)
_cmdtable["msg"] = (_cmd_msg,3)
_cmdtable["acct"] = (_cmd_acct, 2)

helpstring="""
join <acctid> <room> : join a room
msg <acctid> <room|user> <msg>: message a user
acct <acct identifier>
    connect
    disconnect
    delete
    add <name> <pass> <protocol> [server [port]]\n
"""
def _runcmd(cmd,outfile):
    w_list = cmd.split(" ")
    action = _cmdtable[w_list[0]]
    
    if not action:
        outfile.write("no such command %s\n%s" % (w_list[0],helpstring))
        return
    
    if len(w_list[1:]) < action[1]:
        outfile.write("wrong number of arguments\n")
        #outfile.write("wrong number of arguments [got %d expected %d] for `%s' command\n%s" % (
        #    len(w_list[1:]),action[1]),w_list[0],helpstring)
        return
    
    ret = action[0](w_list[1:])
    print "RET", ret
    if not ret:
        outfile.write(helpstring)
        return
    
    else:
        outfile.write(ret)
        
def mainloop():
    assert _acctlist is not None
    LISTEN_SOCKET="/tmp/yobot/clientlisten"
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.remove(LISTEN_SOCKET)
    except OSError, e:
        print e

    s.bind(LISTEN_SOCKET)
    s.listen(1)
    
    while True:
        conn, addr = s.accept()
        conn.setblocking(0)
        pobj = select.poll()
        pobj.register(conn,select.POLLIN|select.POLLHUP)
        while True:
            [(fd, cond)] = pobj.poll(None)
            if cond & select.POLLHUP:
                print "client disconnected.."
                break
            data = conn.recv(512) #string..
            _runcmd(data.strip(),conn.makefile())
        pobj.unregister(conn)