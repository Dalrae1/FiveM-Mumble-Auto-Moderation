@echo off

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
echo Found Python at %pythonpath%
%pythonpath% -m pip install vosk
%pythonpath% -m pip install protobuf==3.20.0
%pythonpath% -m pip install discord_webhook
%pythonpath% -m pip install opuslib
%pythonpath% -m pip install numpy
echo.
echo.
echo.
SETLOCAL EnableExtensions DisableDelayedExpansion
for /F %%a in ('echo prompt $E ^| cmd') do (
  set "ESC=%%a"
)
echo %ESC%[42mSetup Done. You can now launch %ESC%[4mStart Mumble Bot.bat%ESC%[0m
echo.
echo.
echo.
pause
goto :EOF
