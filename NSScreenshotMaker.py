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
from sys import exit
from PIL import Image
from hashlib import sha256
from datetime import datetime
from argparse import ArgumentParser

#Fixing the "archive bit" that causes problems to some users
try:
	import win32file
	import win32con
	def removeArchiveAttribute(fileName):
		win32file.SetFileAttributes(fileName, win32file.GetFileAttributes(fileName) & ~win32con.FILE_ATTRIBUTE_ARCHIVE)
except ImportError:
	def removeArchiveAttribute(fileName):
		pass

#From my testing, piexif's _dump._get_thumbnail() returns an invalid thumbnail for the Switch (it shows a "?"). What we can do though is replace it with this dirty fix.
#There's probably a better way to do it, like using a different library, but eh, it works™ ¯\_(ツ)_/¯
#From StackOverflow (Monkey Patching): https://stackoverflow.com/questions/10429547/how-to-change-a-function-in-existing-3rd-party-library-in-python
piexif._dump._get_thumbnail = lambda jpeg: jpeg #Return it as it is, no need to modify it.

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

def processFile(fileName, key, titleID, baseOutputFolder):
	date = datetime.utcnow()
	outputFolder = baseOutputFolder + date.strftime("/Nintendo/Album/%Y/%m/%d/")
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
	resizeImage(fileName, 320,  180).save(thumbnail,  "JPEG", quality = 40)  #The thumbnails (at least on my screenshots) have a size of 320x180
	makerNoteZero  = b"\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x10\x00" + bytes.fromhex(titleID)
	timestamp = date.strftime("%Y:%m:%d %H:%M:%S")
	exifData = piexif.dump(createJPEGExif(piexif.load(inputImage.getvalue()), makerNoteZero, timestamp, thumbnail.getvalue()))
	piexif.insert(exifData, inputImage.getvalue(), outputImage)
	makerNote  = b"\x00\x00\x00\x00\x00\x00\x10\x00" + getImageHmac(key, outputImage.getvalue())[:16] + b"\x01\x00\x10\x00" + bytes.fromhex(titleID)
	outputBytes = outputImage.getvalue().replace(makerNoteZero, makerNote)
	with open(outputPath, "wb") as file:
		file.write(outputBytes)
	removeArchiveAttribute(baseOutputFolder)
	removeArchiveAttribute(outputPath)
	
if __name__ == "__main__":
	parser = ArgumentParser(description='Create usable screenshots to be shown on the Nintendo Switch.')
	#Get the Nintendo Switch capsrv screenshot HMAC secret" key on SciresM's pastebin
	parser.add_argument('-k', '--key', help='Set the HMAC key (instead of loading it from key.bin)')
	#Default TitleID: Home Menu
	parser.add_argument('-t', '--titleid', default="57B4628D2267231D57E0FC1078C0596D", help='Set the title ID of the app (default is HOME menu)')
	parser.add_argument('-i', '--input',  default='input', help='Set the input folder')
	parser.add_argument('-o', '--output', default='SD',    help='Set the output folder')
	args = parser.parse_args()

	if args.key:
		try:
			key = bytes.fromhex(args.key)
			if len(key) != 0x20:
				print("Error! Invalid Key!")
				exit(1)
		except ValueError:
			print("Error! Invalid Key!")
			exit(1)
	else:
		if not os.path.isfile("key.bin"):
			print("Error! You need to provide the Nintendo Switch capsrv screenshot HMAC secret!")
			exit(1)
		with open("key.bin", "rb") as file:
			key = file.read(0x20)

	if sha256(key).hexdigest() != "e9735dae330300b8bb4b5892c8178f5d57daa32d7b5ef5d15f14491800ce4750": #SHA256 of the key
		print("Error! Invalid Key!")
		exit(1)

	os.makedirs(args.input, exist_ok=True)
	if len(os.listdir(args.input)) == 0:
		print("Input folder is empty!")
		exit(1)
	for fileName in os.listdir(args.input):
		print("Processing file " + fileName)
		processFile(args.input + "/" + fileName, key, args.titleid, args.output)

	print("Done!")