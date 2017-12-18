#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt

filename = os.path.join('data', '0935_mprage_deface.nii')
data = nib.load(filename).get_data()
print(data.shape)

plt.figure()
plt.imshow(data[:, :, 100].T, cmap='gray')
plt.show()
