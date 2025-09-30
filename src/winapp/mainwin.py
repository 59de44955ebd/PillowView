import os

from ctypes import (windll, WINFUNCTYPE, c_int64, c_int, c_uint, c_uint64, c_long, c_ulong, c_longlong, c_voidp, c_wchar_p, Structure,
        sizeof, byref, create_string_buffer, create_unicode_buffer, cast,  c_char_p, pointer)
from ctypes.wintypes import (HWND, WORD, DWORD, LONG, HICON, WPARAM, LPARAM, HANDLE, LPCWSTR, MSG, UINT, LPWSTR, HINSTANCE,
        LPVOID, INT, RECT, POINT, BYTE, BOOL, COLORREF, LPPOINT)

from .const import *
from .wintypes_extended import *
from .dlls import comdlg32, gdi32, shell32, user32, ACCEL
from .window import *
from .menu import *
from .themes import *
from .dialog import *

# HOOK
class CWPRETSTRUCT(Structure):
    _fields_ = [
        ("lResult", LPARAM),
        ("lParam", LPARAM),
        ("wParam", WPARAM),
        ("message", UINT),
        ("hwnd", HWND),
    ]

HOOKPROC = WINFUNCTYPE(LPARAM, INT, WPARAM, LPARAM)

#class ExternalDialog():
#    def __init__(self, hdlg):
#        self.hwnd = hdlg


class MainWin(Window):

    ########################################
    #
    ########################################
    def __init__(self,
        window_title='MyPythonApp',
        window_class='MyPythonApp',
#        hicon=0,
        hicon=user32.LoadImageW(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'app.ico'), IMAGE_ICON, 48, 48, LR_LOADFROMFILE),
        left=CW_USEDEFAULT, top=CW_USEDEFAULT, width=CW_USEDEFAULT, height=CW_USEDEFAULT,
        style=WS_OVERLAPPEDWINDOW,
        ex_style=0,
#        color=None,
        hbrush=COLOR_WINDOW + 1,
        dark_bg_brush=DARK_BG_BRUSH,
        menu_data=None,
        menu_mod_translation_table=None,
        hmenu=0,
        accelerators=None,
        haccel=None,
        cursor=None,
        parent_window=None,
        class_style=CS_VREDRAW | CS_HREDRAW
    ):

        self.hicon = hicon

        self.__window_title = window_title
        self.__popup_menus = {}
        self.__timers = {}
        self.__timer_id_counter = 1000

        # For asnyc dialogs
        self.__current_dialogs = []
        self.dialog_hwnds = []

        def _on_WM_TIMER(hwnd, wparam, lparam):
            if wparam in self.__timers:
                callback = self.__timers[wparam][0]
                if self.__timers[wparam][1]:
                    user32.KillTimer(self.hwnd, wparam)
                    del self.__timers[wparam]
                callback()
            # An application should return zero if it processes this message.
            return 0

        self.__message_map = {
            WM_TIMER:        [_on_WM_TIMER],
            WM_CLOSE:        [self.quit],
        }

        def _window_proc_callback(hwnd, msg, wparam, lparam):
            if msg in self.__message_map:
                for callback in self.__message_map[msg]:
                    res = callback(hwnd, wparam, lparam)
                    if res is not None:
                        return res
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self.windowproc = WNDPROC(_window_proc_callback)

#        if type(color) == int:
#            hbrush = color + 1
#        elif type(color) == COLORREF:
#            hbrush = gdi32.CreateSolidBrush(color)
#        elif hbrush is None:
#            hbrush = COLOR_WINDOW + 1

        self.bg_brush_light = hbrush
        self.dark_bg_brush = dark_bg_brush

        newclass = WNDCLASSEX()
        newclass.lpfnWndProc = self.windowproc
        newclass.style = class_style
        newclass.lpszClassName = window_class
        newclass.hBrush = self.bg_brush_light  #hbrush
        newclass.hCursor = user32.LoadCursorW(0, cursor if cursor else IDC_ARROW)
        newclass.hIcon = self.hicon

        accels = []

        if menu_data:
            self.hmenu = user32.CreateMenu()
            handle_menu_items(self.hmenu, menu_data['items'], accels, menu_mod_translation_table)
        else:
            self.hmenu = hmenu

        user32.RegisterClassExW(byref(newclass))

        super().__init__(
            newclass.lpszClassName,
            style=style,
            ex_style=ex_style,
            left=left, top=top, width=width, height=height,
            window_title=window_title,
            hmenu=self.hmenu,
            parent_window=parent_window
        )

        if accelerators:
            accels += accelerators

        if len(accels):
            acc_table = (ACCEL * len(accels))()
            for (i, acc) in enumerate(accels):
                acc_table[i] = ACCEL(TRUE | acc[0], acc[1], acc[2])
            self.haccel = user32.CreateAcceleratorTableW(acc_table, len(accels))
        else:
            self.haccel = haccel

    ########################################
    #
    ########################################
    def make_popup_menu(self, menu_data):
        hmenu = user32.CreatePopupMenu()
        handle_menu_items(hmenu, menu_data['items'])
        return hmenu

    ########################################
    #
    ########################################
    def show_popup_menu(self, hmenu, x=None, y=None, uflags=TPM_LEFTBUTTON):
        if x is None:
            pt = POINT()
            user32.GetCursorPos(byref(pt))
            x, y = pt.x, pt.y
        res = user32.TrackPopupMenuEx(hmenu, uflags, x, y, self.hwnd, 0)  #  | TPM_RETURNCMD | TPM_NONOTIFY
        user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        return res

    ########################################
    #
    ########################################
    def get_dropped_items(self, hdrop):
        dropped_items = []
        cnt = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
        for i in range(cnt):
            file_buffer = create_unicode_buffer('', MAX_PATH)
            shell32.DragQueryFileW(hdrop, i, file_buffer, MAX_PATH)
            dropped_items.append(file_buffer[:].split('\0', 1)[0])
        shell32.DragFinish(hdrop)
        return dropped_items

    ########################################
    #
    ########################################
    def create_timer(self, callback, ms, is_singleshot=False, timer_id=None):
        if timer_id is None:
            timer_id = self.__timer_id_counter
            self.__timer_id_counter += 1
        self.__timers[timer_id] = (callback, is_singleshot)
        user32.SetTimer(self.hwnd, timer_id, ms, 0)
        return timer_id

    ########################################
    #
    ########################################
    def kill_timer(self, timer_id):
        if timer_id in self.__timers:
            user32.KillTimer(self.hwnd, timer_id)
            del self.__timers[timer_id]

    ########################################
    #
    ########################################
    def register_message_callback(self, msg, callback, overwrite=False):
        if overwrite:
            self.__message_map[msg] = [callback]
        else:
            if msg not in self.__message_map:
                self.__message_map[msg] = []
            self.__message_map[msg].append(callback)
        if msg == WM_DROPFILES:
            shell32.DragAcceptFiles(self.hwnd, True)

    ########################################
    #
    ########################################
    def unregister_message_callback(self, msg, callback=None):
        if msg in self.__message_map:
            if callback is None:  # was: == True
                del self.__message_map[msg]
            elif callback in self.__message_map[msg]:
                self.__message_map[msg].remove(callback)
                if len(self.__message_map[msg]) == 0:
                    del self.__message_map[msg]

    ########################################
    #
    ########################################
    def run(self):
        msg = MSG()

        while user32.GetMessageW(byref(msg), 0, 0, 0) > 0:

            if self.haccel and user32.TranslateAcceleratorW(self.hwnd, self.haccel, byref(msg)):
                continue

            # unfortunately this disables global accelerators while a dialog is shown
#            for dialog in self.__current_dialogs:
#                if user32.IsDialogMessageW(dialog.hwnd, byref(msg)):
#                    break

            for hdlg in self.dialog_hwnds:
                if user32.IsDialogMessageW(hdlg, byref(msg)):
                    break

            # If the inner loop completes without encountering
            # the break statement then the following else
            # block will be executed and outer loop will continue
            else:
                user32.TranslateMessage(byref(msg))
                user32.DispatchMessageW(byref(msg))

        if self.haccel:
            user32.DestroyAcceleratorTable(self.haccel)
        user32.DestroyWindow(self.hwnd)
        user32.DestroyIcon(self.hicon)
        return 0

    ########################################
    #
    ########################################
    def quit(self, *args):
        user32.PostMessageW(self.hwnd, WM_QUIT, 0, 0)

    ########################################
    #
    ########################################
    def apply_theme(self, is_dark):
        super().apply_theme(is_dark)

        # Update colors of window titlebar
        dwm_use_dark_mode(self.hwnd, is_dark)

        user32.SetClassLongPtrW(self.hwnd, GCL_HBRBACKGROUND, self.dark_bg_brush if is_dark else self.bg_brush_light)

        # Update colors of menus
        uxtheme.SetPreferredAppMode(PreferredAppMode.ForceDark if is_dark else PreferredAppMode.ForceLight)
        uxtheme.FlushMenuThemes()

        if self.hmenu:
            # Update colors of menubar
            if is_dark:
                def _on_WM_UAHDRAWMENU(hwnd, wparam, lparam):
                    pUDM = cast(lparam, POINTER(UAHMENU)).contents
                    mbi = MENUBARINFO()
                    ok = user32.GetMenuBarInfo(hwnd, OBJID_MENU, 0, byref(mbi))
                    rc_win = RECT()
                    user32.GetWindowRect(hwnd, byref(rc_win))
                    rc = mbi.rcBar
                    user32.OffsetRect(byref(rc), -rc_win.left, -rc_win.top)

                    #user32.FillRect(pUDM.hdc, byref(rc), DARK_MENUBAR_BG_BRUSH)
                    user32.FillRect(pUDM.hdc, byref(rc), DARK_BG_BRUSH)

                    return TRUE
                self.register_message_callback(WM_UAHDRAWMENU, _on_WM_UAHDRAWMENU)

                def _on_WM_UAHDRAWMENUITEM(hwnd, wparam, lparam):
                    pUDMI = cast(lparam, POINTER(UAHDRAWMENUITEM)).contents
                    mii = MENUITEMINFOW()
                    mii.fMask = MIIM_STRING
                    buf = create_unicode_buffer('', 256)
                    mii.dwTypeData = cast(buf, LPWSTR)
                    mii.cch = 256
                    ok = user32.GetMenuItemInfoW(pUDMI.um.hmenu, pUDMI.umi.iPosition, TRUE, byref(mii))
                    if pUDMI.dis.itemState & ODS_HOTLIGHT or pUDMI.dis.itemState & ODS_SELECTED:
                        user32.FillRect(pUDMI.um.hdc, byref(pUDMI.dis.rcItem), DARK_MENU_BG_BRUSH_HOT)
                    else:
                        #user32.FillRect(pUDMI.um.hdc, byref(pUDMI.dis.rcItem), DARK_MENUBAR_BG_BRUSH)
                        user32.FillRect(pUDMI.um.hdc, byref(pUDMI.dis.rcItem), DARK_BG_BRUSH)
                    gdi32.SetBkMode(pUDMI.um.hdc, TRANSPARENT)
                    gdi32.SetTextColor(pUDMI.um.hdc, DARK_TEXT_COLOR)
                    user32.DrawTextW(pUDMI.um.hdc, mii.dwTypeData, len(mii.dwTypeData), byref(pUDMI.dis.rcItem), DT_CENTER | DT_SINGLELINE | DT_VCENTER)
                    return TRUE
                self.register_message_callback(WM_UAHDRAWMENUITEM, _on_WM_UAHDRAWMENUITEM)

                def UAHDrawMenuNCBottomLine(hwnd, wparam, lparam):
                    rcClient = RECT()
                    user32.GetClientRect(hwnd, byref(rcClient))
                    user32.MapWindowPoints(hwnd, None, byref(rcClient), 2)
                    rcWindow = RECT()
                    user32.GetWindowRect(hwnd, byref(rcWindow))
                    user32.OffsetRect(byref(rcClient), -rcWindow.left, -rcWindow.top)
                    # the rcBar is offset by the window rect
                    rcAnnoyingLine = rcClient
                    rcAnnoyingLine.bottom = rcAnnoyingLine.top
                    rcAnnoyingLine.top -= 1
                    hdc = user32.GetWindowDC(hwnd)

                    # no line at all
                    user32.FillRect(hdc, byref(rcAnnoyingLine), DARK_BG_BRUSH)

                    #dark line (same as toolbar button bg)
                    #user32.FillRect(hdc, byref(rcAnnoyingLine), DARK_SEPARATOR_BRUSH)

                    user32.ReleaseDC(hwnd, hdc)

                def _on_WM_NCPAINT(hwnd, wparam, lparam):
                    user32.DefWindowProcW(hwnd, WM_NCPAINT, wparam, lparam)
                    UAHDrawMenuNCBottomLine(hwnd, wparam, lparam)
                    return TRUE
                self.register_message_callback(WM_NCPAINT, _on_WM_NCPAINT)

                def _on_WM_NCACTIVATE(hwnd, wparam, lparam):
                    user32.DefWindowProcW(hwnd, WM_NCACTIVATE, wparam, lparam)
                    UAHDrawMenuNCBottomLine(hwnd, wparam, lparam)
                    return TRUE
                self.register_message_callback(WM_NCACTIVATE, _on_WM_NCACTIVATE)

            else:
                self.unregister_message_callback(WM_UAHDRAWMENU)
                self.unregister_message_callback(WM_UAHDRAWMENUITEM)
                self.unregister_message_callback(WM_NCPAINT)
                self.unregister_message_callback(WM_NCACTIVATE)

        self.redraw_window()

    ########################################
    #
    ########################################
    def dialog_show_async(self, dialog, hidden=False):
        self.__current_dialogs.append(dialog)
        dialog._show_async(hidden)

    ########################################
    #
    ########################################
    def dialog_show_sync(self, dialog, lparam=0):
        res = dialog._show_sync(lparam=lparam)
        user32.SetActiveWindow(self.hwnd)
        return res

    ########################################
    #
    ########################################
#    def _dialog_remove(self, dialog):
#        if dialog in self.__current_dialogs:
#            self.__current_dialogs.remove(dialog)

    ########################################
    # was: get_open_filename
    ########################################
    def show_open_file_dialog(self, title='Open...', default_extension='',
                filter_string='All Files (*.*)\0*.*\0\0', initial_path=''):

        file_buffer = create_unicode_buffer(initial_path, MAX_PATH)
        ofn = OPENFILENAMEW()
        ofn.hwndOwner = self.hwnd
        ofn.lStructSize = sizeof(OPENFILENAMEW)
        ofn.lpstrTitle = title
        ofn.lpstrFile = cast(file_buffer, LPWSTR)
        ofn.nMaxFile = MAX_PATH
        ofn.lpstrDefExt = default_extension
        ofn.lpstrFilter = cast(create_unicode_buffer(filter_string), c_wchar_p)
        ofn.Flags = OFN_ENABLESIZING | OFN_PATHMUSTEXIST

#        if self.is_dark:
#            classname_buf = create_unicode_buffer(10)
#            def _hookProc(nCode, wParam, lParam):
#                if nCode < 0:
#                    return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
#                msg = cast(lParam, POINTER(CWPRETSTRUCT)).contents
#                user32.GetClassNameW(msg.hwnd, classname_buf, 10)
#                if classname_buf.value == "#32770":
#                    if msg.message == WM_INITDIALOG:
#                        uxtheme.SetPreferredAppMode(PreferredAppMode.ForceDark)
#                        user32.SendMessageW(msg.hwnd, WM_SETTINGCHANGE, 0, create_unicode_buffer('ImmersiveColorSet'))
#                return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
#            self._hook_proc = HOOKPROC(_hookProc)
#            self._hook = user32.SetWindowsHookExW(WH_CALLWNDPROCRET, self._hook_proc, 0, kernel32.GetCurrentThreadId())
#            ok = comdlg32.GetOpenFileNameW(byref(ofn))
#            user32.UnhookWindowsHookEx(self._hook)
#            self._hook, self._hook_proc = None, None
#        else:
        ok = comdlg32.GetOpenFileNameW(byref(ofn))
        return file_buffer[:].split('\0', 1)[0] if ok else None

    ########################################
    # was: get_save_filename
    ########################################
    def show_save_file_dialog(
        self,
        title='Save...',
        default_extension='',
        filter_string='All Files (*.*)\0*.*\0\0',
        initial_path='',
        flags=OFN_ENABLESIZING | OFN_OVERWRITEPROMPT,
        hinstance=None,
        lpTemplateName=None,
        lpfnHook=None,
        nFilterIndex=0,
    ):
        file_buffer = create_unicode_buffer(initial_path, MAX_PATH)
        ofn = OPENFILENAMEW()
        ofn.hwndOwner = self.hwnd
        ofn.lStructSize = sizeof(OPENFILENAMEW)
        ofn.lpstrTitle = title
        ofn.lpstrFile = cast(file_buffer, LPWSTR)
        ofn.nMaxFile = MAX_PATH
        ofn.lpstrDefExt = default_extension
        ofn.lpstrFilter = cast(create_unicode_buffer(filter_string), c_wchar_p)
        ofn.Flags = flags
        ofn.hInstance = hinstance
        ofn.nFilterIndex = nFilterIndex

        if lpTemplateName:
            ofn.lpTemplateName = lpTemplateName
        if lpfnHook:
            ofn.lpfnHook = lpfnHook

#        if self.is_dark:
#            classname_buf = create_unicode_buffer(10)
#            def _hookProc(nCode, wParam, lParam):
#                if nCode < 0:
#                    return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
#                msg = cast(lParam, POINTER(CWPRETSTRUCT)).contents
#                user32.GetClassNameW(msg.hwnd, classname_buf, 10)
#                if classname_buf.value == "#32770":
#                    if msg.message == WM_INITDIALOG:
#                        uxtheme.SetPreferredAppMode(PreferredAppMode.ForceDark)
#                        user32.SendMessageW(msg.hwnd, WM_SETTINGCHANGE, 0, create_unicode_buffer('ImmersiveColorSet'))
#                return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
#            self._hook_proc = HOOKPROC(_hookProc)
#            self._hook = user32.SetWindowsHookExW(WH_CALLWNDPROCRET, self._hook_proc, 0, kernel32.GetCurrentThreadId())
#            ok = comdlg32.GetSaveFileNameW(byref(ofn))
#            user32.UnhookWindowsHookEx(self._hook)
#            self._hook, self._hook_proc = None, None
#        else:
        ok = comdlg32.GetSaveFileNameW(byref(ofn))
        return file_buffer[:].split('\0', 1)[0] if ok else None

    ########################################
    #
    ########################################
    def show_message_box(self, text, caption='', utype=MB_ICONINFORMATION | MB_OK):
        if self.is_dark:
            classname_buf = create_unicode_buffer(10)
            def _hookProc(nCode, wParam, lParam):
                if nCode < 0:
                    return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
                msg = cast(lParam, POINTER(CWPRETSTRUCT)).contents
                user32.GetClassNameW(msg.hwnd, classname_buf, 10)
                if classname_buf.value == "#32770":
                    if msg.message == WM_INITDIALOG:
                        dwm_use_dark_mode(msg.hwnd, True)
                        comctl32.SetWindowSubclass(msg.hwnd, DarkMsgBoxSubclassProc, 0, 0)
                        hwnd = user32.FindWindowExW(msg.hwnd, None, WC_BUTTON, None)
                        while hwnd:
                            uxtheme.SetWindowTheme(hwnd, 'DarkMode_Explorer', None)
                            hwnd = user32.FindWindowExW(msg.hwnd, hwnd, WC_BUTTON, None)
                return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
            self._hook_proc = HOOKPROC(_hookProc)
            self._hook = user32.SetWindowsHookExW(WH_CALLWNDPROCRET, self._hook_proc, 0, kernel32.GetCurrentThreadId())
            res = user32.MessageBoxW(self.hwnd, text, caption, utype)
            user32.UnhookWindowsHookEx(self._hook)
            self._hook, self._hook_proc = None, None
            return res
        else:
            return user32.MessageBoxW(self.hwnd, text, caption, utype)

    ########################################
    #
    ########################################
    def show_about_windows(self):
        if self.is_dark:
            classname_buf = create_unicode_buffer(10)
            def _hookProc(nCode, wParam, lParam):
                if nCode < 0:
                    return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
                msg = cast(lParam, POINTER(CWPRETSTRUCT)).contents
                user32.GetClassNameW(msg.hwnd, classname_buf, 10)
                if classname_buf.value == "#32770":
                    if msg.message == WM_INITDIALOG:
                        dwm_use_dark_mode(msg.hwnd, True)
                        comctl32.SetWindowSubclass(msg.hwnd, DarkDialogSubclassProc, 0, 0)
                        user32.ShowWindow(user32.GetDlgItem(msg.hwnd, 13095), SW_HIDE)  # hide separator line below the windows logo
                        uxtheme.SetWindowTheme(user32.GetDlgItem(msg.hwnd, IDOK), 'DarkMode_Explorer', None)
                return user32.CallNextHookEx(self._hook, nCode, wParam, lParam)
            self._hook_proc = HOOKPROC(_hookProc)
            self._hook = user32.SetWindowsHookExW(WH_CALLWNDPROCRET, self._hook_proc, 0, kernel32.GetCurrentThreadId())
            shell32.ShellAboutW(self.hwnd, create_unicode_buffer('Windows'), None, None)
            user32.UnhookWindowsHookEx(self._hook)
            self._hook, self._hook_proc = None, None
        else:
            shell32.ShellAboutW(self.hwnd, create_unicode_buffer('Windows'), None, None)

    ########################################
    #
    ########################################
    def show_font_dialog(self, font_name, font_size, font_weight=FW_DONTCARE, font_italic=False, font_underline=False):
#        def _chooseFontDlgProc(hdlg, msg, wParam, lParam):
#            if self.is_dark:
#                if msg == WM_INITDIALOG:
#                    DarkDialogInit(hdlg)
#                elif msg == WM_CTLCOLORDLG:
#                    return DarkOnCtlColorDlg(wParam)
#                elif msg == WM_CTLCOLORSTATIC:
#                    return DarkOnCtlColorStatic(wParam)
#                elif msg == WM_CTLCOLORBTN:
#                    return DarkOnCtlColorBtn(wParam)
#                elif msg == WM_CTLCOLOREDIT:
#                    return DarkOnCtlColorEdit(wParam)
#            return 0

        lf = LOGFONTW(
            lfFaceName = font_name,
            lfHeight = -kernel32.MulDiv(font_size, DPI_Y, 72),
            lfCharSet = ANSI_CHARSET,
            lfWeight = font_weight,
            lfItalic = int(font_italic),
            lfUnderline = int(font_underline)
        )
        cf = CHOOSEFONTW(
            hwndOwner = self.hwnd,
            lpLogFont = pointer(lf),
#            lpfnHook = LPHOOKPROC(_chooseFontDlgProc),
            Flags = CF_INITTOLOGFONTSTRUCT | CF_NOSCRIPTSEL | CF_EFFECTS #| CF_ENABLEHOOK
        )
        if comdlg32.ChooseFontW(byref(cf)):
            return (
                lf.lfFaceName,
                kernel32.MulDiv(-lf.lfHeight, 72, DPI_Y) if lf.lfHeight < 0 else lf.lfHeight,
                lf.lfWeight,
                lf.lfItalic, #> 0
                lf.lfUnderline
            )

    ########################################
    #
    ########################################
    def show_color_dialog(self, initial_color=0, custom_colors=[]):
#        def _darkColorDlgProc(hDlg, uMsg, wParam, lParam):
#            if uMsg == WM_INITDIALOG:
#                DarkDialogInit(hDlg)
#            elif uMsg == WM_ERASEBKGND:
#                rc = RECT()
#                user32.GetClientRect(hDlg, byref(rc))
#                user32.FillRect(wParam, byref(rc), DARK_BG_BRUSH)
#                rc2 = RECT(6, 22, 6+209, 22+135)
#                user32.FillRect(wParam, byref(rc2), COLOR_WINDOW + 1)
#                rc3 = RECT(6, 188, 6 + 209, 188 + 47)
#                user32.FillRect(wParam, byref(rc3), COLOR_WINDOW + 1)
#                return 1
#            elif uMsg == WM_CTLCOLORDLG:
#                return DarkOnCtlColorDlg(wParam)
#            elif uMsg == WM_CTLCOLORSTATIC:
#                return DarkOnCtlColorStatic(wParam)
#            elif uMsg == WM_CTLCOLORBTN:
#                return DarkOnCtlColorBtn(wParam)
#            elif uMsg == WM_CTLCOLOREDIT:
#                return DarkOnCtlColorEdit(wParam)
#            return 0

        cc = CHOOSECOLORW()
        cc.hwndOwner = self.hwnd
        cc.Flags = CC_SOLIDCOLOR | CC_FULLOPEN | CC_RGBINIT
        cc.lpCustColors = (COLORREF * 16)()
        for i, c in enumerate(custom_colors[:16]):
            cc.lpCustColors[i] = c
        cc.rgbResult = initial_color
#        if self.is_dark:
#            cc.Flags |= CC_ENABLEHOOK
#            cc.lpfnHook = LPHOOKPROC(_darkColorDlgProc)
        if comdlg32.ChooseColorW(byref(cc)):
            return cc.rgbResult

    ########################################
    #
    ########################################
    def show_page_setup_dialog(self, pt_print_paper_size, rc_print_margins):
#        def _darkPageSetupDlgProc(hdlg, msg, wParam, lParam):
#            if msg == WM_INITDIALOG:
#                DarkDialogInit(hdlg)
#            elif msg == WM_CTLCOLORDLG:
#                return DarkOnCtlColorDlg(wParam)
#            elif msg == WM_CTLCOLORSTATIC:
#                return DarkOnCtlColorStatic(wParam)
#            elif msg == WM_CTLCOLORBTN:
#                return DarkOnCtlColorBtn(wParam)
#            elif msg == WM_CTLCOLOREDIT or msg == WM_CTLCOLORLISTBOX:
#                return DarkOnCtlColorEdit(wParam)
#            return 0

        psd = PAGESETUPDLGW()
        psd.hwndOwner = self.hwnd
        psd.Flags = PSD_INHUNDREDTHSOFMILLIMETERS | PSD_MARGINS
        psd.ptPaperSize = pt_print_paper_size._obj
        psd.rtMargin = rc_print_margins._obj
#        if self.is_dark:
#            psd.Flags |= PSD_ENABLEPAGESETUPHOOK
#            psd.lpfnPageSetupHook = LPHOOKPROC(_darkPageSetupDlgProc)
        ok = comdlg32.PageSetupDlgW(byref(psd))
        if ok:
            for f,_ in psd.ptPaperSize._fields_:
                setattr(pt_print_paper_size._obj, f, getattr(psd.ptPaperSize, f))
            for f,_ in psd.rtMargin._fields_:
                setattr(rc_print_margins._obj, f, getattr(psd.rtMargin, f))
        return ok

    ########################################
    #
    ########################################
    def show_print_dialog(self):
#        def _darkPrintDlgProc(hdlg, msg, wParam, lParam):
#            if msg == WM_INITDIALOG:
#                DarkDialogInit(hdlg)
#            elif msg == WM_CTLCOLORDLG:
#                return DarkOnCtlColorDlg(wParam)
#            elif msg == WM_CTLCOLORSTATIC:
#                return DarkOnCtlColorStatic(wParam)
#            elif msg == WM_CTLCOLORBTN:
#                return DarkOnCtlColorBtn(wParam)
#            elif msg == WM_CTLCOLOREDIT or msg == WM_CTLCOLORLISTBOX:
#                return DarkOnCtlColorEdit(wParam)
#            return 0

        pdlg = PRINTDLGW()
        # hwndOwner = 0 : legacy dialog
        # hwndOwner = desktop hwnd: slightly more modern dialog (non-UWP)
        # hwndOwner = self.hwnd: modern UWP dialog, but dialog only shown for the first time
        pdlg.hwndOwner = 0
        pdlg.Flags = PD_RETURNDC | PD_USEDEVMODECOPIES | PD_NOSELECTION  # | PD_PRINTSETUP
        pdlg.nFromPage = 1
        pdlg.nToPage = 1
        pdlg.nMinPage = 1
        pdlg.nMaxPage = 0xffff
        pdlg.nStartPage = 0XFFFFFFFF  # START_PAGE_GENERAL
#        if self.is_dark:
#            pdlg.Flags |= PD_ENABLEPRINTHOOK
#            pdlg.lpfnPrintHook = LPHOOKPROC(_darkPrintDlgProc)
        ok = comdlg32.PrintDlgW(byref(pdlg))
        return ok, pdlg

    ########################################
    # Returned fr *must* be saved to prevent garbage collection
    ########################################
    def show_find_dialog(self, dialog_proc, find_what=''):
        fr = FINDREPLACEW()
        fr.hwndOwner = self.hwnd
        fr.Flags = FR_DOWN | FR_FINDNEXT | FR_HIDEWHOLEWORD | FR_ENABLEHOOK
        fr.lpstrFindWhat = cast(create_unicode_buffer(find_what, 260), c_wchar_p)
        fr.wFindWhatLen = 260
        fr.lpfnHook = dialog_proc  # LPFRHOOKPROC
        hdlg = comdlg32.FindTextW(fr)
        return fr, hdlg

    ########################################
    # Returned fr *must* be saved to prevent garbage collection
    ########################################
    def show_replace_dialog(self, dialog_proc, find_what='', replace_with=''):
        fr = FINDREPLACEW()
        fr.hwndOwner = self.hwnd
        fr.Flags = FR_DOWN | FR_FINDNEXT | FR_HIDEWHOLEWORD | FR_ENABLEHOOK
        fr.lpstrFindWhat = cast(create_unicode_buffer(find_what, 260), c_wchar_p)
        fr.wFindWhatLen = 260
        fr.lpstrReplaceWith = cast(create_unicode_buffer(replace_with, 260), c_wchar_p)
        fr.wReplaceWithLen = 260
        fr.lpfnHook = dialog_proc
        hdlg = comdlg32.ReplaceTextW(fr)
        return fr, hdlg

    ########################################
    #
    ########################################
#    def add_external_dialog(self, hdlg):
#        self.__current_dialogs.append(ExternalDialog(hdlg))

    ########################################
    #
    ########################################
#    def remove_external_dialog(self, hdlg):
#        for d in self.__current_dialogs:
#            if d.hwnd == hdlg:
#                self.__current_dialogs.remove(d)
#                break

    ########################################
    #
    ########################################
    def center_dialog(self, hdlg):
        rc_dlg = RECT()
        user32.GetWindowRect(hdlg, byref(rc_dlg))
        rc_parent = self.get_window_rect()
        if (rc_parent.right - rc_parent.left) - (rc_dlg.right - rc_dlg.left) > 20:
            x = rc_parent.left + (((rc_parent.right - rc_parent.left) - (rc_dlg.right - rc_dlg.left)) // 2)
        else:
            x = rcParent.left + 70
        if (rc_parent.bottom - rc_parent.top) - (rc_dlg.bottom - rc_dlg.top) > 20:
            y = rc_parent.top + (((rc_parent.bottom - rc_parent.top) - (rc_dlg.bottom - rc_dlg.top)) // 2)
        else:
            y = rc_parent.top + 60
        user32.SetWindowPos(hdlg, 0, x, y, 0, 0, SWP_NOZORDER | SWP_NOSIZE)
