__all__ = ['Plugin']

import os

from math import *

from winapp.const import *
from winapp.controls.button import *
from winapp.controls.edit import *
from winapp.controls.static import *
from winapp.controls.toolbar import *
from winapp.controls.updown import *
from winapp.dialog import *
from winapp.dlls import gdi32, user32
from winapp.settings import Settings

from PIL import Image
from .myedit import *

#from mystatic import MyStatic

from image import *

from const import APP_NAME, HBRUSH_NULL, EVENT_IMAGE_CHANGED

HMOD_RESOURCES = kernel32.LoadLibraryW(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources.dll'))

IDI_CURSOR_FLOODFILL = 5000
IDI_CURSOR_PENCIL = 5001
IDI_CURSOR_PICKER = 5002
IDI_CURSOR_TEXT = 5003

HCURSOR_FLOODFILL = user32.LoadCursorW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDI_CURSOR_FLOODFILL))
HCURSOR_PENCIL = user32.LoadCursorW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDI_CURSOR_PENCIL))
HCURSOR_PICKER = user32.LoadCursorW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDI_CURSOR_PICKER))
HCURSOR_TEXT = user32.LoadCursorW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDI_CURSOR_TEXT))

IDM_PAINT = 1
IDM_EXIT_TEXT = 2

IDM_PAINT_SELECT = 1000
IDM_PAINT_TEXT = 1001
IDM_PAINT_RECT = 1002
IDM_PAINT_ELLIPSE = 1003
IDM_PAINT_PAINTBRUSH = 1004
IDM_PAINT_LINE = 1005
IDM_PAINT_FLOODFILL = 1007
IDM_PAINT_PICKER = 1008

IDB_TOOLBAR_PAINT = 5100
IDB_TOOLBAR_PAINT_DARK = 5101
IDB_SWITCH_COLORS = 5102

CONTEXT_MENU_TEXT = 1100
IDM_TEXT_FONT = 1101
IDM_TEXT_ALIGN_LEFT = 1102
IDM_TEXT_ALIGN_CENTER = 1103
IDM_TEXT_ALIGN_RIGHT = 1104

CONTEXT_MENU_SHAPE = 1200
IDM_SHAPE_DRAW = 1201
IDM_SHAPE_FILL = 1202

CONTEXT_MENU_PICKER = 1300
IDM_PICKER_PEN = 1301
IDM_PICKER_BRUSH = 1302

CONTEXT_MENU_ARROW = 1400
IDM_ARROW_START = 1401
IDM_ARROW_END = 1402

IDD_DLG_PALETTE_COLOR = 5700

BG_COLOR_TEXT = user32.GetSysColor(COLOR_3DFACE)
HPEN_NULL = gdi32.GetStockObject(NULL_PEN)

TOOLBAR_BUTTON_SIZE = 19
TOOLPAR_INDENT = 4
TOOLBAR_WIDTH = 2 * TOOLBAR_BUTTON_SIZE + 14 + 2 * TOOLPAR_INDENT

SEPARATOR_BRUSH = gdi32.CreateSolidBrush(0xA0A0A0)

#class BLENDFUNCTION(Structure):
#    _fields_ = [
#        ("BlendOp", BYTE),
#        ("BlendFlags", BYTE),
#        ("SourceConstantAlpha", BYTE),
#        ("AlphaFormat", BYTE),
#    ]
#
#msimg32 = windll.Msimg32
#msimg32.AlphaBlend.argtypes = (HDC, INT, INT, INT, INT, HDC, INT, INT, INT, INT, BLENDFUNCTION)


class Plugin():

    ########################################
    #
    ########################################
    def __init__(self, main, **kwargs):

        self.main = main
        self.is_initialized = False

        self.state = {
            'font_paint': {'font_name': 'Consolas', 'font_size': 14, 'font_weight': 400, 'font_italic': FALSE, 'font_underline': FALSE},
            'pen_color': 0x000000,
            'brush_color': 0xFFFFFF,
            'line_width': 5,
            'tolerance': 32,
        }

        self.settings = Settings(f'{APP_NAME}\\Paint', self.state)
        self.canvas = self.main.canvas
        self.hpen = gdi32.CreatePen(PS_SOLID, self.state['line_width'], self.state['pen_color'])
        self.hbrush = gdi32.CreateSolidBrush(self.state['brush_color'])
        self.current_tool = IDM_PAINT_SELECT
        self.resizing = 0
        self.shape_draw = False
        self.shape_fill = True
        self.picker_mode = IDM_PICKER_PEN

        self.arrow_start = False
        self.arrow_end = False

        hmenu = user32.GetSubMenu(main.hmenu, MENU_VIEW)
        user32.InsertMenuW(hmenu, 0, MF_BYPOSITION | MF_STRING, main.idm_last + IDM_PAINT, 'Paint Toolbar\tF2')
        user32.InsertMenuW(hmenu, 1, MF_BYPOSITION | MF_SEPARATOR, 0, '')

        # Add items to COMMAND_MESSAGE_MAP
        self.command_id_show = main.idm_last + IDM_PAINT
        self.command_id_exit_text = main.idm_last + IDM_EXIT_TEXT

        main.COMMAND_MESSAGE_MAP.update({
            main.idm_last + IDM_PAINT: self.action_toggle_paint,
            main.idm_last + IDM_EXIT_TEXT: self.action_exit_text,
          })
        main.idm_last += 2

        # Add accelerators
        num_accels = user32.CopyAcceleratorTableW(main.haccel, None, 0)
        acc_table = (ACCEL * (num_accels + 2))()
        user32.CopyAcceleratorTableW(main.haccel, acc_table, num_accels)

        acc_table[num_accels] = ACCEL(1, VK_F2, self.command_id_show)
        acc_table[num_accels + 1] = ACCEL(1, VK_ESCAPE, self.command_id_exit_text)

        user32.DestroyAcceleratorTable(main.haccel)

        main.haccel = user32.CreateAcceleratorTableW(acc_table, num_accels + 2)

        self.create_toolbar_paint()

        self.hmenu_text = user32.GetSubMenu(
            user32.LoadMenuW(HMOD_RESOURCES, MAKEINTRESOURCEW(CONTEXT_MENU_TEXT)),
            0
        )
        self.hmenu_shape = user32.GetSubMenu(
            user32.LoadMenuW(HMOD_RESOURCES, MAKEINTRESOURCEW(CONTEXT_MENU_SHAPE)),
            0
        )
        self.hmenu_picker = user32.GetSubMenu(
            user32.LoadMenuW(HMOD_RESOURCES, MAKEINTRESOURCEW(CONTEXT_MENU_PICKER)),
            0
        )
        self.hmenu_arrow = user32.GetSubMenu(
            user32.LoadMenuW(HMOD_RESOURCES, MAKEINTRESOURCEW(CONTEXT_MENU_ARROW)),
            0
        )

        if self.shape_draw:
            user32.CheckMenuItem(self.hmenu_shape, IDM_SHAPE_DRAW, MF_BYCOMMAND | MF_CHECKED)

        if self.shape_fill:
            user32.CheckMenuItem(self.hmenu_shape, IDM_SHAPE_FILL, MF_BYCOMMAND | MF_CHECKED)

        def _image_changed():
            if self.main.img is None:
                if self.toolbar_paint.visible:
                    return self.action_toggle_paint()
            else:
                if self.current_tool == IDM_PAINT_TEXT:
                    self.edit_paint.show(SW_HIDE)
                    self.edit_paint.set_window_text('')
                self.set_current_tool(IDM_PAINT_SELECT)
                if self.main.img.mode in ('P', 'L', 'LA'):
                    idx = get_closest_palette_color(self.state['pen_color'], main.img)
                    self.state['pen_color'] = RGB_TO_CR(*main.img.getpalette()[3 * idx:3 * idx + 3]) if main.img.mode == 'P' else RGB_TO_CR(idx, idx, idx)
                    idx = get_closest_palette_color(self.state['brush_color'], main.img)
                    self.state['brush_color'] = RGB_TO_CR(*main.img.getpalette()[3 * idx:3 * idx + 3]) if main.img.mode == 'P' else RGB_TO_CR(idx, idx, idx)
                    self.update_pen()
                    self.update_brush()
                    self.static_colors.redraw_window()

        main.connect(EVENT_IMAGE_CHANGED, _image_changed)

        ########################################
        #
        ########################################
        def _on_WM_SETCURSOR(hwnd, wparam, lparam):
            if self.current_tool == IDM_PAINT_TEXT:
                if self.edit_paint.visible:
                    return
                user32.SetCursor(HCURSOR_TEXT)
            elif self.current_tool == IDM_PAINT_PAINTBRUSH:
                user32.SetCursor(HCURSOR_PENCIL)
            elif self.current_tool == IDM_PAINT_PICKER:
                user32.SetCursor(HCURSOR_PICKER)
            elif self.current_tool == IDM_PAINT_FLOODFILL:
                user32.SetCursor(HCURSOR_FLOODFILL)
            else:
                user32.SetCursor(HCURSOR_CROSS)
            return TRUE

        self.canvas.static.register_message_callback(WM_SETCURSOR, _on_WM_SETCURSOR)

        ########################################
        # Edit control for adding text to image
        ########################################
        self.edit_paint = MyEdit(self.canvas)
        self.edit_paint.set_font(self.state['font_paint'])

        ########################################
        #
        ########################################
        def _on_WM_COMMAND(hwnd, wparam, lparam):
            if lparam == self.edit_paint.hwnd:
                notification_code = HIWORD(wparam)
                if notification_code == EN_CHANGE:
                    self.edit_paint.redraw_window()

        self.canvas.static.register_message_callback(WM_COMMAND, _on_WM_COMMAND)

        ########################################
        #
        ########################################
        def _on_WM_CTLCOLOREDIT(hwnd, wparam, lparam):
            gdi32.SetTextColor(wparam, self.state['pen_color'])
            gdi32.SetBkMode(wparam, TRANSPARENT)
            return HBRUSH_NULL
        self.canvas.static.register_message_callback(WM_CTLCOLOREDIT, _on_WM_CTLCOLOREDIT)

        ########################################
        #
        ########################################
        def _on_WM_LBUTTONDOWN(hwnd, wparam, lparam):
            x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF

            if self.current_tool == IDM_PAINT_SELECT:
                self.main.selection.start_drawing(x, y)

            elif self.current_tool == IDM_PAINT_TEXT:
                if self.edit_paint.visible:
                    self._draw_text()
                else:
                    self.edit_paint.start_drawing(x, y)

            elif self.current_tool == IDM_PAINT_RECT:
                self._draw_shape(x, y, self.current_tool)

            elif self.current_tool == IDM_PAINT_ELLIPSE:
                self._draw_shape(x, y, self.current_tool)

            elif self.current_tool == IDM_PAINT_LINE:
                self._draw_shape(x, y, self.current_tool)

            elif self.current_tool == IDM_PAINT_PAINTBRUSH:
                self._draw_paintbrush(x, y)

            elif self.current_tool == IDM_PAINT_FLOODFILL:
                self._draw_floodfill(x, y)

            elif self.current_tool == IDM_PAINT_PICKER:
                self._pick_color(x, y)

        self.canvas.static.unregister_message_callback(WM_LBUTTONDOWN)
        self.canvas.static.register_message_callback(WM_LBUTTONDOWN, _on_WM_LBUTTONDOWN)

        ########################################
        #
        ########################################
        def _on_WM_COMMAND(hwnd, wparam, lparam):
            if lparam == 0:
                command_id = LOWORD(wparam)

#                if command_id in self.COMMAND_MESSAGE_MAP:
#                    self.COMMAND_MESSAGE_MAP[command_id]()
#                    return

                # Toolbar menus
                if command_id == IDM_TEXT_FONT:
                    font = self.main.show_font_dialog(**self.state['font_paint'])
                    if font:
                        for i, k in enumerate(self.state['font_paint'].keys()):
                            self.state['font_paint'][k] = font[i]
                        self.edit_paint.set_font(self.state['font_paint'])

                elif command_id in (IDM_TEXT_ALIGN_LEFT, IDM_TEXT_ALIGN_CENTER, IDM_TEXT_ALIGN_RIGHT):
                    self.set_text_align(command_id)

                elif command_id == IDM_SHAPE_DRAW:
                    self.shape_draw = not self.shape_draw
                    user32.CheckMenuItem(self.hmenu_shape, IDM_SHAPE_DRAW, MF_BYCOMMAND | (MF_CHECKED if self.shape_draw else MF_UNCHECKED))
                    self.update_pen()

                elif command_id == IDM_SHAPE_FILL:
                    self.shape_fill = not self.shape_fill
                    user32.CheckMenuItem(self.hmenu_shape, IDM_SHAPE_FILL, MF_BYCOMMAND | (MF_CHECKED if self.shape_fill else MF_UNCHECKED))
                    self.update_brush()

                elif command_id in (IDM_PICKER_PEN, IDM_PICKER_BRUSH):
                    user32.CheckMenuItem(self.hmenu_picker, self.picker_mode, MF_BYCOMMAND | MF_UNCHECKED)
                    self.picker_mode = command_id
                    user32.CheckMenuItem(self.hmenu_picker, self.picker_mode, MF_BYCOMMAND | MF_CHECKED)

                elif command_id == IDM_ARROW_START:
                    self.arrow_start = not self.arrow_start
                    user32.CheckMenuItem(self.hmenu_arrow, IDM_ARROW_START, MF_BYCOMMAND | (MF_CHECKED if self.arrow_start else MF_UNCHECKED))

                elif command_id == IDM_ARROW_END:
                    self.arrow_end = not self.arrow_end
                    user32.CheckMenuItem(self.hmenu_arrow, IDM_ARROW_END, MF_BYCOMMAND | (MF_CHECKED if self.arrow_end else MF_UNCHECKED))

            # Toolbar buttons
            elif lparam == self.toolbar_paint.hwnd:
                command_id = LOWORD(wparam)

#                if command_id < IDM_PAINT_PEN_COLOR:

                if self.current_tool == IDM_PAINT_SELECT:
                    self.main.selection.show(SW_HIDE)

                elif self.current_tool == IDM_PAINT_TEXT:
                    self.edit_paint.show(SW_HIDE)

                elif self.current_tool in (IDM_PAINT_RECT, IDM_PAINT_ELLIPSE, IDM_PAINT_PAINTBRUSH, IDM_PAINT_LINE):
                    self.static_width.show(SW_HIDE)
                    self.edit_width.show(SW_HIDE)
                    self.updown_width.show(SW_HIDE)

                elif self.current_tool == IDM_PAINT_FLOODFILL:
                    self.static_tolerance.show(SW_HIDE)
                    self.edit_tolerance.show(SW_HIDE)
                    self.updown_tolerance.show(SW_HIDE)

                if command_id == IDM_PAINT_TEXT:
                    self.edit_paint.set_window_text('')

                elif command_id in (IDM_PAINT_RECT, IDM_PAINT_ELLIPSE, IDM_PAINT_PAINTBRUSH, IDM_PAINT_LINE):
                    self.static_width.show()
                    self.edit_width.show()
                    self.updown_width.show()

                elif command_id == IDM_PAINT_FLOODFILL:
                    self.static_tolerance.show()
                    self.edit_tolerance.show()
                    self.updown_tolerance.show()

                self.current_tool = command_id

        self.main.register_message_callback(WM_COMMAND, _on_WM_COMMAND)

        ########################################
        #
        ########################################
        def _on_WM_NOTIFY(hwnd, wparam, lparam):
            nmhdr = cast(lparam, LPNMHDR).contents
            if nmhdr.code == NM_RCLICK:
                nm = cast(lparam, POINTER(NMMOUSE)).contents
                dwItemSpec = c_long(nm.dwItemSpec).value
                if dwItemSpec in (IDM_PAINT_TEXT, IDM_PAINT_RECT, IDM_PAINT_ELLIPSE, IDM_PAINT_LINE, IDM_PAINT_PICKER):
                    rc = RECT()
                    self.toolbar_paint.send_message(TB_GETRECT, dwItemSpec, byref(rc))
                    user32.MapWindowPoints(self.toolbar_paint.hwnd, None, byref(rc), 2)

                    if dwItemSpec == IDM_PAINT_TEXT:
                        self.main.show_popup_menu(self.hmenu_text, rc.right, rc.top)

                    elif dwItemSpec == IDM_PAINT_RECT or dwItemSpec == IDM_PAINT_ELLIPSE:
                        self.main.show_popup_menu(self.hmenu_shape, rc.right, rc.top)

                    elif dwItemSpec == IDM_PAINT_PICKER:
                        self.main.show_popup_menu(self.hmenu_picker, rc.right, rc.top)

                    elif dwItemSpec == IDM_PAINT_LINE:
                        self.main.show_popup_menu(self.hmenu_arrow, rc.right, rc.top)

        self.main.register_message_callback(WM_NOTIFY, _on_WM_NOTIFY)

        self.update_pen()
        self.update_brush()

    ########################################
    #
    ########################################
    def __del__(self):
        self.settings.save(self.state)

    ########################################
    #
    ########################################
    def create_toolbar_paint(self):

        toolbar_buttons = (
            ('-'),

            ('Select', IDM_PAINT_SELECT, BTNS_CHECKGROUP, TBSTATE_ENABLED | TBSTATE_CHECKED),
            ('Text tool', IDM_PAINT_TEXT, BTNS_CHECKGROUP, TBSTATE_ENABLED | TBSTATE_WRAP, IDM_PAINT_TEXT),

            ('Rectangle', IDM_PAINT_RECT, BTNS_CHECKGROUP, TBSTATE_ENABLED, IDM_PAINT_RECT),
            ('Ellipse', IDM_PAINT_ELLIPSE, BTNS_CHECKGROUP, TBSTATE_ENABLED | TBSTATE_WRAP, IDM_PAINT_ELLIPSE),

            ('Paintbrush', IDM_PAINT_PAINTBRUSH, BTNS_CHECKGROUP),
            ('Line', IDM_PAINT_LINE, BTNS_CHECKGROUP, TBSTATE_ENABLED | TBSTATE_WRAP),

            ('Floodfill', IDM_PAINT_FLOODFILL, BTNS_CHECKGROUP, TBSTATE_ENABLED),
            ('Picker', IDM_PAINT_PICKER, BTNS_CHECKGROUP, TBSTATE_ENABLED | TBSTATE_WRAP, IDM_PAINT_PICKER),
        )

        self.toolbar_paint = ToolBar(
            self.main,
            style = WS_CHILD | WS_CLIPSIBLINGS | WS_BORDER | CCS_NODIVIDER | CCS_VERT | CCS_NORESIZE | TBSTYLE_TOOLTIPS,# | TBSTYLE_FLAT,  #
            icon_size = TOOLBAR_BUTTON_SIZE,
            toolbar_buttons = toolbar_buttons,
            h_bitmap = user32.LoadBitmapW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDB_TOOLBAR_PAINT)),
            h_bitmap_dark = user32.LoadBitmapW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDB_TOOLBAR_PAINT_DARK)),
            window_title = 'Paint',
            width = TOOLBAR_WIDTH,
            hide_text = True
        )

        self.toolbar_paint.send_message(TB_SETINDENT, TOOLPAR_INDENT, 0)

        x = TOOLPAR_INDENT
        y = 5 * TOOLBAR_BUTTON_SIZE + 32

        self.static_colors = Static(
            self.toolbar_paint,
            style=WS_CHILD | WS_VISIBLE | SS_BITMAP | SS_NOTIFY,
            left = x, top = y - 12,
            width = 47, height = 57,
        )

        self.hbitmap_colors = user32.LoadBitmapW(HMOD_RESOURCES, MAKEINTRESOURCEW(IDB_SWITCH_COLORS))

        ########################################
        #
        ########################################
        def _on_WM_PAINT(hwnd, wparam, lparam):
            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, byref(ps))

            user32.FrameRect(hdc, byref(RECT(0, 10, 35, 34)), gdi32.GetStockObject(WHITE_BRUSH if self.main.is_dark else BLACK_BRUSH))

            hbr = gdi32.CreateSolidBrush(self.state['brush_color'])
            user32.FillRect(hdc, byref(RECT(1, 11, 12, 33)), hbr)
            user32.FillRect(hdc, byref(RECT(12, 11, 34, 23)), hbr)
            gdi32.DeleteObject(hbr)

            user32.FrameRect(hdc, byref(RECT(12, 23, 47, 47)), gdi32.GetStockObject(WHITE_BRUSH if self.main.is_dark else BLACK_BRUSH))
            hbr = gdi32.CreateSolidBrush(self.state['pen_color'])
            user32.FillRect(hdc, byref(RECT(13, 24, 46, 46)), hbr)
            gdi32.DeleteObject(hbr)

            gdi32.SelectObject(hdc, self.hbitmap_colors)

            hdc_bitmap = gdi32.CreateCompatibleDC(hdc)
            gdi32.SelectObject(hdc_bitmap, self.hbitmap_colors)

            if self.main.is_dark:
                user32.FillRect(hdc, byref(RECT(35, 10, 47, 23)), DARK_BG_BRUSH)
                gdi32.BitBlt(
                    hdc,
                    35, 10, 12, 13,
                    # source
                    hdc_bitmap,
                    0, 0,
                    MERGEPAINT
                )
            else:
                gdi32.BitBlt(
                    hdc,
                    35, 10, 12, 13,
                    # source
                    hdc_bitmap,
                    0, 0,
                    SRCAND
                )
            gdi32.DeleteDC(hdc_bitmap)

            user32.FillRect(hdc, byref(RECT(0, 0, 47, 1)), SEPARATOR_BRUSH)
            user32.FillRect(hdc, byref(RECT(0, 56, 47, 57)), SEPARATOR_BRUSH)

            user32.EndPaint(hwnd, byref(ps))
            return FALSE

        self.static_colors.register_message_callback(WM_PAINT, _on_WM_PAINT)

        y += 50

        ########################################
        # Width (Shapes etc.)
        ########################################
        self.static_width = Static(
            self.toolbar_paint,
            style=WS_CHILD | SS_LEFT,
            bg_color=BG_COLOR_TEXT,
            left = x, top = y + 6,
            width = TOOLBAR_WIDTH - x - 2, height = 16,
            window_title='Width (px)',
        )
        self.static_width.set_font()

        self.edit_width = Edit(
            self.toolbar_paint,
            style = WS_CHILD | ES_NUMBER | ES_LEFT,
            ex_style = WS_EX_CLIENTEDGE,
            left = x, top = y + 22,
            width = TOOLBAR_WIDTH - 2 * x - 4, height = 18,
        )
        self.edit_width.set_font()

        self.updown_width = UpDown(
            self.toolbar_paint,
            style=WS_CHILD | UDS_AUTOBUDDY | UDS_SETBUDDYINT | UDS_ALIGNRIGHT | UDS_ARROWKEYS | UDS_HOTTRACK,
        )

        self.updown_width.set_range(1, 999)
        self.updown_width.set_pos(self.state['line_width'])

        ########################################
        # Tolerance
        ########################################
        self.static_tolerance = Static(
            self.toolbar_paint,
            style = WS_CHILD | SS_LEFT,
            bg_color = BG_COLOR_TEXT,
            left = x, top = y + 6,
            width = TOOLBAR_WIDTH - x - 2, height = 16,
            window_title = 'Tolerance',
        )
        self.static_tolerance.set_font()

        self.edit_tolerance = Edit(
            self.toolbar_paint,
            style = WS_CHILD | ES_NUMBER | ES_LEFT,
            ex_style = WS_EX_CLIENTEDGE,
            left = x, top = y + 22,
            width = TOOLBAR_WIDTH - 2 * x - 4, height = 18,
        )
        self.edit_tolerance.set_font()

        self.updown_tolerance = UpDown(
            self.toolbar_paint,
            style = WS_CHILD | UDS_AUTOBUDDY | UDS_SETBUDDYINT | UDS_ALIGNRIGHT | UDS_ARROWKEYS | UDS_HOTTRACK,
        )

        self.updown_tolerance.set_range(0, 255)
        self.updown_tolerance.set_pos(self.state['tolerance'])

        ########################################
        #
        ########################################
        def _on_WM_COMMAND(hwnd, wparam, lparam):
            notification_code = HIWORD(wparam)

            if lparam == self.static_colors.hwnd:
                if notification_code == STN_CLICKED:
                    pt = POINT()
                    user32.GetCursorPos(byref(pt))
                    user32.MapWindowPoints(None, self.static_colors.hwnd, byref(pt), 1)
                    if pt.y < 10 or pt.y > 46:
                        return

                    if pt.x >= 12 and pt.y >= 23:
                        color = self.show_color_dialog(self.state['pen_color'])
                        if color is not None:
                            self.state['pen_color'] = color
                            self.static_colors.redraw_window()
                            self.update_pen()

                    elif pt.x < 35 and pt.y < 34:
                        color = self.show_color_dialog(self.state['brush_color'])
                        if color is not None:
                            self.state['brush_color'] = color
                            self.static_colors.redraw_window()
                            self.update_brush()

                    elif pt.x >= 35:
                        self.state['pen_color'], self.state['brush_color'] = self.state['brush_color'], self.state['pen_color']
                        self.static_colors.redraw_window()
                        self.update_pen()
                        self.update_brush()

            elif lparam == self.edit_tolerance.hwnd:
                if notification_code == EN_CHANGE:
                   buf = create_unicode_buffer(4)
                   self.edit_tolerance.send_message(WM_GETTEXT, 4, buf)
                   self.state['tolerance'] = int(buf.value)

            elif lparam == self.edit_width.hwnd:
                if notification_code == EN_CHANGE:
                    self.update_pen()

        self.toolbar_paint.register_message_callback(WM_COMMAND, _on_WM_COMMAND)

        self.toolbar_paint.hide_focus_rects()

    ########################################
    #
    ########################################
    def action_toggle_paint(self):
        if not self.toolbar_paint.visible and self.main.img is None:
            return

        rc = self.main.get_client_rect()

        height = rc.bottom
        y = 0
        if self.main.toolbar_main.visible:
            height -= self.main.toolbar_main.height
            y += self.main.toolbar_main.height
        if self.main.statusbar.visible:
            height -= self.main.statusbar.height

        visible = not self.toolbar_paint.visible
        if visible:
            self.toolbar_paint.set_window_pos(x=0, y=y, width=TOOLBAR_WIDTH, height=height, flags=SWP_NOZORDER | SWP_NOACTIVATE)
            self.toolbar_paint.show()

            if not self.is_initialized:
                self.is_initialized = True

                ########################################
                #
                ########################################
                def _on_WM_SIZE(hwnd, wparam, lparam):
                    width, height = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF

                    self.main.toolbar_main.update_size()
                    self.main.statusbar.update_size(width)
                    self.update_layout(width, height)

                self.main.unregister_message_callback(WM_SIZE)
                self.main.register_message_callback(WM_SIZE, _on_WM_SIZE)

                ########################################
                #
                ########################################
                def _toogle_toolbar_main():
                    self.main.toolbar_main.show(int(not self.main.toolbar_main.visible))

                    rc = self.main.get_client_rect()

                    width, height = rc.right, rc.bottom
                    x, y = 0, 0

                    if self.main.statusbar.visible:
                        height -= self.main.statusbar.height
                    if self.main.toolbar_main.visible:
                        height -= self.main.toolbar_main.height
                        y += self.main.toolbar_main.height
                    if self.toolbar_paint.visible:
                        width -= TOOLBAR_WIDTH
                        x +=TOOLBAR_WIDTH

                    self.toolbar_paint.set_window_pos(x=0, y=y, width=TOOLBAR_WIDTH, height=height, flags=SWP_NOZORDER | SWP_NOACTIVATE)

                    self.main.canvas.set_window_pos(
                        x, y,
                        width, height,
                        flags=SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
                    )

                    user32.CheckMenuItem(self.main.hmenu, IDM_TOOLBAR, MF_BYCOMMAND |
                            (MF_CHECKED if self.main.toolbar_main.visible else MF_UNCHECKED))

                self.main.COMMAND_MESSAGE_MAP[IDM_TOOLBAR] = _toogle_toolbar_main

            if user32.IsZoomed(self.main.hwnd):
                self.canvas.set_window_pos(x=TOOLBAR_WIDTH, y=y, width=rc.right - TOOLBAR_WIDTH, height=height, flags=SWP_NOZORDER | SWP_NOACTIVATE)
            else:
                self.canvas.set_window_pos(x=TOOLBAR_WIDTH, y=y, flags=SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
                rc_main = self.main.get_window_rect()
                self.main.set_window_pos(width=rc_main.right - rc_main.left + TOOLBAR_WIDTH, height=rc_main.bottom - rc_main.top, flags=SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)

        else:
            self.toolbar_paint.show(SW_HIDE)
            if user32.IsZoomed(self.main.hwnd):
                self.canvas.set_window_pos(x=0, y=y, width=rc.right, height=height, flags=SWP_NOZORDER | SWP_NOACTIVATE)
            else:
                self.canvas.set_window_pos(x=0, y=y, flags=SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
                rc_main = self.main.get_window_rect()
                self.main.set_window_pos(width=rc_main.right - rc_main.left - TOOLBAR_WIDTH, height=rc_main.bottom - rc_main.top, flags=SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)

            self.edit_paint.show(SW_HIDE)
            self.set_current_tool(IDM_PAINT_SELECT)

        user32.CheckMenuItem(user32.GetSubMenu(self.main.hmenu, 4), self.command_id_show, MF_BYCOMMAND | (MF_CHECKED if self.toolbar_paint.visible else MF_UNCHECKED))

    ########################################
    #
    ########################################
    def action_exit_text(self):
        if self.current_tool == IDM_PAINT_TEXT:
            self.edit_paint.show(SW_HIDE)
            self.edit_paint.set_window_text('')

    ########################################
    #
    ########################################
    def update_layout(self, width, height):
        if self.main.toolbar_main.visible:
            height -= self.main.toolbar_main.height
        if self.main.statusbar.visible:
            height -= self.main.statusbar.height
        self.toolbar_paint.set_window_pos(width=TOOLBAR_WIDTH, height=height, flags=SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)
        if self.toolbar_paint.visible:
            width -= TOOLBAR_WIDTH
        self.canvas.set_window_pos(width=width, height=height, flags=SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)

    ########################################
    #
    ########################################
    def set_current_tool(self, idm):
        self.current_tool = idm
        self.toolbar_paint.send_message(TB_CHECKBUTTON, idm, TRUE)

    ########################################
    #
    ########################################
    def update_pen(self):
        gdi32.DeleteObject(self.hpen)

        buf = create_unicode_buffer(4)
        self.edit_width.send_message(WM_GETTEXT, 4, buf)
        self.state['line_width'] = int(buf.value)

        self.hpen = gdi32.CreatePen(PS_SOLID, self.state['line_width'], self.state['pen_color']) #if self.shape_draw else HPEN_NULL

        if self.edit_paint.visible:
            self.edit_paint.redraw_window()

    ########################################
    #
    ########################################
    def update_brush(self):
        gdi32.DeleteObject(self.hbrush)
        self.hbrush = gdi32.CreateSolidBrush(self.state['brush_color']) #if self.shape_fill else HBRUSH_NULL

    ########################################
    #
    ########################################
    def set_pen_color(self, color):
        self.state['pen_color'] = color
        self.update_pen()
        self.edit_paint.redraw_window()

    ########################################
    #
    ########################################
    def set_brush_color(self, color):
        self.state['brush_color'] = color
        self.update_brush()

    ########################################
    #
    ########################################
    def set_text_align(self, command_id):
        for i in (IDM_TEXT_ALIGN_LEFT, IDM_TEXT_ALIGN_CENTER, IDM_TEXT_ALIGN_RIGHT):
            user32.CheckMenuItem(self.hmenu_text, i, MF_BYCOMMAND | (MF_CHECKED if i == command_id else MF_UNCHECKED))
        style = user32.GetWindowLongA(self.edit_paint.hwnd, GWL_STYLE) & ~3  # remove alignment
        if command_id == IDM_TEXT_ALIGN_LEFT:
            style |= ES_LEFT
        elif command_id == IDM_TEXT_ALIGN_CENTER:
            style |= ES_CENTER
        else:  #if command_id == IDM_TEXT_ALIGN_RIGHT:
            style |= ES_RIGHT
        user32.SetWindowLongA(self.edit_paint.hwnd, GWL_STYLE, style)
        self.edit_paint.redraw_window()

    ########################################
    #
    ########################################
    def show_color_dialog(self, initial_color=0):
        if self.main.img.mode in ('P', 'L', 'LA'):
            #return dialog_color_select.show(self.main, initial_color)
            return self.show_palette_color_dialog(self.main, initial_color)
        else:
            return self.main.show_color_dialog(initial_color)

    ########################################
    #
    ########################################
    def show_palette_color_dialog(self, main, colorref):
        if main.img is None:
            return

        ctx = {
            'idx_selected_old': -1,
            'trans': -1,
        }

        if main.img.mode in ('L', 'LA'):
            ctx['palette'] = [RGB_TO_CR(i, i, i) for i in range(256)]
        else:
            pal = main.img.getpalette()
            if 'transparency' in main.img.info:
                trans = main.img.info['transparency']
                pal[trans * 3:trans * 3 + 3] = main.img.info['transcolor']
                ctx['trans'] = trans
            ctx['palette'] = [RGB_TO_CR(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)]

        try:
            ctx['idx_selected'] = ctx['palette'].index(colorref)
        except Exception as e:
#            print(e)
            ctx['idx_selected'] = -1

        ########################################
        #
        ########################################
        def _static_proc_callback(hwnd, msg, wparam, lparam, uIdSubclass, dwRefData):
            if msg == WM_PAINT:
                ps = PAINTSTRUCT()
                hdc = user32.BeginPaint(hwnd, byref(ps))

                if ctx['idx_selected_old'] > -1:
                    x = 5 + ctx['idx_selected_old'] % 16 * 20
                    y = 5 + ctx['idx_selected_old'] // 16 * 20
                    rc = RECT(x - 2, y - 2, x + 18, y + 18)
#                if idx == ctx['idx_selected_old']:
#                    rc = RECT(x - 2, y - 2, x + 18, y + 18)
                    user32.FrameRect(hdc, byref(rc), DARK_BG_BRUSH if main.is_dark else COLOR_3DFACE + 1)
                    user32.InflateRect(byref(rc), 1, 1)
                    user32.FrameRect(hdc, byref(rc), DARK_BG_BRUSH if main.is_dark else COLOR_3DFACE + 1)
                    ctx['idx_selected_old'] = -1

                x, y = 5, 5
                for idx in range(len(ctx['palette'])):

                    if idx == ctx['idx_selected']:
                        rc = RECT(x - 2, y - 2, x + 18, y + 18)
                        hbr = gdi32.CreateSolidBrush(0x0000FF)
                        user32.FrameRect(hdc, byref(rc), hbr)
                        user32.InflateRect(byref(rc), 1, 1)
                        user32.FrameRect(hdc, byref(rc), hbr)
                        gdi32.DeleteObject(hbr)

                    rc = RECT(x, y, x + 16, y + 16)
                    hbr = gdi32.CreateSolidBrush(ctx['palette'][idx])
                    user32.FillRect(hdc, byref(rc), hbr)
                    gdi32.DeleteObject(hbr)

                    if idx == ctx['trans']:
                        user32.FrameRect(hdc, byref(rc), gdi32.GetStockObject(WHITE_BRUSH if main.is_dark else BLACK_BRUSH))
                        user32.InflateRect(byref(rc), -1, -1)
                        user32.FrameRect(hdc, byref(rc), gdi32.GetStockObject(BLACK_BRUSH if main.is_dark else WHITE_BRUSH))
                        user32.InflateRect(byref(rc), -1, -1)
                        user32.FrameRect(hdc, byref(rc), gdi32.GetStockObject(WHITE_BRUSH if main.is_dark else BLACK_BRUSH))
                        user32.InflateRect(byref(rc), -1, -1)
                        user32.FrameRect(hdc, byref(rc), gdi32.GetStockObject(BLACK_BRUSH if main.is_dark else WHITE_BRUSH))
#                        user32.InflateRect(byref(rc), -4, -4)
#                        user32.FillRect(hdc, byref(rc), DARK_BG_BRUSH if main.is_dark else COLOR_3DFACE + 1)

                    if idx % 16 == 15:
                        x = 5
                        y += 20
                    else:
                        x += 20

                user32.EndPaint(hwnd, byref(ps))
                return FALSE

            return comctl32.DefSubclassProc(hwnd, msg, wparam, lparam)

        static_proc_callback = SUBCLASSPROC(_static_proc_callback)

        ########################################
        #
        ########################################
        def _dialog_proc_callback(hwnd, msg, wparam, lparam):
            if msg == WM_INITDIALOG:
                if main.is_dark:
                    DarkDialogInit(hwnd)
                user32.SendMessageW(hwnd, WM_SETICON, 0, main.hicon)

                ctx['hwnd_dialog'] = hwnd
                ctx['hwnd_static'] = user32.GetDlgItem(hwnd, 1781)
                ctx['hwnd_index'] = user32.GetDlgItem(hwnd, 1779)
                ctx['hwnd_value'] = user32.GetDlgItem(hwnd, 1780)
                comctl32.SetWindowSubclass(ctx['hwnd_static'], static_proc_callback, 1, 0)

                if ctx['idx_selected'] > -1:
                    user32.SetWindowTextW(ctx['hwnd_index'], f"Index: {ctx['idx_selected']}")
                    r, g, b = CR_TO_RGB(ctx['palette'][ctx['idx_selected']])
                    user32.SetWindowTextW(ctx['hwnd_value'], f'Value: RGB({r}, {g}, {b})')

            elif msg == WM_CLOSE:
                main.canvas.update_hbitmap(image_to_hbitmap(main.img))
                user32.EndDialog(hwnd, 0)

            elif msg == WM_LBUTTONDOWN:
                x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
                pt = POINT(x, y)
                user32.MapWindowPoints(hwnd, ctx['hwnd_static'], byref(pt), 1)
                idx_selected = (pt.y - 5) // 20 * 16 + (pt.x - 5) // 20
                if idx_selected >= 0 and idx_selected <= len(ctx['palette']) and idx_selected != ctx['idx_selected']:
                    ctx['idx_selected_old'] = ctx['idx_selected']
                    ctx['idx_selected'] = idx_selected
                    user32.RedrawWindow(ctx['hwnd_static'], 0, 0, RDW_ERASE | RDW_INVALIDATE | RDW_FRAME | RDW_ALLCHILDREN)
                    user32.SetWindowTextW(ctx['hwnd_index'], f'Index: {idx_selected}')
                    r, g, b = CR_TO_RGB(ctx['palette'][idx_selected])
                    user32.SetWindowTextW(ctx['hwnd_value'], f'Value: RGB({r}, {g}, {b})')

            elif msg == WM_COMMAND:
                notification_code = HIWORD(wparam)
                if notification_code == BN_CLICKED:
                    control_id = LOWORD(wparam)

                    if control_id == IDCANCEL:
                        user32.EndDialog(hwnd, 0)

                    elif control_id == IDOK:
                        user32.EndDialog(hwnd, 1)

            elif self.main.is_dark:
                return DarkDialogHandleMessages(msg, wparam)
            return FALSE

        if user32.DialogBoxParamW(
            HMOD_RESOURCES,
            MAKEINTRESOURCEW(IDD_DLG_PALETTE_COLOR),
            main.hwnd,
            DLGPROC(_dialog_proc_callback),
            NULL
        ) and ctx['idx_selected'] > -1:
            return ctx['palette'][ctx['idx_selected']]

    ########################################
    #
    ########################################
    def _draw_text(self):

        if self.edit_paint.send_message(WM_GETTEXTLENGTH, 0, 0) == 0:
            return self.edit_paint.show(SW_HIDE)

        hdc_edit = user32.GetDC(self.edit_paint.hwnd)

        rc_edit = self.edit_paint.get_client_rect()

        hdc_bitmap1 = gdi32.CreateCompatibleDC(hdc_edit)
        h_bitmap = gdi32.CreateCompatibleBitmap(hdc_edit, rc_edit.right, rc_edit.bottom)
        gdi32.SelectObject(hdc_bitmap1, h_bitmap)

        user32.HideCaret(self.edit_paint.hwnd)

        # Blit the edit's (scaled) content incl. background into the bitmap DC
        gdi32.BitBlt(
            # Dest
            hdc_bitmap1,
            0, 0, rc_edit.right, rc_edit.bottom,
            # Src
            hdc_edit,
            0, 0,
            SRCCOPY
        )

        user32.ShowCaret(self.edit_paint.hwnd)

        hdc_bitmap2 = gdi32.CreateCompatibleDC(hdc_edit)
        gdi32.SelectObject(hdc_bitmap2, self.canvas.static.h_bitmap)

        # Get rect of edit relative to static (image)
        rc_dest = self.edit_paint.get_window_rect()
        user32.MapWindowPoints(None, self.canvas.static.hwnd, byref(rc_dest), 2)

        # Remove WS_THICKFRAME
        style = user32.GetWindowLongA(self.edit_paint.hwnd, GWL_STYLE)
        user32.SetWindowLongA(self.edit_paint.hwnd, GWL_STYLE, style & ~WS_THICKFRAME)

        cx = (rc_dest.right - rc_dest.left - (rc_edit.right - rc_edit.left)) // 2
        cy = (rc_dest.bottom - rc_dest.top - (rc_edit.bottom - rc_edit.top)) // 2
#        cx, cy = 3, 3

        gdi32.SetStretchBltMode(hdc_bitmap2, HALFTONE)  # ???
        gdi32.StretchBlt(
            # Dest
            hdc_bitmap2,
            int((rc_dest.left + cx) / self.canvas.zoom),
            int((rc_dest.top + cy) / self.canvas.zoom),
            int(rc_edit.right / self.canvas.zoom),
            int(rc_edit.bottom / self.canvas.zoom),
            # Src
            hdc_bitmap1,
            0, 0, rc_edit.right, rc_edit.bottom,
            SRCCOPY
        )

        user32.ReleaseDC(self.edit_paint.hwnd, hdc_edit)

        gdi32.DeleteDC(hdc_bitmap2)
        gdi32.DeleteDC(hdc_bitmap1)
        gdi32.DeleteObject(h_bitmap)

        img = hbitmap_to_image(self.canvas.static.h_bitmap)
        img.info = self.main.img.info
        self.main.img = img
        self.main.undo_stack.push(self.main.img)

        self.edit_paint.show(SW_HIDE)
        self.edit_paint.set_window_text('')

        user32.SetWindowLongA(self.edit_paint.hwnd, GWL_STYLE, style & ~WS_VISIBLE)  # ???

    ########################################
    # Almost WYSIWYG: while mouse is down we draw/paint into a lores copy of the bitmap,
    # on mouse up we draw/paint into the actual (possibly hires) bitmap
    ########################################
    def _draw_shape(self, x, y, shape_type):

        pt_click = POINT(x, y)  # relative to static (scrolled and zoomed)

        pt_click_abs = POINT(pt_click.x, pt_click.y)
        user32.MapWindowPoints(self.canvas.static.hwnd, None, byref(pt_click_abs), 1)

        ########################################
        # Calculate the visible rect of the static
        # rc_visible is absolute, i.e. in screen coords
        ########################################
        rc_static = self.canvas.static.get_window_rect()
        rc_canvas = self.canvas.get_window_rect()
        # remove scrollbars
        rc_canvas_client = self.canvas.get_client_rect()
        rc_canvas.right = rc_canvas.left + rc_canvas_client.right
        rc_canvas.bottom = rc_canvas.top + rc_canvas_client.bottom
        rc_visible = RECT()
        user32.IntersectRect(byref(rc_visible), byref(rc_static), byref(rc_canvas))
        x, y = rc_visible.left, rc_visible.top
        cx, cy = rc_visible.right - rc_visible.left, rc_visible.bottom - rc_visible.top

        ########################################
        # Capture the visible image into hbitmap_visible
        ########################################
        hdc_screen = user32.GetDC(NULL)
        hdc_bitmap = gdi32.CreateCompatibleDC(hdc_screen)
        hbitmap_visible = gdi32.CreateCompatibleBitmap(hdc_screen,  cx, cy)
        gdi32.SelectObject(hdc_bitmap, hbitmap_visible)
        gdi32.BitBlt(
            # dest
            hdc_bitmap,
            0, 0, cx, cy,
            # source
            hdc_screen,
            x, y,
            SRCCOPY
        )
        gdi32.DeleteDC(hdc_bitmap)
        user32.ReleaseDC(NULL, hdc_screen)

        ########################################
        # Replace static's hbitmap with hbitmap_visible
        ########################################
        hbitmap_org = self.canvas.static.h_bitmap
        self.canvas.static.h_bitmap = hbitmap_visible

        img_width_org, img_height_org = self.canvas.static.img_width, self.canvas.static.img_height
        self.canvas.static.img_width = cx
        self.canvas.static.img_height = cy

        user32.MapWindowPoints(None, self.canvas.hwnd, byref(rc_static), 2)
        self.canvas.static.set_window_pos(max(0, rc_static.left), max(0, rc_static.top), cx, cy)

        user32.MapWindowPoints(None, self.canvas.static.hwnd, byref(pt_click_abs), 1)

        hbitmap_tmp = user32.CopyImage(hbitmap_visible, IMAGE_BITMAP, 0, 0, LR_CREATEDIBSECTION)

        user32.SetCapture(self.canvas.static.hwnd)

        hdc_static = user32.GetDC(self.canvas.static.hwnd)
        hdc_bitmap = gdi32.CreateCompatibleDC(hdc_static)

        if shape_type == IDM_PAINT_LINE or self.shape_draw:
            scaled_pen_size = self.state['line_width'] * self.canvas.zoom
            hpen_scaled = gdi32.CreatePen(PS_SOLID, round(scaled_pen_size), self.state['pen_color'])
        else:
            hpen_scaled = HPEN_NULL
        gdi32.SelectObject(hdc_bitmap, hpen_scaled)

        gdi32.SelectObject(hdc_bitmap, self.hbrush if self.shape_fill else HBRUSH_NULL)

        hdc_bitmap_tmp = gdi32.CreateCompatibleDC(hdc_static)
        gdi32.SelectObject(hdc_bitmap_tmp, hbitmap_tmp)

        pt_dest = POINT()

        ########################################
        #
        ########################################
        def _on_WM_MOUSEMOVE(hwnd, wparam, lparam):
            pt_dest.x, pt_dest.y = GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam)

            state = gdi32.SaveDC(hdc_bitmap)

            gdi32.SelectObject(hdc_bitmap, hbitmap_visible)

            # Blit tmp in copy
            gdi32.BitBlt(
                hdc_bitmap,
                0, 0, cx, cy,
                # source
                hdc_bitmap_tmp,
                0, 0,
                SRCCOPY
            )

            is_shift = user32.GetAsyncKeyState(VK_SHIFT) > 1

            if shape_type == IDM_PAINT_LINE:
                if is_shift:
                    slopy = (round((atan2((pt_click_abs.y - pt_dest.y), (pt_click_abs.x - pt_dest.x)) * 4 / pi)) + 4) % 8
                    if slopy in (0, 4):
                        pt_dest.y = pt_click_abs.y
                    elif slopy in (2, 6):
                        pt_dest.x = pt_click_abs.x
                    else:
                        pt_dest.y = int(pt_click_abs.y + copysign(pt_click_abs.x - pt_dest.x, pt_dest.y - pt_click_abs.y))
                    slopy = (slopy - 4) * pi / 4
                else:
                    slopy = atan2( ( pt_click_abs.y - pt_dest.y ), ( pt_click_abs.x - pt_dest.x ))

            else:
                if is_shift:
                    if abs(pt_dest.x - pt_click_abs.x) < abs(pt_dest.y - pt_click_abs.y):
                        pt_dest.y = int(pt_click_abs.y + copysign(pt_click_abs.x - pt_dest.x, pt_dest.y - pt_click_abs.y))
                    else:
                        pt_dest.x = int(pt_click_abs.x + copysign(pt_click_abs.y - pt_dest.y, pt_dest.x - pt_click_abs.x))

            is_ctrl = user32.GetAsyncKeyState(VK_CONTROL) > 1

            if shape_type == IDM_PAINT_RECT:
                if is_ctrl:
                    gdi32.Rectangle(hdc_bitmap, 2 * pt_click_abs.x - pt_dest.x, 2 * pt_click_abs.y - pt_dest.y, pt_dest.x, pt_dest.y)
                else:
                    gdi32.Rectangle(hdc_bitmap, pt_click_abs.x, pt_click_abs.y, pt_dest.x, pt_dest.y)

            elif shape_type == IDM_PAINT_ELLIPSE:
                if is_ctrl:
                    gdi32.Ellipse(hdc_bitmap, 2 * pt_click_abs.x - pt_dest.x, 2 * pt_click_abs.y - pt_dest.y, pt_dest.x, pt_dest.y)
                else:
                    gdi32.Ellipse(hdc_bitmap, pt_click_abs.x, pt_click_abs.y, pt_dest.x, pt_dest.y)

            elif shape_type == IDM_PAINT_LINE:

                x, y = (2 * pt_click_abs.x - pt_dest.x, 2 * pt_click_abs.y - pt_dest.y) if is_ctrl else (pt_click_abs.x, pt_click_abs.y)

                if self.arrow_start or self.arrow_end:
                    cosy = cos(slopy)
                    siny = sin(slopy)
                    arrow_base = max(round(scaled_pen_size * 3), 7)  # half side length
                    arrow_height = sqrt(3) * arrow_base  # height of triangle

                    if self.arrow_start:
                        self._draw_arrow_head(hdc_bitmap, x, y, -cosy, -siny, arrow_base, arrow_height)
                        gdi32.MoveToEx(hdc_bitmap, x - round(arrow_height * cosy), y - round(arrow_height * siny), None)
                    else:
                        gdi32.MoveToEx(hdc_bitmap, x, y, None)

                    if self.arrow_end:
                        gdi32.LineTo(hdc_bitmap, pt_dest.x + round(arrow_height * cosy), pt_dest.y + round(arrow_height * siny))
                        self._draw_arrow_head( hdc_bitmap, pt_dest.x, pt_dest.y, cosy, siny, arrow_base, arrow_height)
                    else:
                        gdi32.LineTo(hdc_bitmap, pt_dest.x, pt_dest.y)
                else:
                    gdi32.MoveToEx(hdc_bitmap, x, y, None)
                    gdi32.LineTo(hdc_bitmap, pt_dest.x, pt_dest.y)

            gdi32.RestoreDC(hdc_bitmap, state)

            user32.InvalidateRect(self.canvas.static.hwnd, None, TRUE)

        self.canvas.static.register_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)

        ########################################
        #
        ########################################
        def _on_WM_LBUTTONUP(hwnd, wparam, lparam):

            user32.ReleaseCapture(self.canvas.static.hwnd)
            self.canvas.static.unregister_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)
            self.canvas.static.unregister_message_callback(WM_LBUTTONUP, _on_WM_LBUTTONUP)

            # Clean up
            if hpen_scaled != HPEN_NULL:
                gdi32.DeleteObject(hpen_scaled)
            gdi32.DeleteDC(hdc_bitmap_tmp)
            gdi32.DeleteDC(hdc_bitmap)
            user32.ReleaseDC(self.canvas.static.hwnd, hdc_static)
            gdi32.DeleteObject(hbitmap_visible)
            gdi32.DeleteObject(hbitmap_tmp)

            pt_dest_abs = POINT(pt_dest.x, pt_dest.y)
            user32.MapWindowPoints(self.canvas.static.hwnd, None, byref(pt_dest_abs), 1)

            # Restore original bitmap and static position
            self.canvas.static.h_bitmap = hbitmap_org
            self.canvas.static.img_width = img_width_org
            self.canvas.static.img_height = img_height_org
            self.canvas.static.set_window_pos(rc_static.left, rc_static.top, rc_static.right - rc_static.left, rc_static.bottom - rc_static.top)

            # Now draw rect into original bitmap
            pt_click.x, pt_click.y = round(pt_click.x / self.canvas.zoom), round(pt_click.y / self.canvas.zoom)

            user32.MapWindowPoints(None, self.canvas.static.hwnd, byref(pt_dest_abs), 1)
            pt_dest_abs.x, pt_dest_abs.y = round(pt_dest_abs.x / self.canvas.zoom), round(pt_dest_abs.y / self.canvas.zoom)

            hdc_static2 = user32.GetDC(self.canvas.static.hwnd)
            hdc_bitmap2 = gdi32.CreateCompatibleDC(hdc_static2)
            gdi32.SelectObject(hdc_bitmap2, hbitmap_org)
            gdi32.SelectObject(hdc_bitmap2, self.hpen if shape_type == IDM_PAINT_LINE or self.shape_draw else HPEN_NULL)
            gdi32.SelectObject(hdc_bitmap2, self.hbrush if self.shape_fill else HBRUSH_NULL)

            is_ctrl = user32.GetAsyncKeyState(VK_CONTROL) > 1
            if shape_type == IDM_PAINT_RECT:
                if is_ctrl:
                    gdi32.Rectangle(hdc_bitmap2, 2 * pt_click.x - pt_dest_abs.x, 2 * pt_click.y - pt_dest_abs.y, pt_dest_abs.x, pt_dest_abs.y)
                else:
                    gdi32.Rectangle(hdc_bitmap2, pt_click.x, pt_click.y, pt_dest_abs.x, pt_dest_abs.y)

            elif shape_type == IDM_PAINT_ELLIPSE:
                if is_ctrl:
                    gdi32.Ellipse(hdc_bitmap2, 2 * pt_click.x - pt_dest_abs.x, 2 * pt_click.y - pt_dest_abs.y, pt_dest_abs.x, pt_dest_abs.y)
                else:
                    gdi32.Ellipse(hdc_bitmap2, pt_click.x, pt_click.y, pt_dest_abs.x, pt_dest_abs.y)

            elif shape_type == IDM_PAINT_LINE:
                x, y = (2 * pt_click.x - pt_dest_abs.x, 2 * pt_click.y - pt_dest_abs.y) if is_ctrl else (pt_click.x, pt_click.y)
                if self.arrow_start or self.arrow_end:
                    slopy = atan2( ( pt_click.y - pt_dest_abs.y ), ( pt_click.x - pt_dest_abs.x ))
                    cosy = cos(slopy)
                    siny = sin(slopy)
                    arrow_base = max(round(self.state['line_width'] * 3), 7)  # half side length
                    arrow_height = sqrt(3) * arrow_base  # height of triangle

                    if self.arrow_start:
                        self._draw_arrow_head(hdc_bitmap2, x, y, -cosy, -siny, arrow_base, arrow_height)
                        gdi32.MoveToEx(hdc_bitmap2, x - round(arrow_height * cosy), y - round(arrow_height * siny), None)
                    else:
                        gdi32.MoveToEx(hdc_bitmap2, x, y, None)
                    if self.arrow_end:
                        gdi32.LineTo(hdc_bitmap2, pt_dest_abs.x + round(arrow_height * cosy), pt_dest_abs.y + round(arrow_height * siny))
                        self._draw_arrow_head(hdc_bitmap2, pt_dest_abs.x, pt_dest_abs.y, cosy, siny, arrow_base, arrow_height)
                    else:
                        gdi32.LineTo(hdc_bitmap2, pt_dest_abs.x, pt_dest_abs.y)
                else:
                    gdi32.MoveToEx(hdc_bitmap2, x, y, None)
                    gdi32.LineTo(hdc_bitmap2, pt_dest_abs.x, pt_dest_abs.y)

            gdi32.DeleteDC(hdc_bitmap2)
            user32.ReleaseDC(self.canvas.static.hwnd, hdc_static2)

            user32.InvalidateRect(self.canvas.static.hwnd, None, TRUE)

            img = hbitmap_to_image(self.canvas.static.h_bitmap)

            ########################################
            # Restore mode
            ########################################

#            print('OLD - NEW', self.main.img.mode, img.mode)

            if self.main.img.mode in ('P', 'PA'):
                pal_img = self.main.img.convert('P') if self.main.img.mode == 'PA' else self.main.img
                img = img.quantize(palette=pal_img, dither=Image.Dither.NONE)

            elif self.main.img.mode in ('L', 'LA'):
                img = img.convert('L')

            elif self.main.img.mode in ('1', 'CMYK'):
                img = img.convert(self.main.img.mode)

#MODE_TO_BPP = {'1': 1, 'P': 8, 'L': 8, 'PA': 16, 'LA': 16, 'RGB': 24, 'RGBA': 32, 'CMYK': 32}

            ########################################
            # Restore alpha channel
            ########################################

            if self.main.img.mode in ('RGBA', 'LA', 'PA'):
                alpha = self.main.img.getchannel('A')
#                img = img.convert('RGB')
                img.putalpha(alpha)

            img.info = self.main.img.info
            img.format = self.main.img.format

            self.main.img = img
            self.main.undo_stack.push(self.main.img)

            if self.main.img.mode in ('RGBA', 'LA', 'PA'):
                self.main.canvas.update_hbitmap(image_to_hbitmap(self.main.img))

        self.canvas.static.register_message_callback(WM_LBUTTONUP, _on_WM_LBUTTONUP)

    ########################################
    #
    ########################################
    def _draw_arrow_head(self, hdc, x, y, cosy, siny, arrow_base, arrow_height):
        state = gdi32.SaveDC(hdc)
        hbr = gdi32.CreateSolidBrush(self.state['pen_color'])
        gdi32.SelectObject(hdc, hbr)
        gdi32.SelectObject(hdc, HPEN_NULL)
        vert = (POINT * 3)()
        vert[0].x = x + round( arrow_height * cosy - ( arrow_base * siny ) )
        vert[0].y = y + round( arrow_height * siny + ( arrow_base * cosy ) )
        vert[1] = POINT(x, y)  #m_Two;
        vert[2].x = x + round( arrow_height * cosy + arrow_base * siny )
        vert[2].y = y - round( arrow_base * cosy - arrow_height * siny )
#        if(as->openArrowHead)
#            Polyline(hDC,vert,3);
#        else
        gdi32.Polygon(hdc, vert, 3)
        gdi32.DeleteObject(hbr)
        gdi32.RestoreDC(hdc, state)

    ########################################
    #
    ########################################
    def _draw_paintbrush(self, x, y):
        pt_last = POINT(x, y)
        pt_canvas = POINT(round(x / self.canvas.zoom), round(y / self.canvas.zoom))

        user32.SetCapture(self.canvas.static.hwnd)

        hdc_static = user32.GetDC(self.canvas.static.hwnd)
        hdc_bitmap = gdi32.CreateCompatibleDC(hdc_static)

        gdi32.SelectObject(hdc_bitmap, self.hpen)

        line_width = self.state['line_width']

        def _normalize(rc):
            if rc.right < rc.left:
                rc.left, rc.right = rc.right, rc.left
            if rc.bottom < rc.top:
                rc.top, rc.bottom = rc.bottom, rc.top

        ########################################
        #
        ########################################
        def _on_WM_MOUSEMOVE(hwnd, wparam, lparam):
            x, y = GET_X_LPARAM(lparam), GET_Y_LPARAM(lparam)
            x_canvas, y_canvas = round(x / self.canvas.zoom), round(y / self.canvas.zoom)

            state = gdi32.SaveDC(hdc_bitmap)
            gdi32.SelectObject(hdc_bitmap, self.canvas.static.h_bitmap)

            gdi32.MoveToEx(hdc_bitmap, pt_canvas.x, pt_canvas.y, None)
            gdi32.LineTo(hdc_bitmap, x_canvas, y_canvas)

            gdi32.RestoreDC(hdc_bitmap, state)

#                    user32.InvalidateRect(self.canvas.static.hwnd, None, FALSE)

            rc = RECT(pt_last.x, pt_last.y, x, y)
            _normalize(rc)
            user32.InflateRect(byref(rc), line_width, line_width)
            user32.InvalidateRect(self.canvas.static.hwnd, byref(rc), FALSE)

            pt_last.x = x
            pt_last.y = y
            pt_canvas.x = x_canvas
            pt_canvas.y = y_canvas

        self.canvas.static.register_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)

        ########################################
        #
        ########################################
        def _on_WM_LBUTTONUP(hwnd, wparam, lparam):

            gdi32.DeleteDC(hdc_bitmap)
            user32.ReleaseDC(self.canvas.static.hwnd, hdc_static)

            user32.ReleaseCapture(self.canvas.static.hwnd)
            self.canvas.static.unregister_message_callback(WM_MOUSEMOVE, _on_WM_MOUSEMOVE)
            self.canvas.static.unregister_message_callback(WM_LBUTTONUP, _on_WM_LBUTTONUP)

            img = hbitmap_to_image(self.canvas.static.h_bitmap)
            img.info = self.main.img.info
            self.main.img = img
            self.main.undo_stack.push(self.main.img)

        self.canvas.static.register_message_callback(WM_LBUTTONUP, _on_WM_LBUTTONUP)

    ########################################
    # Slow!
    ########################################
    def _draw_floodfill(self, x, y):
        x, y = int(x / self.canvas.zoom), int(y / self.canvas.zoom)
#        if self.state['tolerance']:

        img = self.main.img.copy()

        def _color_to_index(color):
            if self.main.img.mode in ('P', 'PA'):
                pal = self.main.img.getpalette()
                pal = [RGB_TO_CR(pal[i], pal[i+1], pal[i+2]) for i in range(0, len(pal), 3)]
                return pal.index(color)
            else:
                return color & 0xFF

        if img.mode in ('P', 'PA', 'L', 'LA'):
            ImageDraw.floodfill(img, (x, y), _color_to_index(self.state['brush_color']), thresh=self.state['tolerance'])
        else:
            ImageDraw.floodfill(img, (x, y), CR_TO_RGB(self.state['brush_color']), thresh=self.state['tolerance'])

        self.main.img = img
        self.main.undo_stack.push(self.main.img)
        self.canvas.update_hbitmap(image_to_hbitmap(self.main.img))

#        else:
#            hdc_static = user32.GetDC(self.canvas.static.hwnd)
#            hdc_bitmap = gdi32.CreateCompatibleDC(hdc_static)
#            gdi32.SelectObject(hdc_bitmap, self.canvas.static.h_bitmap)
#            gdi32.SelectObject(hdc_bitmap, self.hbrush)
#            gdi32.ExtFloodFill(hdc_bitmap, x, y, gdi32.GetPixel(hdc_static, x, y), FLOODFILLSURFACE)
#            gdi32.DeleteDC(hdc_bitmap)
#            user32.ReleaseDC(self.canvas.static.hwnd, hdc_static)
#        user32.InvalidateRect(self.canvas.static.hwnd, None, FALSE)

    ########################################
    #
    ########################################
    def _pick_color(self, x, y):
#                x, y = int(x / self.canvas.zoom), int(y / self.canvas.zoom)
        hdc_static = user32.GetDC(self.canvas.static.hwnd)
        if self.picker_mode == IDM_PICKER_BRUSH:
            self.state['brush_color'] = gdi32.GetPixel(hdc_static, x, y)
            self.update_brush()
        else:
            self.state['pen_color'] = gdi32.GetPixel(hdc_static, x, y)
            self.update_pen()
        self.static_colors.redraw_window()

        user32.ReleaseDC(self.canvas.static.hwnd, hdc_static)
        self.set_current_tool(IDM_PAINT_SELECT)
