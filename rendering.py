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


def concatenate_pils(images):
    """Concatenate images to a grid

    Args:
        images (nested list of PIL images): [[im1, im2, im3], [im4, im5, im6]]
            will be converted to a 2 x 3 concatenated picture

    Returns:
        result (2D PIL image)

    """
    widths = list()
    heights = list()
    for image_row in images:
        ws, hs = zip(*[image.size for image in image_row])
        widths.append(ws)
        heights.append(heights)
    widths = np.array(widths)
    heights = np.array(heights)

    # the height per row is determined by the max height of this row
    # the width per column is determined by the max width of this column
    max_widths_per_column = np.max(widths, axis=0)
    max_heights_per_row = np.max(heights, axis=1)
    width = np.sum(max_widths_per_column)
    height = np.sum(max_heights_per_row)
    result = Image.new('RGBA', (width, height))

    w_offset = 0
    h_offset = 0
    for image_row, h in zip(all_pils, max_heights_per_row):
        for image, w in zip(image_row, max_widths_per_column):
            result.paste(image, (w_offset, h_offset))
            w_offset += w
        w_offset = 0
        h_offset += h

    return result
