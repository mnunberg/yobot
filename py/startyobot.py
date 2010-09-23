#!/usr/bin/env python
HELPMSG="please specify 'client', 'server', or 'agent' followed by arguments"
import sys
import os
#this is one really really really nasty hack:
#first, set the initial LD_LIBRARY_PATH/PATH variables to export, then
#determine whether we are

#xerox'd from: http://www.py2exe.org/index.cgi/WhereAmI
def we_are_frozen():
    """Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located."""

    return hasattr(sys, "frozen")

def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe"""
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))
    
if not os.environ.get("YOBOTROOTPATH"):
    rootdir = module_path()
    os.environ["YOBOTROOTPATH"]=rootdir
    if os.name == "posix":
        os.environ["LD_LIBRARY_PATH"]+=os.pathsep + rootdir
    elif os.name == "nt":
        os.environ["PATH"]+=os.pathsep+rootdir
    
    print "Respawning with new path"
    #i've tried closing the std fds, but to no avail
    sys.stdout.close()
    sys.stderr.close()
    sys.stdin.close()
    if not we_are_frozen():
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        os.execv(sys.executable, [sys.executable] + sys.argv[1:])
    #should not return
    sys.exit(1)
else:
    rootdir=os.environ.get("YOBOTROOTPATH")
    
if len(sys.argv) < 2:
    print HELPMSG
    sys.exit(1)
type = sys.argv[1].lower()
if type == "client":
    print "invoking client.."
    import client
    client.startup(sys.argv[2:])
elif type == "agent":
    print "invoking agent.."
    import yobotnet
    yobotnet.startup(["-s"]+sys.argv[2:])
elif type == "server":
    if sys.platform == "win32":
        execname="yobot.exe"
        dep_paths = os.pathsep.join([os.path.abspath(p) for p in ("glib","purple")])
        print "ADDING", dep_paths, "TO PATH"
        os.environ["PATH"]+=os.pathsep
        os.environ["PATH"]+=dep_paths
    else:
        execname="yobot"
    execname=os.path.join(rootdir, execname)
    print "invoking purple server.. " + execname
    os.execve(execname, [execname] + sys.argv[2:], os.environ)
else:
    print HELPMSG
    sys.exit(1)