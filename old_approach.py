from typing import Tuple
from numpy import ndarray
from Bio import pairwise2
from Bio.pairwise2 import format_alignment
import pdf2image
import random
import os, os.path
import time
import pytesseract as pytess
import cv2 as opencv
import skbio.sequence
import skbio.alignment
import alignment, alignment.sequencealigner, alignment.sequence, alignment.vocabulary
import unicodedata
import tweet

poppler_path = os.path.abspath(r'.\poppler-22.04.0\Library\bin')
tesseract_path = os.path.abspath(r'E:\Program Files\Tesseract-OCR\tesseract.exe')
image_dir = r'the_text'
output_dir = r'output'
now = time.localtime(time.time())
output_image_filename = f'lyrics_{now.tm_mon}.{now.tm_mday}.{now.tm_year}.{now.tm_hour}h{now.tm_min}m{now.tm_sec}s.png'
output_text_filename = f'lyrics_{now.tm_mon}.{now.tm_mday}.{now.tm_year}.{now.tm_hour}h{now.tm_min}m{now.tm_sec}s.txt'

pdf_rasterization_dpi = 500
mean_crop_dimensions = (3.5, 2.5) # In inches (pdf_rasterization_dpi used to convert to pixels)
min_aspect_ratio = 1.0
crop_distribution_variance = (0.75, 0.5)
minimum_crop_area = 0.75
tweet_length = 200

# random.seed(38)

"""
  Returns a random crop of the given opencv image
"""
def crop_sampler(img: ndarray) -> ndarray:
  while True:
    width = random.normalvariate(mean_crop_dimensions[0], crop_distribution_variance[0])
    height = random.normalvariate(mean_crop_dimensions[1], crop_distribution_variance[1])
    if width * height < minimum_crop_area or width / height < min_aspect_ratio:
      continue
    dx, dy = int(pdf_rasterization_dpi * width), int(pdf_rasterization_dpi * height)
    x = int(random.random() * (img.shape[1] - dx))
    y = int(random.random() * (img.shape[0] - dy))
    if x <= 0 or y <= 0:
      continue
    yield img[y:(y + dy), x:(x + dx)]

"""
  Writes an image and text to output directory
"""
def write_output(crop: ndarray, text: str):
  if not os.path.exists(output_dir):
    os.mkdir(output_dir)
  # with open(os.path.join(output_dir, output_text_filename), 'w') as f:
  #   f.write(text)  
  with open(os.path.join(output_dir, 'most_recent.txt'), 'w') as f:
    f.write(text)
  # opencv.imwrite(os.path.join(output_dir, output_image_filename), crop)
  opencv.imwrite(os.path.join(output_dir, 'most_recent.png'), crop)

"""
  Loads images, randomly selects one and crops it, then runs OCR/OSD on it using
  Tesseract
"""
def sample_image_and_run_ocr() -> Tuple[ndarray, str, str]:
  # Get a list of all candidate images
  def get_all_images_recursive(root_dir: str):
    all_image_paths = []
    def search_file_tree(dir):
      for file in os.listdir(dir):
        if file == r'.' or file == r'..':
          continue
        elif os.path.isdir(os.path.join(dir, file)):
          search_file_tree(os.path.join(dir, file))
        elif os.path.splitext(file)[1] == '.tif':
          all_image_paths.append(os.path.join(dir, file))
    search_file_tree(root_dir)
    return all_image_paths
  
  all_image_paths = get_all_images_recursive(image_dir)

  # Randomly select an image
  random.shuffle(all_image_paths)
  while len(all_image_paths) > 0:
    # Load an image
    image_path = all_image_paths.pop()
    print(f'Trying {image_path}...')
    image = opencv.imread(image_path)
    image = opencv.cvtColor(image, opencv.COLOR_BGR2GRAY)
    # _, image = opencv.threshold(image, 240, 255, opencv.THRESH_BINARY)
    
    # print(image.shape)
    # opencv.imshow('image', opencv.resize(image, (550, 425)))
    # opencv.waitKey(0)

    # Randomly crop it
    for i, crop in enumerate(crop_sampler(image)):
      if i > 25: # If we just can't find any good text, then move on to the next image
        break
      text = pytess.image_to_string(crop, lang='eng')
      if len(text) > 20:
        yield (crop, text, image_path)

def match_score(x, y):
  if x == y:
    return 1
  if x == ' ' or y == ' ':
    return 0
  if (x.isdigit() and y.isalpha()) or (x.isalpha() and y.isdigit()):
    return 0

  return -1

class MyScoring(alignment.sequencealigner.Scoring):
  def __init__(self, vocab):
    super().__init__()
    self.vocab = vocab

  def __call__(self, x, y):
    return match_score(self.vocab.decode(x), self.vocab.decode(y))

if __name__ == '__main__':
  # Set up path to tesseract executable
  pytess.pytesseract.tesseract_cmd = tesseract_path

  for crop, text, source_image_path in sample_image_and_run_ocr():
    # Compute local alignment of OCR string and actual text
    source_text = None
    with open(os.path.splitext(source_image_path)[0] + '.txt', 'r') as text_file:
      source_text = text_file.read()
    
    # BioPython alignment
    alignments = pairwise2.align.localcs(
      source_text.replace('\n', ' ').lower(),
      text.replace('\n', ' ').lower(),
      match_score,
      -2,
      -1,
      one_alignment_only=True)
    alignment = alignments[0]
    aligned_sequence = alignment.seqB

    # scikit-bio alignment
    # source_text_alphabet = set(source_text)
    # ocr_text_alphabet = set(text)
    # sub_matrix = dict()
    # for glyph_i in source_text_alphabet:
    #   sub_matrix[glyph_i] = dict()
    #   for glyph_j in ocr_text_alphabet:
    #     sub_matrix[glyph_i][glyph_j] = match_score(glyph_i, glyph_j)
    
    # alignment = skbio.alignment.local_pairwise_align(
    #   skbio.sequence.Sequence(source_text.lower().encode('ascii', 'ignore'), lowercase=False),
    #   skbio.sequence.Sequence(text.lower().encode('ascii', 'ignore'), lowercase=False),
    #   -2,
    #   -1,
    #   sub_matrix
    # )

    # aligned_sequence = alignment.iloc(1).decode()
    # print(aligned_sequence)

    # alignment alignment
    # source_seq = alignment.sequence.Sequence(source_text.lower().split())
    # text_seq = alignment.sequence.Sequence(text.lower().split())
    # vocab = alignment.vocabulary.Vocabulary()
    # source_encoded = vocab.encodeSequence(source_seq)
    # text_encoded = vocab.encodeSequence(text_seq)
    # aligner = alignment.sequencealigner.LocalSequenceAligner(MyScoring(vocab), -2)
    # score, encodeds = aligner.align(source_encoded, text_encoded, backtrace=True)
    # aligned_sequence = vocab.decodeSequenceAlignment(encodeds[0].second)[1]
    # print(aligned_sequence)

    # Find bounds on "good" part of alignment
    filter_len = 5
    signal = [ 0 ] * (len(source_text) - filter_len)
    for i in range(len(signal) - filter_len):
      for j in range(filter_len):
        if aligned_sequence[i + j] != '-':
          signal[i] += 1
      signal[i] /= filter_len
    
    signal_start, signal_end = -1, -1
    for i in range(len(signal)):
      if signal_start == -1 and signal[i] >= 0.5:
        signal_start = i
      if signal_start != -1 and signal[i] < 0.25:
        signal_end = i
        break
    if signal_end == -1:
      signal_end = len(signal) - 1
    if signal_start == -1:
      continue

    # Pick some reasonable range within the alignment to capture as a tweet
    source_text_len = len(source_text)
    # print(alignment.seqA)
    # print(alignment.seqB)
    current_start, current_end = signal_start, min(signal_start + tweet_length, source_text_len - 1)
    # print(source_text[current_start:current_end])
    prev_start, prev_end  = -1, -1
    # print(current_start, current_end)
    space_and_newline = set('\n ')
    while (current_start != prev_start or current_end != prev_end) and current_end - current_start <= tweet_length:
      prev_start = current_start
      prev_end = current_end
      current_start = max(current_start - 1, 0)
      current_end = min(current_end + 1, source_text_len - 1)
      # Back current_start up by one word
      while current_start > 0 and source_text[current_start] not in space_and_newline:
        current_start -= 1
      # Advance current_end by one word
      while current_end < source_text_len - 1 and source_text[current_end] not in space_and_newline:
        current_end += 1

      # print('in loop', current_start, current_end)
      # print(f'comparing {current_start} and {prev_start}, {current_end} and {prev_end}')

    # print(prev_start, prev_end)

    # Pick subset of best excerpt so that we start and end on line breaks
    best_start, best_end = prev_start, prev_end
    if '\n' in source_text:
      while best_start > 0 and source_text[best_start] != '\n':
        best_start += 1
      while best_end < source_text_len - 1 and source_text[best_end] != '\n':
        best_end -= 1
    print(best_start, best_end)
    tweet_text = source_text[best_start:(best_end + 1)]
    tweet_image = crop
    break

  write_output(tweet_image, tweet_text)
  tweet.post(tweet_text, os.path.join(output_dir, 'most_recent.png'))
