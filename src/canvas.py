"""
Canvas is a window containg a bitmap static with the following features:

- image is centered
- image can be zoomed
- image can be scrolled (if larger than canvas)
- a rectange area of the image can be selected via mouse
- the selection rectangle can be moved and resized

"""

from ctypes import *
from ctypes.wintypes import *

from winapp.window import *
from winapp.dlls import gdi32, user32
#from winapp.image import *
from winapp.const import *
from winapp.wintypes_extended import *

from mystatic import MyStatic

CUR_SCROLL = user32.LoadCursorW(0, MAKEINTRESOURCEW(32654))

#ZOOM_TO_FIT_MARGIN = 0  #10

EVENT_CANVAS_HSCROLLED = 0
EVENT_CANVAS_VSCROLLED = 1
EVENT_CANVAS_ZOOM_CHANGED = 2

class SCROLLINFO(Structure):
    def __init__(self, *args, **kwargs):
        super(SCROLLINFO, self).__init__(*args, **kwargs)
        self.cbSize = sizeof(self)
    _fields_ = [
        ("cbSize", UINT),
        ("fMask", UINT),
        ("nMin", INT),
        ("nMax", INT),
        ("nPage", UINT),
        ("nPos", INT),
        ("nTrackPos", UINT),
    ]


########################################
#
########################################
class Canvas(Window):

    ########################################
    #
    ########################################
    def __init__(self, parent_window, top=0, bgcolor=0x444444, drag_scroll=False):

        self.drag_scroll = drag_scroll

        self.initialized = False
        self.zoom = 1.0

        self.img_width = 0
        self.img_height = 0

        self.scroll_max_x_px = 0
        self.scroll_max_y_px = 0

        # float, -1 to 1
        self.scroll_x = 0
        self.scroll_y = 0

        def _window_proc_callback(hwnd, msg, wparam, lparam):
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        self._windowproc = WNDPROC(_window_proc_callback)

        newclass = WNDCLASSEX()
        newclass.lpfnWndProc = self._windowproc
        newclass.style = CS_VREDRAW | CS_HREDRAW
        newclass.lpszClassName = 'Canvas'
        newclass.hBrush = gdi32.CreateSolidBrush(bgcolor)
        newclass.hCursor = user32.LoadCursorW(0, IDC_ARROW)
        user32.RegisterClassExW(byref(newclass))

        super().__init__(
            window_class=newclass.lpszClassName,
            style=WS_CHILD | WS_VISIBLE | WS_CLIPCHILDREN | WS_VSCROLL | WS_HSCROLL,  # | WS_BORDER
            ex_style=WS_EX_COMPOSITED,
            parent_window=parent_window,
            top=top
        )

        self._hide_scrollbars()

        self.static = MyStatic(self)

        ########################################
        #
        ########################################
        def _on_WM_SIZE(hwnd, wparam, lparam):
            #width, height = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
            self._update_layout() #width, height)

        self.register_message_callback(WM_SIZE, _on_WM_SIZE)

        ########################################
        #
        ########################################
        def _on_WM_HSCROLL(hwnd, wparam, lparam):

            lo = LOWORD(wparam)
            if lo == SB_ENDSCROLL:
                return 0

            scroll_x_px = round(self.scroll_max_x_px * (self.scroll_x + 1) / 2)

            # User clicked the scroll bar shaft above the scroll box.
            if lo == SB_PAGEUP:
                scroll_x_px_new = scroll_x_px - 50

            # User clicked the scroll bar shaft below the scroll box.
            elif lo == SB_PAGEDOWN:
                scroll_x_px_new = scroll_x_px + 50

            # User clicked the top arrow.
            elif lo == SB_LINEUP:
                scroll_x_px_new = scroll_x_px - 5

            # User clicked the bottom arrow.
            elif lo == SB_LINEDOWN:
                scroll_x_px_new = scroll_x_px + 5

            # User dragged the scroll box.
#            elif lo == SB_THUMBPOSITION:
#                scroll_x_px_new = HIWORD(wparam)

            else:  # SB_THUMBTRACK
                scroll_x_px_new = HIWORD(wparam)
                if scroll_x_px_new == 0 and scroll_x_px > 5:
                    return 0

            # New position must be between 0 and the screen height.
            scroll_x_px_new = min(self.scroll_max_x_px, max(0, scroll_x_px_new))

            # If the current position does not change, do not scroll.
            if scroll_x_px_new == scroll_x_px:
                return 0

            self.scroll_x = 2 * scroll_x_px_new / self.scroll_max_x_px - 1

            self._update_layout()

            self.emit(EVENT_CANVAS_HSCROLLED, self.scroll_x)

            return 0

        self.register_message_callback(WM_HSCROLL, _on_WM_HSCROLL)

        ########################################
        #
        ########################################
        def _on_WM_VSCROLL(hwnd, wparam, lparam):

            lo = LOWORD(wparam)
            if lo == SB_ENDSCROLL:
                return 0

            scroll_y_px = round(self.scroll_max_y_px * (self.scroll_y + 1) / 2)

            # User clicked the scroll bar shaft above the scroll box.
            if lo == SB_PAGEUP:
                scroll_y_px_new = scroll_y_px - 50

            # User clicked the scroll bar shaft below the scroll box.
            elif lo == SB_PAGEDOWN:
                scroll_y_px_new = scroll_y_px + 50

            # User clicked the top arrow.
            elif lo == SB_LINEUP:
                scroll_y_px_new = scroll_y_px - 5

            # User clicked the bottom arrow.
            elif lo == SB_LINEDOWN:
                scroll_y_px_new = scroll_y_px + 5

            # User dragged the scroll box.
#            elif lo == SB_THUMBPOSITION:
#                scroll_y_px_new = HIWORD(wparam)

            else:
                scroll_y_px_new = HIWORD(wparam)  #self.scroll_y_px
                if scroll_y_px_new == 0 and scroll_y_px > 5:
                    return 0

            # New position must be between 0 and the screen height.
            scroll_y_px_new = min(self.scroll_max_y_px, max(0, scroll_y_px_new))

            # If the current position does not change, do not scroll.
            if scroll_y_px_new == scroll_y_px:
                return 0

            self.scroll_y = 2 * scroll_y_px_new / self.scroll_max_y_px - 1

            self._update_layout()

            self.emit(EVENT_CANVAS_VSCROLLED, self.scroll_y)

            return 0

        self.register_message_callback(WM_VSCROLL, _on_WM_VSCROLL)

        ########################################
        #
        ########################################
        def _on_WM_MOUSEWHEEL(hwnd, wparam, lparam):
            if self.scroll_max_y_px:
                # Quick and dirty: forward as WM_VSCROLL, with wparam either SB_PAGEDOWN or SB_PAGEUP
                self.send_message(WM_VSCROLL, SB_PAGEDOWN if INT(wparam).value < 0 else SB_PAGEUP, 0)

                # Alternative: calculate explicit new absolute vertical scroll pos based on received wparam value
#               delta = INT(wparam >> 16).value  # Usually +/- 120, occasionally +/- 240
#               pos = ...
#               self.send_message(WM_VSCROLL, MAKELONG(SB_THUMBTRACK, pos), 0)

        self.parent_window.register_message_callback(WM_MOUSEWHEEL, _on_WM_MOUSEWHEEL)

        if drag_scroll:

            ########################################
            # Let all mouse events pass through
            ########################################
            def _on_WM_NCHITTEST(hwnd, wparam, lparam):
                return HTTRANSPARENT

            self.static.register_message_callback(WM_NCHITTEST, _on_WM_NCHITTEST)

            ########################################
            #
            ########################################
            def _on_WM_LBUTTONDOWN(hwnd, wparam, lparam):
                if self.scroll_max_x_px < 1 and self.scroll_max_y_px < 1:
                    return
                x0, y0 = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
                scroll_x_org = round(self.scroll_max_x_px * (self.scroll_x + 1) / 2)
                scroll_y_org = round(self.scroll_max_y_px * (self.scroll_y + 1) / 2)
                user32.SetCapture(self.hwnd)
                user32.SetCursor(CUR_SCROLL)

                ########################################
                #
                ########################################
                def _on_WM_MOUSEMOVE(hwnd, wparam, lparam):
                    x, y = GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam)
                    if self.scroll_max_x_px > 0:
                        scroll_x_px_new = min(self.scroll_max_x_px, max(0, scroll_x_org + x0 - x))
                        self.scroll_x = 2 * scroll_x_px_new / self.scroll_max_x_px - 1
                        self.emit(EVENT_CANVAS_HSCROLLED, self.scroll_x)
                    if self.scroll_max_y_px > 0:
                        scroll_y_px_new = min(self.scroll_max_y_px, max(0, scroll_y_org + y0 - y))
                        self.scroll_y = 2 * scroll_y_px_new / self.scroll_max_y_px - 1  #2 * scroll_y_px_new / self.scroll_max_y_px - 1
                        self.emit(EVENT_CANVAS_VSCROLLED, self.scroll_y)
                    self._update_layout()

                self.register_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)

                ########################################
                #
                ########################################
                def _on_WM_LBUTTONUP(hwnd, wparam, lparam):
                    user32.ReleaseCapture(self.hwnd)
                    self.unregister_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)
                    self.unregister_message_callback(WM_LBUTTONUP, _on_WM_LBUTTONUP)

                self.register_message_callback(WM_LBUTTONUP, _on_WM_LBUTTONUP)

            self.register_message_callback(WM_LBUTTONDOWN, _on_WM_LBUTTONDOWN)

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)
        # Update scrollbar colors
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)

    ########################################
    #
    ########################################
    def set_bgcolor(self, bgcolor):
        user32.SetClassLongPtrW(self.hwnd, GCL_HBRBACKGROUND, gdi32.CreateSolidBrush(bgcolor))
        self.redraw_window()

    ########################################
    #
    ########################################
    def load_hbitmap(self, hbitmap, zoom_to_fit=False, force_update=False, zoom=None):

        self.static.load_hbitmap(hbitmap)
        self.initialized = True

        if zoom_to_fit:
            rc = self.get_window_rect()
            w, h = rc.right - rc.left, rc.bottom - rc.top
            zoom =  min(w / self.static.img_width, h / self.static.img_height)
            self.zoom = min(zoom, 1)  # no upscaling, only downscaling
        else:
            self.zoom = zoom if zoom is not None else 1

        self._update_zoom()

        self.emit(EVENT_CANVAS_ZOOM_CHANGED, self.zoom)

        if force_update:
            user32.InvalidateRect(self.static.hwnd, None, TRUE)
        self.static.show()

    ########################################
    # If width and height did not change
    ########################################
    def update_hbitmap(self, hbitmap, zoom_to_fit=False):
        if not self.initialized:
            self.initialized = True
            return self.load_hbitmap(hbitmap, zoom_to_fit=zoom_to_fit)

#        self.static.load_hbitmap(hbitmap)
        gdi32.DeleteObject(self.static.h_bitmap)
        self.static.h_bitmap = hbitmap
        user32.InvalidateRect(self.static.hwnd, None, TRUE)

    ########################################
    #
    ########################################
    def clear(self):

        self.zoom = 1
        self.emit(EVENT_CANVAS_ZOOM_CHANGED, self.zoom)

        self.scroll_x = 0
        self.scroll_y = 0

        self.initialized = False
        self.static.clear()
        self.static.show(SW_HIDE)
        self._hide_scrollbars()

    ########################################
    # TODO: keep previous center the same
    ########################################
    def zoom_in(self):
        self.zoom *= 1.2
        self._update_zoom()
        self.emit(EVENT_CANVAS_ZOOM_CHANGED, self.zoom)

    ########################################
    #
    ########################################
    def zoom_out(self):
        self.zoom /= 1.2
        self._update_zoom()
        self.emit(EVENT_CANVAS_ZOOM_CHANGED, self.zoom)

    ########################################
    #
    ########################################
    def zoom_original_size(self):
        self.zoom = 1
        self._update_zoom()
        self.emit(EVENT_CANVAS_ZOOM_CHANGED, self.zoom)

    ########################################
    # TODO: keep previous center the same
    ########################################
    def set_zoom(self, zoom):
        self.zoom = zoom
        self._update_zoom()
        self.emit(EVENT_CANVAS_ZOOM_CHANGED, self.zoom)

    ########################################
    #
    ########################################
    def _update_zoom(self):
        self.img_width = int(self.static.img_width * self.zoom)
        self.img_height = int(self.static.img_height * self.zoom)

        self.static.set_window_pos(
            width=self.img_width,
            height=self.img_height,
            flags=SWP_NOMOVE | SWP_NOACTIVATE | SWP_NOZORDER
        )
        self._update_layout()

    ########################################
    #
    ########################################
    def hscroll_to(self, pos):
        self.scroll_x = pos
        self._update_layout()

    ########################################
    #
    ########################################
    def vscroll_to(self, pos):
        self.scroll_y = pos
        self._update_layout()

    ########################################
    #
    ########################################
    def _update_layout(self): #, width=None, height=None):
        if self.static.h_bitmap is None:
            return

#        if width is None:

        rc = self.get_window_rect()
        width, height = rc.right - rc.left, rc.bottom - rc.top

        if self.img_width < width:
            self.scroll_x = 0

        if self.img_height < height:
            self.scroll_y = 0

        x = round((width - self.img_width + self.scroll_x * min(width - self.img_width, 0)) / 2)
        y = round((height - self.img_height + self.scroll_y * min(height - self.img_height, 0)) / 2)

        self.static.set_window_pos(
            x=x,
            y=y,
            flags=SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
        )

#        rc = self.static.get_client_rect()
#        x, y = rc.left, rc.top

        if not self.drag_scroll:

            si = SCROLLINFO()
            si.fMask = SIF_RANGE | SIF_PAGE | SIF_POS

    #            The nPage member must specify a value from 0 to nMax - nMin +1.
    #            The nPos member must specify a value between nMin and nMax - max( nPage– 1, 0).
    #            If either value is beyond its range, the function sets it to a value that is just within the range.

            si.nPage = width + 1
            si.nMax = self.img_width
            si.nPos = -x
            user32.SetScrollInfo(self.hwnd, SB_HORZ, byref(si), TRUE)

            si.nPage = height + 1
            si.nMax = self.img_height
            si.nPos = -y
            user32.SetScrollInfo(self.hwnd, SB_VERT, byref(si), TRUE)

        # The horizontal scrolling range is defined by (bitmap_width) - (client_width).
        # The vertical scrolling range is defined by (bitmap_height) - (client_height).
        self.scroll_max_x_px = max(self.img_width - width, 0)
        self.scroll_max_y_px = max(self.img_height - height, 0)

    ########################################
    #
    ########################################
    def _hide_scrollbars(self):
        si = SCROLLINFO()
        si.fMask = SIF_RANGE
        user32.SetScrollInfo(self.hwnd, SB_HORZ, byref(si), TRUE)
        user32.SetScrollInfo(self.hwnd, SB_VERT, byref(si), TRUE)


########################################
#
########################################
#if __name__ == '__main__':
#    from winapp.mainwin import *
#
#    main = MainWin(window_title='Demo Canvas', width=640, height=640)
#
#    win = Canvas(main)
#
##    win.static_image.load_bitmap(r'D:\test\test_512.bmp')
#
#    win.load_file(r'D:\test\test_512.bmp')
#
#    ########################################
#    #
#    ########################################
#    def _on_WM_SIZE(hwnd, wparam, lparam):
#        width, height = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
#        win.set_window_pos(width=width, height=height, flags=SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOCOPYBITS)
#
#    main.register_message_callback(WM_SIZE, _on_WM_SIZE)
#
#    main.apply_theme(True)
#    main.show()
#
##    win.zoom_in()
#
#    main.run()
