#!/usr/bin/env python

import numpy as np
import nibabel as nib
from pathlib import Path

from segviz.render import ImageRenderer, ImagePairRenderer, ImageEdgeRenderer
from segviz.utils import load_colors
from improc3d import transform_to_coronal


def test_render():
    dirname = Path('results_render')
    dirname.mkdir(exist_ok=True)

    image_fn = 'image.nii.gz'
    label_image_fn = 'label.nii.gz'
    colors_fn = 'colormap.txt'

    image_obj = nib.load(image_fn)
    image = image_obj.get_fdata(dtype=np.float32)
    label_image = nib.load(label_image_fn).get_fdata(dtype=np.float32)
    affine = image_obj.affine
    image = transform_to_coronal(image, affine, coarse=True)
    label_image = transform_to_coronal(label_image, affine, order=0, coarse=True)
    colors = load_colors(colors_fn)
                         
    renderer = ImageRenderer(image)
    assert len(renderer) == image.shape[2]
    im = renderer[100]
    im.show()

    renderer = ImagePairRenderer(image, label_image, colors, alpha=0.5)
    assert len(renderer) == image.shape[2]
    im = renderer[100]
    im.show()

    renderer = ImageEdgeRenderer(image, label_image, colors, alpha=0.5, edge_width=3)
    assert len(renderer) == image.shape[2]
    im = renderer[100]
    im.show()

    im = renderer[105]
    im.show()

    renderer.alpha = 1 
    renderer.edge_width = 1
    im = renderer[95]
    im.show()


if __name__ == '__main__':
    test_render()
