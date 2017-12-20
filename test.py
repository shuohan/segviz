#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import nibabel as nib
import numpy as np

from reslice import Reslicer

# filename = os.path.join('data', '0935_mprage_deface.nii')
# filename = os.path.join('data', 'at1000_mprage_deface.nii')
# filename = os.path.join('data', 'at1000_manual_cerebellum.nii')
filename = os.path.join('data', 'sub-AT1121_ses-kwyjibo20051026_MPRAGEPre_reg_macruise.nii.gz')
obj = nib.load(filename)
data = obj.get_data()
affine = obj.affine

reslicer = Reslicer(data, affine, 0)
# axial = reslicer.to_axial()
coronal = reslicer.to_coronal()
# sagittal = reslicer.to_sagittal()
new_filename = 'test.nii.gz'
new_obj = nib.Nifti1Image(coronal, np.eye(4), obj.header)
new_obj.to_filename(new_filename)

# import matplotlib.pyplot as plt
# plt.figure()
# # plt.subplot(1, 3, 1)
# # plt.imshow(sagittal[:, :, 90], cmap='gray')
# # plt.subplot(1, 3, 2)
# plt.imshow(axial[:, :, 100], cmap='gray')
# # plt.subplot(1, 3, 3)
# # plt.imshow(coronal[:, :, 100], cmap='gray')
# plt.show()
