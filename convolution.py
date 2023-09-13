# from Bio import pairwise2
# from Bio.pairwise2 import format_alignment
import random
import os, os.path
import time
import re
import pytesseract as pytess
import cv2 as opencv
import numba

import string_align
from strutils import StrIndexer

# Globals
tesseract_path = os.path.abspath(r'E:\Program Files\Tesseract-OCR\tesseract.exe')
image_dir = r'the_text'
output_dir = r'output'
now = time.localtime(time.time())
# output_image_filename = f'lyrics_{now.tm_mon}.{now.tm_mday}.{now.tm_year}.{now.tm_hour}h{now.tm_min}m{now.tm_sec}s.png'
# output_text_filename = f'lyrics_{now.tm_mon}.{now.tm_mday}.{now.tm_year}.{now.tm_hour}h{now.tm_min}m{now.tm_sec}s.txt'
output_image_filename = f'latest.png'
output_text_filename = f'latest.txt'

tweet_length = 280

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def get_lyrics_for_image(image_path):
  """
    Reads file at given path as text.

    Arguments:
      image_path: The filesystem path to the image version of lyrics

    Returns:
      The text of the lyrics file associated with the image
  """
  lyrics = None
  with open(os.path.splitext(image_path)[0] + '.txt', 'r') as text_file:
      lyrics = text_file.read()
  return lyrics

def lyric_sampler(image_path):
  """
    Generator function which samples a lyric from the image with word count limit.

    Arguments:
      image_path: The filesystem path to the image version of lyrics
      max_words: The maximum number of words in the sampled lyric (default=32)
    
    Returns:
      A string of lyrics
  """
  whitespace = [ " ", "\t", "\n" ]

  lyrics = get_lyrics_for_image(image_path)
  num_chars = len(lyrics)

  while True:
    i = random.randint(0, num_chars)
    
    """
    # OLD LYRIC GENERATION CODE

    # Find word start
    start = i
    while start > 0 and lyrics[start] not in whitespace:
      start -= 1
    
    # Advance until word count reached
    word_count = 0
    end = i
    while end < len(lyrics) - 1 and word_count < max_words:
      end += 1
      if lyrics[end] in whitespace and lyrics[end - 1] not in whitespace:
        word_count += 1
    
    # Go back and extend the beginning if we've reached the last character
    while start > 0 and word_count < max_words:
      start -= 1
      if lyrics[start] in whitespace and lyrics[start + 1] not in whitespace:
        word_count += 1

    lyric = lyrics[start:end].strip()
    if len(lyric) > tweet_length:
      # TODO make this part go back a word instead of truncating lyric
      lyric = lyric[:tweet_length]
      lyric[:3] = "..."
      lyric[-3:] = "..."
    """
    
    # Randomly decide to take either a single "line" or some paragraphs
    r = random.random()
    if r < 0.5: # Single line
        stop_seqs = [ ".\n", "...", "....", "!", "?", "\n\n", "\r\n\r\n" ]
        indexer = StrIndexer(lyrics).stop_sequences(stop_seqs, True).snap_to_words(False)
        newline_idx = indexer.start(i).step(-1).index()
        lyric = indexer.start(newline_idx).stop_sequences(stop_seqs, True).step(1).max_chars(tweet_length).substr()
        # TODO: replace below logic with regex
        if lyric.startswith("!\n") or lyric.startswith("?\n"):
            lyric = lyric[1:]
        elif lyric.startswith("!\r\n") or lyric.startswith("?\r\n"):
            lyric = lyric[2:]
        if lyric.endswith("\r\n?") or lyric.endswith("\r\n!"):
            lyric = lyric[:-3]
        elif lyric.endswith("\n?") or lyric.endswith("\n!"):
            lyric = lyric[:-2]
    else: # Multiple paragraphs
        num_paragraphs = random.randint(1, 4)
        indexer = StrIndexer(lyrics).stop_sequences([ "\n\n", "\r\n\r\n" ]).snap_to_words(False)
        newline_idx = indexer.start(i).step(-1).index()
        lyric = indexer.start(newline_idx).step(1).max_chars(tweet_length).longest_substr(num_paragraphs)

    # Skip weird leading periods
    leading_period = re.match(r" *\.+ *\n", lyric)
    if leading_period:
        lyric = lyric[leading_period.end():]
    if len(lyric.strip()) < 2 or (len(lyric) < 4 and lyric.startswith(".")):
      continue
    else:
      yield lyric

def image_sampler():
  '''
    Generator function for all lyric images in file tree
    
    Returns:
      An tuple of (image, image_path) where image is an opencv image and
      image_path is a file system path
  '''
  # Get a list of all candidate images
  def get_image_paths_and_word_counts(root_dir):
    all_image_paths = []
    all_word_counts = []
    def search_file_tree(dir):
      for file in os.listdir(dir):
        if file == r'.' or file == r'..':
          continue
        elif os.path.isdir(os.path.join(dir, file)):
          search_file_tree(os.path.join(dir, file))
        elif os.path.splitext(file)[1] == '.tif':
          all_image_paths.append(os.path.join(dir, file))
          lyrics_file = os.path.splitext(file)[0] + '.txt'
          if os.path.exists(os.path.join(dir, lyrics_file)):
            with open(os.path.join(dir, lyrics_file), 'r') as fd:
              all_word_counts.append(len(fd.read().split()))
          else:
            all_word_counts.append(0)
    search_file_tree(root_dir)
    return all_image_paths, all_word_counts
  
  all_image_paths, all_word_counts = get_image_paths_and_word_counts(image_dir)

  # Convert word counts to probabilities
  sum_wc = sum(all_word_counts)
  image_probs = list(map(lambda wc: wc / sum_wc, all_word_counts))
  # print(list(zip(all_image_paths, image_probs)))

  def sample_categorical(population, distribution):
    cutoff = random.random()
    cumulative_dist = 0
    for i in range(len(distribution) - 1):
      if cutoff > cumulative_dist and cutoff <= cumulative_dist + distribution[i]:
        return population[i]
      cumulative_dist += distribution[i]
    return population[-1]

  # Randomly select an image
  while True:
    # Load an image
    image_path = sample_categorical(all_image_paths, image_probs)
    image = opencv.imread(image_path)
    image = opencv.cvtColor(image, opencv.COLOR_BGR2GRAY)
    # _, image = opencv.threshold(image, 240, 255, opencv.THRESH_BINARY)
    
    # print(image.shape)
    # opencv.imshow('image', opencv.resize(image, (550, 425)))
    # opencv.waitKey(0)
    yield (image, image_path)

def tesseract_convolve(img, window_size, step_size):
  '''
    Treats tesseract as a convolutional operator on the image, mapping image slices
    to OSR output.

    Arguments:
      img: opencv image to convolve.
      window_size: tuple of (window_size.x, window_size.y).
      step_size: tuple of step sizes (step_size.x, step_size.y).
    
    Returns:
      A list of convolution evaluations -- tuple of (text, window)
  '''

  win_x, win_y = window_size[0], window_size[1]
  step_x, step_y = step_size[0], step_size[1]

  max_y = img.shape[0] - win_y
  max_x = img.shape[1] - win_x
  result = []
  for y in range(0, max_y, step_y):
    for x in range(0, max_x, step_x):
      print(f'Trying window at ({x}, {y})')
      window = img[y:(y + win_y), x:(x + win_x)]
      text = pytess.image_to_string(window, lang='eng')
      result.append((text, window))

  return result

def write_lyric(img, lyric):
  """
    Saves an image and its associated lyrics. Creates output directory
    if none exists.

    Arguments:
      img: the opencv image to save
      lyric: the text to save
  """
  if not os.path.exists(output_dir):
    os.mkdir(output_dir)
  with open(os.path.join(output_dir, output_text_filename), 'w') as f:
    f.write(lyric)
  opencv.imwrite(os.path.join(output_dir, output_image_filename), img)

def generate_tweet_content(conv_window_size=(1200, 900), conv_step_size=(200, 200)):
  # Set up path to tesseract executable
  #pytess.pytesseract.tesseract_cmd = tesseract_path
  
  random.seed()

  # Choose an image
  img, image_path = next(image_sampler())

  # Choose a lyric
  lyric = next(lyric_sampler(image_path))
  print(f'Searching for lyric "{lyric}"')
  
  # Convolve image
  convolutions = tesseract_convolve(img, conv_window_size, conv_step_size)
  print('got convolutions')
  osrs = list(filter(lambda conv: len(conv[0]) > 0, convolutions)) # Remove windows with no text
  print('filtered convolutions')

  @numba.jit(nopython=True)
  def match_score(x, y):
    if x == y:
      return 1
    if x == ' ' or y == ' ':
      return 0
    if (x.isdigit() and y.isalpha()) or (x.isalpha() and y.isdigit()):
      return 0
    return -1

  # Align with desired text
  simplified_lyric = lyric.replace('\n', ' ').lower()

  # BELOW: biopython alignment
  # def align_predicate(text):
  #   # Define substitution "matrix"
    
  #   print('aligning text')
  #   if len(text) > 900:
  #     print('\taborting alignment... text too long!')
  #     return -9999
  #   alignment = pairwise2.align.localcs(
  #     simplified_lyric,
  #     text.replace('\n', ' ').lower(),
  #     match_score,
  #     -2,
  #     -1,
  #     one_alignment_only=True,
  #     score_only=True)
  #   print('\t aligned text')
  #   if alignment:
  #     return alignment
  #   else:
  #     return -9999 # Sentinel value
    
  texts = [ osr[0] for osr in osrs ]
  # scores = list(map(align_predicate, texts))
  scores = string_align.local_batch(
        simplified_lyric,
        list(map(lambda text: text.replace('\n', ' ').lower(), texts)),
        match_score,
        -2,
        -1).tolist()
  best_index = scores.index(max(scores))

  # Write output
  write_lyric(osrs[best_index][1], lyric)

  # print(lyric)
  # opencv.imshow(lyric, osrs[best_index][1])
  # opencv.waitKey(0)

if __name__ == '__main__':
  generate_tweet_content()
