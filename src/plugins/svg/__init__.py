import os
import sys
from PIL import Image
sys.path.insert(1, os.path.dirname(__file__))
import svg2pil

SVG_OUTPUT_WIDTH = 600
SVG_BACKGROUND_COLOR = "#FFFFFF"

def _open(fp, filename, output_width=SVG_OUTPUT_WIDTH, background_color=SVG_BACKGROUND_COLOR, **kwargs):
    try:
        img = svg2pil.svg2pil(url=filename, unsafe=True, output_width=output_width, background_color=background_color)
        img.format = "SVG"
        img.filename = filename
        return img
    except:
        raise SyntaxError("No SVG file")

# --------------------------------------------------------------------

Image.register_open("SVG", _open, lambda prefix: prefix[:5] == b"<?xml")
Image.register_extension("SVG", ".svg")

if __name__ == "__main__":
    img = Image.open("../_test_files/test.svg")
    img.show()
