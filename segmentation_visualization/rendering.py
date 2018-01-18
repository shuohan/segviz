# -*- coding: utf-8 -*-

"""Functions about rendering

"""
import nibabel as nib
import numpy as np
from PIL import Image, ImageColor

from .image_processing import rescale_image_to_uint8, assign_colors
from .image_processing import compose_image_and_labels
from .reslice import Reslicer

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


def concatenate_pils(images, bg_color):
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
            widths.append(size[0])
            heights.append(size[1])
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
    result = Image.new('RGBA', (width, height), color=bg_color)

    w_offset = 0
    h_offset = 0
    for image_row, h in zip(images, max_heights_per_row):
        for image, w in zip(image_row, max_widths_per_column):
            image_width, image_height = image.size
            dw = int((w - image_width) / 2)
            dh = int((h - image_height) / 2)
            result.paste(image, (w_offset + dw, h_offset + dh))
            w_offset += w
        w_offset = 0
        h_offset += h

    return result


def resize_pil(image, width_zoom, height_zoom, keep_wh_ratio=True):
    """Resize a Pillow image

    Args:
        image (PIL): The image to resize
        width_zoom (float > 0): New width will be width_ratio x orig_width
        height_zoom (float > 0): New height will be height_ratio x orig_height
        keep_wh_ratio (bool): Keep the width/height ratio

    """

    orig_width, orig_height = image.size
    width = width_zoom * orig_width
    height = height_zoom * orig_height
    if keep_wh_ratio:
        orig_width_height_ratio = orig_width / orig_height
        new_width_height_ratio = width / height
        if new_width_height_ratio > orig_width_height_ratio:
            width = height * orig_width_height_ratio
        if new_width_height_ratio < orig_width_height_ratio:
            height = width / orig_width_height_ratio
    new_size = (int(width), int(height))
    resized_image = image.resize(new_size, Image.BILINEAR)
    return resized_image


class ImageRenderer:
    """Render image

    """
    def __init__(self, image_path):
        """
        Args:
            image_path (str): the path to the image

        """
        image_nib = nib.load(image_path)
        self._image = image_nib.get_data()
        self._affine = image_nib.affine

        self._oriented_images = {'axial': dict(image=None),
                                 'coronal': dict(image=None),
                                 'sagittal': dict(image=None)}

        self.rescale_image(0, 1)

    def get_slice(self, orient, slice_id, width_zoom=1, height_zoom=1):
        """ Get a alpha-composition of a slice at an orientation

        Args:
            orient (str): {'axial', 'coronal', 'sagittal'}
            slice_id (int)
            width_zoom (float > 0): The scaling factor of width
            height_zoom (float > 0): The scaling factor of height
                
                The width/height ratio is unchanged, the final size is
                determined by width_zoom and height_zoom together

        Returns:
            image (PIL image): The selected slice of the image

        """
        oriented_images = self._oriented_images[orient]
        if oriented_images['image'] is None:
            self.initialize_oriented_images(orient)
        slice_id = self._trim_slice_id(orient, slice_id)
        image = oriented_images['image'][:, :, slice_id]
        image = Image.fromarray(image, 'L')
        return image

    def initialize_oriented_images(self, orient):
        """ Initialize images along an orientation
        
        Args:
            orient (str): 'axial', 'coronal', 'sagittal'

        """
        image_reslicer = Reslicer(self._image, self._affine, order=1)
        self._oriented_images[orient]['image'] = image_reslicer.to_view(orient)

    def get_num_slices(self, orient):
        """Get the number of slices along an orientation

        Args:
            orient (str): 'axial', 'coronal', 'sagittal'

        """
        if self._oriented_images[orient]['image'] is None:
            self.initialize_oriented_images(orient)
        return self._oriented_images[orient]['image'].shape[2]

    def get_slice_size(self, orient):
        """Get the width and height of slices along an orientation

        Args:
            orient (str): 'axial', 'coronal', 'sagittal'

        """
        if self._oriented_images[orient]['image'] is None:
            self.initialize_oriented_images(orient)
        width = self._oriented_images[orient]['image'].shape[1] 
        height = self._oriented_images[orient]['image'].shape[0] 
        return width, height

    def rescale_image(self, min_val, max_val):
        """Rescale image intensity to [min_val, max_val]

        Other details see function rescale_image_to_uint8

        Args:
            min_val (float >= 0): The lower limit of the intensity
            max_val (float <= 1): The upper limit of the intensity

        """
        min_val = min_val * MAX_UINT8
        max_val = max_val * MAX_UINT8
        self._image = rescale_image_to_uint8(self._image, min_val, max_val)
        for orient, images in self._oriented_images.items():
            if images['image'] is not None:
                images['image'] = rescale_image_to_uint8(images['image'],
                                                         min_val, max_val)

    def _trim_slice_id(self, orient, slice_id):
        """Trim the slice_id to [0, max_num_slices]

        Args:
            slice_id (int): The index of the slice to show

        Returns:
            slice_id (int): Trimed index
            
        """
        max_num_slices = self.get_num_slices(orient) 
        if slice_id < 0:
            slice_id = 0
        elif slice_id >= max_num_slices:
            slice_id = max_num_slices - 1
        return slice_id


class ImagePairRenderer(ImageRenderer):
    """ Render image and its corresponding label_image

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
        self._affine = image_nib.affine

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
        self._colors = colors

        self._oriented_images = {'axial': dict(image=None, label_image=None,
                                               colored_label_image=None),
                                 'coronal': dict(image=None, label_image=None,
                                                 colored_label_image=None),
                                 'sagittal': dict(image=None, label_image=None,
                                                  colored_label_image=None)}

        self.rescale_image(0, 1)

    def initialize_oriented_images(self, orient):
        """ Initialize images along an orientation
        
        Args:
            orient (str): 'axial', 'coronal', 'sagittal'

        """
        image_reslicer = Reslicer(self._image, self._affine, order=1)
        label_reslicer = Reslicer(self._label_image, self._affine, order=0)
        oriented_images = self._oriented_images[orient]
        oriented_images['image'] = image_reslicer.to_view(orient)
        oriented_images['label_image'] = label_reslicer.to_view(orient)

    def assign_colors(self, orient):
        """ Assign colors to label image along an orientation

        Args:
            orient (str): 'axial', 'coronal', 'sagittal'

        """
        self._oriented_images[orient]['colored_label_image'] = assign_colors(
            self._oriented_images[orient]['label_image'], self._colors)

    def get_slice(self, orient, slice_id, alpha, width_zoom=1, height_zoom=1):
        """ Get a alpha-composition of a slice at an orientation

        Args:
            orient (str): {'axial', 'coronal', 'sagittal'}
            slice_id (int)
            alpha (float): [0, 1]
            width_zoom (float > 0): The scaling factor of width
            height_zoom (float > 0): The scaling factor of height
                
                The width/height ratio is unchanged, the final size is
                determined by width_zoom and height_zoom together

        Returns:
            composite_slice (PIL image): alpha-composite 2D image slice

        """
        oriented_images = self._oriented_images[orient]
        if oriented_images['image'] is None:
            self.initialize_oriented_images(orient)

        slice_id = self._trim_slice_id(orient, slice_id)
        image = oriented_images['image'][:, :, slice_id]

        if oriented_images['colored_label_image'] is None:
            self.assign_colors(orient)
        label_image = oriented_images['colored_label_image'][:, :, slice_id]
        label_image = np.squeeze(label_image)

        composition = compose_image_and_labels(image, label_image, alpha)
        composition = resize_pil(composition, width_zoom=width_zoom,
                                 height_zoom=height_zoom)

        return composition
