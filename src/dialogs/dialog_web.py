from ctypes import *
import io
import os

from PIL import Image

from winapp.const import *
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from canvas import *
from const import *
from image import *
from resources import *
from utils import *

MARGIN = 9
FILE_TYPES = ['JPEG', 'PNG', 'GIF', 'WEBP', 'AVIF']
FILE_EXT = ['.jpg', '.png', '.gif', '.webp', '.avif']


class Group():

    ########################################
    #
    ########################################
    def __init__(self, parent_hwnd, parent_size, controls):
        self._controls = controls
        self._parent_size = parent_size
        self._positions = {}
        rc = RECT()
        for c in controls:
            user32.GetWindowRect(c, byref(rc))
            user32.MapWindowPoints(None, parent_hwnd, byref(rc), 1)
            self._positions[c] = POINT(rc.left, rc.top)

    ########################################
    #
    ########################################
    def show(self, show_cmd=1):
        for c in self._controls:
            user32.ShowWindow(c, show_cmd)

    ########################################
    #
    ########################################
    def align_right(self, x):
        for c in self._controls:
            user32.SetWindowPos(
                c, NULL,
                x - self._parent_size.x + self._positions[c].x,
                self._positions[c].y,
                0, 0,
                SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
            )

    ########################################
    #
    ########################################
    def align_bottom(self, y):
        for c in self._controls:
            user32.SetWindowPos(
                c, NULL,
                self._positions[c].x,
                y - self._parent_size.y + self._positions[c].y,
                0, 0,
                SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
            )

    ########################################
    #
    ########################################
    def align_right_bottom(self, x, y):
        for c in self._controls:
            user32.SetWindowPos(
                c, NULL,
                x - self._parent_size.x + self._positions[c].x,
                y - self._parent_size.y + self._positions[c].y,
                0, 0,
                SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
            )


########################################
#
########################################
def show(main):
    if main.img is None:
        return

    ctx = {}
    controls = {}

    ctx['initial'] = True

    ########################################
    #
    ########################################
    def _update_layout(width, height):
        w = (width - 3 * MARGIN) // 2
        h = height - 2 * MARGIN - 130

        x2 = 2 * MARGIN + w
        user32.SetWindowPos(
            controls[IDC_WEB_STATIC_ORG_IMG], NULL,
            MARGIN + 1, 6,
            0, 0,
            SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
        )
        user32.SetWindowPos(
            controls[IDC_WEB_STATIC_OPT_IMG], NULL,
            x2 + 1, 6,
            0, 0,
            SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
        )

        ctx['canvas_org'].set_window_pos(
            x = MARGIN,
            y = 27,
            width=w,
            height=h,
            flags=SWP_NOACTIVATE | SWP_NOZORDER
        )

        ctx['canvas_opt'].set_window_pos(
            x = x2,
            y = 27,
            width = w,
            height = h,
            flags = SWP_NOACTIVATE | SWP_NOZORDER
        )

        user32.SetWindowPos(
            controls[IDC_WEB_TABCTL], NULL,
            MARGIN, 32 + h,
            0, 0,
            SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER
        )

        for g in ctx['groups']:
            g.align_bottom(height)

        ctx['groups'][5].align_right_bottom(width, height)
        ctx['win'].redraw_window()

    ########################################
    #
    ########################################
    def _save(file_format, f):

        img = main.img

        if file_format == 'JPEG':
            ########################################
            # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#jpeg-saving
            # Supports CMYK, RGB, L and 1
            # No RGBA, LA, P
            ########################################
            # dpi
            # exif
            # icc_profile
            optimize = bool(user32.SendMessageW(controls[IDC_WEB_JPEG_CHKBOX_OPTIMIZE], BM_GETCHECK, 0, 0))
            progressive = bool(user32.SendMessageW(controls[IDC_WEB_JPEG_CHKBOX_PROGRESSIVE], BM_GETCHECK, 0, 0))
            quality = user32.SendMessageW(controls[IDC_WEB_JPEG_TRB_QUAL], TBM_GETPOS, 0, 0)
            subsampling = user32.SendMessageW(controls[IDC_WEB_JPEG_COMBO_SUBSAMPLING], CB_GETCURSEL, 0, 0)
            kwargs = {'subsampling': subsampling - 1} if subsampling > 0 else {}
            if img.mode in ('RGBA', 'P', 'PA'): # or MODE_TO_BPP[main.img.mode] < 24:
                img = img.convert('RGB')
            elif img.mode == 'LA':
                img = img.convert('L')
            img.save(f, 'JPEG', quality=quality, progressive=progressive, optimize=optimize, **kwargs)

        elif file_format == 'PNG':
            ########################################
            # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#png-saving
            # Supports RGBA, RGB, LA, L, P
            # No CMYK, 1
            ########################################
            # dpi
            # exif
            # transparency
            color_mode = user32.SendMessageW(controls[IDC_WEB_PNG_COMBO_COLORMODE], CB_GETCURSEL, 0, 0)
            compress_level = user32.SendMessageW(controls[IDC_WEB_PNG_TRB_COMPRESSION], TBM_GETPOS, 0, 0)
            optimize = bool(user32.SendMessageW(controls[IDC_WEB_PNG_CHKBOX_OPTIMIZE], BM_GETCHECK, 0, 0))

            if color_mode == 0:
                if img.mode == 'CMYK':
                    img = img.convert('RGB')
                elif img.mode == 'PA':
                    img = img.convert('P')
                img.save(f, 'PNG', compress_level=compress_level, optimize=optimize)
            else:
                if img.mode in ('RGBA', 'CMYK'):
                    img = img.convert('RGB')
                elif img.mode in ('LA', '1'):
                    img = img.convert('L')
                elif img.mode == 'PA':
                    img = img.convert('P')

                if color_mode == 1:
                    img.convert('P', palette=Image.ADAPTIVE, colors=256).save(f, 'PNG', compress_level=compress_level, optimize=optimize)
                elif color_mode == 2:
                    img.convert('P', palette=Image.ADAPTIVE, colors=128).save(f, 'PNG', compress_level=compress_level, optimize=optimize)
                elif color_mode == 3:
                    img.convert('P', palette=Image.ADAPTIVE, colors=16).save(f, 'PNG', compress_level=compress_level, optimize=optimize)
                elif color_mode == 4:
                    img.convert('L').save(f, 'PNG', compress_level=compress_level, optimize=optimize)

        elif file_format == 'GIF':
            ########################################
            # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif-saving
            # Supports RGBA, RGB, P
            # No CMYK, LA, 1
            ########################################
            # palette
            # transparency
            color_mode = user32.SendMessageW(controls[IDC_WEB_GIF_COMBO_COLORMODE], CB_GETCURSEL, 0, 0)
            interlace = bool(user32.SendMessageW(controls[IDC_WEB_GIF_CHKBOX_INTERLACE], BM_GETCHECK, 0, 0))
#            img = main.img.convert('RGB') if MODE_TO_BPP[main.img.mode] > 24 else main.img
            if img.mode == 'CMYK':
                img = img.convert('RGB')
            elif img.mode in ('LA', '1'):
                img = img.convert('L')
            elif img.mode == 'PA':
                img = img.convert('P')

            if color_mode == 0:
                img.convert('P', palette=Image.ADAPTIVE, colors=256).save(f, 'GIF', interlace=interlace)
            elif color_mode == 1:
                img.convert('P', palette=Image.ADAPTIVE, colors=128).save(f, 'GIF', interlace=interlace)
            elif color_mode == 2:
                img.convert('P', palette=Image.ADAPTIVE, colors=16).save(f, 'GIF', interlace=interlace)
            elif color_mode == 3:
                img.convert('L').save(f, 'GIF', interlace=interlace)

        elif file_format == 'WEBP':
            ########################################
            # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp-saving
            # Supports all
            ########################################
            # exif
            # icc_profile
    #        method
    #            Quality/speed trade-off (0=fast, 6=slower-better). Defaults to 4.
            quality = user32.SendMessageW(controls[IDC_WEB_WEBP_TRB_QUAL], TBM_GETPOS, 0, 0)
            lossless = bool(user32.SendMessageW(controls[IDC_WEB_WEBP_CHKBOX_LOSSLESS], BM_GETCHECK, 0, 0))
            img.save(f, 'WEBP', quality=quality, lossless=lossless)

        elif file_format == 'AVIF':
            ########################################
            # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#avif
            # Supports all
            ########################################
            # quality
            # subsampling
            quality = user32.SendMessageW(controls[IDC_WEB_AVIF_TRB_QUAL], TBM_GETPOS, 0, 0)
            subsampling = user32.SendMessageW(controls[IDC_WEB_AVIF_COMBO_SUBSAMPLING], CB_GETCURSEL, 0, 0)
            subsampling = ['4:4:4', '4:2:2', '4:2:0', '4:0:0'][subsampling]
            img.save(f, 'AVIF', quality=quality, subsampling=subsampling)

    ########################################
    #
    ########################################
    def _show(file_format, zoom_to_fit=False):
        f = io.BytesIO()
        _save(file_format, f)
        bytes = f.tell()
        bs = locale.format_string('%d', bytes, grouping=True)
        user32.SetWindowTextW(controls[IDC_WEB_STATIC_OPT_IMG], f'Optimized image: {bs} bytes ({format_filesize(bytes)})')
        ctx['canvas_opt'].update_hbitmap(image_to_hbitmap(Image.open(f, formats=[file_format])), zoom_to_fit=zoom_to_fit)

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
            if main.is_dark:
                DarkDialogInit(hwnd)
            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)

            def _enum_child_func(hwnd_child, lparam):
                control_id = user32.GetDlgCtrlID(hwnd_child)
                if control_id > 0:
                    controls[control_id] = hwnd_child
                return TRUE
            user32.EnumChildWindows(hwnd, WNDENUMPROC(_enum_child_func), 0)

            # TabControl
            tie = TCITEMW()
            tie.mask = TCIF_TEXT
            for i, txt in enumerate(FILE_TYPES):
                tie.pszText = txt
                user32.SendMessageW(controls[IDC_WEB_TABCTL], TCM_INSERTITEMW, i, byref(tie))

            # Zoom Toolbar
            user32.SendMessageW(controls[IDC_WEB_TB_ZOOM], TB_SETBITMAPSIZE, 0, MAKELONG(16, 16))
            tb = TBADDBITMAP()
            tb.nID = user32.LoadBitmapW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDB_TOOLBAR_ZOOM))
            image_list_id = user32.SendMessageW(controls[IDC_WEB_TB_ZOOM], TB_ADDBITMAP, 3, byref(tb))
            user32.SendMessageW(controls[IDC_WEB_TB_ZOOM], TB_BUTTONSTRUCTSIZE, sizeof(TBBUTTON), 0)
            tb_buttons = (TBBUTTON * 3)(
                TBBUTTON(MAKELONG(0, image_list_id), IDM_ZOOM_IN, TBSTATE_ENABLED, BTNS_BUTTON, (BYTE * 6)(), 0, 'Zoom in'),
                TBBUTTON(MAKELONG(1, image_list_id), IDM_ZOOM_OUT, TBSTATE_ENABLED, BTNS_BUTTON, (BYTE * 6)(), 0, 'Zoom out'),
                TBBUTTON(MAKELONG(2, image_list_id), IDM_ORIGINAL_SIZE, TBSTATE_ENABLED, BTNS_BUTTON, (BYTE * 6)(), 0, 'Original Size')
            )
            user32.SendMessageW(controls[IDC_WEB_TB_ZOOM], TB_ADDBUTTONS, 3, tb_buttons)
            user32.SendMessageW(controls[IDC_WEB_TB_ZOOM], TB_SETMAXTEXTROWS, 0, 0)
            user32.SendMessageW(controls[IDC_WEB_TB_ZOOM], TB_AUTOSIZE, 0, 0)
            if main.is_dark:
                uxtheme.SetWindowTheme(controls[IDC_WEB_TB_ZOOM], 'MaxGoComposited', None)
                hwnd_tooltip = user32.SendMessageW(controls[IDC_WEB_TB_ZOOM], TB_GETTOOLTIPS, 0, 0)
                if hwnd_tooltip:
                    uxtheme.SetWindowTheme(hwnd_tooltip, 'DarkMode_Explorer', None)

            ctx['win'] = Window(wrap_hwnd=hwnd)
            ctx['canvas_org'] = Canvas(ctx['win'], bgcolor=main.state['bg_color'], drag_scroll=True)
            ctx['canvas_opt'] = Canvas(ctx['win'], bgcolor=main.state['bg_color'], drag_scroll=True)

            # Synchronized scrolling
            ctx['canvas_org'].connect(EVENT_CANVAS_HSCROLLED, ctx['canvas_opt'].hscroll_to)
            ctx['canvas_opt'].connect(EVENT_CANVAS_HSCROLLED, ctx['canvas_org'].hscroll_to)
            ctx['canvas_org'].connect(EVENT_CANVAS_VSCROLLED, ctx['canvas_opt'].vscroll_to)
            ctx['canvas_opt'].connect(EVENT_CANVAS_VSCROLLED, ctx['canvas_org'].vscroll_to)

            rc = RECT()
            user32.GetClientRect(hwnd, byref(rc))
            parent_size = POINT(rc.right, rc.bottom)
            ctx['groups'] = [
                Group(hwnd, parent_size, [controls[i] for i in range(IDC_WEB_JPEG_TRB_QUAL, 1012)]),
                Group(hwnd, parent_size, [controls[i] for i in range(IDC_WEB_PNG_STATIC_COLORMODE, 1020)]),
                Group(hwnd, parent_size, [controls[i] for i in range(IDC_WEB_GIF_STATIC_COLORMODE, 1024)]),
                Group(hwnd, parent_size, [controls[i] for i in range(IDC_WEB_WEBP_TRB_QUAL, 1030)]),
                Group(hwnd, parent_size, [controls[i] for i in range(IDC_WEB_AVIF_TRB_QUAL, 1037)]),
                Group(hwnd, parent_size, [controls[IDOK], controls[IDCANCEL], controls[IDC_WEB_TB_ZOOM]]),
            ]

            hfont = gdi32.CreateFontW(-13, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET, OUT_TT_PRECIS,
                    CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, 'Segoe UI')
            user32.SendMessageW(controls[IDC_WEB_STATIC_ORG_IMG], WM_SETFONT, hfont, MAKELPARAM(1, 0))
            user32.SendMessageW(controls[IDC_WEB_STATIC_OPT_IMG], WM_SETFONT, hfont, MAKELPARAM(1, 0))

            # JPEG
            user32.SendMessageW(controls[IDC_WEB_JPEG_TRB_QUAL], TBM_SETPOS, TRUE, 75)
            for s in ('Auto', '4:4:4', '4:2:2', '4:2:0'):
                user32.SendMessageW(controls[IDC_WEB_JPEG_COMBO_SUBSAMPLING], CB_ADDSTRING, 0, s)
            user32.SendMessageW(controls[IDC_WEB_JPEG_COMBO_SUBSAMPLING], CB_SETCURSEL, 0, 0)

            # PNG
            for s in ('True Color', '256 Colors Palette', '128 Colors Palette', '16 Colors Palette', 'Grayscale Palette'):
                user32.SendMessageW(controls[IDC_WEB_PNG_COMBO_COLORMODE], CB_ADDSTRING, 0, s)
            user32.SendMessageW(controls[IDC_WEB_PNG_COMBO_COLORMODE], CB_SETCURSEL, 0, 0)
            user32.SendMessageW(controls[IDC_WEB_PNG_TRB_COMPRESSION], TBM_SETRANGEMAX, FALSE, 9)
            user32.SendMessageW(controls[IDC_WEB_PNG_TRB_COMPRESSION], TBM_SETPOS, TRUE, 6)

            # GIF
            for s in ('256 Colors Palette', '128 Colors Palette', '16 Colors Palette', 'Grayscale Palette'):
                user32.SendMessageW(controls[IDC_WEB_GIF_COMBO_COLORMODE], CB_ADDSTRING, 0, s)
            user32.SendMessageW(controls[IDC_WEB_GIF_COMBO_COLORMODE], CB_SETCURSEL, 0, 0)

            # WEBP
            user32.SendMessageW(controls[IDC_WEB_WEBP_TRB_QUAL], TBM_SETPOS, TRUE, 80)

            # AVIF
            user32.SendMessageW(controls[IDC_WEB_AVIF_TRB_QUAL], TBM_SETPOS, TRUE, 75)
            for s  in ('4:4:4', '4:2:2', '4:2:0', '4:0:0'):
                user32.SendMessageW(controls[IDC_WEB_AVIF_COMBO_SUBSAMPLING], CB_ADDSTRING, 0, s)
            user32.SendMessageW(controls[IDC_WEB_AVIF_COMBO_SUBSAMPLING], CB_SETCURSEL, 2, 0)

#            ctx['canvas_org'].load_hbitmap(image_to_hbitmap(main.img), zoom_to_fit=True)
#
#            bpp = MODE_TO_BPP[main.img.mode]
#            if main.filename:
#                bytes = os.path.getsize(main.filename)
#                user32.SetWindowTextW(hwnd, f'{os.path.basename(main.filename)} ({main.img.width} x {main.img.height} x {bpp} BPP) - Save for Web')
#            else:
#                bytes = bpp * main.img.width * main.img.height
#                user32.SetWindowTextW(hwnd, f'PIL image ({main.img.width} x {main.img.height} x {bpp} BPP) - Save for Web')
#            bs = locale.format_string('%d', bytes, grouping=True)
#            user32.SetWindowTextW(controls[IDC_WEB_STATIC_ORG_IMG], f'Original image: {bs} bytes ({format_filesize(bytes)})')
#
#            _show(FILE_TYPES[0])

        elif msg == WM_SIZE:
            _update_layout(lparam & 0xFFFF, (lparam >> 16) & 0xFFFF)

            if ctx['initial']:
                ctx['initial'] = False
                ctx['canvas_org'].load_hbitmap(image_to_hbitmap(main.img), zoom_to_fit=True)

                bpp = MODE_TO_BPP[main.img.mode]
                if main.filename:
                    bytes = os.path.getsize(main.filename)
                    user32.SetWindowTextW(hwnd, f'{os.path.basename(main.filename)} ({main.img.width} x {main.img.height} x {bpp} BPP) - Save for Web')
                else:
                    bytes = bpp * main.img.width * main.img.height
                    user32.SetWindowTextW(hwnd, f'PIL image ({main.img.width} x {main.img.height} x {bpp} BPP) - Save for Web')
                bs = locale.format_string('%d', bytes, grouping=True)
                user32.SetWindowTextW(controls[IDC_WEB_STATIC_ORG_IMG], f'Original image: {bs} bytes ({format_filesize(bytes)})')

                _show(FILE_TYPES[0], True)

        elif msg == WM_GETMINMAXINFO:
            mmi = cast(lparam, POINTER(MINMAXINFO))
            mmi.contents.ptMinTrackSize = POINT(640, 480)
            return 0

        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, 0)

        elif msg == WM_HSCROLL:
            lo, val, = wparam & 0xFFFF, (wparam >> 16) & 0xFFFF
            if lo == TB_ENDTRACK:
                return 0

            if lo == TB_PAGEDOWN or lo == TB_PAGEUP:  # clicked into slider
                pt = POINT()
                user32.GetCursorPos(byref(pt))
                rc = RECT()
                user32.GetWindowRect(lparam, byref(rc))
                minPos, maxPos = user32.SendMessageW(lparam, TBM_GETRANGEMIN, 0, 0), user32.SendMessageW(lparam, TBM_GETRANGEMAX, 0, 0)
                val = minPos + int((pt.x - rc.left - 10) / (rc.right - rc.left - 20) * (maxPos - minPos))
                user32.SendMessageW(lparam, TBM_SETPOS, 1, val)
            else:
                val = SHORT(val).value

            if lparam == controls[IDC_WEB_JPEG_TRB_QUAL]:
                user32.SetWindowTextW(controls[IDC_WEB_JPEG_EDIT_QUAL], str(val))
                user32.UpdateWindow(controls[IDC_WEB_JPEG_EDIT_QUAL])
                _show('JPEG')
            elif lparam == controls[IDC_WEB_PNG_TRB_COMPRESSION]:
                user32.SetWindowTextW(controls[IDC_WEB_PNG_EDIT_COMPRESSION], str(val))
                user32.UpdateWindow(controls[IDC_WEB_PNG_EDIT_COMPRESSION])
                _show('PNG')
            elif lparam == controls[IDC_WEB_WEBP_TRB_QUAL]:
                user32.SetWindowTextW(controls[IDC_WEB_WEBP_EDIT_QUAL], str(val))
                user32.UpdateWindow(controls[IDC_WEB_WEBP_EDIT_QUAL])
                _show('WEBP')
            elif lparam == controls[IDC_WEB_AVIF_TRB_QUAL]:
                user32.SetWindowTextW(controls[IDC_WEB_AVIF_EDIT_QUAL], str(val))
                user32.UpdateWindow(controls[IDC_WEB_AVIF_EDIT_QUAL])
                _show('AVIF')

        elif msg == WM_NOTIFY:
            mh = cast(lparam, LPNMHDR).contents
            msg = mh.code
            if msg == TCN_SELCHANGE:
                idx = user32.SendMessageW(controls[IDC_WEB_TABCTL], TCM_GETCURSEL, 0, 0)
                for i in range(5):
                    ctx['groups'][i].show(int(i == idx))
                _show(FILE_TYPES[idx])

            elif main.is_dark and msg == NM_CUSTOMDRAW and mh.idFrom == IDC_WEB_TB_ZOOM:
                nmtb = cast(lparam, POINTER(NMTBCUSTOMDRAW)).contents
                nmcd = nmtb.nmcd
                if nmcd.dwDrawStage == CDDS_PREPAINT:
                    # toolbar background
                    user32.FillRect(nmcd.hdc, byref(nmcd.rc), DARK_BG_BRUSH)
                    return TBCDRF_USECDCOLORS  #CDRF_NOTIFYITEMDRAW | CDRF_NOTIFYPOSTERASE | TBCDRF_USECDCOLORS

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)
            control_id = LOWORD(wparam)

            if command == BN_CLICKED:

                if control_id == IDOK:
                    filename, _ = os.path.splitext(main.filename) if main.filename else 'image'
                    idx = user32.SendMessageW(controls[IDC_WEB_TABCTL], TCM_GETCURSEL, 0, 0)
                    ext = FILE_EXT[idx]
                    filename = main.show_save_file_dialog('Save', '', initial_path=filename + ext)
                    if not filename:
                        return FALSE
                    _save(FILE_TYPES[idx], filename)
                    user32.EndDialog(hwnd, 0)

                elif control_id == IDCANCEL:
                    user32.EndDialog(hwnd, 0)

                elif control_id == IDM_ZOOM_IN:
                    ctx['canvas_org'].zoom_in()
                    ctx['canvas_opt'].zoom_in()
                elif control_id == IDM_ZOOM_OUT:
                    ctx['canvas_org'].zoom_out()
                    ctx['canvas_opt'].zoom_out()
                elif control_id == IDM_ORIGINAL_SIZE:
                    ctx['canvas_org'].zoom_original_size()
                    ctx['canvas_opt'].zoom_original_size()

                elif control_id == IDC_WEB_JPEG_CHKBOX_OPTIMIZE or control_id == IDC_WEB_JPEG_CHKBOX_PROGRESSIVE:
                    _show('JPEG')
                elif control_id == IDC_WEB_PNG_CHKBOX_OPTIMIZE:
                    _show('PNG')
                elif control_id == IDC_WEB_GIF_CHKBOX_INTERLACE:
                    _show('GIF')
                elif control_id == IDC_WEB_WEBP_CHKBOX_LOSSLESS:
                    _show('WEBP')

            elif command == CBN_SELCHANGE:
                if control_id == IDC_WEB_JPEG_COMBO_SUBSAMPLING:
                    _show('JPEG')
                elif control_id == IDC_WEB_PNG_COMBO_COLORMODE:
                    _show('PNG')
                elif control_id == IDC_WEB_GIF_COMBO_COLORMODE:
                    _show('GIF')
                elif control_id == IDC_WEB_AVIF_COMBO_SUBSAMPLING:
                    _show('AVIF')

            elif command == EN_CHANGE:
                buf = create_unicode_buffer(4)
                user32.GetWindowTextW(lparam, buf, 4)
                if buf.value == '':
                    return FALSE
                val = int(buf.value)
                if control_id == IDC_WEB_JPEG_EDIT_QUAL:
                    if val > 100:
                        val = 100
                        user32.SetWindowTextW(lparam, '100')
                    user32.SendMessageW(controls[IDC_WEB_JPEG_TRB_QUAL], TBM_SETPOS, TRUE, val)
                    _show('JPEG')
                elif control_id == IDC_WEB_PNG_EDIT_COMPRESSION:
                    if val > 9:
                        val = 9
                        user32.SetWindowTextW(lparam, '9')
                    user32.SendMessageW(controls[IDC_WEB_PNG_TRB_COMPRESSION], TBM_SETPOS, TRUE, val)
                    _show('PNG')
                elif control_id == IDC_WEB_WEBP_EDIT_QUAL:
                    if val > 100:
                        val = 100
                        user32.SetWindowTextW(lparam, '100')
                    user32.SendMessageW(controls[IDC_WEB_WEBP_TRB_QUAL], TBM_SETPOS, TRUE, val)
                    _show('WEBP')
                elif control_id == IDC_WEB_AVIF_EDIT_QUAL:
                    if val > 100:
                        val = 100
                        user32.SetWindowTextW(lparam, '100')
                    user32.SendMessageW(controls[IDC_WEB_AVIF_TRB_QUAL], TBM_SETPOS, TRUE, val)
                    _show('AVIF')

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_SAVE_WEB),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )
