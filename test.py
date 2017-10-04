#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image, ImageChops
import numpy as np
import nibabel as nib
import copy
import scipy.misc as smp
from time import time

image_path = 'image.nii'
labels_path = 'labels.nii'

sliceid = 100
alpha = 0.5

start = time()
image = np.swapaxes(nib.load(image_path).get_data(), 0, 1)
labels = np.swapaxes(nib.load(labels_path).get_data(), 0, 1)
print('load', time() - start)

mask = labels != 0
inverse_mask = np.logical_not(mask)

start = time()
overlay_image = image * mask
overlay_labels = labels * mask
rest = image * inverse_mask
print('numpy', time() - start)

start = time()
overlay_image_pil = smp.toimage(overlay_image[:, :, sliceid])
overlay_labels_pil = smp.toimage(overlay_labels[:, :, sliceid])
overlay_pil = Image.blend(overlay_image_pil, overlay_labels_pil, alpha)
rest_pil = smp.toimage(rest[:, :, sliceid])
result = ImageChops.add(overlay_pil, rest_pil)
print('pil', time() - start)

result.show()
