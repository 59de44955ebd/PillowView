"""
"PIL" is a very simple (dummy) image file format that stores Pillow"s
internally used image data - as returned by Image.tobytes() -
directly in the file, optionally compressed with DEFLATE compression.

It therefor supports any image mode (not rawmode) that Pillow supports.

It adds a minimal file header to the data, and in case of mode
"P" or "PA" also the palette colors and the index of a transparent
color in the palette, if there is one.

It can optionally also store EXIF data at the very end of the file.

The purpose of this file format is not usage in real world applications,
but to simplify testing features in Pillow based applications. Since
the format can load and save any image mode, it makes testing image
operations, filters, conversions etc. concerning supported modes a
litte easier. Pillow comes with an obscure file format called IM,
I guess mainly for this purpose, that also supports most image modes,
but not all.

Note that the "PIL" format is not affiliated with the PIL/Pillow dev
team in any way, I called it "PIL" because a) it is s based on Pillow"s
image modes and internal data layout, and b) because the file extension
*.pil was still available, i.e. not used by a common file format yet.

Just for fun I also created a Thumbnail Handler Shell Extension for
Windows that allows to see thumbnails of .pil image files directly in
the Windows Explorer. The Shell Extensions supports both uncompressed
and compressed image files and the following 15 modes:
CMYK, RGBA, RGB, LA, PA, L, P, P:4, P:2, P:1, 1, I, F, HSV, YCbCr

(Note: P:1, P:2 and P:4 are actually rawmodes, not modes. This image
plugin automatically loads and saves P or PA images with those rawmodes
if the image"s palette has at most 2 resp. 4 resp. 16 colors. The mode
string saved in the file is still just P resp. PA.)


File structure:
===============

                            (4 bytes per row)

|        P        |        L        |       \0        |  <compression>  |
|      <width> (unsigned short)     |     <height> (unsigned short)     |
|       <mode> (PIL Image.mode as 4 chars, right padded with \0)        |


Only if mode is "P" or "PA":
|  <palette size> (unsigned short)  |      <tr>       |   <tr index>    |
|                 <palette data> (3 bytes per color, RGB)               |
|                                ...                                    |


|                  <image data size> (unsigned long)                    |
|               <image data> (compressed or uncompressed)               |
|                                ...                                    |

Either:
|                               0000 (=EOF)                             |
Or:
|                    <EXIF data> (starting with "Exif")                 |
|                                ...                                    |


<compression>: \0 = uncompressed, \1 = DEFLATE (other compression schemes could be added)
<tr>: Transparency? \0 = no, \1 = yes
<tr index>: Index of transparent color in palette (if <tr> is \1)

"""

from __future__ import annotations
import struct
from enum import IntEnum
from typing import IO
import zlib
from PIL import Image, ImageFile, ImageOps


class PILFormatError(NotImplementedError):
    pass


class Compression(IntEnum):
    UNCOMPRESSED = 0
    DEFLATE = 1
    # Other compression schemes could be added in the future


def get_exif_data(filename):
    """
    Public utility function for extracting EXIF data from a PIL image
    file without loading it as image. Returns either raw exif data as
    bytes, which can be parsed with Image.Exif.load(), or None.
    Raises PILFormatError if PIL file is invalid/corrupted.
    """
    try:
        with open(filename, "rb") as fp:
            fp.seek(8)
            mode = fp.read(4).rstrip(b"\0").decode()
            if mode in ("P", "PA"):
                num_colors = struct.unpack("<H", fp.read(2))[0]
                fp.seek(2 + num_colors * 3, 1)
            data_size = struct.unpack("<L", fp.read(4))[0]
            fp.seek(data_size, 1)
            exif_data = fp.read()
        if exif_data.startswith(b"Exif"):
            return exif_data
    except:
        raise PILFormatError("Bad PIL file")

def _accept(prefix: bytes) -> bool:
    return prefix.startswith((b"PL\0\0", b"PL\0\1"))

def _open(fp, filename, ** kwargs):
    magic = fp.read(4)
    if not _accept(magic):
        raise PILFormatError("Bad PIL magic")

    compression = magic[3]
    if compression not in (Compression.UNCOMPRESSED, Compression.DEFLATE):
        raise PILFormatError("Bad PIL compression")

    w, h = struct.unpack("<2H", fp.read(4))

    mode = fp.read(4).rstrip(b"\0").decode()
    if mode == "YCC":
        # YCbCr is the only mode name that needs more than 4 letters.
        mode = "YCbCr"

    if mode in ("P", "PA"):
        num_colors, has_trans, trans_index = struct.unpack("<HBB", fp.read(4))
        palette = [c for c in fp.read(num_colors * 3)]
        data_size = struct.unpack("<L", fp.read(4))[0]
        bits = fp.read(data_size)
        if compression == Compression.DEFLATE:
            bits = zlib.decompress(bits)  # bufsize=...? Default is 16 KiB.

        if num_colors <= 2:
            im = Image.frombytes("P", (w, h), bits, "raw", "P;1")

        elif num_colors <= 4:
            im = Image.frombytes("P", (w, h), bits, "raw", "P;2")

        elif num_colors <= 16:
            im = Image.frombytes("P", (w, h), bits, "raw", "P;4")

        else:
            im = Image.frombytes(mode, (w, h), bits, "raw", mode)

        im.putpalette(palette)
        if has_trans:
            im.info["transparency"] = trans_index

    else:
        data_size = struct.unpack("<L", fp.read(4))[0]
        bits = fp.read(data_size)
        if compression == Compression.DEFLATE:
            bits = zlib.decompress(bits)
        im = Image.frombytes(mode, (w, h), bits, "raw", mode)

    im.format = "PIL"
    if fp.read(4) == b"Exif":
        im.info["exif"] = b"Exif" + fp.read()

    return im

def _save(im: Image.Image, fp: IO[bytes], filename: str | bytes):

    # Not sure, should we default to compressed or uncompressed?
    compression = im.encoderinfo.get("compression", Compression.DEFLATE)
    if compression == Compression.UNCOMPRESSED:
        magic = b"PL\0\0"
    elif compression == Compression.DEFLATE:
        magic = b"PL\0\1"
    else:
        raise ValueError("Unsupported PIL image compression")

    fp.write(magic)

    fp.write(struct.pack("<H", im.width))
    fp.write(struct.pack("<H", im.height))

    if im.mode == "YCbCr":
        # YCbCr is the only mode name that needs more than 4 letters.
        fp.write(b"YCC\0")
    else:
        fp.write(im.mode.ljust(4, "\0").encode())

    if im.mode in ("P", "PA"):
        num_colors = len(im.getpalette()) // 3
        fp.write(struct.pack("<H", num_colors))

        if "transparency" in im.info:
            fp.write(b"\1")
            fp.write(struct.pack("B", im.info["transparency"]))
        else:
            fp.write(b"\0\0")
        pal = im.getpalette()
        #fp.write(b"".join([c.c_ubyte(x) for x in pal]))
        fp.write(struct.pack(f"{len(pal)}B", *pal))

        # If a P/PA image has either (at most) 2, 4 or 16 colors in its palette,
        # we pack multiple pixels into each byte (which results in a smaller
        # file, but makes saving/loading a little slower).
        if num_colors <= 2:
            im = ImageOps.invert(im.convert("1"))
            bits = im.tobytes()
        elif num_colors <= 4:
            bits = im.tobytes()
            bits = struct.pack(f"{len(bits) // 4}B", *((bits[i] << 6 | bits[i + 1] << 4 | bits[i + 2] << 2 | bits[i + 3]) for i in range(0, len(bits), 4)))
        elif num_colors <= 16:
            bits = im.tobytes()
            bits = struct.pack(f"{len(bits) // 2}B", *((bits[i] << 4 | bits[i]) for i in range(0, len(bits), 2)))

        else:
            bits = im.tobytes()
    else:
        bits = im.tobytes()

    if compression == Compression.DEFLATE:
        bits = zlib.compress(bits)  # bufsize=...? Default is 16 KiB.

    fp.write(struct.pack("<L", len(bits)))
    fp.write(bits)

    if "exif" in im.info:
        fp.write(im.info["exif"])
    else:
        fp.write(b"\0\0\0\0")

    ImageFile._save(im, fp, [])

Image.register_open("PIL", _open, _accept)
Image.register_save("PIL", _save)
Image.register_extension("PIL", ".pil")

if __name__ == "__main__":
    img = Image.open("_test_files/test.pil")
    img.show()
