#!/usr/bin/env bash

../scripts/convert_nii -i image.nii.gz -v axial -o results_convert/image_axial
../scripts/convert_nii -i image.nii.gz -v coronal -o results_convert/image_coronal -q -A -C -R -P 0 0 255 255
../scripts/convert_nii -i image.nii.gz -l label.nii.gz -v coronal -o results_convert/pair_coronal -q -a 0.5 -C
../scripts/convert_nii -i image.nii.gz -l label.nii.gz -v coronal -o results_convert/pair_coronal_reindex -q -a 0.8 -r -S -E 1 -s
../scripts/convert_nii -i image.nii.gz -l label.nii.gz -c colormap.txt -v sagittal -o results_convert/edge_sagittal_colormap -q -a 1 -e -d 3 -s -C -S -t 10
