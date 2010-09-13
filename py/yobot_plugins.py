#!/usr/bin/env python
from yobot_interfaces import component_registry
from gui.qyobot import YobotGui
from triviabot.triviabot import TriviaPlugin

component_registry.register_plugin(YobotGui)
component_registry.register_plugin(TriviaPlugin)
#register the plugins..