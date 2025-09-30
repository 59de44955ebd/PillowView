# https://learn.microsoft.com/en-us/windows/win32/controls/edit-controls

from ..const import *  #WS_CHILD, WS_VISIBLE
from ..window import *


########################################
# Wrapper Class
########################################
class Edit(Window):

    ########################################
    #
    ########################################
    def __init__(self, parent_window=None, style=WS_CHILD | WS_VISIBLE, ex_style=0,
            left=0, top=0, width=0, height=0, window_title=None, wrap_hwnd=None,
            dark_bg_color=DARK_CONTROL_BG_COLOR, dark_text_color=DARK_TEXT_COLOR):

        super().__init__(
            WC_EDIT,
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

        self._dark_bg_color = dark_bg_color
        self._dark_text_color = dark_text_color

    ########################################
    #
    ########################################
    def destroy_window(self):
        if self.is_dark:
            self.parent_window.unregister_message_callback(WM_CTLCOLOREDIT, self._on_WM_CTLCOLOREDIT)
        super().destroy_window()

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)

        if is_dark:
            # replace client edge with border
            ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
            if ex_style & WS_EX_CLIENTEDGE:
                style = user32.GetWindowLongW(self.hwnd, GWL_STYLE)
                user32.SetWindowLongA(self.hwnd, GWL_STYLE, style | WS_BORDER)
                user32.SetWindowLongA(self.hwnd, GWL_EXSTYLE, ex_style & ~WS_EX_CLIENTEDGE)
                user32.SetWindowPos(self.hwnd, 0, 0,0, 0,0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
            self.parent_window.register_message_callback(WM_CTLCOLOREDIT, self._on_WM_CTLCOLOREDIT)
        else:
            # replace border with client edge
            style = user32.GetWindowLongW(self.hwnd, GWL_STYLE)
            if style & WS_BORDER:
                ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
                user32.SetWindowLongA(self.hwnd, GWL_EXSTYLE, ex_style | WS_EX_CLIENTEDGE)
                user32.SetWindowLongA(self.hwnd, GWL_STYLE, style & ~WS_BORDER)
                user32.SetWindowPos(self.hwnd, 0, 0,0, 0,0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)
            self.parent_window.unregister_message_callback(WM_CTLCOLOREDIT, self._on_WM_CTLCOLOREDIT)

    ########################################
    #
    ########################################
    def _on_WM_CTLCOLOREDIT(self, hwnd, wparam, lparam):
        if lparam == self.hwnd:
            gdi32.SetTextColor(wparam, self._dark_text_color)
            gdi32.SetBkColor(wparam, self._dark_bg_color)
            gdi32.SetDCBrushColor(wparam, self._dark_bg_color)
            return gdi32.GetStockObject(DC_BRUSH)
