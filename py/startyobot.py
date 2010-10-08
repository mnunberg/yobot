#!/usr/bin/env python
import sys
import os
import optparse

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
    
def get_yobot_dirs(home=None):
    def _mkdir(path):
        if not os.path.exists(path):
            os.mkdir(path, 0700)
        else:
            os.chmod(path, 0700)
            
    if not home:
        home = os.path.expanduser("~")
    config_root = os.path.join(home, ".yobot")
    log = os.path.join(config_root, "log")
    purple_dir = os.path.join(config_root, "purple")
    
    _mkdir(config_root)
    _mkdir(log)
    _mkdir(purple_dir)
    
    return {"config_root":config_root, "log_dir":log, "purple_dir":purple_dir}

def do_start(args=sys.argv):
    if not os.environ.get("YOBOTROOTPATH"):
        rootdir = os.path.abspath(module_path())
        os.environ["YOBOTROOTPATH"]=rootdir
        if os.name == "posix":
            #fails if there isn't something in here already. for PATH we'll just assume it's there on any
            #sane system
            old_ld_libpath = os.environ.get("LD_LIBRARY_PATH")
            if not old_ld_libpath:
                old_ld_libpath = ""
            os.environ["LD_LIBRARY_PATH"]=old_ld_libpath + os.pathsep + rootdir
            print "Respawning with new path"
            if not we_are_frozen():
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                os.execv(sys.executable, [sys.executable] + sys.argv[1:])
            #should not return
            sys.exit(1)
        
        elif os.name == "nt":
            os.environ["PATH"]+=os.pathsep+rootdir
    rootdir=os.environ.get("YOBOTROOTPATH")
    
    print "rootdir is", rootdir

    parser = optparse.OptionParser(usage="[options] -- [component args]")
    parser.add_option("-t", "--type", help="client, server, or agent", dest="type")
    parser.add_option("-c", "--configdir", help="configuration root directory [defaults to home]", dest="configdir")
    parser.add_option("-w", "--use-window", help="on windows, use a window for the server", action="store_true", default=False, dest="use_window")
    parser.add_option("--no-stdio", help="don't use stdout and stderr, log to a file", dest="use_log", action="store_true", default=False)
    
    options, startargs = parser.parse_args(args)
    startargs = startargs[1:]
    type = options.type
    configdir = get_yobot_dirs(options.configdir)
    os.environ["YOBOT_USER_DIR"]=configdir["config_root"]
    
    def module_wrapper(modulename):
        print "invoking", modulename
        if options.use_log:
            log_dir = get_yobot_dirs()
            #open logfile, line buffered
            sys.stdout = sys.stderr = open(os.path.join(configdir["log_dir"], type), "w", 1)
        __import__(modulename)
        m = sys.modules[modulename]
        m.startup(startargs)
    
    if type == "client":
        module_wrapper("client")
    elif type == "agent":
        module_wrapper("yobotnet")
        
    elif type == "server":
        import subprocess
        if os.name == "nt":
            #set up paths
            execname="yobot.exe"
            dep_paths = os.pathsep.join([os.path.abspath(p) for p in ("glib","purple", "purple_support")])
            print "ADDING", dep_paths, "TO PATH"
            os.environ["PATH"]+=os.pathsep
            os.environ["PATH"]+=dep_paths
            #for now, launch the process in a new window...
            if options.use_window:
                #no point in wrapping the stdout/stderr
                os.execvp("cmd", ["cmd", "/c", "start", execname] + startargs)
            else:
                f = open(os.path.join(configdir["log_dir"], type), "w", 1)
                subprocess.Popen([execname] + startargs, stdout=f, stderr=f,
                    stdin =  subprocess.PIPE)
                sys.exit(0)
            #no returning
            sys.exit(1)

        else: #posix
            execname="yobot"
        
        execname=os.path.join(rootdir, execname)
        print "invoking purple server.. " + execname
        if not options.use_log:
            os.execvpe(execname, [execname] + startargs, os.environ)
        else:
            #popen and exit
            f = open(os.path.join(configdir["log_dir"], type), "w", 1)
            subprocess.Popen([execname] + startargs, stdout=f, stderr=f)
            sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)
        
if __name__ == "__main__":
    do_start()
