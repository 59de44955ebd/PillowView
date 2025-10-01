from ctypes import c_int, byref, sizeof, windll, Structure, WINFUNCTYPE, POINTER, cast
from ctypes.wintypes import INT, DWORD, BOOL, HWND, UINT, WPARAM, LPARAM, HMENU, HDC, HKEY, BYTE

from .controls.common import DRAWITEMSTRUCT, MEASUREITEMSTRUCT
from .wintypes_extended import LONG_PTR
from .dlls import advapi32, gdi32
from .const import HKEY_CURRENT_USER, ERROR_SUCCESS, PS_INSIDEFRAME, REG_DWORD

DWMWA_USE_IMMERSIVE_DARK_MODE = 20

# Window messages related to menu bar drawing
WM_UAHDESTROYWINDOW    =0x0090	# handled by DefWindowProc
WM_UAHDRAWMENU         =0x0091	# lParam is UAHMENU
WM_UAHDRAWMENUITEM     =0x0092	# lParam is UAHDRAWMENUITEM
WM_UAHINITMENU         =0x0093	# handled by DefWindowProc
WM_UAHMEASUREMENUITEM  =0x0094	# lParam is UAHMEASUREMENUITEM
WM_UAHNCPAINTMENUPOPUP =0x0095	# handled by DefWindowProc

DARK_BG_COLOR = 0x202020
DARK_BG_BRUSH = gdi32.CreateSolidBrush(DARK_BG_COLOR)

BORDER_COLOR = 0xA0A0A0
BORDER_BRUSH = gdi32.CreateSolidBrush(BORDER_COLOR)

DARK_BORDER_COLOR = 0x646464
DARK_BORDER_BRUSH = gdi32.CreateSolidBrush(DARK_BORDER_COLOR)
DARK_TEXT_COLOR = 0xe0e0e0
DARK_CONTROL_BG_COLOR = 0x2b2b2b
DARK_CONTROL_BG_BRUSH = gdi32.CreateSolidBrush(DARK_CONTROL_BG_COLOR)
DARK_MENUBAR_BG_BRUSH = gdi32.CreateSolidBrush(0x2b2b2b)
DARK_MENU_BG_BRUSH_HOT = gdi32.CreateSolidBrush(0x3e3e3e)

# Used in _DarkListViewSubClassProcCallback
DARK_SEPARATOR_COLOR = 0x424242 #0x636363
# Used by listview and statusbar
DARK_SEPARATOR_BRUSH = gdi32.CreateSolidBrush(DARK_SEPARATOR_COLOR)

# TabControl
DARK_TAB_SELECTED_BG_BRUSH = gdi32.CreateSolidBrush(0x333333)
DARK_TAB_BORDER_BRUSH = DARK_TAB_SELECTED_BG_BRUSH
LIGHT_TAB_BORDER_BRUSH = gdi32.CreateSolidBrush(0xdcdcdc)
TAB_SELECTED_HILITE_BRUSH = gdi32.CreateSolidBrush(0xd77800)

# Trackbar
DARK_DISABLED_BRUSH = gdi32.CreateSolidBrush(0x636363)

class PreferredAppMode():
    Default = 0
    AllowDark = 1
    ForceDark = 2
    ForceLight = 3
    Max = 4

def dwm_use_dark_mode(hwnd, flag):
    value = c_int(1 if flag else 0)
    windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(value), sizeof(value))

UAHDarkModeWndProc = WINFUNCTYPE(BOOL, HWND, UINT, WPARAM, LPARAM, POINTER(LONG_PTR))

class _METRICS(Structure):
    _fields_ = [
        ("cx", DWORD),
        ("cy", DWORD),
    ]

# Describes the sizes of the menu bar or menu item
class UAHMENUITEMMETRICS(Structure):
    _fields_ = [
        ("rgsizeBar", _METRICS * 2),
        ("rgsizePopup", _METRICS * 4),
    ]

# Not really used in our case but part of the other structures
class UAHMENUPOPUPMETRICS(Structure):
    _fields_ = [
        ("rgcx", DWORD * 4),
        ("fUpdateMaxWidths", DWORD),
    ]

# hmenu is the main window menu; hdc is the context to draw in
class UAHMENU(Structure):
    _fields_ = [
        ("hmenu", HMENU),
        ("hdc", HDC),
        ("dwFlags", DWORD),
    ]

# Menu items are always referred to by iPosition here
class UAHMENUITEM(Structure):
    _fields_ = [
        ("iPosition", INT),
        ("umim", UAHMENUITEMMETRICS),
        ("umpm", UAHMENUPOPUPMETRICS),
    ]

# The DRAWITEMSTRUCT contains the states of the menu items, as well as
# the position index of the item in the menu, which is duplicated in
# the UAHMENUITEM's iPosition as well
class UAHDRAWMENUITEM(Structure):
    _fields_ = [
        ("dis", DRAWITEMSTRUCT),
        ("um", UAHMENU),
        ("umi", UAHMENUITEM),
    ]

# The MEASUREITEMSTRUCT is intended to be filled with the size of the item
# height appears to be ignored, but width can be modified
class UAHMEASUREMENUITEM(Structure):
    _fields_ = [
        ("mis", MEASUREITEMSTRUCT),
        ("um", UAHMENU),
        ("umi", UAHMENUITEM),
    ]

# weg
def reg_should_use_dark_mode(use_system=False):
    use_dark_mode = False
    hkey = HKEY()
    if advapi32.RegOpenKeyW(HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' , byref(hkey)) == ERROR_SUCCESS:
        data = DWORD()
        cbData = DWORD(sizeof(data))
        if advapi32.RegQueryValueExW(hkey, 'SystemUsesLightTheme' if use_system else 'AppsUseLightTheme', None, None, byref(data), byref(cbData)) == ERROR_SUCCESS:
            use_dark_mode = not bool(data.value)
        advapi32.RegCloseKey(hkey)
    return use_dark_mode

def reg_get_use_dark_mode():
    use_dark_mode_apps, use_dark_mode_system = False, False
    hkey = HKEY()
    if advapi32.RegOpenKeyW(HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' , byref(hkey)) == ERROR_SUCCESS:
        data = DWORD()
        cbData = DWORD(sizeof(data))
        if advapi32.RegQueryValueExW(hkey, 'AppsUseLightTheme', None, None, byref(data), byref(cbData)) == ERROR_SUCCESS:
            use_dark_mode_apps = not bool(data.value)
        if advapi32.RegQueryValueExW(hkey, 'SystemUsesLightTheme', None, None, byref(data), byref(cbData)) == ERROR_SUCCESS:
            use_dark_mode_system = not bool(data.value)
        advapi32.RegCloseKey(hkey)
    return use_dark_mode_apps, use_dark_mode_system

def reg_set_use_dark_mode_apps(use_dark):
    hkey = HKEY()
    if advapi32.RegOpenKeyW(HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' , byref(hkey)) == ERROR_SUCCESS:
        dwsize = sizeof(DWORD)
        advapi32.RegSetValueExW(hkey, 'AppsUseLightTheme', 0, REG_DWORD, byref(DWORD(int(not use_dark))), dwsize)
        advapi32.RegCloseKey(hkey)

def reg_set_use_dark_mode_system(use_dark):
    hkey = HKEY()
    if advapi32.RegOpenKeyW(HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' , byref(hkey)) == ERROR_SUCCESS:
        dwsize = sizeof(DWORD)
        advapi32.RegSetValueExW(hkey, 'SystemUsesLightTheme', 0, REG_DWORD, byref(DWORD(int(not use_dark))), dwsize)
        advapi32.RegCloseKey(hkey)
