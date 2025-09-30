import os
from ctypes import *
from datetime import datetime

from PIL import ExifTags
from PIL.ExifTags import TAGS

from winapp.const import *
from winapp.controls.common import LVCOLUMNW, LVITEMW
from winapp.dialog import *
from winapp.dlls import *
from winapp.wintypes_extended import *

from const import *
from image import get_bpp
from resources import *
from utils import *


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

            hwnd_listview = user32.GetDlgItem(hwnd, IDC_LSV1)

            ex_style = LVS_EX_FULLROWSELECT | LVS_EX_AUTOSIZECOLUMNS  #LVS_EX_GRIDLINES |
            user32.SendMessageW(hwnd_listview, LVM_SETEXTENDEDLISTVIEWSTYLE, ex_style, ex_style)

            lvc = LVCOLUMNW()
            lvc.mask = LVCF_TEXT | LVCF_WIDTH

            lvc.pszText = "" #EXIF Tag"
            lvc.cx = 200
            user32.SendMessageW(hwnd_listview, LVM_INSERTCOLUMNW, 0, byref(lvc))

            lvc.pszText = "" #Value"
            lvc.cx = 400
            user32.SendMessageW(hwnd_listview, LVM_INSERTCOLUMNW, 1, byref(lvc))

            lvi = LVITEMW()
            lvi.mask = LVIF_TEXT

            infos = []
            infos.append(('General Properties:', ''))
            infos.append(('Format', main.img.format))
            infos.append(('Mode', main.img.mode))
            infos.append(('BPP', str(get_bpp(main.img))))

            infos.append(('Size', f'{main.img.size[0]} x {main.img.size[1]}'))

            if main.filename:
                infos.append(('File name', os.path.basename(main.filename)))
                infos.append(('Full path', main.filename))
                fsize = os.path.getsize(main.filename)
                infos.append(('File size', f'{format_filesize(fsize)} ({fsize:,} Bytes)' if fsize >= 1024 else f'{fsize:,} Bytes'))
                infos.append(('File date/time', str(datetime.fromtimestamp(int(os.path.getmtime(main.filename))))))

#            if main.img.info:
#                infos.append(('', ''))
#                infos.append(('Format specific Properties:', ''))
#                for k, v in main.img.info.items():
#                    infos.append((k, str(v)))

#                print(main.img.getxmp())

                def add_dict(d, indent=''):
                    for k, v in d.items():
                        #if indent == '':
                        k = k[0].upper() + k[1:]
                        if type(v) == dict:
                            infos.append((indent + k, ''))
                            add_dict(v, indent + '  ')
                        elif type(v) == str:
                            v = v.strip()
                            if v:
                                infos.append((indent + k, v))

                xmp = main.img.getxmp()
                if xmp:
                    try:
                        desc = xmp['xapmeta' if 'xapmeta' in xmp else 'xmpmeta']['RDF']['Description']
                        infos.append(('', ''))
                        infos.append(('XMP:', ''))
                        if type(desc) == dict:
                            for k, v in desc.items():
                                k = k[0].upper() + k[1:]
                                if type(v) == dict:
                                    infos.append((k, ''))
                                    add_dict(v, '  ')
                                elif type(v) == str:
                                    v = v.strip()
                                    if v:
                                        infos.append((k, v))
                        elif type(desc) == list:
                            for line in desc:
                                if type(line) == dict:
                                    if 'about' in line:
                                        del line['about']
                                    if line:
                                        add_dict(line, '')

                    except Exception as e:
#                        print(e)
                        pass

                exif = main.img.getexif()
                if len(exif.keys()):
                    infos.append(('', ''))
                    infos.append(('EXIF - General:', ''))
                    for k, v in exif.items():
                        infos.append((TAGS[k] if k in TAGS else str(k), str(v)))

                gps_ifd = exif.get_ifd(ExifTags.IFD.Exif)
                if len(gps_ifd.keys()):
                    infos.append(('', ''))
                    infos.append(('EXIF - IFD:', ''))
                    for k, v in gps_ifd.items():
                        infos.append((TAGS[k] if k in TAGS else str(k), str(v)))

                gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
                if len(gps_ifd.keys()):
                    infos.append(('', ''))
                    infos.append(('EXIF - GPSInfo:', ''))
                    for k, v in gps_ifd.items():
                        infos.append((TAGS[k] if k in TAGS else str(k), str(v)))

                gps_ifd = exif.get_ifd(ExifTags.IFD.IFD1)
                if len(gps_ifd.keys()):
                    infos.append(('', ''))
                    infos.append(('EXIF - Thumbnail:', ''))
                    for k, v in gps_ifd.items():
                        infos.append((TAGS[k] if k in TAGS else str(k), str(v)))

                #        gps_ifd = exif.get_ifd(ExifTags.IFD.Interop)
                #        for k, v in gps_ifd.items():
                #            print(f'Interop - {TAGS[k]}: {v}')

                #        gps_ifd = exif.get_ifd(ExifTags.IFD.MakerNote)
                #        for k, v in gps_ifd.items():
                #            print(f'MakerNote - {TAGS[k]}: {v}')

            infos.append(('', ''))

            i = 0
            for k, v in infos: #.items():
                lvi.iItem = i
                lvi.iSubItem = 0
                lvi.pszText = k
                user32.SendMessageW(hwnd_listview, LVM_INSERTITEMW, 0, byref(lvi))
                lvi.iSubItem = 1
                lvi.pszText = v
                user32.SendMessageW(hwnd_listview, LVM_SETITEMW, 0, byref(lvi))
                i += 1

            ctx['infos'] = infos

        elif msg == WM_SIZE:
            width, height = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
            user32.SetWindowPos(user32.GetDlgItem(hwnd, IDC_LSV1), NULL, 0, 0, width, height - 37, SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)
            user32.SetWindowPos(user32.GetDlgItem(hwnd, IDOK), NULL, 5, height - 31, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
            user32.SetWindowPos(user32.GetDlgItem(hwnd, IDCANCEL), NULL, width - 96, height - 31, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)

        elif msg == WM_COMMAND:
            command = HIWORD(wparam)
            if command == BN_CLICKED:
                control_id = LOWORD(wparam)
                if control_id == IDOK:
                    user32.OpenClipboard(0)
                    try:
                        user32.EmptyClipboard()
                        data = '\r\n'.join([(info[0] + ': ' + info[1]) if info[1] else info[0] for info in ctx['infos']])
                        data = data.encode('utf-16le')
                        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(data) + 2)
                        pcontents = kernel32.GlobalLock(handle)
                        ctypes.memmove(pcontents, data, len(data))
                        kernel32.GlobalUnlock(handle)
                        user32.SetClipboardData(CF_UNICODETEXT, handle)
                    finally:
                        user32.CloseClipboard()

                elif control_id == IDCANCEL:
                    user32.EndDialog(hwnd, 0)

        elif msg == WM_CLOSE:
            user32.EndDialog(hwnd, 0)

        elif main.is_dark:
            return DarkDialogHandleMessages(msg, wparam)
        return FALSE

    user32.DialogBoxParamW(
        HMOD_RESOURCES,
        MAKEINTRESOURCEW(IDD_DLG_IMAGE_INFO),
        main.hwnd,
        DLGPROC(_dialog_proc_callback),
        NULL
    )
