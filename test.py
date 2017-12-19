#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import numpy as np
import nibabel as nib
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage.interpolation import map_coordinates
from scipy.ndimage import affine_transform
import numpy.linalg as npl

filename = os.path.join('data', '0935_mprage_deface.nii')
# filename = os.path.join('data', 'at1000_mprage_deface.nii')
obj = nib.load(filename)
data = obj.get_data()

affine = obj.affine

# NOTE: use corner coords instead of the whole mesh?
x, y, z = data.shape
xmesh, ymesh, zmesh = np.meshgrid(np.arange(x), np.arange(y), np.arange(z))
interp = RegularGridInterpolator((np.arange(x), np.arange(y), np.arange(z)),
                                 data, bounds_error=False, fill_value=0.0)
xcoords = xmesh.flatten()[..., None]
ycoords = ymesh.flatten()[..., None]
zcoords = zmesh.flatten()[..., None]
coords = np.hstack((xcoords, ycoords, zcoords, np.ones(xcoords.shape))).T
physical_coords = affine.dot(coords)
min_physical_coords = np.min(physical_coords, axis=1)
max_physical_coords = np.max(physical_coords, axis=1)
offset = np.hstack((np.vstack((np.eye(3), np.zeros((1, 3)))),
                    min_physical_coords[..., None]))

inv_affine = npl.inv(affine).dot(offset)
physical_shape = np.ceil((max_physical_coords - min_physical_coords)[:3] + 1)
x, y, z = physical_shape 
xmesh, ymesh, zmesh = np.meshgrid(np.arange(x), np.arange(y), np.arange(z))
xcoords = xmesh.flatten()[..., None]
ycoords = ymesh.flatten()[..., None]
zcoords = zmesh.flatten()[..., None]
coords = np.hstack((xcoords, ycoords, zcoords, np.ones(xcoords.shape))).T
vox_coords = inv_affine.dot(coords)

transformed_data_2 = np.reshape(map_coordinates(data, vox_coords[:3, :]),
                                xmesh.shape)

import matplotlib.pyplot as plt
plt.figure()
plt.imshow(transformed_data_2[:, :, 100], cmap='gray')
plt.show()
