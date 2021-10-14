import time
import os
from vosk import Model, KaldiRecognizer
import json
import re
from discord_webhook import DiscordWebhook
import pymumble_py3
from pymumble_py3.constants import *
import wave

badText = ["nigger", "gringo", "faggot", "retard", "queer", "ass ", "barely legal", "cunt", "fag ", "lolita", "under aged", "nigga", "pedophile", "nazi", "swastika", "whore", "tranny", "ham mafia"]
badDiscordWebhook = 'https://discord.com/api/webhooks/896657882236461056/u7G0u58hpPi5GJkhlqQOo2ugZ7He0GVyHJDrlbf3HMfmxmt25uX-oAU_x_3XSaLuaOMc' # This webhook will log any recording that includes anything in badText
goodDiscordWebhook = 'https://discord.com/api/webhooks/896791628948332604/dL7_aIZhaaPcaMepxDPOgcUv8qKdCyAz99f4KzDPpKXI8hP0Q5U1gr1Moxov9-iJMzaZ' # This webhook will log all recordings

def ConvertToMono(filename):
	newFilename = filename[0:-4]+"-mono"+filename[-4:]
	os.system("ffmpeg.exe -y -i \""+filename+"\" -ac 1 \""+newFilename+"\"")
	return newFilename

def IsSpeechBad(text):
	badTextsDetected = []
	for bad in badText:
		if bad.lower() in text.lower():
			badTextsDetected.append(bad)

	if len(badTextsDetected) > 0:
		return badTextsDetected
	else:
		return False

def LogToDiscordBad(username, sentence, badSpeech, clipFilename):
	if badDiscordWebhook != "":
		webhook = DiscordWebhook(url=badDiscordWebhook, rate_limit_retry=True, content="\""+sentence+"\", Detected bad text: "+(', '.join(badSpeech)))
		with open(clipFilename, "rb") as f:
			webhook.add_file(file=f.read(), filename=username+'.mp3')
		response = webhook.execute()

def LogToDiscordGood(username, sentence, clipFilename):
	if goodDiscordWebhook != "":
		webhook = DiscordWebhook(url=goodDiscordWebhook, rate_limit_retry=True, content="\""+sentence+"\"")
		with open(clipFilename, "rb") as f:
			webhook.add_file(file=f.read(), filename=username+'.mp3')
		response = webhook.execute()

def ResultToText(result):
	jsonResult = json.loads(result)
	resultString = ""
	for i in jsonResult:
		if isinstance(jsonResult[i], str):
			resultString = resultString+jsonResult[i]+". "
	return resultString

def TranscribeSpeech(filename):
	wf = wave.open(filename, "rb")
	resultString = ""
	model = Model(".\\modelSmall")
	recognizer = KaldiRecognizer(model, wf.getframerate())
	recognizer.SetWords(True)
	while True:
		data = wf.readframes(4000)
		if len(data) == 0:
			break
		if recognizer.AcceptWaveform(data):
			resultString = resultString+ResultToText(recognizer.Result())
	resultString = resultString+ResultToText(recognizer.FinalResult())
	return resultString

class MumbleBot:
	def __init__(self):
		self.SpeakingUsers = {}
		self.mumble = pymumble_py3.Mumble("localhost", "Botrae",64738,reconnect=True)
		self.mumble.set_receive_sound(True)
		self.mumble.start()
		self.mumble.is_ready()
		self.loop()

	def loop(self):
		while self.mumble.is_alive():
			try:
				for user in self.mumble.users.values():
					userID = user.get_property("session")
					userName = user.get_property("name")
					if user.sound.is_sound(): # User is currently speaking
						if userID not in self.SpeakingUsers:
							audioFilename = os.path.join(os.getcwd(), "%s %s" % (userName, time.strftime("%m %d %Y - %I %M %S %p")))
							self.SpeakingUsers[userID] = {}
							self.SpeakingUsers[userID]["StartTime"] = time.time()
							self.SpeakingUsers[userID]["SoundFile"] = WaveFile(audioFilename)

						sound = user.sound.get_sound()
						self.SpeakingUsers[userID]["SoundFile"].write(sound.pcm)
						self.SpeakingUsers[userID]["LastSound"] = sound.time
					else:
						if userID in self.SpeakingUsers:
							if time.time()-self.SpeakingUsers[userID]["LastSound"] > 1.0: #Hasn't recieved a sound data in 1s
								self.SpeakingUsers[userID]["SoundFile"].close()
								filename = self.SpeakingUsers[userID]["SoundFile"].name
								newFilename = ConvertToMono(filename)
								whatWasSaid = TranscribeSpeech(newFilename)
								if re.search("[a-zA-Z]", whatWasSaid):
									badText = IsSpeechBad(whatWasSaid)
									if badText:
										LogToDiscordBad(userName, whatWasSaid, badText, filename)
									else:
										LogToDiscordGood(userName, whatWasSaid, filename)
								else:
									os.remove(newFilename)
								os.remove(filename)
								del self.SpeakingUsers[userID]
			except RuntimeError:
				pass

class WaveFile():
	def __init__(self, name):
		self.name = name
		self.file_obj = None
		self.name += ".wav"
		self.file_obj = wave.open(self.name, "wb")
		self.file_obj.setparams((2, 2, 24000, 0, 'NONE', 'not compressed'))

	def write(self, data):
		self.file_obj.writeframes(data)

	def close(self):
		self.file_obj.close()

MumbleBot()
