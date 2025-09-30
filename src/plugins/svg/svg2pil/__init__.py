"""
CairoSVG - A simple SVG converter based on Cairo.

"""

# VERSION is used in the "url" module imported by "surface"
VERSION = __version__ = '2.7.1'

from . import surface  # noqa isort:skip

def svg2pil(
    bytestring=None, file_obj=None, url=None,
    dpi=96, scale=1,
    unsafe=False,
    background_color=None,
    output_width=None, output_height=None
):
    return surface.ImageSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url,
        dpi=dpi, scale=scale,
        unsafe=unsafe,
        background_color=background_color,
        output_width=output_width, output_height=output_height
    )
