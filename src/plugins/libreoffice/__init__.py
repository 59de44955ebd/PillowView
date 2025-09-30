import os
import subprocess
from PIL import Image

"""
    Location of sdraw can be customized like this:

    import LibreImagePlugin
    LibreImagePlugin.SDRAW_BIN = "/foo/bar/sdraw"
    ...
"""

IS_WIN = os.name == "nt"
if IS_WIN:
    SDRAW_BIN = r"C:\Program Files\LibreOffice\program\sdraw.exe"

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    SDRAW_BIN = "/opt/libreoffice24.8/program/sdraw"  # Debian, LibreOffice 24.8
    startupinfo = None

def _open(fp, filename, ** kwargs):

    if os.path.splitext(filename)[1].lower() not in [".cdr", ".odg", ".fh", ".fh1", ".fh2", ".fh3", ".fh4", ".fh5", ".fh6", ".fh7", ".fh8", ".fh9", ".fh10", ".fh11"]:
        raise SyntaxError("No LibreOffice file")

    tmp_dir = os.environ["TMP"] if IS_WIN else "/tmp"
    tmp_dir = os.path.join(tmp_dir, "~libreplug")
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)

    proc = subprocess.run(
        [SDRAW_BIN, "--headless", "--convert-to", "bmp", "--outdir", tmp_dir, filename],
        startupinfo = startupinfo,
        stdout = subprocess.DEVNULL,
        stderr = subprocess.DEVNULL,
    )

    if proc.returncode == 0:
        bmp = os.path.join(tmp_dir, os.path.splitext(os.path.basename(filename))[0] + ".bmp")
        if os.path.isfile(bmp):
            try:
                im = Image.open(bmp)
                im.load()
                im.filename = filename
                im.format = os.path.splitext(filename)[1][1:].upper()
                return im
            finally:
                os.unlink(bmp)

# --------------------------------------------------------------------

Image.register_open("CDR", _open, lambda prefix: prefix[:4] == b"RIFF" and prefix[8:11] == b"CDR")
Image.register_extension("CDR", ".cdr")

Image.register_open("ODG", _open, lambda prefix: prefix.startswith(b"PK"))
Image.register_extension("ODG", ".odg")

Image.register_open("ODG", _open, lambda prefix: prefix.startswith(b"\x1C"))
Image.register_extensions(
    "FH", [".fh", ".fh1", ".fh2", ".fh3", ".fh4", ".fh5", ".fh6", ".fh7", ".fh8", ".fh9", ".fh10", ".fh11"]
)

if __name__ == "__main__":
    img = Image.open("_test_files/test.cdr")
    img.show()
