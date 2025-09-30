# https://learn.microsoft.com/en-us/windows/win32/controls/tab-control-reference

from ctypes import *
from ctypes.wintypes import *

from ..const import *  #WS_CHILD, WS_VISIBLE
from ..wintypes_extended import MAKELONG
from ..window import *
from ..themes import *
from ..dlls import gdi32, user32, comctl32
from .common import *
from .tooltips import *

MAX_TAB_TEXT_LEN = 32

########################################
# Class Name
########################################
#TABCONTROL_CLASS = WC_TABCONTROL = "SysTabControl32"

#class TCITEMW(Structure):
#    _fields_ = [
#        ("mask", UINT),
#        ("dwState", DWORD),
#        ("dwStateMask", DWORD),
#        ("pszText", LPWSTR),
#        ("cchTextMax", INT),
#        ("iImage", INT),
#        ("lParam", LPARAM),
#        ]

class TCHITTESTINFO(Structure):
    _pack_ = 4
    _fields_ = [
        ("pt", POINT),
        ("flags", UINT),
        ]

#TCIF_TEXT               =0x0001
#TCIF_IMAGE              =0x0002
#TCIF_RTLREADING         =0x0004
#TCIF_PARAM              =0x0008
#TCIF_STATE              =0x0010
#
#TCIS_BUTTONPRESSED      =0x0001
#TCIS_HIGHLIGHTED        =0x0002

#define TCS_SCROLLOPPOSITE 0x1
#define TCS_BOTTOM 0x2
#define TCS_RIGHT 0x2
#define TCS_MULTISELECT 0x4
#define TCS_FLATBUTTONS 0x8
#define TCS_FORCEICONLEFT 0x10
#define TCS_FORCELABELLEFT 0x20
#define TCS_HOTTRACK 0x40
#define TCS_VERTICAL 0x80
#define TCS_TABS 0x0
#define TCS_BUTTONS 0x100
#define TCS_SINGLELINE 0x0
#define TCS_MULTILINE 0x200
#define TCS_RIGHTJUSTIFY 0x0
#define TCS_FIXEDWIDTH 0x400
#define TCS_RAGGEDRIGHT 0x800
#define TCS_FOCUSONBUTTONDOWN 0x1000
#define TCS_OWNERDRAWFIXED 0x2000
#TCS_TOOLTIPS =0x4000
#define TCS_FOCUSNEVER 0x8000

#define TCS_EX_FLATSEPARATORS 0x1
#define TCS_EX_REGISTERDROP 0x2

#TCM_FIRST               =0x1300
#
##define TCM_GETIMAGELIST        (TCM_FIRST + 2)
##define TCM_SETIMAGELIST        (TCM_FIRST + 3)
#TCM_GETITEMCOUNT	    =(TCM_FIRST + 4)
##define TCM_GETIMAGELIST        (TCM_FIRST + 0x02)
##define TCM_SETIMAGELIST        (TCM_FIRST + 0x03)
#
##TCM_GETITEMA            =(TCM_FIRST + 5)
#TCM_GETITEMW            =(TCM_FIRST + 60)
#
##TCM_SETITEMA            =(TCM_FIRST + 6)
#TCM_SETITEMW            =(TCM_FIRST + 61)
#
##TCM_INSERTITEMA         =(TCM_FIRST + 7)
#TCM_INSERTITEMW         =(TCM_FIRST + 62)
#
#TCM_HITTEST             =(TCM_FIRST + 13)
#TCM_SETITEMEXTRA        =(TCM_FIRST + 14)
#TCM_ADJUSTRECT          =(TCM_FIRST + 40)
#TCM_SETITEMSIZE         =(TCM_FIRST + 41)
#TCM_REMOVEIMAGE         =(TCM_FIRST + 42)
#TCM_SETPADDING          =(TCM_FIRST + 43)
#TCM_GETROWCOUNT         =(TCM_FIRST + 44)
#TCM_GETTOOLTIPS         =(TCM_FIRST + 45)
#TCM_SETTOOLTIPS         =(TCM_FIRST + 46)
#TCM_GETCURFOCUS         =(TCM_FIRST + 47)
#TCM_SETCURFOCUS         =(TCM_FIRST + 48)
#TCM_SETMINTABWIDTH      =(TCM_FIRST + 49)
#TCM_DESELECTALL         =(TCM_FIRST + 50)
#TCM_HIGHLIGHTITEM       =(TCM_FIRST + 51)
#TCM_SETEXTENDEDSTYLE    =(TCM_FIRST + 52)  # optional wParam == mask
#TCM_GETEXTENDEDSTYLE    =(TCM_FIRST + 53)
#TCM_SETUNICODEFORMAT    =CCM_SETUNICODEFORMAT
#TCM_GETUNICODEFORMAT    =CCM_GETUNICODEFORMAT
#TCM_DELETEITEM          =(TCM_FIRST + 8)
#TCM_DELETEALLITEMS      =(TCM_FIRST + 9)
#TCM_GETITEMRECT         =(TCM_FIRST + 10)
#TCM_GETCURSEL           =(TCM_FIRST + 11)
#TCM_SETCURSEL           =(TCM_FIRST + 12)

#TCN_FIRST = -550
#TCN_KEYDOWN             =(TCN_FIRST - 0)
#
##TC_KEYDOWN              NMTCKEYDOWN
#
##typedef struct tagTCKEYDOWN
##{
##    NMHDR hdr;
##    WORD wVKey;
##    UINT flags;
##} NMTCKEYDOWN;
#
#TCN_SELCHANGE           =(TCN_FIRST - 1)
#TCN_SELCHANGING         =(TCN_FIRST - 2)
#TCN_GETOBJECT           =(TCN_FIRST - 3)
#TCN_FOCUSCHANGE         =(TCN_FIRST - 4)


########################################
# Wrapper Class
########################################
class TabControl(Window):

    EVENT_TAB_CLOSE_REQUESTED = 0
    EVENT_TAB_MOVED = 1

    def __init__(
        self,
        parent_window,
        style=WS_CHILD | WS_VISIBLE, ex_style=0,
        left=0, top=0, width=0, height=0,
        window_title=None,
        close_button_imagelist=None,
        tabs_movable=False,
        move_cursor=None,
        hilite_at_bottom=False
    ):

        has_tooltips = style & TCS_TOOLTIPS
        if has_tooltips:
            style & ~TCS_TOOLTIPS

        self.__close_button_hover_index = None
        self.__close_button_imagelist = close_button_imagelist
        self.__close_button_pressed = False
        self.__moved_tab_index = None

        if tabs_movable:
            self.__hcrMove = move_cursor
            self.__hcrMoveInvalid = user32.LoadCursorW(None, IDC_NO)

        super().__init__(
            WC_TABCONTROL,
            parent_window=parent_window,
            style=style,
            ex_style=ex_style,
            left=left,
            top=top,
            width=width,
            height=height,
            window_title=window_title,
        )

        rc = self.get_item_rect(0)
        self.height = rc.bottom + 2 + 1

        if has_tooltips:
            self.tooltips = Tooltips(self)
            user32.SendMessageW(self.hwnd, TCM_SETTOOLTIPS, self.tooltips.hwnd, 0)

        tabs_closable = close_button_imagelist is not None

        def _on_WM_PAINT(hwnd, wparam, lparam):
            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, byref(ps))
            gdi32.SetBkMode(hdc, TRANSPARENT)
            gdi32.SetTextColor(hdc, DARK_TEXT_COLOR if self.is_dark else 0x000000)
            gdi32.SelectObject(hdc, self.hfont)

            # tabbar background
            user32.FillRect(hdc, byref(ps.rcPaint), DARK_BG_BRUSH if self.is_dark else COLOR_3DFACE + 1)

            selected_index = self.get_cur_sel()
            for idx in range(self.get_item_count()):
                rc = self.get_item_rect(idx)
                # tab right  border
                user32.FillRect(hdc, byref(rc), DARK_TAB_BORDER_BRUSH if self.is_dark else LIGHT_TAB_BORDER_BRUSH)

                # tab background
                rc.right -= 1
                if self.is_dark:
                    user32.FillRect(hdc, byref(rc), DARK_TAB_SELECTED_BG_BRUSH if idx == selected_index else DARK_BG_BRUSH)
                else:
                    user32.FillRect(hdc, byref(rc), COLOR_WINDOW + 1 if idx == selected_index else COLOR_3DFACE + 1)
                if idx == selected_index:
                    if hilite_at_bottom:
                        # TODO: why 2 ???
                        user32.FillRect(hdc, byref(RECT(rc.left - (1 if idx else 0), rc.bottom - 3, rc.right + 1, rc.bottom)), TAB_SELECTED_HILITE_BRUSH)
                    else:
                        user32.FillRect(hdc, byref(RECT(rc.left - (1 if idx else 0), rc.top, rc.right + 1, rc.top + 2)), TAB_SELECTED_HILITE_BRUSH)

                # tab text
#                user32.DrawTextW(hdc, self.get_item_text(idx), -1, byref(rc), DT_SINGLELINE | DT_CENTER | DT_VCENTER)
                if hilite_at_bottom:
                    user32.DrawTextW(hdc, self.get_item_text(idx), -1, RECT(rc.left, rc.top, rc.right, rc.bottom - 2), DT_SINGLELINE | DT_CENTER | DT_VCENTER)
                else:
                    user32.DrawTextW(hdc, self.get_item_text(idx), -1, RECT(rc.left, rc.top + 1, rc.right, rc.bottom), DT_SINGLELINE | DT_CENTER | DT_VCENTER)

                # tab close button
                if self.__close_button_imagelist:
    #                if idx == self.__close_button_hover_index:
    #                    user32.FillRect(hdc, byref(RECT(rc.right - 13, rc.top + 3, rc.right - 1, rc.top + 15)), DARK_MENU_BG_BRUSH_HOT)
                    comctl32.ImageList_Draw(self.__close_button_imagelist, 1 if self.is_dark else 0, hdc, rc.right - 15 + 5, 3 + 5, ILD_NORMAL)
                    if idx == self.__close_button_hover_index:
                        user32.InvertRect(hdc, byref(RECT(rc.right - 13, rc.top + 3, rc.right - 1, rc.top + 15)))
            user32.EndPaint(hwnd, byref(ps))
            return FALSE

        self.register_message_callback(WM_PAINT, _on_WM_PAINT)

        if tabs_closable:

            def _on_WM_MOUSELEAVE(hwnd, wparam, lparam):
                if self.__close_button_hover_index is not None:
                    rc = self.get_item_rect(self.__close_button_hover_index)
                    self.__close_button_hover_index = None
                    user32.InvalidateRect(self.hwnd, byref(rc), TRUE)

            self.register_message_callback(WM_MOUSELEAVE, _on_WM_MOUSELEAVE)

        if tabs_closable or tabs_movable:

            # tab reordering via mouse
            def _on_WM_MOUSEMOVE(hwnd, wparam, lparam):

                x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
                pt = POINT(x, y)
                idx = user32.SendMessageW(self.hwnd, TCM_HITTEST, 0, byref(TCHITTESTINFO(pt, 0)))

                if self.__moved_tab_index is not None:
                    user32.SetCursor(self.__hcrMove if idx >= 0 else self.__hcrMoveInvalid)

                if idx < 0:
                    return

                if tabs_closable and self.__moved_tab_index is None:
                    rc = self.get_item_rect(idx)
                    if x >= rc.right - 16:
                        if idx != self.__close_button_hover_index:
                            self.__close_button_hover_index = idx
                            user32.InvalidateRect(self.hwnd, byref(rc), TRUE)
                    elif self.__close_button_hover_index is not None:
                        rc = self.get_item_rect(self.__close_button_hover_index)
                        self.__close_button_hover_index = None
                        user32.InvalidateRect(self.hwnd, byref(rc), TRUE)



#                if self.__moved_tab_index is not None and idx != self.__moved_tab_index:
#                    tie = TCITEMW()
#
#                    tie.mask = TCIF_TEXT | TCIF_PARAM
#                    tie.pszText = cast(create_unicode_buffer(MAX_TAB_TEXT_LEN + 1), LPWSTR)
#                    tie.cchTextMax = MAX_TAB_TEXT_LEN
#
#                    user32.SendMessageW(self.hwnd, TCM_GETITEMW, self.__moved_tab_index, byref(tie))
#                    user32.SendMessageW(self.hwnd, TCM_DELETEITEM, self.__moved_tab_index, 0)
#
#                    self.insert_item(idx, tie)
#                    self.emit(TabControl.EVENT_TAB_MOVED, idx, self.__moved_tab_index)  # new_index, old_index
#                    self.__moved_tab_index = idx



            self.register_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)

            def _on_WM_LBUTTONDOWN(hwnd, wparam, lparam):
                x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
                pt = POINT(x, y)
                idx = user32.SendMessageW(self.hwnd, TCM_HITTEST, 0, byref(TCHITTESTINFO(pt, 0)))
                if idx < 0:
                    return
                if tabs_closable:
                    rc = RECT()
                    user32.SendMessageW(self.hwnd, TCM_GETITEMRECT, idx, byref(rc))
                    if rc.right - pt.x <= 16:
                        self.__close_button_pressed = True
                        self.__moved_tab_index = None
                        return TRUE
                if tabs_movable:
                    self.__moved_tab_index = idx
                    user32.SetCapture(hwnd)

            self.register_message_callback(WM_LBUTTONDOWN, _on_WM_LBUTTONDOWN)

            def _on_WM_LBUTTONUP(hwnd, wparam, lparam):

                if tabs_closable and self.__close_button_pressed:
                    self.__close_button_pressed = False
                    x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
                    pt = POINT(x, y)
                    idx = user32.SendMessageW(self.hwnd, TCM_HITTEST, 0, byref(TCHITTESTINFO(pt, 0)))
                    if idx < 0:
                        return
                    rc = RECT()
                    user32.SendMessageW(self.hwnd, TCM_GETITEMRECT, idx, byref(rc))
                    if rc.right - pt.x <= 16:
                        self.emit(TabControl.EVENT_TAB_CLOSE_REQUESTED, idx)

                elif tabs_movable and self.__moved_tab_index is not None:  #user32.GetCapture():
                    user32.SetCursor(None)
                    user32.ReleaseCapture()

                    x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
                    pt = POINT(x, y)
                    idx = user32.SendMessageW(self.hwnd, TCM_HITTEST, 0, byref(TCHITTESTINFO(pt, 0)))

                    if idx >= 0 and idx != self.__moved_tab_index:
                        tie = TCITEMW()
                        tie.mask = TCIF_TEXT | TCIF_PARAM
                        tie.pszText = cast(create_unicode_buffer(MAX_TAB_TEXT_LEN + 1), LPWSTR)
                        tie.cchTextMax = MAX_TAB_TEXT_LEN
                        user32.SendMessageW(self.hwnd, TCM_GETITEMW, self.__moved_tab_index, byref(tie))
                        user32.SendMessageW(self.hwnd, TCM_DELETEITEM, self.__moved_tab_index, 0)
                        self.insert_item(idx, tie)
                        self.emit(TabControl.EVENT_TAB_MOVED, idx, self.__moved_tab_index)  # new_index, old_index
                    self.__moved_tab_index = None

            self.register_message_callback(WM_LBUTTONUP, _on_WM_LBUTTONUP)

        if parent_window.is_dark:
            self.apply_theme(True)

    ########################################
    #
    ########################################
    def _on_WM_SIZE(self, hwnd, wparam, lparam):
        hwnd_updown = user32.FindWindowExW(self.hwnd, NULL, 'msctls_updown32', '')
        if hwnd_updown:
            uxtheme.SetWindowTheme(hwnd_updown, 'DarkMode_Explorer', None)

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)
        hwnd_updown = user32.FindWindowExW(self.hwnd, NULL, 'msctls_updown32', '')
        if hwnd_updown:
            uxtheme.SetWindowTheme(hwnd_updown, 'DarkMode_Explorer' if is_dark else 'Explorer', None)
        if is_dark:
            self.register_message_callback(WM_SIZE, self._on_WM_SIZE)
        else:
            self.unregister_message_callback(WM_SIZE, self._on_WM_SIZE)

    ########################################
    # custom
    ########################################
    def find_item_by_data(self, data):
        cnt = user32.SendMessageW(self.hwnd, TCM_GETITEMCOUNT, 0, 0)
        tc_item = TCITEMW()
        tc_item.mask = TCIF_PARAM
        for iItem in range(cnt):
            user32.SendMessageW(self.hwnd, TCM_GETITEMW, iItem, byref(tc_item))
            if tc_item.lParam == data:
                return iItem

    #define TabCtrl_GetItem(hwnd, iItem, pitem) \
    #    (BOOL)SNDMSG((hwnd), TCM_GETITEM, (WPARAM)(int)(iItem), (LPARAM)(TC_ITEM *)(pitem))
    def get_item(self, iItem, mask):
        tc_item = TCITEMW()
        tc_item.mask = mask
        user32.SendMessageW(self.hwnd, TCM_GETITEMW, iItem, byref(tc_item))
        return tc_item

    #define TabCtrl_SetItem(hwnd, iItem, pitem) \
    #    (BOOL)SNDMSG((hwnd), TCM_SETITEM, (WPARAM)(int)(iItem), (LPARAM)(TC_ITEM *)(pitem))
    def set_item(self, iItem, tc_item):
        return user32.SendMessageW(self.hwnd, TCM_SETITEMW, iItem, byref(tc_item))  # (TC_ITEM *)

    def get_item_text(self, iItem, text_max=64):
        buf = create_unicode_buffer(text_max)
        tc_item = TCITEMW()
        tc_item.mask = TCIF_TEXT
        # If item information is being retrieved, this member specifies the address of the buffer that receives the tab text.
        tc_item.pszText = cast(buf, LPWSTR)
        tc_item.cchTextMax = text_max
        ok = user32.SendMessageW(self.hwnd, TCM_GETITEMW, iItem, byref(tc_item))
        return buf.value

    def set_item_text(self, iItem, text):
        tc_item = TCITEMW()
        tc_item.mask = TCIF_TEXT
        # If item information is being retrieved, this member specifies the address of the buffer that receives the tab text.
        tc_item.pszText = cast(create_unicode_buffer(text), LPWSTR)
        tc_item.cchTextMax = len(text)
        return user32.SendMessageW(self.hwnd, TCM_SETITEMW, iItem, byref(tc_item))  # (TC_ITEM *)

    def get_item_data(self, iItem):
        tc_item = TCITEMW()
        tc_item.mask = TCIF_PARAM
        user32.SendMessageW(self.hwnd, TCM_GETITEMW, iItem, byref(tc_item))
        return tc_item.lParam

    #define TabCtrl_InsertItem(hwnd, iItem, pitem)   \
    #    (int)SNDMSG((hwnd), TCM_INSERTITEM, (WPARAM)(int)(iItem), (LPARAM)(const TC_ITEM *)(pitem))
    def insert_item(self, iItem, tc_item):
        user32.SendMessageW(self.hwnd, TCM_INSERTITEMW, iItem, byref(tc_item))
        if self.is_dark:
            hwnd_updown = user32.FindWindowExW(self.hwnd, NULL, 'msctls_updown32', '')
            if hwnd_updown:
                uxtheme.SetWindowTheme(hwnd_updown, 'DarkMode_Explorer', None)

    #define TabCtrl_DeleteItem(hwnd, i) \
    #    (BOOL)SNDMSG((hwnd), TCM_DELETEITEM, (WPARAM)(int)(i), 0L)
    def delete_item(self, i):
        return user32.SendMessageW(self.hwnd, TCM_DELETEITEM, i, 0)

    #define TabCtrl_DeleteAllItems(hwnd) \
    #    (BOOL)SNDMSG((hwnd), TCM_DELETEALLITEMS, 0, 0L)
    def delete_all_items(self):
        return user32.SendMessageW(self.hwnd, TCM_DELETEALLITEMS, 0, 0)

    #define TabCtrl_GetItemRect(hwnd, i, prc) \
    #    (BOOL)SNDMSG((hwnd), TCM_GETITEMRECT, (WPARAM)(int)(i), (LPARAM)(RECT *)(prc))
    def get_item_rect(self, i):
        rc = RECT()
        user32.SendMessageW(self.hwnd, TCM_GETITEMRECT, i, byref(rc))
        return rc

    #define TabCtrl_GetCurSel(hwnd) \
    #    (int)SNDMSG((hwnd), TCM_GETCURSEL, 0, 0)
    def get_cur_sel(self):
        return user32.SendMessageW(self.hwnd, TCM_GETCURSEL, 0, 0)

    #define TabCtrl_SetCurSel(hwnd, i) \
    #    (int)SNDMSG((hwnd), TCM_SETCURSEL, (WPARAM)(i), 0)
    def set_cur_sel(self, i):
        return user32.SendMessageW(self.hwnd, TCM_SETCURSEL, i, 0)

    #define TabCtrl_HitTest(hwndTC, pinfo) \
    #    (int)SNDMSG((hwndTC), TCM_HITTEST, 0, (LPARAM)(TC_HITTESTINFO *)(pinfo))
    def hit_test(self, hti):
        return user32.SendMessageW(self.hwnd, TCM_HITTEST, 0, byref(hti))

    #define TabCtrl_SetItemExtra(hwndTC, cb) \
    #    (BOOL)SNDMSG((hwndTC), TCM_SETITEMEXTRA, (WPARAM)(cb), 0L)
#    def set_item_extra(hwndTC, cb):
#        return user32.SendMessageW((hwndTC), TCM_SETITEMEXTRA, cb, 0)

    #define TabCtrl_AdjustRect(hwnd, bLarger, prc) \
    #    (int)SNDMSG(hwnd, TCM_ADJUSTRECT, (WPARAM)(BOOL)(bLarger), (LPARAM)(RECT *)(prc))
    def adjust_rect(self, bLarger, rc):
        return user32.SendMessageW(self.hwnd, TCM_ADJUSTRECT, bLarger, byref(rc))  # (RECT *)

    #define TabCtrl_SetItemSize(hwnd, x, y) \
    #    (DWORD)SNDMSG((hwnd), TCM_SETITEMSIZE, 0, MAKELPARAM(x,y))
    def set_item_size(self, x, y):
        return user32.SendMessageW(self.hwnd, TCM_SETITEMSIZE, 0, MAKELPARAM(x,y))

    #define TabCtrl_RemoveImage(hwnd, i) \
    #        (void)SNDMSG((hwnd), TCM_REMOVEIMAGE, i, 0L)
    def remove_image(self, i):
        return user32.SendMessageW(self.hwnd, TCM_REMOVEIMAGE, i, 0)

    #define TabCtrl_SetPadding(hwnd,  cx, cy) \
    #        (void)SNDMSG((hwnd), TCM_SETPADDING, 0, MAKELPARAM(cx, cy))
    def set_padding(self,  cx, cy):
        return user32.SendMessageW(self.hwnd, TCM_SETPADDING, 0, MAKELPARAM(cx, cy))

    #define TabCtrl_GetItemCount(hwnd) \
    #    (int)SNDMSG((hwnd), TCM_GETITEMCOUNT, 0, 0)
    def get_item_count(self):
        return user32.SendMessageW(self.hwnd, TCM_GETITEMCOUNT, 0, 0)

    #define TabCtrl_GetRowCount(hwnd) \
    #        (int)SNDMSG((hwnd), TCM_GETROWCOUNT, 0, 0L)
    def get_row_count(self):
        return user32.SendMessageW(self.hwnd, TCM_GETROWCOUNT, 0, 0)

    #define TabCtrl_GetToolTips(hwnd) \
    #        (HWND)SNDMSG((hwnd), TCM_GETTOOLTIPS, 0, 0L)
    def get_tool_tips(self):
        return user32.SendMessageW(self.hwnd, TCM_GETTOOLTIPS, 0, 0)

    #define TabCtrl_SetToolTips(hwnd, hwndTT) \
    #        (void)SNDMSG((hwnd), TCM_SETTOOLTIPS, (WPARAM)(hwndTT), 0L)
    def set_tool_tips(self, hwndTT):
        return user32.SendMessageW(self.hwnd, TCM_SETTOOLTIPS, hwndTT, 0)

    ##define TabCtrl_GetCurFocus(hwnd) \
    #    (int)SNDMSG((hwnd), TCM_GETCURFOCUS, 0, 0)
    def get_cur_focus(self):
        return user32.SendMessageW(self.hwnd, TCM_GETCURFOCUS, 0, 0)

    #define TabCtrl_SetCurFocus(hwnd, i) \
    #    SNDMSG((hwnd),TCM_SETCURFOCUS, i, 0)
    def set_cur_focus(self, i):
        user32.SendMessageW(self.hwnd,TCM_SETCURFOCUS, i, 0)

    #define TabCtrl_SetMinTabWidth(hwnd, x) \
    #        (int)SNDMSG((hwnd), TCM_SETMINTABWIDTH, 0, x)
    def set_min_tab_width(self, x):
        return user32.SendMessageW(self.hwnd, TCM_SETMINTABWIDTH, 0, x)

    #define TabCtrl_DeselectAll(hwnd, fExcludeFocus)\
    #        (void)SNDMSG((hwnd), TCM_DESELECTALL, fExcludeFocus, 0)
    def deselect_all(self, fExcludeFocus):
        user32.SendMessageW(self.hwnd, TCM_DESELECTALL, fExcludeFocus, 0)

    #define TabCtrl_HighlightItem(hwnd, i, fHighlight) \
    #    (BOOL)SNDMSG((hwnd), TCM_HIGHLIGHTITEM, (WPARAM)(i), (LPARAM)MAKELONG (fHighlight, 0))
    def highlight_item(self, i, fHighlight):
        return user32.SendMessageW(self.hwnd, TCM_HIGHLIGHTITEM, i, MAKELONG(fHighlight, 0))

    #define TabCtrl_SetExtendedStyle(hwnd, dw)\
    #        (DWORD)SNDMSG((hwnd), TCM_SETEXTENDEDSTYLE, 0, dw)
    def set_extended_style(self, dw):
        return user32.SendMessageW(self.hwnd, TCM_SETEXTENDEDSTYLE, 0, dw)

    #define TabCtrl_GetExtendedStyle(hwnd)\
    #        (DWORD)SNDMSG((hwnd), TCM_GETEXTENDEDSTYLE, 0, 0)
    def get_extended_style(self):
        return user32.SendMessageW(self.hwnd, TCM_GETEXTENDEDSTYLE, 0, 0)

    #define TabCtrl_SetUnicodeFormat(hwnd, fUnicode)  \
    #    (BOOL)SNDMSG((hwnd), TCM_SETUNICODEFORMAT, (WPARAM)(fUnicode), 0)
    def set_unicode_format(self, fUnicode):
        return user32.SendMessageW(self.hwnd, TCM_SETUNICODEFORMAT, fUnicode, 0)

    #define TabCtrl_GetUnicodeFormat(hwnd)  \
    #    (BOOL)SNDMSG((hwnd), TCM_GETUNICODEFORMAT, 0, 0)
    def get_unicode_format(self) :
        return user32.SendMessageW(self.hwnd, TCM_GETUNICODEFORMAT, 0, 0)
