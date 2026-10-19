#!/usr/bin/env python3
"""pixelframe.py: a simulated LED pixel frame for the holiday display.

The real frame is 56 x 37 LEDs (6 ft x 4 ft, 30 LEDs/m strip: 33.3 mm, 1.31" apart).  This module lets us draw on a frame in Python
and save a picture of how the LEDs would look, before any hardware exists.  Pure Python, nothing to install.

    from pixelframe import Frame, ORANGE
    f = Frame()                     # 56 x 37, all off
    f.ellipse(28, 20, 18, 14, ORANGE)
    f.text("BOO!", 17, 2, WHITE)
    f.save_png("boo.png")           # what the LEDs would look like
    print(f.amps())                 # current the 5 V supply would have to deliver

Coordinates: x goes right from 0 to 55, y goes down from 0 to 36, like most computer screens.
Colors are (red, green, blue), each 0 to 255.
"""
import struct
import zlib

WIDTH, HEIGHT = 56, 37

OFF = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 60, 255)
YELLOW = (255, 210, 40)
AMBER = (255, 150, 0)
ORANGE = (255, 110, 0)
DARK_ORANGE = (170, 55, 0)
BROWN = (120, 70, 20)
PURPLE = (160, 0, 255)

# Text art: one character per pixel.  Kids can edit these files in any text editor.
PALETTE = {".": OFF, "O": ORANGE, "o": DARK_ORANGE, "D": (180, 55, 0), "d": (90, 25, 0), "Y": YELLOW, "y": AMBER, "G": GREEN, "B": BROWN,
           "W": WHITE, "R": RED, "U": BLUE, "P": PURPLE}

MA_PER_CHANNEL = 20      # a WS2812B LED draws about 20 mA per color channel at full brightness


class Frame:
    def __init__(self, width=WIDTH, height=HEIGHT):
        self.width, self.height = width, height
        self.pixels = [[OFF] * width for _ in range(height)]

    # --- pixels ---------------------------------------------------------------------------------
    def set(self, x, y, color):
        """Light one pixel.  Points outside the frame are quietly ignored."""
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = color

    def get(self, x, y):
        return self.pixels[y][x]

    def clear(self, color=OFF):
        for row in self.pixels:
            row[:] = [color] * self.width

    def copy(self):
        f = Frame(self.width, self.height)
        f.pixels = [row[:] for row in self.pixels]
        return f

    # --- shapes ---------------------------------------------------------------------------------
    def line(self, x0, y0, x1, y1, color):
        """Straight line (Bresenham's algorithm: steps one pixel at a time)."""
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def rect(self, x, y, w, h, color, fill=True):
        for j in range(h):
            for i in range(w):
                if fill or i in (0, w - 1) or j in (0, h - 1):
                    self.set(x + i, y + j, color)

    def ellipse(self, cx, cy, rx, ry, color, fill=True):
        """Ellipse centered at (cx, cy); a circle when rx == ry.  A pixel is in if its center is in."""
        for y in range(self.height):
            for x in range(self.width):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1 and (fill or d > (1 - 1.6 / min(rx, ry))):
                    self.set(x, y, color)

    def triangle(self, a, b, c, color):
        """Filled triangle with corners a, b, c, each (x, y)."""
        def side(p, q, r):
            return (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1])
        for y in range(self.height):
            for x in range(self.width):
                d = (side((x, y), a, b), side((x, y), b, c), side((x, y), c, a))
                if not (min(d) < 0 < max(d)):
                    self.set(x, y, color)

    # --- text -----------------------------------------------------------------------------------
    def text(self, s, x, y, color, spacing=1):
        """Write text with the 5 x 7 pixel font, top-left corner at (x, y).  Returns the width used."""
        x0 = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT["?"])
            for j, row in enumerate(glyph):
                for i, c in enumerate(row):
                    if c == "#":
                        self.set(x + i, y + j, color)
            x += len(glyph[0]) + spacing
        return x - x0 - spacing

    def text_width(self, s, spacing=1):
        return sum(len(FONT.get(ch, FONT["?"])[0]) + spacing for ch in s.upper()) - spacing

    def text_centered(self, s, y, color):
        return self.text(s, (self.width - self.text_width(s)) // 2, y, color)

    # --- text art files -------------------------------------------------------------------------
    def load_art(self, path, palette=PALETTE, x=0, y=0):
        """Draw a text-art file onto the frame; '.' and unknown characters leave pixels alone."""
        with open(path) as f:
            for j, line in enumerate(l.rstrip("\n") for l in f):
                for i, ch in enumerate(line):
                    if ch in palette and ch != ".":
                        self.set(x + i, y + j, palette[ch])

    def save_art(self, path, palette=PALETTE):
        """Save as text art; colors not in the palette are written as the nearest palette color."""
        inv = list(palette.items())

        def nearest(c):
            return min(inv, key=lambda kv: sum((a - b) ** 2 for a, b in zip(kv[1], c)))[0]
        with open(path, "w") as f:
            for row in self.pixels:
                f.write("".join(nearest(c) for c in row) + "\n")

    # --- power ----------------------------------------------------------------------------------
    def amps(self):
        """Current this picture draws from the 5 V supply, in amps (about 1 mA per LED when off)."""
        ma = sum(sum(c) / 255 * MA_PER_CHANNEL + 1 for row in self.pixels for c in row)
        return ma / 1000

    # --- pictures -------------------------------------------------------------------------------
    def save_png(self, path, cell=16, led=0.42, background=(12, 10, 14), unlit=(32, 30, 36)):
        """Save a picture of the frame: one round LED per pixel, on a dark background.

        cell: picture pixels per LED; led: LED radius as a fraction of the cell.  Unlit LEDs show faintly,
        like the real strip in daylight.  The edges of each dot are smoothed (anti-aliased)."""
        W, H = self.width * cell, self.height * cell
        r = led * cell
        # coverage of one LED dot, worked out once (4 x 4 samples per picture pixel)
        mask = []
        for py in range(cell):
            row = []
            for px in range(cell):
                inside = 0
                for sy in range(4):
                    for sx in range(4):
                        dx = px + (sx + 0.5) / 4 - cell / 2
                        dy = py + (sy + 0.5) / 4 - cell / 2
                        inside += dx * dx + dy * dy <= r * r
                row.append(inside / 16)
            mask.append(row)
        rows = []
        for y in range(self.height):
            for py in range(cell):
                line = bytearray([0])                      # PNG filter type 0 for this row
                for x in range(self.width):
                    c = self.pixels[y][x]
                    if c == OFF:
                        c = unlit
                    for px in range(cell):
                        k = mask[py][px]
                        line += bytes(int(b + (v - b) * k) for v, b in zip(c, background))
                rows.append(bytes(line))
        write_png(path, W, H, b"".join(rows))


def write_png(path, width, height, raw):
    """Minimal PNG writer: 8-bit RGB, rows already prefixed with their filter byte."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))


# 5 x 7 pixel font ("#" = lit).  Narrow characters are fine: each glyph sets its own width.
_F = """
A .###. #...# #...# ##### #...# #...# #...#
B ####. #...# #...# ####. #...# #...# ####.
C .###. #...# #.... #.... #.... #...# .###.
D ####. #...# #...# #...# #...# #...# ####.
E ##### #.... #.... ####. #.... #.... #####
F ##### #.... #.... ####. #.... #.... #....
G .###. #...# #.... #.### #...# #...# .####
H #...# #...# #...# ##### #...# #...# #...#
I ### .#. .#. .#. .#. .#. ###
J ..### ...#. ...#. ...#. #..#. #..#. .##..
K #...# #..#. #.#.. ##... #.#.. #..#. #...#
L #.... #.... #.... #.... #.... #.... #####
M #...# ##.## #.#.# #.#.# #...# #...# #...#
N #...# ##..# #.#.# #..## #...# #...# #...#
O .###. #...# #...# #...# #...# #...# .###.
P ####. #...# #...# ####. #.... #.... #....
Q .###. #...# #...# #...# #.#.# #..#. .##.#
R ####. #...# #...# ####. #.#.. #..#. #...#
S .#### #.... #.... .###. ....# ....# ####.
T ##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..
U #...# #...# #...# #...# #...# #...# .###.
V #...# #...# #...# #...# #...# .#.#. ..#..
W #...# #...# #...# #.#.# #.#.# #.#.# .#.#.
X #...# #...# .#.#. ..#.. .#.#. #...# #...#
Y #...# #...# .#.#. ..#.. ..#.. ..#.. ..#..
Z ##### ....# ...#. ..#.. .#... #.... #####
0 .###. #...# #..## #.#.# ##..# #...# .###.
1 .#. ##. .#. .#. .#. .#. ###
2 .###. #...# ....# ...#. ..#.. .#... #####
3 ####. ....# ....# .###. ....# ....# ####.
4 ...#. ..##. .#.#. #..#. ##### ...#. ...#.
5 ##### #.... ####. ....# ....# #...# .###.
6 .###. #.... #.... ####. #...# #...# .###.
7 ##### ....# ...#. ..#.. .#... .#... .#...
8 .###. #...# #...# .###. #...# #...# .###.
9 .###. #...# #...# .#### ....# ....# .###.
! # # # # # . #
? .###. #...# ....# ...#. ..#.. ..... ..#..
. . . . . . . #
, .. .. .. .. .. .# #.
: . # # . # # .
' # # . . . . .
- ..... ..... ..... ##### ..... ..... .....
+ ..... ..#.. ..#.. ##### ..#.. ..#.. .....
* ..... #.#.# .###. ##### .###. #.#.# .....
""".strip().splitlines()
FONT = {line[0]: line[2:].split() for line in _F}
FONT[" "] = ["..."] * 7


if __name__ == "__main__":
    # demo: the font and the palette
    f = Frame()
    f.text_centered("HAPPY", 2, ORANGE)
    f.text_centered("HALLOWEEN", 11, PURPLE)
    f.text_centered("OCT 31", 20, GREEN)
    for i, c in enumerate((RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, WHITE)):
        f.rect(4 + i * 7, 30, 5, 4, c)
    f.save_png("demo.png")
    print("demo.png: %.1f A at full brightness" % f.amps())
