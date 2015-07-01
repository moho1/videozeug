# videozeug
Skripte, die ich für die Video AG entwickle.

## cornerpin.py
cornerpin.py is a tool to apply the Adobe Premiere Pro Corner Pin
Effekt, but in a faster Way.

It gets the coordinates of the corners as argument, computes a homographie
between the original image and the warped image and generates opencv.remap
matrixes to finally apply opencv remap.

The way using remap is faster than applying cv2.warpPerspective on every frame.

## diff.py
diff.py is a tool, to read a video and generate a black/white-mask,
which fades, depending on motion in a part of the video.

If there is, for example, a motion (a person) in the left half of the
Image, then fade the mask to black with an offset of 50 frames and a
fading Time of 25 frames. If the motion is gone for at least 50 frames
fade the mask in again with the same settings.

In Adobe Premiere Pro, the mask can be set as the alpha-channel
using the "Set Matte"-Effekt.
