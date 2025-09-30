from ctypes import *
from PIL import Image

from winapp.const import *
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from const import *
from image import CR_TO_RGB
from resources import *

########################################
#
########################################
def show(main):

    ctx = {}

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
            if main.is_dark:
                DarkDialogInit(hwnd)

            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)
            user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_NEW_BTN_COLOR_RGB), BM_SETCHECK, BST_CHECKED, 0)

            hwnd_color = user32.GetDlgItem(hwnd, IDC_NEW_STATIC_BGCOLOR)
            rc = RECT()
            user32.GetClientRect(hwnd_color, byref(rc))
            ctx['hbitmap'] = gdi32.CreateBitmap(rc.right, rc.bottom, 1, 32, NULL)
            hdc = user32.GetDC(NULL)
            hdc_bitmap = gdi32.CreateCompatibleDC(hdc)
            gdi32.SelectObject(hdc_bitmap, ctx['hbitmap'])
            hbr = gdi32.CreateSolidBrush(main.state['bgcolor_new'])
            user32.FillRect(hdc_bitmap, byref(rc), hbr)
            gdi32.DeleteObject(hbr)
            gdi32.DeleteDC(hdc_bitmap)
            user32.ReleaseDC(NULL, hdc)

            user32.SendMessageW(hwnd_color, STM_SETIMAGE, IMAGE_BITMAP, ctx['hbitmap'])

        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, 0)

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)
            if command == BN_CLICKED:
                control_id = LOWORD(wparam)
                if control_id == IDOK:
                    buf = create_unicode_buffer(6)
                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_NEW_EDIT_WIDTH), buf, 6)
                    w = int(buf.value)
                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_NEW_EDIT_HEIGHT), buf, 6)
                    h = int(buf.value)
                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_NEW_EDIT_DPI_X), buf, 6)
                    dpi_x = int(buf.value)
                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_NEW_EDIT_DPI_Y), buf, 6)
                    dpi_y = int(buf.value)
                    main.dpi = (dpi_x, dpi_y)

                    img = Image.new('RGB', (w, h), color=CR_TO_RGB(main.state['bgcolor_new']))
                    main.load_image(img)
                    user32.EndDialog(hwnd, 1)

                elif control_id == IDCANCEL:
                    user32.EndDialog(hwnd, 0)

                elif control_id == IDC_NEW_BTN_BGCOLOR:
                    color = main.show_color_dialog(initial_color=main.state['bgcolor_new'])
                    if color and color != main.state['bgcolor_new']:
                        main.state['bgcolor_new'] = color
                        hwnd_color = user32.GetDlgItem(hwnd, IDC_NEW_STATIC_BGCOLOR)
                        rc = RECT()
                        user32.GetClientRect(hwnd_color, byref(rc))
                        hdc = user32.GetDC(NULL)
                        hdc_bitmap = gdi32.CreateCompatibleDC(hdc)
                        gdi32.SelectObject(hdc_bitmap, ctx['hbitmap'])
                        hbr = gdi32.CreateSolidBrush(main.state['bgcolor_new'])
                        user32.FillRect(hdc_bitmap, byref(rc), hbr)
                        gdi32.DeleteObject(hbr)
                        gdi32.DeleteDC(hdc_bitmap)
                        user32.ReleaseDC(NULL, hdc)
                        user32.SendMessageW(hwnd_color, STM_SETIMAGE, IMAGE_BITMAP, ctx['hbitmap'])

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_NEW),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )

