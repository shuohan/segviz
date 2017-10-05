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
                         'whose columns are R, G, B; the order of the rows '
                         'corresponds to the ascent of label values (check -r '
                         'for more details; the first label value (normally 0) '
                         'corresponds to the background whose color alpha will '
                         'be set to 0 during visualization')
parser.add_argument('-a', '--alpha', help='transparency of the label image',
                    default=0.5, required=False)
parser.add_argument('-i', '--sliceid', help='slice no.', default=None,
                    type=int, required=False)
parser.add_argument('-r', '--use-reference', action='store_true', default=False,
                    help='by default, the value of a label is directly the '
                         'index of a color; in case the colors is only stored '
                         'in the order of the ascent of the label values (for '
                         'example, labels are 2, 5, 10, but there are only '
                         'three colors, we need to convert 2, 5, 10 to '
                         '0, 1, 2), use this option to create a index '
                         '"reference", then the color is get via '
                         'colors[ref[label_val]]')
args = parser.parse_args()

image_path = args.image
labels_path = args.labels

if args.colors is None:
    from PIL import ImageColor
    colors = np.empty((len(ImageColor.colormap), 3))
    for i, (k, v) in enumerate(sorted(ImageColor.colormap.items())):
        colors[i, :] = ImageColor.getrgb(v)
    colors = colors / 255
else:
    colors = np.load(colors_path)

alpha = args.alpha

image = np.swapaxes(nib.load(image_path).get_data(), 0, 1)
labels = np.swapaxes(nib.load(labels_path).get_data(), 0, 1).astype(np.int32)

if args.sliceid is None:
    sliceid = int(image.shape[2] / 2)
else:
    sliceid = args.sliceid

alphas = alpha * np.ones((colors.shape[0], 1))
alphas[0] = 0
colors = np.hstack([colors, alphas])

if args.use_reference:
    label_set = np.unique(labels)
    new_colors = np.empty((np.max(label_set)+1, colors.shape[1]))
    indices = np.mod(np.arange(len(label_set), dtype=int), colors.shape[0])
    print(indices)
    new_colors[label_set, :] = colors[indices, :]
    colors = new_colors

image_slice = image[:, :, sliceid]
stacked_image = np.repeat(image_slice[:, :, None], 3, 2)
labels_slice = labels[:, :, sliceid]
stacked_labels = colors[labels_slice, :]

image_pil = smp.toimage(stacked_image).convert('RGBA')
labels_pil = smp.toimage(stacked_labels).convert('RGBA')
overlay_pil = Image.alpha_composite(image_pil, labels_pil)
overlay_pil.show()
