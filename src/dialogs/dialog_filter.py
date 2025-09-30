from ctypes import *
from math import pi, tan
from PIL import Image, ImageFilter, ImageOps

from winapp.const import *
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from canvas import *
from const import *
from image import *
from resources import *


# Supports RGBA, CMYK, RGB, LA, L
class Brightness():
    default_pos = 500
    default_display = '0'

    def __init__(self, image: Image.Image) -> None:
        self.img = image

    def enhance(self, factor: float) -> Image.Image:
        """ factor: - 1 ... 1 """
        f = factor * 255
        return self.img.point(lambda c: c + f), f'{factor:.2f}'


class Contrast():
    default_pos = 500
    default_display = '0'

    def __init__(self, image: Image.Image) -> None:
        self.img = image

    def enhance(self, factor: float) -> Image.Image:
        """ factor: - 1 ... 1 """
        f = min(128, tan((factor + 1) * pi / 4))
        return self.img.point(lambda c: 127 + (c - 127) * f), f'{factor:.2f}'


class GammaCorrection():
    default_pos = 167
    default_display = '1.00'

    def __init__(self, image: Image.Image) -> None:
        self.img = image

    def enhance(self, factor: float) -> Image.Image:
        gamma = .1 + (factor + 1)/2 * 5.4
        f = 255 ** (1 - gamma)
        return self.img.point(lambda c: c **gamma * f), f'{gamma:.2f}'


class GaussianBlur():
    default_pos = 0
    default_display = '0'

    def __init__(self, image: Image.Image) -> None:
        self.img = image

    def enhance(self, factor: float) -> Image.Image:
        radius = (factor + 1) * 2.5
        return self.img.filter(ImageFilter.GaussianBlur(radius=radius)), f'{radius:.2f}'

# Posterize
# https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.posterize
class Posterize():
    default_pos = 0
    default_display = '8'

    def __init__(self, image: Image.Image) -> None:
        if "A" in image.getbands():
            self.alpha = image.getchannel("A")
            self.img = image.convert(image.mode[:-1])
        else:
            self.img = image
            self.alpha = None

    def enhance(self, factor: float) -> Image.Image:
        bits = int(8 - (factor + 1) * 3.5)
        img = ImageOps.posterize(self.img, bits)
        if self.alpha:
            img.putalpha(self.alpha)
        return img, f'{bits}'

class Saturation():
    default_pos = 500
    default_display = '0'

    def __init__(self, image: Image.Image) -> None:
        self.img = image
        self.intermediate_mode = "L"

        if "A" in image.getbands():
            self.intermediate_mode = "LA"

        if self.intermediate_mode != image.mode:
            image = image.convert(self.intermediate_mode).convert(image.mode)
        self.degenerate = image

    def enhance(self, factor: float) -> Image.Image:
        return Image.blend(self.degenerate, self.img, factor + 1), f'{factor:.2f}'

# Solarize
# https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.solarize
class Solarize():
    default_pos = 0
    default_display = '0'

    def __init__(self, image: Image.Image) -> None:
        if "A" in image.getbands():
            self.alpha = image.getchannel("A")
            self.img = image.convert(image.mode[:-1])
        else:
            self.img = image
            self.alpha = None

    def enhance(self, factor: float) -> Image.Image:
        threshold = int(255 - (factor + 1) * 255/2)
        img = ImageOps.solarize(self.img, threshold)
        if self.alpha:
            img.putalpha(self.alpha)
        return img, f'{255 - threshold}'


class UnsharpMask():
    default_pos = 0
    default_display = '0 %'

    def __init__(self, image: Image.Image) -> None:
        self.img = image

    def enhance(self, factor: float) -> Image.Image:
        factor = (factor + 1) * 2.5
        percent = round(factor * 100)
        return self.img.filter(ImageFilter.UnsharpMask(percent=percent)), f'{percent} %'


FILTERS = {
    IDM_FILTER_PARAM_BRIGHTNESS: ('Brightness', Brightness),
    IDM_FILTER_PARAM_CONTRAST: ('Contrast', Contrast),
    IDM_FILTER_PARAM_GAMMA: ('Gamma Correction', GammaCorrection),
    IDM_FILTER_PARAM_GAUSSIAN_BLUR: ('Gaussian Blur', GaussianBlur),
    IDM_FILTER_PARAM_POSTERIZE: ('Posterize', Posterize),  # No LA
    IDM_FILTER_PARAM_SATURATION: ('Saturation', Saturation),
    IDM_FILTER_PARAM_SOLARIZE: ('Solarize', Solarize),  # No LA
    IDM_FILTER_PARAM_UNSHARP_MASK: ('Unsharp Mask', UnsharpMask),
}

MAX_IMG_SIZE = 256
MARGIN = 9

########################################
#
########################################
def show(main, filter_idm):
    img = main.img

    ctx = {}
    controls = {}

    alpha = None
    if img.mode in ('CMYK', 'P', '1'):
        img = img.convert('RGB')
    elif img.mode == 'PA':
        alpha = img.getchannel("A")
        img = img.convert('RGB')
    elif img.mode == 'LA':
        alpha = img.getchannel("A")
        img = img.convert('L')
    elif img.mode == 'RGBA':
        alpha = img.getchannel("A")

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

    filter_class = FILTERS[filter_idm][1]
    enhancer = filter_class(img_preview)

    def _update_layout(width, height):
        w = width - 2 * MARGIN

        ctx['canvas'].set_window_pos(
            x = MARGIN,
            y = 3, #MARGIN,
            width=w,
            height=height - MARGIN - 80,
            flags=SWP_NOACTIVATE | SWP_NOZORDER
        )

        user32.SetWindowPos(
            controls[IDC_FILTER_SLIDER], NULL,
            MARGIN,
            height - 24 - MARGIN - 40,
            w - MARGIN - 30, 20,
            SWP_NOACTIVATE | SWP_NOZORDER
        )
        user32.SetWindowPos(
            controls[IDC_FILTER_EDIT], NULL,
            width - MARGIN - 38,
            height - 24 - MARGIN - 40,
            0, 0,
            SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
        )

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

            user32.SetWindowTextW(hwnd, FILTERS[filter_idm][0])

            ctx['win'] = Window(wrap_hwnd=hwnd)
            ctx['canvas'] = Canvas(ctx['win'], bgcolor=main.state['bg_color'])

            def _enum_child_func(hwnd_child, lparam):
                control_id = user32.GetDlgCtrlID(hwnd_child)
                if control_id > 0:
                    controls[control_id] = hwnd_child
                return TRUE
            user32.EnumChildWindows(hwnd, WNDENUMPROC(_enum_child_func), 0)

            user32.SendDlgItemMessageW(hwnd, IDC_FILTER_SLIDER, TBM_SETRANGEMAX, FALSE, 1000)  # ws: 200
            user32.SendDlgItemMessageW(hwnd, IDC_FILTER_SLIDER, TBM_SETPOS, TRUE, filter_class.default_pos)
            user32.SetDlgItemTextW(hwnd, IDC_FILTER_EDIT, filter_class.default_display)

            rc = RECT()
            user32.GetClientRect(hwnd, byref(rc))
            _update_layout(rc.right, rc.bottom)

            ctx['canvas'].load_hbitmap(image_to_hbitmap(img_preview), zoom_to_fit=True)

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
                val = int((pt.x - rc.left - 10) / (rc.right - rc.left - 20) * 1000)
                user32.SendMessageW(lparam, TBM_SETPOS, 1, val)
            else:
                val = SHORT(val).value

            img, display = enhancer.enhance((val - 500) / 500)
            if alpha_preview:
                img.putalpha(alpha_preview)
            ctx['canvas'].update_hbitmap(image_to_hbitmap(img))
            user32.SetDlgItemTextW(hwnd, IDC_FILTER_EDIT, display) #f'{val - 100}')

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)

            if command == BN_CLICKED:
                control_id = LOWORD(wparam)

                if control_id == IDOK:
                    val = user32.SendDlgItemMessageW(hwnd, IDC_FILTER_SLIDER, TBM_GETPOS, 0, 0)

                    if val != 500:

                        if main.img.mode == 'CMYK':
                            img = main.img.convert('RGB')
                            img, _ = FILTERS[filter_idm][1](img).enhance((val - 500) / 500)
                            main.img = img.convert("CMYK")

                        elif main.img.mode == 'PA':
                            img = main.img.convert('RGB')
                            img, _ = FILTERS[filter_idm][1](img).enhance((val - 500) / 500)
                            img = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=len(main.img.getpalette()) // 3)
                            img.putalpha(ctx['alpha'])
                            main.img = img

                        elif main.img.mode == 'LA':
                            img = main.img.convert('L')
                            img, _ = FILTERS[filter_idm][1](img).enhance((val - 500) / 500)
                            img.putalpha(ctx['alpha'])
                            main.img = img

                        elif main.img.mode == 'P':
                            img = main.img.convert('RGB')
                            img, _ = FILTERS[filter_idm][1](img).enhance((val - 500) / 500)
                            img = img.convert('P', palette=Image.Palette.ADAPTIVE, colors=len(main.img.getpalette()) // 3)
                            main.img = img

                        elif main.img.mode == '1':
                            main.img = main.img.convert('L')
                            main.img, _ = FILTERS[filter_idm][1](main.img).enhance((val - 500) / 500)
                            main.img = main.img.convert('P', palette=Image.Palette.ADAPTIVE, colors=2)
                            main.update_status_infos()
                            main.update_menus()

                        else:  # RGB, RGBA
                            main.img, _ = FILTERS[filter_idm][1](main.img).enhance((val - 500) / 500)
                            if ctx['alpha']:
                                main.img.putalpha(ctx['alpha'])

                        main.undo_stack.push(main.img)
                        main.canvas.update_hbitmap(image_to_hbitmap(main.img))

                    user32.EndDialog(hwnd, 1)

                elif control_id == IDCANCEL:
                    user32.EndDialog(hwnd, 0)

                elif control_id == IDC_BTN_RESET:
                    user32.SendDlgItemMessageW(hwnd, IDC_FILTER_SLIDER, TBM_SETPOS, TRUE, filter_class.default_pos)
                    user32.SetDlgItemTextW(hwnd, IDC_FILTER_EDIT, filter_class.default_display)
                    ctx['canvas'].update_hbitmap(image_to_hbitmap(img_preview))

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    return user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_FILTER),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )
