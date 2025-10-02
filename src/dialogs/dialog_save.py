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

    control_hwnds = {}
    kwargs = {}
    ctx = {}

    formats = sorted(list(FORMATS_SAVE.keys()))
    nFilterIndex = formats.index(main.img.format) + 1 if main.img.format in formats else formats.index('PNG') + 1

    control_ids = {}
    control_ids['AVIF'] = (IDC_AVIF_STC1, IDC_AVIF_TRB1, IDC_AVIF_STC2, IDC_AVIF_CBO1, IDC_AVIF_CHK_ANIM)
    control_ids['DDS'] = (IDC_DDS_STC1, IDC_DDS_CBO1)
    control_ids['GIF'] = (IDC_GIF_STC1, IDC_GIF_CBO1, IDC_GIF_CHK1, IDC_GIF_CHK_ANIM)
    control_ids['ICNS'] = (IDC_ICNS_CHK_SIZES,)
    control_ids['ICO'] = (IDC_ICO_CHK_PACKED, IDC_ICO_CHK_SIZES)
    control_ids['JPEG'] = (IDC_JPEG_STC1, IDC_JPEG_TRB1, IDC_JPEG_STC2, IDC_JPEG_CBO1, IDC_JPEG_CHK1, IDC_JPEG_CHK2)
    control_ids['JPEG2000'] = (IDC_JPEG2000_STC1, IDC_JPEG2000_TRB1, IDC_JPEG2000_CHK1)
    control_ids['PDF'] = (IDC_PDF_STC1, IDC_PDF_EDIT_TITLE, IDC_PDF_STC2, IDC_PDF_EDIT_AUTHOR, IDC_PDF_STC3, IDC_PDF_EDIT_RES, IDC_PDF_CHK_ALL)
    control_ids['PNG'] = (IDC_PNG_STC1, IDC_PNG_CBO1, IDC_PNG_STC2, IDC_PNG_TRB1, IDC_PNG_CHK1, IDC_PNG_CHK_ANIM)
    control_ids['TIFF'] = (IDC_TIFF_TRB1, IDC_TIFF_CBO1, IDC_TIFF_STC1, IDC_TIFF_STC2, IDC_TIFF_CHK_ALL)
    control_ids['WEBP'] = (IDC_WEBP_STC1, IDC_WEBP_TRB1, IDC_WEBP_CHK1, IDC_WEBP_CHK_ANIM)

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
#                if main.is_dark:
#                    DarkDialogInit(hwnd)

            def _enum_child_func(hwnd_child, lparam):
                control_hwnds[user32.GetDlgCtrlID(hwnd_child)] = hwnd_child
                return TRUE
            user32.EnumChildWindows(hwnd, WNDENUMPROC(_enum_child_func), 0)

            # AVIF
            user32.SendMessageW(control_hwnds[IDC_AVIF_TRB1], TBM_SETPOS, TRUE, 75)
            hwnd_combo = control_hwnds[IDC_AVIF_CBO1]
            for s in ('4:4:4', '4:2:2', '4:2:0', '4:0:0'):
                user32.SendMessageW(hwnd_combo, CB_ADDSTRING, 0, s)
            user32.SendMessageW(hwnd_combo, CB_SETCURSEL, 2, 0)
            user32.EnableWindow(control_hwnds[IDC_AVIF_CHK_ANIM], int(main.can_play))

            # GIF
            hwnd_combo = control_hwnds[IDC_GIF_CBO1]
            for s in ('256 Colors Palette', '128 Colors Palette', '16 Colors Palette', 'Grayscale Palette'):
                user32.SendMessageW(hwnd_combo, CB_ADDSTRING, 0, s)
            user32.SendMessageW(hwnd_combo, CB_SETCURSEL, 0, 0)
            user32.EnableWindow(control_hwnds[IDC_GIF_CHK_ANIM], int(main.can_play))

            # ICNS
            if 'sizes' in main.img.info and len(main.img.info["sizes"]) > 1:
                user32.EnableWindow(control_hwnds[IDC_ICNS_CHK_SIZES], FALSE)
            else:
                user32.SendMessageW(control_hwnds[IDC_ICNS_CHK_SIZES], BM_SETCHECK, BST_CHECKED, 0)

            # ICO
            if 'sizes' in main.img.info and len(main.img.info["sizes"]) > 1:
                user32.EnableWindow(control_hwnds[IDC_ICO_CHK_SIZES], FALSE)
            else:
                user32.SendMessageW(control_hwnds[IDC_ICO_CHK_SIZES], BM_SETCHECK, BST_CHECKED, 0)

            # JPEG
            user32.SendMessageW(control_hwnds[IDC_JPEG_TRB1], TBM_SETPOS, TRUE, 75)

            hwnd_combo = control_hwnds[IDC_JPEG_CBO1]
            for s in ('Auto', '4:4:4', '4:2:2', '4:2:0'):
                user32.SendMessageW(hwnd_combo, CB_ADDSTRING, 0, s)
            user32.SendMessageW(hwnd_combo, CB_SETCURSEL, 0, 0)

            # JPEG2000
            user32.SendMessageW(control_hwnds[IDC_JPEG2000_TRB1], TBM_SETPOS, TRUE, 100)

            # PDF
            if main.filename:
                user32.SetWindowTextW(control_hwnds[IDC_PDF_EDIT_TITLE], os.path.splitext(os.path.basename(main.filename))[0])
            user32.SetWindowTextW(control_hwnds[IDC_PDF_EDIT_AUTHOR], os.environ['USERNAME'])
            user32.EnableWindow(control_hwnds[IDC_PDF_CHK_ALL], int(main.has_frames))

            # PNG
            hwnd_combo = control_hwnds[IDC_PNG_CBO1]
            for s in ('True Color', '256 Colors Palette', '128 Colors Palette', '16 Colors Palette', 'Grayscale Palette'):
                user32.SendMessageW(hwnd_combo, CB_ADDSTRING, 0, s)
            user32.SendMessageW(hwnd_combo, CB_SETCURSEL, 0, 0)
            user32.SendMessageW(control_hwnds[IDC_PNG_TRB1], TBM_SETRANGEMAX, FALSE, 9)
            user32.SendMessageW(control_hwnds[IDC_PNG_TRB1], TBM_SETPOS, TRUE, 6)
            user32.EnableWindow(control_hwnds[IDC_PNG_CHK_ANIM], int(main.can_play))

            # TIFF
            hwnd_combo = control_hwnds[IDC_TIFF_CBO1]
            for s in ('None', 'LZW', 'Deflate', 'JPEG', 'Packbits'):
                user32.SendMessageW(hwnd_combo, CB_ADDSTRING, 0, s)
            user32.SendMessageW(hwnd_combo, CB_SETCURSEL, 0, 0)
            user32.SendMessageW(control_hwnds[IDC_TIFF_TRB1], TBM_SETPOS, TRUE, 75)
            user32.EnableWindow(control_hwnds[IDC_TIFF_CHK_ALL], int(main.has_frames))

            # WEBP
            user32.SendMessageW(control_hwnds[IDC_WEBP_TRB1], TBM_SETPOS, TRUE, 80)
            user32.EnableWindow(control_hwnds[IDC_WEBP_CHK_ANIM], int(main.can_play))

            # DDS
            hwnd_combo = control_hwnds[IDC_DDS_CBO1]
            for s in ('DXT1', 'DXT3', 'DXT5', 'BC2', 'BC3', 'BC5'):
                user32.SendMessageW(hwnd_combo, CB_ADDSTRING, 0, s)
            user32.SendMessageW(hwnd_combo, CB_SETCURSEL, 0, 0)

            current_format = formats[nFilterIndex - 1]
            for k, v in control_ids.items():
                show_cmd = int(k == current_format)
                for control_id in v:
                    user32.ShowWindow(control_hwnds[control_id], show_cmd)

        elif msg == WM_NOTIFY:
            nmhdr = cast(lparam, LPNMHDR).contents
#                print(nmhdr.code)

            if nmhdr.code == CDN_TYPECHANGE:

                ofn = cast(lparam, POINTER(OFNOTIFYW)).contents
                f = formats[ofn.lpOFN.contents.nFilterIndex - 1]  # TIFF

                for k, v in control_ids.items():
                    show_cmd = int(k == f)
                    for control_id in v:
                        user32.ShowWindow(control_hwnds[control_id], show_cmd)

            elif nmhdr.code == CDN_FILEOK:
                ofn = cast(lparam, POINTER(OFNOTIFYW)).contents
                f = formats[ofn.lpOFN.contents.nFilterIndex - 1]

                ctx['format'] = f

                if f == 'AVIF':
                    kwargs['quality'] = user32.SendMessageW(control_hwnds[IDC_AVIF_TRB1], TBM_GETPOS, 0, 0)
                    kwargs['subsampling'] = ('4:4:4', '4:2:2', '4:2:0', '4:0:0')[user32.SendMessageW(control_hwnds[IDC_AVIF_CBO1], CB_GETCURSEL, 0, 0)]
                    if user32.SendMessageW(control_hwnds[IDC_AVIF_CHK_ANIM], BM_GETCHECK, 0, 0):
                        kwargs['save_all'] = True
                        kwargs['duration'] = int(main.img.info['duration']) if 'duration' in main.img.info else 100

                elif f == 'DDS':
                    kwargs['pixel_format'] = ('DXT1', 'DXT3', 'DXT5', 'BC2', 'BC3', 'BC5')[user32.SendMessageW(control_hwnds[IDC_DDS_CBO1], CB_GETCURSEL, 0, 0)]

                elif f == 'GIF':
                    ctx['color_mode'] = user32.SendMessageW(control_hwnds[IDC_GIF_CBO1], CB_GETCURSEL, 0, 0)
                    kwargs['interlace'] = bool(user32.SendMessageW(control_hwnds[IDC_GIF_CHK1], BM_GETCHECK, 0, 0))
                    if user32.SendMessageW(control_hwnds[IDC_GIF_CHK_ANIM], BM_GETCHECK, 0, 0):
                        kwargs['save_all'] = True
                        kwargs['duration'] = int(main.img.info['duration']) if 'duration' in main.img.info else 100
                        kwargs['background'] = main.img.info['background'] if 'background' in main.img.info else 255
                        kwargs['disposal'] = 2

                elif f == 'ICNS':
                    if ('sizes' not in main.img.info or len(main.img.info["sizes"]) == 1) and not user32.SendMessageW(control_hwnds[IDC_ICNS_CHK_SIZES], BM_GETCHECK, 0, 0):
                        kwargs['single_size'] = True

                elif f == 'ICO':
                    if not user32.SendMessageW(control_hwnds[IDC_ICO_CHK_PACKED], BM_GETCHECK, 0, 0):
                        kwargs['bitmap_format'] = 'bmp'
                    if ('sizes' not in main.img.info or len(main.img.info["sizes"]) == 1) and not user32.SendMessageW(control_hwnds[IDC_ICO_CHK_SIZES], BM_GETCHECK, 0, 0):
                        kwargs['single_size'] = True

                elif f == 'JPEG':
                    kwargs['quality'] = user32.SendMessageW(control_hwnds[IDC_JPEG_TRB1], TBM_GETPOS, 0, 0)
                    subsampling = user32.SendMessageW(control_hwnds[IDC_JPEG_CBO1], CB_GETCURSEL, 0, 0)
                    if subsampling > 0:
                        kwargs['subsampling'] = subsampling - 1
                    kwargs['optimze'] = bool(user32.SendMessageW(control_hwnds[IDC_JPEG_CHK1], BM_GETCHECK, 0, 0))
                    kwargs['progressive'] = bool(user32.SendMessageW(control_hwnds[IDC_JPEG_CHK2], BM_GETCHECK, 0, 0))

                elif f == 'JPEG2000':
                    if not user32.SendMessageW(control_hwnds[IDC_JPEG2000_CHK1], BM_GETCHECK, 0, 0):
                        kwargs['irreversible'] = True
                        kwargs['quality_mode'] = 'rates'
                        kwargs['quality_layers'] = [100 - user32.SendMessageW(control_hwnds[IDC_JPEG2000_TRB1], TBM_GETPOS, 0, 0)]

                elif f == 'PDF':
                    buf = create_unicode_buffer(MAX_PATH)
                    user32.GetWindowTextW(control_hwnds[IDC_PDF_EDIT_TITLE], buf, MAX_PATH)
                    if buf.value:
                        kwargs['title'] = buf.value
                    user32.GetWindowTextW(control_hwnds[IDC_PDF_EDIT_AUTHOR], buf, MAX_PATH)
                    if buf.value:
                        kwargs['author'] = buf.value
                    user32.GetWindowTextW(control_hwnds[IDC_PDF_EDIT_RES], buf, MAX_PATH)
                    if buf.value:
                        kwargs['resolution'] = int(buf.value)
                    if user32.SendMessageW(control_hwnds[IDC_PDF_CHK_ALL], BM_GETCHECK, 0, 0):
                        kwargs['save_all'] = True

                elif f == 'PNG':
                    ctx['color_mode'] = user32.SendMessageW(control_hwnds[IDC_PNG_CBO1], CB_GETCURSEL, 0, 0)
                    kwargs['compress_level'] = user32.SendMessageW(control_hwnds[IDC_PNG_TRB1], TBM_GETPOS, 0, 0)
                    kwargs['optimze'] = bool(user32.SendMessageW(control_hwnds[IDC_PNG_CHK1], BM_GETCHECK, 0, 0))
                    if user32.SendMessageW(control_hwnds[IDC_PNG_CHK_ANIM], BM_GETCHECK, 0, 0):
                        kwargs['save_all'] = True
                        kwargs['duration'] = int(main.img.info['duration']) if 'duration' in main.img.info else 100

                elif f == 'TIFF':
                    kwargs['compression'] = [None, 'tiff_lzw', 'tiff_deflate', 'jpeg', 'packbits'][user32.SendMessageW(control_hwnds[IDC_TIFF_CBO1], CB_GETCURSEL, 0, 0)]
                    if kwargs['compression'] == 'jpeg':
                        kwargs['quality'] = user32.SendMessageW(control_hwnds[IDC_TIFF_TRB1], TBM_GETPOS, 0, 0)
                    if user32.SendMessageW(control_hwnds[IDC_TIFF_CHK_ALL], BM_GETCHECK, 0, 0):
                        kwargs['save_all'] = True

                elif f == 'WEBP':
                    kwargs['quality'] = user32.SendMessageW(control_hwnds[IDC_WEBP_TRB1], TBM_GETPOS, 0, 0)
                    kwargs['lossless'] = bool(user32.SendMessageW(control_hwnds[IDC_WEBP_CHK1], BM_GETCHECK, 0, 0))
                    if user32.SendMessageW(control_hwnds[IDC_WEBP_CHK_ANIM], BM_GETCHECK, 0, 0):
                        kwargs['save_all'] = True
                        kwargs['duration'] = int(main.img.info['duration']) if 'duration' in main.img.info else 100

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)
            if command == CBN_SELCHANGE:
                flag = int(user32.SendMessageW(control_hwnds[IDC_TIFF_CBO1], CB_GETCURSEL, 0, 0) == 3)
                user32.EnableWindow(control_hwnds[IDC_TIFF_TRB1], flag)

        return FALSE

    filename = main.show_save_file_dialog(
        'Save',
        filter_string=main.filter_save,
        initial_path=os.path.splitext(main.filename)[0] if main.filename else 'image',
        flags=OFN_ENABLESIZING | OFN_OVERWRITEPROMPT | OFN_EXPLORER | OFN_ENABLETEMPLATE | OFN_ENABLEHOOK,
        hinstance=HMOD_RESOURCES,
        lpTemplateName=MAKEINTRESOURCEW(IDD_DLG_SETTINGS_SAVE),
        lpfnHook = LPHOOKPROC(_dialog_proc_callback),
        nFilterIndex=nFilterIndex,
    )
    if not filename:
        return

    img = main.img

    if ctx['format'] in BPP1_ONLY:
        img = img.convert('1')

    elif ctx['format'] in P_ONLY:
        img = img.convert('P')

    elif img.mode == 'CMYK':
        if ctx['format'] in NO_CMYK:
            img = img.convert('RGB')

    elif img.mode == 'RGBA':
        if ctx['format'] in NO_RGBA:
            img = img.convert('RGB')

    elif img.mode == 'LA':
        if ctx['format'] in NO_LA:
            img = img.convert('L' if ctx['format'] in NO_RGBA else 'RGBA')

    elif img.mode == 'L':
        if ctx['format'] in NO_L:
            img = img.convert('RGB')

    elif img.mode == 'P':
        if ctx['format'] in NO_P:
            img = img.convert('RGB')

    elif img.mode == 'PA':
        if ctx['format'] not in OK_PA:
            img = img.convert('RGBA')

    elif img.mode == '1':
        if ctx['format'] in NO_BPP1:
            img = img.convert('RGB')

    if ctx['format'] == 'ICNS':
        if 'single_size' in kwargs:
            sizes = [s for s in (32, 64, 128, 256, 512, 1024) if s <= img.size[0]]
            target_size = (sizes[-1], sizes[-1])
            if img.size != target_size:
                img = img.resize(target_size)
            kwargs['single_size'] = target_size[0]

    elif ctx['format'] == 'ICO':

        if 'sizes' in img.info and len(img.info['sizes']) > 1:
            # If the image has multiple sizes, save it as it is
            kwargs['sizes'] = img.info["sizes_sorted"]
            append_images = []
            for i in range(1, len(img.info["sizes_sorted"])):
                img.size = img.info["sizes_sorted"][i]
                tmp = img.copy()

                # This fixes a bug in Pillow's Ico plugin
                if tmp.mode == 'RGBA':
                    colors = tmp.getchannel('A').getcolors()
                    if len(colors) == 1:
                        tmp = tmp.convert('RGB')

                append_images.append(tmp)
            kwargs['append_images'] = append_images

            img.size = img.info["sizes_sorted"][0]
            # This fixes a bug in Pillow's Ico plugin
            if img.mode == 'RGBA':
                colors = img.getchannel('A').getcolors()
                if len(colors) == 1:
                    img = img.convert('RGB')

        elif 'single_size' in kwargs:
            del kwargs['single_size']
            sizes = [s for s in (16, 24, 32, 64, 128, 256) if s <= img.size[0]]
            target_size = (sizes[-1], sizes[-1])
            if img.size != target_size:
                img = img.resize(target_size)
            kwargs['sizes'] = [target_size]

        elif kwargs['bitmap_format'] == 'bmp':
            sizes = [s for s in (16, 24, 32, 64, 128, 256) if s <= img.size[0]]
            main_size = sizes[-1]

            # make .ico more compatible by forcing black background for all sizes
#            if "A" in img.getbands():
#                img = img.convert('RGBA')
#                tmp = img if img.size == (main_size, main_size) else img.resize((main_size, main_size))
#                img_main = Image.new('RGBA', (main_size, main_size))  # default = black background
#                img_main.alpha_composite(tmp)
#                append_images = []
#                for s in sizes[:-1]:
#                    tmp = Image.new('RGBA', (s, s))
#                    tmp.alpha_composite(img.resize((s, s)))
#                    append_images.append(tmp)
#            else:
            img_main = img if img.size == (main_size, main_size) else img.resize((main_size, main_size))
            append_images = []
            for s in sizes[:-1]:
                append_images.append(img.resize((s, s)))

            kwargs['sizes'] = [(s, s) for s in sizes]
            kwargs['append_images'] = append_images
            img = img_main

    elif ctx['format'] == 'JPEG':
        if img.format == 'JPEG':
            kwargs['icc_profile'] = img.info.get('icc_profile')
            kwargs['exif'] = img.getexif()

    elif ctx['format'] == 'RAW':
        with open(filename, 'wb') as f:
            f.write(img.tobytes())
        return filename

    if img.mode == 'P' and 'transparency' in img.info:
        pal = img.getpalette()
        trans = img.info['transparency']
        pal[trans * 3:trans * 3 + 3] = img.info['transcolor']
        img.putpalette(pal)

    img.save(filename, **kwargs)

    if img.mode == 'P' and 'transparency' in img.info:
        pal[trans * 3:trans * 3 + 3] = CR_TO_RGB(main.state['bg_color'])
        img.putpalette(pal)

    return filename
