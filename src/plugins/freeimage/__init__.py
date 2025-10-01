import os
import sys
from PIL import Image, ImagePalette, ImageOps

IS_WIN = os.name == 'nt'

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, DIR)
from freeimage import *

########################################
#
########################################
def gamma_correction(img, gamma):
    factor = 255 ** (1 - gamma)
    return img.point(lambda c: c ** gamma * factor)

########################################
#
########################################
def _open(fp, filename, ** kwargs):
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.mng':
        fmt = FREE_IMAGE_FORMAT.FIF_MNG
        fmt_pil = 'MNG'
    elif ext in ('.pct', '.pict'):
        fmt = FREE_IMAGE_FORMAT.FIF_PICT
        fmt_pil = 'PICT'
    elif ext == '.psd':
        fmt = FREE_IMAGE_FORMAT.FIF_PSD
        fmt_pil = 'PSD'
    elif ext in ('.tif', '.tiff'):
        fmt = FREE_IMAGE_FORMAT.FIF_TIFF
        fmt_pil = 'TIFF'
    else:
        raise SyntaxError('No FreeImage file')

    if IS_WIN:
        dib = fi.FreeImage_LoadU(fmt, filename, 0)
    else:
        dib = fi.FreeImage_Load(fmt, filename.encode(), 0)

    w = fi.FreeImage_GetWidth(dib)
    h = fi.FreeImage_GetHeight(dib)
    pitch = fi.FreeImage_GetPitch(dib)
    bits = fi.FreeImage_GetBits(dib)
    img_type = fi.FreeImage_GetImageType(dib)
    data_size = pitch * h

    img = None

    ########################################
    # 12: bpp == 128 - 4x 32-bit floats per pixel (PSD and TIFF)
    ########################################
    if img_type == FREE_IMAGE_TYPE.FIT_RGBAF:
        cnt = data_size // sizeof(c_float)

        data_in = cast(bits, POINTER(c_float * cnt)).contents
        data_out = (c_ubyte * cnt)()

        for i in range(cnt):
            data_out[i] = round(data_in[i] * 255)

        img = Image.frombytes('RGBA', (w, h), data_out, 'raw', 'RGBA', 0, -1)
        fi.FreeImage_Unload(dib)

        img = gamma_correction(img, 1 / 2.2)

    ########################################
    # 11: bpp == 96 - 3x 32-bit floats per pixel (PSD and TIFF)
    ########################################
    elif img_type == FREE_IMAGE_TYPE.FIT_RGBF:

        cnt = data_size // sizeof(c_float)

        data_in = cast(bits, POINTER(c_float * cnt)).contents
        data_out = (c_ubyte * cnt)()

        for i in range(cnt):
            data_out[i] = round(data_in[i] * 255)

        img = Image.frombytes('RGB', (w, h), data_out, 'raw', 'RGB', 0, -1)
        fi.FreeImage_Unload(dib)

        img = gamma_correction(img, 1 / 2.2)

    ########################################
    # 10: bpp == 64 - 4x 16-bit RGBA (PSD and TIFF)
    ########################################
    elif img_type == FREE_IMAGE_TYPE.FIT_RGBA16:
        dib_converted = fi.FreeImage_ConvertTo32Bits(dib)
        fi.FreeImage_Unload(dib)

        bits = fi.FreeImage_GetBits(dib_converted)
        pitch = fi.FreeImage_GetPitch(dib_converted)
        data = cast(bits, POINTER(c_ubyte * (pitch * h))).contents

        img = Image.frombytes('RGBA', (w, h), data, 'raw', 'BGRA', 0, -1)
        fi.FreeImage_Unload(dib_converted)

    ########################################
    # 9: bpp == 48 - 3x 16-bit RGB (PSD and TIFF)
    ########################################
    elif img_type == FREE_IMAGE_TYPE.FIT_RGB16:
        dib_converted = fi.FreeImage_ConvertTo24Bits(dib)
        fi.FreeImage_Unload(dib)

        bits = fi.FreeImage_GetBits(dib_converted)
        pitch = fi.FreeImage_GetPitch(dib_converted)
        data = cast(bits, POINTER(c_ubyte * (pitch * h))).contents

        img = Image.frombytes('RGB', (w, h), data, 'raw', 'BGR', 0, -1)
        fi.FreeImage_Unload(dib_converted)

    ########################################
    # 1: standard bitmap
    ########################################
    elif img_type == FREE_IMAGE_TYPE.FIT_BITMAP:
        bpp = fi.FreeImage_GetBPP(dib)
        data = cast(bits, POINTER(c_ubyte * data_size)).contents

        if bpp == 8:
            ct = fi.FreeImage_GetColorType(dib)
            if ct == FREE_IMAGE_COLOR_TYPE.FIC_MINISWHITE:
                img = ImageOps.invert(Image.frombytes('L', (w, h), data, 'raw', 'L', 0, -1))

            elif ct == FREE_IMAGE_COLOR_TYPE.FIC_MINISBLACK:
                img = Image.frombytes('L', (w, h), data, 'raw', 'L', 0, -1)

            else:  # FIC_PALETTE
                cu = fi.FreeImage_GetColorsUsed(dib)
                img = Image.frombytes('P', (w, h), data, 'raw', 'P', 0, -1)
                pal = cast(fi.FreeImage_GetPalette(dib), POINTER(c_ubyte * (4 * cu))).contents
                img.putpalette(ImagePalette.raw("BGRX", pal))

        elif bpp == 24:
            img = Image.frombytes('RGB', (w, h), data, 'raw', 'BGR', 0, -1)

        elif bpp == 32:  # FIC_RGB
            ct = fi.FreeImage_GetColorType(dib)
            if ct == FREE_IMAGE_COLOR_TYPE.FIC_RGB:
                img = Image.frombytes('RGB', (w, h), data, 'raw', 'BGRX', 0, -1)
            else:
                # PICT 2: 32-bit color PICTs could be output with an alpha channel, but CMYK color was not supported.
                img = Image.frombytes('RGBA', (w, h), data, 'raw', 'BGRA', 0, -1)

        fi.FreeImage_Unload(dib)

    if img:
        img.format = fmt_pil
        img.filename = filename
        return img
    else:
        raise SyntaxError('No FreeImage file')

# --------------------------------------------------------------------

Image.register_open("PICT", _open)
Image.register_extensions("PICT", (".pct", ".pict"))

Image.register_open("MNG", _open, lambda prefix: prefix.startswith(b'\x8AMNG'))
Image.register_extension("MNG", ".mng")

Image.register_open("PSD", _open, lambda prefix: prefix.startswith(b'8BPS'))
Image.register_extension("PSD", ".psd")

Image.register_open("TIFF", _open, lambda prefix: prefix.startswith(b'II\x2A\x00'))
Image.register_extensions("TIFF", (".tif", ".tiff"))

if __name__ == "__main__":
    img = Image.open("../_test_files/test.pct")
    img.show()
