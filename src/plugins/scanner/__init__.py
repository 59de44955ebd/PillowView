__all__ = ['Plugin']

import io
import os
import sys

from PIL import Image

from winapp.dlls import user32
from winapp.const import MF_STRING, MF_BYPOSITION, MF_SEPARATOR

from const import MENU_FILE

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, DIR)
import twain

IDM_SCAN = 1


class Plugin():

    ########################################
    #
    ########################################
    def __init__(self, main, **kwargs):

        self.main = main

        hmenu = user32.GetSubMenu(main.hmenu, MENU_FILE)
#        user32.AppendMenuW(hmenu, MF_STRING, main.idm_last + IDM_SCAN, 'Ac&quire from Scanner...')
        cnt = user32.GetMenuItemCount(hmenu)
        user32.InsertMenuW(hmenu, cnt - 1, MF_BYPOSITION | MF_STRING, main.idm_last + IDM_SCAN, 'Ac&quire from Scanner...')
        user32.InsertMenuW(hmenu, cnt, MF_BYPOSITION | MF_SEPARATOR, 0, '')

        # Add items to COMMAND_MESSAGE_MAP
        main.COMMAND_MESSAGE_MAP.update({
            main.idm_last + IDM_SCAN: self.action_scan,
        })
        main.idm_last += 1

    ########################################
    #
    ########################################
    def action_scan(self):
        self.main.enable_window(False)
        with twain.SourceManager() as sm:
            src = sm.open_source()
            if not src:
                self.main.enable_window(True)
                return

            src.request_acquire(show_ui=False, modal_ui=True)
            try:
                (handle, remaining_count) = src.xfer_image_natively()
            except Exception as e:
                print(e)
                self.main.enable_window(True)
                return

            bmp_bytes = twain.dib_to_bm_file(handle)
            self.main.enable_window(True)

            self.main.load_image(Image.open(io.BytesIO(bmp_bytes), formats=['bmp']))
