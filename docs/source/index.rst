Medical Image Segmentation Visualization
========================================

Code is `here <https://gitlab.com/shan-utils/segviz>`_.

Show alpha-composition of an image slice and its corresponding label image.

.. image:: _static/image.png
.. image:: _static/pair.png
.. image:: _static/edge.png

Three modes are supported:

* Show only the image
* Show an alpha-composite of the image and its label image
* Show only the outer edges of each label region

Users can adjust:

* The intensity scales of the image
* The alpha value of the composition
* The edge width of the label image

This package also provides command line tools to

* Convert a NIfTI image into PNG slices
* Generate an HTML file of a group of images
* Run a web service to view the HTML file remotely


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   examples
   api

Index
-----

* :ref:`genindex`
