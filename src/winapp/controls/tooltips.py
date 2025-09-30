# https://learn.microsoft.com/en-us/windows/win32/controls/tooltip-control-reference

from ctypes import POINTER
from ctypes.wintypes import *

from ..const import *
from ..window import *
from ..dlls import user32
from .common import NMHDR

########################################
# Structs
########################################
#typedef struct tagTOOLINFOW {
#  UINT      cbSize;
#  UINT      uFlags;
#  HWND      hwnd;
#  UINT_PTR  uId;
#  RECT      rect;
#  HINSTANCE hinst;
#  LPWSTR    lpszText;
#  LPARAM    lParam;
#  void      *lpReserved;
#} TTTOOLINFOW, *PTOOLINFOW, *LPTTTOOLINFOW;

class TOOLINFOW(Structure):
    def __init__(self, *args, **kwargs):
        super(TOOLINFOW, self).__init__(*args, **kwargs)
        self.cbSize = sizeof(self)
    _fields_ = [
        ('cbSize', UINT),
        ('uFlags', UINT),
        ('hwnd', HWND),
        ('uId', HANDLE),  # UINT_PTR
        ('rect', RECT),
        ('hinst', HINSTANCE),
        ('lpszText', LPWSTR),
        ('lParam', LPARAM),
        ('lpReserved', LPVOID)
    ]

#typedef struct tagNMTTDISPINFOW {
#    NMHDR hdr;
#    LPWSTR lpszText;
#    WCHAR szText[80];
#    HINSTANCE hinst;
#    UINT uFlags;
#    LPARAM lParam;
#} NMTTDISPINFOW, *LPNMTTDISPINFOW;

class NMTTDISPINFOW(Structure):
    _fields_ = [
        ('hdr', NMHDR),
        ('lpszText', LPWSTR),
        ('szText', WCHAR * 80),
        ('hinst', HINSTANCE),  #
        ('uFlags', UINT),
        ('lParam', LPARAM),
    ]
LPNMTTDISPINFOW = POINTER(NMTTDISPINFOW)

########################################
# Wrapper Class
########################################
class Tooltips(Window):

#   // Create the tooltip. g_hInst is the global instance handle.
#    HWND hwndTip = CreateWindowEx(NULL, TOOLTIPS_CLASS, NULL,
#                              WS_POPUP |TTS_ALWAYSTIP | TTS_BALLOON,
#                              CW_USEDEFAULT, CW_USEDEFAULT,
#                              CW_USEDEFAULT, CW_USEDEFAULT,
#                              hDlg, NULL,
#                              g_hInst, NULL);

    ########################################
    #
    ########################################
    def __init__(
        self,
        parent_window=None,
        style=WS_VISIBLE | WS_POPUP | TTS_ALWAYSTIP, # | TTS_NOANIMATE | TTS_NOFADE | TTS_BALLOON,
        ex_style=WS_EX_TOPMOST,
        left=CW_USEDEFAULT, top=CW_USEDEFAULT, width=CW_USEDEFAULT, height=CW_USEDEFAULT,
        window_title=None
    ):

#    def __init__(self, window_class, style=WS_CHILD | WS_VISIBLE, ex_style=0,
#            left=0, top=0, width=0, height=0, window_title=None, hmenu=0, parent_window=None, wrap_hwnd=None):

        super().__init__(
            WC_TOOLTIPS,
            style=style,
            ex_style=ex_style,
            left=left,
            top=top,
            width=width,
            height=height,
            window_title=window_title,
            parent_window=parent_window
        )

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)
