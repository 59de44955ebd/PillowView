from winapp.window import *
from winapp.wintypes_extended import *

from canvas import EVENT_CANVAS_ZOOM_CHANGED
from const import *


########################################
#
########################################
class Selection(Window):

    ########################################
    #
    ########################################
    def __init__(self, canvas):

        self.zoom = 1

        def _window_proc_callback(hwnd, msg, wparam, lparam):
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._windowproc = WNDPROC(_window_proc_callback)

        newclass = WNDCLASSEX()
        newclass.lpfnWndProc = self._windowproc
#        newclass.style = CS_VREDRAW | CS_HREDRAW
        newclass.lpszClassName = 'Selection'
        newclass.hBrush = HBRUSH_NULL
        newclass.hCursor = user32.LoadCursorW(0, IDC_ARROW)
        user32.RegisterClassExW(byref(newclass))

        super().__init__(
            parent_window=canvas.static,
            window_class=newclass.lpszClassName,
            style=WS_CHILD | WS_THICKFRAME,
        )

        user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE)

        ########################################
        #
        ########################################
        def _on_WM_NCPAINT(hwnd, wparam, lparam):
            hdc = user32.GetWindowDC(hwnd)
            rc = self.get_window_rect()

            # This creates a 1 px wide b/w dotted border
            hpen = gdi32.CreatePen(PS_SOLID, 1, 0)
            gdi32.SelectObject(hdc, hpen)
            gdi32.SelectObject(hdc, HBRUSH_NULL)
            gdi32.Rectangle(hdc, 0, 0, rc.right - rc.left, rc.bottom - rc.top)
            gdi32.DeleteObject(hpen)
            user32.DrawFocusRect(hdc, byref(RECT(0, 0, rc.right - rc.left, rc.bottom - rc.top)))

            user32.ReleaseDC(hwnd, hdc)
            return 1

        self.register_message_callback(WM_NCPAINT, _on_WM_NCPAINT)

        ########################################
        #
        ########################################
        def _on_WM_NCCALCSIZE(hwnd, wparam, lparam):
            if wparam:
                # Reduce thick frame width from 7 to 3
                parms = cast(lparam, POINTER(NCCALCSIZE_PARAMS)).contents
                parms.rgrc[0].left -= 4
                parms.rgrc[0].right += 4
                parms.rgrc[0].top -= 4
                parms.rgrc[0].bottom += 4

        self.register_message_callback(WM_NCCALCSIZE, _on_WM_NCCALCSIZE)

        ########################################
        #
        ########################################
        def _on_WM_RBUTTONDOWN(hwnd, wparam, lparam):
            x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
            pt_move = POINT(x, y)
            rc_parent = self.parent_window.get_client_rect()
            rc = self.get_window_rect()
            max_x = rc_parent.right - (rc.right - rc.left)
            max_y = rc_parent.bottom - (rc.bottom - rc.top)
            user32.SetCursor(HCURSOR_MOVE)
            user32.SetCapture(self.parent_window.hwnd)

            ########################################
            #
            ########################################
            def _on_WM_MOUSEMOVE(hwnd, wparam, lparam):
                x, y = GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam)
                x = min(max(x - pt_move.x, 0), max_x)
                y = min(max(y - pt_move.y, 0), max_y)
                self.set_window_pos(x, y, flags=SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER)

            self.parent_window.register_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)

            ########################################
            #
            ########################################
            def _on_WM_RBUTTONUP(hwnd, wparam, lparam):
                user32.ReleaseCapture(hwnd)
                self.parent_window.unregister_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)
                self.parent_window.unregister_message_callback(WM_RBUTTONUP, _on_WM_RBUTTONUP)

            self.parent_window.register_message_callback(WM_RBUTTONUP, _on_WM_RBUTTONUP)

        self.register_message_callback(WM_RBUTTONDOWN, _on_WM_RBUTTONDOWN)

        ########################################
        #
        ########################################
        def _on_WM_LBUTTONDOWN(hwnd, wparam, lparam):
            self.show(SW_HIDE)

        self.register_message_callback(WM_LBUTTONDOWN, _on_WM_LBUTTONDOWN)

        canvas.connect(EVENT_CANVAS_ZOOM_CHANGED, self._zoom_changed)

    ########################################
    #
    ########################################
    def _zoom_changed(self, zoom):

        f = zoom / self.zoom
        self.zoom = zoom

        rc = self.get_rect()

        self.set_window_pos(
            round(rc.left * f),
            round(rc.top * f),
            round((rc.right - rc.left) * f),
            round((rc.bottom - rc.top) * f),
            flags=SWP_NOACTIVATE | SWP_NOZORDER
        )

    ########################################
    #
    ########################################
    def start_drawing(self, x, y):

        x0, y0 = x, y
        rc = self.parent_window.get_client_rect()

        self.set_window_pos(x, y, 0, 0, flags=SWP_NOACTIVATE | SWP_NOZORDER)
        self.show(SW_HIDE)

        user32.SetCursor(HCURSOR_CROSS)
        user32.SetCapture(self.parent_window.hwnd)

        ########################################
        #
        ########################################
        def _on_WM_MOUSEMOVE(hwnd, wparam, lparam):
            x, y = GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam)

            if x < x0:
                x = max(x, 0)
                w = x0 - x
            else:
                w = min(x - x0, rc.right - x0)
                x = x0

            if y < y0:
                y = max(y, 0)
                h = y0 - y
            else:
                h = min(y - y0, rc.bottom - y0)
                y = y0

            if not self.visible and w and h:
                self.show()

            self.set_window_pos(x, y, w, h, flags=SWP_NOACTIVATE | SWP_NOZORDER)

        self.parent_window.register_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)

        ########################################
        #
        ########################################
        def _on_WM_LBUTTONUP(hwnd, wparam, lparam):
            user32.ReleaseCapture(self.parent_window.hwnd)
            user32.SetCursor(NULL)
            self.parent_window.unregister_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)
            self.parent_window.unregister_message_callback(WM_LBUTTONUP, _on_WM_LBUTTONUP)

        self.parent_window.register_message_callback(WM_LBUTTONUP, _on_WM_LBUTTONUP)

    ########################################
    # Selection rect relative to static
    ########################################
    def get_rect(self):
        rc = self.get_window_rect()
        user32.MapWindowPoints(None, self.parent_window.hwnd, byref(rc), 2)
        return rc

    ########################################
    #
    ########################################
#    def do_zoom(self, zoom_handler):
#        rc1 = self.parent_window.get_client_rect()
#        rc = self.get_rect()
#
#        zoom_handler()
#
#        rc2 = self.parent_window.get_client_rect()
#        f = rc2.right / rc1.right
#        self.set_window_pos(
#            round(rc.left * f),
#            round(rc.top * f),
#            round((rc.right - rc.left) * f),
#            round((rc.bottom - rc.top) * f),
#            flags=SWP_NOACTIVATE | SWP_NOZORDER
#        )
