#!/usr/bin/env python2

import cv2
import numpy as np
import math
import os
import sys

n = 8 # Frames to go back to compare to
blend = 0.01 # Fade older diffs out with e^blend

# Das Rumrechnen zum ein- und ausfaden ist ganz grosses gefrikel. Ich wuerde
# das gerne konfigurierbar machen, habe aber zu viel Angst, dabei Sachen kapput
# zu machen und diese sehr lange debuggen zu muessen.
# Daher:
# Zum ein- und ausfaden jeweils 50 Frames Erkennungszeit, dann wird mit einem
# Offset zur ersten Bewegung von 25 Frames ueber 25 Frames linear ein- bzw.
# ausgefadet.
#
# Das Programm spuckt in derzeitiger Konfiguration rohe rgb24-Frames aus, die
# von ffmpeg encodiert werden koennen. Anders habe ich unter Linux keine Ausgabe
# in sinnvolle Codecs hinbekommen. Andere Ausgaben stehen ueber die
# *Writer-Klassen (s.u.) zur Verfuegung.
# Die Ausgabe des RAWWriter laesst sich wie folgt verarbeiten:
# ./diff.py infile.MTS | ffmpeg -f rawvideo -s 1280x1024 -pix_fmt bgr24 -r 25 -i - -c:v qtrle outfile.mov

#vid = cv2.VideoCapture(0)
vid = cv2.VideoCapture(sys.argv[1])

#last=None
lastdiff = None
frames = []
cn = -1

blocktime = 0
#visible = True
visible = None
change = False

cv2.namedWindow("Frame")
cv2.namedWindow("Gray")
cv2.namedWindow("Diff")
cv2.namedWindow("Thresh")

#cv2.waitKey(1)
#raw_input()

class BufferWriter(object):
	def __init__(self, num_frames, writer):
		self.writer = writer
		self.num_frames = num_frames
		self.ringbuffer = []
		for i in range(self.num_frames):
			self.ringbuffer.append(None)
		self.pos = 0

	def incpos(self):
		self.pos = (self.pos+1)%self.num_frames

	def dump(self):
		frame = self.ringbuffer[self.pos]
		if frame is not None:
			self.writer(frame)

	def write(self, frame):
		self.incpos()
		self.dump()
		self.ringbuffer[self.pos] = frame

	def get(self, age):
		return self.ringbuffer[(self.pos-age)%self.num_frames]

	def overwrite(self, frame, age):
		self.ringbuffer[(self.pos-age)%self.num_frames] = frame

	def writeall(self):
		for i in range(self.num_frames):
			self.incpos()
			self.dump()

class PNGWriter(object):
	def __init__(self, outdir):
		self.outdir = outdir
		self.count = 0
		
	def write(self, frame):
		cv2.imwrite(os.path.join(self.outdir, "%07d.png" % self.count), frame,(cv2.cv.CV_IMWRITE_PNG_COMPRESSION, 0))
		self.count+=1

class OpenCVWriter(object):
	def __init__(self, outfile):
		self.outvid = cv2.VideoWriter(outfile, cv2.cv.CV_FOURCC("L","A","G","S"), 25, (1280,1024))
		
	def write(self, frame):
		self.outvid.write(frame)

class RAWWriter(object):
	def write(self, frame):
		sys.stdout.write( frame.tostring() )

#writer = PNGWriter("pngdir")
#writer = OpenCVWriter("out.avi")
writer = RAWWriter()
bwriter = BufferWriter(100, writer.write)

while True:
	(grabbed, frame)=vid.read()
	if not grabbed:
		break
	frame = cv2.resize(frame, (800,450))
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (0, 0), 1)
#	if last is None:
#		last = gray
	if cn == -1:
		for cn in range(n):
			frames.append(gray)
		cn = 0
	frames[(cn-1)%n] = gray
#	frameDelta = cv2.absdiff(last, gray)
	frameDelta = cv2.absdiff(frames[cn], gray)
	if lastdiff is None:
		lastdiff = frameDelta
	frameDelta += lastdiff*math.exp(-blend)
	thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
	(cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	blocked = False
	for c in cnts:
		if cv2.contourArea(c) < 5:
			continue
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		cv2.circle(frame, (x,y), 5, (0,0,255), 2)
		if x < 464:
			blocked = True
	if visible is None:
		visible = not blocked
	if blocked and blocktime < 50:
		if blocktime < 0:
			blocktime = 0
		blocktime+=1
	elif not blocked and blocktime > -50:
		if blocktime > 0:
			blocktime = 0
		blocktime-=1
	if visible and blocktime == 50:
		if visible: change = True
		visible = False
	if not visible and blocktime == -50:
		if not visible: change = True
		visible = True
	
	if visible:
		bwriter.write(np.full((1024,1280, 3), 255, np.uint8))
	else:
		bwriter.write(np.full((1024,1280, 3), 0, np.uint8))
	
	if not visible and change:
		for i in range(25):
			oldimg = bwriter.get(100-i)
			if oldimg is None:
				continue
			bwriter.overwrite(oldimg - int(255*(i/25.0)) , 100-i)
		for i in range(100-25+1):
			if bwriter.get(i) is None:
				continue
			bwriter.overwrite(np.full((1024,1280, 3), 0, np.uint8), i)
	elif visible and change:
		for i in range(25):
			oldimg = bwriter.get(i)
			if oldimg is None:
				continue
			bwriter.overwrite(oldimg + int(255*((25-i)/25.0)) , i)
	if change: change = False
	
	cv2.drawContours(frame, cnts, -1, (255, 0, 0), 2)
	cv2.imshow("Frame", frame )
	cv2.imshow("Gray", gray )
	cv2.imshow("Diff", frameDelta)
	cv2.imshow("Thresh", thresh )
	cv2.waitKey(1)
#	last=gray
	cn = (cn+1)%n

bwriter.writeall()
