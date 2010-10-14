@set yobotroot=%cd%
@set pidginroot=C:\Program Files\Pidgin
@set sleep=%yobotroot%\tools\_sleep.exe
@set PATH=%PATH%;%pidginroot%;%pidginroot%\Plugins;%yobotroot%;%yobotroot%\contrib
@set LOGPATH=Z:\
start "Purple" cmd /c "%yobotroot%\yobot.exe -d 1 > %LOGPATH%\purple.log% 2>&1"
rem %sleep% 1000
start "Yobot Agent" cmd /c "C:\python26\python.exe %yobotroot%\py\yobotnet.py"
rem %sleep% 1000
start "QYobot" cmd /c "C:\python26\python.exe %yobotroot%\py\client.py -p triviabot -p gui_main"
