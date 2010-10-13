#!/bin/sh
LD_LIBRARY_PATH=$PWD
#urxvt -hold -title "purple" -e ./yobot 1 & yobot_pid=$!
#sleep 0.5
#urxvt -hold -title "GDB:Purple" -e gdb yobot $(pgrep yobot) & gdb_pid=$!
#sleep 0.5
#PYTHONPATH+=:$PWD/py urxvt -hold -title "yobot agent" -e py/yobotnet.py -s & relay_pid=$!
#sleep 0.5
#PYTHONPATH+=:$PWD/py urxvt -hold -title "yobot client" -e py/client.py & client_pid=$!

python="/usr/bin/env python "
if $(uname -s |grep -q Darwin); then
	python="arch -i386 /usr/bin/env python "
fi
ulimit -c $((1024**3))
$python py/yobotnet.py & relay_pid=$!
#sleep 1
$python py/client.py -p foo  -p gui_main -p triviabot & client_pid=$!
#sleep 1
./yobot --debug=1 & yobot_pid=$!

trap "kill $yobot_pid; kill $relay_pid; pkill yobot; kill $client_pid" SIGINT SIGSTOP SIGQUIT
trap -p
wait
echo "EXITING"
