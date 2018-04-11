#!/usr/bin/env python3
#   _  __________                         __        __  __  ___     __          
#  / |/ / __/ __/__________ ___ ___  ___ / /  ___  / /_/  |/  /__ _/ /_____ ____
# /    /\ \_\ \/ __/ __/ -_) -_) _ \(_-</ _ \/ _ \/ __/ /|_/ / _ `/  '_/ -_) __/
#/_/|_/___/___/\__/_/  \__/\__/_//_/___/_//_/\___/\__/_/  /_/\_,_/_/\_\\__/_/  
#Copyright (c) 2018 cheuble (https://github.com/cheuble)
#All rights reserved.
#
#This work is licensed under the terms of the MIT license.
#For a copy, see <https://opensource.org/licenses/MIT>.

#http://switchbrew.org/index.php?title=Capture_services#Notes for more info.

import os
import io
import hmac
import piexif
import binascii
from PIL import Image
from sys import argv, exit
from hashlib import sha256
from datetime import datetime

#From my testing, piexif's _dump._get_thumbnail() returns an invalid thumbnail for the Switch (it shows a "?"). What we can do though is replace it with this dirty fix.
#There's probably a better way to do it, like using a different library, but eh, it works™ ¯\_(ツ)_/¯
#From StackOverflow (Monkey Patching): https://stackoverflow.com/questions/10429547/how-to-change-a-function-in-existing-3rd-party-library-in-python
piexif._dump._get_thumbnail = lambda jpeg: jpeg #Return it as it is, no need to modify it.
	
def printHelp():
	print("Nintendo Switch Screenshot Maker by cheuble")
	print("Usage: " + argv[0] + " [options]")
	print("Options:")
	print("-h | --help				Prints this help")
	print("-k | --key				Manually sets the key (instead of loading it form key.bin)")
	print("-t | --titleid				Manually sets the Title ID of the game (Default: Home Menu)")

#https://stackoverflow.com/questions/44231209/resize-rectangular-image-to-square-keeping-ratio-and-fill-background-with-black
def resizeImage(path, sizeX, sizeY):
	size = (sizeX, sizeY)
	resizedImage  = Image.new("RGB", size, (0, 0, 0))
	originalImage = Image.open(path).convert("RGB")
	originalImage.thumbnail(size)
	width, height = originalImage.size
	resizedImage.paste(originalImage, (int((sizeX - width) / 2), int((sizeY - height) / 2)))
	return resizedImage

def getImageHmac(key, input):
	return hmac.new(key, input, sha256).digest()

#Note: Never use piexif again.
#I don't know if the Switch actually checks for all of these, but it's better to have more information.
def createJPEGExif(exifDict, makerNote, timestamp, thumbnail):
	newExifDict = exifDict.copy()
	newExifDict.update({
		"Exif": {36864: b"0230", 37121: b"\x01\x02\x03\x00", 40962: 1280, 40963: 720, 40960: b"0100", 40961: 1, 37500: makerNote},
		"0th":  {274: 1, 531: 1, 296: 2, 34665: 164, 282: (72, 1), 283: (72, 1), 306: timestamp, 271: "Nintendo co., ltd"},
		"1st":  {513: 1524, 514: 32253, 259: 6, 296: 2, 282: (72, 1), 283: (72, 1)},
		"thumbnail": thumbnail
	})
	return newExifDict
	
def processFile(fileName, key, titleID):
	date = datetime.utcnow()
	outputFolder = date.strftime("SD/Nintendo/Album/%Y/%m/%d/")
	ind = 0
	while os.path.isfile(outputFolder + date.strftime("%Y%m%d%H%M%S") + "{:02d}".format(ind) + "-" + titleID + ".jpg"):
		ind += 1
		if ind > 99:
			date = datetime.utcnow()
			outputFolder = date.strftime("SD/Nintendo/Album/%Y/%m/%d/")
			ind = 0
	outputPath = outputFolder + date.strftime("%Y%m%d%H%M%S") + "{:02d}".format(ind) + "-" + titleID + ".jpg"
	os.makedirs(outputFolder, exist_ok=True)
	inputImage  = io.BytesIO()
	outputImage = io.BytesIO()
	thumbnail   = io.BytesIO()
	resizeImage(fileName, 1280, 720).save(inputImage, "JPEG", quality = 100) #The screenshots must have a size of 1280x720
	resizeImage(fileName, 320,  180).save(thumbnail,  "JPEG", quality = 100) #The thumbnails (at least on my screenshots) have a size of 320x180
	makerNoteZero  = b"\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x10\x00" + bytes.fromhex(titleID)
	timestamp = date.strftime("%Y:%m:%d %H:%M:%S")
	exifData = piexif.dump(createJPEGExif(piexif.load(inputImage.getvalue()), makerNoteZero, timestamp, thumbnail.getvalue()))
	piexif.insert(exifData, inputImage.getvalue(), outputImage)
	makerNote  = b"\x00\x00\x00\x00\x00\x00\x10\x00" + getImageHmac(key, outputImage.getvalue())[:16] + b"\x01\x00\x10\x00" + bytes.fromhex(titleID)
	outputBytes = outputImage.getvalue().replace(makerNoteZero, makerNote)
	with open(outputPath, "wb") as file:
		file.write(outputBytes)
	
if __name__ == "__main__":
	key = b"\x00"
	titleId = "57B4628D2267231D57E0FC1078C0596D" #Default TitleID: Home Menu
	for i in range(len(argv)):
		if argv[i] == "--help" or argv[i] == "-h":
			printHelp()
			exit(0)
		elif argv[i] == "--key" or argv[i] == "-k":
			if i + 1 < len(argv):
				try:
					key = bytes.fromhex(argv[i+1])
				except ValueError:
					print("Error! Invalid Key!\n\n")
					printHelp()
					exit(1)
				i+=1
		elif argv[i] == "--titleid" or argv[i] == "-t":
			if i + 1 < len(argv):
				if len(argv[i+1]) == 0x20:
					titleId = argv[i+1].upper()
					i+=1
	#Get the "Nintendo Switch capsrv screenshot HMAC secret" key on SciresM's pastebin
	if len(key) != 0x20:
		if not os.path.isfile("key.bin"):
			print("Error! You need to provide the Nintendo Switch capsrv screenshot HMAC secret!\n\n")
			printHelp()
			exit(1)
		with open("key.bin", "rb") as file:
			key = file.read(0x20)
	print("Key: " + str(binascii.hexlify(key))[2:66].upper())
	os.makedirs("input", exist_ok=True)
	if len(os.listdir("input")) == 0:
		print("Input folder is empty!\n\n")
		exit(1)
	for fileName in os.listdir("input"):
		print("Processing file " + fileName)
		processFile("input/" + fileName, key, titleId)
	print("Done!")