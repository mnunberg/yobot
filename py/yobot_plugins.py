#!/usr/bin/env python
from yobot_interfaces import component_registry
import os
import sys

#both of these require an X server
have_gui = True
if "posix" in os.name:
    if "darwin" not in sys.platform:
        have_gui = True if os.environ.get("DISPLAY") else False

if have_gui:
    from gui.qyobot import YobotGui
    component_registry.register_plugin(YobotGui)
    from triviabot.triviabot import TriviaPlugin
    component_registry.register_plugin(TriviaPlugin)
else:
    print "not importing gui_main and triviabot modules. is DISPLAY set?"
#register the plugins..