import os
import importlib
import io
import math
import time

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps, BmpImagePlugin
BmpImagePlugin.USE_RAW_ALPHA = True
import PilImagePlugin

from winapp.dlls import *
from winapp.mainwin import *
from winapp.controls.toolbar import *
from winapp.controls.statusbar import *
from winapp.settings import Settings

from canvas import Canvas, EVENT_CANVAS_ZOOM_CHANGED
import image
from image import *
from selection import Selection
from undo import UndoStack, EVENT_CAN_UNDO_CHANGED, EVENT_CAN_REDO_CHANGED
from const import *


class App(MainWin):

    ########################################
    #
    ########################################
    def __init__(self, args):

        self.state = {
            'window': {'left': CW_USEDEFAULT, 'top': CW_USEDEFAULT, 'width': CW_USEDEFAULT, 'height': CW_USEDEFAULT},
            'bg_color': 0x444444,
            'plugins': ['jpeg_transform'],
            'bgcolor_new' : 0xFFFFFF,
            'use_dark': False,
            'show_toolbar': True,
            'resize_window': True,
            'ask_save': False,
        }

        self.settings = Settings(APP_NAME, self.state)
        self.filename = None
        self.img = None
        self.is_fullscreen = False
        self.is_playing = False
        self.pt_print_paper_size = POINT(21000, 29700)  # in mm/100
        self.rc_print_margins = RECT(1000, 1500, 1000, 1500)  # in mm/100

        image.BG_COLOR = CR_TO_RGB(self.state['bg_color'])

        self.undo_stack = UndoStack()
        self.undo_stack.connect(EVENT_CAN_UNDO_CHANGED, lambda flag:
            (user32.EnableMenuItem(self.hmenu, IDM_UNDO, MF_BYCOMMAND if flag else MF_BYCOMMAND | MF_GRAYED) and False) or
            self.toolbar_main.send_message(TB_ENABLEBUTTON, IDM_UNDO, int(flag))
        )
        self.undo_stack.connect(EVENT_CAN_REDO_CHANGED, lambda flag:
                user32.EnableMenuItem(self.hmenu, IDM_REDO, MF_BYCOMMAND if flag else MF_BYCOMMAND | MF_GRAYED))

        super().__init__(
            APP_NAME,
            **self.state['window'],
            hicon = user32.LoadIconW(HMOD_RESOURCES, MAKEINTRESOURCEW(1)),
            hmenu = user32.LoadMenuW(HMOD_RESOURCES, MAKEINTRESOURCEW(1)),
            haccel = user32.LoadAcceleratorsW(HMOD_RESOURCES, MAKEINTRESOURCEW(1)),
            hbrush = HBRUSH_NULL,
            dark_bg_brush = HBRUSH_NULL,
        )

        self.COMMAND_MESSAGE_MAP = {
            # File
            IDM_NEW:                self.action_new,
            IDM_OPEN:               self.action_open,
            IDM_REOPEN:             self.action_reopen,
            IDM_SAVE:               self.action_save,
            IDM_EXPORT_FOR_WEB:     self.action_export_for_web,
            IDM_CLOSE:              self.action_close,
            IDM_PAGE_SETUP:         self.action_page_setup,
            IDM_PRINT:              self.action_print,
            IDM_EXIT:               self.quit,

            # Edit
            IDM_UNDO:               self.action_undo,
            IDM_REDO:               self.action_redo,
            IDM_COPY:               self.action_copy,
            IDM_PASTE:              self.action_paste,
            IDM_CROP:               self.action_crop,
            IDM_SELECT_ALL:         self.action_select_all,
            IDM_RESIZE:             self.action_resize,
            IDM_ROTATE_RIGHT:       self.action_rotate_right,
            IDM_FLIP_VERTICAL:      self.action_flip_vertical,
            IDM_FLIP_HORIZONTAL:    self.action_flip_horizontal,

            IDM_CHANGE_DEPTH:       self.action_change_depth,

            IDM_CONVERT_RGB:        self.action_convert_rgb,
            IDM_CONVERT_GRAYSCALE:  self.action_convert_grayscale,

            IDM_EXTRACT_ALPHA:      self.action_extract_alpha,
            IDM_REMOVE_ALPHA:       self.action_remove_alpha,

            IDM_INVERT:             self.action_invert,
            IDM_AUTO_CONTRAST:      self.action_auto_contrast,
            IDM_COLOR_BALANCE:      self.action_color_balance,

            IDM_EDIT_PALETTE:       self.action_edit_palette,
            IDM_EXPORT_PALETTE:     self.action_export_palette,
            IDM_IMPORT_PALETTE:     self.action_import_palette,

            IDM_EFFECT_LOMOGRAPH:   self.action_effect_lomograph,
            IDM_EFFECT_POLAROID:    self.action_effect_polaroid,
            IDM_EFFECT_SEPIA:       self.action_effect_sepia,
            IDM_EFFECT_POINTILIZE:  self.action_effect_pointilize,
            IDM_EFFECT_VIGNETTE:    self.action_effect_vignette,

            IDM_FILTER_BLUR:        lambda: self.action_filter(0),
            IDM_FILTER_CONTOUR:     lambda: self.action_filter(1),
            IDM_FILTER_DETAIL:      lambda: self.action_filter(2),
            IDM_FILTER_EDGE_ENHANCE: lambda: self.action_filter(3),
            IDM_FILTER_EMBOSS:      lambda: self.action_filter(4),
            IDM_FILTER_EQUALIZE:    self.action_filter_equalize,
            IDM_FILTER_SHARPEN:     lambda: self.action_filter(5),
            IDM_FILTER_SMOOTH:      lambda: self.action_filter(6),

            IDM_FILTER_PARAM_BRIGHTNESS:  lambda: self.action_filter_param(IDM_FILTER_PARAM_BRIGHTNESS),
            IDM_FILTER_PARAM_CONTRAST:    lambda: self.action_filter_param(IDM_FILTER_PARAM_CONTRAST),
            IDM_FILTER_PARAM_GAMMA:  lambda: self.action_filter_param(IDM_FILTER_PARAM_GAMMA),

            IDM_FILTER_PARAM_GAUSSIAN_BLUR: lambda: self.action_filter_param(IDM_FILTER_PARAM_GAUSSIAN_BLUR),
            IDM_FILTER_PARAM_POSTERIZE:  lambda: self.action_filter_param(IDM_FILTER_PARAM_POSTERIZE),
            IDM_FILTER_PARAM_SATURATION:  lambda: self.action_filter_param(IDM_FILTER_PARAM_SATURATION),
            IDM_FILTER_PARAM_SOLARIZE:  lambda: self.action_filter_param(IDM_FILTER_PARAM_SOLARIZE),
            IDM_FILTER_PARAM_UNSHARP_MASK:  lambda: self.action_filter_param(IDM_FILTER_PARAM_UNSHARP_MASK),

            IDM_GRADATION_CURVE:    self.action_gradation_curve,

            # View
            IDM_IMAGE_INFOS:        self.action_image_infos,
            IDM_HISTOGRAM:          self.action_histogram,

            IDM_ZOOM_IN:            self.action_zoom_in,
            IDM_ZOOM_OUT:           self.action_zoom_out,
            IDM_ORIGINAL_SIZE:      self.action_original_size,

            IDM_ANIM_TOGGLE_PLAY:   self.action_toggle_play,
            IDM_FRAME_PREVIOUS:     lambda: self.action_skip_frames(-1),
            IDM_FRAME_NEXT:         lambda: self.action_skip_frames(1),

            IDM_FRAME_PREVIOUS10:   lambda: self.action_skip_frames(-10),
            IDM_FRAME_NEXT10:       lambda: self.action_skip_frames(10),

            # Options
            IDM_FULLSCREEN:         self.action_toggle_fullscreen,
            IDM_DARK:               self.action_toggle_dark,
            IDM_TOOLBAR:            self.action_toggle_toolbar,
            IDM_RESIZE_WINDOW:      lambda: self.action_toggle_state(IDM_RESIZE_WINDOW, 'resize_window'),
            IDM_ASK_SAVE:           lambda: self.action_toggle_state(IDM_ASK_SAVE, 'ask_save'),
            IDM_WINDOW_COLOR:       self.action_window_color,

            # Plugins
            IDM_MANAGE_PLUGINS:     self.action_manage_plugins,

            # Help
            IDM_ABOUT:              self.action_about,
        }

        toolbar_buttons = (
            ('New...', IDM_NEW),
            ('Open...', IDM_OPEN),
            ('Save...', IDM_SAVE, BTNS_BUTTON, 0),
            ('Print...', IDM_PRINT, BTNS_BUTTON, 0),
            ('-'),
            ('Copy', IDM_COPY, BTNS_BUTTON, 0),
            ('Paste', IDM_PASTE),
            ('Undo', IDM_UNDO, BTNS_BUTTON, 0),
            ('-'),
            ('Image Infos...', IDM_IMAGE_INFOS, BTNS_BUTTON, 0),
            ('Zoom in', IDM_ZOOM_IN, BTNS_BUTTON, 0),
            ('Zoom out', IDM_ZOOM_OUT, BTNS_BUTTON, 0),
            ('Previous Frame', IDM_FRAME_PREVIOUS, BTNS_BUTTON, 0),
            ('Next Frame', IDM_FRAME_NEXT, BTNS_BUTTON, 0),
            ('-'),
            ('About...', IDM_ABOUT),
        )

        self.toolbar_main = ToolBar(
            self,
            style = WS_CHILD | WS_CLIPSIBLINGS | WS_BORDER | TBSTYLE_TOOLTIPS | TBSTYLE_FLAT | (WS_VISIBLE if self.state['show_toolbar'] else 0),
            ex_style = WS_EX_COMPOSITED,
            icon_size = 16,
            toolbar_buttons = toolbar_buttons,

            height = 28,

            h_bitmap = user32.LoadBitmapW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDB_TOOLBAR_MAIN)),
            h_imagelist_disabled = comctl32.ImageList_LoadImageW(
                HMOD_RESOURCES,
                MAKEINTRESOURCEW(IDB_TOOLBAR_MAIN_DISABLED),
                16,
                0,
                CLR_NONE,
                IMAGE_BITMAP,
                LR_CREATEDIBSECTION
            ),

            h_bitmap_dark = user32.LoadBitmapW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDB_TOOLBAR_MAIN_DARK)),
            h_imagelist_disabled_dark = NULL,

            window_title = 'Main',
            num_images = 13,
            hide_text = True
        )

        user32.SendMessageW(self.toolbar_main.hwnd, TB_SETINDENT, 3, 0)

        self.canvas = Canvas(self, top = self.toolbar_main.height if self.state['show_toolbar'] else 0,
                bgcolor=self.state['bg_color'])
        self.canvas.connect(EVENT_CANVAS_ZOOM_CHANGED, lambda zoom:
                self.statusbar.set_text(f'{round(100 * zoom)} %', STATUSBAR_PART_ZOOM))

        self.selection = Selection(self.canvas)
        self.selection_rect = [0, 0, 0, 0]

        ########################################
        #
        ########################################
        def _on_WM_SIZE(hwnd, wparam, lparam):
            self.selection_rect[2:] = (lparam & 0xFFFF) + 6, ((lparam >> 16) & 0xFFFF) + 6
            if self.selection.visible:
                self.update_status_selection()
        self.selection.register_message_callback(WM_SIZE, _on_WM_SIZE)

        ########################################
        #
        ########################################
        def _on_WM_MOVE(hwnd, wparam, lparam):
            self.selection_rect[:2] = (lparam & 0xFFFF) - 3, ((lparam >> 16) & 0xFFFF) - 3
            if self.selection.visible:
                self.update_status_selection()
        self.selection.register_message_callback(WM_MOVE, _on_WM_MOVE)

        ########################################
        #
        ########################################
        def _on_WM_SHOWWINDOW(hwnd, wparam, lparam):
            user32.EnableMenuItem(self.hmenu, IDM_CROP, MF_BYCOMMAND if wparam else MF_BYCOMMAND | MF_GRAYED)
            if not wparam:
                self.statusbar.set_text('', STATUSBAR_PART_SELECTION)
        self.selection.register_message_callback(WM_SHOWWINDOW, _on_WM_SHOWWINDOW)

        ########################################
        #
        ########################################
        def _on_WM_LBUTTONDOWN(hwnd, wparam, lparam):
            x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
            self.selection.start_drawing(x, y)

        self.canvas.static.register_message_callback(WM_LBUTTONDOWN, _on_WM_LBUTTONDOWN)

        ########################################
        #
        ########################################
        def _on_WM_RBUTTONDOWN(hwnd, wparam, lparam):
            x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF

            self.selection.start_drawing(x, y)
            user32.SetCursor(HCURSOR_ZOOM)

            ########################################
            #
            ########################################
            def _on_WM_RBUTTONUP(hwnd, wparam, lparam):
                self.canvas.static.send_message(WM_LBUTTONUP, 0, 0)
                self.canvas.static.unregister_message_callback(WM_RBUTTONUP, _on_WM_RBUTTONUP)

                # Selection rect relative to static
                rc_sel = self.selection.get_rect()

                rc_static = self.canvas.static.get_client_rect()

                # float in range 0..1
                sel_center_x = rc_sel.left / (rc_static.right - (rc_sel.right - rc_sel.left))
                sel_center_y = rc_sel.top / (rc_static.bottom - (rc_sel.bottom - rc_sel.top))

                # Calculate zoom
                rc_canvas = self.canvas.get_client_rect()

                sel_w = (rc_sel.right - rc_sel.left) / self.canvas.zoom
                sel_h = (rc_sel.bottom - rc_sel.top) / self.canvas.zoom

                zoom_x = rc_canvas.right / sel_w
                zoom_y = rc_canvas.bottom / sel_h
                zoom = min(zoom_x, zoom_y)

                self.canvas.set_zoom(zoom)

                # from -1 to 1
                self.canvas.hscroll_to(2 * sel_center_x - 1)
                self.canvas.vscroll_to(2 * sel_center_y - 1)

                self.selection.show(SW_HIDE)

            self.canvas.static.register_message_callback(WM_RBUTTONUP, _on_WM_RBUTTONUP)

        self.canvas.static.register_message_callback(WM_RBUTTONDOWN, _on_WM_RBUTTONDOWN)

        self.statusbar = StatusBar(self)

        self.idm_last = 1000
        plugin_dir = os.path.join(APP_DIR, 'plugins')
        if os.path.isdir(plugin_dir):
            for p in os.listdir(plugin_dir):
                if p in list(self.state['plugins']):
                    plugin = importlib.import_module(f'plugins.{p}')
                    if hasattr(plugin, 'Plugin'):
                        try:
                            plugin.Plugin(self)
                        except Exception as e:
                            self.show_message_box(str(e), f'Plugin {p}', MB_ICONERROR | MB_OK)
                            self.state['plugins'].remove(p)

        # Create file open filter
        filter_open = {k: [] for k in sorted(set(Image.registered_extensions().values()))}
        for ext, fmt in Image.registered_extensions().items():
            filter_open[fmt].append('*' + ext)
        # EPS is the only registered extension that might be save-only
        # (if the ghostscript plugin isn't activated)
        if 'EPS' not in Image.OPEN:
            del filter_open['EPS']
        self.filter_open = ''
        exts_all = []
        for k, v in filter_open.items():
            exts = ';'.join(v)
            exts_all.append(exts)
            self.filter_open += f'{k} ({exts})\0{exts}\0'

        self.filter_open = f"Supported Files\0{';'.join(exts_all)}\0" + self.filter_open

        # Create file save filter
        self.filter_save = ''
        for k, v in dict(sorted(FORMATS_SAVE.items())).items():
            exts = ';'.join(v)
            self.filter_save += f'{k} ({exts})\0{exts}\0'

        ########################################
        #
        ########################################
        def _on_WM_SIZE(hwnd, wparam, lparam):
            width, height = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
            self.update_layout(width, height)
            self.toolbar_main.update_size()
            self.statusbar.update_size(width)

        self.register_message_callback(WM_SIZE, _on_WM_SIZE)

        ########################################
        #
        ########################################
        def _on_WM_COMMAND(hwnd, wparam, lparam):
            if lparam == 0 or lparam == self.toolbar_main.hwnd:
                command_id = LOWORD(wparam)
                if command_id in self.COMMAND_MESSAGE_MAP:
                    self.COMMAND_MESSAGE_MAP[command_id]()

        self.register_message_callback(WM_COMMAND, _on_WM_COMMAND)

        ########################################
        #
        ########################################
        def _on_WM_NOTIFY(hwnd, wparam, lparam):
            nmhdr = cast(lparam, LPNMHDR).contents
            msg = nmhdr.code

            if nmhdr.hwndFrom == self.statusbar.hwnd:
                if msg == NM_RCLICK or msg == NM_DBLCLK:
                    lpnm = cast(lparam, LPNMMOUSE).contents

                    if lpnm.dwItemSpec == STATUSBAR_PART_FRAMES:
                        if 'sizes' in self.img.info:
                            if self.img.format == 'ICNS':
                                sizes = self.img.info["sizes"]
                                menu_data = {"items": []}
                                for i, s in enumerate(sizes):
                                    row = {"caption": f'@{s[2]} x {s[0]} x {s[1]}', "id": i + 1}
                                    if i == self.img.info["size_index"]:
                                        row["flags"] = "CHECKED"
                                    menu_data["items"].append(row)
                                hmenu = self.make_popup_menu(menu_data)
                                idx = self.show_popup_menu(hmenu, uflags=TPM_LEFTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY)
                                if idx == 0:
                                    return
                                self.img.info["size_index"] = idx - 1
                                self.img.size = (sizes[idx - 1][0], sizes[idx - 1][1])
                                self.img.load(scale=sizes[idx - 1][2])

                            elif self.img.format == 'ICO':
                                curr_idx = self.img.info["sizes_sorted"].index(self.img.size)
                                menu_data = {"items": []}
                                for i, s in enumerate(self.img.info["sizes_sorted"]):
                                    row = {"caption": f'{s[0]} x {s[1]}', "id": i + 1}
                                    if i == curr_idx:
                                        row["flags"] = "CHECKED"
                                    menu_data["items"].append(row)
                                hmenu = self.make_popup_menu(menu_data)
                                idx = self.show_popup_menu(hmenu, uflags=TPM_LEFTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY)
                                if idx == 0:
                                    return
                                self.img.size = self.img.info["sizes_sorted"][idx - 1]

                            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True)
                            self.statusbar.set_text(f'{idx} / {len(self.img.info["sizes"])}', STATUSBAR_PART_FRAMES)
                            self.update_status_infos()

                        elif getattr(self.img, "n_frames", 1) > 1:
                            frame_cnt = getattr(self.img, "n_frames", 1)
                            curr_idx = self.img.tell()
                            menu_data = {"items": []}

                            MAX_ITEMS = 21
                            if frame_cnt > MAX_ITEMS:
                                n = frame_cnt // MAX_ITEMS
                                frames = list(range(0, frame_cnt - 1, n)) + [frame_cnt - 1]
                                if curr_idx not in frames:
                                    frames = sorted(frames + [curr_idx])
                            else:
                                frames = range(frame_cnt)
                            for i in frames:
                                if i == curr_idx:
                                    menu_data["items"].append({"caption": str(i + 1), "id": i + 1, "flags": "CHECKED"})
                                else:
                                    menu_data["items"].append({"caption": str(i + 1), "id": i + 1})

                            hmenu = self.make_popup_menu(menu_data)
                            frame = self.show_popup_menu(hmenu, uflags=TPM_LEFTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY)
                            if frame:
                                self.animation_goto(frame - 1)

        self.register_message_callback(WM_NOTIFY, _on_WM_NOTIFY)

        ########################################
        #
        ########################################
        def _on_WM_DROPFILES(hwnd, wparam, lparam):
            dropped_items = self.get_dropped_items(wparam)
            if os.path.isfile(dropped_items[0]):
                self.load_file(dropped_items[0])

        self.register_message_callback(WM_DROPFILES, _on_WM_DROPFILES)

        if self.state['use_dark']:
            user32.CheckMenuItem(self.hmenu, IDM_DARK, MF_BYCOMMAND | MF_CHECKED)
            self.apply_theme(True)
            uxtheme.SetWindowTheme(self.canvas.hwnd, 'DarkMode_Explorer', None)

        if len(args) > 0:
            self.load_file(args[0])

        self.show()

        if self.state['show_toolbar']:
            user32.CheckMenuItem(self.hmenu, IDM_TOOLBAR, MF_BYCOMMAND | MF_CHECKED)
        if self.state['ask_save']:
            user32.CheckMenuItem(self.hmenu, IDM_ASK_SAVE, MF_BYCOMMAND | MF_CHECKED)
        if self.state['resize_window']:
            user32.CheckMenuItem(self.hmenu, IDM_RESIZE_WINDOW, MF_BYCOMMAND | MF_CHECKED)

    ########################################
    #
    ########################################
    def quit(self, *_):
        if self.state['ask_save'] and self.is_dirty():
            res = self.show_message_box('Save changes?', APP_NAME, utype=MB_ICONQUESTION | MB_YESNOCANCEL)
            if res == IDCANCEL:
                return 1
            elif res == IDYES:
                self.action_save()
        self.show(SW_RESTORE)
        rc = self.get_window_rect()
        self.state['window'] = {'left': max(rc.left, 0), 'top': max(rc.top, 0), 'width': rc.right - rc.left, 'height': rc.bottom - rc.top}
        self.state['use_dark'] = self.is_dark
        self.state['show_toolbar'] = self.toolbar_main.visible
        self.settings.save(self.state)
        super().quit()

    ########################################
    #
    ########################################
    def update_layout(self, width=None, height=None):
        if width is None:
            rc = self.get_client_rect()
            width, height = rc.right, rc.bottom
        if self.toolbar_main.visible:
            height -= self.toolbar_main.height
        if self.statusbar.visible:
            height -= self.statusbar.height
        self.canvas.set_window_pos(width=width, height=height, flags=SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)

    ########################################
    #
    ########################################
    def update_window_title(self):
        self.set_window_text(f'{self.filename if self.filename else "Memory Image"} - {APP_NAME}' if self.img else APP_NAME)

    ########################################
    #
    ########################################
    def update_status_infos(self):
        self.statusbar.set_text(f' {self.img.width} x {self.img.height} x {get_bpp(self.img)} BPP', STATUSBAR_PART_INFOS)
        self.statusbar.set_text(self.img.mode, STATUSBAR_PART_MODE)

    ########################################
    #
    ########################################
    def update_status_selection(self):
        x, y, w, h = (round(x / self.canvas.zoom) for x in self.selection_rect)
        self.statusbar.set_text(f'{x}, {y}  {w} x {h}', STATUSBAR_PART_SELECTION)

    ########################################
    #
    ########################################
    def update_menus(self):
        flag = MF_BYCOMMAND if self.img else MF_BYCOMMAND | MF_GRAYED
        for idm in (
            IDM_REOPEN, IDM_SAVE, IDM_EXPORT_FOR_WEB, IDM_PRINT, IDM_CLOSE, IDM_PRINT, IDM_COPY,
            IDM_SELECT_ALL, IDM_RESIZE, IDM_ROTATE_RIGHT, IDM_FLIP_VERTICAL, IDM_FLIP_HORIZONTAL,
            IDM_CHANGE_DEPTH, IDM_CONVERT_RGB, IDM_CONVERT_GRAYSCALE,
            IDM_INVERT, IDM_AUTO_CONTRAST, IDM_EFFECT_LOMOGRAPH,
            IDM_EFFECT_POLAROID, IDM_EFFECT_SEPIA, IDM_EFFECT_POINTILIZE, IDM_EFFECT_VIGNETTE, IDM_FILTER_BLUR,
            IDM_FILTER_CONTOUR, IDM_FILTER_DETAIL, IDM_FILTER_EDGE_ENHANCE, IDM_FILTER_EMBOSS,
            IDM_FILTER_SHARPEN, IDM_FILTER_SMOOTH, IDM_FILTER_EQUALIZE, IDM_FILTER_PARAM_BRIGHTNESS,
            IDM_FILTER_PARAM_CONTRAST, IDM_FILTER_PARAM_SATURATION, IDM_FILTER_PARAM_GAMMA,
            IDM_FILTER_PARAM_GAUSSIAN_BLUR, IDM_FILTER_PARAM_UNSHARP_MASK, IDM_FILTER_PARAM_POSTERIZE, IDM_FILTER_PARAM_SOLARIZE,
            IDM_GRADATION_CURVE,
            IDM_IMAGE_INFOS, IDM_HISTOGRAM, IDM_ZOOM_IN, IDM_ZOOM_OUT, IDM_ORIGINAL_SIZE, IDM_COLOR_BALANCE
        ):
            user32.EnableMenuItem(self.hmenu, idm, flag)

        flag = MF_BYCOMMAND if self.can_play else MF_BYCOMMAND | MF_GRAYED
        user32.EnableMenuItem(self.hmenu, IDM_ANIM_TOGGLE_PLAY, flag)

        flag = MF_BYCOMMAND if self.has_frames else MF_BYCOMMAND | MF_GRAYED
        for idm in (IDM_FRAME_PREVIOUS, IDM_FRAME_NEXT, IDM_FRAME_PREVIOUS10, IDM_FRAME_NEXT10):
            user32.EnableMenuItem(self.hmenu, idm, flag)

        flag = MF_BYCOMMAND if self.img and self.img.mode in ('RGBA', 'LA', 'PA') else MF_BYCOMMAND | MF_GRAYED
        for idm in (IDM_EXTRACT_ALPHA, IDM_REMOVE_ALPHA):
            user32.EnableMenuItem(self.hmenu, idm, flag)

        flag = MF_BYCOMMAND if self.img and self.img.mode in ('P', 'PA') else MF_BYCOMMAND | MF_GRAYED
        for idm in (IDM_EDIT_PALETTE, IDM_EXPORT_PALETTE, IDM_IMPORT_PALETTE):
            user32.EnableMenuItem(self.hmenu, idm, flag)

        flag = int(self.img is not None)
        for idm in (IDM_SAVE, IDM_PRINT, IDM_COPY, IDM_IMAGE_INFOS, IDM_ZOOM_IN, IDM_ZOOM_OUT):
            self.toolbar_main.send_message(TB_ENABLEBUTTON, idm, flag)
        flag = int(self.has_frames)
        for idm in (IDM_FRAME_PREVIOUS, IDM_FRAME_NEXT):
            self.toolbar_main.send_message(TB_ENABLEBUTTON, idm, flag)

    ########################################
    #
    ########################################
    def get_win_rect_for_image(self):
        if self.visible:
            rc_win = self.get_window_rect()
            x, y = rc_win.left, rc_win.top
        else:
            x, y = self.state['window']['left'], self.state['window']['top']

        img_max_w = RC_DESKTOP.right - 5 - 16
        dh = 82 + (self.toolbar_main.height if self.toolbar_main.visible else 0)
        img_max_h = RC_DESKTOP.bottom - 5 - dh
        zoom = min(1, min(img_max_w / self.img.width, img_max_h / self.img.height))
        win_w = max(480, int(self.img.width * zoom) + 16)
        win_h = int(self.img.height * zoom) + dh
        x = max(0, min(x, RC_DESKTOP.right - win_w))
        y = max(5, min(y, RC_DESKTOP.bottom - win_h))

        return x, y, win_w, win_h, zoom

    ########################################
    #
    ########################################
    def load_file(self, filename):
        if self.state['ask_save'] and self.is_dirty():
            res = self.show_message_box('Save changes?', APP_NAME, utype=MB_ICONQUESTION | MB_YESNOCANCEL)
            if res == IDCANCEL:
                return 1
            elif res == IDYES:
                self.action_save()
        self.statusbar.set_text('')

        if filename.lower().endswith('.lnk'):
            from winapp.lnk_support import get_lnk_target_path
            filename = get_lnk_target_path(filename)

        ext = os.path.splitext(filename)[1].lower()

        img = None
        if ext == '.txt':
            with open(filename, 'r') as f:
                img = text_to_image(f.read())

        elif ext == '.raw':
            from dialogs import dialog_raw_open
            img = dialog_raw_open.show(self, filename)

        elif ext == '.wal':
            from PIL import WalImageFile
            img = WalImageFile.open(filename)

        if img is None:
            try:
                img = Image.open(filename)  # crash for .webp ???
            except Exception as e:
                print(e)
                self.statusbar.set_text(str(e))
                return

        if img.mode not in MODE_TO_BPP:
            img = img.convert('L' if img.mode in ('F', 'I') else 'RGB')

        if img.mode == '1' and img.format == 'BMP':
            img = ImageOps.invert(img)

        if self.is_playing:
            self.animation_stop()

        if self.img is None:
            self.statusbar.set_parts(STATUSBAR_PARTS, parts_right_aligned=True)
            rc = self.get_client_rect()
            self.statusbar.update_size(rc.right)

        self.img = img
        self.undo_stack.clear(self.img)
        self.filename = filename
        self.has_frames = False
        self.can_play = False

        if img.mode == 'P':
            if 'transparency' in img.info:
                pal = img.getpalette()
                img.info['transcolor'] = pal[img.info['transparency'] * 3:img.info['transparency'] * 3 + 3]
                pal[img.info['transparency'] * 3:img.info['transparency'] * 3 + 3] = CR_TO_RGB(self.state['bg_color'])
                img.putpalette(pal)

        elif img.mode == 'RGBA':
            if img.format == 'BMP':
                # Handle 32-bit BMP as transparent only if alpha channel isn't completely black
                colors = img.getchannel('A').getcolors()
                if len(colors) == 1:
                    img = img.convert('RGB')

        if self.img.format == 'ICNS':
            self.img.load()

        if self.state['resize_window']:
            x, y, width, height, zoom = self.get_win_rect_for_image()
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=False, zoom=zoom)
            self.set_window_pos(x=x, y=y, width=width, height=height, flags=SWP_NOZORDER | SWP_NOACTIVATE)
        else:
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=True)

        self.selection.show(SW_HIDE)
        self.update_window_title()
        self.update_status_infos()

        self.statusbar.set_text(self.img.format, STATUSBAR_PART_FORMAT)

        if 'sizes' in self.img.info:  # ICO and ICNS
            if self.img.format == 'ICNS':
                idx = 0  #len(self.img.info["sizes"]) - 1 #.index(self.img.size)
                self.img.info["size_index"] = idx
            else:
                self.img.info["sizes_sorted"] = sorted(list(self.img.info["sizes"]), reverse=True)
                idx = self.img.info["sizes_sorted"].index(self.img.size)
            self.statusbar.set_text(f'{idx + 1} / {len(self.img.info["sizes"])}', STATUSBAR_PART_FRAMES)
        else:
            frame_cnt = getattr(self.img, "n_frames", 1)
            self.statusbar.set_text(f'1 / {frame_cnt}', STATUSBAR_PART_FRAMES)
            self.has_frames = frame_cnt > 1
            if self.has_frames:
                # Autorun animations
                if self.img.format in FORMATS_ANIMATION:
                    self.can_play = True
                    self.animation_play()

        self.emit(EVENT_IMAGE_CHANGED)  # Used by plugins

        self.update_menus()

    ########################################
    # Currently called by PASTE and by scanner plugin
    ########################################
    def load_image(self, img):
        if self.state['ask_save'] and self.is_dirty():
            res = self.show_message_box('Save changes?', APP_NAME, utype=MB_ICONQUESTION | MB_YESNOCANCEL)
            if res == IDCANCEL:
                return 1
            elif res == IDYES:
                self.action_save()
        self.statusbar.set_text('')
        if self.img is None:
            self.statusbar.set_parts(STATUSBAR_PARTS, parts_right_aligned=True)
        self.img = img

        self.undo_stack.clear(self.img)
        self.filename = None
        self.has_frames = False
        self.can_play = False

        if self.state['resize_window']:
            x, y, width, height, zoom = self.get_win_rect_for_image()
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=False, zoom=zoom)
            self.set_window_pos(x=x, y=y, width=width, height=height, flags=SWP_NOZORDER | SWP_NOACTIVATE)
        else:
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=True)

        self.update_window_title()
        self.update_menus()
        self.update_status_infos()
        self.emit(EVENT_IMAGE_CHANGED)

    ########################################
    #
    ########################################
    def is_dirty(self):
        if self.img is None:
            return False
        return self.filename is None or self.undo_stack.can_undo

    ########################################
    #
    ########################################
    def action_new(self):
        if self.state['ask_save'] and self.is_dirty():
            res = self.show_message_box('Save changes?', APP_NAME, utype=MB_ICONQUESTION | MB_YESNOCANCEL)
            if res == IDCANCEL:
                return 1
            elif res == IDYES:
                self.action_save()
        from dialogs import dialog_new
        dialog_new.show(self)

    ########################################
    #
    ########################################
    def action_open(self):
        filename = self.show_open_file_dialog('Open', '', self.filter_open)
        if filename:
            self.load_file(filename)

    ########################################
    #
    ########################################
    def action_reopen(self):
        if self.filename:
            self.load_file(self.filename)

    ########################################
    #
    ########################################
    def action_save(self):
        if self.img is None:
            return
        if self.can_play:
            if self.is_playing:
                self.animation_stop()
            self.animation_goto(0)
        from dialogs import dialog_save
        filename = dialog_save.show(self)
        if not filename:
            return

        # Logic: we only update the filename, but keep the current image, i.e. the original
        # format and mode/BPP. "Reopen" in the menu loads the actual saved image.
        self.filename = filename
        self.undo_stack.clear(self.img)
        self.update_window_title()

    ########################################
    #
    ########################################
    def action_export_for_web(self):
        if self.img is None:
            return
        from dialogs import dialog_web
        dialog_web.show(self)

    ########################################
    #
    ########################################
    def action_close(self):
        if self.img is None:
            return
        if self.is_playing:
            self.animation_stop()
        self.img.close()
        self.canvas.clear()
        self.filename = None
        self.img = None
        self.has_frames = False
        self.can_play = False
        self.undo_stack.clear()
        self.update_window_title()
        self.update_menus()
        self.statusbar.set_parts()
        self.emit(EVENT_IMAGE_CHANGED)

    ########################################
    #
    ########################################
    def action_undo(self):
        hwnd_focus = user32.GetFocus()
        buf = create_unicode_buffer(5)
        user32.GetClassNameW(hwnd_focus, buf, 5)
        if buf.value == 'Edit':
            return user32.SendMessageW(hwnd_focus, EM_UNDO, 0, 0)
        self.img = self.undo_stack.undo()

        if self.state['resize_window']:
            x, y, width, height, zoom = self.get_win_rect_for_image()
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=False, zoom=zoom)
        else:
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=True)

        self.update_status_infos()
        self.update_menus()

    ########################################
    #
    ########################################
    def action_redo(self):
        hwnd_focus = user32.GetFocus()
        buf = create_unicode_buffer(5)
        user32.GetClassNameW(hwnd_focus, buf, 5)
        if buf.value == 'Edit':
            return user32.SendMessageW(hwnd_focus, EM_UNDO, 0, 0)
        self.img = self.undo_stack.redo()

        if self.state['resize_window']:
            x, y, width, height, zoom = self.get_win_rect_for_image()
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=False, zoom=zoom)
        else:
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=True)

        self.update_status_infos()
        self.update_menus()

    ########################################
    #
    ########################################
    def action_copy(self):
        hwnd_focus = user32.GetFocus()
        buf = create_unicode_buffer(5)
        user32.GetClassNameW(hwnd_focus, buf, 5)
        if buf.value == 'Edit':
            return user32.SendMessageW(hwnd_focus, WM_COPY, 0, 0)

        if self.img is None:
            return

        if self.selection.visible:
            rc = self.selection.get_rect()
            x, y, cx, cy = (
                int(rc.left / self.canvas.zoom),
                int(rc.top / self.canvas.zoom),
                int((rc.right - rc.left) / self.canvas.zoom),
                int((rc.bottom - rc.top) / self.canvas.zoom)
            )
        else:
            x, y, cx, cy = 0, 0, self.img.width, self.img.height

        hbitmap = self.canvas.static.h_bitmap
        hbitmap_copy = gdi32.CreateBitmap(cx, cy, 1, 32, NULL)

        srcDC = gdi32.CreateCompatibleDC(user32.GetDC(NULL))
        newDC = gdi32.CreateCompatibleDC(user32.GetDC(NULL))

        srcBitmap = gdi32.SelectObject(srcDC, hbitmap)
        newBitmap = gdi32.SelectObject(newDC, hbitmap_copy)

        gdi32.BitBlt(newDC, 0, 0, cx, cy, srcDC, x, y, SRCCOPY)

        gdi32.SelectObject(srcDC, srcBitmap)
        gdi32.SelectObject(newDC, newBitmap)

        gdi32.DeleteDC(srcDC)
        gdi32.DeleteDC(newDC)

        user32.OpenClipboard(self.hwnd)
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_BITMAP, hbitmap_copy)
        user32.CloseClipboard()

    ########################################
    #
    ########################################
    def action_paste(self):
        hwnd_focus = user32.GetFocus()
        buf = create_unicode_buffer(5)
        user32.GetClassNameW(hwnd_focus, buf, 5)
        if buf.value == 'Edit':
            return user32.SendMessageW(hwnd_focus, WM_PASTE, 0, 0)

        img = None
        user32.OpenClipboard(self.hwnd)

        if user32.IsClipboardFormatAvailable(CF_BITMAP):
            h_bitmap = user32.GetClipboardData(CF_BITMAP)
            if h_bitmap:
                img = hbitmap_to_image(h_bitmap)

        elif user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            user32.OpenClipboard(self.hwnd)
            data = user32.GetClipboardData(CF_UNICODETEXT)
            data_locked = kernel32.GlobalLock(data)
            text = c_wchar_p(data_locked)
            kernel32.GlobalUnlock(data_locked)
            img = text_to_image(text.value)

        user32.CloseClipboard()

        if img:
            self.load_image(img)

    ########################################
    #
    ########################################
    def action_crop(self):
        rc = self.selection.get_rect()
        self.selection.show(SW_HIDE)
        self.img = self.img.crop((
            rc.left / self.canvas.zoom,
            rc.top / self.canvas.zoom,
            rc.right / self.canvas.zoom,
            rc.bottom / self.canvas.zoom
        ))
        self.undo_stack.push(self.img)

        if self.state['resize_window']:
            x, y, width, height, zoom = self.get_win_rect_for_image()
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=False, zoom=zoom)
            self.set_window_pos(x=x, y=y, width=width, height=height, flags=SWP_NOZORDER | SWP_NOACTIVATE)
        else:
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True, zoom_to_fit=True)

        self.update_status_infos()
        self.statusbar.set_text(f'{round(100 * self.canvas.zoom)} %', STATUSBAR_PART_ZOOM)

    ########################################
    #
    ########################################
    def action_select_all(self):
        hwnd_focus = user32.GetFocus()
        buf = create_unicode_buffer(5)
        user32.GetClassNameW(hwnd_focus, buf, 5)
        if buf.value == 'Edit':
            return user32.SendMessageW(hwnd_focus, EM_SETSEL, 0, -1)
        rc = self.canvas.static.get_client_rect()
        self.selection.set_window_pos(0, 0, rc.right, rc.bottom, flags=SWP_NOACTIVATE | SWP_NOZORDER)
        self.selection.show()

    ########################################
    #
    ########################################
    def action_resize(self):
        def _on_resize(size, resample, sharpen):
            if self.img.mode == '1':
                self.img = self.img.convert('L')
            elif self.img.mode == 'P':
                self.img = self.img.convert('RGB')
            self.img = self.img.resize(size, resample = resample)
            if sharpen:
                self.img = ImageEnhance.Sharpness(self.img).enhance(2.0)
            self.undo_stack.push(self.img)
            self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True)
            self.update_status_infos()
        from dialogs import dialog_resize
        dialog_resize.show(self, _on_resize)

    ########################################
    #
    ########################################
    def action_rotate_right(self):
        self.img = self.img.transpose(method=Image.Transpose.ROTATE_270)
        self.undo_stack.push(self.img)
        self.canvas.load_hbitmap(image_to_hbitmap(self.img), force_update=True)
        self.update_status_infos()

    ########################################
    #
    ########################################
    def action_flip_vertical(self):
        self.img = self.img.transpose(method=Image.Transpose.FLIP_TOP_BOTTOM)
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))

    ########################################
    #
    ########################################
    def action_flip_horizontal(self):
        self.img = self.img.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))

    ########################################
    #
    ########################################
    def action_change_depth(self):

        # fills palette with black to force specified size
        def _force_pal_size(img, pal_size):
            pal = img.getpalette()
            num_colors = len(pal) // 3
            if num_colors < pal_size:
                pal += [0] * ((pal_size - num_colors) * 3)
                img.putpalette(pal)

        def _on_change_depth(control_id, dither, colors):
            img = self.img

            # Dithering method, used when converting from mode RGB to P or from RGB or L to 1.
            # Available methods are Dither.NONE or Dither.FLOYDSTEINBERG (default).
            dither = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE

            if img.mode in ('CMYK', '1', 'P') and control_id in (
                    IDC_DEPTH_BTN_P_8, IDC_DEPTH_BTN_P_4,
                    IDC_DEPTH_BTN_P_1, IDC_DEPTH_BTN_P_CUSTOM
            ):
                img = img.convert('RGB')

            if control_id == IDC_DEPTH_BTN_RGBA:
                alpha = img.getchannel("A")
                img = img.convert('RGBA')
                img.putalpha(alpha)

            elif control_id == IDC_DEPTH_BTN_CMYK:
                img = img.convert('CMYK')

            elif control_id == IDC_DEPTH_BTN_RGB:
                img = img.convert('RGB')

            elif control_id == IDC_DEPTH_BTN_LA:
                alpha = img.getchannel("A")
                img = img.convert('LA')
                img.putalpha(alpha)

            elif control_id == IDC_DEPTH_BTN_PA:
                alpha = img.getchannel("A")
                if img.mode == 'LA':
                    img = img.convert('P')
                else:
                    img = img.convert('P', colors=256, palette=Image.ADAPTIVE, dither=dither)
                img.putalpha(alpha)

            elif control_id == IDC_DEPTH_BTN_L:
                img = img.convert('L')

            elif control_id == IDC_DEPTH_BTN_P_8:
                if img.mode in ('L', 'LA'):
                    img = img.convert('P')
                else:
                    img = img.convert('P', colors=256, palette=Image.ADAPTIVE, dither=dither)
                    _force_pal_size(img, 256)

            elif control_id == IDC_DEPTH_BTN_P_4:
                if img.mode in ('L', 'LA'):
                    img = img.convert('P', colors=16)
                else:
                    img = img.convert('P', colors=16, palette=Image.ADAPTIVE, dither=dither)
                    _force_pal_size(img, 16)

            elif control_id == IDC_DEPTH_BTN_P_1:
                if img.mode in ('L', 'LA'):
                    img = img.convert('P', colors=2)
                else:
                    img = img.convert('P', colors=2, palette=Image.ADAPTIVE, dither=dither)

            elif control_id == IDC_DEPTH_BTN_P_CUSTOM:
                if img.mode in ('L', 'LA'):
                    img = img.convert('P', colors=colors)
                else:
                    img = img.convert('P', colors=colors, palette=Image.ADAPTIVE, dither=dither)
                    _force_pal_size(img, colors)

            elif control_id == IDC_DEPTH_BTN_1:
                img = img.convert('1', dither=dither)

            self.img = img
            self.undo_stack.push(self.img)

            self.canvas.update_hbitmap(image_to_hbitmap(self.img))

            self.update_status_infos()
            self.update_menus()

        from dialogs import dialog_depth
        dialog_depth.show(self, _on_change_depth)

    ########################################
    #
    ########################################
    def action_convert_rgb(self):
        if self.img is None or self.img.mode == 'RGB':
            return
        self.img = self.img.convert('RGB')
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.update_status_infos()

    ########################################
    #
    ########################################
    def action_convert_grayscale(self):
        if self.img is None or self.img.mode in ('L', 'LA'):
            return
        if self.img.mode == 'RGBA':
            alpha = self.img.getchannel("A")
            self.img = self.img.convert('LA')
            self.img.putalpha(alpha)
        else:
            self.img = self.img.convert('L')
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.update_status_infos()
        self.update_menus()

    ########################################
    #
    ########################################
    def action_extract_alpha(self):
        self.img = self.img.getchannel('A')
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.update_status_infos()
        self.update_menus()

    ########################################
    #
    ########################################
    def action_remove_alpha(self):
        self.img = self.img.convert(self.img.mode[:-1])  # removes trailing 'A'
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.update_status_infos()
        self.update_menus()

    ########################################
    #
    ########################################
    def action_invert(self):
        if self.img.mode == 'CMYK':
            self.img = ImageOps.invert(self.img.convert('RGB')).convert('CMYK')

        elif self.img.mode == 'P':
            self.img = ImageOps.invert(self.img.convert('RGB')).convert('P',
                    palette=Image.ADAPTIVE, dither=Image.Dither.NONE)

        elif self.img.mode == 'PA':
            alpha = self.img.getchannel("A")
            self.img = ImageOps.invert(self.img.convert('RGB')).convert('P',
                    palette=Image.ADAPTIVE, dither=Image.Dither.NONE)
            self.img.putalpha(alpha)

        elif self.img.mode == 'RGBA':
            alpha = self.img.getchannel("A")
            self.img = ImageOps.invert(self.img.convert('RGB'))
            self.img.putalpha(alpha)

        elif self.img.mode == 'LA':
            alpha = self.img.getchannel("A")
            self.img = ImageOps.invert(self.img.convert('L'))
            self.img.putalpha(alpha)

        else:
            self.img = ImageOps.invert(self.img)
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))

    ########################################
    # 1 makes no sense, ignore
    ########################################
    def action_auto_contrast(self):
        if self.img.mode == 'CMYK':
            self.img = ImageOps.autocontrast(self.img.convert('RGB')).convert('CMYK')

        elif self.img.mode == 'RGBA':
            alpha = self.img.getchannel('A')
            self.img = ImageOps.autocontrast(self.img.convert("RGB"))
            self.img.putalpha(alpha)

        elif self.img.mode == 'LA':
            alpha = self.img.getchannel('A')
            self.img = ImageOps.autocontrast(self.img.convert("L"))
            self.img.putalpha(alpha)

        elif self.img.mode == 'PA':
            alpha = self.img.getchannel('A')
            self.img = ImageOps.autocontrast(self.img.convert('RGB')).convert('P',
                    palette=Image.ADAPTIVE, dither=Image.Dither.NONE)
            self.img.putalpha(alpha)

        elif self.img.mode == 'P':
            self.img = ImageOps.autocontrast(self.img.convert('RGB')).convert('P',
                    palette=Image.ADAPTIVE, dither=Image.Dither.NONE)

        elif self.img.mode == '1':
            return

        else:
            self.img = ImageOps.autocontrast(self.img)

        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))

    ########################################
    # CMYK, P, L, 1 => RGB, LA => RGBA
    ########################################
    def action_effect_lomograph(self):
        img = self.img
        alpha = img.getchannel("A") if "A" in img.getbands() else None
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = img.convert('RGB', matrix=(
            1.5, 0,    0,    0,
            0,   1.45, 0,    0,
            0,   0,    1.09, 0,
        ))
        tmp = create_vignette(img.size).convert('RGB')
        img = ImageChops.multiply(img, tmp)
        img = Image.merge("RGB", [
            ImageEnhance.Brightness(img.getchannel("R")).enhance(.9),
            ImageEnhance.Brightness(img.getchannel("G")).enhance(1),
            ImageEnhance.Brightness(img.getchannel("B")).enhance(0.8),
        ])
        if alpha:
            img.putalpha(alpha)
        self.img = img
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.update_status_infos()

    ########################################
    # CMYK, P, L, 1 => RGB, LA => RGBA
    ########################################
    def action_effect_polaroid(self):
        img = self.img
        alpha = img.getchannel("A") if "A" in img.getbands() else None
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = img.convert('RGB', matrix=(
             1.638, -0.122,  1.016, 0,
            -0.062,  1.378, -0.016, 0,
            -0.262, -0.122,  1.383, 0,
        ))
        # An enhancement factor of 0.0 gives a solid gray image, a factor of 1.0 gives
        # the original image, and greater values increase the contrast of the image.
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(.65)
        tmp = create_vignette(img.size).convert('RGB')
        img = ImageChops.multiply(img, tmp)
        img = Image.merge("RGB", [
            ImageEnhance.Brightness(img.getchannel("R")).enhance(1.142),
            ImageEnhance.Brightness(img.getchannel("G")).enhance(0.964),
            ImageEnhance.Brightness(img.getchannel("B")).enhance(0.894),
        ])

        self.img = img
        if alpha:
            self.img.putalpha(alpha)
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.update_status_infos()

    ########################################
    # CMYK, P, L, 1 => RGB, LA => RGBA
    ########################################
    def action_effect_sepia(self):
        img = self.img
        alpha = img.getchannel("A") if "A" in img.getbands() else None
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = img.convert('RGB', matrix=(
            .393, .769, .189, 0,
            .349, .686, .168, 0,
            .272, .534, .131, 0
        ))
        if alpha:
            img.putalpha(alpha)
        self.img = img
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.update_status_infos()

    ########################################
    # Create a Pointilize version of the image
    # Supports all modes
    ########################################
    def action_effect_pointilize(self):
        # Config
        radius = 6
        step_size = radius + 3
        # Intentional error on the positionning of dots to create a wave-like effect
        errors = (-1, -2, -1, -1, 0, 1, 1, -1, 0, -1)
        img = self.img.copy()
        width, height = self.img.size
        draw = ImageDraw.Draw(img)
        colors_tmp = self.img.resize((math.ceil(width / step_size), math.ceil(height / step_size))).getdata()
        cnt = 0
        for y in range(radius, height, step_size):
            for x in range(radius, width, step_size):
                color = colors_tmp[cnt]
                ex = errors[cnt % len(errors)]
                cnt += 1
                ey = errors[cnt % len(errors)]
                draw.circle((x + ex, y + ey), radius, fill=color)
        self.img = img
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.update_status_infos()

    ########################################
    # CMYK, P, L, 1 => RGB, LA => RGBA
    ########################################
    def action_effect_vignette(self):
        img = self.img
        alpha = img.getchannel("A") if "A" in img.getbands() else None
        if img.mode != 'RGB':
            img = img.convert('RGB')
        tmp = create_vignette(img.size).convert('RGB')
        img = ImageChops.multiply(img, tmp)
        if alpha:
            img.putalpha(alpha)
        self.img = img
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.update_status_infos()

    ########################################
    # 1, L, P -> P (new palette)
    # CMYK => RGB => CMYK
    ########################################
    def action_color_balance(self):
        from dialogs import dialog_color_balance
        dialog_color_balance.show(self)

    ########################################
    #
    ########################################
    def action_edit_palette(self):
        from dialogs import dialog_palette
        dialog_palette.show(self)

    ########################################
    #
    ########################################
    def action_export_palette(self):
        filename = self.show_save_file_dialog(
            'Export Palette',
            default_extension = 'act',
            initial_path = 'export',
            filter_string = 'Adobe Color Table (*.act)\0*.act\0Microsoft Palette (*.pal)\0*.pal\0\0'
        )
        if not filename:
            return

        ext = os.path.splitext(filename)[1].lower()
        colors = self.img.getpalette()
        palette_size = len(colors) // 3

        if ext == '.pal':
            import struct
            data_size = palette_size * 4
            file_size = data_size + 24
            with open(filename, 'wb+') as f:
                f.write(b'RIFF')
                f.write(struct.pack('<I', file_size - 8))
                f.write(b'PAL ')
                f.write(b'data')
                f.write(struct.pack('<I', file_size - 20))
                f.write(struct.pack('<BBH', 0, 3, palette_size))
                for i in range(palette_size):
                    f.write(struct.pack('>BBBB', colors[3 * i] , colors[3 * i + 1], colors[3 * i + 2], 0))
        else:
            data = bytearray(772)
            for i, c in enumerate(colors):
                data[i] = c
            if palette_size == 256:
                data[768] = 1
            else:
                data[769] = palette_size
            data[770] = 255
            data[771] = 255
            with open(filename, 'wb+') as f:
                f.write(bytes(data))

    ########################################
    #
    ########################################
    def action_import_palette(self):
        filename = self.show_open_file_dialog(
            'Import Palette',
            default_extension = 'act',
            filter_string = 'Adobe Color Table (*.act)\0*.act\0Microsoft Palette (*.pal)\0*.pal\0\0'
        )
        if not filename:
            return
        ext = os.path.splitext(filename)[1].lower()
        try:
            with open(filename, 'rb') as f:
                f.seek(24)
                data = f.read()
            if ext == '.pal':
                data = data[24:]
                pal = [b for i, b in enumerate(data) if i % 4 != 3]
            else:
                num_colors = data[768] << 8 + data[769] if len(data) >= 770 else 256
                pal = [data[i] for i in range(num_colors * 3)]
            self.img = self.img.copy()
            self.img.putpalette(pal)
            self.undo_stack.push(self.img)
            self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        except Exception as e:
            self.statusbar.set_text(f'Error loading palette: {e}')

    ########################################
    #
    ########################################
    def action_filter(self, idx):
        filter_name = ['BLUR', 'CONTOUR', 'DETAIL', 'EDGE_ENHANCE', 'EMBOSS', 'SHARPEN', 'SMOOTH'][idx]
        img = self.img
        alpha = img.getchannel("A") if "A" in img.getbands() else None
        if img.mode in ('P', 'PA'):
            img = img.convert('RGB')
            img = img.filter(filter=getattr(ImageFilter, filter_name))
            img = img.convert('P', palette=Image.ADAPTIVE, dither=Image.Dither.NONE)
        elif img.mode ==  'CMYK' and filter_name == 'CONTOUR':
            img = img.convert('RGB')
            img = img.filter(filter=getattr(ImageFilter, filter_name))
            img = img.convert('CMYK')
        else:
            img = img.filter(filter=getattr(ImageFilter, filter_name))
        if alpha:
            img.putalpha(alpha)
        self.img = img
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))

    ########################################
    # 1 makes no sense, ignore
    ########################################
    def action_filter_equalize(self):
        if self.img.mode == '1':
            return
        img = self.img
        alpha = img.getchannel("A") if "A" in img.getbands() else None
        if img.mode == 'CMYK':
            img = ImageOps.equalize(self.img.convert('RGB')).convert('CMYK')
        elif img.mode in ('P', 'PA'):
            img = ImageOps.equalize(self.img.convert('RGB')).convert('P', palette=Image.ADAPTIVE, dither=Image.Dither.NONE)
        elif img.mode == 'LA':
            img = ImageOps.equalize(self.img.convert('L'))
        elif img.mode == 'RGBA':
            img = ImageOps.equalize(img.convert('RGB'))
        else:
            img = ImageOps.equalize(img)
        if alpha:
            img.putalpha(alpha)
        self.img = img
        self.undo_stack.push(self.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))

    ########################################
    #
    ########################################
    def action_filter_param(self, idx):
        from dialogs import dialog_filter
        dialog_filter.show(self, idx)

    ########################################
    #
    ########################################
    def action_image_infos(self):
        from dialogs import dialog_image_info
        dialog_image_info.show(self)

    ########################################
    #
    ########################################
    def action_histogram(self):
        from dialogs import dialog_histogram
        dialog_histogram.show(self)

    ########################################
    #
    ########################################
    def action_gradation_curve(self):
        from dialogs import dialog_gradation_curve
        dialog_gradation_curve.show(self)

    ########################################
    #
    ########################################
    def action_zoom_in(self):
        self.canvas.zoom_in()

    ########################################
    #
    ########################################
    def action_zoom_out(self):
        self.canvas.zoom_out()

    ########################################
    #
    ########################################
    def action_original_size(self):
        self.canvas.zoom_original_size()

    ########################################
    #
    ########################################
    def action_toggle_toolbar(self):
        self.toolbar_main.show(int(not self.toolbar_main.visible))
        rc = self.get_client_rect()
        rc.bottom -= self.statusbar.height
        if self.toolbar_main.visible:
            self.canvas.set_window_pos(
                0, self.toolbar_main.height,
                rc.right, rc.bottom - self.toolbar_main.height,
                flags=SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
            )
        else:
            self.canvas.set_window_pos(
                0, 0, rc.right, rc.bottom,
                flags=SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
            )
        user32.CheckMenuItem(self.hmenu, IDM_TOOLBAR, MF_BYCOMMAND |
                (MF_CHECKED if self.toolbar_main.visible else MF_UNCHECKED))

    ########################################
    #
    ########################################
    def action_toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        style = user32.GetWindowLongA(self.hwnd, GWL_STYLE)
        if self.is_fullscreen:
            self.statusbar.show(SW_HIDE)
            user32.SetMenu(self.hwnd, 0)
            style &= ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
        else:
            self.statusbar.show()
            style |= (WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
            user32.SetMenu(self.hwnd, self.hmenu)
        user32.SetWindowLongA(self.hwnd, GWL_STYLE, style)
        self.show(SW_SHOWMAXIMIZED if self.is_fullscreen else SW_NORMAL)

    ########################################
    #
    ########################################
    def action_toggle_dark(self):
        is_dark = not self.is_dark
        self.apply_theme(is_dark)
        user32.CheckMenuItem(self.hmenu, IDM_DARK, MF_BYCOMMAND |
                (MF_CHECKED if is_dark else MF_UNCHECKED))

    ########################################
    #
    ########################################
    def action_toggle_state(self, idm, prop):
        self.state[prop] = not self.state[prop]
        user32.CheckMenuItem(self.hmenu, idm, MF_BYCOMMAND |
                (MF_CHECKED if self.state[prop] else MF_UNCHECKED))

    ########################################
    # TODO: P
    ########################################
    def action_window_color(self):
        bgcolor = self.show_color_dialog(initial_color=self.state['bg_color'])
        if bgcolor is not None:
            self.canvas.set_bgcolor(bgcolor)
            self.state['bg_color'] = bgcolor
            image.BG_COLOR = CR_TO_RGB(self.state['bg_color'])
            if 'A' in self.img.getbands():
                self.canvas.update_hbitmap(image_to_hbitmap(self.img))

    ########################################
    #
    ########################################
    def action_manage_plugins(self):
        from dialogs import dialog_plugins
        dialog_plugins.show(self)

    ########################################
    #
    ########################################
    def action_about(self):
        self.show_message_box(
            (
                f'{APP_NAME} v{APP_VERSION}\n\nImage viewer and simple image editor '
                'for Windows based on\nPython, Pillow and the Windows API. '
                'Inspired by IrfanView.'
            ),
            'About'
        )

    ########################################
    #
    ########################################
    def action_page_setup(self):
        self.show_page_setup_dialog(byref(self.pt_print_paper_size), byref(self.rc_print_margins))

    ########################################
    #
    ########################################
    def action_print(self):
        ok, pdlg = self.show_print_dialog()
        if not ok:
            return False
        hdc = pdlg.hDC

        di = DOCINFOW()
        di.lpszDocName = os.path.basename(self.filename) if self.filename else 'Untitled'
        if gdi32.StartDocW(hdc, byref(di)) <= 0:
            gdi32.DeleteDC(hdc)
            return

        if not gdi32.StartPage(hdc):
            gdi32.AbortDoc(hdc)
            gdi32.DeleteDC(hdc)
            return

        # Get printer resolution
        pt_dpi = POINT(
            gdi32.GetDeviceCaps(hdc, LOGPIXELSX),
            gdi32.GetDeviceCaps(hdc, LOGPIXELSY)
        )

        INCHES_PER_UNIT = 1 / 2540
        rc = RECT(
            round(self.rc_print_margins.left * pt_dpi.x * INCHES_PER_UNIT),
            round(self.rc_print_margins.top * pt_dpi.x * INCHES_PER_UNIT),
            round(self.pt_print_paper_size.x * pt_dpi.x * INCHES_PER_UNIT) - round(self.rc_print_margins.right * pt_dpi.x * INCHES_PER_UNIT),
            round(self.pt_print_paper_size.y * pt_dpi.x * INCHES_PER_UNIT) - round(self.rc_print_margins.bottom * pt_dpi.x * INCHES_PER_UNIT)
        )

        if self.img.width / self.img.height > (rc.right - rc.left) / (rc.bottom - rc.top):
            x = rc.left
            w = rc.right - rc.left
            h = w * self.img.height // self.img.width
            y = ((rc.bottom - rc.top) - h) // 2
        else:
            y = rc.top
            h = rc.bottom - rc.top
            w = h * self.img.width // self.img.height
            x = ((rc.right - rc.left) - w) // 2

        h_bitmap = self.canvas.static.h_bitmap
        hdc_mem = gdi32.CreateCompatibleDC(hdc)
        gdi32.SelectObject(hdc_mem, h_bitmap)

        gdi32.SetStretchBltMode(hdc, HALFTONE)  # ???
        gdi32.StretchBlt(
            hdc, x, y, w, h,
            hdc_mem, 0, 0, self.img.width, self.img.height, SRCCOPY
        )
        gdi32.DeleteDC(hdc_mem)

        gdi32.EndPage(hdc)
        gdi32.EndDoc(hdc)

        gdi32.DeleteDC(hdc)

    ########################################
    #
    ########################################
    def animation_play(self):
        frame_cnt = getattr(self.img, 'n_frames', 1)

        if self.img.format == 'PNG':
            self.img.seek(frame_cnt - 1)
            self.img.seek(0)

        self.statusbar.set_text(f'- / {frame_cnt}', STATUSBAR_PART_FRAMES)

        class ctx():
            n = self.img.tell()
            dur = int(self.img.info['duration']) if 'duration' in self.img.info else 100

        def _play():
            try:
                self.img.seek(ctx.n % frame_cnt)
                self.canvas.update_hbitmap(image_to_hbitmap(self.img))
                ctx.n += 1

                # Uncomment for supporting intermediate duration changes
#                if 'duration' in self.img.info:
#                    dur = int(self.img.info['duration'])
#                    if dur != ctx.dur:
#                        user32.SetTimer(self.hwnd, ANIMATION_TIMER_ID, dur, 0)
#                        ctx.dur = dur

            except Exception as e:
                print(e)
                self.animation_stop()

        self.create_timer(_play, ctx.dur, timer_id=ANIMATION_TIMER_ID)
        self.is_playing = True

    ########################################
    #
    ########################################
    def animation_stop(self):
        self.kill_timer(ANIMATION_TIMER_ID)
        self.is_playing = False
        frame_cnt = getattr(self.img, 'n_frames', 1)
        self.statusbar.set_text(f'{self.img.tell() + 1} / {frame_cnt}', STATUSBAR_PART_FRAMES)

    ########################################
    #
    ########################################
    def animation_goto(self, frame):
        if self.is_playing:
            self.animation_stop()

        frame_cnt = getattr(self.img, 'n_frames', 1)
        if self.img.format == 'PNG':
            #frame = (self.img.tell() + n) % frame_cnt
            self.img.seek(frame_cnt - 1)
            self.img.seek(0)

        self.img.seek(frame)
        self.canvas.update_hbitmap(image_to_hbitmap(self.img))
        self.statusbar.set_text(f'{frame + 1} / {frame_cnt}', STATUSBAR_PART_FRAMES)

    ########################################
    #
    ########################################
    def action_toggle_play(self):
        if not self.can_play:
            return
        if self.is_playing:
            self.animation_stop()
        else:
            self.animation_play()

    ########################################
    #
    ########################################
    def action_skip_frames(self, n):
        if not self.has_frames:
            return
        frame_cnt = getattr(self.img, 'n_frames', 1)
        frame = (self.img.tell() + n) % frame_cnt
        self.animation_goto(frame)


if __name__ == '__main__':
    import sys
    import traceback
    sys.excepthook = traceback.print_exception
    app = App(sys.argv[1:])
    sys.exit(app.run())
