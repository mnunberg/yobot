#!/bin/sh
LD_LIBRARY_PATH=$PWD
#urxvt -hold -title "purple" -e ./yobot 1 & yobot_pid=$!
#sleep 0.5
#urxvt -hold -title "GDB:Purple" -e gdb yobot $(pgrep yobot) & gdb_pid=$!
#sleep 0.5
#PYTHONPATH+=:$PWD/py urxvt -hold -title "yobot agent" -e py/yobotnet.py -s & relay_pid=$!
#sleep 0.5
#PYTHONPATH+=:$PWD/py urxvt -hold -title "yobot client" -e py/client.py & client_pid=$!
ulimit -c 16384
./yobot 1 & yobot_pid=$!
#sleep 0.5
#urxvt -hold -title "GDB:Purple" -e gdb ./yobot -x gdbcmds & gdb_pid=$!
sleep 0.5
py/yobotnet.py -s & relay_pid=$!
sleep 0.5
py/client.py & client_pid=$!
trap "kill $yobot_pid; kill $relay_pid; pkill yobot; kill $client_pid" SIGINT SIGSTOP SIGQUIT
trap -p
wait
echo "EXITING"
