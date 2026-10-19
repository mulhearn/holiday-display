#!/usr/bin/env python3
"""game.py: a still mock-up of a video game on the full frame (56 x 37).

    python3 game.py                     # saves game.png
    python3 viewer.py game --squares    # shows it full screen, pixels as squares
"""
from pixelframe import Frame, WIDTH, HEIGHT, WHITE, RED, GREEN, YELLOW, ORANGE, PURPLE, BROWN

SKIN = (255, 200, 150)
GROUND, PLATFORM, MOON = (110, 60, 20), (150, 80, 30), (230, 230, 200)

# The player, a witch: one character per pixel, '.' is see-through.
WITCH = """
..P..
.PPP.
PPPPP
.SSS.
.GGG.
SGGGS
.B.B.
"""
COLORS = {"P": PURPLE, "S": SKIN, "G": GREEN, "B": BROWN}


def sprite(f, art, x, y):
    for j, row in enumerate(art.strip().splitlines()):
        for i, ch in enumerate(row):
            if ch in COLORS:
                f.set(x + i, y + j, COLORS[ch])


def draw():
    """Return a new frame with the game scene on it."""
    f = Frame(WIDTH, HEIGHT)
    for y in range(HEIGHT):                                         # night sky, a little lighter near the ground
        f.rect(0, y, WIDTH, 1, (0, 0, 20 + y * 2 // 3))
    for x, y in ((5, 13), (12, 12), (20, 3), (30, 6), (40, 2), (50, 11), (26, 10)):
        f.set(x, y, WHITE)
    f.ellipse(46, 6, 3, 3, MOON)
    f.rect(0, 32, WIDTH, 5, GROUND)                                 # ground, with grass on top
    f.rect(0, 32, WIDTH, 1, GREEN)
    for x0, y0, w in ((7, 24, 10), (24, 19, 9), (39, 25, 11)):      # platforms
        f.rect(x0, y0, w, 2, PLATFORM)
        f.rect(x0, y0, w, 1, GREEN)
    for x in (26, 28, 30):                                          # coins
        f.set(x, 16, YELLOW)
    sprite(f, WITCH, 10, 17)
    f.rect(43, 22, 3, 3, ORANGE)                                    # a pumpkin enemy, with its stem
    f.set(44, 21, GREEN)
    f.text("420", 1, 1, WHITE)                                      # score and lives
    f.text("3", 51, 1, RED)
    return f


if __name__ == "__main__":
    f = draw()
    f.save_png("game.png")
    print("game.png: %.1f A at full brightness" % f.amps())
