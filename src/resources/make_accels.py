import os

APP_DIR = os.path.dirname(os.path.realpath(__file__))

VKEY_NAME_MAP = {
    'Del': 'DELETE',
    'Plus': 'OEM_PLUS',
    'Minus': 'OEM_MINUS',
    'Enter': 'RETURN',
    'Left': 'LEFT',
    'Right': 'RIGHT',
}

with open(os.path.join(APP_DIR, 'menu.rc'), 'r') as f:
    lines = [l.strip() for l in f.read().split('\n')]

lines_new = []

for line in lines:
    if line.startswith('MENUITEM '):
        parts = line[9:].strip().split(',')
        if len(parts) < 2:
            continue
        if '\\t' not in parts[0]:
            continue

        acc = parts[0][parts[0].index('\\t') + 2:-1]

        has_plus = '+' in acc
        letter = acc[acc.rindex('+') + 1:] if has_plus else acc

        if letter in VKEY_NAME_MAP:
            letter = VKEY_NAME_MAP[letter]

        line_new = '  ' + (f'"{letter}"' if len(letter) == 1 else f'VK_{letter}') + f', {parts[1]}, NOINVERT, '
        if has_plus:
            if 'Alt+' in acc:
                line_new += 'ALT, '
            if 'Ctrl+' in acc:
                line_new += 'CONTROL, '
            if 'Shift+' in acc:
                line_new += 'SHIFT, '

        line_new += 'VIRTKEY'
        lines_new.append(line_new)

with open(os.path.join(APP_DIR, 'accels.rc'), 'w') as f:
    f.write('#include "windows.h"\n#include "resources.h"\n\nPILLOWVIEW ACCELERATORS\n{\n')
    f.write('\n'.join(lines_new))
    f.write('\n}\n\n')
