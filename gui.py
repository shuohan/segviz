# -*- coding: utf-8 -*-

"""Classes constructing the GUI

"""

import os
from PyQt5.QtCore import QDir, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QCheckBox, QFileDialog, QGridLayout,
                             QGroupBox, QHBoxLayout, QLabel, QPushButton,
                             QSizePolicy, QSpinBox, QVBoxLayout, QWidget)
from PIL.ImageQt import ImageQt

from rendering import ImageRenderer


class ImageWindow(QLabel):
    """ Provide a window containing the overlay picture

    Args:
        image_path (file, *.nii or *.nii.gz): The path to the image to show
        image_path (file, *.nii or *.nii.gz): The path to the label image on top
        slice_idx (int): The index of the current showing slice
        orient (str): The orientation {'axial', 'coronal', 'sagittal'}
        alpha (float): The alpha value in [0, 1] of the label image
        default_width (int): The original width of the image just initialization
            of the window
        default_height (int): The original height of the image just
            initialization of the window

    """

    def __init__(self, image_path, label_image_path, colors,
                 orient='axial', initial_slice_idx=None, initial_alpha=0.5,
                 need_to_convert_colors=True, output_dir=None):
        """
        Args:
            image_path (str): The path to the image to display
            label_image_path (str): The path to the labels to display
            colors (num_colors x 3 (rbg) or num_colors x 4 (rgba) numpy array):
                The colors used to color the label image
            orient (str, optional): Orientation to show; 'axial', 'coronal',
                or 'sagittal'
            initial_slice_idx (int, optional): The index of the inital slice to
                show
            initial_alpha (float, optional): The initial alpha of the labels
            need_to_convert_colors (bool): By default, the value of a label is
                directly the index of a color; in case the colors is only stored
                in the order of the ascent of the label values (for example,
                labels are 2, 5, 10, but there are only three colors, we need to
                convert 2, 5, 10 to 0, 1, 2), use this option to convert the
                colors array so that (2, 5, 10) rows of the new array has the
                (0, 1, 2) rows of the original colors
            output_dir (str): If not None, pressing enter will not save the 
                image; otherwise, the image will be save as
                {output_dir}/{image_name}_orient_{orient}_slice_{slice_idx}.png
                `image_name` will be the same with the input image

        """
        super(ImageWindow, self).__init__()
        self._image_renderer = ImageRenderer(image_path, label_image_path,
                                             colors, need_to_convert_colors)
        # setting orient requires slice_idx but setting slice_idx also requires
        # the orient
        self.image_path = image_path
        self.label_image_path = label_image_path
        self.output_dir = output_dir
        self._slice_idx = None
        self.orient = orient
        self.slice_idx = initial_slice_idx
        self.alpha = initial_alpha
        self._width_zoom = 1 # for rescaling the image during window resizing
        self._height_zoom = 1
        default_size = self._image_renderer.get_slice_size(self.orient)
        self.default_width, self.default_height = default_size
        self._update()

    @property
    def orient(self):
        return self._orient
    
    @orient.setter
    def orient(self, orient):
        if orient not in {'axial', 'coronal', 'sagittal'}:
            raise RuntimeError('Orient shoud be "axial", "coronal", or '
                               '"sagittal"')
        else:
            self._orient = orient
            # different orientation has different num slices
            if self.slice_idx is not None:
                self.slice_idx = self.slice_idx

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, new_alpha):
        if new_alpha < 0:
            self._alpha = 0
        elif new_alpha > 1:
            self._alpha = 1
        else:
            self._alpha = new_alpha

    @property
    def slice_idx(self):
        return self._slice_idx

    @slice_idx.setter
    def slice_idx(self, slice_idx):
        num_slices = self._image_renderer.get_num_slices(self.orient)
        if slice_idx is None:
            self._slice_idx = int(num_slices / 2)
        elif slice_idx < 0:
            self._slice_idx = 0
        elif slice_idx >= num_slices:
            self._slice_idx = num_slices - 1
        else:
            self._slice_idx = slice_idx

    def _update(self):
        """Update the image within the window to show

        """
        self.image_slice = self._image_renderer.get_slice(self.orient,
                                                          self.slice_idx,
                                                          self.alpha,
                                                          self._width_zoom,
                                                          self._height_zoom)
        self.setPixmap(QPixmap.fromImage(ImageQt(self.image_slice)))

    def keyPressEvent(self, e):
        """The events when pressing a key

        """
        if e.key() == Qt.Key_Left:
            self.alpha -= 0.05
        elif e.key() == Qt.Key_Right:
            self.alpha += 0.05
        elif e.key() == Qt.Key_Up:
            self.slice_idx += 1
        elif e.key() == Qt.Key_Down:
            self.slice_idx -= 1
        elif e.key() == Qt.Key_BracketLeft:
            if self.orient == 'axial':
                self.orient = 'sagittal'
            elif self.orient == 'coronal':
                self.orient = 'axial'
            elif self.orient == 'sagittal':
                self.orient = 'coronal'
        elif e.key() == Qt.Key_BracketRight:
            if self.orient == 'axial':
                self.orient = 'coronal'
            elif self.orient == 'coronal':
                self.orient = 'sagittal'
            elif self.orient == 'sagittal':
                self.orient = 'axial'
        elif e.key() == Qt.Key_Return:
            if self.output_dir is not None:
                if not os.path.isdir(self.output_dir):
                    os.makedirs(self.output_dir)
                image_name = os.path.basename(self.image_path).split('.')[0]
                slice_str = '%03d' % self.slice_idx
                output_filename = '_'.join([image_name, 'orient', self.orient,
                                            'slice', slice_str]) + '.png'
                output_filename = os.path.join(self.output_dir, output_filename)
                self.image_slice.save(output_filename, 'PNG')
                print('Save to', output_filename)
            else:
                print('Output file is not set, cannot save image')
        self._update()

    def resizeEvent(self, e):
        """The event when resizing a window

        """
        if hasattr(self, '_width_zoom') and hasattr(self, '_height_zoom'):
            self._width_zoom = self.width() / self.default_width
            self._height_zoom = self.height() / self.default_height
            self._update()
