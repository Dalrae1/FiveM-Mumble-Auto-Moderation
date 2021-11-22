@echo off
TITLE Mumble Bot
SET mypath=%~dp0
SET PATH=%PATH%;%mypath%dependancies
py "bot.py"
echo Process Terminated.
pause
