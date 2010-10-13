#!/usr/bin/env python
import yobotproto
import collections
import yobotclass

_codes = {}

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
    
for t in ("RESPONSE", "RESPONSE_END", "BACKLOG", "DATA_IS_BINARY", "OFFLINE_MSG"):
    s = 'YOBOT_' + t
    _codes['msg'][getattr(yobotproto, s)] = s

for k in dir(yobotproto):
    v = getattr(yobotproto, k)
    for d in ("evt", "cmd", "err", "prplmsg", "msg"):
        if k.startswith(_codes[d]['PREFIX']):
            _codes[d][v] = k
            break

for t in ("evt","cmd","err","prpltype","severity","improto"):
    exec("def %stostr(c): return _codes['%s'].get(c, '['+str(c)+']')" %
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


_status_maps = {}
for s in ("Online", "Offline", "Invisible", "Busy", "Idle", "Away", "BRB"):
    _status_maps[getattr(yobotproto, "YOBOT_EVENT_BUDDY_" + s.upper())] = s
def buddystatustostr(s):
    return _status_maps.get(s, "")
    
def improto_supports_html(improto):
    return improto not in (yobotproto.YOBOT_IRC,)