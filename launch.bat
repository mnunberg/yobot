@set yobotroot=%cd%
@set pidginroot=C:\Program Files\Pidgin
@set sleep=%yobotroot%\tools\_sleep.exe
@set PATH=%PATH%;%pidginroot%;%pidginroot%\Plugins;%yobotroot%;%yobotroot%\contrib

REM CD %PIDGINROOT%
start "Purple" cmd /t:75 /c "%yobotroot%\yobot.exe 0 > Z:\winlog 2>&1"
REM %yobotroot%\tools\_sleep.exe 1000
%sleep% 1000
start "Yobot Agent" cmd /c python %yobotroot%\py\yobotnet.py -s
%sleep% 1000
REM %yobotroot%\tools\_sleep.exe 1000
start "QYobot" cmd /c python %yobotroot%\py\client.py
