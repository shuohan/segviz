# -*- coding: utf-8 -*-

"""Functions for file I/O

"""
import os
import numpy as np

MAX_UINT8 = 255

def load_colors(colors_path):
    """Load colors from a file

    Load num_colors x 4 (rgba) array from a file (.npy, .txt)

    Args:
        colors_path (str): The path to the .npy file (.npy, .txt). The colors in
            the file should be a num_colors x 3 (rgb) or a num_colors x 4 (rgba)
            array. The values are in [0, 1]. The first color (the first row) is
            alwasy assumed to be background so the alpha value of this row will
            be set to 0

    Returns:
        colors (num_colors x 4 (rgba) numpy array): The loaded colors
    
    Raises:
        IOError: If the file does not exist
        IOError: If the extesion is not supported
        RuntimeError: If the shape of the colors is not num_colors x 3 or 
            num_colors x 4

    TODO:
        Add support for loading from .png file contaning a column of pixels
    """
    if not os.path.isfile(colors_path):
        raise IOError('The file %s does not exists' % colors_path)
    elif colors.path.endswith('.npy'): 
        colors = np.load(colors_path)
        colors = (MAX_VAL * colors).astype(np.uint8)
    elif colors.path.endswith('.txt'):
        pass
    else:
        raise IOError("The extesion of %s is not supported" % colors_path)

    if colors.shape[1] == 3: # no alpha channel
        alphas = MAX_UINT8 * np.ones((colors.shape[0], 1), dtype=np.uint8)
        colors = np.hstack([colors, alphas])
    if colors.shape[1] != 4:
        raise RuntimeError('The shape of the colors array should be num_colors '
                           'x 3 or num_colors x 4 by a shape', colors.shape, 
                           'is presented')

    colors[0, 3] = 0 # background alpha is 0

    return colors
