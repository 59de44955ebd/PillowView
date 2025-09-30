import locale
locale.setlocale(locale.LC_ALL, '')

########################################
#
########################################
def format_filesize(num):
    for unit in ['B','KiB','MiB']:
        if abs(num) < 1024.0:
            num = locale.format_string('%3.2f', num)
            return f'{num} {unit}'
        num /= 1024.0
    num = locale.format_string('%.2f', num)
    return f'{num} GiB'
