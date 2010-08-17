#!/usr/bin/python
import socket
import sys
import cmd
import select
import time
import collections

SOCKNAME = "/tmp/yobot/clientlisten"
CONV = 34

class YobotInterpreter(cmd.Cmd):
    baseprompt = "YoBot: "
    prompt = baseprompt
    conn = None
    sockpoll = None
    mode = None
    sockname = SOCKNAME
    cmdmode = None
    def initconn(self):
        try:
            if self.conn and self.sockpoll:
                try:
                    self.sockpoll.unregister(self.conn)
                except KeyError:
                    pass
            self.conn = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
            self.conn.connect(self.sockname)
            self.sockpoll = select.poll()
            self.sockpoll.register(self.conn,select.POLLIN|select.POLLHUP)
        except (socket.error, select.error), e:
            try:
                self.sockpoll.unregister(self.conn)
            except Exception, blah:
                print blah
            self.conn = None
            print e
    
    def initmode(self):
        self.mode = collections.defaultdict(lambda: [None,None])
    
    def precmd(self, line):
        if not self.sockpoll or not self.conn :
            self.mode = None
            print "not connected!, trying to reconnect..."
            self.initconn()
        else:
            l = self.sockpoll.poll(1)
            if l and len(l) >= 1:
                _, ev = l[0]
                if ev == select.POLLHUP:
                    print "remote end hung up.. reconnecting"
                    self.mode = None
                    self.initconn()
                    return
        if self.mode:
            #just for chatting...
            if self.cmdmode == CONV and not line.startswith("/"):
                line = "msg %s [%s] " % (self.account, self.room) + line

        return line
    def default(self, line):
        print "LINE IS", line
        #only supported for rooms:
        if line.startswith("/"):
            params = line.split(" ")[1:]
            if len(params) >= 2:
                self.mode = True
                self.cmdmode = CONV
                self.account = params[0]
                self.room = " ".join(params[1:])
                self.prompt = "%s (%s:%s) " % (self.baseprompt, self.account,self.room)

                return
            elif line.startswith("/main"):
                self.mode = None
                self.cmdmode = None
                self.account = None
                self.room = None
                self.prompt = self.baseprompt
            else:
                print "unknown..."
                
        if self.conn:
            self.conn.send(line)
            print "line sent"
            #print s.recv(10) this line works.. but poll never returns anything
            if self.sockpoll.poll(None):
                print "reading response"
                print self.conn.recv(1024)
    
c = YobotInterpreter()
c.sockname = SOCKNAME
c.initconn()

prefid = 31
prefroom = "Linux, FreeBSD, Solaris:1"

c.onecmd("acct %d add yobot3 foofoo yahoo" % (prefid))
time.sleep(3)
c.onecmd("acct %d connect" % (prefid,))
time.sleep(3)
c.onecmd("msg %d [mordynu] hi" % (prefid,))
time.sleep(3)
#c.onecmd("join %d %s " % (prefid, prefroom))
#c.onecmd("/mode %d %s" % (prefid, prefroom))
#c.cmdloop()
