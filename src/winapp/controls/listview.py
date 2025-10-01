# https://learn.microsoft.com/en-us/windows/win32/controls/list-view-control-reference

from ctypes import *
from ctypes.wintypes import *

from ..const import *
from ..window import *

from ..dlls import comctl32, user32, uxtheme
from ..themes import *
from .common import *

########################################
# Structs
########################################

class ROW(Structure):
    _fields_ = [
        ("a",          UINT),
        ("b",          UINT),
        ("c",          UINT),
        ("d",          UINT),
        ("e",          UINT),
    ]

class NMLVDISPINFO(Structure):
    _fields_ = [
        ("hdr",          NMHDR),
        ("item",         LVITEMW),
    ]

class NMITEMACTIVATE(Structure):
    _fields_ = [
        ("hdr",        NMHDR),
        ("iItem",      INT),
        ("iSubItem",   INT),
        ("uNewState",  UINT),
        ("uOldState",  UINT),
        ("uChanged",   UINT),
        ("ptAction",   POINT),
        ("lParam",     LPARAM),
        ("uKeyFlags",  UINT),
    ]

class LVHITTESTINFO(Structure):
    _fields_ = [
        ("pt",          POINT),
        ("flags",       UINT),
        ("iItem",       INT),
        ("iSubItem",    INT),
        ("iGroup",      INT),
    ]

class LVFINDINFOW(Structure):
    _fields_ = [
        ("flags",       UINT),
        ("psz",         LPCWSTR),
        ("lParam",      LPARAM),
        ("pt",          POINT),
        ("vkDirection", UINT),
    ]

class NMLVCUSTOMDRAW(Structure):
    _fields_ = [
        ("nmcd", NMCUSTOMDRAW),
        ("clrText", COLORREF),
        ("clrTextBk", COLORREF),
        ("iSubItem", INT),
        ("dwItemType", DWORD),
        ("clrFace", COLORREF),
        ("iIconEffect", INT),
        ("iIconPhase", INT),
        ("iPartId", INT),
        ("iStateId", INT),
        ("rcText", RECT),
        ("uAlign", UINT),
    ]


########################################
# Wrapper Class
########################################
class ListView(Window):

    def __init__(
        self, parent_window=None, style=WS_CHILD | WS_VISIBLE, ex_style=0,
        left=0, top=0, width=0, height=0, window_title=None
    ):

        super().__init__(
            WC_LISTVIEW,
            parent_window=parent_window,
            style=style,
            ex_style=ex_style,
            left=left,
            top=top,
            width=width,
            height=height,
            window_title=window_title,
        )

    def set_image_list(self, h_imagelist, list_type=LVSIL_NORMAL):
        user32.SendMessageW.argtypes = [HWND, UINT, WPARAM, HANDLE]
        return user32.SendMessageW(self.hwnd, LVM_SETIMAGELIST, list_type, h_imagelist)

    def insert_item(self, lvi):
        return user32.SendMessageW(self.hwnd, LVM_INSERTITEMW, 0, byref(lvi))

    def insert_column(self, nCol: int, lpszColumnHeading: str, nFormat: int = LVCFMT_LEFT,
            nWidth: int = -1, nSubItem: int = -1, iImage: int = -1, iOrder: int = -1) -> int:
        column = LVCOLUMNW()
        column.mask = LVCF_TEXT | LVCF_FMT
        column.pszText = lpszColumnHeading
        column.fmt = nFormat
        if nWidth != -1:
            column.mask |= LVCF_WIDTH
            column.cx = nWidth
        if nSubItem != -1:
            column.mask |= LVCF_SUBITEM
            column.iSubItem = nSubItem
        if iImage != -1:
            column.mask |= LVCF_IMAGE
            column.iImage = iImage
        if iOrder != -1:
            column.mask |= LVCF_ORDER
            column.iOrder = iOrder
        return user32.SendMessageW(self.hwnd, LVM_INSERTCOLUMNW, nCol, byref(column))

    def sort_items(self, pfnCompare, lParamSort):
        return user32.SendMessageW(self.hwnd, LVM_SORTITEMS, lParamSort, pfnCompare)

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)

        hwnd_header = self.send_message(LVM_GETHEADER, 0, 0)
        if hwnd_header:
            uxtheme.SetWindowTheme(hwnd_header, 'ItemsView', None)
            user32.SendMessageW(hwnd_header, WM_CHANGEUISTATE, MAKELONG(UIS_SET, UISF_HIDEFOCUS), 0)

            HDS_FLAT = 0x0200
            HDS_OVERFLOW = 0x1000
            user32.SetWindowLongA(hwnd_header, GWL_STYLE, user32.GetWindowLongA(hwnd_header, GWL_STYLE) | HDS_FLAT)

            if is_dark:
                self.register_message_callback(WM_NOTIFY, self.on_WM_NOTIFY)
            else:
                self.unregister_message_callback(WM_NOTIFY, self.on_WM_NOTIFY)

        if is_dark:
            user32.SendMessageW(self.hwnd, LVM_SETTEXTCOLOR,   0, DARK_TEXT_COLOR)
            user32.SendMessageW(self.hwnd, LVM_SETTEXTBKCOLOR, 0, DARK_CONTROL_BG_COLOR)
            user32.SendMessageW(self.hwnd, LVM_SETBKCOLOR,     0, DARK_CONTROL_BG_COLOR)
        else:
            user32.SendMessageW(self.hwnd, LVM_SETTEXTCOLOR,   0, 0x000000)
            user32.SendMessageW(self.hwnd, LVM_SETTEXTBKCOLOR, 0, 0xffffff)
            user32.SendMessageW(self.hwnd, LVM_SETBKCOLOR,     0, 0xffffff)

    ########################################
    #
    ########################################
    def on_WM_NOTIFY(self, hwnd, wparam, lparam):
        nmhdr = cast(lparam, LPNMHDR).contents
        msg = nmhdr.code
        if msg == NM_CUSTOMDRAW:
            nmcd = cast(lparam, LPNMCUSTOMDRAW).contents

            if nmcd.dwDrawStage == CDDS_PREPAINT:
                return CDRF_NOTIFYITEMDRAW

            elif nmcd.dwDrawStage == CDDS_ITEMPREPAINT:
                if nmcd.uItemState & CDIS_SELECTED:
                    gdi32.SetBkColor(nmcd.hdc, DARK_CONTROL_BG_COLOR)
                    user32.FillRect(nmcd.hdc, byref(nmcd.rc), DARK_CONTROL_BG_BRUSH)
                    d = 1
                else:
                    gdi32.SetBkColor(nmcd.hdc, DARK_BG_COLOR)
                    user32.FillRect(nmcd.hdc, byref(nmcd.rc), DARK_BG_BRUSH)
                    d = 0

                user32.FillRect(nmcd.hdc, byref(RECT(nmcd.rc.right - 2, nmcd.rc.top, nmcd.rc.right - 1, nmcd.rc.bottom)), DARK_SEPARATOR_BRUSH)

                buf = create_unicode_buffer(32)
                lvc = LVCOLUMNW()
                lvc.mask = LVCF_TEXT
                lvc.cchTextMax = 32
                lvc.pszText = cast(buf, LPWSTR)
                self.send_message(LVM_GETCOLUMNW, nmcd.dwItemSpec, byref(lvc))
                gdi32.SetTextColor(nmcd.hdc, DARK_TEXT_COLOR)
                user32.DrawTextW(nmcd.hdc, buf.value, -1, RECT(nmcd.rc.left + 6 + d, nmcd.rc.top + d, nmcd.rc.right, nmcd.rc.bottom), DT_SINGLELINE | DT_LEFT | DT_VCENTER)

            return CDRF_SKIPDEFAULT
