import time, os, json, re, wave, struct, math, random
from vosk import Model, KaldiRecognizer, SetLogLevel
from discord_webhook import DiscordWebhook
from dependancies import pymumble_py3
from threading import Thread
import numpy as np
SetLogLevel(-1)


badText = ["nigger", "gringo", "faggot", "retard", "fag ", "nigga"]

# Mumble address to connect to
host = "127.0.0.1"

#Mumble port to connect to
port = 30120


# This webhook will log any recording that includes anything in badText. Replace with False to disable webhook.
badDiscordWebhook = "https://discord.com/api/webhooks/898037470061527091/bBvnUJ49YiwQsbCRa2vEkDhqGYNF9_98tkUwTldzUvtUvpVBAXT6HlTVF-muIzPjl6bU"

# This webhook will log all recordings. Replace with False to disable webhook.
goodDiscordWebhook = "https://discord.com/api/webhooks/898037356832112640/wemzZxr20GwfEIjP-n6m6ZM6g-xQT_d9Dwhq1WrWt-U1imgtQQeUl1hC0VnzVVcNzvOv"

# Local path to save audio. Replace with False to disable saving locally.
localAudioPath = "recordings/" 

# Voice model to use when transcribing speech. Replace with False to disable transcriptions.
voiceModel = ".\\modelSmall"






# Do not modify
BITRATE = 48000/2
MONO_CHUNK_SIZE = BITRATE * 2 / 1000
STEREO_CHUNK_SIZE = MONO_CHUNK_SIZE * 2 
silent = b"\x00" * int(STEREO_CHUNK_SIZE)

def ConvertToMono(filename):
	channel = 0
	wav = wave.open(filename)
	# Read data
	nch   = wav.getnchannels()
	depth = wav.getsampwidth()
	wav.setpos(0)
	sdata = wav.readframes(wav.getnframes())

	# Extract channel data (24-bit data not supported)
	typ = { 1: np.uint8, 2: np.uint16, 4: np.uint32 }.get(depth)
	if not typ:
		raise ValueError("sample width {} not supported".format(depth))
	if channel >= nch:
		raise ValueError("cannot extract channel {} out of {}".format(channel+1, nch))
	data = np.frombuffer(sdata, dtype=typ)
	ch_data = data[channel::nch]

	wavparams = wav.getparams()
	wav.close()

	outwav = wave.open(filename, 'w')
	outwav.setparams(wavparams)
	outwav.setnchannels(1)
	outwav.writeframes(ch_data.tobytes())
	outwav.close()
	return filename



def ConvertToMonoOld(filename):
	newFilename = filename[0:-4]+"-mono"+filename[-4:]
	os.system("ffmpeg.exe -hide_banner -loglevel error -y -i \""+filename+"\" -ac 1 \""+newFilename+"\"")
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
	if badDiscordWebhook and badDiscordWebhook != "":
		webhook = DiscordWebhook(url=badDiscordWebhook, rate_limit_retry=True, content=username+": \""+sentence+"\", Detected bad text: "+(', '.join(badSpeech)))
		with open(clipFilename, "rb") as f:
			webhook.add_file(file=f.read(), filename=username+'.mp3')
		response = webhook.execute()

def LogToDiscordGood(username, sentence, clipFilename):
	if goodDiscordWebhook and goodDiscordWebhook != "":
		webhook = DiscordWebhook(url=goodDiscordWebhook, rate_limit_retry=True, content=username+": \""+sentence+"\"")
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
	if voiceModel:
		ConvertToMono(filename)
		wf = wave.open(filename, "rb")
		resultString = ""
		model = Model(voiceModel)
		recognizer = KaldiRecognizer(model, wf.getframerate())
		recognizer.SetWords(True)
		while True:
			data = wf.readframes(400000)
			if len(data) == 0:
				break
			if recognizer.AcceptWaveform(data):
				resultString = resultString+ResultToText(recognizer.Result())
		resultString = resultString+ResultToText(recognizer.FinalResult())
		wf.close()
		return resultString
	return "Transcription Disabled."

def ProcessAudio(userName, userID, filename):
	whatWasSaid = TranscribeSpeech(filename)
	print(userName+": \""+whatWasSaid+"\"")
	if re.search("[a-zA-Z]", whatWasSaid):
		badText = IsSpeechBad(whatWasSaid)
		if badText:
			LogToDiscordBad(userName, whatWasSaid, badText, filename)
		else:
			LogToDiscordGood(userName, whatWasSaid, filename)
	if not localAudioPath:
		self.SpeakingUsers[userID]["SoundFile"].close()
		os.remove(filename)



class MumbleBot:

	def channelCreated(self, channel):
		self.mumble.users.myself.add_listening_channels([channel["channel_id"]])

	def __init__(self):
		self.SpeakingUsers = {}
		
		self.mumble = pymumble_py3.Mumble(host, "Bot",port=port,reconnect=True, debug=False)
		self.mumble.set_receive_sound(True)
		self.mumble.start()
		self.mumble.is_ready()

		channelIds = []
		for channel in self.mumble.channels.values():
			channelIds.append(channel["channel_id"])
		self.mumble.users.myself.add_listening_channels(channelIds)

		self.mumble.callbacks.set_callback(pymumble_py3.constants.PYMUMBLE_CLBK_CHANNELCREATED, self.channelCreated)

		self.loop()

	def loop(self):

		while self.mumble.is_alive():
			try:
				for user in self.mumble.users.values():
					userID = user.get_property("session")
					userName = user.get_property("name")
					audioFilename = "%s %s" % (userName, time.strftime("%m %d %Y - %I %M %S %p"))
					audioFilename = "".join(x for x in audioFilename if x.isalnum()) #Sterilize filename
					if localAudioPath:
						audioFilename = localAudioPath+audioFilename
					if user.sound.is_sound(): # User is currently speaking
						if userID not in self.SpeakingUsers:
							
							self.SpeakingUsers[userID] = {}
							self.SpeakingUsers[userID]["StartTime"] = time.time()
							self.SpeakingUsers[userID]["SoundFile"] = WaveFile(audioFilename)
						
						sound = user.sound.get_sound()
						if "LastSound" in self.SpeakingUsers[userID]: # Write silence. May be wrong because of delay between packets
							silenceTime = (time.time()-self.SpeakingUsers[userID]["LastSound"])*1000
							if silenceTime > 200: 
								self.SpeakingUsers[userID]["SoundFile"].write(silent*int(silenceTime))
								
						self.SpeakingUsers[userID]["SoundFile"].write(sound.pcm)
						self.SpeakingUsers[userID]["LastSound"] = time.time()
					else:
						if userID in self.SpeakingUsers:
							if time.time()-self.SpeakingUsers[userID]["LastSound"] > 1.0: #Hasn't recieved a sound data in 1s
								self.SpeakingUsers[userID]["SoundFile"].close()
								filename = self.SpeakingUsers[userID]["SoundFile"].name
								thread = Thread(target = ProcessAudio, args = (userName, userID, filename))
								thread.start()
								del self.SpeakingUsers[userID]
			except RuntimeError:
				pass
			except AttributeError:
				pass

class WaveFile():
	def __init__(self, name):
		self.name = name
		self.file_obj = None
		self.name += ".wav"
		self.file_obj = wave.open(self.name, "wb")
		self.file_obj.setparams((2, 2, BITRATE, 0, 'NONE', 'not compressed'))

	def write(self, data):
		self.file_obj.writeframes(data)

	def close(self):
		self.file_obj.close()

MumbleBot()
