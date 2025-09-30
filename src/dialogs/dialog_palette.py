from ctypes import *
import io

from winapp.const import *
from winapp.controls.common import *
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from const import *
from image import *
from resources import *

########################################
#
########################################
def show(main):
    if main.img is None:
        return

    img = main.img.copy()

    pal = img.getpalette()

    num_colors = len(pal) // 3

    if 'transparency' in img.info:
        trans = img.info['transparency']
        pal[trans * 3:trans * 3 + 3] = img.info['transcolor']
    else:
        trans= -1

    ctx = {
        'idx_selected': -1,
        'idx_selected_old': -1,
        'palette': [RGB_TO_CR(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)],
        'trans': trans
    }

    ########################################
    #
    ########################################
    def _static_proc_callback(hwnd, msg, wparam, lparam, uIdSubclass, dwRefData):
        if msg == WM_PAINT:
            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, byref(ps))

            if ctx['idx_selected_old'] > -1:
                x = 5 + ctx['idx_selected_old'] % 16 * 20
                y = 5 + ctx['idx_selected_old'] // 16 * 20
                rc = RECT(x - 2, y - 2, x + 18, y + 18)
                user32.FrameRect(hdc, byref(rc), DARK_BG_BRUSH if main.is_dark else COLOR_3DFACE + 1)
                user32.InflateRect(byref(rc), 1, 1)
                user32.FrameRect(hdc, byref(rc), DARK_BG_BRUSH if main.is_dark else COLOR_3DFACE + 1)
                ctx['idx_selected_old'] = -1

            x, y = 5, 5

            for idx in range(len(ctx['palette'])):
                if idx == ctx['idx_selected']:
                    rc = RECT(x - 2, y - 2, x + 18, y + 18)
                    hbr = gdi32.CreateSolidBrush(0x0000FF)
                    user32.FrameRect(hdc, byref(rc), hbr)
                    user32.InflateRect(byref(rc), 1, 1)
                    user32.FrameRect(hdc, byref(rc), hbr)
                    gdi32.DeleteObject(hbr)

                rc = RECT(x, y, x + 16, y + 16)
                hbr = gdi32.CreateSolidBrush(ctx['palette'][idx])
                user32.FillRect(hdc, byref(rc), hbr)
                gdi32.DeleteObject(hbr)

                if idx == ctx['trans']:
                    user32.FrameRect(hdc, byref(rc), gdi32.GetStockObject(WHITE_BRUSH if main.is_dark else BLACK_BRUSH))
                    user32.InflateRect(byref(rc), -1, -1)
                    user32.FrameRect(hdc, byref(rc), gdi32.GetStockObject(BLACK_BRUSH if main.is_dark else WHITE_BRUSH))
                    user32.InflateRect(byref(rc), -1, -1)
                    user32.FrameRect(hdc, byref(rc), gdi32.GetStockObject(WHITE_BRUSH if main.is_dark else BLACK_BRUSH))
                    user32.InflateRect(byref(rc), -1, -1)
                    user32.FrameRect(hdc, byref(rc), gdi32.GetStockObject(BLACK_BRUSH if main.is_dark else WHITE_BRUSH))

#                    user32.InflateRect(byref(rc), -4, -4)
#                    user32.FillRect(hdc, byref(rc), DARK_BG_BRUSH if main.is_dark else COLOR_3DFACE + 1)
#                    user32.FillRect(hdc, byref(rc), gdi32.GetStockObject(WHITE_BRUSH if main.is_dark else BLACK_BRUSH))

                if idx % 16 == 15:
                    x = 5
                    y += 20
                else:
                    x += 20

            user32.EndPaint(hwnd, byref(ps))
            return FALSE

        return comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)

    static_proc_callback = SUBCLASSPROC(_static_proc_callback)

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):
        if msg == WM_INITDIALOG:
            if main.is_dark:
                DarkDialogInit(hwnd)
            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)

            ctx['hwnd_dialog'] = hwnd
            ctx['hwnd_static'] = user32.GetDlgItem(hwnd, 1781)
            ctx['hwnd_index'] = user32.GetDlgItem(hwnd, 1779)
            ctx['hwnd_value'] = user32.GetDlgItem(hwnd, 1780)
            comctl32.SetWindowSubclass(ctx['hwnd_static'], static_proc_callback, 1, 0)

        elif msg == WM_CLOSE:
            main.canvas.update_hbitmap(image_to_hbitmap(main.img))
            user32.EndDialog(hwnd, 0)

        elif msg == WM_LBUTTONDOWN:
            x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
            pt = POINT(x, y)
            user32.MapWindowPoints(hwnd, ctx['hwnd_static'], byref(pt), 1)
            idx_selected = (pt.y - 5) // 20 * 16 + (pt.x - 5) // 20
            if idx_selected >= 0 and idx_selected < len(ctx['palette']) and idx_selected != ctx['idx_selected']:
                ctx['idx_selected_old'] = ctx['idx_selected']
                ctx['idx_selected'] = idx_selected
                user32.RedrawWindow(ctx['hwnd_static'], 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)
                user32.SetWindowTextW(ctx['hwnd_index'], f'Index: {idx_selected}')
                r, g, b = CR_TO_RGB(ctx['palette'][idx_selected])
                user32.SetWindowTextW(ctx['hwnd_value'], f'Value: RGB({r}, {g}, {b})')

        elif msg == WM_LBUTTONDBLCLK:
            x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
            pt = POINT(x, y)
            user32.MapWindowPoints(hwnd, ctx['hwnd_static'], byref(pt), 1)
            idx = (pt.y - 5) // 20 * 16 + (pt.x - 5) // 20
            if idx >= 0 and idx < len(ctx['palette']):
                col = main.show_color_dialog(ctx['palette'][idx])
                if col is not None and col != ctx['palette'][idx]:
                    ctx['palette'][idx] = col
                    user32.RedrawWindow(ctx['hwnd_static'], 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)

        elif msg == WM_RBUTTONDOWN:
            x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
            pt = POINT(x, y)
            user32.MapWindowPoints(hwnd, ctx['hwnd_static'], byref(pt), 1)
            idx = (pt.y - 5) // 20 * 16 + (pt.x - 5) // 20
            if idx >= 0 and idx < len(ctx['palette']):

                ctx['trans'] = -1 if idx == ctx['trans'] else idx
                user32.RedrawWindow(ctx['hwnd_static'], 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)

        elif msg == WM_COMMAND:
            notification_code = HIWORD(wparam)
            if notification_code == BN_CLICKED:
                control_id = LOWORD(wparam)

                if control_id == IDCANCEL:
                    main.canvas.update_hbitmap(image_to_hbitmap(main.img))
                    user32.EndDialog(hwnd, 0)

                elif control_id == IDC_BTN_APPLY:
                    pal = [x for c in ctx['palette'] for x in CR_TO_RGB(c)]
                    if ctx['trans'] > -1:
                        pal[ctx['trans'] * 3:ctx['trans'] * 3 + 3] = CR_TO_RGB(main.state['bg_color'])
                    img.putpalette(pal)
                    main.canvas.update_hbitmap(image_to_hbitmap(img))

                elif control_id == IDOK:
                    pal = [x for c in ctx['palette'] for x in CR_TO_RGB(c)]
                    if ctx['trans'] > -1:
                        img.info['transparency'] = ctx['trans']
                        img.info['transcolor'] = pal[ctx['trans'] * 3:ctx['trans'] * 3 + 3]
                        pal[ctx['trans'] * 3:ctx['trans'] * 3 + 3] = CR_TO_RGB(main.state['bg_color'])
                    img.putpalette(pal)
                    main.canvas.update_hbitmap(image_to_hbitmap(img))
                    main.img = img
                    main.undo_stack.push(main.img)
                    user32.EndDialog(hwnd, 1)

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    rc = main.canvas.static.get_window_rect()

    def _on_timer():
        if user32.GetKeyState(VK_RBUTTON) & 0x8000 != 0:
            pt = POINT()
            user32.GetCursorPos(byref(pt))
            rc_dialog = RECT()
            user32.GetWindowRect(ctx['hwnd_dialog'], byref(rc_dialog))
            if user32.PtInRect(byref(rc_dialog), pt):
                return
            if user32.PtInRect(byref(rc), pt):
                user32.MapWindowPoints(None, main.canvas.static.hwnd, byref(pt), 1)
                idx_selected = main.img.getpixel((pt.x, pt.y))[0] if main.img.mode == 'PA' else main.img.getpixel((pt.x, pt.y))
                if idx_selected != ctx['idx_selected']:
                    ctx['idx_selected_old'] = ctx['idx_selected']
                    ctx['idx_selected'] = idx_selected
                    user32.RedrawWindow(ctx['hwnd_static'], 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)
                    user32.SetWindowTextW(ctx['hwnd_index'], f'Index: {idx_selected}')
                    r, g, b = CR_TO_RGB(ctx['palette'][idx_selected])
                    user32.SetWindowTextW(ctx['hwnd_value'], f'Value: RGB({r}, {g}, {b})')

    timer_id = main.create_timer(_on_timer, 200)

    res = user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_PALETTE_ENTRIES),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )

    main.kill_timer(timer_id)
    return res
