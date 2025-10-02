from __future__ import annotations

import struct
from PIL import Image, ImageFile, ImageOps
from PIL._binary import i16le as i16
from PIL._binary import i32le as i32

# --------------------------------------------------------------------

def _accept(prefix: bytes) -> bool:
    return prefix.startswith(b"\0\0\2\0")

def _open(fp, filename, ** kwargs):
    offset = fp.tell()
    # check magic
    s = fp.read(6)
    if not _accept(s):
        raise SyntaxError("not a CUR file")

    # pick the largest cursor in the file
    m = b""
    for i in range(i16(s, 4)):
        s = fp.read(16)
        if not m or (s[0] > m[0] and s[1] > m[1]):
            m = s
            xy = i16(s, 4), i16(s, 6)
            size = s[0], s[1]

    if not m:
        raise TypeError("No cursors were found")

    fp.seek(i32(m, 12) + offset + 48)

    data_size = ((size[0] * size[1] + 31) >> 3) & (~3)
    im = Image.frombytes('1', size, fp.read(data_size), 'raw', '1', 0, -1)
    im.info['ANDbitmap'] = Image.frombytes('1', size, fp.read(data_size), 'raw', '1;I', 0, -1)
    im.info['Hotspot'] = xy

    return im

#Reserved 	2 byte 	=0
#Type 	2 byte 	=2
#Count 	2 byte 	Number of Cursors in this file=1

#Width 	1 byte 	Cursor Width (most commonly =32)
#Height 	1 byte 	Cursor Height (most commonly =32)
#ColorCount 	1 byte 	=0 !
#Reserved 	1 byte 	=0
#XHotspot 	2 byte 	Hotspot's X-Position
#YHotspot 	2 byte 	Hotspot's Y-Position

#SizeInBytes 	4 byte 	Size of (InfoHeader + ANDBitmap + XORBitmap)
#FileOffset 	4 byte 	FilePos, where InfoHeader starts

#InfoHeader 	40 byte 	Variant of BMP InfoHeader
#  	Size 	4 bytes 	Size of InfoHeader structure = 40
#  	Width 	4 bytes 	Cursor Width
#  	Height 	4 bytes 	Cursor Height (added height of XORbitmap and ANDbitmap)
#  	Planes 	2 bytes 	number of planes = 1
#  	BitCount 	2 bytes 	bits per pixel = 1
#  	Compression 	4 bytes 	Type of Compression = 0
#  	ImageSize 	4 bytes 	Size of Image in Bytes = 0 (uncompressed)
#  	XpixelsPerM 	4 bytes 	unused = 0
#  	YpixelsPerM 	4 bytes 	unused = 0
#  	ColorsUsed 	4 bytes 	unused = 0
#  	ColorsImportant 	4 bytes 	unused = 0

#Colors 	8 bytes 	since BitsPerPixel = 1 this will always be 2 entries
#Color 0 Red 	1 byte 	Background color red component =0
#Color 0 Green 	1 byte 	Background color green component =0
#Color 0 Blue 	1 byte 	Background color blue component =0
#reserved 	1 byte 	=0

#Color 1 Red 	1 byte 	Foreground color red component =255
#Color 1 Green 	1 byte 	Foreground color green component =255
#Color 1 Blue 	1 byte 	Foreground color blue component =255
#reserved 	1 byte 	=0

#XORbitmap
#ANDbitmap

#def _save(im: Image.Image, fp: IO[bytes], filename: str | bytes, hotspot: tuple[int, int] = (16, 16)):
#    data_size = ((im.width * im.height + 31) >> 3) & (~3)
#
#    fp.write(b"\0\0\2\0\1\0")
#    fp.write(struct.pack("2B", *im.size))
#    fp.write(b"\0\0")
#    fp.write(struct.pack("<2H", *hotspot))  #*im.info['Hotspot']))
#    fp.write(struct.pack("<L", 48 + 2 * data_size))
#    fp.write(struct.pack("<L", fp.tell() + 4))
#
#    # InfoHeader
#    fp.write(struct.pack("<L", 40))
#    fp.write(struct.pack("<2L", im.width, im.height * 2))
#    fp.write(struct.pack("<2H", 1, 1))
#    fp.write(struct.pack("<6L", 0, 0, 0, 0, 0, 0))
#
#    fp.write(b"\0\0\0\0\xFF\xFF\xFF\0")
#
#    fp.write(im.convert('1').transpose(method=Image.Transpose.FLIP_TOP_BOTTOM).tobytes())
#    fp.write(ImageOps.invert(im.getchannel('A').transpose(method=Image.Transpose.FLIP_TOP_BOTTOM).convert('1')).tobytes())
#
#    ImageFile._save(im, fp, [])

# --------------------------------------------------------------------

Image.register_open("CUR", _open, _accept)
#Image.register_save("CUR", _save)
Image.register_extension("CUR", ".cur")
