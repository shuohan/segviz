#!/usr/bin/env python

import numpy as np
import nibabel as nib
from pathlib import Path

from segviz.render import ImageRenderer, ImagePairRenderer, ImageEdgeRenderer
from segviz.utils import load_colors
from improc3d import transform_to_coronal, transform_to_sagittal


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
    im = renderer[140]
    im.save(dirname.joinpath('image.png'))

    renderer = ImagePairRenderer(image, label_image, colors, alpha=0.5)
    assert len(renderer) == image.shape[2]
    im = renderer[140]
    im.save(dirname.joinpath('pair.png'))

    renderer.alpha = 1
    im = renderer[140]
    im.save(dirname.joinpath('pair_a1p0.png'))

    renderer = ImageEdgeRenderer(image, label_image, colors, alpha=0.5, edge_width=3)
    assert len(renderer) == image.shape[2]
    im = renderer[140]
    im.show()

    im = renderer[145]
    im.show()

    renderer.alpha = 1 
    renderer.edge_width = 1
    im = renderer[140]
    im.show()
    im.save(dirname.joinpath('edge.png'))

    renderer.edge_width = 3
    im = renderer[140]
    im.save(dirname.joinpath('edge_e3.png'))

    image_obj = nib.load(image_fn)
    image = image_obj.get_fdata(dtype=np.float32)
    label_image = nib.load(label_image_fn).get_fdata(dtype=np.float32)
    affine = image_obj.affine
    image = transform_to_sagittal(image, affine, coarse=True)
    label_image = transform_to_sagittal(label_image, affine, order=0, coarse=True)
    colors = load_colors(colors_fn)

    renderer = ImagePairRenderer(image, label_image, colors, alpha=0.5)
    assert len(renderer) == image.shape[2]
    im = renderer[90]
    im.save(dirname.joinpath('pair_sag.png'))
    assert renderer.slice_size == (182, 218)


if __name__ == '__main__':
    test_render()
