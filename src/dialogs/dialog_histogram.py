from ctypes import *

from winapp.const import *
from winapp.dialog import *
from winapp.dlls import gdi32, user32
from winapp.wintypes_extended import *

from const import HMOD_RESOURCES
from resources import *

MARGIN = 12

########################################
#
########################################
def show(main):

    if main.img.mode == 'P':
        img_converted = main.img.convert('RGB')

    ctx = {}

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
#            if main.is_dark:
#                DarkDialogInit(hwnd)
            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)

            user32.SetWindowPos(hwnd, NULL, 0, 0, 2 * MARGIN + 512 + 16, MARGIN + 310, SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)

            user32.SetWindowPos(user32.GetDlgItem(hwnd, IDCANCEL), NULL,
                MARGIN + 514 - 90,
                251,
                0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)

            user32.SendDlgItemMessageW(hwnd, IDC_HIST_RBN_GRAY, BM_SETCHECK, BST_CHECKED, 0)

            if main.img.mode in ('L', 'LA', '1'):
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_HIST_RBN_R), FALSE)
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_HIST_RBN_G), FALSE)
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_HIST_RBN_B), FALSE)
                if main.img.mode != 'LA':
                    user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_HIST_RBN_A), FALSE)

            elif main.img.mode == 'CMYK':
                user32.SetDlgItemTextW(hwnd, IDC_HIST_RBN_R, 'Cyan')
                user32.SetDlgItemTextW(hwnd, IDC_HIST_RBN_G, 'Magenta')
                user32.SetDlgItemTextW(hwnd, IDC_HIST_RBN_B, 'Yellow')
                user32.SetDlgItemTextW(hwnd, IDC_HIST_RBN_A, 'Black')

            elif main.img.mode == 'RGB':
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_HIST_RBN_A), FALSE)

            elif main.img.mode == 'P':
                user32.SetDlgItemTextW(hwnd, IDC_HIST_RBN_A, 'Index')

            if main.is_dark:
                DarkDialogInit(hwnd)

            histogram = main.img.convert('L').histogram()
            mx = max(histogram)
            ctx['histogram'] = [int(c * 200 / mx) for c in histogram]

        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, 0)

        elif msg == WM_PAINT:

            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, byref(ps))

            rc = RECT(MARGIN, 24, MARGIN + 512, 244)
            user32.FillRect(hdc, byref(rc), gdi32.GetStockObject(BLACK_BRUSH if main.is_dark else WHITE_BRUSH))

            user32.InflateRect(byref(rc), 1, 1)
            user32.FrameRect(hdc, byref(rc), DARK_BORDER_BRUSH if main.is_dark else BORDER_BRUSH)

            gdi32.SelectObject(hdc, gdi32.GetStockObject(WHITE_PEN if main.is_dark else BLACK_PEN))
            y = 239 + 4

            for x in range(256):
                gdi32.MoveToEx(hdc, MARGIN + 2*x, y, None)
                gdi32.LineTo(hdc, MARGIN + 2*x, y - ctx['histogram'][x])

            user32.EndPaint(hwnd, byref(ps))
            return FALSE

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)

            if command == BN_CLICKED:
                control_id = LOWORD(wparam)

                if control_id == IDC_HIST_RBN_GRAY:
                    histogram = main.img.convert('L').histogram()
                    mx = max(histogram)
                    ctx['histogram'] = [int(c * 200 / mx) for c in histogram]
                    user32.RedrawWindow(hwnd, 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)

                elif control_id == IDC_HIST_RBN_R:
                    if main.img.mode == 'P':
                        histogram = img_converted.getchannel('R').histogram()
                    else:
                        histogram = main.img.getchannel('C' if main.img.mode == 'CMYK' else "R").histogram()

                    mx = max(histogram)
                    ctx['histogram'] = [int(c * 200 / mx) for c in histogram]
                    user32.RedrawWindow(hwnd, 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)

                elif control_id == IDC_HIST_RBN_G:
                    if main.img.mode == 'P':
                        histogram = img_converted.getchannel('G').histogram()
                    else:
                        histogram = main.img.getchannel('M' if main.img.mode == 'CMYK' else "G").histogram()
                    mx = max(histogram)
                    ctx['histogram'] = [int(c * 200 / mx) for c in histogram]
                    user32.RedrawWindow(hwnd, 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)

                elif control_id == IDC_HIST_RBN_B:
                    if main.img.mode == 'P':
                        histogram = img_converted.getchannel('B').histogram()
                    else:
                        histogram = main.img.getchannel('Y' if main.img.mode == 'CMYK' else "B").histogram()
                    mx = max(histogram)
                    ctx['histogram'] = [int(c * 200 / mx) for c in histogram]
                    user32.RedrawWindow(hwnd, 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)

                elif control_id == IDC_HIST_RBN_A:
                    if main.img.mode == 'P':
                        histogram = main.img.histogram()
                    else:
                        histogram = main.img.getchannel('K' if main.img.mode == 'CMYK' else "A").histogram()
                    mx = max(histogram)
                    ctx['histogram'] = [int(c * 200 / mx) for c in histogram]
                    user32.RedrawWindow(hwnd, 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)

                elif control_id == IDCANCEL:
                    user32.EndDialog(hwnd, 0)

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_HISTOGRAM),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )
