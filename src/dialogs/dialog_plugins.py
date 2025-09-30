from ctypes import *
import os

from winapp.const import *
from winapp.controls.common import LVCOLUMNW, LVITEMW
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from const import *
from resources import *

########################################
#
########################################
def show(main):

    rc = RECT()

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
            if main.is_dark:
                DarkDialogInit(hwnd)
            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)
#            user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_SBR1), SB_GETRECT, 0, byref(rc))

            hwnd_listview = user32.GetDlgItem(hwnd, IDC_LSV1)

            ex_style = LVS_EX_CHECKBOXES | LVS_EX_FULLROWSELECT | LVS_EX_AUTOSIZECOLUMNS
            user32.SendMessageW(hwnd_listview, LVM_SETEXTENDEDLISTVIEWSTYLE, ex_style, ex_style)

            lvc = LVCOLUMNW()
            lvc.mask = LVCF_TEXT | LVCF_WIDTH

            lvc.pszText = "Name"
            lvc.cx = 120
            user32.SendMessageW(hwnd_listview, LVM_INSERTCOLUMNW, 0, byref(lvc))

            lvc.pszText = "Description"
            lvc.cx = 500
            user32.SendMessageW(hwnd_listview, LVM_INSERTCOLUMNW, 1, byref(lvc))

            ########################################
            # add items to the the list view control
            ########################################
            lvi = LVITEMW()
            lvi.mask = LVIF_TEXT #| LVIF_STATE

            for i, p in enumerate(os.listdir(os.path.join(APP_DIR, 'plugins'))):
                lvi.iItem = i

                lvi.iSubItem = 0
                lvi.pszText = p
                user32.SendMessageW(hwnd_listview, LVM_INSERTITEMW, 0, byref(lvi))

                info_file = os.path.join(APP_DIR, 'plugins', p, 'info.txt')
                if os.path.isfile(info_file):
                    with open(info_file, 'r') as f:
                        lvi.iSubItem = 1
                        lvi.pszText = f.read()
                        user32.SendMessageW(hwnd_listview, LVM_SETITEMW, 0, byref(lvi))

            for i, p in enumerate(os.listdir(os.path.join(APP_DIR, 'plugins'))):
                if p in main.state['plugins']:
                    lvi = LVITEMW()
                    lvi.stateMask = LVIS_STATEIMAGEMASK
                    lvi.state = 0x2000  # 0x1000 if res & 0x2000 else 0x2000
                    user32.SendMessageW(hwnd_listview, LVM_SETITEMSTATE, i, byref(lvi))

        elif msg == WM_NOTIFY:
            mh = cast(lparam, LPNMHDR).contents
            if mh.code == LVN_ITEMCHANGED:
                lv = cast(lparam, POINTER(NMLISTVIEW)).contents
                if lv.uOldState == 0:
                    return FALSE
                # 2: checked, 1: unchecked, otherwise ignore
                check_val = lv.uNewState >> 12
                if check_val:
                    buf = create_unicode_buffer(32)
                    lvi = LVITEMW()
                    lvi.pszText = cast(buf, LPWSTR)
                    lvi.cchTextMax = 32
                    user32.SendMessageW(mh.hwndFrom, LVM_GETITEMTEXTW, lv.iItem, byref(lvi))
                    if check_val == 2:
                        if buf.value not in main.state['plugins']:
                               main.state['plugins'].append(buf.value)
                    else:
                        main.state['plugins'].remove(buf.value)

        elif msg == WM_SIZE:
            width, height = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
#            hwnd_statusbar = user32.GetDlgItem(hwnd, IDC_SBR1)
#            user32.SendMessageW(hwnd_statusbar, WM_SIZE, 0, 0)
            height -= rc.bottom
            user32.SetWindowPos(user32.GetDlgItem(hwnd, IDC_LSV1), NULL, 0, 0, width, height, SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)

        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, 0)

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_PLUGIN_MANAGER),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )
