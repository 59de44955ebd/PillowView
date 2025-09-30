from ctypes import *
import math
import os

from PIL import Image, ImageFilter

from winapp.const import *
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from const import *
from image import gamma_correction
from resources import *

########################################
#
########################################
def show(main, filename):

    ctx = {'img': None}

    ########################################
    #
    ########################################
    def _dialog_proc_callback(hwnd, msg, wparam, lparam):

        if msg == WM_INITDIALOG:
            if main.is_dark:
                DarkDialogInit(hwnd)
            user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)

#            user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_RBN_BBP_24), BM_SETCHECK, BST_CHECKED, 0)
            user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_CHK_INTERLEAVED), BM_SETCHECK, BST_CHECKED, 0)

            # Try to guess values
            size = os.path.getsize(filename)
            ctx['size'] = size

            sq = math.isqrt(size)
            if size == sq ** 2:
                if sq % 4 == 0:
                    user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_RBN_BBP_32), BM_SETCHECK, BST_CHECKED, 0)
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_WIDTH), str(sq // 2))
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_HEIGHT), str(sq // 2))
                else:
                    user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_RBN_BBP_8), BM_SETCHECK, BST_CHECKED, 0)
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_WIDTH), str(sq))
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_HEIGHT), str(sq))

            elif size % 3 == 0: # RGB?
                size //= 3
                sq = math.isqrt(size)
                user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_RBN_BBP_24), BM_SETCHECK, BST_CHECKED, 0)
                if size == sq ** 2:
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_WIDTH), str(sq))
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_HEIGHT), str(sq))
                elif size % 12 == 0:
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_WIDTH), str(size // 3))
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_HEIGHT), str(size // 4))

            elif size % 4 == 0: # RGBA?
                size //= 4
                sq = math.isqrt(size)
                user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_RBN_BBP_32), BM_SETCHECK, BST_CHECKED, 0)
                if size == sq ** 2:
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_WIDTH), str(sq))
                    user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_HEIGHT), str(sq))

            else:
                user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_RBN_BBP_8), BM_SETCHECK, BST_CHECKED, 0)

        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, 0)

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)

            if command == BN_CLICKED:
                control_id = LOWORD(wparam)

                if control_id == IDOK:
                    buf = create_unicode_buffer(8)

                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_WIDTH), buf, 8)
                    w = int(buf.value or 0)
                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_HEIGHT), buf, 8)
                    h = int(buf.value or 0)
                    if w == 0 or h == 0:
                        main.show_message_box('Both width and height must be specified and bigger than 0.', 'Invalid Settings', MB_ICONERROR | MB_OK)
                        return 0

                    user32.GetWindowTextW(user32.GetDlgItem(hwnd, IDC_RAW_EDIT_HEADER), buf, 8)
                    header_size = int(buf.value or 0)

                    bbp = 24
                    for n in (1, 8, 16, 24, 32, 48, 64, 96, 128):
                        if user32.SendMessageW(user32.GetDlgItem(hwnd, eval(f'IDC_RAW_RBN_BBP_{n}')), BM_GETCHECK, 0, 0):
                            bbp = n
                            break

                    with open(filename, 'rb') as f:
                        if header_size:
                            f.seek(header_size)
                        bits = f.read()

                    interleaved = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_CHK_INTERLEAVED), BM_GETCHECK, 0, 0)
                    is_bgr = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_CHK_BGR), BM_GETCHECK, 0, 0)
                    use_alpha = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_CHK_ALPHA), BM_GETCHECK, 0, 0)
                    is_big_endian = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_CHK_BE), BM_GETCHECK, 0, 0)
                    vertical_flip = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_CHK_VERTICAL_FLIP), BM_GETCHECK, 0, 0)

                    if ctx['size'] < w * h * (bbp // 8) + header_size:
                        main.show_message_box('Not enough image data for selected settings.', 'Wrong Settings', MB_ICONERROR | MB_OK)
                        return 0

                    class BEFloat(ctypes.BigEndianStructure):
                        _fields_ = [('v', ctypes.c_float)]

                    if bbp == 128:
                        try:
                            if is_big_endian:

                                if interleaved:
                                    data_8bit = (c_ubyte * (w * h * 4))()
                                    pos = 0
                                    for i in range(w * h * 4):
                                        data_8bit[i] = round(BEFloat.from_buffer_copy(bits[pos:pos+4]).v * 255)
                                        pos += 4
                                    if use_alpha:
                                        ctx['img'] = Image.frombytes('RGBA', (w, h), bytes(data_8bit), 'raw', 'BGRA' if is_bgr else 'RGBA')
                                    else:
                                        ctx['img'] = Image.frombytes('RGBX', (w, h), bytes(data_8bit), 'raw', 'BGRX' if is_bgr else 'RGBX').convert('RGB')
                                else:
                                    pos = 0
                                    channels = []
                                    channel_names = ('R', 'G', 'B', 'A') if use_alpha else ('R', 'G', 'B')
                                    for c in channel_names:
                                        data_8bit = (c_ubyte * (w * h))()
                                        for i in range(w * h):
                                            data_8bit[i] = round(BEFloat.from_buffer_copy(bits[pos:pos+4]).v * 255)
                                            pos += 4
                                        channels.append(Image.frombytes('L', (w, h), bytes(data_8bit), 'raw', 'L'))
                                    if is_bgr:
                                        channels[:3] = list(reversed(channels[:3]))
                                    ctx['img'] = Image.merge('RGBA' if use_alpha else 'RGB', channels)
                            else:
                                data = cast(bits, POINTER(FLOAT))
                                if interleaved:
                                    data_8bit = (c_ubyte * (w * h * 4))()
                                    for i in range(w * h * 4):
                                        data_8bit[i] = round(data[i] * 255)

                                    if use_alpha:
                                        ctx['img'] = Image.frombytes('RGBA', (w, h), bytes(data_8bit), 'raw', 'BGRA' if is_bgr else 'RGBA')
                                    else:
                                        ctx['img'] = Image.frombytes('RGBX', (w, h), bytes(data_8bit), 'raw', 'BGRX' if is_bgr else 'RGBX').convert('RGB')
                                else:
                                    pos = 0
                                    channels = []
                                    channel_names = ('R', 'G', 'B', 'A') if use_alpha else ('R', 'G', 'B')
                                    for c in channel_names:
                                        data_8bit = (c_ubyte * (w * h))()
                                        for i in range(w * h):
                                            data_8bit[i] = round(data[pos + i] * 255)
                                        channels.append(Image.frombytes('L', (w, h), bytes(data_8bit), 'raw', 'L'))
                                        pos += w * h
                                    if is_bgr:
                                        channels[:3] = list(reversed(channels[:3]))
                                    ctx['img'] = Image.merge('RGBA' if use_alpha else 'RGB', channels)
                        except:
                            main.show_message_box('Decode error - maybe wrong Endianness specified.', 'Wrong Settings', MB_ICONERROR | MB_OK)
                            return 0

                        gamma = 1 / 2.2
                        ctx['img'] = gamma_correction(ctx['img'], gamma)

                    elif bbp == 96:
                        try:
                            if is_big_endian:
                                if interleaved:
                                    data_8bit = (c_ubyte * (w * h * 3))()
                                    pos = 0
                                    for i in range(w * h * 3):
                                        data_8bit[i] = round(BEFloat.from_buffer_copy(bits[pos:pos+4]).v * 255)
                                        pos += 4
                                    ctx['img'] = Image.frombytes('RGB', (w, h), bytes(data_8bit), 'raw', 'BGR' if is_bgr else 'RGB')
                                else:
                                    pos = 0
                                    channels = []
                                    for c in ('R', 'G', 'B'):
                                        data_8bit = (c_ubyte * (w * h))()
                                        for i in range(w * h):
                                            data_8bit[i] = round(BEFloat.from_buffer_copy(bits[pos:pos+4]).v * 255)
                                            pos += 4
                                        channels.append(Image.frombytes('L', (w, h), bytes(data_8bit), 'raw', 'L'))
                                    if is_bgr:
                                        channels.reverse()
                                    ctx['img'] = Image.merge('RGB', channels)
                            else:
                                data = cast(bits, POINTER(FLOAT))
                                if interleaved:
                                    data_8bit = (c_ubyte * (w * h * 3))()
                                    for i in range(w * h * 3):
                                        data_8bit[i] = round(data[i] * 255)
                                    ctx['img'] = Image.frombytes('RGB', (w, h), bytes(data_8bit), 'raw', 'BGR' if is_bgr else 'RGB')
                                else:
                                    pos = 0
                                    channels = []
                                    for c in ('R', 'G', 'B'):
                                        data_8bit = (c_ubyte * (w * h))()
                                        for i in range(w * h):
                                            data_8bit[i] = round(data[i] * 255)
                                        channels.append(Image.frombytes('L', (w, h), bytes(data_8bit), 'raw', 'L'))
                                        pos += w * h
                                    if is_bgr:
                                        channels.reverse()
                                    ctx['img'] = Image.merge('RGB', channels)
                        except:
                            main.show_message_box('Decode error - maybe wrong Endianness specified.', 'Wrong Settings', MB_ICONERROR | MB_OK)
                            return 0

                        ctx['img'] = gamma_correction(ctx['img'], 1 / 2.2)

                    elif bbp == 64:
                        data = cast(bits, POINTER(c_uint16))
                        if interleaved:
                            data_8bit = (c_ubyte * (w * h * 4))()
                            for i in range(w * h * 4):
                                data_8bit[i] = data[i] >> 8
                            if use_alpha:
                                ctx['img'] = Image.frombytes('RGBA', (w, h), bytes(data_8bit), 'raw', 'BGRA' if is_bgr else 'RGBA')
                            else:
                                ctx['img'] = Image.frombytes('RGBX', (w, h), bytes(data_8bit), 'raw', 'BGRX' if is_bgr else 'RGBX').convert('RGB')
                        else:
                            pos = 0
                            channels = []
                            channel_names = ('R', 'G', 'B', 'A') if use_alpha else ('R', 'G', 'B')
#                            if use_alpha:
                            for c in channel_names:
                                data_8bit = (c_ubyte * (w * h))()
                                for i in range(w * h):
                                    data_8bit[i] = data[pos + i] >> 8
                                channels.append(Image.frombytes('L', (w, h), bytes(data_8bit), 'raw', 'L'))
                                pos += w * h
                            if is_bgr:
                                channels[:3] = list(reversed(channels[:3]))
                            ctx['img'] = Image.merge('RGBA' if use_alpha else 'RGB', channels)

                    elif bbp == 48:
                        data = cast(bits, POINTER(c_uint16))
                        if interleaved:
                            data_8bit = (c_ubyte * (w * h * 3))()
                            for i in range(w * h * 3):
                                data_8bit[i] = data[i] >> 8
                            ctx['img'] = Image.frombytes('RGB', (w, h), bytes(data_8bit), 'raw', 'BGR' if is_bgr else 'RGB')
                        else:
                            pos = 0
                            channels = []
                            for c in ('R', 'G', 'B'):
                                data_8bit = (c_ubyte * (w * h))()
                                for i in range(w * h):
                                    data_8bit[i] = data[pos + i] >> 8
                                channels.append(Image.frombytes('L', (w, h), bytes(data_8bit), 'raw', 'L'))
                                pos += w * h
                            if is_bgr:
                                channels.reverse()
                            ctx['img'] = Image.merge('RGB', channels)

                    elif bbp == 32:
                        is_cmyk = user32.SendMessageW(user32.GetDlgItem(hwnd, IDC_RAW_CHK_CMYK), BM_GETCHECK, 0, 0)
                        if interleaved:
                            if is_cmyk:
                                ctx['img'] = Image.frombytes('CMYK', (w, h), bits, 'raw', 'CMYK')
                            elif use_alpha:
                                ctx['img'] = Image.frombytes('RGBA', (w, h), bits, 'raw', 'BGRA' if is_bgr else 'RGBA')
                            else:
                                ctx['img'] = Image.frombytes('RGBX', (w, h), bits, 'raw', 'RGBX').convert('RGB')
                        else:
                            channel_size = w * h
                            pos = 0
                            channels = []
                            if is_cmyk:
                                for c in ('C', 'M', 'Y', 'K'):
                                    channels.append(Image.frombytes('L', (w, h), bits[pos:pos + channel_size], 'raw', 'L'))
                                    pos += channel_size
                                ctx['img'] = Image.merge('CMYK', channels)
                            elif use_alpha:
                                for c in ('R', 'G', 'B', 'A'):
                                    channels.append(Image.frombytes('L', (w, h), bits[pos:pos + channel_size], 'raw', 'L'))
                                    pos += channel_size
                                if is_bgr:
                                    channels[:3] = list(reversed(channels[:3]))
                                ctx['img'] = Image.merge('RGBA', channels)
                            else:
                                for c in ('R', 'G', 'B'):
                                    channels.append(Image.frombytes('L', (w, h), bits[pos:pos + channel_size], 'raw', 'L'))
                                    pos += channel_size
                                if is_bgr:
                                    channels.reverse()
                                ctx['img'] = Image.merge('RGB', channels)

                    elif bbp == 24:
                        if interleaved:
                            ctx['img'] = Image.frombytes('RGB', (w, h), bits, 'raw', 'BGR' if is_bgr else 'RGB')
                        else:
                            channel_size = w * h
                            pos = 0
                            channels = []
                            for c in ('R', 'G', 'B'):
                                channels.append(Image.frombytes('L', (w, h), bits[pos:pos + channel_size], 'raw', 'L'))
                                pos += channel_size
                            if is_bgr:
                                channels.reverse()
                            ctx['img'] = Image.merge('RGB', channels)

                    elif bbp == 16:
                        #if use_alpha:
                        if interleaved:
                            ctx['img'] = Image.frombytes('LA', (w, h), bits, 'raw', 'LA')  #.convert('RGBA')
                        else:
                            channel_size = w * h
                            pos = 0
                            channels = []
                            for c in ('L', 'A'):
                                channels.append(Image.frombytes('L', (w, h), bits[pos:pos + channel_size], 'raw', 'L'))
                                pos += channel_size
                            ctx['img'] = Image.merge('LA', channels) #.convert('RGBA')

                    elif bbp == 8:
                        ctx['img'] = Image.frombytes('L', (w, h), bits, 'raw', 'L')

                    elif bbp == 1:
                        ctx['img'] = Image.frombytes('1', (w, h), bits, 'raw', '1')

                    if vertical_flip:
                        ctx['img'] = ctx['img'].transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)

                    user32.EndDialog(hwnd, 1)

                if control_id == IDCANCEL:
                    user32.EndDialog(hwnd, 0)

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    if user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_RAW_OPEN),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    ):
        return ctx['img']
