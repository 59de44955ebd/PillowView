from ctypes import Structure, sizeof, POINTER, byref
from ctypes.wintypes import DWORD, UINT, HBRUSH, HMENU, HBITMAP, LPWSTR, HANDLE, RECT, HWND, BOOL

from .wintypes_extended import ULONG_PTR
from .const import *
from .dlls import user32

class MENUINFO(Structure):
    def __init__(self, *args, **kwargs):
        super(MENUINFO, self).__init__(*args, **kwargs)
        self.cbSize = sizeof(self)
    _fields_ = [
        ('cbSize', DWORD),
        ('fMask', DWORD),
        ('dwStyle', DWORD),
        ('cyMax', UINT),
        ('hbrBack', HBRUSH),
        ('dwContextHelpID', DWORD),
        ('dwMenuData', ULONG_PTR),
    ]
LPMENUINFO = POINTER(MENUINFO)

class MENUITEMINFOW(Structure):
    def __init__(self, *args, **kwargs):
        super(MENUITEMINFOW, self).__init__(*args, **kwargs)
        self.cbSize = sizeof(self)
    _fields_ = [
        ('cbSize', UINT),
        ('fMask', UINT),
        ('fType', UINT),
        ('fState', UINT),
        ('wID', UINT),
        ('hSubMenu', HMENU),
        ('hbmpChecked', HBITMAP),
        ('hbmpUnchecked', HBITMAP),
        ('dwItemData', HANDLE), #ULONG_PTR
        ('dwTypeData', LPWSTR),
        ('cch', UINT),
        ('hbmpItem', HANDLE),
    ]
LPMENUITEMINFOW = POINTER(MENUITEMINFOW)

class MENUBARINFO(Structure):
    def __init__(self, *args, **kwargs):
        super(MENUBARINFO, self).__init__(*args, **kwargs)
        self.cbSize = sizeof(self)
    _pack_ = 4
    _fields_ = [
        ('cbSize', DWORD),
        ('rcBar', RECT),
        ('hMenu', HMENU),
        ('hwndMenu', HWND),
        ('fBarFocused', BOOL),
        ('fFocused', BOOL),
        ('fUnused', BOOL),
    ]

VKEY_NAME_MAP = {
    'Del': VK_DELETE,
    'Plus': VK_OEM_PLUS,
    'Minus': VK_OEM_MINUS,
    'Enter': VK_RETURN,
    'Left': VK_LEFT,
    'Right': VK_RIGHT,
}

########################################
#
########################################
def handle_menu_items(hmenu, menu_items, accels=None, key_mod_translation=None):
    for row in menu_items:
        if row is None or row['caption'] == '-':
            user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, '-')
            continue
        if 'items' in row:

            hmenu_child = user32.CreateMenu()
            #hmenu_child = user32.CreatePopupMenu()

            flags = MF_POPUP
            if 'flags' in row and 'GRAYED' in row['flags']:
                flags |= MF_GRAYED
            user32.AppendMenuW(hmenu, flags, hmenu_child, row['caption'])

            if 'id' in row or 'hbitmap' in row:
                info = MENUITEMINFOW()
#                    ok = user32.GetMenuItemInfoW(hmenu, hmenu_child, FALSE, byref(info))
                info.fMask = 0
                if 'id' in row:
                    info.wID = row['id'] if 'id' in row else -1
                    info.fMask |= MIIM_ID
                if 'hbitmap' in row:
                    info.hbmpItem = row['hbitmap']
                    info.fMask |= MIIM_BITMAP
                user32.SetMenuItemInfoW(hmenu, hmenu_child, FALSE, byref(info))

            handle_menu_items(hmenu_child, row['items'], accels, key_mod_translation)
        else:
#                if row['caption'] == '-':
#                    user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, '-')
#                    continue
            id = row['id'] if 'id' in row else None
            flags = MF_STRING
            if 'flags' in row:
                if 'CHECKED' in row['flags']:
                    flags |= MF_CHECKED
                if 'GRAYED' in row['flags']:
                    flags |= MF_GRAYED
            if '\t' in row['caption']:
                parts = row['caption'].split('\t') #[1]
                vk = parts[1]
                fVirt = 0
                if 'Alt+' in vk:
                    fVirt |= FALT
                    vk = vk.replace('Alt+', '')
                    if key_mod_translation and 'ALT' in key_mod_translation:
                        parts[1] = parts[1].replace('Alt', key_mod_translation['ALT'])
                if 'Ctrl+' in vk:
                    fVirt |= FCONTROL
                    vk = vk.replace('Ctrl+', '')
                    if key_mod_translation and 'CTRL' in key_mod_translation:
                        parts[1] = parts[1].replace('Ctrl', key_mod_translation['CTRL'])
                if 'Shift+' in vk:
                    fVirt |= FSHIFT
                    vk = vk.replace('Shift+', '')
                    if key_mod_translation and 'SHIFT' in key_mod_translation:
                        parts[1] = parts[1].replace('Shift', key_mod_translation['SHIFT'])

                if len(vk) > 1:
                    if key_mod_translation and vk.upper() in key_mod_translation:
                        parts[1] = parts[1].replace(vk, key_mod_translation[vk.upper()])
                    vk = VKEY_NAME_MAP[vk] if vk in VKEY_NAME_MAP else eval('VK_' + vk)
                else:
                    vk = ord(vk)

                if accels is not None:
                    accels.append((fVirt, vk, id))

                row['caption'] = '\t'.join(parts)
            user32.AppendMenuW(hmenu, flags, id, row['caption'])

            if 'hbitmap' in row:
                info = MENUITEMINFOW()
#                    ok = user32.GetMenuItemInfoW(hmenu, id, FALSE, byref(info))
                info.fMask = MIIM_BITMAP
                info.hbmpItem = row['hbitmap']
                user32.SetMenuItemInfoW(hmenu, id, FALSE, byref(info))