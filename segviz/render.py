# -*- coding: utf-8 -*-

"""Functions about rendering

"""
import nibabel as nib
import numpy as np
from scipy.ndimage.morphology import binary_erosion
from PIL import Image, ImageColor

from .image_processing import rescale_image_to_uint8, assign_colors
from .image_processing import compose_image_and_labels, quantile_scale
from .reslice import Reslicer

MIN_UINT8 = 0
MAX_UINT8 = 255

class ImageRenderer:
    """Render image

    """
    def __init__(self, image_path, use_affine=True):
        """
        Args:
            image_path (str): the path to the image

        """
        image_nib = nib.load(image_path)
        self.use_affine = use_affine
        self._image = image_nib.get_data()
        if self.use_affine:
            self._affine = image_nib.affine
        else:
            self._affine = image_nib.affine.round()

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
    def automatic_rescale(self):
        self._image = quantile_scale(self._image)
        for orient, images in self._oriented_images.items():
            if images['image'] is not None:
                images['image'] = quantile_scale(images['image'])

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
    def __init__(self, image_path, label_image_path, colors, use_affine=True,
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
        self.use_affine = use_affine
        self._image = image_nib.get_data()
        if use_affine:
            self._affine = image_nib.affine
        else:
            self._affine = image_nib.affine.round()

        label_image_nib = nib.load(label_image_path)
        self._label_image = np.round(label_image_nib.get_data()).astype(int)
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


class ImageEdgeRenderer(ImagePairRenderer):
    """ Render image and its corresponding label_image

    Only the edge of each label mask is colored

    Args: 

    """
    def __init__(self, image_path, label_image_path, colors, use_affine=True,
                 need_to_convert_colors=False, edge_width=1):
        super().__init__(image_path, label_image_path, colors, use_affine,
                         need_to_convert_colors)
        self.edge_width = edge_width

    def assign_colors(self, orient):
        """ Assign colors to label image along an orientation

        Args:
            orient (str): 'axial', 'coronal', 'sagittal'

        """
        label_image = self._oriented_images[orient]['label_image']
        for label in np.unique(label_image):
            mask = label_image == label
            erosion = binary_erosion(mask, iterations=self.edge_width)
            label_image[erosion] = 0
        colored =  assign_colors( label_image, self._colors)
        self._oriented_images[orient]['colored_label_image'] = colored
