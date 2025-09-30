import io
import os
import shutil
import subprocess

from PIL import Image

"""
  Can be overwritten with custom path:

  import FfmpegImagePlugin
  FfmpegImagePlugin.FFMPEG_BIN = r"D:\bin\ffmpeg.exe"
  ...

"""
FFMPEG_BIN = shutil.which('ffmpeg')

"""
    Can be overwritten with more or less (container) formats:

    import FfmpegImagePlugin
    FfmpegImagePlugin.VIDEO_FORMATS = (".ogv", ".rm")
  ...
"""
VIDEO_FORMATS = (".avi", ".flv", ".mkv", ".mov", ".mp4", ".mpg", ".mpeg", ".webm", ".wmv", ".vob")

IS_WIN = os.name == 'nt'
if IS_WIN:
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    if ' ' in FFMPEG_BIN:
        FFMPEG_BIN = f'"{FFMPEG_BIN}"'

########################################
#
########################################
def _open(fp, filename, ** kwargs):
    if os.path.splitext(filename)[1].lower() not in VIDEO_FORMATS:
        raise SyntaxError("No FFmpeg file")

    if IS_WIN:
        filename = os.path.realpath(filename)

    def load_frame(filename, frame):
        proc = subprocess.run(
            (
                f"{FFMPEG_BIN} -hide_banner -v 0 -y -i \"{filename}\" -vf select='eq(n\\,{frame})' "
                f"-vframes 1 -c:v bmp -f image2pipe -"
            ),
            startupinfo = startupinfo if IS_WIN else None,
            shell = not IS_WIN,
            capture_output = True,
        )
        img = Image.open(io.BytesIO(proc.stdout), formats=("BMP",))
        img.load()
        return img

    img = load_frame(filename, 0)  #.copy()
    img.filename = filename
    img.format = "FFMPEG"
    img.__frame = 0

    # find number of frames
    if IS_WIN:
        proc = subprocess.run(
            (
                'cmd.exe /cfor /f "usebackq tokens=2 delims= " %F IN '
                f'(`{FFMPEG_BIN} -hide_banner -i "{filename}" -map 0:v:0 -c:v copy '
                '-f null -y nul 2^>^&1 ^|find "frame="`) do @echo %F'
            ),
            capture_output = True,
            startupinfo = startupinfo,
        )
    else:
        proc = subprocess.run(
            (
                f"{FFMPEG_BIN} -hide_banner -i \"{filename}\" -map 0:v:0 -c:v copy -f null -y /dev/null "
                "2>&1 | grep -Eo 'frame= *[0-9]+ *' | grep -Eo '[0-9]+' | tail -1"
            ),
            shell = True,
            capture_output = True,
        )

    img.n_frames = int(proc.stdout.strip())
    img.is_animated = img.n_frames > 1

    def _seek(self, frame):
        if frame < 0 or frame >= self.n_frames:
            raise EOFError()
        self.__frame = frame
        _img = load_frame(self.filename, frame)
        self.im = _img.im
        _img.close()

    img.seek = _seek.__get__(img)

    img.tell = lambda: img.__frame

    # Image.show() calls dump with 'save_all': True, remove this
    img._dump = (lambda file = None, format = None, d = img._dump, **options:
            options.update({"save_all": False}) or d(file, format, **options))

    return img

# --------------------------------------------------------------------

Image.register_open("FFMPEG", _open)

Image.register_extensions(
    "FFMPEG", VIDEO_FORMATS
)

if __name__ == "__main__":
    img = Image.open("_test_files/test.mp4")
    img.seek(123)
    img.show()
