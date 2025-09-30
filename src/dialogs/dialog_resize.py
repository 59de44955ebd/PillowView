from ctypes import *

from winapp.const import *
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from const import *
from resources import *

RESAMPLE_FILTERS = ['Bicubic', 'Bilinear', 'Box', 'Hamming', 'Lanczos', 'Nearest']
MAX_SIZE = 9999

########################################
#
########################################
def show(main, callback):
    if main.img is None:
        return

    class ctx():
        preserve = 1
        is_pixels = True

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
            if main.is_dark:
                DarkDialogInit(hwnd)
            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)

            user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_STATIC_CURRENT_SIZE),
                    f'Current size: {main.img.width} x {main.img.height} Pixels')
            user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_STATIC_NEW_SIZE),
                    f'New size: {main.img.width} x {main.img.height} Pixels')
            user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_WIDTH), str(main.img.width))
            user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_HEIGHT), str(main.img.height))

            user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RADIO_PIXELS), BM_SETCHECK, BST_CHECKED, 0)
            user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_CHECKBOX_PRESERVE_RATIO), BM_SETCHECK, BST_CHECKED, 0)

            hwnd_combo = user32.GetDlgItem(hwnd, IDC_COMBO_METHOD)
            for f in RESAMPLE_FILTERS:
                user32.SendMessageW(hwnd_combo, CB_ADDSTRING, 0, f)
            user32.SendMessageW(hwnd_combo, CB_SETCURSEL, RESAMPLE_FILTERS.index('Bicubic'), 0)

#                user32.SendMessageW(hwnd, WM_CHANGEUISTATE, MAKELONG(UIS_SET, UISF_HIDEFOCUS), 0)

            # The dialog box procedure should return TRUE to direct the system to set the keyboard focus to the control specified by wparam.
            # Otherwise, it should return FALSE to prevent the system from setting the default keyboard focus.
            return TRUE

        elif msg == WM_COMMAND:
            control_id = LOWORD(wparam)
            command = HIWORD(wparam)

            if command == BN_CLICKED:
                if control_id == IDOK:

                    buf = create_unicode_buffer(8)
                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_WIDTH), buf, 8)
                    w = int(buf.value)
                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_HEIGHT), buf, 8)
                    h = int(buf.value)
                    if not ctx.is_pixels:
                        w, h = round(main.img.width * w / 100), round(main.img.height * h / 100)

                    resample = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_COMBO_METHOD), CB_GETCURSEL, 0, 0)
                    #resample = getattr(Image.Resampling, RESAMPLE_FILTERS[resample].upper())
                    sharpen = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_CHECKBOX_SHARPEN), BM_GETCHECK, 0, 0)
                    callback((w, h), resample, sharpen)

                    user32.EndDialog(hwnd, 0)

                elif control_id == IDCANCEL:
                    user32.EndDialog(hwnd, 0)

                elif control_id == IDC_RADIO_PIXELS:
                    ctx.is_pixels = True

                elif control_id == IDC_RADIO_PCT:
                    ctx.is_pixels = False

                elif control_id == IDC_CHECKBOX_PRESERVE_RATIO:
                    ctx.preserve = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_CHECKBOX_PRESERVE_RATIO), BM_GETCHECK, 0, 0)

            elif command == EN_CHANGE:

                if control_id == IDC_EDIT_WIDTH:
                    buf = create_unicode_buffer(8)
                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_WIDTH), buf, 8)
                    if buf.value:
                        w = int(buf.value)
                        if ctx.is_pixels and w > MAX_SIZE:
                            w = MAX_SIZE
                            user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_WIDTH), str(w))

                        if ctx.preserve:
                            h = round(w * main.img.height / main.img.width)
                            user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_HEIGHT), str(h))

                elif control_id == IDC_EDIT_HEIGHT:
                    buf = create_unicode_buffer(8)
                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_HEIGHT), buf, 8)
                    if buf.value:
                        h = int(buf.value)
                        if ctx.is_pixels and h > MAX_SIZE:
                            h = MAX_SIZE
                            user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_HEIGHT), str(h))

                        if ctx.preserve:
                            w = round(h * main.img.width / main.img.height)
                            user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT_WIDTH), str(w))

        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, 0)

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_RESIZE_IMAGE),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )
