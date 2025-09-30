from ctypes import *

from PIL import Image, ImageEnhance, ImageFilter

from winapp.const import *
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from canvas import *
from const import *
from image import *
from resources import *

MAX_IMG_SIZE = 256
MARGIN = 9

########################################
#
########################################
def show(main):
    img = main.img

    ctx = {}
    controls = {}

    alpha = None
    if img.mode in ('CMYK', 'P', 'L', '1'):
        img = img.convert('RGB')
    elif img.mode == 'PA':
        alpha = img.getchannel("A")
        img = img.convert('RGB')
    elif img.mode == 'LA':
        alpha = img.getchannel("A")
        img = img.convert('RGB')
    elif img.mode == 'RGBA':
        alpha = img.getchannel("A")







#    if main.img.width <= MAX_IMG_SIZE and main.img.height <= MAX_IMG_SIZE:
#        img_preview = main.img.copy()
#    else:
#        r = main.img.width / main.img.height
#        if r > 1:
#            size = (MAX_IMG_SIZE, int(MAX_IMG_SIZE / r))
#        else:
#            size = (int(MAX_IMG_SIZE * r), MAX_IMG_SIZE)
#        img_preview = main.img.resize(size)



    if img.width <= MAX_IMG_SIZE and img.height <= MAX_IMG_SIZE:
        img_preview = img.copy()
        alpha_preview = alpha
    else:
        r = img.width / img.height
        if r > 1:
            size = (MAX_IMG_SIZE, int(MAX_IMG_SIZE / r))
        else:
            size = (int(MAX_IMG_SIZE * r), MAX_IMG_SIZE)
        img_preview = img.resize(size)
        alpha_preview  = alpha.resize(size) if alpha else None
        if alpha_preview:
            img_preview.putalpha(alpha_preview)

    ctx['alpha'] = alpha
#    alpha_preview = img_preview.getchannel("A") if "A" in img_preview.getbands() else None





#    if img_preview.mode in ('1', 'L', 'P', 'CMYK'):
#        img_preview = img_preview.convert('RGB')
#
#    elif img_preview.mode == 'LA':
#        img_preview = img_preview.convert('RGBA')

    img_black = Image.new('L', img_preview.size, 0)
    img_white = Image.new('L', img_preview.size, 255)

#    if "A" in img_preview.getbands():
#        img_black.putalpha(img_preview.getchannel("A"))
#        img_white.putalpha(img_preview.getchannel("A"))

#    alpha = img_preview.getchannel("A") if img_preview.mode == 'RGBA' else None
#    bg = Image.new('RGBA', img_preview.size, CR_TO_RGB(main.state['bg_color'])) if img_preview.mode == 'RGBA' else None



    ########################################
    #
    ########################################
    def _update_layout(width, height):
#        w =

        ctx['canvas'].set_window_pos(
            x = MARGIN,
            y = 3,
            width = width - 2 * MARGIN,
            height = height - MARGIN - 140,
            flags = SWP_NOACTIVATE | SWP_NOZORDER
        )

        y = height - 24 - MARGIN - 95

        for c in ('R', 'G', 'B'):
            user32.SetWindowPos(
                controls[eval(f'IDC_STATIC_{c}')], NULL,
                MARGIN + 5,
                y + 3,
                0, 0,
                SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
            )
            user32.SetWindowPos(
                controls[eval(f'IDC_SLIDER_{c}')], NULL,
                MARGIN + 20,
                y,
                width - 3 * MARGIN - 50, 20,
                SWP_NOACTIVATE | SWP_NOZORDER
            )
            user32.SetWindowPos(
                controls[eval(f'IDC_EDIT_{c}')], NULL,
                width - MARGIN - 30,
                y,
                0, 0,
                SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
            )
            y += 30

        y = height - 24 - MARGIN
        user32.SetWindowPos(controls[IDC_BTN_RESET], NULL, MARGIN, y, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER)
        user32.SetWindowPos(controls[IDOK], NULL, width - MARGIN - 2 * 90 - 5, y, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER)
        user32.SetWindowPos(controls[IDCANCEL], NULL, width - MARGIN - 90, y, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER)

        ctx['win'].redraw_window()

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
            if main.is_dark:
                DarkDialogInit(hwnd)
            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)

            ctx['win'] = Window(wrap_hwnd=hwnd)
            ctx['canvas'] = Canvas(ctx['win'], bgcolor=main.state['bg_color'])

            def _enum_child_func(hwnd_child, lparam):
                control_id = user32.GetDlgCtrlID(hwnd_child)
                if control_id > 0:
                    controls[control_id] = hwnd_child
                return TRUE
            user32.EnumChildWindows(hwnd, WNDENUMPROC(_enum_child_func), 0)

            rc = RECT()
            user32.GetClientRect(hwnd, byref(rc))
            _update_layout(rc.right, rc.bottom)

            ctx['canvas'].load_hbitmap(image_to_hbitmap(img_preview), zoom_to_fit=True)
            for c in ('R', 'G', 'B'):
                user32.SendDlgItemMessageW(hwnd, eval(f'IDC_SLIDER_{c}'), TBM_SETRANGEMAX, FALSE, 200)
                user32.SendDlgItemMessageW(hwnd, eval(f'IDC_SLIDER_{c}'), TBM_SETPOS, TRUE, 100)
                ctx[c] = img_preview.getchannel(c)

        elif msg == WM_SIZE:
            _update_layout(lparam & 0xFFFF, (lparam >> 16) & 0xFFFF)

        elif msg == WM_GETMINMAXINFO:
            mmi = cast(lparam, POINTER(MINMAXINFO))
            mmi.contents.ptMinTrackSize = POINT(340, 340)
            return 0

        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, 0)

        elif msg == WM_HSCROLL:
            lo, val, = wparam & 0xFFFF, (wparam >> 16) & 0xFFFF
            if lo == TB_ENDTRACK:
                return 0
            if lo == TB_PAGEDOWN or lo == TB_PAGEUP: # clicked into slider
                pt = POINT()
                user32.GetCursorPos(byref(pt))
                rc = RECT()
                user32.GetWindowRect(lparam, byref(rc))
                val = int((pt.x - rc.left - 10) / (rc.right - rc.left - 20) * 200)
                user32.SendMessageW(lparam, TBM_SETPOS, 1, val)
            else:
                val = SHORT(val).value

            for c in ('R', 'G', 'B'):
                if lparam == controls[eval(f'IDC_SLIDER_{c}')]:
                    user32.SetDlgItemTextW(hwnd, eval(f'IDC_EDIT_{c}'), f'{val - 100}')
                    if val <= 100:
                        ctx[c] = Image.blend(img_black, img_preview.getchannel(c), val / 100)
                    else:
                        ctx[c] = Image.blend(img_white, img_preview.getchannel(c), (200 - val) / 100)
                    break

            if alpha_preview:
                img = Image.merge("RGBA", [ctx['R'], ctx['G'], ctx['B'], alpha_preview])
            else:
                img = Image.merge("RGB", [ctx['R'], ctx['G'], ctx['B']])

            ctx['canvas'].update_hbitmap(image_to_hbitmap(img))

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)

            if command == BN_CLICKED:
                control_id = LOWORD(wparam)

                if control_id == IDOK:
                    black = Image.new('L', main.img.size, 0)
                    white = Image.new('L', main.img.size, 255)

                    m = main.img.mode
#                    if m in ('1', 'L', 'P', 'CMYK'):
#                        img = main.img.convert('RGB')
#                    elif m == 'LA':
#                        img = main.img.convert('RGBA')
#                    else:
#                        img = main.img

                    img = main.img

                    if img.mode in ('CMYK', 'L', 'P', 'LA', 'PA', '1'):
                        img = img.convert('RGB')

                    # img.mode is now either RGB or RGBA

                    channels = []
                    for c in ('R', 'G', 'B'):
                        val = user32.SendDlgItemMessageW(hwnd, eval(f'IDC_SLIDER_{c}'), TBM_GETPOS, 0, 0)
                        if val <= 100:
                            channels.append(Image.blend(black, img.getchannel(c), val / 100))
                        else:
                            channels.append(Image.blend(white, img.getchannel(c), (200 - val) / 100))

#                    if m in ('RGBA', 'LA'):
#                        channels.append(img.getchannel('A'))

                    main.img = Image.merge('RGB', channels)

                    if m == 'CMYK':
                        main.img = main.img.convert('CMYK')

                    elif m in ('LA', 'RGBA'):
                        main.img.putalpha(ctx['alpha'])

                    elif m == 'PA':
                        main.img = main.img.convert('P', palette=Image.ADAPTIVE, dither=Image.Dither.NONE)
                        main.img.putalpha(ctx['alpha'])

                    elif m in ('1', 'L', 'P'):
                        main.img = main.img.convert('P', palette=Image.ADAPTIVE, dither=Image.Dither.NONE)

                    if ctx['alpha']:
                        channels.append(ctx['alpha'])

#                    img = Image.merge(img.mode, channels)

#                    elif m in ('1', 'L', 'P'):
#                        main.img = img.convert('P', palette=Image.ADAPTIVE, dither=Image.Dither.NONE)
#
#                    else:
#                        main.img = img

                    if m in ('1', 'L', 'LA'):  # mode has changed
                        main.update_menus()
                        main.update_status_infos()

                    main.undo_stack.push(main.img)
                    main.canvas.update_hbitmap(image_to_hbitmap(main.img))

                    user32.EndDialog(hwnd, 0)

                elif control_id == IDCANCEL:
                    user32.EndDialog(hwnd, 0)

                elif control_id == IDC_BTN_RESET:
                    for c in ('R', 'G', 'B'):
                        user32.SendDlgItemMessageW(hwnd, eval(f'IDC_SLIDER_{c}'), TBM_SETPOS, TRUE, 100)
                        user32.SetDlgItemTextW(hwnd, eval(f'IDC_EDIT_{c}'), '0')
                    ctx['canvas'].update_hbitmap(image_to_hbitmap(img_preview))

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_COLOR_BALANCE),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )
