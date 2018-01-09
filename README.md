# Segmentation Visualization 

## Introduction

This little tool can show the segmentation label image on top of the corresponding image. It aims to run smoothly using SSH X11 forwarding and provide simple controls of image navigation and flexible configuration. 

## Usage

The tool provides two executables `show_slices` and `interact_image`.

`show_slices` can display multiple images, orientations (axial, coronal, and sagittal), and slices simultaneously on a grid.

`interact_image` uses PyQt to interactively navigate through orientations and slices of a single image. Pressing `Up` and `Down` arrow keys can scroll through slices, pressing `Left` and `Right` arrow keys can change alpha value of labels, pressing `[` and `]` will change the image orientation (axial, coronal, and sagittal), and pressing `Enter` key will save the current slice in the window to a .png file.

The colormap and alpha value of the label image can be configured.

Check `show_slices --help` and `interact_image --help` for more details.

## Examples

The following command show 10th, 20th, and 30th axial slices, 10th and 20th coronal slices, 10th, 20th, and 30th sagittal slices of two images `image1.nii.gz` and `image2.nii.gz`. It uses the colormap contained in the file `colors.npy`, and alpha value 0.5. `-r` means remapping the colormap using the available labels in the label images.

    ./show_slices -p image1.nii.gz labels1.nii.gz -p image2.nii.gz labels2.nii.gz -as 10 20 30 -cs 10 20 -ss 10 20 30 -c colors.npy -r -a 0.5

The following command show `image.nii.gz` with its label image `labels.nii.gz` in a window. Pressing `Enter` will save the file to `./{image_filename}_orient_{orient}_slice_{slice_idx}.png`.

    ./interact_image -i image.nii.gz -l labels.nii.gz -o ./ --colors colors.npy -r
