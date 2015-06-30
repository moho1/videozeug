#!/usr/bin/env python2

# Usage:
# ./cornerpin.py ulx uly urx ury llx lly lrx lry invid1.MTS [invid....MTS] | ffmpeg ...
# ffmpeg Command can be, for example:
# ffmpeg -f rawvideo -s 1920x1080 -pix_fmt bgr24 -r 25 -i - -pix_fmt yuv420p -c:v libx264 -an -preset:v ultrafast out.mov
# ffmpeg -f rawvideo -s 1920x1080 -pix_fmt bgr24 -r 25 -i - -c:v mjpeg -an out.avi

import sys

import cv2
import numpy as np

def genlinfuncs(ulx, uly, urx, ury, llx, lly, lrx, lry):
        ayu = (float(ury)-float(uly))/(float(urx)-float(ulx))
        fyu = lambda x: x * ayu + (float(uly)-(float(ulx)*ayu))

        ayl = (float(lry)-float(lly))/(float(lrx)-float(llx))
        fyl = lambda x: x * ayl + (float(lly)-(float(llx)*ayl))

        axl = (float(llx)-float(ulx))/(float(lly)-float(uly))
        fxl = lambda y: y * axl + (float(ulx)-(float(uly)*axl))

        axr = (float(lrx)-float(urx))/(float(lry)-float(ury))
        fxr = lambda y: y * axr + (float(urx)-(float(ury)*axr))

#	print "yu", ayu, (float(uly)-(float(ulx)*ayu))
#	print "yl", ayl, (float(lly)-(float(llx)*ayl))
#	print "xl", axl, (float(ulx)-(float(uly)*axl))
#	print "xr", axr, (float(urx)-(float(ury)*axr))
	
	return (fyu, fyl, fxl, fxr)

def genmask(fyu, fyl, fxl, fxr, size):
	(ys,xs) = size
	
	xmap = np.empty((ys,xs), dtype=np.float32)
	ymap = np.empty((ys,xs), dtype=np.float32)
	
	for y in range(int(ys)):
		for x in range(int(xs)):
			xmap[y,x] = (xs/(fxr(float(y))-fxl(float(y))))*(float(x)-fxl(float(y)))
			ymap[y,x] = (ys/(fyl(float(x))-fyu(float(x))))*(float(y)-fyu(float(x)))
			
#	print xmap
#	print ymap
	
	np.clip(xmap, 0, xs-1, xmap)
	np.clip(ymap, 0, ys-1, ymap)
	
	return (xmap,ymap)

def stretchimg(img, xmap, ymap):
	return cv2.remap(img, xmap, ymap, cv2.INTER_LINEAR) 

def cpvid(cvreader, writefunc, xmap, ymap):
	good, mat = cvreader.read()
	while good:
		img = stretchimg(mat, xmap, ymap)
		writefunc(img)
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
	(fyu, fyl, fxl, fxr) = genlinfuncs(
				float(sys.argv[1]),float(sys.argv[2]), # ulx, uly
				float(sys.argv[3]),float(sys.argv[4]), # urx, ury
				float(sys.argv[5]),float(sys.argv[6]), # llx, lly
				float(sys.argv[7]),float(sys.argv[8]), # lrx, lry
				)
	
	(xmap,ymap) = genmask(fyu, fyl, fxl, fxr, (cvreader.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT),cvreader.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)))
	
	write = RAWVidWriter().write
	
	for vid in sys.argv[9:]:
		cvreader = cv2.VideoCapture(vid)
		cpvid(cvreader, write, xmap, ymap)
