import numpy as np
import numba

@numba.jit(nopython=True)
def local(seqA, seqB, sub_score, gap_open, gap_extend):
  """
    Performs local sequence alignment of two strings using the Smith-Waterman algorithm.

    Arguments:
      seqA: The sequence to align against
      seqB: The sequence to be aligned
      sub_score: A function mapping pairs of characters to substitution scores
      gap_open: Penalty for opening a gap
      gap_extend: Penalty for extending a gap
    
    Returns:
      The score of the optimal alignment for the given sequences
  """
  # Allocate arrays
  M = np.zeros((len(seqA) + 1, len(seqB) + 1))
  I_x = np.zeros(M.shape)
  I_y = np.zeros(M.shape)

  # Fill matrices
  for i in range(1, len(seqA) + 1):
    for j in range(1, len(seqB) + 1):
      match_score = sub_score(seqA[i-1], seqB[j-1])
      M[i,j] = max(
        M[i-1,j-1] + match_score,
        I_x[i-1,j-1] + match_score,
        I_y[i-1,j-1] + match_score,
        0
      )
      I_x[i,j] = max(
        M[i-1,j] + gap_open + gap_extend,
        I_x[i-1,j] + gap_extend,
        0
      )
      I_y[i,j] = max(
        M[i,j-1] + gap_open + gap_extend,
        I_y[i,j-1] + gap_extend,
        0
      )
  
  # Get solution
  best_score = max(np.max(M), np.max(I_x), np.max(I_y))
  return best_score

@numba.jit(nopython=True)
def local_batch(seqA, seqsB, sub_score, gap_open, gap_extend):
  """
    Performs local sequence alignment of two strings using the Smith-Waterman algorithm.

    Arguments:
      seqA: The sequence to align against
      seqsB: List of sequences to be aligned
      sub_score: A function mapping pairs of characters to substitution scores
      gap_open: Penalty for opening a gap
      gap_extend: Penalty for extending a gap
    
    Returns:
      numpy array of scores of the optimal alignment for the given sequences
  """
  scores = np.zeros(len(seqsB))
  for k in range(len(seqsB)):
    seqB = seqsB[k]
    
    # Allocate arrays
    M = np.zeros((len(seqA) + 1, len(seqB) + 1))
    I_x = np.zeros(M.shape)
    I_y = np.zeros(M.shape)

    # Fill matrices
    for i in range(1, len(seqA) + 1):
      for j in range(1, len(seqB) + 1):
        match_score = sub_score(seqA[i-1], seqB[j-1])
        M[i,j] = max(
          M[i-1,j-1] + match_score,
          I_x[i-1,j-1] + match_score,
          I_y[i-1,j-1] + match_score,
          0
        )
        I_x[i,j] = max(
          M[i-1,j] + gap_open + gap_extend,
          I_x[i-1,j] + gap_extend,
          0
        )
        I_y[i,j] = max(
          M[i,j-1] + gap_open + gap_extend,
          I_y[i,j-1] + gap_extend,
          0
        )
    
    # Get solution
    best_score = max(np.max(M), np.max(I_x), np.max(I_y))
    scores[k] = best_score
  return scores

