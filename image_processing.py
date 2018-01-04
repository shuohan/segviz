# -*- coding: utf-8 -*-

"""Utilities for simple image processing

"""
import numpy as np
from PIL import Image


def rescale_image_to_uint8(image, min_val=MIN_UINT8, max_val=MAX_UINT8):
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


def assign_colors_to_label_image(label_image, colors):
    """Assign colors to a label image

    The values of `label_image` are corresponding to the row indices of the
    array colors. The 0 values of `label_image` is assumed to be background so
    the first row of `colors` has 0 alpha.  

    Args:
        label_image (int numpy array): Can be 3D or 2D.
        colors (num_colors x 4 (rgba) numpy array): The colors array. The number
            of colors should be greater than the maximal label value. The first
            colors is assumed to be background and the alphs is set to zero.

    Returns:
        colorful_label_image (uint8 numpy array): The last dimension is rgba.

    Raises:
        RuntimeError: If the shape of the colors is not num_colors x 4 (rgba)

    """
    if colors.shape[0] != 4:
        raise RuntimeError('The shape of the colors should be num_colors x 4 '
                           '(rgba). Instead, shape', colors.shape, 'is used.')
    colors[0, 3] = 0 # background alpha
    colorful_label_image = colors[label_image, :]
    return colorful_label_image


def compose_image_and_labels(image, label_image, alpha):
    """Compose image and a label image
    
    Alpha composition of `image` and the corresponding `label_image`
    (segmentation or parcellation). `label_image` is a rgba array and `image`
    will be rendered as a grayscale image. `alpha` will be applied to
    `label_image`.

    Args:
        image (dim1 x dim2 unit8 numpy image)
        label_image (dim1 x dim2 x 4 (rgba) unit8 numpy image)
        alpha (float): The alpha value of labels. Should be in [0, 1] and the
        function will scale it to [0, 255].

    Returns:
        composite_image (2D PIL image)

    """
    label_image[:, :, 3] = label_image[:, :, 3] * alpha
    image_pil = convert_grayscale_image_to_pil(image)
    label_image_pil = Image.fromarray(label_image).convert('RGBA')
    composite_image = Image.alpha_composite(image_pil, label_image_pil)
    return composite_image


def convert_grayscale_image_to_pil(image):
    """Convert a 2D grayscale image to PIL image

    Args:
        image (dim1 x dim2 uint8 numpy array):

    Returns:
        image_pil (2D PIL image)

    """
    image = np.repeat(image[:, :, None], 3, 2)
    image_pil = Image.fromarray(image).convert('RGBA')
    return image_pil
