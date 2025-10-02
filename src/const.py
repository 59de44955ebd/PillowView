import os
import sys
from ctypes import byref
from ctypes.wintypes import RECT
from winapp.dlls import gdi32, kernel32, user32
from winapp.const import *
from winapp.wintypes_extended import MAKEINTRESOURCEW

from resources import *

IS_FROZEN = getattr(sys, 'frozen', False)

APP_NAME = 'PillowView'
APP_VERSION ='1.0'
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = APP_DIR if IS_FROZEN else os.path.join(APP_DIR, 'bin')

if IS_FROZEN:
    HMOD_RESOURCES = kernel32.GetModuleHandleW(None)
else:
    HMOD_RESOURCES = kernel32.LoadLibraryW(os.path.join(APP_DIR, 'resources.dll'))

RC_DESKTOP = RECT()
user32.SystemParametersInfoA(SPI_GETWORKAREA, NULL, byref(RC_DESKTOP), NULL)

HCURSOR_MOVE = user32.LoadCursorW(NULL, IDC_SIZEALL)
HCURSOR_CROSS = user32.LoadCursorW(NULL, IDC_CROSS)
HCURSOR_ZOOM = user32.LoadCursorW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDI_CURSOR_ZOOM))

HBRUSH_NULL = gdi32.GetStockObject(NULL_BRUSH)

ANIMATION_TIMER_ID = 1000

EVENT_IMAGE_CHANGED = 1

# Modes that we support for loaded images. Images with other modes are converted to RGB when loaded.
MODE_TO_BPP = {'1': 1, 'P': 8, 'L': 8, 'PA': 16, 'LA': 16, 'RGB': 24, 'RGBA': 32, 'CMYK': 32}

FORMATS_SAVE = {
    'AVIF': ('.avif', '.avifs'),
    'BLP': ('*.blp',),
    'BMP': ('*.bmp',),
#    'CUR': ('*.cur',),
    'DDS': ('*.dds',),
    'DIB': ('*.dib',),
    'EPS': ('*.eps', '*.ps'),
    'GIF': ('*.gif',),
    'ICNS': ('*.icns',),
    'ICO': ('*.ico',),
    'IM': ('*.im',),
    'JPEG': ('*.jpg', '*.jpeg', '*.jpe', '*.jfif'),
    'JPEG2000': ('*.jp2', '*.j2k', '*.jpc', '*.jpf', '*.jpx', '*.j2c'),
    'MSP': ('*.msp',),
    'PCX': ('*.pcx',),
    'PDF': ('*.pdf',),
    'PIL': ('*.pil',),
    'PNG': ('*.png', '*.apng'),
    'PPM': ('*.ppm', '*.pnm', '*.pgm', '*.pfm', '*.pbm'),
    'QOI': ('*.qoi',),
    'RAW': ('*.raw',),
    'SGI': ('*.sgi', '*.rgba', '*.rgb', '*.bw'),
    'TGA': ('*.tga', '*.icb', '*.vda', '*.vst'),
    'TIFF': ('*.tif', '*.tiff'),
    'WEBP': ('*.webp',),
    'XBM': ('*.xbm',),
}

FORMATS_ANIMATION = ['AVIF', 'FLI', 'GIF', 'PNG', 'WEBP']

BPP1_ONLY = ('MSP', 'XBM')
P_ONLY = ('BLP',)
NO_CMYK = ('BMP', 'DDS', 'DIB', 'GIF', 'ICNS', 'ICO', 'PCX', 'PNG', 'PPM', 'QOI', 'SGI', 'TGA')
NO_RGBA = ('EPS', 'JPEG', 'PCX')
NO_LA = ('BMP', 'DIB', 'EPS', 'JPEG', 'PCX', 'PPM', 'QOI', 'SGI')
NO_L = ('QOI',)
NO_P = ('DDS', 'EPS', 'JPEG', 'JPEG2000', 'PPM', 'QOI', 'SGI')
NO_BPP1 = ('DDS', 'EPS', 'GIF', 'JPEG', 'JPEG2000', 'PNG', 'SGI', 'TGA', 'TIFF')
OK_PA = ('AVIF', 'IM', 'PIL', 'TIFF', 'WEBP')

STATUSBAR_PARTS = (0,   130, 130, 60, 45, 70, 60)

STATUSBAR_PART_SELECTION = 1
STATUSBAR_PART_INFOS = 2
STATUSBAR_PART_FORMAT = 3
STATUSBAR_PART_MODE = 4
STATUSBAR_PART_FRAMES = 5       # max: 9999 / 9999
STATUSBAR_PART_ZOOM = 6         # max: 9999%

MENU_FILE = 0
MENU_EDIT = 1
MENU_IMAGE = 2
MENU_FILTER = 3
MENU_VIEW = 4
MENU_HELP = 5
