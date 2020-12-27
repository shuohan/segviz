#!/usr/bin/env bash

../scripts/convert_nii -i image.nii.gz -v axial -o results_convert/image_axial
../scripts/convert_nii -i image.nii.gz -v coronal -o results_convert/image_coronal -q -A
../scripts/convert_nii -i image.nii.gz -l label.nii.gz -v coronal -o results_convert/pair_coronal -q -a 0.5
../scripts/convert_nii -i image.nii.gz -l label.nii.gz -v coronal -o results_convert/pair_coronal_reindex -q -a 0.8 -r
../scripts/convert_nii -i image.nii.gz -l label.nii.gz -c colormap.txt -v sagittal -o results_convert/edge_sagittal_colormap -q -a 1 -e -d 3 -s
