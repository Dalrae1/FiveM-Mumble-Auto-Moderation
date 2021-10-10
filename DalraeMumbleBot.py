import time
from threading import Thread
import os
from vosk import Model, KaldiRecognizer
import wave
import json
import types
from discord_webhook import DiscordWebhook



badText = ["fuck", "shit", "idiot"]
discordWebhook = 'WEBHOOKURL'



BUFFER = 0.1
BITRATE = 24000
RESOLUTION = 10 # in ms
FLOAT_RESOLUTION = float(RESOLUTION) / 1000
MONO_CHUNK_SIZE = BITRATE * 2 * RESOLUTION / 1000
STEREO_CHUNK_SIZE = MONO_CHUNK_SIZE * 2 

import pymumble_py3
from pymumble_py3.constants import *

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

def LogToDiscord(username, badSpeech, clipFilename):
	webhook = DiscordWebhook(url=discordWebhook, rate_limit_retry=True, content="Detected bad words: "+(', '.join(badSpeech)))
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
		self.cursor_time = 0.0
		self.audioFiles = {}
		self.exit = False

		self.users = dict()

		self.mumble = pymumble_py3.Mumble("localhost", "Botrae",64738)
		self.mumble.set_loop_rate(0.005)
		self.mumble.set_application_string("Bot")
		self.mumble.callbacks.add_callback(PYMUMBLE_CLBK_CONNECTED,self.connection_cb)
		self.mumble.set_receive_sound(True)
		self.mumble.start()
		self.mumble.is_ready()
		self.loop()

	def connection_cb(self,*args):
		print("CONNECTED TO MUMBLE SERVER")


	def loop(self):
		"""Master loop""" 
		import os.path
		import audioop

		self.cursor_time=time.time()
		while self.mumble.is_alive():
			if self.cursor_time < time.time() - BUFFER:
				

				for user in self.mumble.users.values():
					base_sound = None
					userID = user.get_property("session")
					userName = user.get_property("name")
					if user.sound.is_sound():
						if userID not in self.audioFiles:
							audio_file_name = os.path.join(os.getcwd(), "%s %s" % (userName, time.strftime("%Y%m%d-%H%M%S")))
							self.audioFiles[userID] = AudioFile(audio_file_name)
						sound = user.sound.get_sound(FLOAT_RESOLUTION)
						
						if base_sound == None:
							base_sound = sound.pcm
						else:
							base_sound = audioop.add(base_sound, sound.pcm, 2)
					else:
						if userID in self.audioFiles: # Was just talking
							self.audioFiles[userID].close()
							filename = self.audioFiles[userID].name
							whatWasSaid = TranscribeSpeech(ConvertToMono(filename))
							badText = IsSpeechBad(whatWasSaid)
							if badText:
								LogToDiscord(userName, badText, filename)
							del self.audioFiles[userID]
							os.remove(filename)
							

					if base_sound:
						self.audioFiles[userID].write(base_sound)

				self.cursor_time += FLOAT_RESOLUTION
			else:
				time.sleep(FLOAT_RESOLUTION)



class AudioFile():
	"""
	Manage the audio saving, through a pipe or in a WAV file
	"""
	def __init__(self, name):
		from subprocess import Popen, PIPE
		import sys
		
		self.name = name
		self.type = None
		self.file_obj = None
		
		self.name += ".wav"
		self.file_obj = wave.open(self.name, "wb")
		self.file_obj.setparams((2, 2, BITRATE, 0, 'NONE', 'not compressed'))
		self.type = "wav"
		
	def write(self, data):
		if self.type == "pipe":
			self.file_obj.write(data)
		else:
			self.file_obj.writeframes(data)
	
	def close(self):
		self.file_obj.close()

if __name__ == "__main__":
	recbot = MumbleBot()
