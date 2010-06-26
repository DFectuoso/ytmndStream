#!/usr/bin/python

import sys
import aifc
import os
import re

## parameters

FPS = 24

SCRATCH_DIR = ".scratch_%05d" % os.getpid()
PREFIX = SCRATCH_DIR + "/temp"

os.mkdir(SCRATCH_DIR)

## command-line arguments

if len(sys.argv) is not 3:
  print("expecting two args, got "+str(sys.argv))
  sys.exit(-1)

original_gif = sys.argv[1]
original_wav = sys.argv[2]

## compute audio duration in seconds

temp_aif = PREFIX + ".aif"
os.system("sox %s %s" % (original_wav, temp_aif))
aif = aifc.open(temp_aif, 'r')
duration = float(aif.getnframes())/aif.getframerate()
aif.close()

## delay extraction
print "gifsicle -I %s" % original_gif 
analysis = os.popen("gifsicle -I %s" % original_gif).readlines()

frames = int(re.search(r"(\d+) image",analysis[0]).group(1))
print "The gif has %d frames." % frames
frame_delays = []
if frames is 1:
  frame_delays = [0.1]
else:
  for line in analysis:
    if "#" in line:
      try:
        delay = float(re.search(r"delay ([\d\.]+)s", line).group(1))
      except:
        delay = 0.1
      print "  +%f" % delay
      frame_delays.append(delay)

## frame extraction

os.system("gifsicle --unoptimize -e %s -o %s" % (original_gif, PREFIX))

## frame linking loop

video_frame_step = 1.0/FPS
timecode = 0
accum = 0
frame_counter = 0
frame_index = 0
def link(src, dst):
  os.link("%s.%03d" % (PREFIX, src), "%s.%03d.gif" % (PREFIX, dst))

while timecode < duration:
  link(frame_index, frame_counter)
  accum += video_frame_step
  if accum > frame_delays[frame_index]:
    accum -= frame_delays[frame_index]
    frame_index += 1
    if frame_index == frames: frame_index = 0
  frame_counter += 1
  timecode += video_frame_step


## transcodinG

os.system("ffmpeg -r %d -i %s -i %s -y out.mpeg" %
        (FPS,
         PREFIX + ".%03d.gif",
         original_wav))

## cleanup

os.system("rm %s.*" % PREFIX)
os.rmdir(SCRATCH_DIR)
