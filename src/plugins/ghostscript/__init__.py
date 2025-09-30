from __future__ import annotations
import io
import os
import shutil
import subprocess
from PIL import Image, ImageFile
from PIL._binary import i32le as i32

import re
import tempfile
from typing import IO

# --------------------------------------------------------------------

split = re.compile(r"^%%([^:]*):[ \t]*(.*)[ \t]*$")
field = re.compile(r"^%[%!\w]([^:]*)[ \t]*$")

IS_WIN = os.name == 'nt'

"""
  Can be overwritten with custom path:

  import GhostImagePlugin
  GhostImagePlugin.GS_BIN = '/foo/gs'
  ...

"""
GS_BIN = os.path.join(os.path.dirname(__file__), 'bin', 'gs.cmd') if IS_WIN else shutil.which('gs')

"""
  Can be overwritten:

  import GhostImagePlugin
  GhostImagePlugin.PDF_DISPLAY_DPI = 300
  ...

"""
PDF_DISPLAY_DPI = 150

# pbm pbmraw pgm pgmraw pgnm pgnmraw pnm pnmraw ppm ppmraw pkm pkmraw pksm pksmraw
# "pnmraw" automatically chooses between PBM ("1"), PGM ("L"), and PPM ("RGB").
PDF_DEVICE = 'ppmraw'

if IS_WIN:
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

########################################
#
########################################
def get_page_count(filename):
    if IS_WIN:
        filename = filename.replace('\\', '\\\\')
    proc = subprocess.run(
        [
            GS_BIN,
            "-dQUIET",
            "-dNOSAFER",
            "-dNODISPLAY",
            "-c",
            f"({filename}) (r) file runpdfbegin pdfpagecount = quit",
        ],
        capture_output = True,
        shell = False,
        startupinfo = startupinfo if IS_WIN else None
    )
    return int(proc.stdout.strip())

########################################
#
########################################
def load_page(filename, page):

    proc = subprocess.run(
        [
            GS_BIN,
            "-dQUIET",
            "-dBATCH",      # exit after processing
            "-dNOPAUSE",    # don't pause between pages
            "-dSAFER",
            f"-r{PDF_DISPLAY_DPI:f}x{PDF_DISPLAY_DPI:f}",
            f"-sPageList={page + 1}",
            f"-sDEVICE={PDF_DEVICE}",
            # The options below are for smoother text rendering. The default text render mode is unbearable.
            "-dInterpolateControl=-1",
            "-dTextAlphaBits=4",
            "-dGraphicsAlphaBits=4",
            "-sOutputFile=-",
            "-f",
            filename,
        ],
        capture_output = True,
        shell = False,
        startupinfo = startupinfo if IS_WIN else None
    )
    img = Image.open(io.BytesIO(proc.stdout), formats=('PPM',))
    img.load()
    return img

def _open_pdf(fp, filename, ** kwargs):

    get_page_count(filename)

    img = load_page(filename, 0)  #.copy()
    img.filename = filename
    img.format = "PDF"
    img.__frame = 0
    img.n_frames = get_page_count(filename)
    img.is_animated = img.n_frames > 1

    def _seek(self, frame):
        if frame < 0 or frame >= self.n_frames:
            raise EOFError()
        self.__frame = frame
        _img = load_page(self.filename, frame)
        self.im = _img.im
        _img.close()

    img.seek = _seek.__get__(img)

    img.tell = lambda: img.__frame

    img._dump = (lambda file=None, format=None, d=img._dump, **options:
            options.update({'save_all': False}) or d(file, format, **options))

    return img


def _accept_eps(prefix: bytes) -> bool:
    return prefix.startswith(b"%!PS") or (
        len(prefix) >= 4 and i32(prefix) == 0xC6D3D0C5
    )


def Ghostscript(
    tile: list[ImageFile._Tile],
    size: tuple[int, int],
    fp: IO[bytes],
    scale: int = 1,
    transparency: bool = False,
) -> Image.core.ImagingCore:
    """Render an image using Ghostscript"""

    # Unpack decoder tile
    args = tile[0].args
    assert isinstance(args, tuple)
    length, bbox = args

    # Hack to support hi-res rendering
    scale = int(scale) or 1
    width = size[0] * scale
    height = size[1] * scale
    # resolution is dependent on bbox and size
    res_x = 72.0 * width / (bbox[2] - bbox[0])
    res_y = 72.0 * height / (bbox[3] - bbox[1])

    out_fd, outfile = tempfile.mkstemp()
    os.close(out_fd)

    infile_temp = None
    if hasattr(fp, "name") and os.path.exists(fp.name):
        infile = fp.name
    else:
        in_fd, infile_temp = tempfile.mkstemp()
        os.close(in_fd)
        infile = infile_temp

        # Ignore length and offset!
        # Ghostscript can read it
        # Copy whole file to read in Ghostscript
        with open(infile_temp, "wb") as f:
            # fetch length of fp
            fp.seek(0, io.SEEK_END)
            fsize = fp.tell()
            # ensure start position
            # go back
            fp.seek(0)
            lengthfile = fsize
            while lengthfile > 0:
                s = fp.read(min(lengthfile, 100 * 1024))
                if not s:
                    break
                lengthfile -= len(s)
                f.write(s)

    if transparency:
        # "RGBA"
        device = "pngalpha"
    else:
        # "pnmraw" automatically chooses between
        # PBM ("1"), PGM ("L"), and PPM ("RGB").
        device = "pnmraw"

    # push data through Ghostscript
    try:
        subprocess.check_call(
            [
                GS_BIN,
                "-q",  # quiet mode
                f"-g{width:d}x{height:d}",  # set output geometry (pixels)
                f"-r{res_x:f}x{res_y:f}",  # set input DPI (dots per inch)
                "-dBATCH",  # exit after processing
                "-dNOPAUSE",  # don't pause between pages
                "-dSAFER",  # safe mode
                f"-sDEVICE={device}",
                f"-sOutputFile={outfile}",  # output file
                # adjust for image origin
                "-c",
                f"{-bbox[0]} {-bbox[1]} translate",
                "-f",
                infile,  # input file
                # showpage (see https://bugs.ghostscript.com/show_bug.cgi?id=698272)
                "-c",
                "showpage",
            ],
            startupinfo = startupinfo if IS_WIN else None
        )
        with Image.open(outfile) as out_im:
            out_im.load()
            return out_im.im.copy()
    finally:
        try:
            os.unlink(outfile)
            if infile_temp:
                os.unlink(infile_temp)
        except OSError:
            pass


class EpsImageFile(ImageFile.ImageFile):
    """EPS File Parser for the Python Imaging Library"""

    format = "EPS"
    format_description = "Encapsulated Postscript"

    mode_map = {1: "L", 2: "LAB", 3: "RGB", 4: "CMYK"}

    def _open(self) -> None:
        (length, offset) = self._find_offset(self.fp)

        # go to offset - start of "%!PS"
        self.fp.seek(offset)

        self._mode = "RGB"

        # When reading header comments, the first comment is used.
        # When reading trailer comments, the last comment is used.
        bounding_box: list[int] | None = None
        imagedata_size: tuple[int, int] | None = None

        byte_arr = bytearray(255)
        bytes_mv = memoryview(byte_arr)
        bytes_read = 0
        reading_header_comments = True
        reading_trailer_comments = False
        trailer_reached = False

        def check_required_header_comments() -> None:
            """
            The EPS specification requires that some headers exist.
            This should be checked when the header comments formally end,
            when image data starts, or when the file ends, whichever comes first.
            """
            if "PS-Adobe" not in self.info:
                msg = 'EPS header missing "%!PS-Adobe" comment'
                raise SyntaxError(msg)
            if "BoundingBox" not in self.info:
                msg = 'EPS header missing "%%BoundingBox" comment'
                raise SyntaxError(msg)

        def read_comment(s: str) -> bool:
            nonlocal bounding_box, reading_trailer_comments
            try:
                m = split.match(s)
            except re.error as e:
                msg = "not an EPS file"
                raise SyntaxError(msg) from e

            if not m:
                return False

            k, v = m.group(1, 2)
            self.info[k] = v
            if k == "BoundingBox":
                if v == "(atend)":
                    reading_trailer_comments = True
                elif not bounding_box or (trailer_reached and reading_trailer_comments):
                    try:
                        # Note: The DSC spec says that BoundingBox
                        # fields should be integers, but some drivers
                        # put floating point values there anyway.
                        bounding_box = [int(float(i)) for i in v.split()]
                    except Exception:
                        pass
            return True

        while True:
            byte = self.fp.read(1)
            if byte == b"":
                # if we didn't read a byte we must be at the end of the file
                if bytes_read == 0:
                    if reading_header_comments:
                        check_required_header_comments()
                    break
            elif byte in b"\r\n":
                # if we read a line ending character, ignore it and parse what
                # we have already read. if we haven't read any other characters,
                # continue reading
                if bytes_read == 0:
                    continue
            else:
                # ASCII/hexadecimal lines in an EPS file must not exceed
                # 255 characters, not including line ending characters
                if bytes_read >= 255:
                    # only enforce this for lines starting with a "%",
                    # otherwise assume it's binary data
                    if byte_arr[0] == ord("%"):
                        msg = "not an EPS file"
                        raise SyntaxError(msg)
                    else:
                        if reading_header_comments:
                            check_required_header_comments()
                            reading_header_comments = False
                        # reset bytes_read so we can keep reading
                        # data until the end of the line
                        bytes_read = 0
                byte_arr[bytes_read] = byte[0]
                bytes_read += 1
                continue

            if reading_header_comments:
                # Load EPS header

                # if this line doesn't start with a "%",
                # or does start with "%%EndComments",
                # then we've reached the end of the header/comments
                if byte_arr[0] != ord("%") or bytes_mv[:13] == b"%%EndComments":
                    check_required_header_comments()
                    reading_header_comments = False
                    continue

                s = str(bytes_mv[:bytes_read], "latin-1")
                if not read_comment(s):
                    m = field.match(s)
                    if m:
                        k = m.group(1)
                        if k.startswith("PS-Adobe"):
                            self.info["PS-Adobe"] = k[9:]
                        else:
                            self.info[k] = ""
                    elif s[0] == "%":
                        # handle non-DSC PostScript comments that some
                        # tools mistakenly put in the Comments section
                        pass
                    else:
                        msg = "bad EPS header"
                        raise OSError(msg)
            elif bytes_mv[:11] == b"%ImageData:":
                # Check for an "ImageData" descriptor
                # https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/#50577413_pgfId-1035096

                # If we've already read an "ImageData" descriptor,
                # don't read another one.
                if imagedata_size:
                    bytes_read = 0
                    continue

                # Values:
                # columns
                # rows
                # bit depth (1 or 8)
                # mode (1: L, 2: LAB, 3: RGB, 4: CMYK)
                # number of padding channels
                # block size (number of bytes per row per channel)
                # binary/ascii (1: binary, 2: ascii)
                # data start identifier (the image data follows after a single line
                #   consisting only of this quoted value)
                image_data_values = byte_arr[11:bytes_read].split(None, 7)
                columns, rows, bit_depth, mode_id = (
                    int(value) for value in image_data_values[:4]
                )

                if bit_depth == 1:
                    self._mode = "1"
                elif bit_depth == 8:
                    try:
                        self._mode = self.mode_map[mode_id]
                    except ValueError:
                        break
                else:
                    break

                # Parse the columns and rows after checking the bit depth and mode
                # in case the bit depth and/or mode are invalid.
                imagedata_size = columns, rows
            elif bytes_mv[:5] == b"%%EOF":
                break
            elif trailer_reached and reading_trailer_comments:
                # Load EPS trailer
                s = str(bytes_mv[:bytes_read], "latin-1")
                read_comment(s)
            elif bytes_mv[:9] == b"%%Trailer":
                trailer_reached = True
            bytes_read = 0

        # A "BoundingBox" is always required,
        # even if an "ImageData" descriptor size exists.
        if not bounding_box:
            msg = "cannot determine EPS bounding box"
            raise OSError(msg)

        # An "ImageData" size takes precedence over the "BoundingBox".
        self._size = imagedata_size or (
            bounding_box[2] - bounding_box[0],
            bounding_box[3] - bounding_box[1],
        )

        self.tile = [
            ImageFile._Tile("eps", (0, 0) + self.size, offset, (length, bounding_box))
        ]

    def _find_offset(self, fp: IO[bytes]) -> tuple[int, int]:
        s = fp.read(4)

        if s == b"%!PS":
            # for HEAD without binary preview
            fp.seek(0, io.SEEK_END)
            length = fp.tell()
            offset = 0
        elif i32(s) == 0xC6D3D0C5:
            # FIX for: Some EPS file not handled correctly / issue #302
            # EPS can contain binary data
            # or start directly with latin coding
            # more info see:
            # https://web.archive.org/web/20160528181353/http://partners.adobe.com/public/developer/en/ps/5002.EPSF_Spec.pdf
            s = fp.read(8)
            offset = i32(s)
            length = i32(s, 4)
        else:
            msg = "not an EPS file"
            raise SyntaxError(msg)

        return length, offset

    def load(
        self, scale: int = 1, transparency: bool = False
    ) -> Image.core.PixelAccess | None:
        # Load EPS via Ghostscript
        if self.tile:
            self.im = Ghostscript(self.tile, self.size, self.fp, scale, transparency)
            self._mode = self.im.mode
            self._size = self.im.size
            self.tile = []
        return Image.Image.load(self)

    def load_seek(self, pos: int) -> None:
        # we can't incrementally load, so force ImageFile.parser to
        # use our custom load method by defining this method.
        pass


# --------------------------------------------------------------------

Image.register_open("PDF", _open_pdf, lambda prefix: prefix[:4] == b'%PDF')
Image.register_extensions("PDF", [".pdf", ".ai"])

Image.register_open("EPS", EpsImageFile, _accept_eps)
#Image.register_extensions("PDF", [".eps", ".ps"])

if __name__ == "__main__":
    img = Image.open("../_test_files/test.pdf")
    img.show()
