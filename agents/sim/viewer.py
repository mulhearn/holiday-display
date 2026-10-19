#!/usr/bin/env python3
"""viewer.py: show a frame full screen, as round LEDs on a dark background (needs pygame).

    python3 viewer.py jack           # a Python module here with draw() -> Frame (jack.py); animated if it
                                     # also has frame(t) -> Frame, t in seconds
    python3 viewer.py jack.txt       # a text-art file
    python3 viewer.py jack --window  # in a window instead of full screen
    python3 viewer.py game --squares # pixels as squares (as behind a diffuser) instead of round LEDs

Esc or q quits.  The picture keeps the frame's shape (56 x 37), centered, as large as the screen allows.
"""
import importlib
import sys

import pygame

from pixelframe import Frame, OFF

BACKGROUND = (12, 10, 14)
UNLIT = (32, 30, 36)        # unlit LEDs show faintly, as in save_png
LED = 0.42                  # LED radius as a fraction of the spacing between LEDs
FPS = 15                    # frames per second of an animation


def load(name):
    """(animate, frame): a module's frame(t) to animate, or else one still frame, from a text-art file (name ends
    in .txt) or a module's draw()."""
    if name.endswith(".txt"):
        f = Frame()
        f.load_art(name)
        return None, f
    module = importlib.import_module(name.removesuffix(".py"))
    if hasattr(module, "frame"):
        return module.frame, None
    return None, module.draw()


def show(screen, frame, squares=False, previous=None):
    """Draw the frame on the screen: one filled circle (or square) per LED, straight to the screen (fast on a Pi).
    Given the previous frame, only the LEDs that changed are drawn again."""
    W, H = screen.get_size()
    cell = min(W / frame.width, H / frame.height)
    x0, y0 = (W - cell * frame.width) / 2, (H - cell * frame.height) / 2
    r = max(1, round(LED * cell))
    if previous is None:
        screen.fill(BACKGROUND)
    for y, row in enumerate(frame.pixels):
        before = previous.pixels[y] if previous else None
        for x, c in enumerate(row):
            if before and before[x] == c:
                continue
            center = (round(x0 + (x + 0.5) * cell), round(y0 + (y + 0.5) * cell))
            if squares:
                pygame.draw.rect(screen, UNLIT if c == OFF else c, (center[0] - r, center[1] - r, 2 * r, 2 * r))
            else:
                pygame.draw.circle(screen, UNLIT if c == OFF else c, center, r)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    animate, frame = load(args[0])
    squares = "--squares" in argv
    pygame.init()
    if "--window" in argv:
        first = frame or animate(0)
        cell = max(4, 1000 // first.width)              # about 1000 pixels wide
        screen = pygame.display.set_mode((first.width * cell, first.height * cell))
    else:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    pygame.display.set_caption("holiday display: " + args[0])
    clock = pygame.time.Clock()
    start = pygame.time.get_ticks()
    last = None                 # the frame on the screen now
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q)):
                pygame.quit()
                return
            if event.type == pygame.VIDEOEXPOSE:
                last = None     # the screen was lost: draw everything again
        f = animate((pygame.time.get_ticks() - start) / 1000) if animate else frame
        if f is not last:       # a still picture is drawn once; then the loop only watches for keys
            show(screen, f, squares, last)
            pygame.display.flip()
            last = f
        clock.tick(FPS)


if __name__ == "__main__":
    main(sys.argv[1:])
