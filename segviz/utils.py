import numpy as np
from PIL import Image
from pathlib import Path
import importlib.resources


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
        numpy.ndarray[uint8]:
        The label image with colors. The last dimension
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


def reindex_colors(colors, labels):
    """Reindex the colors array using labels presented in a label image.

    Because the labels in a label image are not necessarily a series of
    consecutive integers, the ``1, ..., num_labels`` rows of the original colors
    will be mapped to ``label1, lebel2, ..., labeln`` rows of the new colors
    array. The other rows of the new colors will be set to empty colors (black
    with alpha = 0).

    Note:
        If the number of colors is less than the labels, the colors will be
        cycled around.

    For example, colors

    .. code-block:: text

        [[255,   0,   0, 255],
         [  0, 255,   0, 255]]

    will be converted into

    .. code-block:: text

        [[255,   0,   0, 255],
         [  0,   0,   0,   0],
         [  0, 255,   0, 255],
         [255,   0,   0, 255]]

    for labels 0, 2, 3.

    Args:
        colors (numpy.ndarray[uint8]): The RGBA colors to convert.
        labels (iterable[int]): The labels of the label image.

    Returns:
        numpy.ndarray: The reindexed colors.

    """
    label_set = np.unique(np.round(labels).astype(int))[1:] # remove bg color
    new_colors_shape = (np.max(label_set) + 1, colors.shape[1])
    new_colors = np.zeros(new_colors_shape, dtype=np.uint8)
    num_colors = colors.shape[0] - 1
    indices = np.mod(np.arange(len(label_set), dtype=int), num_colors) + 1
    new_colors[label_set, :] = colors[indices, :]
    return new_colors


def get_default_colormap():
    """Returns the matplotlib's tab10 colormap.

    Returns:
        numpy.ndarray[uint8]: The num_colors x 3 (RGB) colors.

    """
    background = [  0,   0,   0]
    tab_blue =   [  0, 120, 177]
    tab_orange = [255, 126,  42]
    tab_green =  [  0, 160,  58]
    tab_red =    [223,  35,  45]
    tab_purple = [153, 103, 185]
    tab_brown =  [144,  86,  76]
    tab_pink =   [235, 119, 191]
    tab_gray =   [127, 127, 127]
    tab_olive =  [187, 189,  60]
    tab_cyan =   [  0, 190, 205]
    return np.array([background, tab_blue, tab_orange, tab_green, tab_red,
                     tab_purple, tab_brown, tab_pink, tab_gray, tab_olive,
                     tab_cyan], dtype=np.uint8)


def append_alpha_column(colors):
    """Appends an alpha column to RGB colors.

    Args:
        colors (numpy.ndarray[uint8]): The num_colors x 3 array to append.

    Returns:
        numpy.ndarray[unit8]: The appended array.

    Raises:
        RuntimeError: The shape of the input ``colors`` is not num_colors x 3.

    """
    if colors.shape[1] != 3:
        color_shape = ' x '.join([str(s)for s in colors.shape])
        raise RuntimeError('The colors should be a num_colors x 3 (RGB) array. '
                           'Instead, a shape %s is used.' % color_shape)
    alphas = MAX_UINT8 * np.ones((colors.shape[0], 1), dtype=np.uint8)
    colors = np.hstack([colors, alphas])
    return colors


def concat_pils(images, bg_color=[0, 0, 0, 0]):
    """Concatenates PIL images into a grid.

    The input ``images`` should be arranged in a 2D array. The layout of the
    array is displayed as the image grid.

    Args:
        images (list[list[PIL.Image]]): The image grid.
        bg_color (list[uint8]): The RGBA background color.

    Returns:
        PIL.Image: The concatenated image grid.

    """
    widths = [[im.size[1] for im in image] for image in images]
    heights = [[im.size[0] for im in image] for image in images]

    if len(widths) == 0 or len(heights) == 0:
        return Image.new('RGB', (0, 0))

    widths = np.array(widths)
    heights = np.array(heights)
    max_widths_per_col = np.max(widths, axis=0)
    max_heights_per_row = np.max(heights, axis=1)
    grid_width = np.sum(max_widths_per_col)
    grid_height = np.sum(max_heights_per_row)

    result = Image.new('RGBA', (grid_width, grid_height), color=tuple(bg_color))

    width_offset = 0
    height_offset = 0
    for image_row, row_height in zip(images, max_heights_per_row):
        for image, col_width in zip(image_row, max_widths_per_col):
            image_width, image_height = image.size
            width_pad = int((col_width - image_width) / 2)
            height_pad = int((row_height - image_height) / 2)
            offset = (width_offset + width_pad, height_offset + height_pad)
            result.paste(image, offset)
            width_offset += col_width
        width_offset = 0
        height_offset += row_height

    return result


def load_colors(colors_path, mode=1):
    """Loads a num_colors x 4 RGBA/RGB array of colors from a .npy/.txt file.

    The .txt file should have an ITK-SNAP format. For example:

    .. code-block: text

        ################################################
        # ITK-SnAP Label Description File
        # File format:
        # IDX   -R-  -G-  -B-  -A--  VIS MSH  LABEL
        # Fields:
        #    IDX:   Zero-based index
        #    -R-:   Red color component (0..255)
        #    -G-:   Green color component (0..255)
        #    -B-:   Blue color component (0..255)
        #    -A-:   Label transparency (0.00 .. 1.00)
        #    VIS:   Label visibility (0 or 1)
        #    IDX:   Label mesh visibility (0 or 1)
        #  LABEL:   Label description
        ################################################
            0     0    0    0     0    0   0  "Clear Label"
           12   255  255  150     1    1   1  "Label 1"

    Note:
        Only fields IDX, R, G, B, and A are read from the .txt file. A blank
        color is used for each of rows that are not included in IDX.

    Args:
        colors_path (str): The path to the file with RGBA/RGB.
        mode (int): 1 or 255 for the value range if the input is .npy.

    Returns:
        numpy.ndarray: The loaded colors with shape num_colors x 4 RBGA.

    Raises:
        IOError: The file does not exist.
        ValueError: The input argument ``mode`` is not 1 or 255.
        IOError: Only .txt and .npy are supported.
        RuntimeError: The shape is not num_colors x 3 or num_colors x 4.

    TODO:
        Add support for loading from a .png file contaning a column of pixels

    """
    colors_path = Path(colors_path)
    if not colors_path.exists():
        raise IOError('The file {} does not exists.'.format(colors_path))

    if mode != 1 and mode != 255:
        message = 'Mode should be 1 or 255. Instead {} is used'.format(mode)
        raise ValueError(message)

    if colors_path.suffix == '.npy':
        colors = np.load(colors_path)
        colors = MAX_UINT8 * colors if mode == 1 else colors
        assert (colors <= 255).all() and (colors >= 0).all()
        colors = colors.astype(np.uint8)

        if colors.shape[1] != 3 and colors.shape[1] != 4:
            shape = ' x '.join([str(s)for s in colors.shape])
            message = ('The shape of the colors array should be num_colors x 3 '
                       'or num_colors x 4. Instaed {} is used.'.format(shape))
            raise RuntimeError(message)

        if colors.shape[1] == 3:
            colors = append_alpha_column(colors)

    elif colors_path.suffix == '.txt':
        with open(colors_path) as colors_file:
            lines = colors_file.readlines()
        lines = [l.strip() for l in lines if not l.strip().startswith('#')]
        lines = np.array([list(map(float, l.split()[:5])) for l in lines])
        colors = np.zeros((int(np.max(lines[:, 0])) + 1, 4), dtype=np.uint8)
        indices = lines[:, 0].astype(int)
        colors[indices, :3] = lines[:, 1 : 4].astype(np.uint8)
        colors[indices, -1] = (lines[:, -1] * MAX_UINT8).astype(np.uint8)

    else:
        message = 'The extesion of "{}" is not supported.'.format(colors_path)
        raise IOError(message)

    return colors
