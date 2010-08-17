#!/bin/sh
git remote add origin ssh://mnunberg@yobot.git.sourceforge.net/gitroot/yobot/yobot
git config branch.master.remote origin
git config branch.master.merge refs/heads/master
git push origin master
