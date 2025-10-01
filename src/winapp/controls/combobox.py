# https://learn.microsoft.com/en-us/windows/win32/controls/combo-boxes

from ctypes import Structure, sizeof, byref, create_unicode_buffer
from ctypes.wintypes import DWORD, RECT, HWND

from ..const import *
from ..window import Window
from ..dlls import gdi32, user32, uxtheme
from ..themes import DARK_TEXT_COLOR, DARK_CONTROL_BG_COLOR
from .listbox import ListBox
from .common import COMBOBOXINFO


# #######################################
# Wrapper Class
# #######################################
class ComboBox(Window):

    # #######################################
    #
    # #######################################
    def __init__(self, parent_window, style=WS_CHILD | WS_VISIBLE, ex_style=0,
                 left=0, top=0, width=0, height=0, window_title=None,
                 wrap_hwnd=None):

        super().__init__(
            WC_COMBOBOX,
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

        self.__has_edit = style & CBS_DROPDOWN

    # #######################################
    #
    # #######################################
    def destroy_window(self):
        if self.is_dark:
            self.unregister_message_callback(WM_CTLCOLORLISTBOX, self.on_WM_CTLCOLORLISTBOX)
            if self.__has_edit:
                self.unregister_message_callback(WM_CTLCOLOREDIT, self._on_WM_CTLCOLOREDIT)
        super().destroy_window()

    def add_string(self, s):
        user32.SendMessageW(self.hwnd, CB_ADDSTRING, 0, s)

    def set_current_selection(self, idx):
        user32.SendMessageW(self.hwnd, CB_SETCURSEL, idx, 0)

    def get_current_selection(self):
        return user32.SendMessageW(self.hwnd, CB_GETCURSEL, 0, 0)

    # #######################################
    #
    # #######################################
    def apply_theme(self, is_dark):
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_CFD' if is_dark else 'CFD', None)
        super().apply_theme(is_dark)

        # scrollbar colors
        ci = COMBOBOXINFO()
        user32.SendMessageW(self.hwnd, CB_GETCOMBOBOXINFO, 0, byref(ci))
        uxtheme.SetWindowTheme(ci.hwndList, 'DarkMode_Explorer' if is_dark else 'Explorer', None)

        if is_dark:
            self.register_message_callback(WM_CTLCOLORLISTBOX, self.on_WM_CTLCOLORLISTBOX)
            if self.__has_edit:
                self.register_message_callback(WM_CTLCOLOREDIT, self._on_WM_CTLCOLOREDIT)
        else:
            self.unregister_message_callback(WM_CTLCOLORLISTBOX, self.on_WM_CTLCOLORLISTBOX)
            if self.__has_edit:
                self.unregister_message_callback(WM_CTLCOLOREDIT, self._on_WM_CTLCOLOREDIT)

    # #######################################
    #
    # #######################################
    def on_WM_CTLCOLORLISTBOX(self, hwnd, wparam, lparam):
        gdi32.SetTextColor(wparam, DARK_TEXT_COLOR)
        gdi32.SetBkColor(wparam, DARK_CONTROL_BG_COLOR)
        gdi32.SetDCBrushColor(wparam, DARK_CONTROL_BG_COLOR)
        return gdi32.GetStockObject(DC_BRUSH)

    # #######################################
    #
    # #######################################
    def _on_WM_CTLCOLOREDIT(self, hwnd, wparam, lparam):
        gdi32.SetTextColor(wparam, DARK_TEXT_COLOR)
        gdi32.SetBkColor(wparam, DARK_CONTROL_BG_COLOR)
        gdi32.SetDCBrushColor(wparam, DARK_CONTROL_BG_COLOR)
        return gdi32.GetStockObject(DC_BRUSH)
