# https://learn.microsoft.com/en-us/windows/win32/controls/buttons

from ctypes import *
from ctypes.wintypes import HANDLE, RECT, UINT

from ..const import *
from ..wintypes_extended import MAKELPARAM
from ..window import Window
from ..themes import *
from ..dlls import gdi32, user32, uxtheme
from ..themes import DARK_BG_COLOR
from .static import Static, SS_SIMPLE

########################################
# Button Control Structures
########################################
class BUTTON_IMAGELIST(Structure):
    _fields_ = [
        ("himl", HANDLE),
        ("margin", RECT),
        ("uAlign", UINT),
    ]


########################################
# Wrapper Class
########################################
class Button(Window):

    ########################################
    #
    ########################################
    def __init__(self, parent_window, style=WS_CHILD | WS_VISIBLE, ex_style=0,
            left=0, top=0, width=94, height=23, window_title='OK', wrap_hwnd=None):

        super().__init__(
            WC_BUTTON,
            parent_window=parent_window,
            style=style,
            ex_style=ex_style,
            left=left,
            top=top,
            width=width,
            height=height,
            window_title=window_title,
            wrap_hwnd=wrap_hwnd
        )
        self.set_font()


        if style & BS_TYPEMASK == BS_GROUPBOX:

            rc = self.get_window_rect()

            user32.MapWindowPoints(None, parent_window.hwnd, byref(rc), 2)

            self.static = Static(
                parent_window=parent_window,
                style=WS_CHILD | SS_SIMPLE | WS_VISIBLE,
                ex_style=WS_EX_TRANSPARENT,
                left=rc.left + 10,
                top=rc.top,
                width=rc.right - rc.left - 16, height=rc.bottom - rc.top,
                window_title=window_title,
            )

            self.static.set_font(hfont=self.hfont)

    ########################################
    #
    ########################################
    def destroy_window(self):
        if self.is_dark:
            self.parent_window.unregister_message_callback(WM_CTLCOLORBTN, self._on_WM_CTLCOLORBTN)
        super().destroy_window()

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)
        if is_dark:
            self.parent_window.register_message_callback(WM_CTLCOLORBTN, self._on_WM_CTLCOLORBTN)
        else:
            self.parent_window.unregister_message_callback(WM_CTLCOLORBTN, self._on_WM_CTLCOLORBTN)

    ########################################
    #
    ########################################
    def _on_WM_CTLCOLORBTN(self, hwnd, wparam, lparam):
        if lparam == self.hwnd:
            gdi32.SetDCBrushColor(wparam, DARK_BG_COLOR)
            return gdi32.GetStockObject(DC_BRUSH)


########################################
# Wrapper Class
########################################
class CheckBox(Window):

    ########################################
    #
    ########################################
    def __init__(
            self,
            parent_window,
            style=WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
            ex_style=0,
            bg_color=0xffffff, #COLOR_WINDOW + 1,
            dark_bg_color=DARK_BG_COLOR,
            left=0, top=0, width=0, height=0,
            window_title=None
        ):

        super().__init__(
            WC_BUTTON,
            parent_window=parent_window,
            style=style,
            ex_style=ex_style,
            left=left,
            top=top,
            width=width,
            height=height,
        )

        self.checkbox_static = Static(
            self,
            style=WS_CHILD | SS_SIMPLE | WS_VISIBLE,
            bg_color=bg_color,
            dark_bg_color=dark_bg_color,
            left=16,
            top=1,
            width=width - 16,
            height=height,
            window_title=window_title.replace('&', '')
        )

    ########################################
    #
    ########################################
    def _on_WM_CTLCOLORSTATIC(self, hwnd, wparam, lparam):
        if lparam == self.hwnd:
            gdi32.SetDCBrushColor(wparam, DARK_BG_COLOR)
            return gdi32.GetStockObject(DC_BRUSH)

    ########################################
    #
    ########################################
    def set_font(self, *args, **kwargs):
        self.checkbox_static.set_font(*args, **kwargs)

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)
        if is_dark:
            self.parent_window.register_message_callback(WM_CTLCOLORSTATIC, self._on_WM_CTLCOLORSTATIC)
        else:
            self.parent_window.unregister_message_callback(WM_CTLCOLORSTATIC, self._on_WM_CTLCOLORSTATIC)
