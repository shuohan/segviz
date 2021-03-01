from .render import ImageRenderer, ImagePairRenderer, ImageEdgeRenderer
from .render import CheckerboardRenderer
from .utils import assign_colors, compose_image_and_labels
from .utils import convert_grayscale_image_to_pil, reindex_colors
from .utils import append_alpha_column, concat_pils, load_colors
from .utils import get_default_colormap

__all__ = ['ImageRenderer', 'ImagePairRenderer', 'ImageEdgeRenderer',
           'assign_colors', 'compose_image_and_labels',
           'convert_grayscale_image_to_pil', 'reindex_colors',
           'append_alpha_column', 'concat_pils', 'load_colors',
           'get_default_colormap']


import importlib.resources

def read_template(image_only=False, reverse=False):
    """Loads a html template for jinja.

    Returns:
        str: The loaded template.

    """
    if image_only:
        if reverse:
            html = 'image_template_rev.html'
        else:
            html = 'image_template.html'
    else:
        if reverse:
            html = 'label_template_rev.html'
        else:
            html = 'label_template.html'
    return importlib.resources.read_text(__name__, html)
