@echo off
py -m ensurepip
cls
IF %ERRORLEVEL% == 0 (
    echo python exists!
) ELSE (
    echo python does not exist, installing...
    resources\python.exe -quiet
    cls
    echo Python installed, please restart program.
    pause
    exit
)
py resources/main.py

IF %ERRORLEVEL% == 0 (
   echo Requirements installed!
) ELSE (
   echo Requirements not installed installing...
   py -m pip install -r resources/requirements.txt
   py resources/main.py
)