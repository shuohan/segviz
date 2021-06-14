import numpy as np
from PIL import Image
from scipy.ndimage.morphology import binary_erosion
from improc3d import quantile_scale, calc_bbox3d

from .utils import MIN_UINT8, MAX_UINT8
from .utils import assign_colors, compose_image_and_labels


class ImageRenderer:
    """Renders slices from a 3D image using PIL.

    Note:
        The 3rd dimension is used as the slice dimension. Use `improc3d
        <https://github.com/shuohan/improc3d>`_ to reslice the image.

        >>> from improc3d import transform_to_sagittal
        >>> sagittal = transform_to_sagittal(image, lpim_affine)
        >>> renderer = ImageRenderer(sagittal)
        >>> print('Number of slices', len(renderer))
        >>> sag_slice = renderer[100]

    Attributes:
        image (numpy.ndarray): The image to render.

    """
    def __init__(self, image):
        self.image = image
        self._rescaled = image
        self.rescale_intensity()

    def automatic_rescale(self):
        """Rescales the image automatically. Works fine for T1w brain images."""
        self._rescaled = quantile_scale(self.image, lower_th=MIN_UINT8,
                                        upper_th=MAX_UINT8)
        self._rescaled = self._rescaled.astype(np.uint8)

    @property
    def slice_size(self):
        """Returns the width and height of image slices."""
        width = self.image.shape[1]
        height = self.image.shape[0]
        return width, height

    @property
    def intensity_range(self):
        """Returns the value range of the image intensities ``[vmin, vmax]``."""
        vmin = np.min(self.image)
        vmax = np.max(self.image)
        return vmin, vmax

    def rescale_intensity(self, vmin=None, vmax=None):
        """Rescales image intensity into ``[vmin, vmax]``.

        Args:
            vmin (float): Any values below ``vmin`` are set to 0.
            vmax (float): Any values above ``vmax`` are set to 255.

        """
        int_range = self.intensity_range
        vmin = int_range[0] if vmin is None else vmin
        vmax = int_range[1] if vmax is None else vmax

        self._rescaled = self.image.copy()
        self._rescaled[self._rescaled < vmin] = vmin
        self._rescaled[self._rescaled > vmax] = vmax
        self._rescaled = (self._rescaled - vmin) / (vmax - vmin)
        self._rescaled = self._rescaled * (MAX_UINT8 - MIN_UINT8) + MIN_UINT8
        self._rescaled = self._rescaled.astype(np.uint8)

    def __len__(self):
        return self.image.shape[-1]

    def __getitem__(self, ind):
        ind = self._check_slice_ind(ind)
        image_slice = self._rescaled[:, :, ind]
        image_slice = Image.fromarray(image_slice, 'L')
        image_slice = image_slice.transpose(Image.TRANSPOSE)
        return image_slice

    def _check_slice_ind(self, ind):
        if ind < 0:
            ind = 0
            print('Slice index should not be less than {}.'.format(ind))
        if ind > len(self) - 1:
            ind = len(self) - 1
            print('Slice index should not be greater than {}.'.format(ind))
        return ind


class ImagePairRenderer(ImageRenderer):
    """Renders image and its corresponding label image as an alpha-composite.

    Note:
        The attribute :attr:`label_image` will be converted into a "colored"
        image by assigning :attr:`colors` to its label values. As the input,
        it should have the same shape with :attr:`image`; after conversion, it
        will have a 4th dimension as the colors.

    Attributes:
        label_image (numpy.ndarray): The corresponding label image. It should
            have the same spatial shape with :attr:`image`.
        colors (numpy.ndarray): The num_colors x 4 RGBA colors array.
        alpha (float): The alpha value of the label image.

    """
    def __init__(self, image, label_image, colors, alpha=1.0):
        assert image.shape == label_image.shape
        super().__init__(image)
        self._alpha = alpha
        self.colors = colors
        self.label_image = label_image
        self._assign_colors()

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value
        self._assign_colors()

    def _assign_colors(self):
        self._colored_label_image = assign_colors(self.label_image, self.colors)

    def __getitem__(self, ind):
        ind = self._check_slice_ind(ind)
        image_slice = self._rescaled[:, :, ind]
        label_slice = self._colored_label_image[:, :, ind, :]
        comp = compose_image_and_labels(image_slice, label_slice, self.alpha)
        comp = comp.transpose(Image.TRANSPOSE)
        return comp

    def get_label_range(self):
        """Returns the index range of slices with non-background labels."""
        bbox = calc_bbox3d(self.label_image > 0)
        slice_range = bbox[-1]
        return slice_range.start, slice_range.stop


class ImageEdgeRenderer(ImagePairRenderer):
    """Renders an image and the outside contours (edge) of each labeled region.

    Attributes:
        edge_width (int): The width of the edge as the number of pixels.

    """
    def __init__(self, image, label_image, colors, alpha=1, edge_width=1):
        self._edge_width = edge_width
        super().__init__(image, label_image, colors, alpha)

    @property
    def edge_width(self):
        return self._edge_width

    @edge_width.setter
    def edge_width(self, width):
        self._edge_width = width
        self._assign_colors()

    def _assign_colors(self):
        """Only assigns the colors to the outside contours (edges)."""
        label_image = self.label_image.copy()
        for label in np.unique(label_image):
            mask = label_image == label
            erosion = binary_erosion(mask, iterations=self.edge_width)
            label_image[erosion] = 0
        self._colored_label_image = assign_colors(label_image, self.colors)


class CheckerboardRenderer(ImageRenderer):
    def __init__(self, image1, image2, patch_size=20, alpha=0):
        self._renderer1 = ImageRenderer(image1)
        self._renderer2 = ImageRenderer(image2)
        assert self._renderer1.slice_size == self._renderer2.slice_size
        self.patch_size = patch_size
        self.alpha = alpha

    def automatic_rescale(self):
        self._renderer1.automatic_rescale()
        self._renderer2.automatic_rescale()

    @property
    def slice_size(self):
        return self._renderer1.slice_size

    @property
    def intensity_range(self):
        vmin1, vmax1 = self._renderer1.intensity_range
        vmin2, vmax2 = self._renderer2.intensity_range
        return vmin1, vmax1, vmin2, vmax2

    def rescale_intensity(self, vmin1=None, vmax1=None, vmin2=None, vmax2=None):
        self._renderer1.rescale_intensity(vmin1, vmax1)
        self._renderer2.rescale_intensity(vmin2, vmax2)

    def __len__(self):
        return len(self._renderer1)

    def __getitem__(self, ind):
        image_slice1 = self._renderer1[ind]
        image_slice2 = self._renderer2[ind]
        image_slice = self._compose(image_slice1, image_slice2)
        return image_slice

    def _check_slice_ind(self, ind):
        assert False

    def _compose(self, image_slice1, image_slice2):
        array1 = np.array(image_slice1.convert('RGBA'), dtype=np.uint8)
        array2 = np.array(image_slice2.convert('RGBA'), dtype=np.uint8)
        height, width = array1.shape[:2]
        left = 0
        top = 0
        alpha_upper = self.alpha
        alpha = self.alpha
        while top < height:
            hstart = top
            hend = hstart + self.patch_size
            while left < width:
                wstart = left
                wend = left + self.patch_size
                array1[hstart:hend, wstart:wend, 3] = \
                    array1[hstart:hend, wstart:wend, 3] * (1 - alpha)
                array2[hstart:hend, wstart:wend, 3] = \
                    array2[hstart:hend, wstart:wend, 3] * alpha
                left = wend
                alpha = 1 - alpha
            top = hend
            left = 0
            alpha = 1 - alpha_upper
            alpha_upper = alpha

        image1 = Image.fromarray(array1)
        image2 = Image.fromarray(array2)
        composition = Image.alpha_composite(image1, image2)
        return composition


class AlphaRenderer(ImageRenderer):
    def __init__(self, image1, image2, alpha=0):
        self._renderer1 = ImageRenderer(image1)
        self._renderer2 = ImageRenderer(image2)
        assert self._renderer1.slice_size == self._renderer2.slice_size
        self.alpha = alpha

    def automatic_rescale(self):
        self._renderer1.automatic_rescale()
        self._renderer2.automatic_rescale()

    @property
    def slice_size(self):
        return self._renderer1.slice_size

    @property
    def intensity_range(self):
        vmin1, vmax1 = self._renderer1.intensity_range
        vmin2, vmax2 = self._renderer2.intensity_range
        return vmin1, vmax1, vmin2, vmax2

    def rescale_intensity(self, vmin1=None, vmax1=None, vmin2=None, vmax2=None):
        self._renderer1.rescale_intensity(vmin1, vmax1)
        self._renderer2.rescale_intensity(vmin2, vmax2)

    def __len__(self):
        return len(self._renderer1)

    def __getitem__(self, ind):
        image_slice1 = self._renderer1[ind]
        image_slice2 = self._renderer2[ind]
        image_slice = self._compose(image_slice1, image_slice2)
        return image_slice

    def _check_slice_ind(self, ind):
        assert False

    def _compose(self, image_slice1, image_slice2):
        array1 = np.array(image_slice1.convert('RGBA'), dtype=np.uint8)
        array2 = np.array(image_slice2.convert('RGBA'), dtype=np.uint8)
        array2[..., 3] = array2[..., 3] * self.alpha
        image1 = Image.fromarray(array1)
        image2 = Image.fromarray(array2)
        composition = Image.alpha_composite(image1, image2)
        return composition
