# https://learn.microsoft.com/en-us/windows/win32/controls/status-bar-reference

from ctypes import byref, pointer, create_unicode_buffer
from ctypes.wintypes import INT, RECT

from ..const import * #WM_USER, WS_CHILD, WS_VISIBLE, BF_MONO, BF_FLAT, BDR_OUTER
from ..window import *
from ..dlls import user32
from ..themes import *

# custom (for SB_GETBORDERS)
class BORDERINFO(Structure):
    _fields_ = [
        ("horizontal", INT),
        ("vertical", INT),
        ("between", INT),
    ]


class StatusBar(Window):

    def __init__(
        self,
        parent_window,
        style=WS_CHILD | WS_VISIBLE,
        ex_style=0, window_title=None,
        parts=[],
        parts_right_aligned=False
    ):

        self.parts = parts

        num_parts = len(parts) if parts else 1
        self.parts_right_aligned = False if num_parts < 2 else parts_right_aligned

        super().__init__(
            WC_STATUSBAR,
            parent_window=parent_window,
            style=style,
            ex_style=ex_style,
            window_title=window_title
        )

        if num_parts > 1:
            rc = RECT()
            user32.GetWindowRect(parent_window.hwnd, byref(rc))
            w = rc.right - rc.left
            sb_parts = (INT * num_parts)()

            if self.parts_right_aligned:
                for i in range(num_parts - 1):
                    sb_parts[i] = w - sum(parts[i+1:])
            else:
                # fixed position (left aligned)
                for i in range(num_parts - 1):
                    sb_parts[i] = parts[i]

            sb_parts[num_parts - 1] = -1
            user32.SendMessageW(self.hwnd, SB_SETPARTS, num_parts, sb_parts)

        # get height of statusbar
        rc = RECT()
        user32.SendMessageW(self.hwnd, SB_GETRECT, 0, byref(rc))
        self.height = rc.bottom

        if parent_window.is_dark:
            self.apply_theme(True)

    def set_parts(self, parts=[], parts_right_aligned=False):
        self.parts = parts

        num_parts = len(parts) if parts else 1
        self.parts_right_aligned = False if num_parts < 2 else parts_right_aligned

        if num_parts > 1:
            rc = RECT()
            user32.GetWindowRect(self.parent_window.hwnd, byref(rc))
            w = rc.right - rc.left
            sb_parts = (INT * num_parts)()

            if self.parts_right_aligned:
                for i in range(num_parts - 1):
                    sb_parts[i] = w - sum(parts[i+1:])
            else:
                # fixed position (left aligned)
                for i in range(num_parts - 1):
                    sb_parts[i] = parts[i]

            sb_parts[num_parts - 1] = -1
            user32.SendMessageW(self.hwnd, SB_SETPARTS, num_parts, sb_parts)
        else:
            sb_parts = (INT * 1)(-1)
            res = self.send_message(SB_SETPARTS, 1, sb_parts)

    def set_text(self, msg='', part=0):
        user32.SendMessageW(self.hwnd, SB_SETTEXTW, part, msg)

    def set_icon(self, hicon, part=0):
        user32.SendMessageW(self.hwnd, SB_SETICON, part, hicon)

    def right_align_parts(self, width):
        status_parts_count = len(self.parts)
        sb_parts = (INT * status_parts_count)()
        for i in range(status_parts_count - 1):
            sb_parts[i] = width - sum(self.parts[i + 1:])
        sb_parts[status_parts_count - 1] = -1
        user32.SendMessageW(self.hwnd, SB_SETPARTS, status_parts_count, sb_parts)

#    def update_size(self, *args):
#        user32.SendMessageW(self.hwnd, WM_SIZE, 0, 0)

    def update_size(self, width=None):
        user32.SendMessageW(self.hwnd, WM_SIZE, 0, 0)
        if self.parts_right_aligned:
            self.right_align_parts(width)

    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)

        if is_dark:
            hfont = user32.SendMessageW(self.hwnd, WM_GETFONT, 0, 0)
            rc_part = RECT()

            def _on_WM_PAINT(hwnd, wparam, lparam):
                ps = PAINTSTRUCT()
                hdc = user32.BeginPaint(self.hwnd, byref(ps))

                user32.FillRect(hdc, byref(ps.rcPaint), DARK_BG_BRUSH)

                # Draw 1 px border at top
                ps.rcPaint.bottom = ps.rcPaint.top + 1
                user32.FillRect(hdc, byref(ps.rcPaint), DARK_SEPARATOR_BRUSH)

                gdi32.SelectObject(hdc, hfont)
                gdi32.SetBkMode(hdc, TRANSPARENT)
                gdi32.SetTextColor(hdc, DARK_TEXT_COLOR)

                for i in range(len(self.parts) + 1):
                    user32.SendMessageW(self.hwnd, SB_GETRECT, i, byref(rc_part))
                    if ps.rcPaint.left >= rc_part.right or ps.rcPaint.right < rc_part.left:
                        continue

                    # Draw text
                    text_len = user32.SendMessageW(self.hwnd, SB_GETTEXTLENGTHW, i, 0) + 1
                    buf = create_unicode_buffer(text_len)
                    user32.SendMessageW(self.hwnd, SB_GETTEXTW, i, buf)
                    user32.DrawTextW(hdc, buf.value, text_len,
                            byref(RECT(rc_part.left + 2, rc_part.top + 1, rc_part.right, rc_part.bottom - 1)),
                            DT_SINGLELINE | DT_VCENTER | DT_LEFT)

                    # Draw separator
                    if i < len(self.parts) - 1:
                        user32.FillRect(hdc, byref(RECT(rc_part.right - 1, rc_part.top + 1, rc_part.right, rc_part.bottom - 3)),
                                DARK_SEPARATOR_BRUSH)

                user32.EndPaint(self.hwnd, byref(ps))
                return 0

            def _on_WM_ERASEBKGND(hwnd, wparam, lparam):
                return 0

            self.register_message_callback(WM_PAINT, _on_WM_PAINT)
            self.register_message_callback(WM_ERASEBKGND, _on_WM_ERASEBKGND)
        else:
            self.unregister_message_callback(WM_PAINT)
            self.unregister_message_callback(WM_ERASEBKGND)
