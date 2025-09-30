__all__ = ['Plugin']

import os
import subprocess

from PIL import Image

from winapp.const import *  #MF_POPUP, MF_STRING, MF_SEPARATOR, WM_CLOSE
from winapp.dlls import user32

from const import MENU_FILE

WPHOTO_BIN = os.path.join(os.path.dirname(__file__), 'bin', 'wphoto.exe')
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW


class Plugin():

    ########################################
    #
    ########################################
    def __init__(self, main, **kwargs):

        self.main = main

        proc = subprocess.run(
            [WPHOTO_BIN, '--list-devices'],
            capture_output=True,
            startupinfo=startupinfo,
        )

        lines = proc.stdout.strip().decode().split('\r\n')
        devices = [l for l in lines[1:] if l != '' and not l.startswith('    ')]

        supported_devices = []
        for device in devices:
            proc = subprocess.run(
                [WPHOTO_BIN, f'--device={device}', '--list-features'],
                capture_output=True,
                startupinfo=startupinfo,
            )
            if b'WPD_FUNCTIONAL_CATEGORY_STILL_IMAGE_CAPTURE' in proc.stdout:
                supported_devices.append(device)

        if supported_devices:
            hmenu = user32.GetSubMenu(main.hmenu, MENU_FILE)
            cnt = user32.GetMenuItemCount(hmenu)
            hmenu_child = user32.CreateMenu()
            user32.InsertMenuW(hmenu, cnt - 1, MF_BYPOSITION | MF_POPUP, hmenu_child, 'Acquire from &Camera')
            user32.InsertMenuW(hmenu, cnt, MF_BYPOSITION | MF_SEPARATOR, 0, '')
            for device in supported_devices:
                main.idm_last += 1
                user32.AppendMenuW(hmenu_child, MF_STRING, main.idm_last, device)
                main.COMMAND_MESSAGE_MAP[main.idm_last] = lambda device=device: self.action_take_picture(device)

    ########################################
    #
    ########################################
    def action_take_picture(self, device):

        tmp_dir = os.environ['TMP']

        proc = subprocess.run(
            [WPHOTO_BIN, f'--device={device}', '--capture-image-and-download'],
            capture_output=True,
            startupinfo=startupinfo,
            cwd=tmp_dir,
        )

        if proc.returncode == 0 and proc.stdout.startswith(b'Transferred object'):
            a = proc.stdout.index(b"' to '")
            b = proc.stdout[a + 6:].index(b"'")
            filename = os.path.join(tmp_dir, proc.stdout[a + 6:a + 6 + b].decode())
            if os.path.isfile(filename):
                try:
                    img = Image.open(filename)
                    self.main.load_image(img.copy())
                finally:
                    os.unlink(filename)
