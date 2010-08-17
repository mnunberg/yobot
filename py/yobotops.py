#!/usr/bin/env python
import yobotproto
import collections
import select
import yobotclass
import time
import sys

sys.stdout = sys.stderr
_codes = {}
def _log(m):
    print m

for typ,enumprefix in (
    ("evt","EVENT"),
    ("cmd", "CMD"),
    ("err", "ERR"),
    ("prplmsg", ""),
    ("msg", "MSG"),
    ("improto", ""),
    ("prpltype", ""),
    ("severity","")):
    _codes[typ] = collections.defaultdict(str)
    _codes[typ]['PREFIX'] = 'YOBOT_' + enumprefix
    
_codes['prplmsg']['PREFIX'] = "PURPLE_MESSAGE_"

for t in ("YAHOO","AIM","IRC","MSN", "GTALK", "JABBER"):
    s = 'YOBOT_' + t
    _codes['improto'][getattr(yobotproto, s)] = s

for t in ("ACCOUNT","CONV","CORE"):
    s = 'YOBOT_PURPLE_' + t
    _codes['prpltype'][getattr(yobotproto, s)] = s
    
for t in ("INFO","CRIT","WARN","PURPLE_CONNECTION_ERROR"):
    s = 'YOBOT_' + t
    _codes['severity'][getattr(yobotproto, s)] = s

for k, v in yobotproto.__dict__.iteritems():
    for d in ("evt", "cmd", "err", "prplmsg", "msg"):
        if k.startswith(_codes[d]['PREFIX']):
            _codes[d][v] = k
            break

for t in ("evt","cmd","err","prpltype","severity","improto"):
    exec("def %stostr(c): return _codes['%s'][c]" %
         (t,t,))

_codes['msg'].pop('PREFIX')
_codes['prplmsg'].pop('PREFIX')

def msgtostr(m):
    """
    this is a bitmask so we need a different kind of conversion lookup
    """
    flaglist = []
    for k,v in _codes['msg'].iteritems():
        if k & m:
            flaglist.append(v)

    if flaglist:
        return "|".join(flaglist)

    return ""

def prplmsgtostr(m):
    flaglist=[]
    for k,v in _codes['prplmsg'].iteritems():
        if k & m:
            flaglist.append(v)
    if flaglist:
        return "|".join(flaglist)
    return ""

flagtostr = msgtostr

#these functions are glue to the SWIG-generated wrappers for the C functions from
#protoclient.c/h/i. None of these have any return value.. the caller is supposed
#to wait for an event

#def mkacct(name, passw, proto,acct_id):
#    print "mkacct"
#    yobotproto.yobot_protoclient_mkacct_send(_server_read_fd,name,passw,acct_id,proto)
#    
#def enacct(acct_id):
#    print "enacct"
#    comm = yobotproto.yobotcomm()
#    cmd = yobotproto.yobotcmd()
#    comm.type = yobotproto.YOBOT_COMMTYPE_CMD
#    cmd.command = yobotproto.YOBOT_CMD_ACCT_ENABLE
#    cmd.acct_id = acct_id
#    yobotproto.yobot_protoclient_cmd_send(_server_read_fd,comm,cmd,"",0)
#    
#def sendmsg(to,txt,acct_id,is_chat=False):
#    print "sendmsg"
#    yobotflags = yobotproto.YOBOT_MSG_TO_SERVER
#    if is_chat:
#        yobotflags |= yobotproto.YOBOT_MSG_TYPE_CHAT
#    else:
#        yobotflags |= yobotproto.YOBOT_MSG_TYPE_IM
#        
#    yobotproto.yobot_protoclient_msg_send(_server_read_fd,
#                                          acct_id,
#                                          to,
#                                          txt,
#                                          None,
#                                          long(time.time()),
#                                          yobotflags,
#                                          yobotproto.PURPLE_MESSAGE_SEND)
#    print "sendmsg done"
#    
#def joinroom(room,acct_id):
#    print "joinroom"
#    comm = yobotproto.yobotcomm()
#    cmd = yobotproto.yobotcmd()
#    comm.type = yobotproto.YOBOT_COMMTYPE_CMD
#    cmd.command = yobotproto.YOBOT_CMD_ROOM_JOIN
#    cmd.acct_id = acct_id
#    s_len = len(room) + 1
#    yobotproto.yobot_protoclient_cmd_send(_server_read_fd,comm,cmd,room,s_len)
#    
#def getcomm(fd):
#    comm = yobotproto.yobotcomm()
#    yobotproto.yobot_proto_comm_get(fd,comm)
#    return comm
#
#def getcmd(fd):
#    return yobotclass.YobotCommand(yobotproto.yobot_proto_cmd_get(fd))
#
#def getevent(fd):
#    return yobotclass.YobotEvent(yobotproto.yobot_proto_event_get(fd))
#
#def getmsg(fd):
#    return yobotclass.YobotMessage(yobotproto.yobot_proto_msg_get(fd))
#    
#def getmkacct(fd):
#    ymkaccti = yobotproto.yobot_proto_mkacct_get(fd)
#    acct = yobotclass.YobotAccount(ymkaccti.user, ymkaccti._pass,
#                                    ymkaccti.yomkacct.improto,ymkaccti.yomkacct.id,
#                                    mkacct=False)
#    return acct


#_msghandler = None
#_evthandler = None
#_server_read_fd = None
#_server_write_fd = None
#
#def setevthandler(f):
#    global _evthandler
#    _evthandler=f
#def setmsghandler(f):
#    global _msghandler
#    _msghandler=f
#
#def setfds(server_read,server_write):
#    global _server_write_fd
#    global _server_read_fd
#    _server_read_fd = server_read
#    _server_write_fd = server_write
#
#def setlogger(f):
#    global _log
#    _log = f
#
#
