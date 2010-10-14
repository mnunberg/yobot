#!/bin/sh

#simple wrapper around wc which will tell me the lines of all *my* code... should be fun. also prints out the files that i've written...
file_list=$(ls -1 \
main.c protoclient.{c,h} \
yobot_blist.{c,h} \
yobot_conversation.c \
yobot_log.{c,h} \
yobotproto.h \
yobotproto.i \
yobot_request.c \
yobot_ui.{c,h} \
yobot_uiops.c \
yobotutil.{c,h} \
win32/{fn_override.c,\
fn_override.h,\
yobot_win32.c,\
yobot_win32.h} \
py/{account,client_config,client_support,debuglog,msglogger,startyobot,\
yobotclass,yobot_interfaces,yobotnet,yobotops,yobot_plugins}.py \
py/gui/{config_dialog,gui_util,html_fmt,qyobot,yahoo_captcha,chatwindow}.py \
py/triviabot/{gui_new,triviabot}.py)
wc -l $file_list | sort -n
sloccount $file_list
