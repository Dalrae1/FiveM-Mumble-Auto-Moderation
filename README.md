# FiveM-Mumble-Auto-Moderation

Hey guys! This is probably one of the coolest scripts I've ever made, but sadly, it does require quite a bit of setup for it to work.

What is this script?
*This is NOT a resource*, it's a Python script that will connect to a custom Mumble server (In this case, Grumble) and record all voice chat data. It will then transcribe that voice chat data into text, and check it against a list of words that you don't like.

**Setup:**
1. Configure the configuration values in the `DalraeMumbleBot.py` script
2. Run the `Setup.bat` file, which will install all dependancies
3. Run the `Start Mumble Bot.bat` file, which will configure opus and run the bot
