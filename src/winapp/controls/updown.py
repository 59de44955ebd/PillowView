# https://learn.microsoft.com/en-us/windows/win32/controls/up-down-control-reference

from ctypes import Structure, POINTER
from ctypes.wintypes import INT

from ..wintypes_extended import MAKELPARAM
from ..const import * #WM_USER
from ..window import *
from .common import NMHDR

class NMUPDOWN(Structure):
    _fields_ = [
        ("hdr", NMHDR),
        ("iPos", INT),
        ("iDelta", INT),
    ]
LPNMUPDOWN = POINTER(NMUPDOWN)


########################################
# Wrapper Class
########################################
class UpDown(Window):

    ########################################
    #
    ########################################
    def __init__(
        self, parent_window=None, style=WS_CHILD | WS_VISIBLE, ex_style=0,
            left=0, top=0, width=0, height=0, window_title=None):

        super().__init__(
            WC_UPDOWN,
            parent_window=parent_window,
            style=style,
            ex_style=ex_style,
            left=left,
            top=top,
            width=width,
            height=height,
            window_title=window_title,
        )

        if style & UDS_AUTOBUDDY:
            self.hwnd_buddy = user32.SendMessageW(self.hwnd, UDM_GETBUDDY, 0, 0)

    ########################################
    #
    ########################################
    def destroy_window(self):
        if self.is_darkmode:
            self.parent_window.unregister_callback(WM_CTLCOLOREDIT, self.on_WM_CTLCOLOREDIT)
        if self.hwnd_buddy:
            user32.DestroyWindow(self.hwnd_buddy)
        super().destroy_window()

    def get_range(self):
        return user32.SendMessageW(self.hwnd, UDM_GETRANGE, 0, 0)

    def set_range(self, from_, to):
        # Sets the minimum and maximum positions (range) for an up-down control.
        user32.SendMessageW(self.hwnd, UDM_SETRANGE, 0, MAKELPARAM(to, from_))

    def get_range32(self):
        return user32.SendMessageW(self.hwnd, UDM_GETRANGE32, 0, 0)

    def set_range32(self, from_, to):
        # Sets the 32-bit range of an up-down control.
        user32.SendMessageW(self.hwnd, UDM_SETRANGE32, 0, MAKELPARAM(to, from_))

    def get_pos(self):
        return user32.SendMessageW(self.hwnd, UDM_GETPOS, 0, 0)

    def set_pos(self, pos):
        # Sets the current position for an up-down control with 16-bit precision.
        user32.SendMessageW(self.hwnd, UDM_SETPOS, 0, pos)

    def get_pos32(self):
        return user32.SendMessageW(self.hwnd, UDM_GETPOS32, 0, 0)

    def set_pos32(self, pos):
        # Sets the position of an up-down control with 32-bit precision.
        user32.SendMessageW(self.hwnd, UDM_SETPOS32, 0, pos)

    def get_buddy(self):
        return user32.SendMessageW(self.hwnd, UDM_GETBUDDY, 0, 0)

    def set_buddy(self, win):
        # Sets the buddy window for an up-down control.
        user32.SendMessageW(self.hwnd, UDM_SETBUDDY, win.hwnd, 0)
        self.hwnd_buddy = win.hwnd

    ########################################
    # special
    ########################################
    def set_window_pos(self, x, y, w, h, hwnd_insert_after=0, flags=0):
        if self.hwnd_buddy and flags & SWP_NOSIZE:
            rc = RECT()
            user32.GetWindowRect(self.hwnd_buddy, byref(rc))
            user32.SetWindowPos(self.hwnd_buddy, hwnd_insert_after, x, y, 0, 0, flags)
            super().set_window_pos(x + rc.right - rc.left + 1, y, 0, 0, hwnd_insert_after, SWP_NOSIZE)
        else:
            super().set_window_pos(x, y, w, h, hwnd_insert_after, flags)

    ########################################
    # special
    ########################################
    def get_window_rect(self):
        rc = RECT()
        user32.GetWindowRect(self.hwnd, byref(rc))
        if self.hwnd_buddy:
            rc2 = RECT()
            user32.GetWindowRect(self.hwnd_buddy, byref(rc2))
            rc.left = rc2.left
        return rc

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        #print('Button apply_theme')
        self.is_darkmode = is_dark

        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)

    ########################################
    #
    ########################################
    def on_WM_CTLCOLOREDIT(self, hwnd, wparam, lparam):
        if lparam == self.hwnd_buddy:
            gdi32.SetTextColor(wparam, DARK_TEXT_COLOR)
            gdi32.SetBkColor(wparam, DARK_CONTROL_BG_COLOR)
            gdi32.SetDCBrushColor(wparam, DARK_CONTROL_BG_COLOR)
            return gdi32.GetStockObject(DC_BRUSH)
