# https://learn.microsoft.com/en-us/windows/win32/controls/toolbar-control-reference

from ctypes import Structure, sizeof, byref, cast
from ctypes.wintypes import *

from winapp.const import *
from winapp.controls.common import *
from winapp.dlls import user32
from winapp.themes import *
from winapp.window import *
from winapp.wintypes_extended import DWORD_PTR, UINT_PTR, MAKELONG

class TBMETRICS(Structure):
    def __init__(self, *args, **kwargs):
        super(TBMETRICS, self).__init__(*args, **kwargs)
        self.cbSize = sizeof(self)
    _fields_ = [
        ("cbSize", UINT),
        ("dwMask", DWORD),
        ("cxPad", INT),
        ("cyPad", INT),
        ("cxBarPad", INT),
        ("cyBarPad", INT),
        ("cxButtonSpacing", INT),
        ("cyButtonSpacing", INT),
    ]

class TBBUTTONINFOW(Structure):
    def __init__(self, *args, **kwargs):
        super(TBBUTTONINFOW, self).__init__(*args, **kwargs)
        self.cbSize = sizeof(self)
    _fields_ = [
        ("cbSize", UINT),
        ("dwMask", DWORD),
        ("idCommand", INT),
        ("iImage", INT),
        ("fsState", BYTE),
        ("fsStyle", BYTE),
        ("cx", WORD),
        ("lParam", DWORD_PTR),
        ("pszText", LPWSTR),
        ("cchText", INT)
    ]

class TBREPLACEBITMAP(Structure):
    _fields_ = [
        ("hInstOld", HINSTANCE),
        ("nIDOld", UINT_PTR),
        ("hInstNew", HINSTANCE),
        ("nIDNew", UINT_PTR),
        ("nButtons", INT),
    ]

class NMTOOLBARW(Structure):
    _fields_ = [
        ("hdr", NMHDR),
        ("iItem", INT),
        ("tbButton", TBBUTTON),
        ("cchText", INT),
        ("pszText", LPWSTR),
        ("rcButton", RECT),
    ]

DARK_TOOLBAR_BUTTON_CHECKED_BG_COLOR = 0x383838
DARK_TOOLBAR_BUTTON_CHECKED_BG_BRUSH = gdi32.CreateSolidBrush(DARK_TOOLBAR_BUTTON_CHECKED_BG_COLOR)

DARK_TOOLBAR_BUTTON_CHECKED_BORDER_COLOR = 0x646464

DARK_TOOLBAR_BUTTON_ROLLOVER_BG_COLOR = 0x454545
DARK_TOOLBAR_BUTTON_ROLLOVER_BG_BRUSH = gdi32.CreateSolidBrush(DARK_TOOLBAR_BUTTON_ROLLOVER_BG_COLOR)

DARK_TOOLBAR_BUTTON_ROLLOVER_BORDER_COLOR = 0x9b9b9b

TOOLBAR_BORDER_BRUSH = BORDER_BRUSH  #gdi32.CreateSolidBrush(0xA0A0A0)
DARK_TOOLBAR_BORDER_BRUSH = DARK_BORDER_BRUSH  #gdi32.CreateSolidBrush(0x646464)


########################################
# Wrapper Class
########################################
class ToolBar(Window):

    def __init__(
        self,
        parent_window=None,
        toolbar_buttons=None,

        h_bitmap=None,
        h_imagelist_disabled=None,

        h_bitmap_dark=None,
        h_imagelist_disabled_dark=None,

        icon_size=16,
        left=0, top=0,
        width=0, height=0,  # only used if CCS_NORESIZE set in styles
        style=WS_CHILD | WS_VISIBLE | CCS_NODIVIDER,
        ex_style=0, #WS_EX_COMPOSITED,
        window_title='',
        hide_text=False,
        num_images=None
    ):

        self.has_border = style & WS_BORDER
        if self.has_border:
            style &= ~WS_BORDER

        super().__init__(
            WC_TOOLBAR,
            parent_window=parent_window,
            left=left, top=top,
            width=width, height=height,
            style=style,
            ex_style=ex_style,
            window_title=window_title
        )

        if window_title:
            user32.SetWindowTextW(self.hwnd, window_title)

        self.is_vertical = style & CCS_VERT

        # The size can be set only before adding any bitmaps to the toolbar.
        # If an application does not explicitly set the bitmap size, the size defaults to 16 by 15 pixel
        user32.SendMessageW(self.hwnd, TB_SETBITMAPSIZE, 0, MAKELONG(icon_size, icon_size))

#        user32.SendMessageW(self.hwnd, TB_SETPADDING, 0, MAKELONG(6, 6))  # 6 => 28x28

        # Do not forget to send TB_BUTTONSTRUCTSIZE if the toolbar was created by using CreateWindowEx.
        user32.SendMessageW(self.hwnd, TB_BUTTONSTRUCTSIZE, sizeof(TBBUTTON), 0)

        self.__h_bitmap = h_bitmap
        self.__h_imagelist_disabled = h_imagelist_disabled

        self.__h_bitmap_dark = h_bitmap_dark
        self.__h_imagelist_disabled_dark = h_imagelist_disabled_dark

        num_buttons = len(toolbar_buttons) if toolbar_buttons else 0
        self.__num_images = num_images or num_buttons

        self.__wholedropdown_button_ids = []
        self.__dropdown_button_ids = []

        if toolbar_buttons:

            if h_bitmap:
                tb = TBADDBITMAP()
                tb.hInst = 0
                tb.nID = self.__h_bitmap
                image_list_id = user32.SendMessageW(self.hwnd, TB_ADDBITMAP, num_images or num_buttons, byref(tb))
            else:
                image_list_id = 0

            tb_buttons = (TBBUTTON * num_buttons)()

            j = 0
            for (i, btn) in enumerate(toolbar_buttons):
                if btn[0] == '-':
                    tb_buttons[i] = TBBUTTON(
                        0,#5,
                        btn[1] if len(btn) > 1 else 0,
                        TBSTATE_ENABLED | (TBSTATE_WRAP if self.is_vertical else 0),
                        BTNS_SEP,
                    )
                else:
                    tb_buttons[i] = TBBUTTON(
                        MAKELONG(j, image_list_id),
                        btn[1], # command_id
                        btn[3] if len(btn) > 3 else TBSTATE_ENABLED,
                        btn[2] if len(btn) > 2 else BTNS_BUTTON,
                        (BYTE * 6)(),
                        btn[4] if len(btn) > 4 else 0,  # dwData
                        btn[0]
                    )

                    if len(btn) > 2:
                        if btn[2] & BTNS_DROPDOWN or btn[2] & BTNS_WHOLEDROPDOWN:
                            self.__dropdown_button_ids.append(btn[1])
                        if btn[2] & BTNS_WHOLEDROPDOWN:
                            self.__wholedropdown_button_ids.append(btn[1])

                    j += 1

            # add buttons
            ok = user32.SendMessageW(self.hwnd, TB_ADDBUTTONS, num_buttons, tb_buttons)

            if self.__h_imagelist_disabled is not None:
                user32.SendMessageW(self.hwnd, TB_SETDISABLEDIMAGELIST, 0, self.__h_imagelist_disabled)

        # remove text from buttons
        if hide_text:
            user32.SendMessageW(self.hwnd, TB_SETMAXTEXTROWS, 0, 0)

#        user32.SendMessageW(self.hwnd, TB_AUTOSIZE, 0, 0)

        rc = RECT()
        user32.GetWindowRect(self.hwnd, byref(rc))
        self.height = rc.bottom - rc.top # - 2

        self.parent_window.register_message_callback(WM_NOTIFY, self.on_WM_NOTIFY)

        # Dark divider border at top
        def _on_WM_NCPAINT(hwnd, wparam, lparam):
            if self.is_dark:
                hdc = user32.GetWindowDC(hwnd)
                rc = self.get_window_rect()
                rc = RECT(0, 0, rc.right - rc.left, 2)
                user32.FillRect(hdc, byref(rc), DARK_BG_BRUSH)
                rc.bottom = 1
                user32.FillRect(hdc, byref(rc), DARK_TOOLBAR_BORDER_BRUSH)
                user32.ReleaseDC(hwnd, hdc)
                return 0

        self.register_message_callback(WM_NCPAINT, _on_WM_NCPAINT)

    def check_button(self, button_id, flag):
        #user32.SendMessageW(self.hwnd, TB_CHECKBUTTON, button_id, flag)
        user32.PostMessageW(self.hwnd, TB_CHECKBUTTON, button_id, flag)

    def update_size(self, *args):
        user32.SendMessageW(self.hwnd, WM_SIZE, 0, 0)

    def set_indent(self, indent):
        user32.SendMessageW(self.hwnd, TB_SETINDENT, indent, 0)

    def set_imagelist(self, h_imagelist):
        user32.SendMessageW(self.hwnd, TB_SETIMAGELIST, 0, h_imagelist)

    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)
        if is_dark:
            if self.__h_bitmap_dark:
                rb = TBREPLACEBITMAP()
                rb.hInstOld = 0
                rb.hInstNew = 0
                rb.nIDOld = self.__h_bitmap
                rb.nIDNew = self.__h_bitmap_dark
                rb.nButtons = self.__num_images
                image_list_id = user32.SendMessageW(self.hwnd, TB_REPLACEBITMAP, 0, byref(rb))
            if self.__h_imagelist_disabled_dark is not None:
                user32.SendMessageW(self.hwnd, TB_SETDISABLEDIMAGELIST, 0, self.__h_imagelist_disabled_dark)
        else:
            if self.__h_bitmap_dark:
                rb = TBREPLACEBITMAP()
                rb.hInstOld = 0
                rb.hInstNew = 0
                rb.nIDOld = self.__h_bitmap_dark
                rb.nIDNew = self.__h_bitmap
                rb.nButtons = self.__num_images
                image_list_id = user32.SendMessageW(self.hwnd, TB_REPLACEBITMAP, 0, byref(rb))
            if self.__h_imagelist_disabled is not None:
                user32.SendMessageW(self.hwnd, TB_SETDISABLEDIMAGELIST, 0, self.__h_imagelist_disabled)

        # update tooltip colors
        hwnd_tooltip = user32.SendMessageW(self.hwnd, TB_GETTOOLTIPS, 0, 0)
        if hwnd_tooltip:
            uxtheme.SetWindowTheme(hwnd_tooltip, 'DarkMode_Explorer' if is_dark else 'Explorer', None)

    def on_WM_NOTIFY(self, hwnd, wparam, lparam):
        nmhdr = cast(lparam, LPNMHDR).contents
        msg = nmhdr.code
        if msg == NM_CUSTOMDRAW and nmhdr.hwndFrom == self.hwnd:

            nmtb = cast(lparam, POINTER(NMTBCUSTOMDRAW)).contents
            nmcd = nmtb.nmcd

            if nmcd.dwDrawStage == CDDS_PREPAINT:
                # toolbar background
                user32.FillRect(nmcd.hdc, byref(nmcd.rc), DARK_BG_BRUSH if self.is_dark else COLOR_3DFACE + 1)  # COLOR_WINDOW

                if self.has_border:
                    rc = self.get_client_rect()
                    if self.is_vertical:
                        rc.left = rc.right - 1
                    else:
                        rc.top = rc.bottom - 1
                    user32.FillRect(nmtb.nmcd.hdc, byref(rc), DARK_TOOLBAR_BORDER_BRUSH if self.is_dark else TOOLBAR_BORDER_BRUSH)
                return CDRF_NOTIFYITEMDRAW if self.is_dark else CDRF_DODEFAULT

            elif nmcd.dwDrawStage == CDDS_ITEMPREPAINT:

                if not self.is_dark:
                    return TBCDRF_NOOFFSET | TBCDRF_NOETCHEDEFFECT
#                    return TBCDRF_BLENDICON if nmcd.uItemState & CDIS_DISABLED else TBCDRF_NOOFFSET | TBCDRF_NOETCHEDEFFECT

                if nmcd.uItemState & CDIS_HOT:
                    ########################################
                    # hot (rollover) button state
                    ########################################
                    gdi32.SelectObject(nmcd.hdc, DARK_TOOLBAR_BUTTON_ROLLOVER_BG_BRUSH)
                    hpen = gdi32.CreatePen(PS_SOLID, 1, DARK_TOOLBAR_BUTTON_ROLLOVER_BORDER_COLOR)
                    gdi32.SelectObject(nmcd.hdc, hpen)
                    if nmcd.lItemlParam in self.__dropdown_button_ids and not nmcd.lItemlParam in self.__wholedropdown_button_ids:
                        gdi32.RoundRect(nmcd.hdc, nmcd.rc.left, nmcd.rc.top, nmcd.rc.right - 15, nmcd.rc.bottom, 6, 6)
                    else:
                        gdi32.RoundRect(nmcd.hdc, nmcd.rc.left, nmcd.rc.top, nmcd.rc.right, nmcd.rc.bottom, 6, 6)
                    gdi32.DeleteObject(hpen)
                    return (TBCDRF_NOBACKGROUND | TBCDRF_NOOFFSET | TBCDRF_NOETCHEDEFFECT | TBCDRF_NOEDGES
                        | (CDRF_NOTIFYPOSTPAINT | TBCDRF_NOMARK if nmcd.lItemlParam in self.__dropdown_button_ids else 0)
                    )

                elif nmcd.uItemState & CDIS_CHECKED:
                    ########################################
                    # checked button state
                    ########################################
                    gdi32.SelectObject(nmcd.hdc, DARK_TOOLBAR_BUTTON_CHECKED_BG_BRUSH)
                    hpen = gdi32.CreatePen(PS_SOLID, 1, DARK_TOOLBAR_BUTTON_CHECKED_BORDER_COLOR)
                    gdi32.SelectObject(nmcd.hdc, hpen)
                    if nmcd.lItemlParam in self.__dropdown_button_ids:
                        gdi32.RoundRect(nmcd.hdc, nmcd.rc.left, nmcd.rc.top, nmcd.rc.right - 15, nmcd.rc.bottom, 6, 6)
                    else:
                        gdi32.RoundRect(nmcd.hdc, nmcd.rc.left, nmcd.rc.top, nmcd.rc.right, nmcd.rc.bottom, 6, 6)
                    gdi32.DeleteObject(hpen)
                    return (TBCDRF_NOBACKGROUND | TBCDRF_NOOFFSET | TBCDRF_NOETCHEDEFFECT | TBCDRF_NOEDGES
                        | (CDRF_NOTIFYPOSTPAINT | TBCDRF_NOMARK  if nmcd.lItemlParam in self.__dropdown_button_ids else 0)
                    )

                elif nmcd.uItemState & CDIS_DISABLED:
                    ########################################
                    # disabled button state
                    ########################################
                    return TBCDRF_BLENDICON

                else:
                    ########################################
                    # default button state
                    ########################################
                    if nmcd.lItemlParam in self.__dropdown_button_ids:
                        return CDRF_NOTIFYPOSTPAINT
                    return CDRF_DODEFAULT

            elif nmcd.dwDrawStage == CDDS_ITEMPOSTPAINT:

                def _draw_arrow(hdc, x, y):
                    hbr = gdi32.GetStockObject(WHITE_BRUSH)
                    user32.FillRect(hdc, byref(RECT(x,     y,      x + 7, y + 1)), hbr)
                    user32.FillRect(hdc, byref(RECT(x + 1, y + 1,  x + 6, y + 2)), hbr)
                    user32.FillRect(hdc, byref(RECT(x + 2, y + 2,  x + 5, y + 3)), hbr)
                    user32.FillRect(hdc, byref(RECT(x + 3, y + 3,  x + 4, y + 4)), hbr)

                if nmcd.lItemlParam in self.__wholedropdown_button_ids:
                    _draw_arrow(nmcd.hdc, nmcd.rc.left + 21, nmcd.rc.top + 9)
                else:
                    if nmcd.uItemState & CDIS_HOT:
                        gdi32.SelectObject(nmcd.hdc, DARK_TOOLBAR_BUTTON_ROLLOVER_BG_BRUSH)
                        hpen = gdi32.CreatePen(PS_SOLID, 1, DARK_TOOLBAR_BUTTON_ROLLOVER_BORDER_COLOR)
                        gdi32.SelectObject(nmcd.hdc, hpen)
                        rc = RECT(nmcd.rc.right - 14, nmcd.rc.top - 4, nmcd.rc.right + 2, nmcd.rc.bottom + 4)
                        user32.FillRect(nmcd.hdc, byref(rc), DARK_BG_BRUSH)
                        gdi32.RoundRect(nmcd.hdc, rc.left, rc.top, rc.right, rc.bottom, 6, 6)
                        gdi32.DeleteObject(hpen)
                    elif nmcd.uItemState & CDIS_CHECKED:
                        gdi32.SelectObject(nmcd.hdc, DARK_TOOLBAR_BUTTON_CHECKED_BG_BRUSH)
                        hpen = gdi32.CreatePen(PS_SOLID, 1, DARK_TOOLBAR_BUTTON_CHECKED_BORDER_COLOR)
                        gdi32.SelectObject(nmcd.hdc, hpen)
                        rc = RECT(nmcd.rc.right - 14, nmcd.rc.top - 4, nmcd.rc.right + 2, nmcd.rc.bottom + 4)
                        user32.FillRect(nmcd.hdc, byref(rc), DARK_BG_BRUSH)
                        gdi32.RoundRect(nmcd.hdc, rc.left, rc.top, rc.right, rc.bottom , 6, 6)
                        gdi32.DeleteObject(hpen)
                    _draw_arrow(nmcd.hdc, nmcd.rc.left + 23, nmcd.rc.top + 5)
                return CDRF_SKIPDEFAULT
