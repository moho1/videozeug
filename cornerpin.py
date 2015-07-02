#!/usr/bin/env python2

# Usage:
# ./cornerpin.py ulx uly urx ury llx lly lrx lry invid1.MTS [invid....MTS] | ffmpeg ...
# ffmpeg Command can be, for example:
# ffmpeg -f rawvideo -s 1920x1080 -pix_fmt bgr24 -r 25 -i - -pix_fmt yuv420p -c:v libx264 -an -preset:v ultrafast out.mov
# ffmpeg -f rawvideo -s 1920x1080 -pix_fmt bgr24 -r 25 -i - -c:v mjpeg -an out.avi

import sys

import cv2
import numpy as np

def genMapFromHom(H, size):
	(ys,xs) = size
	xmap = np.empty((ys,xs), dtype=np.float32)
	ymap = np.empty((ys,xs), dtype=np.float32)
	xtmap = np.empty((ys,xs), dtype=np.float32)
	ytmap = np.empty((ys,xs), dtype=np.float32)
	for y in range(int(ys)):
		for x in range(int(xs)):
			xtmap[y,x] = x
			ytmap[y,x] = y
	xmap = cv2.warpPerspective(xtmap, H, (int(xs),int(ys)), flags=cv2.INTER_CUBIC)
	ymap = cv2.warpPerspective(ytmap, H, (int(xs),int(ys)), flags=cv2.INTER_CUBIC)
	return (xmap, ymap)

def stretchimg(img, xmap, ymap):
	return cv2.remap(img, xmap, ymap, cv2.INTER_LINEAR)

def cpvid(cvreader, writefunc, xmap, ymap):
	good, mat = cvreader.read()
	while good:
#		cv2.imshow("In", mat)
		img = stretchimg(mat, xmap, ymap)
#		sys.stderr.write(str(mat.shape))
#		sys.stderr.write(str(img.shape))
#		cv2.imshow("Out", img)
		writefunc(img)
#		cv2.waitKey(1)
#		print img
#		print img.dtype
#		cv2.imshow("Default",img)
#		cv2.waitKey(1)
		good, mat = cvreader.read()

class RAWVidWriter(object):
	def write(self, frame):
		sys.stdout.write(frame.tostring())

class OpenCVVidWriter(object):
	def __init__(self, filename):
		self.writer = cv2.VideoWriter(filename)
		self.write = self.writer.write

if __name__ == "__main__":
	cvreader = cv2.VideoCapture(sys.argv[9])
	H = cv2.getPerspectiveTransform(
			np.array([
				(0,0),
				(cvreader.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH),0),
				(0,cvreader.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)),
				(cvreader.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH),cvreader.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
				], dtype=np.float32),
			np.array([
				(sys.argv[1],sys.argv[2]), # ulx, uly
				(sys.argv[3],sys.argv[4]), # urx, ury
				(sys.argv[5],sys.argv[6]), # llx, lly
				(sys.argv[7],sys.argv[8])  # lrx, lry
				], dtype=np.float32))
	#sys.stderr.write(str(H))
	(xmap, ymap) = genMapFromHom(H, (cvreader.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT),cvreader.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)))
	
	write = RAWVidWriter().write
	
	for vid in sys.argv[9:]:
		cvreader = cv2.VideoCapture(vid)
		cpvid(cvreader, write, xmap, ymap)
