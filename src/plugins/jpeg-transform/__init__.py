__all__ = ['Plugin']

import os
import subprocess

from winapp.dlls import user32
from winapp.const import MF_POPUP, MF_STRING, MF_SEPARATOR, MF_BYCOMMAND, MF_GRAYED, MF_ENABLED

from const import MENU_IMAGE, EVENT_IMAGE_CHANGED

JPEGTRAN = os.path.join(os.path.dirname(__file__), 'bin', 'jpegtran.exe')

IDM_JPG_ROTATE_90 = 1
IDM_JPG_ROTATE_180 = 2
IDM_JPG_ROTATE_270 = 3
IDM_JPG_FLIP_HOR = 4
IDM_JPG_FLIP_VERT = 5
IDM_JPG_CROP = 6


class Plugin():

    ########################################
    #
    ########################################
    def __init__(self, main, **kwargs):

        self.main = main

        # Add menu items
        hmenu = user32.GetSubMenu(main.hmenu, MENU_IMAGE)
        cnt = user32.GetMenuItemCount(hmenu)

        user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, '')
        hmenu_child = user32.CreateMenu()
        user32.AppendMenuW(hmenu, MF_POPUP, hmenu_child, 'JPEG Lossless')

        user32.AppendMenuW(hmenu_child, MF_STRING | MF_GRAYED, main.idm_last + IDM_JPG_ROTATE_90, 'Rotate 90°')
        user32.AppendMenuW(hmenu_child, MF_STRING | MF_GRAYED, main.idm_last + IDM_JPG_ROTATE_180, 'Rotate 180°')
        user32.AppendMenuW(hmenu_child, MF_STRING | MF_GRAYED, main.idm_last + IDM_JPG_ROTATE_270, 'Rotate 270°')
        user32.AppendMenuW(hmenu_child, MF_SEPARATOR, 0, '-')
        user32.AppendMenuW(hmenu_child, MF_STRING | MF_GRAYED, main.idm_last + IDM_JPG_FLIP_HOR, 'Flip horizontal')
        user32.AppendMenuW(hmenu_child, MF_STRING | MF_GRAYED, main.idm_last + IDM_JPG_FLIP_VERT, 'Flip vertical')
        user32.AppendMenuW(hmenu_child, MF_SEPARATOR, 0, '-')
        user32.AppendMenuW(hmenu_child, MF_STRING | MF_GRAYED, main.idm_last + IDM_JPG_CROP, 'Crop lossless')

        # Add items to COMMAND_MESSAGE_MAP
        main.COMMAND_MESSAGE_MAP.update({
            main.idm_last + IDM_JPG_ROTATE_90:      lambda: self.action_jpg_rotate(90),
            main.idm_last + IDM_JPG_ROTATE_180:     lambda: self.action_jpg_rotate(180),
            main.idm_last + IDM_JPG_ROTATE_270:     lambda: self.action_jpg_rotate(270),
            main.idm_last + IDM_JPG_FLIP_HOR:       lambda: self.action_jpg_flip('horizontal'),
            main.idm_last + IDM_JPG_FLIP_VERT:      lambda: self.action_jpg_flip('vertical'),
            main.idm_last + IDM_JPG_CROP:           self.action_jpg_crop,
        })

        idm_first = main.idm_last + IDM_JPG_ROTATE_90
        main.idm_last += 6

        def _image_changed():
            flag = MF_BYCOMMAND | (MF_GRAYED if main.img is None or main.img.format != 'JPEG' else MF_ENABLED)
            for i in range(6):
                user32.EnableMenuItem(hmenu_child, idm_first+ i, flag)

        main.connect(EVENT_IMAGE_CHANGED, _image_changed)

    ########################################
    #
    ########################################
    def action_jpg_rotate(self, angle):
        if self.main.img is None or self.main.img.format != 'JPEG':
            return
#        jpeg_rotate(self.main.filename, angle)
        command = [
            JPEGTRAN,
            '-rotate',
            f'{angle}',
            self.main.filename,
            self.main.filename
        ]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.check_call(command, startupinfo=startupinfo)
        self.main.load_file(self.main.filename)

    ########################################
    #
    ########################################
    def action_jpg_flip(self, axis):
        if self.main.img is None or self.main.img.format != 'JPEG':
            return
#        jpeg_flip(self.main.filename, axis)
        command = [
            JPEGTRAN,
            '-flip',
            axis,
            self.main.filename,
            self.main.filename
        ]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.check_call(command, startupinfo=startupinfo)
        self.main.load_file(self.main.filename)

    ########################################
    #
    ########################################
    def action_jpg_crop(self):
        if self.main.img is None or self.main.img.format != 'JPEG' or not self.main.selection.visible:
            return

        rc = self.main.selection.get_rect()
        x, y, w, h = int(rc.left / self.main.canvas.zoom), int(rc.top / self.main.canvas.zoom), int((rc.right - rc.left) / self.main.canvas.zoom), int((rc.bottom- rc.top) / self.main.canvas.zoom)

#        filename_cropped = jpeg_crop(self.main.filename, x, y, w, h)

        basename, ext = os.path.splitext(self.main.filename)
        filename_cropped = f'{basename}_cropped{ext}'
        command = [
            JPEGTRAN,
            '-crop',
            f'{w}x{h}+{x}+{y}',
            self.main.filename,
            filename_cropped
        ]
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.check_call(command, startupinfo=startupinfo)

        self.main.load_file(filename_cropped)
