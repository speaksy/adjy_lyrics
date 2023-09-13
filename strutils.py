import random

class StrIndexer:    
  def __init__(self, string):
    self._string = string
    
    self._idx_start = 0
    self._idx_step = 1
    self._idx_max_chars = float('inf')
    self._idx_max_words = float('inf')
    self._idx_stop_seqs = [ ]
    self._idx_snap_to_words = True

  def index(self):
    """
    Gets an index which maximizes word/char distance from start index
    if there are no stop sequences. Otherwise it respects stop sequences
    and returns the index of the first character before/after a stop sequence.
    """
    
    word_delims = [ '\t', ' ', '\n' ] # Must be single characters

    def valid(idx, lower=0, upper=None):
      """Helper function to check if index is in valid range. upper=None means
      to bound by string length"""
      return idx >= lower and idx < len(self._string) if upper == None else upper

    def stop_seqs_reached(idx):
      """Tests if characters after idx represent a stop sequence"""
      best_matched_seq = ""
      for seq in self._idx_stop_seqs:
        end_idx = idx + self._idx_step * len(seq)
        if valid(end_idx):
          if self._idx_step < 0:
            test_seq = self._string[end_idx:idx]
          else:
            test_seq = self._string[(idx + self._idx_step):(end_idx + self._idx_step)]
          if test_seq == seq and len(test_seq) > len(best_matched_seq):
            best_matched_seq = seq
      return best_matched_seq
    
    def snap_to_word(idx, step=None):
      """Returns idx snapped to nearest word. step = None means to use
      object instance's step size"""
      if idx == 0 or idx == len(self._string) - 1:
        return idx

      while valid(idx) and self._string[idx] not in word_delims:
        idx += self._idx_step if step == None else step

      idx += self._idx_step

      # Ensure valid index
      while not valid(idx):
        idx -= self._idx_step
      return idx

    true_start = self._idx_start
    cur = self._idx_start
    word_count = 0
    char_count = 0

    # Snap to nearest word
    if self._idx_snap_to_words:
      cur = snap_to_word(cur)
      true_start = cur

    # Expand matched range
    prev = ""
    while valid(cur):
      if word_count >= self._idx_max_words or char_count >= self._idx_max_chars:
        # Break if reached word/char count
        break
      elif len(stop_seqs_reached(cur)) > 0:
        # Return if hit stop sequence
        if self._idx_include_stop_seqs:
          # Advance cur until we include stop seq or reach end of string
          stop_seq = stop_seqs_reached(cur)
          desired_cur = cur + self._idx_step * len(stop_seq)
          if valid(desired_cur) and char_count + len(stop_seq) <= self._idx_max_chars:
            cur = desired_cur
        return cur
      
      # Update word/char counts
      char_count += 1
      if self._string[cur] in word_delims and prev not in word_delims:
        word_count += 1

      # Take a step 
      prev = cur
      cur += self._idx_step

    # Ensure cur is valid index
    while not valid(cur):
      cur -= self._idx_step
    if self._idx_snap_to_words:
      cur = snap_to_word(cur, step=-self._idx_step) # Snap "backwards" to word
    
    return cur


  def substr(self):
    """
    Runs index() and returns the substring from start to returned index
    """

    word_delims = [ '\t', ' ', '\n' ] # Must be single characters

    def valid(idx, lower=0, upper=None):
      """Helper function to check if index is in valid range. upper=None means
      to bound by string length"""
      return idx >= lower and idx < len(self._string) if upper == None else upper

    def snap_to_word(idx, step=None):
      """Returns idx snapped to nearest word. step = None means to use
      object instance's step size"""
      if idx == 0 or idx == len(self._string) - 1:
        return idx

      while valid(idx) and self._string[idx] not in word_delims:
        idx += self._idx_step if step == None else step

      idx += self._idx_step

      # Ensure valid index
      while not valid(idx):
        idx -= self._idx_step
      return idx


    cur = self.index()
    true_start = self._idx_start if not self._idx_snap_to_words else snap_to_word(self._idx_start)

    # Return matched range
    if true_start < cur:
      return self._string[true_start:(cur + 1)]
    else:
      return self._string[cur:(true_start + 1)]

  def longest_substr(self, max_depth=-1):
    def extend_substr(begin, permissible_len, level):
      if begin < 0 or begin >= len(self._string) or (max_depth > -1 and level > max_depth):
        return begin
      new_idx = self.start(begin).index()
      remainder = permissible_len - abs(begin - new_idx) 
      if new_idx != begin and remainder > 0:
        return extend_substr(new_idx + self._idx_step, remainder, level + 1)
      else:
        return begin 

    orig_start = self._idx_start
    true_start = self._idx_start if not self._idx_snap_to_words else snap_to_word(self._idx_start)
    cur = extend_substr(true_start, self._idx_max_chars, 1)
    self.start(orig_start)

    # Return matched range
    if true_start < cur:
      return self._string[true_start:(cur + 1)]
    else:
      return self._string[cur:(true_start + 1)]


  def start(self, start):
    if start < 0 or start >= len(self._string):
      raise ValueError('Start index outside string range')
    
    self._idx_start = start
    return self

  def step(self, step):
    if step != 1 and step != -1:
      raise ValueError('Step must be either 1 or -1')
    self._idx_step = step
    return self

  def max_chars(self, max_chars):
    if max_chars < 0:
      raise ValueError('Max chars cannot be less than 0')
    self._idx_max_chars = max_chars
    return self

  def max_words(self, max_words):
    if max_words < 0:
      raise ValueError('Max words cannot be less than 0')
    self._idx_max_words = max_words
    return self
  
  def stop_sequences(self, stop_seqs, include_stop_seqs_in_substr=False):
    self._idx_stop_seqs = stop_seqs
    self._idx_include_stop_seqs = include_stop_seqs_in_substr
    return self

  def snap_to_words(self, snap):
    self._idx_snap_to_words = snap
    return self


if __name__ == '__main__':
  test_string = """1 Wait! Hold! Wait... tighter! Eyes closed, era; hour.
Weak-weight; shy moment
-Quick hold it!

2 wait hold. wait, runner. Don't go cold Summer.
Day, week, hour, Era
-Quick hold it!

3 Somewhere in between
what it was and was to me...
There is a line I cannot find
For it's ever drawn behind...

"Where two forms ever debut... The Cloverleaf
four rivers run through."

5 ... On A page in their purlieu...

6 "The Lightning bug below them flew ...Their
Candles lit IN sacrAment; ... holy riTe!"

Now holy wrIt...

"...An Open field..."

a brokeN star:

"It's who they were..." """
  indexer = StrIndexer(test_string)
  indexer.stop_sequences([ "\n\n" ]).snap_to_words(True)

  assert(indexer.substr() == """1 Wait! Hold! Wait... tighter! Eyes closed, era; hour.
Weak-weight; shy moment
-Quick hold it!""")

  assert(indexer.start(25).substr() == """Eyes closed, era; hour.
Weak-weight; shy moment
-Quick hold it!""")

  stop_seq_idx = indexer.start(77).index()
  assert(test_string[stop_seq_idx+1:stop_seq_idx+3] == "\n\n")

  print("All automated tests passed")

  # Proper lyric test
  print("Lyric sample test:")
  i = random.randint(0, len(test_string))
  indexer = StrIndexer(test_string).start(i).step(-1).stop_sequences([ "\n\n" ]).snap_to_words(False)
  newline_idx = indexer.index()
  lyric = indexer.start(newline_idx).step(1).max_chars(280).longest_substr()
  print(lyric)

