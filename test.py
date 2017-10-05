#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import nibabel as nib
import scipy.misc as smp
from PIL import Image, ImageChops

parser = argparse.ArgumentParser(description='show labels on top of image')
parser.add_argument('image')
parser.add_argument('labels')
parser.add_argument('-c', '--colors', default=None, required=False,
                    help='a numpy file containing the colors of labels; the '
                         'loaded colors should be a num_colors x 3 array '
                         'whose columns are R, G, B; the order of the rows is '
                         'corresponding to the ascent of label values; the '
                         'first label value (normally 0) corresponds to the '
                         'background whose color alpha will be set to 0 during '
                         'visualization')
parser.add_argument('-a', '--alpha', help='transparency of the label image',
                    default=0.5, required=False)
parser.add_argument('-n', '--slice-num', help='slice no. ', default=None, 
                    required=False)
args = parser.parse_args()

image_path = args.image
labels_path = args.labels
if args.colors is None:
    from PIL import ImageColor
    colors = np.empty((len(ImageColor.colormap), 3))
    for i, (k, v) in enumerate(sorted(ImageColor.colormap.items())):
        colors[i, :] = ImageColor.getrgb(v)
    colors = colors / 255
print(colors)

sliceid = 100
alpha = 0.3

image = np.swapaxes(nib.load(image_path).get_data(), 0, 1)
labels = np.swapaxes(nib.load(labels_path).get_data(), 0, 1).astype(np.int32)

# colors = np.load(colors_path)
alphas = alpha * np.ones((colors.shape[0], 1))
alphas[0] = 0
colors = np.hstack([colors, alphas])

label_set = np.unique(labels)
refs = np.empty(np.max(label_set)+1, dtype=int)
refs[label_set] = np.mod(np.arange(len(label_set)), colors.shape[0])

image_slice = image[:, :, sliceid]
stacked_image = np.repeat(image_slice[:, :, None], 3, 2)
labels_slice = labels[:, :, sliceid]
stacked_labels = colors[refs[labels_slice], :]

image_pil = smp.toimage(stacked_image).convert('RGBA')
labels_pil = smp.toimage(stacked_labels).convert('RGBA')
overlay_pil = Image.alpha_composite(image_pil, labels_pil)
overlay_pil.show()
