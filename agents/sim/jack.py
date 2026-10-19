#!/usr/bin/env python3
"""jack.py: draw the jack-o'-lantern with pixelframe, save jack.png (LED view) and jack.txt (text art).

    python3 jack.py              # saves jack.png and jack.txt
    python3 viewer.py jack       # shows it full screen, animated: the candle flickers and it winks

Every pixel is colored by asking which shape its center falls in (frame 56 x 37).
"""
import math
import random

from pixelframe import Frame, YELLOW, AMBER, GREEN, BROWN

BODY = (180, 55, 0)       # a deep, dim orange: the face glows brighter than the skin
RIB = (90, 25, 0)

cx, cy, rx, ry = 28, 21.25, 19.5, 14.5               # pumpkin center and half-widths, in pixels


def in_pumpkin(x, y):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def in_triangle(p, a, b, c):
    def side(p, q, r):
        return (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1])
    d = (side(p, a, b), side(p, b, c), side(p, c, a))
    return not (min(d) < 0 < max(d))


EYES_NOSE = (((13, 20.25), (24, 20.25), (18.5, 12.75)),     # triangles: left eye, right eye, nose
             ((32, 20.25), (43, 20.25), (37.5, 12.75)),
             ((25, 24.75), (31, 24.75), (28, 21.25)))


def color(X, Y):
    """The color at point (X, Y) of the picture, in pixels; None where nothing is drawn."""
    if 26.5 <= X < 30.5 and 3.75 <= Y < 8.75 and not (Y < 4.75 and (X < 27.5 or X >= 29.5)):
        return BROWN                                                    # stem
    if ((X - 33) / 2.6) ** 2 + ((Y - 6.05) / 1.3) ** 2 <= 1 or (35 <= X < 36.25 and 6.75 <= Y < 7.75):
        return GREEN                                                    # leaf
    if not in_pumpkin(X, Y):
        return None
    if not all(in_pumpkin(X + dx, Y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
        return RIB                                                      # outline
    if any(in_triangle((X, Y), *t) for t in EYES_NOSE):
        return YELLOW
    u = ((X - 28) / 14.5) ** 2                                          # mouth: a grin between two curves
    top, bottom = 26.25 - 2.5 * u, 32.25 - 4.5 * u
    if 13.5 <= X < 43.5 and top <= Y <= bottom:
        upper_tooth = (19 <= X <= 22.5 or 33.5 <= X <= 37) and Y < top + 2.2
        lower_tooth = 26.5 <= X <= 29.5 and Y > bottom - 2.2
        if not (upper_tooth or lower_tooth):
            return YELLOW if Y < (top + bottom) / 2 + 0.5 else AMBER
    for k in (-13.5, -6.5, 6.5, 13.5):                                  # ribs, at the top and bottom
        curve = cx + k * (1 - ((Y - cy) / ry) ** 2) ** 0.5
        if 9 < abs(Y - cy) < ry - 1.5 and abs(X - curve) < 0.55:
            return RIB
    return BODY


def draw():
    """Return a new frame with the jack-o'-lantern on it."""
    f = Frame()
    for y in range(f.height):
        for x in range(f.width):
            c = color(x + 0.5, y + 0.5)                                 # the center of pixel (x, y)
            if c:
                f.set(x, y, c)
    return f


# --- animation: the viewer calls frame(t), t in seconds -----------------------------------------
WINK_EVERY, WINK_LENGTH = 8.0, 0.5               # seconds
_still, _face = None, None


def candle(t):
    """Brightness of the candle at time t, between about 0.65 and 1: a slow waver plus a quick random jitter."""
    jitter = random.Random(int(t * 12)).random()       # a new random value 12 times a second
    return 0.84 + 0.1 * math.sin(2.1 * t) * math.sin(5.3 * t) + 0.12 * (jitter - 0.5)


def frame(t):
    """The jack-o'-lantern at time t: the face (lit by the candle) flickers, and the left eye winks now and then."""
    global _still, _face
    if _still is None:
        _still = draw()                              # draw the picture once; each frame only changes the face
        _face = [(x, y, c) for y, row in enumerate(_still.pixels) for x, c in enumerate(row) if c in (YELLOW, AMBER)]
    f = _still.copy()
    k = candle(t)
    winking = t % WINK_EVERY > WINK_EVERY - WINK_LENGTH     # at the end of each period, not at start-up
    for x, y, c in _face:
        if winking and x < 25 and y < 19:            # left eye (rows 13-19) shut, leaving a slit on row 19
            f.set(x, y, BODY)
        else:
            f.set(x, y, tuple(round(v * k) for v in c))
    return f


if __name__ == "__main__":
    f = draw()
    f.save_png("jack.png")
    f.save_art("jack.txt")
    print("jack.png, jack.txt: %.1f A at full brightness" % f.amps())
