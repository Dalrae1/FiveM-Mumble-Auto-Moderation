# FiveM-Mumble-Auto-Moderation



Hey guys! This is probably one of the coolest scripts I've ever made, but sadly, it does require quite a bit of setup for it to work.

What is this script?
This is NOT a resource, it's a Python script that will connect to a custom Mumble server (In this case, Grumble) and record all voice chat data. It will then transcribe that voice chat data into text, and check it against a list of words that you don't like.


(NOTE: ONLY TESTED WITH MUMBLE-VOIP ON WINDOWS x64)


Setup:


Dependancies:
You will need to download these before anything.
* [Python 3.x](https://www.python.org/downloads/)
* [Docker](https://www.docker.com/products/docker-desktop)
* [Go 1 Enviroment](https://golang.org/dl/)


2) Download the [Grumble server](https://github.com/mumble-voip/grumble) and put it in `(SERVERDIR)/Grumble Build Image/grumble`
3) Create a bat file `Build Grumble Image.bat` in `(SERVERDIR)/Grumble Build Image`
4) Copy and paste the following into the bat file: 


```
docker image rm mumble-voip/grumble --force
git clone https://github.com/mumble-voip/grumble.git
cd grumble
go get mumble.info/grumble/cmd/grumble
docker build -t mumble-voip/grumble .
```


5) Run the bat file
6) Create a bat file `Start Grumble Server Port 64738.bat`
7) Copy and paste the following into the bat file:
```
TITLE Grumble Server
SET mypath=%~dp0
docker run -v "%mypath:~0,-1%\Grumble Server:/data" -p 64738:64738 -p 64738:64738/udp mumble-voip/grumble
```
8) You should now have a functioning Grumble server in your FiveM server.
9) To use this custom server, put `MumbleSetServerAddress("SERVERIP", 64738)` into any client script, or use the config values associated with changing the address with whatever voice script you use. 
10) Check if the Grumble server is working. (IMPORTANT)
11) Install the python modules:

> pip install pymumble
> 
> pip install vosk
> 
> pip install discord_webhook
12) Follow [these](https://github.com/azlux/botamusique/wiki/Windows-dev-environment) instructions to download the Opus codec on your system
13) Download the script from [here](https://github.com/Dalrae1/FiveM-Mumble-Auto-Moderation)
14) Create a folder called "Mumble Bot" and extract the download into it
15) Download ffmpeg from [here](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z) and drag and drop ffmpeg.exe into the `Mumble Bot` directory
16) Configure the Discord webhook and the bad words to be detected by modifying DalraeMumbleBot.py
17) Run `start.bat` and ` Start Grumble Server Port 64738.bat` and it should now log all bad words into the Discord webhook.

This is EXTREMELY beta, and I probably got one of the steps above wrong.

https://youtu.be/OEH_A5ENjzQ







