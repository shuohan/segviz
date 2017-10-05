#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image, ImageChops
import numpy as np
import nibabel as nib
import copy
import scipy.misc as smp
from time import time
import sys

image_path = 'image.nii'
labels_path = 'labels.nii'
colors_path = '/home/shuo/projects/test_label_colors/colors.npy'

sliceid = 100
alpha = 0.1

start = time()
image = np.swapaxes(nib.load(image_path).get_data(), 0, 1)
labels = np.swapaxes(nib.load(labels_path).get_data(), 0, 1)
colors = np.load(colors_path)
print('load', time() - start)

start = time()
labels = np.digitize(labels, np.unique(labels), right=True)
print('digitize', time() - start)

mask = labels != 0
inverse_mask = np.logical_not(mask)

start = time()
overlay_image = image * mask
overlay_labels = labels * mask
rest = image * inverse_mask
print('numpy', time() - start)

start = time()
image_slice = overlay_image[:, :, sliceid]
stacked_overlay_image = np.dstack([image_slice, image_slice, image_slice])
overlay_image_pil = smp.toimage(stacked_overlay_image)

labels_slice = overlay_labels[:, :, sliceid]
stacked_labels = np.dstack([colors[labels_slice, 0], colors[labels_slice, 1], 
                            colors[labels_slice, 2]]) 
overlay_labels_pil = smp.toimage(stacked_labels)

overlay_pil = Image.blend(overlay_image_pil, overlay_labels_pil, alpha)
overlay_pil.show()

rest_slice = rest[:, :, sliceid]
stacked_rest = np.dstack([rest_slice, rest_slice, rest_slice])
rest_pil = smp.toimage(stacked_rest)
result = ImageChops.add(overlay_pil, rest_pil)

print('pil', time() - start)

result.show()
