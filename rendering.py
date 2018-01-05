# -*- coding: utf-8 -*-

"""Functions about rendering

"""
import nibabel as nib
import numpy as np
from PIL import Image, ImageColor

from nibabel_affine.reslice import Reslicer
from image_processing import rescale_image_to_uint8
from image_processing import assign_colors_to_label_image

MIN_UINT8 = 0
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
        color_shape = ' x '.join([str(s)for s in colors.shape])
        raise RuntimeError('The colors should be num_colors x 3 (rgb) array. '
                           'Instead, a shape %s is used.' % color_shape)
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
        size = list(zip(*[image.size for image in image_row]))
        if len(size) == 2:
            widths.append(ws)
            heights.append(hs)
    if len(widths) == 0 or len(heights) == 0:
        return Image.new('RGB', (0, 0))
    else:
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


class ImageRenderer:

    """ Render image and its corresponding label_image.

    This class takes an 3D image and its label image as inputs. By setting alpha
    and slice index, it can output a alpha-composed 2D slice. This class can
    also handle orientation.

    Args: 

    """
    def __init__(self, image_path, label_image_path, colors,
                 need_to_convert_colors=False):
        """
        Args:
            image_path (str): the path to the image
            label_image_path (str): the path to the corresponding label image
            colors (num_colors x 4 (rbga) numpy array): num_colors should be
                larger than or equal to the maxmimal label value
                row is assumed to be background so the alpha should be 0
            need_to_convert_colors (bool): By default, the value of a label is
                directly the index of a color; in case the colors is only stored
                in the order of the ascent of the label values (for example,
                labels are 2, 5, 10, but there are only three colors, we need to
                convert 2, 5, 10 to 0, 1, 2), use this option to convert the
                colors array so that (2, 5, 10) rows of the new array has the
                (0, 1, 2) rows of the original colors

        """
        image_nib = nib.load(image_path)
        self._image = image_nib.get_data()
        self._image_affine = image_nib.affine

        label_image_nib = nib.load(label_image_path)
        self._label_image = label_image_nib.get_data().astype(int)
        if need_to_convert_colors:
            colors = convert_colors(colors, np.unique(self._label_image))
        if colors.shape[1] == 3:
            colors = add_alpha_column(colors)
        elif colors.shape[1] != 4:
            color_shape = ' x '.join([str(s)for s in colors.shape])
            raise RuntimeError('The colors should be num_colors x 3 (rgb) or '
                               'num_colors x 4 (rgba) array. Instead, a shape '
                               '%s is used.' % color_shape)
        self._label_image = assign_colors_to_label_image(self._label_image,
                                                         colors)
        self._axial_image = None
        self._axial_label_image = None
        self._coronal_image = None
        self._coronal_label_image = None
        self._sagittal_image = None
        self._sagittal_label_image = None

        self.rescale_image(0, 1)

    def rescale_image(self, min_val, max_val):
        """Rescale image intensity to [min_val, max_val]

        Other details see function rescale_image_to_uint8

        Args:
            min_val (float >= 0): The lower limit of the intensity
            max_val (float <= 1): The upper limit of the intensity

        """
        self._image = rescale_image_to_uint8(self._image, min_val, max_val)
        for orient in ('axial', 'coronal', 'sagittal'):
            image_along_orient = getattr(self, '_%s_image' % orient)
            if image_along_orient is not None:
                image_along_orient = rescale_image_to_uint8(image_along_orient,
                                                            min_val, max_val)
                setattr(self, '_%s_image' % orient, image_along_orient)

    def get_slice(self, orient, slice_id, alpha):
        """ Get a alpha-composition of a slice at an orientation

        Args:
            orient (str): {'axial', 'coronal', 'sagittal'}
            slice_id (int)
            alpha (float): [0, 1]

        Returns:
            composite_slice (PIL image): alpha-composite 2D image slice

        """
        image_along_orient = getattr(self, '_%s_image' % orient)
        label_image_along_orient = getattr(self, '_%s_label_image' % orient)
        if image_along_orient is None or label_image_along_orient is None:
            image_reslicer = Reslicer(self._image_data, self._image_affine,
                                      order=1)
            label_image_reslicer = Reslicer(self._label_image_data,
                                            self._image_affine, order=0)
            transformed_image = getattr(image_reslicer, 'to_%s' % orient)
            transformed_label_image = getattr(label_image_reslicer,
                                              'to_%s' % orient)
            setattr(self, '_%s_image' % orient, transformed_image)
            setattr(self, '_%s_label_image' % orient, transformed_label_image)

        slice_id = self._trim_slice_id(slice_id)
        image_slice = image_along_orient[:, :, slice_id]
        label_image_slice = label_image_along_orient[:, :, slice_id, :]
        label_image_slice = np.squeeze(label_image_slice)
        composite_slice = compose_image_and_labels(image_slice,
                                                   label_image_slice, alpha)
        return composite_slice

    def _trim_slice_id(self, slice_id):
        """Trim the slice_id to [0, max_num_slices]

        Args:
            slice_id (int): The index of the slice to show

        Returns:
            slice_id (int): Trimed index
            
        """
        max_num_slices = self._image_nib.shape[2]
        if slice_id < 0:
            slice_id = 0
        elif slice_id >= max_num_slices:
            slice_id = max_num_slices - 1
        return slice_id
