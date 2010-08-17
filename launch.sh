#!/bin/sh
#./yobot &

urxvt -hold -title "purple" -e ./yobot 0 & yobot_pid=$!
sleep 0.5
PYTHONPATH+=:$PWD/py urxvt -hold -title "yobot agent" -e py/yobotnet.py -s & relay_pid=$!
sleep 0.5
PYTHONPATH+=:$PWD/py urxvt -hold -title "yobot client" -e py/client.py & client_pid=$!

trap "kill $yobot_pid; pkill yobot" SIGINT SIGSTOP SIGQUIT
trap -p
wait
echo "EXITING"
