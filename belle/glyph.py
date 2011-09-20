# -*- coding: utf-8 -*-
from __future__ import print_function

import re
import struct
import sys
import freetype
import Image, ImageDraw

import logging

log = logging.getLogger(__name__)

class FT2Bitmap(object):
    def __init__(self, bitmap):
        self.bitmap = bitmap

    def to_pil_image(self):
        data = ''.join([struct.pack('B', c) for c in self.bitmap.buffer])
        return Image.frombuffer("L", (self.bitmap.width, self.bitmap.rows), data, "raw", "L", 0, 1)

class GlyphWriter(object):
    def __init__(self, char):
        self.char = char
        
    def write(self, to, mapping=None):
        if mapping is None:
            mapping = NormalMapping
        glyph_ = self._composite(self._load_glyph(), self._load_glyph_outline())
        to.paste(glyph_, mapping(self.char.height).map(self.char, glyph_), glyph_)

    def _composite(self, fill_glyph, outline_glyph):
        size = (1, 1)
        if self.char.is_filled():
            fill_mask = self._write_glyph(self._load_glyph())
            size = map(max, size, fill_mask.size)
        if self.char.is_outlined():
            outline_mask = self._write_glyph(self._load_glyph_outline())
            size = map(max, size, outline_mask.size)

        out = Image.new("RGBA", size, (0,0,0,0))
        draw = ImageDraw.Draw(out)

        if self.char.is_outlined():
            draw.bitmap((0, 0), outline_mask, self.char.outline_color)
        if self.char.is_filled():
            draw.bitmap((self.char.outline_width, self.char.outline_width), fill_mask, self.char.color)
        if self.char.rotation:
            out = out.rotate(self.char.rotation, expand=1)
        return out
        
    def _load_glyph(self):
        face = freetype.Face(self.char.face)
        face.set_char_size(int(self.char.height * 64))
        face.load_char(self.char.char, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
        return face.glyph.get_glyph()

    def _load_glyph_outline(self):
        glyph = self._load_glyph()
        stroker = freetype.Stroker()
        stroker.set(int(self.char.outline_width * 64), freetype.FT_STROKER_LINECAP_ROUND, freetype.FT_STROKER_LINEJOIN_ROUND, 0 )
        glyph.stroke(stroker)
        return glyph

    def _write_glyph(self, glyph):
        blyph = glyph.to_bitmap(freetype.FT_RENDER_MODE_NORMAL, freetype.Vector(0,0))
        self.char.set_bitmap_offset((blyph.left, -blyph.top))
        bitmap = blyph.bitmap
        return FT2Bitmap(bitmap).to_pil_image()

class Character(object):
    def __init__(self, char=None, x=None, y=None, width=None, height=None, rotation=None, face=None, color=None, outline_color=None, outline_width=None, tate=False):
        self.char = char
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation
        self.face = face
        self.color = color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.tate = tate
        self._left = 0
        self._top = 0

        if not self.outline_width > 0.0:
            self.outline_width = None

    def set_bitmap_offset(self, offset):
        self._left, self._top = offset

    def get_bitmap_offset(self):
        return (self._left, self._top)

    def is_outlined(self):
        return self.outline_color is not None and self.outline_width is not None

    def is_filled(self):
        return self.color is not None

class NormalMapping(object):
    need_tate_format = u'ぁぃぅぇぉゃゅょっァィゥェォャュョッ、。「」…‥・ー−—〜'

    def __init__(self, glyph_size):
        self.glyph_size = glyph_size

    def map(self, char, glyph):
        x, y = char.get_bitmap_offset()
        x -= self.glyph_size / 2
        y -= self.glyph_size / 2
        y += self.glyph_size
        if char.tate and char.char in self.need_tate_format:
            return (char.x + y, char.y + x)
        else:
            return (char.x + x, char.y + y)

