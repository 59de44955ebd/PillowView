from ctypes import *
import os

from winapp.const import *
from winapp.dialog import *
from winapp.dlls import gdi32, user32
from winapp.wintypes_extended import *

from const import HMOD_RESOURCES, APP_DIR
from image import *
from resources import *

MARGIN = 12

MIN_DISTANCE = 16

# More samples means smoother curve but longer processing
SAMPLE_SIZE = 256

##########
ts = CDLL(os.path.join(APP_DIR, 'tinyspline.dll'))
ts.ts_bspline_interpolate_cubic_natural.argtypes = (POINTER(c_double), c_size_t, c_size_t, c_void_p, c_void_p)  #POINTER(tsStatus)
ts.ts_bspline_sample.argtypes = (c_void_p, c_size_t, POINTER(POINTER(c_double)), POINTER(c_size_t), c_void_p)  #POINTER(tsStatus)
ts.ts_bspline_bisect.argtypes = (c_void_p, c_double, c_double, c_long, c_size_t, c_long, c_size_t, c_void_p, c_void_p)  #POINTER(tsStatus)
ts.ts_deboornet_result.argtypes = (c_void_p, POINTER(POINTER(c_double)), c_void_p)  #POINTER(tsStatus)
ts.ts_bspline_free.argtypes = (c_void_p,)
ts.ts_deboornet_free.argtypes = (c_void_p,)

########################################
#
########################################
def bspline_interpolate_cubic_natural(points):
    points_d = (c_double * len(points))(*points)
    spline = c_void_p()
    res = ts.ts_bspline_interpolate_cubic_natural(
        points_d,
        len(points) // 2,
        2,
        byref(spline),
        None
    )
    #print(res)
    if res == 0:
        return spline

########################################
#
########################################
def spline_sample(spline, sample_size):
    actual_num = c_size_t()
    points = POINTER(c_double)()
    res = ts.ts_bspline_sample(
        byref(spline),
        sample_size,
        byref(points),
        byref(actual_num),
        None
    )
    if res == 0:
        return points

########################################
#
########################################
def get_lut(spline):
    result = POINTER(c_double)()
    net = c_void_p()

    def _get(x):
        ts.ts_bspline_bisect(
            byref(spline), x,
            0.0, 0, 0, 1, 50,
            byref(net),
            None
        )
        ts.ts_deboornet_result(
            byref(net),
            byref(result),
            None
        )
        return result[1]

    lut = [round(_get(x)) for x in range(256)]
    ts.ts_deboornet_free(byref(net))
    return lut

########################################
#
########################################
def show(main):

    if main.img.mode == 'P':
        img_input = main.img.convert('RGB')
    elif main.img.mode == '1':
        img_input = main.img.convert('L')
    else:
        img_input = main.img

    x_left = MARGIN
    x_right = x_left + 256

    y_top = 34
    y_bottom = y_top + 256

    class ctx():
        img = main.img
        down = False
        channel = None
        x = [0, 255]
        y = [0, 255]
        idx = None


    ctx.spline = bspline_interpolate_cubic_natural([0, 0, 255, 255])
    ctx.points = spline_sample(ctx.spline, SAMPLE_SIZE)

    rc_curve = RECT(MARGIN, y_top, MARGIN + 256, y_top + 256)
    color_curve = 0xFFFFFF if main.is_dark else 0x000000
    hbr_curve = gdi32.GetStockObject(WHITE_BRUSH if main.is_dark else BLACK_BRUSH)
    hbr_bg = gdi32.GetStockObject(BLACK_BRUSH if main.is_dark else WHITE_BRUSH)
    hbr_border = DARK_BORDER_BRUSH if main.is_dark else BORDER_BRUSH
    hpen_grid = gdi32.CreatePen(PS_SOLID, 1, DARK_BORDER_COLOR if main.is_dark else BORDER_COLOR)

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
            if main.is_dark:
                DarkDialogInit(hwnd)
            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)

            h =  MARGIN + 256 + 100 + 20
            user32.SetWindowPos(hwnd, NULL, 0, 0, 2 * MARGIN + 256 + 16, h, SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)

            user32.SetWindowPos(user32.GetDlgItem(hwnd, IDC_BTN_RESET), NULL,
                MARGIN,
                h - 70,
                0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)

            user32.SetWindowPos(user32.GetDlgItem(hwnd, IDOK), NULL,
                MARGIN + 256 - 2 * 75 - 3,
                h - 70,
                0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)

            user32.SetWindowPos(user32.GetDlgItem(hwnd, IDCANCEL), NULL,
                MARGIN + 256 - 75 + 2,
                h - 70,
                0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)

            if img_input.mode in ('RGB', 'RGBA'):
                for s in ('RGB', 'Red', 'Green', 'Blue'):
                    user32.SendDlgItemMessageW(hwnd, IDC_GRADATION_COMBO_CHANNEL, CB_ADDSTRING, 0, s)
                user32.SendDlgItemMessageW(hwnd, IDC_GRADATION_COMBO_CHANNEL, CB_SETCURSEL, 0, 0)

            elif img_input.mode  == 'CMYK':
                for s in ('CMYK', 'Cyan', 'Magenta', 'Yellow', 'Black'):
                    user32.SendDlgItemMessageW(hwnd, IDC_GRADATION_COMBO_CHANNEL, CB_ADDSTRING, 0, s)
                user32.SendDlgItemMessageW(hwnd, IDC_GRADATION_COMBO_CHANNEL, CB_SETCURSEL, 0, 0)

            else:
                user32.EnableWindow(user32.GetDlgItem(hwnd, IDC_GRADATION_COMBO_CHANNEL), 0)

#            if main.is_dark:
#                DarkDialogInit(hwnd)

        elif msg == WM_CLOSE:
            main.canvas.update_hbitmap(image_to_hbitmap(main.img))
            user32.EndDialog(hwnd, 0)

        elif msg == WM_LBUTTONDOWN:
            x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
            if (x_left <= x < x_right) and (y_top < y <= y_bottom):
                x, y = x - x_left, y_bottom - y

                if len(ctx.x) > 2:
                    closest = min(ctx.x[1:-1], key=lambda v: abs(v - x))
                    if abs(closest - x) < MIN_DISTANCE:
                        ctx.idx = ctx.x.index(closest)
                        ctx.x[ctx.idx], ctx.y[ctx.idx] = x, y
                    else:
                        idx = ctx.x.index(closest)
                        ctx.idx = idx + 1 if x > closest else idx
                        ctx.x.insert(ctx.idx, x)
                        ctx.y.insert(ctx.idx, y)
                else:
                    ctx.idx = 1
                    ctx.x.insert(ctx.idx, x)
                    ctx.y.insert(ctx.idx, y)

                points = [sub[item] for item in range(len(ctx.y)) for sub in [ctx.x, ctx.y]]

                ts.ts_bspline_free(byref(ctx.spline))
                ctx.spline = bspline_interpolate_cubic_natural(points)
                ctx.points = spline_sample(ctx.spline, SAMPLE_SIZE)

                user32.InvalidateRect(hwnd, byref(rc_curve), TRUE)
                user32.SetCapture(hwnd)
                ctx.down = True

        elif msg == WM_MOUSEMOVE:
            if not ctx.down:
                return FALSE
            x, y = GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam)
            if (x_left <= x < x_right) and (y_top < y <= y_bottom):
                x, y = x - x_left, y_bottom - y

                ctx.x[ctx.idx], ctx.y[ctx.idx] = max(ctx.x[ctx.idx - 1] + 1, min(ctx.x[ctx.idx + 1] - 1, x)), y

                points = [sub[item] for item in range(len(ctx.y)) for sub in [ctx.x, ctx.y]]

                ts.ts_bspline_free(byref(ctx.spline))
                ctx.spline = bspline_interpolate_cubic_natural(points)
                ctx.points = spline_sample(ctx.spline, SAMPLE_SIZE)

                user32.InvalidateRect(hwnd, byref(rc_curve), TRUE)

        elif msg == WM_LBUTTONUP:
            ctx.down = False
            user32.ReleaseCapture(hwnd)

            x, y = GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam)
            if (x_left <= x < x_right) and (y_top < y <= y_bottom):
                lut = get_lut(ctx.spline)
                if ctx.channel:
                    ctx.channels[ctx.channel] = img_input.getchannel(ctx.channel).point(lambda c: lut[c])
                    ctx.img = Image.merge(img_input.mode, list(ctx.channels.values()))
                else:
                    ctx.img = img_input.point(lambda c: lut[c])
                main.canvas.update_hbitmap(image_to_hbitmap(ctx.img))

        elif msg == WM_RBUTTONDOWN:
            if len(ctx.x) > 2:
                x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
                if (x_left <= x < x_right) and (y_top < y <= y_bottom):
                    x, y = x - x_left, y_bottom - y
                    closest = min(ctx.x[1:-1], key=lambda v: abs(v - x))
                    if abs(closest - x) < MIN_DISTANCE:
                        idx = ctx.x.index(closest)
                        ctx.x.pop(idx)
                        ctx.y.pop(idx)

                        points = [sub[item] for item in range(len(ctx.y)) for sub in [ctx.x, ctx.y]]

                        ts.ts_bspline_free(byref(ctx.spline))
                        ctx.spline = bspline_interpolate_cubic_natural(points)
                        ctx.points = spline_sample(ctx.spline, SAMPLE_SIZE)

                        user32.InvalidateRect(hwnd, byref(rc_curve), TRUE)

                        lut = get_lut(ctx.spline)

                        if ctx.channel:
                            ctx.channels[ctx.channel] = img_input.getchannel(ctx.channel).point(lambda c: lut[c])
                            ctx.img = Image.merge(img_input.mode, list(ctx.channels.values()))
                        else:
                            ctx.img = img_input.point(lambda c: lut[c])
                        main.canvas.update_hbitmap(image_to_hbitmap(ctx.img))

        elif msg == WM_PAINT:

            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, byref(ps))

            rc = RECT(MARGIN, y_top, MARGIN + 256, y_top + 256)

            # BG
            user32.FillRect(hdc, byref(rc), hbr_bg)

            # Border
            user32.InflateRect(byref(rc), 1, 1)
            user32.FrameRect(hdc, byref(rc), hbr_border)

            # Grid
            gdi32.SelectObject(hdc, hpen_grid)
            for x in range(64, 255, 64):
                gdi32.MoveToEx(hdc, MARGIN + x, y_top, None)
                gdi32.LineTo(hdc, MARGIN + x, y_top + 256)
            for y in range(64, 255, 64):
                gdi32.MoveToEx(hdc, MARGIN, y_top + y, None)
                gdi32.LineTo(hdc, MARGIN + 256, y_top + y)

            # Curve
            for i in range(0, SAMPLE_SIZE * 2, 2):
                gdi32.SetPixel(
                    hdc,
                    MARGIN + max(0, min(255, round(ctx.points[i]))),
                    y_bottom - max(0, min(255, round(ctx.points[i + 1]))) - 1,
                    color_curve
                )

            # Dots
            for i in range(1, len(ctx.x) - 1):
                x, y = MARGIN + ctx.x[i], y_bottom - ctx.y[i]
                user32.FillRect(hdc, byref(RECT(x - 2, y - 3, x + 3, y + 2)), hbr_curve)

            user32.EndPaint(hwnd, byref(ps))
            return FALSE

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)

            if command == BN_CLICKED:
                control_id = LOWORD(wparam)
                if control_id == IDOK:
                    if main.img.mode == 'P':
                        ctx.img = ctx.img.convert(
                            'P',
                            palette=Image.ADAPTIVE,
                            dither=Image.Dither.NONE
                        )

                    main.img = ctx.img
                    main.undo_stack.push(main.img)
                    user32.EndDialog(hwnd, 1)

                elif control_id == IDCANCEL:
                    main.canvas.update_hbitmap(image_to_hbitmap(main.img))
                    user32.EndDialog(hwnd, 0)

                elif control_id == IDC_BTN_RESET:

                    ctx.x = [0, 255]
                    ctx.y = [0, 255]

                    points = [sub[item] for item in range(len(ctx.y)) for sub in [ctx.x, ctx.y]]

                    ts.ts_bspline_free(byref(ctx.spline))
                    ctx.spline = bspline_interpolate_cubic_natural([0, 0, 255, 255])
                    ctx.points = spline_sample(ctx.spline, SAMPLE_SIZE)

                    user32.InvalidateRect(hwnd, byref(rc_curve), TRUE)

                    main.canvas.update_hbitmap(image_to_hbitmap(img_input))

            elif command == CBN_SELCHANGE:
                channel = user32.SendDlgItemMessageW(hwnd, IDC_GRADATION_COMBO_CHANNEL, CB_GETCURSEL, 0, 0)
                if channel == 0:
                    ctx.channel = None
                else:
                    channels = ['C', 'M', 'Y', 'K'] if img_input.mode == 'CMYK' else ['R', 'G', 'B']
                    ctx.channel = channels[channel - 1]
                    ctx.channels = {c: img_input.getchannel(c) for c in img_input.mode}

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_GRADATION_CURVE),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )

    gdi32.DeleteObject(hpen_grid)
    ts.ts_bspline_free(byref(ctx.spline))
