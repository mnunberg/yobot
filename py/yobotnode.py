import select
import socket
import yobotproto
import yobotclass
import yobotops
import collections
import random
import threading
import time

def get_rand(bits,st):
    if bits > 32:
        return None
    for _ in range(1,10):
        tmp = random.getrandbits(bits)
        if int(tmp) not in st:
            st.add(int(tmp))
            return int(tmp)
    return None
        

class YobotNode(object):
    def __init__(self, server_write_fd):
        self.server_write_fd = server_write_fd
    
    cmdhandlers = collections.defaultdict(lambda: lambda (x,y): None)
    eventhandlers = collections.defaultdict(lambda: lambda (x,y,): None)
    accounts = set()
    
    def gotmsg(self,ybmsg):
        pass
    def gotcmd(self, ybcmd):
        pass
    def gotmkacct(self,acct):
        pass    
    def gotevt(self, evt):
        pass
    
    listen_on_server = yobotops.mainloop2
    
class YobotServer(YobotNode):
    clients = set()
    "a set of connected clients"
    
    client_sendqueue = collections.defaultdict(lambda: [])
    "pending messages to be sent to clients"
    
    acctmap = collections.defaultdict(lambda: [])
    "a mapping of accounts to a list of subscribed clients"
    
    bindaddr = "0.0.0.0"
    bindport = 7770
    listenfd = None
    
    def __init__(self, server_write_fd,bindaddr=None,bindport=None):
        super(YobotNode,self).__init__(server_write_fd)
        if bindaddr:
            self.bindaddr = bindaddr
        if bindport:
            self.bindport = int(bindport)
    
    
    
    def dispatch(self, client_id, sock):
        "Handles client communication"
        fd = sock.fileno()
        sockpoll = select.poll()
        
        sockpoll.register(fd, select.POLLIN|select.POLLHUP|select.POLLOUT|select.POLLNVAL|select.POLLHUP)
        
        pollresult = sockpoll.poll(5000)
        if not len(pollresult) > 0 or not pollresult[0][1] & select.POLLIN:
            self.clients.remove(client_id)
            sock.close()
            return
        
        comm = yobotops.getcomm(fd)
        if comm.type != yobotproto.YOBOT_COMMTYPE_CMD:
            self.clients.remove(client_id)
            sock.close()
            return
        
        ycmd = yobotops.getcmd(fd)
        if ycmd.cmd != yobotproto.YOBOT_CMD_CLIENT_REGISTER:
            self.clients.remove(client_id)
            sock.close()
            return
        
        evt = yobotclass.YobotEvent()
        evt.event = yobotproto.YOBOT_EVENT_CLIENT_REGISTERED
        evt.objid = client_id
        evt.send(fd)
        
        while True:
            #block
            presult = sockpoll.poll(None)

            if presult[0][1] & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
                print "socket error or disconnect! bailing"
                return
            
            if presult[0][1] & select.POLLIN:
                comm = yobotops.getcomm(fd)
                if comm.type == yobotproto.YOBOT_COMMTYPE_CMD:
                    cmd = yobotops.getcmd(fd)
                    self.cmdhandlers[cmd.cmd](cmd)
                elif comm.type == yobotproto.YOBOT_COMMTYPE_EVENT:
                    print "GOT EVENT!! this shouldn't happen!"
                    print "BAILING"
                    return
            
            if presult[0][1] & select.POLLOUT and len(self.client_sendqueue[client_id]) > 0:
                #get pending messages
                q = self.client_sendqueue[client_id]
                while len(q):
                    m = q.pop(0)
                    m.send(fd)

            time.sleep(0.01)

    def listener(self):
        self.listenfd = socket.socket() #tcp socket
        self.listenfd.bind((self.bindaddr,self.bindport,))
        self.listenfd.listen(5)
        
        while True:
            newsock, newaddr = self.listenfd.accept()
            #establish a client ID and then work with it..
            newcid = get_rand(32, self.clients)
            if not newcid:
                newsock.close()
                print "Couldn't allocate new ID"
                continue
            self.clients.add(newcid)
            
            new_dispatcher = threading.Thread(
                name="dispatcher for %s" % (str(newaddr),),
                target = self.dispatch, args=(newcid, newsock))
            new_dispatcher.start()
            print "dispatched handler for client from %s" % (str(newaddr),)