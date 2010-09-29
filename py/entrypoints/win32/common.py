import os
import sys
import time
import subprocess

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

#modify path...
from os import environ, path, execv
environ["PATH"]+=path.pathsep + module_path() + path.pathsep


def run(client_args=[], invoke_client=False,
        server_args=[], invoke_server=False,
        agent_args=[], invoke_agent=False,
        init_args=[],console=False):

    init_args += ["--"]
    console_exec=[] if not console else ["cmd", "/c", "start"]

    if invoke_server:
        subprocess.Popen(console_exec + ["startyobot.exe", "--type", "server"] + init_args + server_args)
        time.sleep(0.5)
    if invoke_agent:
        subprocess.Popen(console_exec + ["startyobot.exe", "--type", "agent"] + init_args + agent_args)
        time.sleep(0.5)
    if invoke_client:
        subprocess.Popen(console_exec + ["startyobot.exe", "--type", "client"] + init_args + client_args)
