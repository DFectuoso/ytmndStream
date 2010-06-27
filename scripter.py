#!/usr/bin/python

import sys
import aifc
import os
import os.path
import re
import urllib2
import simplejson
import web
import random
             
## parameters


def magic(name):
  ## command-line arguments
  FPS = 24
  SCRATCH_DIR = ".scratch_%d" % random.randint(0,6500000)
  PREFIX = SCRATCH_DIR + "/temp"
  os.mkdir(SCRATCH_DIR)

  if name == "":
    print("expecting one ytmnd name, got "+str(sys.argv))
    return

  # Get the url of the sound and foreground
  ytmnd_name = name 
  ytmnd_html = urllib2.urlopen("http://" + ytmnd_name + ".ytmnd.com").read()
  expr = r"ytmnd.site_id = (\d+);"
  ytmnd_id = re.search(expr,ytmnd_html).group(1)
  ytmnd_info = simplejson.load(urllib2.urlopen("http://" + ytmnd_name + ".ytmnd.com/info/" + ytmnd_id + "/json"))

  #Assign full url names for the sound and foreground
  original_gif = ytmnd_info['site']['foreground']['url']
  original_wav = ytmnd_info['site']['sound']['url']

  #download files
  os.system("wget %s" % original_gif)
  os.system("wget %s" % original_wav)

  #get the right names
  original_wav = original_wav.split("/")[-1]
  original_gif = original_gif.split("/")[-1]

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
  os.system("ffmpeg -r %d -i %s -i %s -y %s.mpeg" %
        (FPS,
         PREFIX + ".%03d.gif",
         original_wav, ytmnd_name))

  ## cleanup
  os.system("rm %s" % original_gif)
  os.system("rm %s" % original_wav)
  os.system("rm %s.*" % PREFIX)
  os.rmdir(SCRATCH_DIR)
  sys.exit(1)

urls = (
  '/foo/(.+)', 'index'
)

class index:
  def GET(self,foo):
    if os.path.isfile(foo + ".mpeg"):
      return "Exist"
    else:
      try:
        pid = os.fork() 
        if pid != 0:
          magic(foo)
        else:
          return "I will be getting:" + foo
      except OSError, e: 
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1) 


app = web.application(urls, globals())

if __name__ == "__main__": app.run()

