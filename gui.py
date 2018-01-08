#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes constructing the GUI

"""

from PyQt5.QtCore import QDir, Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QCheckBox, QFileDialog, QGridLayout,
                             QGroupBox, QHBoxLayout, QLabel, QPushButton,
                             QSizePolicy, QSpinBox, QVBoxLayout, QWidget)
from PIL.ImageQt import ImageQt

from rendering import ImageRenderer
from file_loading import load_colors


class ImageWindow(QLabel):
    """ Provide a window containing the overlay picture

    Args:
        slice_idx (int): The index of the current showing slice
        orient (str): The orientation {'axial', 'coronal', 'sagittal'}
        alpha (float): The alpha value in [0, 1] of the label image

    """

    def __init__(self, image_path, label_image_path, colors,
                 orient='axial', initial_slice_idx=None, initial_alpha=0.5):
        super(ImageWindow, self).__init__()
        self._image_renderer = ImageRenderer(image_path, label_image_path,
                                             colors, 1)
        self._slice_idx = None
        self.orient = orient
        self.slice_idx = initial_slice_idx
        self.alpha = initial_alpha
        self._width_zoom = 1
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
        image = self._image_renderer.get_slice(self.orient, self.slice_idx,
                                               self.alpha, self._width_zoom,
                                               self._height_zoom)
        self.setPixmap(QPixmap.fromImage(ImageQt(image)))

    def keyPressEvent(self, e):
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
        self._update()

    def resizeEvent(self, e):
        if hasattr(self, '_width_zoom') and hasattr(self, '_height_zoom'):
            self._width_zoom = self.width() / self.default_width
            self._height_zoom = self.height() / self.default_height
            self._update()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    colors = load_colors('colors.npy')
    window = ImageWindow('image.nii.gz', 'labels.nii.gz', colors,
                         initial_slice_idx=10, orient='coronal')
    window.show()
    sys.exit(app.exec_())
