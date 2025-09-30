from ctypes import *

from winapp.const import *
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from const import *
from image import get_bpp
from resources import *

RESAMPLE_FILTERS = ['Bicubic', 'Bilinear', 'Box', 'Hamming', 'Lanczos', 'Nearest']
MAX_SIZE = 9999

########################################
#
########################################
def show(main, callback):
    if main.img is None:
        return

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
            if main.is_dark:
                DarkDialogInit(hwnd)
            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)

            if "A" not in main.img.getbands():
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_RGBA), 0)
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_LA), 0)
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_PA), 0)


            # Disable current mode since otherwise nothing to do
            if main.img.mode == 'RGBA':
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_RGBA), 0)
            elif main.img.mode == 'CMYK':
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_CMYK), 0)
            elif main.img.mode == 'RGB':
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_RGB), 0)
            elif main.img.mode == 'LA':
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_LA), 0)
            elif main.img.mode == 'PA':
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_PA), 0)
            elif main.img.mode == 'L':
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_L), 0)
            elif main.img.mode == 'P':
                bpp = get_bpp(main.img)
                if bpp == 1:
                    user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_P_1), 0)
                elif bpp == 4:
                    user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_P_4), 0)
                else:
                    user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_P_8), 0)
            elif main.img.mode == '1':
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_1), 0)

            if main.img.mode == 'RGB':
                user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_L), BM_SETCHECK, BST_CHECKED, 0)
            else:
                user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_RGB), BM_SETCHECK, BST_CHECKED, 0)

        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, 0)

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)

            if command == BN_CLICKED:
                control_id = LOWORD(wparam)

                if control_id == IDOK:
                    dither = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_DEPTH_BTN_DITHER), BM_GETCHECK, 0, 0)
                    control_id_depth = None

                    for control_id in (IDC_DEPTH_BTN_RGBA, IDC_DEPTH_BTN_CMYK, IDC_DEPTH_BTN_RGB, IDC_DEPTH_BTN_LA, IDC_DEPTH_BTN_PA,
                        IDC_DEPTH_BTN_L, IDC_DEPTH_BTN_P_8, IDC_DEPTH_BTN_P_4, IDC_DEPTH_BTN_P_1, IDC_DEPTH_BTN_1, IDC_DEPTH_BTN_P_CUSTOM
                    ):
                        if user32.SendMessageW(user32.GetDlgItem(hwnd, control_id), BM_GETCHECK, 0, 0) == BST_CHECKED:
                            control_id_depth = control_id
                            break

                    if control_id_depth == IDC_DEPTH_BTN_P_CUSTOM:
                        buf = create_unicode_buffer(4)
                        user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_DEPTH_EDIT_CUSTOM), buf, 4)
                        colors = min(256, max(2, int(buf.value)))
                    else:
                        colors = None
                    callback(control_id_depth, dither, colors)
                    user32.EndDialog(hwnd, 0)

                elif control_id == IDCANCEL:
                    user32.EndDialog(hwnd, 0)

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_DEPTH),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )
