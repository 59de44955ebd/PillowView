# https://learn.microsoft.com/en-us/windows/win32/controls/static-controls

from ..const import *
from ..window import *
from ..dlls import user32
from ..themes import *


########################################
# Wrapper Class
########################################
class Static(Window):

    ########################################
    #
    ########################################
    def __init__(
        self, parent_window=None, style=WS_CHILD | WS_VISIBLE, ex_style=0,
        left=0, top=0, width=0, height=0, window_title=None,
        bg_color=0xffffff, #COLOR_WINDOW + 1,
        dark_bg_color=DARK_BG_COLOR,
        wrap_hwnd=None
    ):

        self.bg_color = bg_color
        self.dark_bg_color = dark_bg_color

        super().__init__(
            WC_STATIC,
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

        if self.parent_window:
            self.parent_window.register_message_callback(WM_CTLCOLORSTATIC, self._on_WM_CTLCOLORSTATIC)

    ########################################
    #
    ########################################
    def destroy_window(self):
        if self.parent_window:
            self.parent_window.unregister_message_callback(WM_CTLCOLORSTATIC, self._on_WM_CTLCOLORSTATIC)
        super().destroy_window()

    ########################################
    #
    ########################################
    def _on_WM_CTLCOLORSTATIC(self, hwnd, wparam, lparam):
        if self.is_dark:
            gdi32.SetTextColor(wparam, DARK_TEXT_COLOR if self.is_dark else 0x000000)
            gdi32.SetBkColor(wparam, self.dark_bg_color if self.is_dark else self.bg_color)
            gdi32.SetDCBrushColor(wparam, self.dark_bg_color if self.is_dark else self.bg_color)
            return gdi32.GetStockObject(DC_BRUSH)

    ########################################
    #
    ########################################
    def set_image(self, hbitmap):
        user32.SendMessageW(self.hwnd, STM_SETIMAGE, IMAGE_BITMAP, hbitmap)

    ########################################
    #
    ########################################
    def set_icon(self, hicon):
        user32.SendMessageW(self.hwnd, STM_SETICON, hicon, 0)

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)
        self.force_redraw_window()  # triggers WM_CTLCOLORSTATIC
