__all__ = ['Plugin']

import os
import shutil
import sys

from winapp.const import *  #MF_POPUP, MF_STRING, MF_SEPARATOR, WM_CLOSE
from winapp.dialog import *
from winapp.dlls import user32
from winapp.wintypes_extended import *

from const import MENU_IMAGE, EVENT_IMAGE_CHANGED

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
import pytesseract

HMOD_RESOURCES = kernel32.LoadLibraryW(os.path.join(os.path.dirname(__file__), 'resources.dll'))

IDD_DLG_OCR = 1
IDC_COMBO = 3
IDC_EDIT = 4

MARGIN = 10

LANGS = {
	'afr':     		'Afrikaans',
	'amh':     		'Amharic',
	'ara':     		'Arabic',
	'asm':     		'Assamese',
	'aze':     		'Azerbaijani',
	'aze_cyrl': 	'Azerbaijani - Cyrilic',
	'bel':     		'Belarusian',
	'ben':     		'Bengali',
	'bod':     		'Tibetan',
	'bos':     		'Bosnian',
	'bre':     		'Breton',
	'bul':     		'Bulgarian',
	'cat':     		'Catalan; Valencian',
	'ceb':     		'Cebuano',
	'ces':     		'Czech',
	'chi_sim': 		'Chinese - Simplified',
	'chi_tra': 		'Chinese - Traditional',
	'chr':     		'Cherokee',
	'cos':     		'Corsican',
	'cym':     		'Welsh',
	'dan':     		'Danish',
	'dan_frak': 	'Danish - Fraktur',
	'deu':     		'German',
	'deu_frak': 	'German - Fraktur',
	'deu_latf': 	'German (Fraktur Latin)',
	'dzo':     		'Dzongkha',
	'ell':     		'Greek, Modern (1453-)',
	'eng':     		'English',
	'enm':     		'English, Middle (1100-1500)',
	'epo':     		'Esperanto',
	'equ':     		'Math / equation detection module',
	'est':     		'Estonian',
	'eus':     		'Basque',
	'fao':     		'Faroese',
	'fas':     		'Persian',
	'fil':     		'Filipino (old - Tagalog)',
	'fin':     		'Finnish',
	'fra':     		'French',
	'frk':     		'German - Fraktur (now deu_latf)',
	'frm':     		'French, Middle (ca.1400-1600)',
	'fry':     		'Western Frisian',
	'gla':     		'Scottish Gaelic',
	'gle':     		'Irish',
	'glg':     		'Galician',
	'grc':     		'Greek, Ancient (to 1453)',
	'guj':     		'Gujarati',
	'hat':     		'Haitian; Haitian Creole',
	'heb':     		'Hebrew',
	'hin':     		'Hindi',
	'hrv':     		'Croatian',
	'hun':     		'Hungarian',
	'hye':     		'Armenian',
	'iku':     		'Inuktitut',
	'ind':     		'Indonesian',
	'isl':     		'Icelandic',
	'ita':     		'Italian',
	'ita_old': 		'Italian - Old',
	'jav':     		'Javanese',
	'jpn':     		'Japanese',
	'kan':     		'Kannada',
	'kat':     		'Georgian',
	'kat_old': 		'Georgian - Old',
	'kaz':     		'Kazakh',
	'khm':     		'Central Khmer',
	'kir':     		'Kirghiz; Kyrgyz',
	'kmr':     		'Kurmanji (Kurdish - Latin Script)',
	'kor':     		'Korean',
	'kor_vert': 	'Korean (vertical)',
	'kur':     		'Kurdish (Arabic Script)',
	'lao':     		'Lao',
	'lat':     		'Latin',
	'lav':     		'Latvian',
	'lit':     		'Lithuanian',
	'ltz':     		'Luxembourgish',
	'mal':     		'Malayalam',
	'mar':     		'Marathi',
	'mkd':     		'Macedonian',
	'mlt':     		'Maltese',
	'mon':     		'Mongolian',
	'mri':     		'Maori',
	'msa':     		'Malay',
	'mya':     		'Burmese',
	'nep':     		'Nepali',
	'nld':     		'Dutch; Flemish',
	'nor':     		'Norwegian',
	'oci':     		'Occitan (post 1500)',
	'ori':     		'Oriya',
	'pan':     		'Panjabi; Punjabi',
	'pol':     		'Polish',
	'por':     		'Portuguese',
	'pus':     		'Pushto; Pashto',
	'que':     		'Quechua',
	'ron':     		'Romanian; Moldavian; Moldovan',
	'rus':     		'Russian',
	'san':     		'Sanskrit',
	'sin':     		'Sinhala; Sinhalese',
	'slk':     		'Slovak',
	'slk_frak': 	'Slovak - Fraktur',
	'slv':     		'Slovenian',
	'snd':     		'Sindhi',
	'spa':     		'Spanish; Castilian',
	'spa_old': 		'Spanish; Castilian - Old',
	'sqi':     		'Albanian',
	'srp':     		'Serbian',
	'srp_latn': 	'Serbian - Latin',
	'sun':     		'Sundanese',
	'swa':     		'Swahili',
	'swe':     		'Swedish',
	'syr':     		'Syriac',
	'tam':     		'Tamil',
	'tat':     		'Tatar',
	'tel':     		'Telugu',
	'tgk':     		'Tajik',
	'tgl':     		'Tagalog (new - Filipino)',
	'tha':     		'Thai',
	'tir':     		'Tigrinya',
	'ton':     		'Tonga',
	'tur':     		'Turkish',
	'uig':     		'Uighur; Uyghur',
	'ukr':     		'Ukrainian',
	'urd':     		'Urdu',
	'uzb':     		'Uzbek',
	'uzb_cyrl': 	'Uzbek - Cyrilic',
	'vie':     		'Vietnamese',
	'yid':     		'Yiddish',
	'yor':     		'Yoruba'
}


class Plugin():

    ########################################
    #
    ########################################
    def __init__(self, main, **kwargs):

        if not shutil.which('tesseract'):
            if os.path.isfile(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
                # If you don't have tesseract executable in your PATH, include the following:
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            else:
                raise Exception("Tesseract was neither found in the PATH nor in the default installation folder.\n\nTo use this plugin you first have to install Tesseract.")

        self.main = main

        hmenu = user32.GetSubMenu(main.hmenu, MENU_IMAGE)
        user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, '')
        idm_ocr = main.idm_last + 1
        user32.AppendMenuW(hmenu, MF_STRING | MF_GRAYED, idm_ocr, 'Extract Text (OCR)...')
        main.COMMAND_MESSAGE_MAP[idm_ocr] = self.action_ocr
        main.idm_last += 1

        def _image_changed():
            flag = MF_BYCOMMAND | (MF_ENABLED if main.img else MF_GRAYED)
            user32.EnableMenuItem(hmenu, idm_ocr, flag)

        main.connect(EVENT_IMAGE_CHANGED, _image_changed)

    ########################################
    #
    ########################################
    def action_ocr(self):

        class ctx():
            pass

        ########################################
        #
        ########################################
        def _dialog_proc_callback(hwnd, msg, wparam, lparam):
            if msg == WM_INITDIALOG:
                if self.main.is_dark:
                    DarkDialogInit(hwnd)

                user32.SendMessageW(hwnd, WM_SETICON, 0, self.main.hicon)

                for k, v in LANGS.items():
                    user32.SendDlgItemMessageW(hwnd, IDC_COMBO, CB_ADDSTRING, 0, v)
                user32.SendDlgItemMessageW(hwnd, IDC_COMBO, CB_SETCURSEL, list(LANGS.keys()).index('eng'), 0)

                ctx.hfont = gdi32.CreateFontW(-13, 0, 0, 0, FW_DONTCARE, FALSE, FALSE, FALSE, ANSI_CHARSET, OUT_TT_PRECIS,
                        CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH | FF_DONTCARE, 'Arial')
                user32.SendDlgItemMessageW(hwnd, IDC_EDIT, WM_SETFONT, ctx.hfont, MAKELPARAM(1, 0))

            elif msg == WM_SIZE:
                width, height = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
                user32.SetWindowPos(user32.GetDlgItem(hwnd, IDOK), NULL, width - MARGIN - 75, 2, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER)
                user32.SetWindowPos(user32.GetDlgItem(hwnd, IDC_EDIT), NULL, 0, 0, width - 2 * MARGIN - 1, height - 69, SWP_NOMOVE | SWP_NOACTIVATE | SWP_NOZORDER)
                user32.SetWindowPos(user32.GetDlgItem(hwnd, IDCANCEL), NULL, width - MARGIN - 90, height - 31, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOZORDER)

            elif msg == WM_GETMINMAXINFO:
                mmi = cast(lparam, POINTER(MINMAXINFO))
                mmi.contents.ptMinTrackSize = POINT(360, 360)
                return 0

            elif msg == WM_CLOSE:
                user32.EndDialog(hwnd, 0)

            elif msg == WM_COMMAND:
                notification_code = HIWORD(wparam)
                if notification_code == BN_CLICKED:
                    control_id = LOWORD(wparam)

                    if control_id == IDCANCEL:
                        user32.EndDialog(hwnd, 0)

                    elif control_id == IDOK:
                        lang = list(LANGS.keys())[user32.SendDlgItemMessageW(hwnd, IDC_COMBO, CB_GETCURSEL, 0, 0)]
                        text = pytesseract.image_to_string(self.main.img, lang=lang) or '(No Text found)'
                        user32.SetWindowTextW(user32.GetDlgItem(hwnd, IDC_EDIT), text.replace('\n', '\r\n'))

            elif self.main.is_dark:
                return DarkDialogHandleMessages(msg, wparam)
            return FALSE

        user32.DialogBoxParamW(
            HMOD_RESOURCES,
            MAKEINTRESOURCEW(IDD_DLG_OCR),
            self.main.hwnd,
            DLGPROC(_dialog_proc_callback),
            NULL
        )

        gdi32.DeleteObject(ctx.hfont)
