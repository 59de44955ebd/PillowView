# https://learn.microsoft.com/en-us/windows/win32/controls/list-view-control-reference

from ctypes import *
from ctypes.wintypes import *

from ..const import *  # WS_CHILD, WS_VISIBLE
from ..window import *

from ..dlls import comctl32, user32, uxtheme
from ..themes import *
from .common import *

#comctl32 = windll.Comctl32
#comctl32.ImageList_Create.restype = HANDLE

########################################
# Structs
########################################
#typedef struct tagLVITEMW
#{
#    UINT mask;
#    int iItem;
#    int iSubItem;
#    UINT state;
#    UINT stateMask;
#    LPWSTR pszText;
#    int cchTextMax;
#    int iImage;
#    LPARAM lParam;
#    int iIndent;
##if (NTDDI_VERSION >= NTDDI_WINXP)
#    int iGroupId;
#    UINT cColumns; // tile view columns
#    PUINT puColumns;
##endif
##if (NTDDI_VERSION >= NTDDI_VISTA)
#    int* piColFmt;
#    int iGroup; // readonly. only valid for owner data.
##endif
#} LVITEMW, *LPLVITEMW;


class ROW(Structure):
    _fields_ = [
        ("a",          UINT),
        ("b",          UINT),
        ("c",          UINT),
        ("d",          UINT),
        ("e",          UINT),
    ]

#class LVITEMW(Structure):
#    _fields_ = [
#        ("mask",          UINT),
#        ("iItem",         INT),
#        ("iSubItem",      INT),
#        ("state",         UINT),
#        ("stateMask",     UINT),
#        ("pszText",       LPWSTR),
#        ("cchTextMax",    INT),
#        ("iImage",        INT),
#        ("lParam",        LPARAM), #POINTER(ROW)),  #LPARAM),
#        ("iIndent",       INT),
#        ("iGroupId",      INT),
#        ("cColumns",      UINT),
#        ("puColumns",     POINTER(UINT)),
#        ("piColFmt",      POINTER(INT)),
#        ("iGroup",        INT),
#    ]

#typedef struct tagLVDISPINFOW {
#    NMHDR hdr;
#    LVITEMW item;
#} NMLVDISPINFOW, *LPNMLVDISPINFOW;

class NMLVDISPINFO(Structure):
    _fields_ = [
        ("hdr",          NMHDR),
        ("item",         LVITEMW),
    ]
#LPNMLVDISPINFO = POINTER(NMLVDISPINFO)

#LV_DISPINFOW    =NMLVDISPINFOW
#LV_DISPINFO     =NMLVDISPINFO

#typedef struct tagNMITEMACTIVATE {
#  NMHDR  hdr;
#  int    iItem;
#  int    iSubItem;
#  UINT   uNewState;
#  UINT   uOldState;
#  UINT   uChanged;
#  POINT  ptAction;
#  LPARAM lParam;
#  UINT   uKeyFlags;
#} NMITEMACTIVATE, *LPNMITEMACTIVATE;

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
#LPNMITEMACTIVATE = POINTER(NMITEMACTIVATE)

#LVCOLUMNW_V1_SIZE =CCSIZEOF_STRUCT(LVCOLUMNW, iSubItem)
#typedef struct tagLVCOLUMNW {
#  UINT   mask;
#  int    fmt;
#  int    cx;
#  LPWSTR pszText;
#  int    cchTextMax;
#  int    iSubItem;
#  int    iImage;
#  int    iOrder;
#  int    cxMin;
#  int    cxDefault;
#  int    cxIdeal;
#} LVCOLUMNW, *LPLVCOLUMNW;

#class LVCOLUMNW(Structure):
#    _fields_ = [
#        ("mask", UINT),
#        ("fmt",      INT),
#        ("cx",   INT),
#        ("pszText",  LPWSTR),
#        ("cchTextMax",  INT),
#        ("iSubItem",   INT),
#        ("iImage",   INT),
#        ("iOrder",     INT),
#        ("cxMin",  INT),
#        ("cxDefault",     INT),
#        ("cxIdeal",  INT),
#    ]
#LPLVCOLUMNW = POINTER(LVCOLUMNW)

#typedef struct tagLVHITTESTINFO
#{
#    POINT pt;
#    UINT flags;
#    int iItem;
#    int iSubItem;    # this is was NOT in win95.  valid only for LVM_SUBITEMHITTEST
#    int iGroup; # readonly. index of group. only valid for owner data.
#                # supports single item in multiple groups.
#} LVHITTESTINFO, *LPLVHITTESTINFO;

class LVHITTESTINFO(Structure):
    _fields_ = [
        ("pt",          POINT),
        ("flags",       UINT),
        ("iItem",       INT),
        ("iSubItem",    INT),
        ("iGroup",      INT),
    ]
#LPLVHITTESTINFO = POINTER(LVHITTESTINFO)

#typedef struct tagLVFINDINFOW {
#  UINT    flags;
#  LPCWSTR psz;
#  LPARAM  lParam;
#  POINT   pt;
#  UINT    vkDirection;
#} LVFINDINFOW, *LPFINDINFOW;

class LVFINDINFOW(Structure):
    _fields_ = [
        ("flags",       UINT),
        ("psz",         LPCWSTR),
        ("lParam",      LPARAM),
        ("pt",          POINT),
        ("vkDirection", UINT),
    ]


#typedef struct tagLVBKIMAGEW
#{
#    ULONG ulFlags;              # LVBKIF_*
#    HBITMAP hbm;
#    LPWSTR pszImage;
#    UINT cchImageMax;
#    int xOffsetPercent;
#    int yOffsetPercent;
#} LVBKIMAGEW, *LPLVBKIMAGEW;

#typedef struct tagLVGROUP
#{
#    UINT    cbSize;
#    UINT    mask;
#    LPWSTR  pszHeader;
#    int     cchHeader;
#    LPWSTR  pszFooter;
#    int     cchFooter;
#    int     iGroupId;
#    UINT    stateMask;
#    UINT    state;
#    UINT    uAlign;
#    LPWSTR  pszSubtitle;
#    UINT    cchSubtitle;
#    LPWSTR  pszTask;
#    UINT    cchTask;
#    LPWSTR  pszDescriptionTop;
#    UINT    cchDescriptionTop;
#    LPWSTR  pszDescriptionBottom;
#    UINT    cchDescriptionBottom;
#    int     iTitleImage;
#    int     iExtendedImage;
#    int     iFirstItem;         # Read only
#    UINT    cItems;             # Read only
#    LPWSTR  pszSubsetTitle;     # NULL if group is not subset
#    UINT    cchSubsetTitle;
#	LVGROUP_V5_SIZE CCSIZEOF_STRUCT(LVGROUP, uAlign)
#} LVGROUP, *PLVGROUP;

#LV_FINDINFOW    =LVFINDINFOW

#typedef struct tagLVFINDINFOW
#{
#    UINT flags;
#    LPCWSTR psz;
#    LPARAM lParam;
#    POINT pt;
#    UINT vkDirection;
#} LVFINDINFOW, *LPFINDINFOW;

#typedef struct tagLVGROUPMETRICS
#{
#    UINT cbSize;
#    UINT mask;
#    UINT Left;
#    UINT Top;
#    UINT Right;
#    UINT Bottom;
#    COLORREF crLeft;
#    COLORREF crTop;
#    COLORREF crRight;
#    COLORREF crBottom;
#    COLORREF crHeader;
#    COLORREF crFooter;
#} LVGROUPMETRICS, *PLVGROUPMETRICS;

#typedef struct tagLVINSERTGROUPSORTED
#{
#    PFNLVGROUPCOMPARE pfnGroupCompare;
#    void *pvData;
#    LVGROUP lvGroup;
#}LVINSERTGROUPSORTED, *PLVINSERTGROUPSORTED;

#typedef struct tagLVTILEVIEWINFO
#{
#    UINT    cbSize;
#    DWORD   dwMask;     #LVTVIM_*
#    DWORD   dwFlags;    #LVTVIF_*
#    SIZE    sizeTile;
#    int     cLines;
#    RECT    rcLabelMargin;
#} LVTILEVIEWINFO, *PLVTILEVIEWINFO;
#
#typedef struct tagLVTILEINFO
#{
#    UINT    cbSize;
#    int     iItem;
#    UINT    cColumns;
#    PUINT   puColumns;
#    int*    piColFmt;
#} LVTILEINFO, *PLVTILEINFO;

#LVTILEINFO_V5_SIZE CCSIZEOF_STRUCT(LVTILEINFO, puColumns)

#typedef struct
#{
#    UINT cbSize;
#    DWORD dwFlags;
#    int iItem;
#    DWORD dwReserved;
#} LVINSERTMARK, * LPLVINSERTMARK;

#typedef struct tagLVSETINFOTIP
#{
#    UINT cbSize;
#    DWORD dwFlags;
#    LPWSTR pszText;
#    int iItem;
#    int iSubItem;
#} LVSETINFOTIP, *PLVSETINFOTIP;

#typedef struct tagLVFOOTERINFO
#{
#    UINT mask;          # LVFF_*
#    LPWSTR pszText;
#    int cchTextMax;
#    UINT cItems;
#} LVFOOTERINFO, *LPLVFOOTERINFO;

#typedef struct tagLVFOOTERITEM
#{
#    UINT mask;          # LVFIF_*
#    int iItem;
#    LPWSTR pszText;
#    int cchTextMax;
#    UINT state;         # LVFIS_*
#    UINT stateMask;     # LVFIS_*
#} LVFOOTERITEM, *LPLVFOOTERITEM;

# supports a single item in multiple groups.
#typedef struct tagLVITEMINDEX
#{
#    int iItem;          # listview item index
#    int iGroup;         # group index (must be -1 if group view is not enabled)
#} LVITEMINDEX, *PLVITEMINDEX;

#LPNM_LISTVIEW   LPNMLISTVIEW
#NM_LISTVIEW     NMLISTVIEW

#typedef struct tagNMLISTVIEW
#{
#    NMHDR   hdr;
#    int     iItem;
#    int     iSubItem;
#    UINT    uNewState;
#    UINT    uOldState;
#    UINT    uChanged;
#    POINT   ptAction;
#    LPARAM  lParam;
#} NMLISTVIEW, *LPNMLISTVIEW;

#class NMLISTVIEW(Structure):
#    _fields_ = [
#        ("hdr",        NMHDR),
#        ("iItem",      INT),
#        ("iSubItem",   INT),
#        ("uNewState",  UINT),
#        ("uOldState",  UINT),
#        ("uChanged",  UINT),
#        ("ptAction",   POINT),
#        ("lParam",     LPARAM),
#    ]
#LPNMLISTVIEW = POINTER(NMLISTVIEW)

# NMITEMACTIVATE is used instead of NMLISTVIEW in IE >= =0x400
# therefore all the fields are the same except for extra uKeyFlags
# they are used to store key flags at the time of the single click with
# delayed activation - because by the time the timer goes off a user may
# not hold the keys (shift, ctrl) any more
#typedef struct tagNMITEMACTIVATE
#{
#    NMHDR   hdr;
#    int     iItem;
#    int     iSubItem;
#    UINT    uNewState;
#    UINT    uOldState;
#    UINT    uChanged;
#    POINT   ptAction;
#    LPARAM  lParam;
#    UINT    uKeyFlags;
#} NMITEMACTIVATE, *LPNMITEMACTIVATE;

#NMLVCUSTOMDRAW_V3_SIZE CCSIZEOF_STRUCT(NMLVCUSTOMDRAW, clrTextBk)

#typedef struct tagNMLVCUSTOMDRAW
#{
#    NMCUSTOMDRAW nmcd;
#    COLORREF clrText;
#    COLORREF clrTextBk;
#    int iSubItem;
#    DWORD dwItemType;
#    # Item custom draw
#    COLORREF clrFace;
#    int iIconEffect;
#    int iIconPhase;
#    int iPartId;
#    int iStateId;
#    # Group Custom Draw
#    RECT rcText;
#    UINT uAlign;      # Alignment. Use LVGA_HEADER_CENTER, LVGA_HEADER_RIGHT, LVGA_HEADER_LEFT
#} NMLVCUSTOMDRAW, *LPNMLVCUSTOMDRAW;

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
#LPNMLVCUSTOMDRAW = POINTER(NMLVCUSTOMDRAW)


#typedef struct tagNMLVCACHEHINT
#{
#    NMHDR   hdr;
#    int     iFrom;
#    int     iTo;
#} NMLVCACHEHINT, *LPNMLVCACHEHINT;

#LPNM_CACHEHINT  LPNMLVCACHEHINT
#PNM_CACHEHINT   LPNMLVCACHEHINT
#NM_CACHEHINT    NMLVCACHEHINT

#typedef struct tagNMLVFINDITEMW
#{
#    NMHDR   hdr;
#    int     iStart;
#    LVFINDINFOW lvfi;
#} NMLVFINDITEMW, *LPNMLVFINDITEMW;

#PNM_FINDITEMW   LPNMLVFINDITEMW
#LPNM_FINDITEMW  LPNMLVFINDITEMW
#NM_FINDITEMW    NMLVFINDITEMW

#PNM_FINDITEM    PNM_FINDITEMW
#LPNM_FINDITEM   LPNM_FINDITEMW
#NM_FINDITEM     NM_FINDITEMW
#NMLVFINDITEM    NMLVFINDITEMW
#LPNMLVFINDITEM  LPNMLVFINDITEMW

#typedef struct tagNMLVODSTATECHANGE
#{
#    NMHDR hdr;
#    int iFrom;
#    int iTo;
#    UINT uNewState;
#    UINT uOldState;
#} NMLVODSTATECHANGE, *LPNMLVODSTATECHANGE;
#
#PNM_ODSTATECHANGE   LPNMLVODSTATECHANGE
#LPNM_ODSTATECHANGE  LPNMLVODSTATECHANGE
#NM_ODSTATECHANGE    NMLVODSTATECHANGE

#typedef struct tagLVKEYDOWN
#{
#    NMHDR hdr;
#    WORD wVKey;
#    UINT flags;
#} NMLVKEYDOWN, *LPNMLVKEYDOWN;

#if (NTDDI_VERSION >= NTDDI_VISTA)
#typedef struct tagNMLVLINK
#{
#    NMHDR       hdr;
#    LITEM       link;
#    int         iItem;
#    int         iSubItem;
#} NMLVLINK,  *PNMLVLINK;

#typedef struct tagNMLVGETINFOTIPW
#{
#    NMHDR hdr;
#    DWORD dwFlags;
#    LPWSTR pszText;
#    int cchTextMax;
#    int iItem;
#    int iSubItem;
#    LPARAM lParam;
#} NMLVGETINFOTIPW, *LPNMLVGETINFOTIPW;

# NMLVGETINFOTIPA.dwFlag values

#typedef struct tagNMLVSCROLL
#{
#    NMHDR   hdr;
#    int     dx;
#    int     dy;
#} NMLVSCROLL, *LPNMLVSCROLL;

#typedef struct tagNMLVEMPTYMARKUP
#{
#    NMHDR hdr;
#    # out params from client back to listview
#    DWORD dwFlags;                      # EMF_*
#    WCHAR szMarkup[L_MAX_URL_LENGTH];   # markup displayed
#} NMLVEMPTYMARKUP;


#int CALLBACK CompareFunc(LPARAM lParam1, LPARAM lParam2, LPARAM lParamSort);
#COMPAREPROC = WINFUNCTYPE(INT, LPARAM, LPARAM, LPARAM)


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
        #return ListView_SetImageList(self.hwnd, h_imagelist, list_type)
        user32.SendMessageW.argtypes = [HWND, UINT, WPARAM, HANDLE]
        return user32.SendMessageW(self.hwnd, LVM_SETIMAGELIST, list_type, h_imagelist)

    def insert_item(self, lvi):
        return user32.SendMessageW(self.hwnd, LVM_INSERTITEMW, 0, byref(lvi))

#    def insert_column(self, idx, text, fmt=LVCFMT_LEFT, width=100)
#        lvc = LVCOLUMNW()
#        lvc.pszText = text
#        lvc.fmt = fmt
#        lvc.cx = width
#        lvc.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_FMT
#
#        return user32.SendMessageW(self.hwnd, LVM_INSERTCOLUMNW, idx, byref(lvc))

#    def greeting(name: str) -> str:
#        return 'Hello ' + str(name)

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

#	def AddColumn(LPCTSTR strColumn, int nItem, int nSubItem = -1,
#			int nMask = LVCF_FMT | LVCF_WIDTH | LVCF_TEXT | LVCF_SUBITEM,
#			int nFmt = LVCFMT_LEFT)
#		const int cxOffset = 15
#		LVCOLUMN lvc = {}
#		lvc.mask = nMask
#		lvc.fmt = nFmt
#		lvc.pszText = (LPTSTR)strColumn
#		lvc.cx = GetStringWidth(lvc.pszText) + cxOffset
#		if(nMask & LVCF_SUBITEM)
#			lvc.iSubItem = (nSubItem != -1) ? nSubItem : nItem
#		return InsertColumn(nItem, &lvc)
#
#	def AddItem(self, nItem: int, nSubItem: int, strItem: str, nImageIndex: int  = -3) -> int:
#		LVITEM lvItem = {}
#		lvItem.mask = LVIF_TEXT
#		lvItem.iItem = nItem
#		lvItem.iSubItem = nSubItem
#		lvItem.pszText = (LPTSTR)strItem
#		if(nImageIndex != -3)
#		{
#			lvItem.mask |= LVIF_IMAGE
#			lvItem.iImage = nImageIndex
#		}
#		if(nSubItem == 0)
#			return InsertItem(&lvItem)
#		return SetItem(&lvItem) ? nItem : -1

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        uxtheme.SetWindowTheme(self.hwnd, 'DarkMode_Explorer' if is_dark else 'Explorer', None)
#        uxtheme.SetWindowTheme(self.hwnd, 'ItemsView', None)

        hwnd_header = self.send_message(LVM_GETHEADER, 0, 0)
        if hwnd_header:

#            uxtheme.SetWindowTheme(hwnd_header, 'DarkMode_Explorer' if is_dark else 'Explorer', None)
#            uxtheme.SetWindowTheme(hwnd_header, '', '')
            uxtheme.SetWindowTheme(hwnd_header, 'ItemsView', None)

            user32.SendMessageW(hwnd_header, WM_CHANGEUISTATE, MAKELONG(UIS_SET, UISF_HIDEFOCUS), 0)

            HDS_FLAT = 0x0200
            HDS_OVERFLOW            =0x1000
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
