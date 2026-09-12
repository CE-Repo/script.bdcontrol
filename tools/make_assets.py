#!/usr/bin/env python3
"""Generate the PNG assets shipped with script.bdcontrol.

Everything is drawn with the standard library only so the textures can be
rebuilt on any machine without extra dependencies:

    python3 tools/make_assets.py

Shapes are rendered with 4x supersampling to get smooth edges.
"""
import math
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MEDIA = os.path.join(ROOT, 'resources', 'skins', 'default', 'media')
RESOURCES = os.path.join(ROOT, 'resources')

SS = 4  # supersampling factor

ACCENT = (0, 145, 234)
ACCENT_DARK = (0, 96, 160)
PANEL = (18, 20, 24)
INK = (236, 240, 245)


def write_png(path, width, height, pixels):
    """Write RGBA pixels (list of rows, each a list of (r, g, b, a))."""
    raw = bytearray()
    for row in pixels:
        raw.append(0)  # filter type: none
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))

    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        return out + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', header)
           + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
           + chunk(b'IEND', b''))
    with open(path, 'wb') as handle:
        handle.write(png)
    print('wrote %s (%dx%d, %d bytes)' % (path, width, height, len(png)))


def blank(width, height):
    return [[(0, 0, 0, 0) for _ in range(width)] for _ in range(height)]


def blend(dst, color, coverage):
    """Alpha-composite `color` (r, g, b, a) over dst with extra coverage."""
    sr, sg, sb, sa = color
    sa = sa * coverage
    if sa <= 0:
        return dst
    dr, dg, db, da = dst
    sa /= 255.0
    da /= 255.0
    out_a = sa + da * (1 - sa)
    if out_a <= 0:
        return (0, 0, 0, 0)
    out_r = (sr * sa + dr * da * (1 - sa)) / out_a
    out_g = (sg * sa + dg * da * (1 - sa)) / out_a
    out_b = (sb * sa + db * da * (1 - sa)) / out_a
    return (int(round(out_r)), int(round(out_g)), int(round(out_b)),
            int(round(out_a * 255)))


def paint(pixels, width, height, color, inside):
    """Paint every pixel using a supersampled `inside(x, y) -> bool` test."""
    step = 1.0 / SS
    offset = step / 2.0
    samples = float(SS * SS)
    for py in range(height):
        row = pixels[py]
        for px in range(width):
            hits = 0
            for sy in range(SS):
                y = py + offset + sy * step
                for sx in range(SS):
                    x = px + offset + sx * step
                    if inside(x, y):
                        hits += 1
            if hits:
                row[px] = blend(row[px], color, hits / samples)


def rounded_rect_test(x0, y0, x1, y1, radius):
    def inside(x, y):
        cx = min(max(x, x0 + radius), x1 - radius)
        cy = min(max(y, y0 + radius), y1 - radius)
        if x < x0 or x > x1 or y < y0 or y > y1:
            return False
        dx = x - cx
        dy = y - cy
        if dx == 0 or dy == 0:
            return True
        return dx * dx + dy * dy <= radius * radius
    return inside


def ring_test(cx, cy, outer, inner):
    def inside(x, y):
        d = math.hypot(x - cx, y - cy)
        return inner <= d <= outer
    return inside


def triangle_test(points):
    (ax, ay), (bx, by), (cx, cy) = points

    def sign(px, py, qx, qy, rx, ry):
        return (px - rx) * (qy - ry) - (qx - rx) * (py - ry)

    def inside(x, y):
        d1 = sign(x, y, ax, ay, bx, by)
        d2 = sign(x, y, bx, by, cx, cy)
        d3 = sign(x, y, cx, cy, ax, ay)
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)
    return inside


def solid(path, width, height, color):
    pixels = [[color for _ in range(width)] for _ in range(height)]
    write_png(path, width, height, pixels)


def rounded(path, size, radius, color, border=None, border_width=0):
    pixels = blank(size, size)
    if border and border_width:
        paint(pixels, size, size, border,
              rounded_rect_test(0.0, 0.0, float(size), float(size), radius))
        paint(pixels, size, size, color,
              rounded_rect_test(float(border_width), float(border_width),
                                float(size - border_width),
                                float(size - border_width),
                                max(radius - border_width, 0.5)))
    else:
        paint(pixels, size, size, color,
              rounded_rect_test(0.0, 0.0, float(size), float(size), radius))
    write_png(path, size, size, pixels)


def make_icon(path, size=512):
    pixels = blank(size, size)
    paint(pixels, size, size, (12, 14, 18, 255),
          rounded_rect_test(0.0, 0.0, float(size), float(size), size * 0.18))
    paint(pixels, size, size, ACCENT_DARK + (255,),
          rounded_rect_test(size * 0.06, size * 0.06, size * 0.94, size * 0.94,
                            size * 0.14))
    paint(pixels, size, size, (16, 19, 24, 255),
          rounded_rect_test(size * 0.075, size * 0.075, size * 0.925,
                            size * 0.925, size * 0.125))
    centre = size / 2.0
    paint(pixels, size, size, ACCENT + (255,),
          ring_test(centre, centre, size * 0.36, size * 0.30))
    paint(pixels, size, size, ACCENT + (90,),
          ring_test(centre, centre, size * 0.29, size * 0.10))
    paint(pixels, size, size, (16, 19, 24, 255),
          ring_test(centre, centre, size * 0.085, 0.0))
    play = size * 0.17
    paint(pixels, size, size, INK + (255,),
          triangle_test(((centre - play * 0.55, centre - play),
                         (centre - play * 0.55, centre + play),
                         (centre + play * 0.95, centre))))
    write_png(path, size, size, pixels)


def main():
    os.makedirs(MEDIA, exist_ok=True)
    # Full screen dimmer behind the OSD.
    solid(os.path.join(MEDIA, 'bd-dim.png'), 8, 8, (0, 0, 0, 120))
    # 9-slice panel background (border="28" in the skin file).
    rounded(os.path.join(MEDIA, 'bd-panel.png'), 64, 22, PANEL + (240,),
            border=ACCENT + (60,), border_width=2)
    # Buttons (border="10").
    rounded(os.path.join(MEDIA, 'bd-button-nofocus.png'), 32, 8,
            (255, 255, 255, 26))
    rounded(os.path.join(MEDIA, 'bd-button-focus.png'), 32, 8, ACCENT + (255,))
    # Progress bar pieces.
    solid(os.path.join(MEDIA, 'bd-bar-back.png'), 8, 8, (255, 255, 255, 45))
    solid(os.path.join(MEDIA, 'bd-bar-mid.png'), 8, 8, ACCENT + (255,))
    make_icon(os.path.join(RESOURCES, 'icon.png'))


if __name__ == '__main__':
    main()
