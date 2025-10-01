# https://learn.microsoft.com/en-us/windows/win32/controls/trackbar-control-reference

from ctypes import windll, byref
from ctypes.wintypes import *

from ..wintypes_extended import WNDPROC, HIWORD
from ..const import * #WM_USER
from ..themes import *
from ..dlls import user32
from ..window import *


########################################
# Wrapper Class
########################################
class TrackBar(Window):

    def __init__(self, parent_window=None, range_max=100, range_min=0, page_size=1, current_value=0, left=0, top=0, width=0, height=0,
            hscroll_callback=None,
            restore_focus_hwnd=None,
            style=WS_CHILD | WS_VISIBLE | TBS_HORZ | TBS_TOOLTIPS,
            ex_style=0,
            window_title=None
        ):

        super().__init__(
            WC_TRACKBAR,
            parent_window=parent_window,
            style=style,
            ex_style=ex_style,
            left=left,
            top=top,
            width=width,
            height=height,
            window_title=window_title,
        )

        self.width = width
        self.height = height

        self.hscroll_callback = hscroll_callback
        self.restore_focus_hwnd = restore_focus_hwnd if restore_focus_hwnd else parent_window.hwnd

        self.default = current_value
        self.range_min = range_min
        self.range_max = range_max

        if range_min != 0:
            user32.SendMessageW(self.hwnd, TBM_SETRANGEMIN, FALSE, range_min)

        user32.SendMessageW(self.hwnd, TBM_SETRANGEMAX, FALSE, range_max)

        user32.SendMessageW(self.hwnd, TBM_SETPAGESIZE, 0, page_size)

        user32.SendMessageW(self.hwnd, TBM_SETPOS, TRUE, current_value)

        # makes slider scroll to click position
        self.parent_window.register_message_callback(WM_HSCROLL, self.on_WM_HSCROLL)

    ########################################
    #
    ########################################
    def destroy_window(self):
        self.parent_window.unregister_message_callback(WM_HSCROLL, self.on_WM_HSCROLL)
        if self.is_dark:
            self.parent_window.unregister_message_callback(WM_CTLCOLORSTATIC, self.on_WM_CTLCOLORSTATIC)
        super().destroy_window()

    def get_pos(self):
        return user32.SendMessageW(self.hwnd, TBM_GETPOS, 0, 0)

    def set_pos(self, pos):
        user32.SendMessageW(self.hwnd, TBM_SETPOS, 1, pos)

    def set_pos_notify(self, pos):
        user32.SendMessageW(self.hwnd, TBM_SETPOSNOTIFY, 0, pos)

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)

        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)

        if is_dark:
            self.parent_window.register_message_callback(WM_CTLCOLORSTATIC, self.on_WM_CTLCOLORSTATIC)
            self.parent_window.register_message_callback(WM_NOTIFY, self.on_WM_NOTIFY)

        else:
            self.parent_window.unregister_message_callback(WM_CTLCOLORSTATIC, self.on_WM_CTLCOLORSTATIC)
            self.parent_window.unregister_message_callback(WM_NOTIFY, self.on_WM_NOTIFY)

        # Update tooltip colors
        hwnd_tooltip = user32.SendMessageW(self.hwnd, TBM_GETTOOLTIPS, 0, 0)
        if hwnd_tooltip:
            uxtheme.SetWindowTheme(hwnd_tooltip, 'DarkMode_Explorer' if is_dark else 'Explorer', None)

    ########################################
    #
    ########################################
    def on_WM_CTLCOLORSTATIC(self, hwnd, wparam, lparam):
        if lparam == self.hwnd:
            gdi32.SetDCBrushColor(wparam, DARK_BG_COLOR)
            return gdi32.GetStockObject(DC_BRUSH)

    ########################################
    # makes slider scroll to click position
    ########################################
    def on_WM_HSCROLL(self, hwnd, wparam, lparam):
        if lparam == self.hwnd:
            lo, hi, = wparam & 0xFFFF, (wparam >> 16) & 0xFFFF

            if lo == TB_ENDTRACK:
                # remove keyboardfocus from trackbar
                if self.restore_focus_hwnd:
                    user32.SetFocus(self.restore_focus_hwnd)
                return 0

            if lo == TB_PAGEDOWN or lo == TB_PAGEUP: # clicked into slider
                pt = POINT()
                user32.GetCursorPos(byref(pt))
                rc = RECT()
                user32.GetWindowRect(self.hwnd, byref(rc))
                hi = self.range_min + int((pt.x - rc.left - 10) / (rc.right - rc.left - 20) * (self.range_max - self.range_min))
                user32.SendMessageW(self.hwnd, TBM_SETPOS, TRUE, hi)
            else:
                hi = SHORT(hi).value

            if self.hscroll_callback:
                self.hscroll_callback(lo, hi)
            return 0

    ########################################
    #
    ########################################
    def on_WM_NOTIFY(self, hwnd, wparam, lparam):
        nmhdr = cast(lparam, LPNMHDR).contents
        msg = nmhdr.code
        if msg == NM_CUSTOMDRAW and nmhdr.hwndFrom == self.hwnd:
            nmcd = cast(lparam, LPNMCUSTOMDRAW).contents

            if nmcd.dwDrawStage == CDDS_PREPAINT:
                return CDRF_DODEFAULT if user32.IsWindowEnabled(self.hwnd) else CDRF_NOTIFYITEMDRAW  #| CDRF_NOTIFYPOSTERASE

            if nmcd.dwDrawStage == CDDS_ITEMPREPAINT:
                return CDRF_NOTIFYPOSTPAINT

            elif nmcd.dwDrawStage == CDDS_ITEMPOSTPAINT:
                # 2: knob
                # 3: channel

                if nmcd.dwItemSpec == 3:
                    user32.FillRect(nmcd.hdc, byref(nmcd.rc), DARK_DISABLED_BRUSH)
                    return CDRF_SKIPDEFAULT
                return CDRF_DODEFAULT
