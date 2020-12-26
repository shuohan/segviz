#!/usr/bin/env python

import numpy as np
from pathlib import Path

from segviz.utils import load_colors


dirname = Path('results_utils')
dirname.mkdir(exist_ok=True)

def test_load_colors():
    rgb_fn = dirname.joinpath('rgb.npy')
    rgb = [[0.8, 0.1, 0.99],
           [0.1, 0, 0.5]]
    np.save(rgb_fn, rgb)

    rgb = (np.array(rgb) * 255).astype(np.uint8)
    rgb = np.hstack([rgb, [[255], [255]]])

    assert np.array_equal(rgb, load_colors(rgb_fn, mode=1))

    rgba_fn = dirname.joinpath('rgba.npy')
    rgba = [[255, 255, 255, 255],
            [120, 0, 23, 10]]
    np.save(rgba_fn, rgba)

    lrgba = load_colors(rgba_fn, mode=255)
    assert np.array_equal(rgba, lrgba)
    assert lrgba.dtype == np.uint8

    txt = ('################################################\n'
           '# ITK-SnAP Label Description File\n'
           '# File format:\n'
           '# IDX   -R-  -G-  -B-  -A--  VIS MSH  LABEL\n'
           '# Fields:\n'
           '#    IDX:   Zero-based index\n'
           '#    -R-:   Red color component (0..255)\n'
           '#    -G-:   Green color component (0..255)\n'
           '#    -B-:   Blue color component (0..255)\n'
           '#    -A-:   Label transparency (0.00 .. 1.00)\n'
           '#    VIS:   Label visibility (0 or 1)\n'
           '#    IDX:   Label mesh visibility (0 or 1)\n'
           '#  LABEL:   Label description\n'
           '################################################\n'
           '    0     0    0    0     0    0   0  "Clear Label"\n'
           '    3   255  255  150     1    1   1  "Label 1"')
    txt_fn = dirname.joinpath('colors.txt')
    with open(txt_fn, 'w') as txt_file:
        txt_file.writelines(txt)
    colors = [[0, 0, 0, 0],
              [0, 0, 0, 0], 
              [0, 0, 0, 0], 
              [255, 255, 150, 255]]

    lcolors = load_colors(txt_fn)
    assert np.array_equal(colors, lcolors)
    assert lcolors.dtype == np.uint8

    print('success')


if __name__ == '__main__':
    test_load_colors()
