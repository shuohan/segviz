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
        self.orient = orient
        self.slice_idx = initial_slice_idx
        self.alpha = initial_alpha
        self._update()

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
        if slice_idx is None:
            self._slice_idx = 0
        else:
            self._slice_idx = slice_idx

    def _update(self):
        self._image_slice = self._image_renderer.get_slice(self.orient, 
                                                           self.slice_idx,
                                                           self.alpha)
        self.setPixmap(QPixmap.fromImage(ImageQt(self._image_slice)))

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Left:
            self.alpha -= 0.05
        elif e.key() == Qt.Key_Right:
            self.alpha += 0.05
        
        self._update()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    colors = load_colors('colors.npy')
    window = ImageWindow('image.nii.gz', 'labels.nii.gz', colors,
                         initial_slice_idx=10)
    window.show()
    sys.exit(app.exec_())
