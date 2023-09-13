import collections


NEGATIVE_INFINITY = float('-inf')

def default_sub_score(x, y):
  if x == y:
    return 1
  if x == ' ' or y == ' ':
    return 0
  if (x.isdigit() and y.isalpha()) or (x.isalpha() and y.isdigit()):
    return 0

  return -1

"""
  sumatrix argument should also include linear gap penalty!
"""
def overlap_align(x, y, sub_score=default_sub_score, g=-5):
    """Computes an optimal overlap pairwise alignment from sequence x to sequence y
    with an affine gap scoring function.
        
    Args:
        x: a string representing the first sequence
        y: a string representing the second sequence
        submatrix: a substitution matrix that also contains character-specific space scores
        g: the gap existence score for gaps
    Returns:
        A tuple, (score, alignment), where score is a numeric value giving the score of the
        alignment and alignment is a list of two strings
    """
    M = []
    I_x = []
    I_y = []
    for i in range(len(x) + 1):
        M.append([])
        I_x.append([])
        I_y.append([])
        for j in range(len(y) + 1):
            M[i].append(NEGATIVE_INFINITY)
            I_x[i].append(NEGATIVE_INFINITY)
            I_y[i].append(NEGATIVE_INFINITY)
    
    # Pointer dictionaries: key=(i,j) value=[(matrix_ptrs,k,l)]
    M_ptrs = collections.defaultdict(list)
    I_x_ptrs = collections.defaultdict(list)
    I_y_ptrs = collections.defaultdict(list)
    
    # Initialize matricies
    M[0][0] = 0
    I_x[0][0] = 0
    I_y[0][0] = g
    for i in range(1, len(x) + 1):
        I_x[i][0] = 0
        I_y[i][0] = NEGATIVE_INFINITY
        M[i][0] = NEGATIVE_INFINITY
    for j in range(1, len(y) + 1):
        I_y[0][j] = I_y[0][j - 1] + sub_score(y[j - 1], ' ')
        I_x[0][j] = NEGATIVE_INFINITY
        M[0][j] = NEGATIVE_INFINITY
    
    # Fill out matrices
    for i in range(1, len(x) + 1):
        for j in range(1, len(y) + 1):            
            # Find M(i,j)
            m_score = M[i - 1][j - 1] + sub_score(x[i - 1], y[j - 1])
            i_x_score = I_x[i - 1][j - 1] + sub_score(x[i - 1], y[j - 1])
            i_y_score = I_y[i - 1][j - 1] + sub_score(x[i - 1], y[j - 1])
            m_max = max(m_score, i_x_score, i_y_score)
            if m_score == m_max:
                M_ptrs[(i,j)].append((M_ptrs, i - 1, j - 1))
            if i_x_score == m_max:
                M_ptrs[(i,j)].append((I_x_ptrs, i - 1, j - 1))
            if i_y_score == m_max:
                M_ptrs[(i,j)].append((I_y_ptrs, i - 1, j - 1))
            M[i][j] = m_max
            
            # Find I_x(i,j)
            m_score = M[i - 1][j] + g + sub_score(x[i - 1], ' ')
            i_x_score = I_x[i - 1][j] + sub_score(x[i - 1], ' ')
            i_x_max = max(m_score, i_x_score)
            if m_score == i_x_max:
                I_x_ptrs[(i,j)].append((M_ptrs, i - 1, j))
            if i_x_score == i_x_max:
                I_x_ptrs[(i,j)].append((I_x_ptrs, i - 1, j))
            I_x[i][j] = i_x_max
            
            # Find I_y(i,j)
            m_score = M[i][j - 1] + g + sub_score(y[j - 1], ' ')
            i_y_score = I_y[i][j - 1] + sub_score(y[j - 1], ' ')
            i_y_max = max(m_score, i_y_score)
            if m_score == i_y_max:
                I_y_ptrs[(i,j)].append((M_ptrs, i, j - 1))
            if i_y_score == i_y_max:
                I_y_ptrs[(i,j)].append((I_y_ptrs, i, j - 1))
            I_y[i][j] = i_y_max
    
    # Find argmax of last row
    argmax = None
    max_score = NEGATIVE_INFINITY
    for matrix in [ M, I_x, I_y ]:
        for j in range(len(y) + 1):
            if matrix[-1][j] > max_score or (matrix[-1][j] == max_score and argmax != None and j > argmax[1]):
                max_score = matrix[-1][j]
                argmax = (matrix, j)
    
    # Traceback
    cur_i = len(x)
    cur_j = argmax[1]
    cur_matrix = None
    if argmax[0] == M:
        cur_matrix = M_ptrs
    elif argmax[0] == I_x:
        cur_matrix = I_x_ptrs
    else:
        cur_matrix = I_y_ptrs
    alignment = [ [], [] ]
    for j in range(len(y), cur_j, -1):
        alignment[0].insert(0, ' ')
        alignment[1].insert(0, y[j - 1])
        
    while cur_j > 0:
        # Find next pointer
        prev_paths = cur_matrix[(cur_i, cur_j)]
        chosen_path = None
        if len(prev_paths) == 1:
            chosen_path = prev_paths[0]
        else:
            I_x_filter = list(filter(lambda path: path[0] == I_x_ptrs, prev_paths))
            M_filter = list(filter(lambda path: path[0] == M_ptrs, prev_paths))
            I_y_filter = list(filter(lambda path: path[0] == I_y_ptrs, prev_paths))
            if len(I_x_filter) > 0:
                chosen_path = I_x_filter[0]
            elif len(M_filter) > 0:
                chosen_path = M_filter[0]
            elif len(I_y_filter) > 0:
                chosen_path = I_y_filter[0]
                
        prev_matrix, prev_i, prev_j = chosen_path
        
        # Add to alignment
        if prev_i < cur_i and prev_j < cur_j:
            alignment[0].insert(0, x[cur_i - 1])
            alignment[1].insert(0, y[cur_j - 1])
        elif prev_i == cur_i:
            alignment[0].insert(0, ' ')
            alignment[1].insert(0, y[cur_j - 1])
        else:
            alignment[0].insert(0, x[cur_i - 1])
            alignment[1].insert(0, ' ')
        
        cur_matrix = prev_matrix
        cur_i = prev_i
        cur_j = prev_j
    
    for i in range(cur_i, 0, -1):
        alignment[0].insert(0, x[i - 1])
        alignment[1].insert(0, ' ')
    
    string_alignment = [ ''.join(alignment[0]), ''.join(alignment[1]) ]
    return (max_score, string_alignment)