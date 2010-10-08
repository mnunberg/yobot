#!/bin/sh
#This is for launching with wine. The launch.bat script will for some reason not
#work, even with removing the hard-coded paths
PURPLEPATH="C:\\Program Files\\Pidgin"
PURPLEPATH+=";$PURPLEPATH\\Gtk\\bin;Gtk\\bin"
CMD="cmd /c set PATH=%PATH%;$PURPLEPATH;%cd%; & "
logfile="logtmp"
> $logfile

function pretty_fmt() {
echo "*****************$1*******************" >> $logfile
}

pretty_fmt "launching agent"
wine $CMD python.exe py/yobotnet.py 2>&1 >> $logfile & agent_pid=$!
sleep 1
pretty_fmt "launching client"
wine $CMD python.exe py/client.py --plugin triviabot --plugin gui_main 2>&1 >> $logfile & client_pid=$!
pretty_fmt "sleeping"
sleep 4
pretty_fmt "launching yobot"
wine $CMD yobot.exe --debug=0 --mode=desktop 2>&1 >> $logfile & yobot_pid=$!

trap "kill $agent_pid $client_pid" SIGINT SIGSTOP SIGQUIT
trap -p
wait
echo "EXIT"
pretty_fmt "exiting"
