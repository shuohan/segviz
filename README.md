# Medical Image Segmentation Visualization

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Show alpha-composition of an image slice and its corresponding label image.

![image](docs/source/_static/image.png) ![pair](docs/source/_static/pair.png) ![edge](docs/source/_static/edge.png)

Three modes are supported:

* Show only the image
* Show an alpha-composite of the image and its label image
* Show only the outer edges of each label region

Users can adjust:

* The intensity scales of the image
* The alpha value of the composition
* The edge width of the label image

Use [improc3d](https://gitlab.com/shan-utils/improc3d) to transform a brain image into its axial, coronal, and sagittal views.

See the [documentation](https://shan-utils.gitlab.io/segviz) for more details.
