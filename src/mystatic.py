from winapp.window import *
from image import BITMAP


########################################
#
########################################
class MyStatic(Window):

    ########################################
    #
    ########################################
    def __init__(self, parent_window):

        self.h_bitmap = None
        self.img_width = 0
        self.img_height = 0

        def _window_proc_callback(hwnd, msg, wparam, lparam):
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._windowproc = WNDPROC(_window_proc_callback)

        newclass = WNDCLASSEX()
        newclass.lpfnWndProc = self._windowproc
        newclass.style = CS_VREDRAW | CS_HREDRAW
        newclass.lpszClassName = 'MyStatic'
        newclass.hBrush = gdi32.GetStockObject(BLACK_BRUSH)
        newclass.hCursor = user32.LoadCursorW(0, IDC_ARROW)
        user32.RegisterClassExW(byref(newclass))

        super().__init__(
            parent_window=parent_window,
            window_class=newclass.lpszClassName,
            style=WS_CHILD,
        )

        ########################################
        #
        ########################################
        def _on_WM_PAINT(hwnd, wparam, lparam):
            if self.h_bitmap is None:
                return
            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, byref(ps))
            rc = self.get_client_rect()
            hdc_mem = gdi32.CreateCompatibleDC(hdc)

            gdi32.SelectObject(hdc_mem, self.h_bitmap)

            gdi32.SetStretchBltMode(hdc, HALFTONE)

            gdi32.StretchBlt(
                # dest
                hdc, 0, 0, rc.right, rc.bottom,
                # scr
                hdc_mem, 0, 0, self.img_width, self.img_height,
                SRCCOPY  # SRCCOPY
            )

            gdi32.DeleteDC(hdc_mem)

            user32.EndPaint(hwnd, byref(ps))
            return FALSE

        self.register_message_callback(WM_PAINT, _on_WM_PAINT)

    ########################################
    #
    ########################################
    def load_hbitmap(self, h_bitmap):
        self.clear()
        self.h_bitmap = h_bitmap
        bm = BITMAP()
        gdi32.GetObjectW(self.h_bitmap, sizeof(BITMAP), byref(bm))
        self.img_width, self.img_height = bm.bmWidth, bm.bmHeight

    ########################################
    #
    ########################################
    def clear(self):
        if self.h_bitmap:
            gdi32.DeleteObject(self.h_bitmap)
            self.h_bitmap = None

