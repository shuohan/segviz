# -*- coding: utf-8 -*-

"""Utilities for simple image processing

"""

import numpy

def rescale_image_to_uint8(image, min_val, max_val):
    """Rescale image to the specified uint8 range

    Linearly rescale an image to the range [min_val, max_val]. This range should
    be within [0, 255] for a uint8 image. This can be viewed as applying a
    simple histogram tranform:
          -----
         /
        /
    ___/

    Args:
        image (numpy array): The image to rescale
        min_val (uint8): The result minial intensity value; >= 0
        max_val (uint8): The result maximal intensity value; <= 255

    Returns:
        rescaled_image (numpy array): The rescaled image

    """
    MIN_UINT8 = 0
    MAX_UINT8 = 255

    image = image.astype(float)
    orig_min = np.min(image)
    orig_max = np.max(image)

    # rescale to [0, 1] first
    rescaled_image = (image - orig_min) / (orig_max - orig_min)

    # rescale to [min_val, max_val]
    min_val = float(min_val)
    max_val = float(max_val)
    rescaled_image = rescaled_image * (max_val - min_val) + min_val

    # cut off values out of [MIN_UINT8, MAX_UINT8]
    rescaled_image[rescaled_image>MAX_UINT8] = MAX_UINT8
    rescaled_image[rescaled_image<MIN_UINT8] = MIN_UINT8

    rescaled_image = rescaled_image.astype(np.uint8)

    return rescaled_image
