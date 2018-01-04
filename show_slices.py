#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

from io import load_colors
from rendering import ImageRenderer, concatenate_pils, get_default_colormap

from PIL import Image


if __name__ == '__main__':

    description = ('show slices of labels on top of image. Multiple slices are '
                   'placed in a grid. Each row contains multiple slices of a '
                   'single image along a specific orientation. For an image, '
                   'axial, coronal, sagittal slices will be placed in '
                   'consecutive rows. Slices will be displayed in ascent.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-p', '--input-pair', nargs='+', required=True,
                        metavar=('IMAGE', 'LABEL_VOLUME'), action='append',
                        help='image and label_volume pair; label_volume is '
                             'optional. Multiple pairs are acceptable.')
    parser.add_argument('-c', '--colors', default=None, required=False,
                        help='a numpy file containing the colors of labels; '
                             'the loaded colors should be a num_colors x 3 '
                             'array whose columns are R, G, B; the order of '
                             'the rows corresponds to the ascent of label '
                             'values (check -r for more details; the first '
                             'label value (normally 0) corresponds to the '
                             'background whose color alpha will be set to 0 '
                             'during visualization; if `None`, a default '
                             'colormap will be used.')
    parser.add_argument('-a', '--alpha', help='transparency of the label image',
                        default=0.5, required=False, type=float)
    parser.add_argument('-as', '--axial-slices', default=None, type=int, 
                        help='indices of axial slices to show', required=False,
                        nargs='+')
    parser.add_argument('-cs', '--coronal-slices', default=None, type=int, 
                        help='indices of coronal slices to show', required=False,
                        nargs='+')
    parser.add_argument('-ss', '--sagittal-slices', default=None, type=int, 
                        help='indices of sagittal slices to show',
                        required=False, nargs='+')
    parser.add_argument('-s', '--max-num-slices-in-row', default=0, type=int,
                        help='if 0, all slices of an image along an '
                             'orientation will be placed in a row. If greater '
                             'than 0, '
                             '`mod(num_slices, max_num_slices_in_row) + 1` '
                             'blocks will be displaced. TODO')
    parser.add_argument('-min', '--min', type=int, default=0, required=False,
                        help='min cutoff value of image, a value in [0, 1]' '
                             'if the value is less than 0, the intensity of an '
                             'image is first scaled to this minimal value and '
                             'new values less than 0 will be set to zero.')
    parser.add_argument('-max', '--max', type=int, default=1, required=False,
                        help='max cutoff value of image, a value in [0, 1]; '
                             'if the value is greater than 1, the intensity of '
                             'an image is first scaled to this maximal value '
                             'and new values greater than 1 will be set to 1.')
    parser.add_argument('-r', '--convert_colors', action='store_true',
                        help='by default, the value of a label is directly the '
                             'index of a color; in case the colors is only '
                             'stored in the order of the ascent of the label '
                             'values (for example, labels are 2, 5, 10, but '
                             'there are only three colors, we need to convert '
                             '2, 5, 10 to 0, 1, 2), use this option to convert '
                             'the colors array so that (2, 5, 10) rows of the '
                             'new array has the (0, 1, 2) rows of the original '
                             'colors.', default=False)
    parser.add_argument('-o', '--output-filename', type=str, required=False,
                        help='the path to the file to store the composite '
                             'slices. If `None`, the slices will be displayed '
                             'instead of stored.', default=None)
    args = parser.parse_args()

    slice_indices = dict(axial=args.axial_slices, coronal=args.coronal_slices,
                         sagittal=args.sagittal_slices)
    num_columns = max([len(slices) for slices in (args.axial_slices,
                                                  args.coronal_slices,
                                                  args.sagittal_slices)])
    # construct grid 
    colors = load_colors(args.colors)
    slices = list()
    for image, label_image in args.input_pair:
        ir = ImageRenderer(image, label_image, colors, args.convert_colors)
        ir.rescale_image(args.min, args.max)
        row = list()
        for orient in sorted(slice_indices.keys):
            for si in slice_indices[orient]:
                row.append(ir.get_slice(orient, si, args.alpha))
            for i in range(num_columns - len(slice_indices[orient])):
                row.append(Image.fromarray(np.empty((0, 0))))
        slices.append(row)
    grid = concatenate_pils(slices)

    if args.output_filename is None:
        grid.show()
    else:
        print('saving')
        grid.save(args.output_filename, 'PNG')
