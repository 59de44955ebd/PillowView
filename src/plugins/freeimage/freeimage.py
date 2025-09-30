import os
from ctypes import *
from enum import IntEnum

if os.name == 'nt':
    fi = CDLL(os.path.join(os.path.dirname(__file__), 'bin', 'freeimage-3.18.0-win64.dll'))
else:
    from ctypes.util import find_library
    fi = CDLL(find_library('freeimage'))

# Define the types we need.
class _CtypesEnum(IntEnum):
    """A ctypes-compatible IntEnum superclass."""
    @classmethod
    def from_param(cls, obj):
        return int(obj)


class FREE_IMAGE_FORMAT(_CtypesEnum):
    FIF_UNKNOWN = -1
    FIF_BMP     = 0
    FIF_ICO     = 1
    FIF_JPEG    = 2
    FIF_JNG     = 3
    FIF_KOALA   = 4
    FIF_LBM     = 5
    FIF_IFF = FIF_LBM
    FIF_MNG     = 6
    FIF_PBM     = 7
    FIF_PBMRAW  = 8
    FIF_PCD     = 9
    FIF_PCX     = 10
    FIF_PGM     = 11
    FIF_PGMRAW  = 12
    FIF_PNG     = 13
    FIF_PPM     = 14
    FIF_PPMRAW  = 15
    FIF_RAS     = 16
    FIF_TARGA   = 17
    FIF_TIFF    = 18
    FIF_WBMP    = 19
    FIF_PSD     = 20
    FIF_CUT     = 21
    FIF_XBM     = 22
    FIF_XPM     = 23
    FIF_DDS     = 24
    FIF_GIF     = 25
    FIF_HDR     = 26
    FIF_FAXG3   = 27
    FIF_SGI     = 28
    FIF_EXR     = 29
    FIF_J2K     = 30
    FIF_JP2     = 31
    FIF_PFM     = 32
    FIF_PICT    = 33
    FIF_RAW     = 34
    FIF_WEBP    = 35
    FIF_JXR     = 36


class FREE_IMAGE_TYPE(_CtypesEnum):
    FIT_UNKNOWN = 0     # unknown type
    FIT_BITMAP  = 1     # standard image          : 1-, 4-, 8-, 16-, 24-, 32-bit
    FIT_c_ulong16  = 2     # array of unsigned short : unsigned 16-bit
    FIT_c_long16   = 3     # array of short          : signed 16-bit
    FIT_c_ulong32  = 4     # array of unsigned long  : unsigned 32-bit
    FIT_c_long32   = 5     # array of long           : signed 32-bit
    FIT_FLOAT   = 6     # array of float          : 32-bit IEEE floating point
    FIT_DOUBLE  = 7     # array of double         : 64-bit IEEE floating point
    FIT_COMPLEX = 8     # array of FICOMPLEX      : 2 x 64-bit IEEE floating point
    FIT_RGB16   = 9     # 48-bit RGB image        : 3 x 16-bit
    FIT_RGBA16  = 10    # 64-bit RGBA image       : 4 x 16-bit
    FIT_RGBF    = 11    # 96-bit RGB float image  : 3 x 32-bit IEEE floating point
    FIT_RGBAF   = 12    # 128-bit RGBA float image : 4 x 32-bit IEEE floating point


class FREE_IMAGE_COLOR_TYPE(_CtypesEnum):
    FIC_MINISWHITE = 0  # min value is white
    FIC_MINISBLACK = 1  # min value is black
    FIC_RGB        = 2  # RGB color model
    FIC_PALETTE    = 3  # color map indexed
    FIC_RGBALPHA   = 4  # RGB color model with alpha channel
    FIC_CMYK       = 5  # CMYK color model

#class FREE_IMAGE_TMO(_CtypesEnum):
#    FITMO_DRAGO03	 = 0  # Adaptive logarithmic mapping (F. Drago, 2003)
#    FITMO_REINHARD05 = 1  # Dynamic range reduction inspired by photoreceptor physiology (E. Reinhard, 2005)
#    FITMO_FATTAL02	 = 2  # Gradient domain high dynamic range compression (R. Fattal, 2002)

class FIBITMAP(Structure):
    _fields_ = (
        ("data",   c_void_p),
    )

class RGBQUAD(Structure):
    _fields_ = (
        ("rgbBlue",     c_ubyte),
        ("rgbGreen",    c_ubyte),
        ("rgbRed",      c_ubyte),
        ("rgbReserved", c_ubyte),
    )

# const char * FreeImage_GetVersion();
fi.FreeImage_GetVersion.restype = c_char_p

# FIBITMAP * FreeImage_Load(FREE_IMAGE_FORMAT fif, const char *filename, int flags FI_DEFAULT(0));
fi.FreeImage_Load.argtypes = (FREE_IMAGE_FORMAT, c_char_p, c_long)
fi.FreeImage_Load.restype = POINTER(FIBITMAP)

# FIBITMAP * FreeImage_LoadU(FREE_IMAGE_FORMAT fif, const wchar_t *filename, int flags FI_DEFAULT(0));
fi.FreeImage_LoadU.argtypes = (FREE_IMAGE_FORMAT, c_wchar_p, c_long)
fi.FreeImage_LoadU.restype = POINTER(FIBITMAP)

# void FreeImage_Unload(FIBITMAP *dib);
fi.FreeImage_Unload.argtypes = (POINTER(FIBITMAP),)

# c_ubyte * FreeImage_GetBits(FIBITMAP *dib);
fi.FreeImage_GetBits.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_GetBits.restype = POINTER(c_ubyte)

# unsigned FreeImage_GetWidth(FIBITMAP *dib);
fi.FreeImage_GetWidth.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_GetWidth.restype = c_ulong

fi.FreeImage_GetHeight.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_GetHeight.restype = c_ulong

fi.FreeImage_GetBPP.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_GetBPP.restype = c_ulong

fi.FreeImage_GetPitch.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_GetPitch.restype = c_ulong

# FREE_IMAGE_TYPE FreeImage_GetImageType(FIBITMAP *dib);
fi.FreeImage_GetImageType.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_GetImageType.restype = FREE_IMAGE_TYPE

# FIBITMAP * FreeImage_ConvertTo32Bits(FIBITMAP *dib);
fi.FreeImage_ConvertTo32Bits.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_ConvertTo32Bits.restype = POINTER(FIBITMAP)

# RGBQUAD * FreeImage_GetPalette(FIBITMAP *dib)
fi.FreeImage_GetPalette.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_GetPalette.restype = POINTER(RGBQUAD)

# FREE_IMAGE_COLOR_TYPE FreeImage_GetColorType(FIBITMAP *dib);
fi.FreeImage_GetColorType.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_GetColorType.restype = FREE_IMAGE_COLOR_TYPE

# unsigned FreeImage_GetColorsUsed(FIBITMAP *dib);
fi.FreeImage_GetColorsUsed.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_GetColorsUsed.restype = c_ulong

# FIBITMAP * FreeImage_ConvertTo24Bits(FIBITMAP *dib);
fi.FreeImage_ConvertTo24Bits.argtypes = (POINTER(FIBITMAP),)
fi.FreeImage_ConvertTo24Bits.restype = POINTER(FIBITMAP)
