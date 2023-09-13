import os, os.path
import subprocess
import sys

import tweet
import convolution as lyric_generator

if __name__ == '__main__':
  lyric_text_path = os.path.join(lyric_generator.output_dir, lyric_generator.output_text_filename)
  lyric_image_path = os.path.join(lyric_generator.output_dir, lyric_generator.output_image_filename)

  # Original modification time
  orig_time = os.path.getmtime(lyric_text_path)

  modified_time = orig_time
  while modified_time == orig_time: # Run until success
    subprocess.run(['/usr/local/bin/python3.8', './convolution.py'])
    modified_time = os.path.getmtime(lyric_text_path)

  # Tweet latest image/text
  lyric = None
  with open(lyric_text_path, 'r') as text_file:
      lyric = text_file.read()
  tweet.post(lyric, lyric_image_path)
