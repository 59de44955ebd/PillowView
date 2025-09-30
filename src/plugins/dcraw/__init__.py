import io
import os
import shutil
import subprocess
from PIL import Image

IS_WIN = os.name == "nt"

"""
  Can be overwritten with custom path:

  import DcrawImagePlugin
  DcrawImagePlugin.DCRAW_BIN = "/foo/dcraw"
  ...

"""
DCRAW_BIN = os.path.join(os.path.dirname(__file__), "bin", "dcraw.exe") if IS_WIN else shutil.which("dcraw")

"""
  Load embedded thumbnail instead of actual RAW image if there is one
  and has at least this width (much faster).
  Set to 0 to never load thumbnails.
"""
MIN_THUMB_WIDTH = 640

"""
  (Otherwise) load half-size RAW image (faster)
"""
LOAD_HALF_SIZE = True

DCRAW_FORMATS = [
    ".arw", ".cr2", ".cr3", ".crw", ".dcr", ".dng", ".erf", ".kdc",
    ".mos", ".mrw", ".nef", ".nrw", ".orf", ".pef", ".raf", ".raw",
    ".rwl", ".rw2", ".srf", ".srw", ".x3f"
]

if IS_WIN:
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    startupinfo = None

def _open(fp, filename, ** kwargs):
    ext = os.path.splitext(filename)[1]
    if ext.lower() not in DCRAW_FORMATS:
        raise SyntaxError("No dcraw file")

    raw_format = ext[1:].upper()
    proc = subprocess.run(
        [DCRAW_BIN, "-c", "-e", filename],
        capture_output=True,
        startupinfo=startupinfo
    )
    if MIN_THUMB_WIDTH:
        try:
            # Are there other thumbnail formats?
            img = Image.open(io.BytesIO(proc.stdout), formats=("JPEG", "PPM",))
            if img.width >= MIN_THUMB_WIDTH:
                img.filename = filename
                img.format = raw_format
                return img
        except Exception as e:
            pass
    proc = subprocess.run(
        [DCRAW_BIN, "-c", "-h" if LOAD_HALF_SIZE else "", filename],
        capture_output=True,
        startupinfo=startupinfo
    )
    img = Image.open(io.BytesIO(proc.stdout), formats=("PPM",))
    img.filename = filename
    img.format = raw_format
    return img

# --------------------------------------------------------------------

Image.register_open("DCRAW", _open)
Image.register_extensions("DCRAW", DCRAW_FORMATS)

if __name__ == "__main__":
    img = Image.open("../_test_files/test.nef")
    img.show()
