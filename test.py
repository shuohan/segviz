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
alpha = 0.3

start = time()
image = np.swapaxes(nib.load(image_path).get_data(), 0, 1)
labels = np.swapaxes(nib.load(labels_path).get_data(), 0, 1)
colors = np.load(colors_path)
alphas = alpha * np.ones((colors.shape[0], 1))
alphas[0] = 0
colors = np.hstack([colors, alphas])
print('load', time() - start)

start = time()
labels = np.digitize(labels, np.unique(labels), right=True)
print('digitize', time() - start)

mask = labels != 0
inverse_mask = np.logical_not(mask)

start = time()
image_slice = image[:, :, sliceid]
stacked_image = np.dstack([image_slice, image_slice, image_slice])
image_pil = smp.toimage(stacked_image).convert('RGBA')

labels_slice = labels[:, :, sliceid]
print(colors[0, :])
stacked_labels = colors[labels_slice, :]
mask = stacked_labels[:, :, 3] * alpha
mask_pil = smp.toimage(mask)
labels_pil = smp.toimage(stacked_labels).convert('RGBA')

overlay_pil = Image.alpha_composite(image_pil, labels_pil)
overlay_pil.show()

print('pil', time() - start)
