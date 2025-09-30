from ctypes import byref, cast, sizeof, POINTER, create_unicode_buffer
from ctypes.wintypes import BYTE, DWORD, LPWSTR, HKEY

from .dlls import advapi32
from .const import HKEY_CURRENT_USER, ERROR_SUCCESS, REG_DWORD, REG_SZ

MAX_TEXT_LEN = 2024


class Settings():

    ########################################
    #
    ########################################
    def __init__(self, app_name, settings_dict=None):
        self._app_name = app_name
        if settings_dict:
            self.load(settings_dict)

    ########################################
    # Load from registry
    ########################################
    def load(self, settings_dict):
        hkey = HKEY()
        if advapi32.RegOpenKeyW(HKEY_CURRENT_USER, f'Software\\{self._app_name}' , byref(hkey)) != ERROR_SUCCESS:
            return False
        data = (BYTE * sizeof(DWORD))()
        cbdata = DWORD(sizeof(data))
        data_str = (BYTE * MAX_TEXT_LEN)()
        for k, v in settings_dict.items():
            if type(v) == bool:
                if advapi32.RegQueryValueExW(hkey, k, None, None, byref(data), byref(cbdata)) == ERROR_SUCCESS:
                    settings_dict[k] = bool(cast(data, POINTER(DWORD)).contents.value)
            elif type(v) == int:
                if advapi32.RegQueryValueExW(hkey, k, None, None, byref(data), byref(cbdata)) == ERROR_SUCCESS:
                    settings_dict[k] = cast(data, POINTER(DWORD)).contents.value
            elif type(v) == str:
                cbdata_str = DWORD(sizeof(data_str))
                if advapi32.RegQueryValueExW(hkey, k, None, None, data_str, byref(cbdata_str)) == ERROR_SUCCESS:
                    settings_dict[k] = cast(data_str, LPWSTR).value
            elif type(v) == list or type(v) == dict:
                cbdata_str = DWORD(sizeof(data_str))
                if advapi32.RegQueryValueExW(hkey, k, None, None, data_str, byref(cbdata_str)) == ERROR_SUCCESS:
                    settings_dict[k] = eval(cast(data_str, LPWSTR).value)

        advapi32.RegCloseKey(hkey)
        return True

    ########################################
    # Save to registry
    ########################################
    def save(self, settings_dict):
        hkey = HKEY()
        if advapi32.RegOpenKeyW(HKEY_CURRENT_USER, f'Software\\{self._app_name}' , byref(hkey)) != ERROR_SUCCESS:
            advapi32.RegCreateKeyW(HKEY_CURRENT_USER, f'Software\\{self._app_name}' , byref(hkey))
            advapi32.RegCloseKey(hkey)
        if advapi32.RegOpenKeyW(HKEY_CURRENT_USER, f'Software\\{self._app_name}' , byref(hkey)) != ERROR_SUCCESS:
            return False
        dwsize = sizeof(DWORD)
        for k, v in settings_dict.items():
            if type(v) == bool:
                v = int(v)
                advapi32.RegSetValueExW(hkey, k, 0, REG_DWORD, byref(DWORD(v)), dwsize)
            elif type(v) == int:
                advapi32.RegSetValueExW(hkey, k, 0, REG_DWORD, byref(DWORD(v)), dwsize)
            elif type(v) == str:
                buf = create_unicode_buffer(v)
                advapi32.RegSetValueExW(hkey, k, 0, REG_SZ, buf, sizeof(buf))
            elif type(v) == list or type(v) == dict:
                buf = create_unicode_buffer(str(v))
                advapi32.RegSetValueExW(hkey, k, 0, REG_SZ, buf, sizeof(buf))
        advapi32.RegCloseKey(hkey)
        return True
