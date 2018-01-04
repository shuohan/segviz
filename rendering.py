# -*- coding: utf-8 -*-

"""Functions about rendering

"""
import numpy as np
from PIL import Image, ImageColor

MAX_UINT8 = 255

def convert_colors(colors, labels):
    """Convert colors array using labels presented in a label image

    The [1, ..., num_labels] rows of the original colors will be mapped to 
    [label1, lebel2, ..., labeln] row of the new colors array. The other rows 
    of the new colors will be set to 'empty'.

    Args:
        colors (num_colors x 4 array (rgba) uint8 numpy array): The colors to
            convert
        labels (int list): The labels of the label image to color

    Returns:
        converted_colors (max_label x 4 numpy array): Converted colors

    """
    label_set = np.unique(labels.astype(int))
    new_colors_shape = (np.max(label_set)+1, colors.shape[1])
    new_colors = np.empty(new_colors_shape, dtype=np.uint8)
    indices = np.mod(np.arange(len(label_set), dtype=int), colors.shape[0])
    new_colors[label_set, :] = colors[indices, :]
    return new_colors


def get_default_colormap():
    """Get colormap from PIL
    
    Returns:
        colors (num_colors x 3 (rgb) uint8 numpy array)
    """
    colors = np.empty((len(ImageColor.colormap), 3), dtype=np.uint8)
    for i, (k, v) in enumerate(sorted(ImageColor.colormap.items())):
        colors[i, :] = ImageColor.getrgb(v)
    return colors


def add_alpha_column(colors):
    """Add an alpha column to colors

    Args:
        colors (num_colors x 3 (rgb) uint8 numpy array)

    Returns:
        colors (num_colors x 4 (rgba) uint8 numpy array)

    Raises:
        RuntimeError: The array is not num_colors x 3.

    """
    if colors.shape[1] != 3:
        raise RuntimeError('The colors should be num_colors x 3 (rgb) array. '
                           'Instead, a shape', colors.shape, 'is used.')
    alphas = MAX_UINT8 * np.ones((colors.shape[0], 1), dtype=np.uint8)
    colors = np.hstack([colors, alphas])
    return colors
