import numpy as np
from PIL import Image


MIN_UINT8 = 0
MAX_UINT8 = 255


def assign_colors(label_image, colors):
    """Assigns colors to a label image.

    Note:
        * The values of ``label_image`` correspond to the row indices of the
          array colors.
        * The 0 values of ``label_image`` is assumed to be background, so
          the first row of ``colors`` is forced to be an alpha value of 0.  

    Args:
        label_image (numpy.ndarray[int]): The label image to assign colors to.
            It can be a 3D or 2D array.
        colors (numpy.ndarray): The colors array. Each row is the RGB value of
            the corresponding label value. The number of colors should be
            greater than the maximal label value. The first colors is assumed to
            be background and its alpha is set to zero.

    Returns:
        numpy.ndarray[uint8]: The label image with colors. The last dimension
            with a size of 4is the color value of RGBA. The other dimensions
            have the same shape with the input ``label_image``.

    Raises:
        RuntimeError: The shape of the ``colors`` is not ``num_colors x 4``
            (RGBA).

    """
    if colors.shape[1] != 4:
        color_shape = ' x '.join([str(s)for s in colors.shape])
        raise RuntimeError('The shape of the colors should be num_colors x 4 '
                           '(RGBA). Instead, shape %s is used.' % color_shape)
    colors[0, 3] = 0 # background alpha
    label_image = np.round(label_image).astype(int)
    colorful_label_image = colors[label_image, :]
    return colorful_label_image


def compose_image_and_labels(image, label_image, alpha):
    """Composes an 2D image and its corresponding label image.
    
    Alpha composition of ``image`` and its ``label_image`` (segmentation or
    parcellation). ``label_image`` is a RGBA array and ``image`` will be
    rendered as a grayscale image. The value ``alpha`` is applied to
    ``label_image``.

    Args:
        image (numpy.ndarray[uint8]): The 2D image to compose.
        label_image (numpy.ndarray): The label image to compose. The first two
            dimensions have the same shape with ``image`` and the last dimension
            has a size of 4 and contains RGBA values.
        alpha (float): The alpha value of labels. It should be in [0, 1] and
            this function will automatically scale the apha values to [0, 255].

    Returns:
        PIL.Image: The alpha-composed image.

    """
    label_image = np.copy(label_image)
    label_image[:, :, 3] = label_image[:, :, 3] * alpha
    image_pil = convert_grayscale_image_to_pil(image)
    label_image_pil = Image.fromarray(label_image).convert('RGBA')
    composite_image = Image.alpha_composite(image_pil, label_image_pil)
    return composite_image


def convert_grayscale_image_to_pil(image):
    """Converts a 2D grayscale image into a PIL image.

    Args:
        image (numpy.ndarray[uint8]): The image to convert.

    Returns:
        PIL.Image: The converted image.

    """
    image = np.repeat(image[:, :, None], 3, 2)
    image_pil = Image.fromarray(image).convert('RGBA')
    return image_pil
