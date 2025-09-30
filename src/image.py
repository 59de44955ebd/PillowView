from ctypes import cast, POINTER, byref, c_char_p, c_ubyte, create_string_buffer, sizeof, Structure
from ctypes.wintypes import LONG, WORD, DWORD, LPVOID, BYTE
import io
from math import sqrt
from PIL import Image, ImageDraw, ImageFont, ImagePalette
from winapp.const import DIB_RGB_COLORS, BI_RGB, NULL
from winapp.dlls import gdi32
from const import MODE_TO_BPP

BG_COLOR = (0, 0, 255)

# https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmap
class BITMAP(Structure):
    _fields_ = [
        ("bmType", LONG),
        ("bmWidth", LONG),
        ("bmHeight", LONG),
        ("bmWidthBytes", LONG),
        ("bmPlanes", WORD),
        ("bmBitsPixel", WORD),
        ("bmBits", LPVOID),
    ]

# https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-bitmapinfoheader
class BITMAPINFOHEADER(Structure):
    def __init__(self, *args, **kwargs):
        super(BITMAPINFOHEADER, self).__init__(*args, **kwargs)
        self.biSize = sizeof(self)
    _fields_ = [
        ("biSize", DWORD),
        ("biWidth", LONG),
        ("biHeight", LONG),
        ("biPlanes", WORD),
        ("biBitCount", WORD),
        ("biCompression", DWORD),
        ("biSizeImage", DWORD),
        ("biXPelsPerMeter", LONG),
        ("biYPelsPerMeter", LONG),
        ("biClrUsed", DWORD),
        ("biClrImportant", DWORD)
    ]

# https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-rgbquad
class RGBQUAD(Structure):
    _fields_ = [
        ("rgbBlue", BYTE),
        ("rgbGreen", BYTE),
        ("rgbRed", BYTE),
        ("rgbReserved", BYTE),
    ]

class BITMAPINFO(Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", RGBQUAD * 256),
    ]

########################################
# COLORREF to (PIL) tuple
########################################
def CR_TO_RGB(c):
    return (c & 0xFF, c >> 8 & 0xFF, c >> 16 & 0xFF)

def RGB_TO_CR(r, g, b):
    return r | (g << 8) | (b << 16)

########################################
#
########################################
def get_bpp(img):
    if img.mode == 'P':
        num_colors = len(img.getpalette()) // 3
        if num_colors == 2:
            return 1
        elif num_colors == 16:
            return 4
        return 8
    else:
        return MODE_TO_BPP[img.mode]

########################################
#
########################################
def image_to_hbitmap(img):
    f = io.BytesIO()

    if img.mode in ('LA', 'PA'):
        img = img.convert('RGBA')

    elif MODE_TO_BPP[img.mode] < 24 or img.mode == 'CMYK':
        img = img.convert('RGB')

    if img.mode == 'RGBA':
        bg = Image.new('RGBA', img.size, BG_COLOR)  # Cache?
        img = Image.alpha_composite(bg, img).convert('RGB')

    img.transpose(Image.FLIP_TOP_BOTTOM).save(f, 'DIB')
    data = f.getvalue()[sizeof(BITMAPINFOHEADER):]
    bmi: BITMAPINFO = BITMAPINFO()
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = img.width
    bmi.bmiHeader.biHeight = -img.height
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = MODE_TO_BPP[img.mode]
    bmi.bmiHeader.biCompression = BI_RGB
    bmi.bmiHeader.biSizeImage = ((((img.width * bmi.bmiHeader.biBitCount) + 31) & ~31) >> 3) * img.height
    h_bitmap = gdi32.CreateDIBSection(None, byref(bmi), DIB_RGB_COLORS, None, None, 0)
    gdi32.SetDIBits(NULL, h_bitmap, 0, img.height, cast(c_char_p(data), POINTER(c_ubyte)), byref(bmi), DIB_RGB_COLORS)
    return h_bitmap

########################################
# Only used by paste and by Paint plugin
# Always 32-bit without actual alpha channel
########################################
def hbitmap_to_image(h_bitmap):
    bm = BITMAP()
    gdi32.GetObjectW(h_bitmap, sizeof(BITMAP), byref(bm))
    bm.bmBitsPixel = 32

    hdc = gdi32.CreateCompatibleDC(NULL)
    gdi32.SelectObject(hdc, h_bitmap)
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = bm.bmWidth
    bmi.bmiHeader.biHeight = -bm.bmHeight
    bmi.bmiHeader.biPlanes = bm.bmPlanes
    bmi.bmiHeader.biBitCount = bm.bmBitsPixel
    bmi.bmiHeader.biCompression = BI_RGB
    bmi.bmiHeader.biSizeImage = ((((bm.bmWidth * bmi.bmiHeader.biBitCount) + 31) & ~31) >> 3) * bm.bmHeight
    bits = create_string_buffer(bmi.bmiHeader.biSizeImage)
    gdi32.GetDIBits(hdc, h_bitmap, 0, bm.bmHeight, bits, byref(bmi), DIB_RGB_COLORS)
    gdi32.DeleteDC(hdc)
    return Image.frombytes('RGB', (bm.bmWidth, bm.bmHeight), bits, 'raw', 'BGRX')

########################################
#
########################################
def text_to_image(text):
    text = text.replace('\t', '   ')
    font = ImageFont.truetype('consola.ttf', 14)
    draw = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = draw.textbbox((0, 0), text, font=font)
    img = Image.new('L', (bb[2] + 20, bb[3] + 20), 255)
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill=0, font=font)
    return img

########################################
#
########################################
def create_vignette(size):
    w = 200
    f = .9
    mx = sqrt(2) * w / 2
    img = Image.new('L', (w, w))
    for x in range(w):
        for y in range(w):
            r = sqrt((x - w / 2)**2 + (y - w / 2)**2)
            c = max(r - w / 2 * f, 0) * 255 / (mx - w / 2 * f)
            img.putpixel((x, y), int(255 - c * .6 ))
    return img.resize(size)

########################################
#
########################################
def gamma_correction(img, gamma):
    factor = 255 ** (1 - gamma)
    return img.point(lambda c: c ** gamma * factor)

########################################
# Used by paint plugin
########################################
def get_closest_palette_color(colorref, img):
    if img.mode in ('L', 'LA'):
        r, g, b = CR_TO_RGB(colorref)
        return round(r * .299 + g * .587 + b * .114)  # ITU-R 601-2 luma transform
    else:
        tmp = Image.new('RGB', (1, 1), color=CR_TO_RGB(colorref))
        tmp = tmp.quantize(palette = img) #, dither = Image.Dither.NONE)
        return tmp.getpixel((0, 0))
