@echo off
TITLE Mumble Bot
SET mypath=%~dp0
SET PATH=%PATH%;%mypath%dependancies

goto :DOES_PYTHON_EXIST

:DOES_PYTHON_EXIST
py --version 2>NUL
if errorlevel 1 goto :PYTHON_DOES_NOT_EXIST
goto :PYTHON_DOES_EXIST

:PYTHON_DOES_NOT_EXIST
echo Python is not installed. Install Python 3.10
start "" "https://www.python.org/downloads/windows/"
goto :EOF

:PYTHON_DOES_EXIST
for /f "delims=" %%V in ('where py') do @set pythonpath=%%V
for /f "delims=" %%V in ('%pythonpath% --version') do @set pythonversion=%%V 
echo Using %pythonversion% at %pythonpath%

%pythonpath% "%mypath%DalraeMumbleBot.py"

echo Process Terminated.
pause
