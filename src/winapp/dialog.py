from ctypes import (Structure, create_unicode_buffer, c_voidp, windll, cast, byref, sizeof,
        c_wchar_p, c_ubyte, POINTER, pointer)
from ctypes.wintypes import (SHORT, WORD, DWORD, HWND, HINSTANCE, LPWSTR, LPCWSTR, LPVOID,
        HANDLE, INT, WCHAR, BYTE, COLORREF, HDC, UINT, WPARAM, LPARAM, LONG, HGLOBAL)

from .wintypes_extended import WINFUNCTYPE, UINT_PTR, SUBCLASSPROC
from .dlls import comdlg32, comctl32, gdi32
from .const import *

from .window import *
from .themes import *

#from .controls.button import *
#from .controls.edit import *
#from .controls.static import *

from .controls.common import COMBOBOXINFO, LVCOLUMNW, TCITEMW
#from .controls.combobox import COMBOBOXINFO
#from .controls.listview import LVCOLUMNW
#from .controls.tabcontrol import TCITEMW


#DIALOG_CLASS = '#32770'

#DIALOG_DEFAULT = 0
#DIALOG_MSGBOX = 1           # MessageBox (used as default)
#DIALOG_CUSTOM_PROC = 2      # Dialog with custom dialog proc
#DIALOG_FILE = 3             # Open/Save file dialog

CHECKBOX_SUBCLASS_ID = 0
DIALOG_SUBCLASS_ID = 0
MSGBOX_SUBCLASS_ID = 0

MSGBOX_BOTTOM_HEIGHT = 42
MAX_SEARCH_REPLACE_LEN = MAX_PATH

BUTTON_COMMAND_IDS = {
    MB_OK: (IDOK,),
    MB_OKCANCEL: (IDOK, IDCANCEL),
    MB_ABORTRETRYIGNORE: (IDABORT, IDRETRY, IDIGNORE),
    MB_YESNOCANCEL: (IDYES, IDNO, IDCANCEL),
    MB_YESNO: (IDYES, IDNO),
    MB_RETRYCANCEL: (IDRETRY, IDCANCEL)
}

#class SHSTOCKICONINFO(Structure):
#    def __init__(self, *args, **kwargs):
#        super(SHSTOCKICONINFO, self).__init__(*args, **kwargs)
#        self.cbSize = sizeof(self)
#    _fields_ = (
#        ('cbSize', DWORD),
#        ('hIcon', HANDLE),
#        ('iSysImageIndex', INT),
#        ('iIcon', INT),
#        ('szPath', WCHAR * MAX_PATH),
#    )

LPHOOKPROC = WINFUNCTYPE(UINT_PTR, HWND, UINT, WPARAM, LPARAM)

########################################
# Open/Save Filename
########################################

#OFNHOOKPROC = WINFUNCTYPE(UINT_PTR, HWND, UINT, WPARAM, LPARAM)
#LPOFNHOOKPROC = OFNHOOKPROC #POINTER(OFNHOOKPROC) #c_voidp # TODO

class OPENFILENAMEW(Structure):
    _fields_ = (
        ('lStructSize', DWORD),
        ('hwndOwner', HWND),
        ('hInstance', HINSTANCE),
        ('lpstrFilter', LPWSTR),
        ('lpstrCustomFilter', LPWSTR),
        ('nMaxCustFilter', DWORD),
        ('nFilterIndex', DWORD),
        ('lpstrFile', LPWSTR),
        ('nMaxFile', DWORD),
        ('lpstrFileTitle', LPWSTR),
        ('nMaxFileTitle', DWORD),
        ('lpstrInitialDir', LPCWSTR),
        ('lpstrTitle', LPCWSTR),
        ('Flags', DWORD),
        ('nFileOffset', WORD),
        ('nFileExtension', WORD),
        ('lpstrDefExt', LPCWSTR),
        ('lCustData', LPARAM),
        ('lpfnHook', LPHOOKPROC),
        ('lpTemplateName', LPCWSTR),
        ('pvReserved', LPVOID),
        ('dwReserved', DWORD),
        ('FlagsEx', DWORD),
    )

class OFNOTIFYW(Structure):
    _fields_ = (
        ('hdr', NMHDR),
        ('lpOFN', POINTER(OPENFILENAMEW)),
        ('pszFile', LPWSTR),
    )

########################################
# ChooseFont
########################################

class LOGFONTW(Structure):
    def __str__(self):
        return  "('%s' %d)" % (self.lfFaceName, self.lfHeight)
#    def __repr__(self):
#        return "<LOGFONTW '%s' %d>" % (self.lfFaceName, self.lfHeight)
    _fields_ = [
        # C:/PROGRA~1/MIAF9D~1/VC98/Include/wingdi.h 1090
        ('lfHeight', LONG),
        ('lfWidth', LONG),
        ('lfEscapement', LONG),
        ('lfOrientation', LONG),
        ('lfWeight', LONG),
        ('lfItalic', BYTE),
        ('lfUnderline', BYTE),
        ('lfStrikeOut', BYTE),
        ('lfCharSet', BYTE),
        ('lfOutPrecision', BYTE),
        ('lfClipPrecision', BYTE),
        ('lfQuality', BYTE),
        ('lfPitchAndFamily', BYTE),
        ('lfFaceName', WCHAR * LF_FACESIZE),
    ]

class CHOOSEFONTW(Structure):
    def __init__(self, *args, **kwargs):
        super(CHOOSEFONTW, self).__init__(*args, **kwargs)
        self.lStructSize = sizeof(self)
    _fields_ = [
        ('lStructSize',                 DWORD),
        ('hwndOwner',                   HWND),
        ('hDC',                         HDC),
        ('lpLogFont',                   POINTER(LOGFONTW)),
        ('iPointSize',                  INT),
        ('Flags',                       DWORD),
        ('rgbColors',                   COLORREF),
        ('lCustData',                   LPARAM),
        ('lpfnHook',                    LPHOOKPROC),
        ('lpTemplateName',              LPCWSTR),
        ('hInstance',                   HINSTANCE),
        ('lpszStyle',                   LPWSTR),
        ('nFontType',                   WORD),
        ('___MISSING_ALIGNMENT__',      WORD),
        ('nSizeMin',                    INT),
        ('nSizeMax',                    INT),
    ]

########################################
# Print
########################################

class PRINTDLGW(Structure):
    def __init__(self, *args, **kwargs):
        super(PRINTDLGW, self).__init__(*args, **kwargs)
        self.lStructSize = sizeof(self)
    _fields_ = [
        ('lStructSize',                 DWORD),
        ('hwndOwner',                   HWND),
        ('hDevMode',                    HGLOBAL),
        ('hDevNames',                   HGLOBAL),
        ('hDC',                         HDC),
        ('Flags',                       DWORD),
        ('nFromPage',                   WORD),
        ('nToPage',                     WORD),
        ('nMinPage',                    WORD),
        ('nMaxPage',                    WORD),
        ('nCopies',                     WORD),
        ('hInstance',                   HINSTANCE),
        ('lCustData',                   LPARAM),
        ('lpfnPrintHook',               LPHOOKPROC),  # LPPRINTHOOKPROC
        ('lpfnSetupHook',               LPVOID),  # LPSETUPHOOKPROC
        ('lpPrintTemplateName',         LPCWSTR),
        ('lpSetupTemplateName',         LPCWSTR),
        ('hPrintTemplate',              HGLOBAL),
        ('hSetupTemplate',              HGLOBAL),
    ]

LPPRINTDLGW = POINTER(PRINTDLGW)

#PD_ALLPAGES = 0
#PD_RETURNDC = 0x00000100
#PD_RETURNDEFAULT = 0x00000400

comdlg32.PrintDlgW.argtypes = (LPPRINTDLGW,)

class DOCINFOW(Structure):
    def __init__(self, *args, **kwargs):
        super(DOCINFOW, self).__init__(*args, **kwargs)
        self.cbSize = sizeof(self)
    _fields_ = [
        ('cbSize', INT),
        ('lpszDocName', LPCWSTR),
        ('lpszOutput', LPCWSTR),
        ('lpszDatatype', LPCWSTR),
        ('fwType', DWORD),
    ]

gdi32.StartDocW.argtypes = (HDC, POINTER(DOCINFOW))

gdi32.EndDoc.argtypes = (HDC,)
gdi32.AbortDoc.argtypes = (HDC,)

gdi32.StartPage.argtypes = (HDC,)
gdi32.EndPage.argtypes = (HDC,)

########################################
# PageSetup
########################################

class PAGESETUPDLGW(Structure):
    def __init__(self, *args, **kwargs):
        super(PAGESETUPDLGW, self).__init__(*args, **kwargs)
        self.lStructSize = sizeof(self)
    _fields_ = [
        ('lStructSize',                 DWORD),
        ('hwndOwner',                   HWND),
        ('hDevMode',                    HGLOBAL),
        ('hDevNames',                   HGLOBAL),
        ('Flags',                       DWORD),
        ('ptPaperSize',                 POINT),
        ('rtMinMargin',                 RECT),
        ('rtMargin',                    RECT),
        ('hInstance',                   HINSTANCE),
        ('lCustData',                   LPARAM),
        ('lpfnPageSetupHook',           LPHOOKPROC),  # LPPAGESETUPHOOK
        ('lpfnPagePaintHook',           LPVOID),  # LPPAGEPAINTHOOK
        ('lpPageSetupTemplateName',     LPCWSTR),
        ('hPageSetupTemplate',          HGLOBAL),
    ]

LPPAGESETUPDLGW = POINTER(PAGESETUPDLGW)

comdlg32.PageSetupDlgW.argtypes = (LPPAGESETUPDLGW,)

########################################
# ChooseColor
########################################

#LPCCHOOKPROC = WINFUNCTYPE(UINT_PTR, HWND, UINT, WPARAM, LPARAM)

class CHOOSECOLORW(Structure):
    def __init__(self, *args, **kwargs):
        super(CHOOSECOLORW, self).__init__(*args, **kwargs)
        self.lStructSize = sizeof(self)
    _fields_ = [
        ("lStructSize",                 DWORD),
        ("hwndOwner",                   HWND),
        ("hInstance",                   HWND),
        ("rgbResult",                   COLORREF),
        ("lpCustColors",                POINTER(COLORREF)),
        ("Flags",                       DWORD),
        ("lCustData",                   LPARAM),
        ("lpfnHook",                    LPHOOKPROC),  # LPCCHOOKPROC
        ("lpTemplateName",              LPCWSTR),
#        ("lpEditInfo",                  LPVOID),  # LPEDITMENU
    ]

LPCHOOSECOLORW = POINTER(CHOOSECOLORW)

comdlg32.ChooseColorW.argtypes = (LPCHOOSECOLORW,)

CC_SOLIDCOLOR = 0x80
CC_FULLOPEN = 0x02
CC_RGBINIT = 0x01


########################################
# Find/Replace
########################################

#LPFRHOOKPROC = WINFUNCTYPE(UINT_PTR, HWND, UINT, WPARAM, LPARAM)

class FINDREPLACEW(Structure):
    def __init__(self, *args, **kwargs):
        super(FINDREPLACEW, self).__init__(*args, **kwargs)
        self.lStructSize = sizeof(self)
    _fields_ = [
        ('lStructSize',                 DWORD),
        ('hwndOwner',                   HWND),
        ('hInstance',                   HINSTANCE),
        ('Flags',                       DWORD),
        ('lpstrFindWhat',               LPWSTR),
        ('lpstrReplaceWith',            LPWSTR),
        ('wFindWhatLen',                WORD),
        ('wReplaceWithLen',             WORD),
        ('lCustData',                   LPARAM),
        ('lpfnHook',                    LPHOOKPROC), # LPFRHOOKPROC
        ('lpTemplateName',              LPCWSTR),
    ]

comdlg32.FindTextW.argtypes = (POINTER(FINDREPLACEW),)
comdlg32.FindTextW.restype = HWND

comdlg32.ReplaceTextW.argtypes = (POINTER(FINDREPLACEW),)
comdlg32.ReplaceTextW.restype = HWND

# modern icon (flat)
#def get_stock_icon(siid):
#    sii = SHSTOCKICONINFO()
#    SHGSI_ICON = 0x000000100
#    shell32.SHGetStockIconInfo(siid, SHGSI_ICON, byref(sii))
#    return sii.hIcon

#def dialog_calculate_text_rect(text, font_name='MS Shell Dlg', font_size=8, hfont=None):
#    hdc = user32.GetDC(0)
#    if hfont is None:
#        hfont = gdi32.CreateFontW(font_size, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET, OUT_TT_PRECIS,
#                CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, font_name)
#    gdi32.SelectObject(hdc, hfont)
#    #gdi32.SetMapMode(hdc, MM_TWIPS)
#    rc = RECT(0, 0, 0, 0)
#    user32.DrawTextW(hdc, text, -1, byref(rc), DT_CALCRECT | DT_LEFT | DT_NOPREFIX)
#    user32.ReleaseDC(0, hdc)
#    return rc

## logical coordinates, not pixels
#def dialog_calculate_multiline_text_height(text, text_width, font_name='MS Shell Dlg', font_size=8, hfont=None):
#    hdc = user32.GetDC(0)
#    if hfont is None:
#        hfont = gdi32.CreateFontW(font_size, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET, OUT_TT_PRECIS,
#                CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, font_name)
#    gdi32.SelectObject(hdc, hfont)
#    rc = RECT(0, 0, text_width, 0)
#    user32.DrawTextW(hdc, text, -1, byref(rc), DT_CALCRECT | DT_LEFT | DT_TOP | DT_WORDBREAK | DT_NOPREFIX)
#    user32.ReleaseDC(0, hdc)
#    return rc.bottom

#def dialog_center(hwnd, hwnd_parent):
#    rc_dlg = RECT()
#    user32.GetWindowRect(hwnd, byref(rc_dlg))
#    rc_parent = RECT()
#    user32.GetWindowRect(hwnd_parent, byref(rc_parent))
#
#    if (rc_parent.right - rc_parent.left) - (rc_dlg.right - rc_dlg.left) > 20:
#        x = rc_parent.left + (((rc_parent.right - rc_parent.left) - (rc_dlg.right - rc_dlg.left)) // 2)
#    else:
#        x = rcParent.left + 70
#    if (rc_parent.bottom - rc_parent.top) - (rc_dlg.bottom - rc_dlg.top) > 20:
#        y = rc_parent.top + (((rc_parent.bottom - rc_parent.top) - (rc_dlg.bottom - rc_dlg.top)) // 2)
#    else:
#        y = rc_parent.top + 60
#    user32.SetWindowPos(hwnd, 0, x, y, 0, 0, SWP_NOZORDER | SWP_NOSIZE)



class ExternalDialog():
    def __init__(self, hwnd):
        self.hwnd = hwnd


########################################
#
########################################
def DarkOnCtlColorDlg(hdc):
    gdi32.SetBkColor(hdc, DARK_BG_COLOR)
    return DARK_BG_BRUSH

########################################
#
########################################
def DarkOnCtlColorStatic(hdc):
    gdi32.SetTextColor(hdc, DARK_TEXT_COLOR)
    gdi32.SetBkColor(hdc, DARK_BG_COLOR)
    return DARK_BG_BRUSH

########################################
#
########################################
def DarkOnCtlColorStaticMsgBox(hdc):
    gdi32.SetTextColor(hdc, DARK_TEXT_COLOR)
    gdi32.SetBkColor(hdc, DARK_CONTROL_BG_COLOR)
    return DARK_CONTROL_BG_BRUSH

########################################
#
########################################
def DarkOnCtlColorBtn(hdc):
    gdi32.SetDCBrushColor(hdc, DARK_BG_COLOR)
    return gdi32.GetStockObject(DC_BRUSH)

########################################
#
########################################
def DarkOnCtlColorEdit(hdc):
    gdi32.SetTextColor(hdc, DARK_TEXT_COLOR)
    gdi32.SetBkColor(hdc, DARK_BG_COLOR)  # DARK_CONTROL_BG_COLOR
    gdi32.SetDCBrushColor(hdc, DARK_BG_COLOR)
    return gdi32.GetStockObject(DC_BRUSH)

########################################
#
########################################
def _DarkCheckBoxSubClassProcCallback(hwnd, msg, wparam, lparam, uidsubclass, dwrefdata):
    if msg == WM_CTLCOLORSTATIC:
        return DarkOnCtlColorStatic(wparam)
    return comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)
#    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

DarkCheckBoxSubclassProc = SUBCLASSPROC(_DarkCheckBoxSubClassProcCallback)

########################################
#
########################################
def _DarkGroupBoxSubClassProcCallback(hwnd, msg, wparam, lparam, uidsubclass, dwrefdata):

    def _paint_groupbox(hdc):
        rcClient = RECT()
        user32.GetClientRect(hwnd, byref(rcClient))

        rcBackground = RECT()
        pointer(rcBackground)[0] = rcClient
        rcBackground.top += 6
        rcBackground.bottom -= 1

        user32.FrameRect(hdc, byref(rcBackground), DARK_BORDER_BRUSH)

        MAX_WIN_TEXT_LEN = 256
        winText = create_unicode_buffer(MAX_WIN_TEXT_LEN)

        user32.GetWindowTextW(hwnd, winText, MAX_WIN_TEXT_LEN)
        if winText[0]:
            gdi32.SelectObject(hdc, user32.SendMessageW(hwnd, WM_GETFONT, 0, 0))

            gdi32.SetBkColor(hdc, DARK_BG_COLOR)
            gdi32.SetTextColor(hdc, DARK_TEXT_COLOR)

            hbr = gdi32.CreateSolidBrush(DARK_BG_COLOR)
            rcGap = RECT(rcClient.left + 7, rcBackground.top, rcClient.left + 9, rcBackground.top + 1)
            user32.FillRect(hdc, byref(rcGap), hbr)
            gdi32.DeleteObject(hbr)

            gdi32.SetTextColor(hdc, DARK_TEXT_COLOR)
            rcText = RECT(rcClient.left + 9, rcClient.top, rcClient.right, rcClient.bottom)
            user32.DrawTextW(hdc, winText, -1, byref(rcText), DT_SINGLELINE | DT_LEFT)  # | DT_VCENTER)

    if msg == WM_PRINTCLIENT:
        hdc = cast(wparam, HDC)
        _paint_groupbox(hdc)
        return 0

    elif msg == WM_PAINT:
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, byref(ps))
        _paint_groupbox(hdc)
        user32.EndPaint(hwnd, byref(ps))
        return 0

    return comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)

DarkGroupBoxSubClassProc = SUBCLASSPROC(_DarkGroupBoxSubClassProcCallback)

########################################
#
########################################
def _DarkListViewSubClassProcCallback(hwnd, msg, wparam, lparam, uidsubclass, dwrefdata):
    if msg == WM_NOTIFY:
        nmhdr = cast(lparam, LPNMHDR).contents
        if nmhdr.code == NM_CUSTOMDRAW:
            nmcd = cast(lparam, LPNMCUSTOMDRAW).contents

            if nmcd.dwDrawStage == CDDS_PREPAINT:
                return CDRF_NOTIFYITEMDRAW

            elif nmcd.dwDrawStage == CDDS_ITEMPREPAINT:
                if nmcd.uItemState & CDIS_SELECTED:
                    gdi32.SetBkColor(nmcd.hdc, DARK_CONTROL_BG_COLOR)

                    hbr = gdi32.CreateSolidBrush(DARK_CONTROL_BG_COLOR)
                    user32.FillRect(nmcd.hdc, byref(nmcd.rc), hbr)
                    gdi32.DeleteObject(hbr);

                    d = 1
                else:
                    gdi32.SetBkColor(nmcd.hdc, 0x171717)  # DARK_BG_COLOR

                    hbr = gdi32.CreateSolidBrush(0x171717)
                    user32.FillRect(nmcd.hdc, byref(nmcd.rc), hbr)
                    gdi32.DeleteObject(hbr)

                    d = 0

                rc = RECT(nmcd.rc.right - 2, nmcd.rc.top, nmcd.rc.right - 1, nmcd.rc.bottom)

                hbr = gdi32.CreateSolidBrush(DARK_SEPARATOR_COLOR)
                user32.FillRect(nmcd.hdc, byref(rc), hbr)
                gdi32.DeleteObject(hbr)

                buf = create_unicode_buffer(32)
                lvc = LVCOLUMNW()
                lvc.mask = LVCF_TEXT
                lvc.cchTextMax = 32
                lvc.pszText = cast(buf, LPCWSTR)

                user32.SendMessageW(hwnd, LVM_GETCOLUMNW, nmcd.dwItemSpec, byref(lvc))

                gdi32.SetTextColor(nmcd.hdc, DARK_TEXT_COLOR)

                rc2 = RECT(nmcd.rc.left + 6 + d, nmcd.rc.top + d, nmcd.rc.right, nmcd.rc.bottom)
                user32.DrawTextW(nmcd.hdc, buf, -1, byref(rc2), DT_SINGLELINE | DT_LEFT | DT_VCENTER)

            return CDRF_SKIPDEFAULT

    return comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)

DarkListViewSubClassProc = SUBCLASSPROC(_DarkListViewSubClassProcCallback)


#TAB_SELECTED_DARK_BG_BRUSH = gdi32.CreateSolidBrush(0x333333)
#TAB_BORDER_BRUSH_DARK = TAB_SELECTED_DARK_BG_BRUSH
#TAB_SELECTED_HILITE_BRUSH = gdi32.CreateSolidBrush(0xD77800)  # 0xFF9933

########################################
#
########################################
def _DarkTabControlSubClassProcCallback(hwnd, msg, wparam, lparam, uidsubclass, dwrefdata):
    if msg == WM_PAINT:

        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, byref(ps))
        gdi32.SetBkMode(hdc, TRANSPARENT)
        gdi32.SetTextColor(hdc, DARK_TEXT_COLOR)

#        gdi32.SelectObject(hdc, self.hfont)
        gdi32.SelectObject(hdc, user32.SendMessageW(hwnd, WM_GETFONT, 0, 0))

        # tabbar background
        user32.FillRect(hdc, byref(ps.rcPaint), DARK_BG_BRUSH)

        selected_index = user32.SendMessageW(hwnd, TCM_GETCURSEL, 0, 0)
        rc = RECT()

        TEXT_MAX = 64
        buf = create_unicode_buffer(TEXT_MAX)
        tc_item = TCITEMW()
        tc_item.mask = TCIF_TEXT
        # If item information is being retrieved, this member specifies the address of the buffer that receives the tab text.
        tc_item.pszText = cast(buf, LPWSTR)
        tc_item.cchTextMax = TEXT_MAX

        for idx in range(user32.SendMessageW(hwnd, TCM_GETITEMCOUNT, 0, 0)):
            user32.SendMessageW(hwnd, TCM_GETITEMRECT, idx, byref(rc))

            # tab right  border
            user32.FillRect(hdc, byref(rc), DARK_TAB_BORDER_BRUSH)

            # tab background
            rc.right -= 1
            user32.FillRect(hdc, byref(rc), DARK_TAB_SELECTED_BG_BRUSH if idx == selected_index else DARK_BG_BRUSH)

            if idx == selected_index:
                user32.FillRect(hdc, byref(RECT(rc.left - (1 if idx else 0), rc.top, rc.right + 1, rc.top + 2)), TAB_SELECTED_HILITE_BRUSH)

            # tab text
            user32.SendMessageW(hwnd, TCM_GETITEMW, idx, byref(tc_item))
            user32.DrawTextW(hdc, buf.value, -1, RECT(rc.left, rc.top + 1, rc.right, rc.bottom), DT_SINGLELINE | DT_CENTER | DT_VCENTER)

            # tab close button
#            if self.__close_button_imagelist:
##                if idx == self.__close_button_hover_index:
##                    user32.FillRect(hdc, byref(RECT(rc.right - 13, rc.top + 3, rc.right - 1, rc.top + 15)), DARK_MENU_BG_BRUSH_HOT)
#                comctl32.ImageList_Draw(self.__close_button_imagelist, 1 if self.is_dark else 0, hdc, rc.right - 15 + 5, 3 + 5, ILD_NORMAL)
#                if idx == self.__close_button_hover_index:
#                    user32.InvertRect(hdc, byref(RECT(rc.right - 13, rc.top + 3, rc.right - 1, rc.top + 15)))

        user32.EndPaint(hwnd, byref(ps))
        return FALSE

    return comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)
#    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

DarkTabControlSubClassProc = SUBCLASSPROC(_DarkTabControlSubClassProcCallback)

########################################
#
########################################
def _DialogSubClassProcCallback(hwnd, msg, wparam, lparam, uidsubclass, dwrefdata):

#    if msg == WM_ERASEBKGND:
#        rc = RECT()
#        user32.GetClientRect(hwnd, byref(rc))
#        user32.FillRect(wparam, byref(rc), DARK_CONTROL_BG_BRUSH)
#        return TRUE


    if msg == WM_CTLCOLORDLG:
        #if self.is_dark:
        return DarkOnCtlColorDlg(wparam)

    elif msg == WM_CTLCOLORSTATIC:
        #if self.is_dark:
        return DarkOnCtlColorStatic(wparam)

    elif msg == WM_CTLCOLORBTN:
        #if self.is_dark:
        return DarkOnCtlColorBtn(wparam)

    elif msg == WM_CTLCOLOREDIT or msg == WM_CTLCOLORLISTBOX:
        #if self.is_dark:
        return DarkOnCtlColorEdit(wparam)

    return comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)

DarkDialogSubclassProc = SUBCLASSPROC(_DialogSubClassProcCallback)

########################################
#
########################################
def _MsgBoxSubClassProcCallback(hwnd, msg, wparam, lparam, uidsubclass, dwrefdata):

    if msg == WM_ERASEBKGND:
        rc = RECT()
        user32.GetClientRect(hwnd, byref(rc))
        user32.FillRect(wparam, byref(rc), DARK_CONTROL_BG_BRUSH)
        return TRUE

#        MSGBOX_HANDLE_CONTROL_MESSAGES()

    elif msg == WM_CTLCOLORDLG:
        #if self.is_dark:
        return DarkOnCtlColorDlg(wparam)

    elif msg == WM_CTLCOLORSTATIC:
        #if self.is_dark:
        return DarkOnCtlColorStaticMsgBox(wparam)

    elif msg == WM_CTLCOLORBTN:
        #if self.is_dark:
        return DarkOnCtlColorBtn(wparam)

    elif msg == WM_CTLCOLOREDIT or msg == WM_CTLCOLORLISTBOX:
        #if self.is_dark:
        #return self.DarkOnCtlColorBtn(wparam)
        gdi32.SetTextColor(wparam, DARK_TEXT_COLOR)
        gdi32.SetBkColor(wparam, DARK_CONTROL_BG_COLOR)
        gdi32.SetDCBrushColor(wparam, DARK_CONTROL_BG_COLOR)
        return gdi32.GetStockObject(DC_BRUSH)

    elif msg == WM_PAINT:
        # Make lower part with buttons darker
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, byref(ps))
        MSGBOX_BOTTOM_HEIGHT = 42
        ps.rcPaint.top = ps.rcPaint.bottom - MSGBOX_BOTTOM_HEIGHT
        user32.FillRect(hdc, byref(ps.rcPaint), DARK_BG_BRUSH)
        user32.EndPaint(hwnd, byref(ps))
        return 0

    return comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)

DarkMsgBoxSubclassProc = SUBCLASSPROC(_MsgBoxSubClassProcCallback)

DARK_EDIT_BG_COLOR = 0x383838

########################################
#
########################################
def _DarkComboBoxClassProcCallback(hwnd, msg, wparam, lparam, uidsubclass, dwrefdata):

#    static HWND s_hwndListBox;

    if msg == WM_CTLCOLORLISTBOX:
        # This makes the internal listbox having dark BG and light text,
        # but only if not custom drawn
        if not (user32.GetWindowLongA(lparam, GWL_STYLE) & LBS_OWNERDRAWFIXED):
#            return DarkOnCtlColorListBox((HDC)wparam)
            pass
        else:

#            s_hwndListBox = (HWND)lparam;

            gdi32.SetBkColor(wparam, 0)
            gdi32.SetDCBrushColor(wparam, 0)
            return gdi32.GetStockObject(DC_BRUSH)

    elif msg == WM_CTLCOLOREDIT:
        gdi32.SetTextColor(wparam, DARK_TEXT_COLOR)
        gdi32.SetBkColor(wparam, DARK_EDIT_BG_COLOR)
        gdi32.SetDCBrushColor(wparam, DARK_EDIT_BG_COLOR)
        return gdi32.GetStockObject(DC_BRUSH)

    elif msg == WM_DRAWITEM:
#        DRAWITEMSTRUCT *di = (DRAWITEMSTRUCT*)lparam;
        di = cast(lparam, POINTER(DRAWITEMSTRUCT)).contents
        if not (di.itemState & ODS_SELECTED):
            comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)
            di = cast(lparam, POINTER(DRAWITEMSTRUCT)).contents
            user32.InvertRect(di.hDC, byref(di.rcItem))
            return TRUE

    return comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)

DarkComboBoxSubclassProc = SUBCLASSPROC(_DarkComboBoxClassProcCallback)

########################################
#
########################################
def DarkDialogInit(hwnd):

    dwm_use_dark_mode(hwnd, True)

    hfont = user32.SendMessageW(hwnd, WM_GETFONT, 0, 0)

    controls = []
    def _enum_child_func(hwnd_child, lparam):
        controls.append(hwnd_child)
        return TRUE
    user32.EnumChildWindows(hwnd, WNDENUMPROC(_enum_child_func), 0)

    dlg = Window(wrap_hwnd=hwnd)

    for hwnd_control in controls:
        buf = create_unicode_buffer(32)
        user32.GetClassNameW(hwnd_control, buf, 32)
        window_class = buf.value

        ########################################
        # Button
        ########################################
        if window_class == 'Button':

            uxtheme.SetWindowTheme(hwnd_control, 'DarkMode_Explorer', None)

            style = user32.GetWindowLongPtrA(hwnd_control, GWL_STYLE)

            if style & BS_TYPEMASK in (BS_CHECKBOX, BS_AUTOCHECKBOX, BS_RADIOBUTTON, BS_AUTORADIOBUTTON, BS_AUTO3STATE):
                rc = RECT()
                user32.GetClientRect(hwnd_control, byref(rc))

                buf = create_unicode_buffer(64)
                user32.GetWindowTextW(hwnd_control, buf, 64)
                window_title = buf.value.replace('&', '')
                user32.SetWindowTextW(hwnd_control, window_title)

                # wrap to prevent garbage collection while dialog exists
                window_checkbox = Window('Button', parent_window=dlg, wrap_hwnd=hwnd_control)

#                rc_text = Dialog.calculate_text_rect(window_title, hfont=hfont)
                rc_text = rc

                hwnd_static = user32.CreateWindowExW(
                    0,
                    WC_STATIC,
                    window_title,
                    WS_CHILD | SS_SIMPLE | WS_VISIBLE,
                    17,
                    0,
                    rc.right - rc.left,
                    rc.bottom - rc.top,
                    window_checkbox.hwnd,
                    NULL,
                    NULL,
                    NULL
                )
                user32.SendMessageW(hwnd_static, WM_SETFONT, hfont, MAKELPARAM(1, 0))

                comctl32.SetWindowSubclass(hwnd_control, DarkCheckBoxSubclassProc, CHECKBOX_SUBCLASS_ID, 0)

            elif style & BS_TYPEMASK == BS_GROUPBOX:
#                rc = RECT()
#                user32.GetWindowRect(hwnd_control, byref(rc))
#                user32.MapWindowPoints(None, hwnd, byref(rc), 2)
#                buf = create_unicode_buffer(64)
#                user32.GetWindowTextW(hwnd_control, buf, 64)
#
#                static = Static(
#                    parent_window=dlg,
#                    style=WS_CHILD | SS_SIMPLE | WS_VISIBLE,
#                    ex_style=WS_EX_TRANSPARENT,
#                    left=rc.left + 10, top=rc.top, width=rc.right - rc.left - 16, height=rc.bottom - rc.top,
#                    window_title=buf.value
#                )
#                static.set_font(hfont=hfont)
#                static.apply_theme(True)

                comctl32.SetWindowSubclass(hwnd_control, DarkGroupBoxSubClassProc, 1, 0)

        ########################################
        # ComboBox
        ########################################
        elif window_class == 'ComboBox':
            uxtheme.SetWindowTheme(hwnd_control, 'DarkMode_CFD', None)

            # Find internal listbox (ComboLBox)
            ci = COMBOBOXINFO()
            user32.SendMessageW(hwnd_control, CB_GETCOMBOBOXINFO, 0, byref(ci))
            if ci.hwndList:
                # Dark scrollbars for the internal Listbox (ComboLBox)
                uxtheme.SetWindowTheme(ci.hwndList, "DarkMode_Explorer", None)

                ex_style = user32.GetWindowLongA(ci.hwndList, GWL_EXSTYLE)
                if ex_style & WS_EX_CLIENTEDGE:
                    user32.SetWindowLongA(ci.hwndList, GWL_EXSTYLE, ex_style & ~WS_EX_CLIENTEDGE   & ~WS_EX_STATICEDGE)
                    user32.SetWindowLongA(ci.hwndList, GWL_STYLE, user32.GetWindowLongA(ci.hwndList, GWL_STYLE) | WS_BORDER)

            COMBOBOX_SUBCLASS_ID = 0
            comctl32.SetWindowSubclass(hwnd_control, DarkComboBoxSubclassProc, COMBOBOX_SUBCLASS_ID, 0)

        ########################################
        # ComboBoxEx32
        ########################################
        elif window_class == 'ComboBoxEx32':
            # Find internal combobox control
            hwnd_combobox = user32.SendMessageW(hwnd_control, CBEM_GETCOMBOCONTROL, 0, 0)
            uxtheme.SetWindowTheme(hwnd_combobox, "DarkMode_CFD", None)

#            SetWindowSubclass(hwnd_combobox, &DarkComboBoxExClassProc, COMBOBOXEX_SUBCLASS_ID, 0);

#        elif window_class == 'ComboLBox':
#            uxtheme.SetWindowTheme(hwnd_control, 'DarkMode_CFD', None)
#
#            user32.SetWindowLongPtrA(hwnd_control, GWL_EXSTYLE,
#                    user32.GetWindowLongPtrA(hwnd_control, GWL_EXSTYLE) & ~WS_EX_CLIENTEDGE)
#            user32.SetWindowLongPtrA(hwnd_control, GWL_STYLE,
#                    user32.GetWindowLongPtrA(hwnd_control, GWL_STYLE) | WS_BORDER)
#            user32.SetWindowPos(hwnd_control, 0, 0, 0, 0, 0,
#                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)

        ########################################
        # Edit
        ########################################
        elif window_class == 'Edit':
            uxtheme.SetWindowTheme(hwnd_control, 'DarkMode_Explorer', None)
            # check parent
            user32.GetClassNameW(user32.GetParent(hwnd_control), buf, 32)
            if buf.value != 'ComboBox':
                user32.SetWindowLongA(hwnd_control, GWL_EXSTYLE,
                        user32.GetWindowLongA(hwnd_control, GWL_EXSTYLE) & ~WS_EX_STATICEDGE & ~WS_EX_CLIENTEDGE)
                user32.SetWindowLongA(hwnd_control, GWL_STYLE,
                        user32.GetWindowLongA(hwnd_control, GWL_STYLE) | WS_BORDER)

                rc = RECT()
                user32.GetWindowRect(hwnd_control, byref(rc))
                #w, h = rc.right - rc.left, rc.bottom - rc.top
                #user32.SendMessageW(hwnd_control, EM_SETMARGINS, EC_LEFTMARGIN, 2)
                user32.MapWindowPoints(None, user32.GetParent(hwnd_control), byref(rc), 2)
                user32.SetWindowPos(
                    hwnd_control, 0,
                    rc.left + 1, rc.top,
                    rc.right - rc.left - 2, rc.bottom - rc.top,
                    SWP_NOZORDER | SWP_FRAMECHANGED
                )

        ########################################
        # Static
        ########################################
        elif window_class == 'Static':
            ex_style = user32.GetWindowLongA(hwnd_control, GWL_EXSTYLE)
            if ex_style & WS_EX_STATICEDGE or ex_style & WS_EX_CLIENTEDGE:
                user32.SetWindowLongA(hwnd_control, GWL_EXSTYLE, ex_style & ~WS_EX_STATICEDGE & ~WS_EX_CLIENTEDGE)
                user32.SetWindowLongA(hwnd_control, GWL_STYLE, user32.GetWindowLongA(hwnd_control, GWL_STYLE) | WS_BORDER)

        ########################################
        # SysListView32
        ########################################
        elif window_class == 'SysListView32':

            uxtheme.SetWindowTheme(hwnd_control, "DarkMode_Explorer", None)

            user32.SendMessageW(hwnd_control, LVM_SETTEXTCOLOR, 0, DARK_TEXT_COLOR)
            user32.SendMessageW(hwnd_control, LVM_SETTEXTBKCOLOR, 0, DARK_CONTROL_BG_COLOR)
            user32.SendMessageW(hwnd_control, LVM_SETBKCOLOR, 0, DARK_CONTROL_BG_COLOR)

            # Unfortunately I couldn't find a way to invert the colors of a SysHeader32,
            # it's always black on white. But without theming removed it looks slightly
            # better inside a dark mode ListView.
            hwnd_header = user32.SendMessageW(hwnd_control, LVM_GETHEADER, 0, 0);
            if hwnd_header:
                uxtheme.SetWindowTheme(hwnd_header, "ItemsView", None)
                comctl32.SetWindowSubclass(hwnd_control, DarkListViewSubClassProc, CHECKBOX_SUBCLASS_ID, 0)

        ########################################
        # SysTabControl32
        ########################################
        elif window_class == 'SysTabControl32':
            comctl32.SetWindowSubclass(hwnd_control, DarkTabControlSubClassProc, 1, 0)

        ########################################
        # UpDown
        ########################################
        elif window_class == 'msctls_updown32':
            uxtheme.SetWindowTheme(hwnd_control, 'DarkMode_Explorer', None)

#        elif window_class == 'msctls_statusbar32':
#            Statusbar(wrap_hwnd=hwnd_control).apply_theme(True)

########################################
#
########################################
def DarkDialogHandleMessages(msg, wparam):
    if msg == WM_CTLCOLORDLG or msg == WM_CTLCOLORSTATIC:
        gdi32.SetTextColor(wparam, DARK_TEXT_COLOR)
        gdi32.SetBkColor(wparam, DARK_BG_COLOR)
        return DARK_BG_BRUSH

    elif msg == WM_CTLCOLORBTN:
        gdi32.SetDCBrushColor(wparam, DARK_BG_COLOR)
        return gdi32.GetStockObject(DC_BRUSH)

    elif msg == WM_CTLCOLOREDIT or msg == WM_CTLCOLORLISTBOX:
        gdi32.SetTextColor(wparam, DARK_TEXT_COLOR)
        gdi32.SetBkColor(wparam, DARK_CONTROL_BG_COLOR)
        gdi32.SetDCBrushColor(wparam, DARK_CONTROL_BG_COLOR)
        return gdi32.GetStockObject(DC_BRUSH)
    return FALSE
