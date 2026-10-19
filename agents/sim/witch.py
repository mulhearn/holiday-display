#!/usr/bin/env python3
"""witch.py: a witch flies across the full moon (animated).

    python3 witch.py             # saves witch.png, a still as she crosses the moon
    python3 viewer.py witch      # shows it full screen, animated

The witch is a silhouette: dark against the lit moon.  In the dark sky you only see the stars she hides as she
passes.  At 56 x 37 a caricature reads better than true proportions: a tall hat, a long hooked nose.
"""
import math
import random

from pixelframe import Frame, WIDTH, HEIGHT

# The witch on her broom, facing right: '#' is silhouette, '.' see-through.
SPRITE = """
..........#.................
...........#................
...........##...............
...........##...............
..........####..............
..........####..............
..........#####.............
.........######.............
......#############.........
.........#######............
.........###########........
.........#######...#........
..........#######...........
............###.............
...........#####............
...........#####............
.######....#####............
########..#######...........
############################
########..#.####...#........
.######........####.........
"""

SKY_TOP, SKY_BOTTOM = (0, 0, 14), (8, 10, 45)
STAR = (200, 200, 230)
MOON = (245, 235, 175)
SILHOUETTE = (3, 2, 6)              # almost off: on the LEDs it reads as black
GROUND = (4, 4, 8)

MOON_X, MOON_Y, MOON_R = 30, 16.5, 14.2
FLIGHT = 12.0                       # seconds to cross the frame, then she comes round again
START_Y, END_Y = 9, 2               # her top row at the left and right edges: a slow, straight climb

ART = SPRITE.strip().splitlines()
SW, SH = len(ART[0]), len(ART)


def in_moon(x, y, margin=0):
    return (x + 0.5 - MOON_X) ** 2 + (y + 0.5 - MOON_Y) ** 2 <= (MOON_R + margin) ** 2


_scenery = None


def scenery():
    """Sky, stars, moon and a dark skyline: what never changes, drawn once."""
    global _scenery
    if _scenery is not None:
        return _scenery
    f = Frame()
    for y in range(HEIGHT):
        k = y / (HEIGHT - 1)
        f.rect(0, y, WIDTH, 1, tuple(round(a + (b - a) * k) for a, b in zip(SKY_TOP, SKY_BOTTOM)))
    rng = random.Random(7)
    for _ in range(70):                                     # stars at four brightnesses, clear of the moon
        x, y = rng.randrange(WIDTH), rng.randrange(31)
        if not in_moon(x, y, margin=1.5):
            b = rng.choice((0.35, 0.55, 0.8, 1.0))
            f.set(x, y, tuple(round(v * b) for v in STAR))
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if in_moon(x, y):
                f.set(x, y, MOON)
    for x in range(WIDTH):                                  # rooftops and trees along the bottom
        h = 3 + round(1.5 * math.sin(x / 2.5) + math.sin(x / 1.2 + 1))
        if 10 <= x < 15:
            h = 6 if x != 12 else 8                         # a house with a chimney
        f.rect(x, HEIGHT - h, 1, h, GROUND)
    _scenery = f
    return f


def frame(t):
    """The scene at time t, in seconds."""
    f = scenery().copy()
    p = (t % FLIGHT) / FLIGHT                               # 0 to 1 across the frame
    x0 = round(-SW + p * (WIDTH + SW))                      # from just off the left edge to just off the right
    y0 = round(START_Y + p * (END_Y - START_Y))
    for j, row in enumerate(ART):
        for i, ch in enumerate(row):
            if ch == "#":
                f.set(x0 + i, y0 + j, SILHOUETTE)
    return f


def draw():
    """A still: the witch in front of the moon."""
    return frame(FLIGHT * (MOON_X - SW / 2 + SW) / (WIDTH + SW))


if __name__ == "__main__":
    f = draw()
    f.save_png("witch.png")
    print("witch.png: %.1f A at full brightness" % f.amps())
