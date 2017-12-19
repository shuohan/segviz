#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import nibabel as nib

from reslice import Reslicer

filename = os.path.join('data', '0935_mprage_deface.nii')
# filename = os.path.join('data', 'at1000_mprage_deface.nii')
obj = nib.load(filename)
data = obj.get_data()
affine = obj.affine

reslicer = Reslicer(data, affine)
# axial = reslicer.to_LPI_minus()
axial = reslicer.to_axial()
# coronal = reslicer.to_coronal()

import matplotlib.pyplot as plt
plt.figure()
plt.subplot(1, 3, 1)
plt.imshow(data[:, :, 100], cmap='gray')
plt.subplot(1, 3, 2)
plt.imshow(axial[:, :, 100], cmap='gray')
# plt.subplot(1, 3, 3)
# plt.imshow(coronal[:, :, 50], cmap='gray')
plt.show()
