"""Draws every emote texture.

Style: HSR-sticker-like speech bubbles with exaggerated kaomoji faces. Thick slightly wobbly ink,
clean white bubble with a soft shade, flat colour fills (tears, blush, hearts) with a little shine.

Face parts are drawn in the bubble's own frame (128x112, same quad as the bubble), so every part
sits in place and can be animated around its own pivot. Several parts have flipbook frames
(<name>_1, _2...) for flowing tears, wobbling mouths and the like.

Output (mod resources, textures/):
  emote/bubble.png              bubble (tinted pastel per emote)
  emote/f_<part>[_n].png        face parts in bubble frame
  emote/p_<name>.png (+_glow)   white particles, tinted per emitter
  emote/s_<name>.png            small stand-alone signs (!, ?, anger mark)
  fx/<name>.png                 additive white fx (sparkle, mote, ring)
"""
import math
import os
import sys

import numpy as np

from sdf import (Canvas, arc_pts, bezier, box, circle, ellipse, gaussian, heart, hexc, inter, mix, polygon,
                 polyline, segment, smooth, star, sub, union)

ROOT = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(ROOT, "..", "mod", "src", "main", "resources", "assets", "rubycon_emotes", "textures")

FRAME = (128, 112)                       # bubble frame in px; units: x in [-1.143, 1.143], y in [-1, 1]
INK = hexc("#2a2236")
WHITE = hexc("#ffffff")
LW = 0.062                               # ink half-width
EYE_L, EYE_R = (-0.36, 0.26), (0.44, 0.26)
MOUTH = (0.04, -0.3)
CHEEK_L, CHEEK_R = (-0.62, -0.1), (0.72, -0.1)

TEAR = ("#8fd3ff", "#d6f0ff", "#3b8fe0")
PINK = ("#ff8fb0", "#ffc7d6", "#e2557f")
RED = ("#ff5a64", "#ff9a9a", "#b8202e")
GOLD = ("#ffd34d", "#fff0a8", "#d99a12")
TONGUE = ("#ff8f9a", "#ffc0c6", "#d8566a")
MOUTH_IN = ("#7a2a3c", "#a8475a", "#4a1424")


# ============================================================ helpers
def wob(pts, amp=0.012, seed=1):
    """Hand-drawn wobble: tiny smooth noise across the stroke."""
    out = []
    for i, (x, y) in enumerate(pts):
        k = i / max(1, len(pts) - 1)
        out.append((x + amp * math.sin(k * 13.1 + seed * 2.3), y + amp * math.cos(k * 11.7 + seed * 1.7)))
    return out


def ink(c, d, w=LW, a=1.0):
    """Stroke the zero-set of d (a centre-line distance) with ink."""
    aa = c.px * 1.2
    c.over(INK, smooth(w + aa, w - aa, d) * a)


def line(c, pts, w=LW, seed=1, a=1.0, taper=False):
    pts = wob(pts, seed=seed)
    d = polyline(c, pts, w * (0.55 if taper else 1), w) if taper else polyline(c, pts, w)
    aa = c.px * 1.2
    c.over(INK, smooth(aa, -aa, d) * a)


def fill(c, d, pal, outline=LW, shine=True):
    """Ink-outlined flat fill with a soft top-light and a small highlight."""
    base, light, dark = (hexc(p) for p in pal)
    aa = c.px * 1.2
    if outline:
        c.over(INK, smooth(outline * 1.4 + aa, outline * 1.4 - aa, d))
    m = smooth(aa, -aa, d)
    depth = np.clip(-d / 0.12, 0, 1)
    col = mix(dark, base, smooth(0.0, 0.6, depth))
    col = mix(col, light, smooth(0.2, 1.0, depth) * smooth(-0.2, 0.9, c.y - c.y.mean()) * 0.6)
    c.over(col, m)
    if shine:
        k = max(1, int(0.05 / c.px))
        dd = np.roll(np.roll(d, k, axis=0), -k, axis=1)
        c.over(WHITE, smooth(aa, -aa, d + 0.035) * smooth(-aa, aa, dd + 0.0) * 0.75)
    return m


def flat(c, d, rgb, a=1.0):
    aa = c.px * 1.2
    c.over(hexc(rgb) if isinstance(rgb, str) else rgb, smooth(aa, -aa, d) * a)


def drop_sdf(c, cx, cy, r, tip=2.0):
    d1 = circle(c, cx, cy, r)
    tri = polygon(c, [(cx - r * 0.86, cy + r * 0.5), (cx, cy + r * tip), (cx + r * 0.86, cy + r * 0.5)])
    k = r * 0.3
    h = np.clip(0.5 + 0.5 * (tri - d1) / k, 0, 1)
    return tri * (1 - h) + d1 * h - k * h * (1 - h)


def at(p, dx=0.0, dy=0.0):
    return p[0] + dx, p[1] + dy


# ============================================================ bubble
def bubble(c):
    body = ellipse(c, 0.06, 0.06, 1.0, 0.8)
    tail = polygon(c, [(-0.62, -0.42), (-1.08, -0.94), (-0.22, -0.62)])
    k = 0.08
    h = np.clip(0.5 + 0.5 * (tail - body) / k, 0, 1)
    d = tail * (1 - h) + body * h - k * h * (1 - h)
    aa = c.px * 1.2
    # soft contact shadow below, then ink, then white body with a faint lower shade and a gloss arc
    sh = gaussian(np.roll(smooth(aa, -aa, d), int(0.06 / c.px), axis=0), 0.05 / c.px)
    c.over(hexc("#1a1428"), sh * 0.35)
    c.over(INK, smooth(LW * 1.5 + aa, LW * 1.5 - aa, d))
    m = smooth(aa, -aa, d)
    shade = smooth(0.25, -0.75, c.y) * smooth(-0.02, -0.2, d)
    col = mix(WHITE, hexc("#dcd8e6"), shade * 0.55)
    c.over(col, m)
    gloss = polyline(c, arc_pts(0.06, 0.06, 0.82, math.radians(105), math.radians(150), 16), 0.035)
    c.over(WHITE, smooth(aa, -aa, gloss) * 0.9)
    c.over(hexc("#c9c3d8"), smooth(aa, -aa, polyline(c, arc_pts(0.06, 0.06, 0.86, math.radians(-20), math.radians(-70), 16), 0.02)) * 0.6)


# ============================================================ eyes
PARTS = {}


def part(name, frames=1):
    def deco(fn):
        PARTS[name] = (fn, frames)
        return fn
    return deco


def both(fn):
    return lambda c, f=0: [fn(c, EYE_L, -1, f), fn(c, EYE_R, 1, f)]


@part("e_tt")
def _(c, f=0):
    for (x, y), s in ((EYE_L, -1), (EYE_R, 1)):
        line(c, [(x - 0.22, y + 0.1 + 0.02 * s), (x + 0.22, y + 0.1 - 0.02 * s)], LW * 1.15, seed=3 + s)
        line(c, [(x + 0.01, y + 0.1), (x - 0.01, y - 0.2)], LW * 1.15, seed=5 + s)


@part("e_xx")
def _(c, f=0):
    for (x, y), s in ((EYE_L, 1), (EYE_R, -1)):
        line(c, [(x - 0.17 * s, y + 0.14), (x + 0.15 * s, y), (x - 0.17 * s, y - 0.14)], LW * 1.15, seed=7 + s)


@part("e_happy")
def _(c, f=0):
    for (x, y), s in ((EYE_L, 1), (EYE_R, -1)):
        line(c, arc_pts(x, y - 0.12, 0.19, math.radians(20), math.radians(160), 18), LW * 1.15, seed=9 + s)


@part("e_heart")
def _(c, f=0):
    for (x, y) in (EYE_L, EYE_R):
        fill(c, heart(c, x, y - 0.02, 0.52), RED, outline=LW * 0.9)


@part("e_dot")
def _(c, f=0):
    for (x, y) in (EYE_L, EYE_R):
        flat(c, ellipse(c, x, y, 0.075, 0.1), INK)


@part("e_big")
def _(c, f=0):
    for (x, y), s in ((EYE_L, -1), (EYE_R, 1)):
        d = ellipse(c, x, y, 0.24, 0.27)
        aa = c.px * 1.2
        c.over(INK, smooth(LW + aa, LW - aa, d))
        flat(c, d, WHITE)
        flat(c, circle(c, x + 0.02 * s, y - 0.03, 0.055), INK)


@part("e_ring")
def _(c, f=0):
    for (x, y), _s in ((EYE_L, -1), (EYE_R, 1)):
        ink(c, np.abs(ellipse(c, x, y, 0.17, 0.2)), LW * 1.05)
        flat(c, circle(c, x, y, 0.05), INK)


@part("e_flat")
def _(c, f=0):
    for (x, y), s in ((EYE_L, -1), (EYE_R, 1)):
        line(c, [(x - 0.2, y), (x + 0.2, y + 0.005)], LW * 1.15, seed=11 + s)


@part("e_half")
def _(c, f=0):
    """Smug half-lidded: lid line with the pupil peeking under it."""
    for (x, y), s in ((EYE_L, -1), (EYE_R, 1)):
        line(c, [(x - 0.21, y + 0.02), (x + 0.21, y + 0.06)], LW * 1.15, seed=13 + s)
        flat(c, inter(ellipse(c, x + 0.07, y - 0.04, 0.1, 0.1), c.y - (y + 0.02)), INK)


@part("e_angry")
def _(c, f=0):
    for (x, y), s in ((EYE_L, 1), (EYE_R, -1)):
        line(c, [(x - 0.22 * s, y + 0.22), (x + 0.16 * s, y + 0.06)], LW * 1.25, seed=15 + s)
        flat(c, ellipse(c, x + 0.02 * s, y - 0.08, 0.08, 0.1), INK)


@part("e_worried")
def _(c, f=0):
    for (x, y), s in ((EYE_L, 1), (EYE_R, -1)):
        line(c, [(x - 0.2 * s, y + 0.06), (x + 0.14 * s, y + 0.22)], LW * 1.0, seed=17 + s)
        flat(c, ellipse(c, x, y - 0.08, 0.075, 0.1), INK)


@part("e_star")
def _(c, f=0):
    for (x, y) in (EYE_L, EYE_R):
        fill(c, star(c, x, y, 5, 0.25, 0.11) - 0.02, GOLD, outline=LW * 0.85)


@part("e_spiral_l")
def _(c, f=0):
    spiral(c, EYE_L)


@part("e_spiral_r")
def _(c, f=0):
    spiral(c, EYE_R)


def spiral(c, p):
    pts = []
    for i in range(80):
        t = i / 79
        a = t * math.pi * 2 * 1.75
        r = 0.03 + 0.21 * t
        pts.append((p[0] + math.cos(a) * r, p[1] + math.sin(a) * r))
    d = polyline(c, pts, LW * 0.62)
    aa = c.px * 1.2
    c.over(INK, smooth(aa, -aa, d))


@part("e_u")
def _(c, f=0):
    for (x, y), s in ((EYE_L, -1), (EYE_R, 1)):
        line(c, arc_pts(x, y + 0.1, 0.17, math.radians(200), math.radians(340), 18), LW * 1.15, seed=19 + s)


@part("e_wink")
def _(c, f=0):
    x, y = EYE_L
    line(c, arc_pts(x, y - 0.12, 0.19, math.radians(20), math.radians(160), 18), LW * 1.15, seed=21)
    x, y = EYE_R
    flat(c, ellipse(c, x, y, 0.09, 0.13), INK)
    flat(c, circle(c, x - 0.03, y + 0.05, 0.03), WHITE)


@part("e_dead")
def _(c, f=0):
    for (x, y), s in ((EYE_L, -1), (EYE_R, 1)):
        line(c, [(x - 0.15, y + 0.15), (x + 0.15, y - 0.15)], LW * 1.1, seed=23 + s)
        line(c, [(x - 0.15, y - 0.15), (x + 0.15, y + 0.15)], LW * 1.1, seed=25 + s)


@part("e_glare")
def _(c, f=0):
    """ಠ_ಠ: thick flat brow over a circled pupil."""
    for (x, y), s in ((EYE_L, -1), (EYE_R, 1)):
        line(c, [(x - 0.22, y + 0.2), (x + 0.22, y + 0.2)], LW * 1.3, seed=27 + s)
        ink(c, np.abs(circle(c, x, y - 0.06, 0.13)), LW * 0.85)
        flat(c, circle(c, x, y - 0.08, 0.045), INK)


@part("e_up")
def _(c, f=0):
    for (x, y), _s in ((EYE_L, -1), (EYE_R, 1)):
        ink(c, np.abs(ellipse(c, x, y, 0.15, 0.17)), LW * 0.85)
        flat(c, circle(c, x + 0.05, y + 0.07, 0.06), INK)


@part("e_tsu")
def _(c, f=0):
    for (x, y), s in ((EYE_L, -1), (EYE_R, 1)):
        x = x * 0.7 + 0.05
        line(c, [(x - 0.06, y + 0.12), (x + 0.08, y - 0.02)], LW * 1.15, seed=29 + s)


@part("e_fierce")
def _(c, f=0):
    """Determined: sharp brows and big shiny eyes."""
    for (x, y), s in ((EYE_L, 1), (EYE_R, -1)):
        line(c, [(x - 0.22 * s, y + 0.26), (x + 0.12 * s, y + 0.16)], LW * 1.2, seed=31 + s)
        flat(c, ellipse(c, x, y - 0.05, 0.11, 0.14), INK)
        flat(c, circle(c, x - 0.035, y, 0.04), WHITE)
        flat(c, circle(c, x + 0.03, y - 0.1, 0.018), WHITE)


@part("e_cry_shut")
def _(c, f=0):
    """Squeezed-shut crying eyes (><-ish arcs pressed down)."""
    for (x, y), s in ((EYE_L, 1), (EYE_R, -1)):
        line(c, arc_pts(x, y + 0.06, 0.18, math.radians(200), math.radians(340), 18), LW * 1.2, seed=33 + s)
        line(c, [(x - 0.2 * s, y + 0.2), (x + 0.1 * s, y + 0.12)], LW * 0.9, seed=35 + s)


# ============================================================ mouths
@part("m_wobble", frames=3)
def _(c, f=0):
    """Sobbing mouth from the sketch: wide open, wavy upper lip, trembling (3 frames)."""
    x, y = MOUTH
    ph = f * 2.1
    top = [(x - 0.34 + 0.68 * i / 24, y + 0.06 + 0.045 * math.sin(i / 24 * math.pi * 5 + ph)) for i in range(25)]
    bot = bezier((x + 0.34, y + 0.06), (x + 0.1, y - 0.42 - 0.02 * f), (x - 0.34, y + 0.06), 20)
    d = polygon(c, top + bot[1:-1])
    fill(c, d, MOUTH_IN, outline=LW * 0.8, shine=False)
    flat(c, inter(d + 0.02, ellipse(c, x, y - 0.26, 0.16, 0.08)), hexc(TONGUE[0]))


@part("m_open")
def _(c, f=0):
    x, y = MOUTH
    d = inter(ellipse(c, x, y + 0.02, 0.32, 0.3), c.y - (y + 0.06))
    fill(c, d, MOUTH_IN, outline=LW * 0.8, shine=False)
    flat(c, inter(d + 0.02, ellipse(c, x, y - 0.22, 0.17, 0.1)), hexc(TONGUE[0]))


@part("m_smile")
def _(c, f=0):
    x, y = MOUTH
    d = polygon(c, bezier((x - 0.2, y + 0.06), (x, y + 0.08), (x + 0.2, y + 0.06), 8)
                + bezier((x + 0.2, y + 0.06), (x + 0.02, y - 0.3), (x - 0.2, y + 0.06), 12)[1:-1])
    fill(c, d, MOUTH_IN, outline=LW * 0.75, shine=False)
    flat(c, inter(d + 0.015, ellipse(c, x, y - 0.12, 0.09, 0.06)), hexc(TONGUE[0]))


@part("m_w")
def _(c, f=0):
    x, y = MOUTH
    line(c, arc_pts(x - 0.1, y + 0.06, 0.1, math.radians(200), math.radians(350), 14)
         + arc_pts(x + 0.1, y + 0.06, 0.1, math.radians(190), math.radians(340), 14), LW, seed=41)


@part("m_o")
def _(c, f=0):
    x, y = MOUTH
    fill(c, ellipse(c, x, y, 0.08, 0.1), MOUTH_IN, outline=LW * 0.8, shine=False)


@part("m_scream", frames=2)
def _(c, f=0):
    x, y = MOUTH
    w = 0.21 + 0.02 * f
    d = box(c, x, y - 0.06, w, 0.24 - 0.02 * f, 0.12)
    fill(c, d, MOUTH_IN, outline=LW * 0.85, shine=False)
    flat(c, inter(d + 0.02, ellipse(c, x, y - 0.28, 0.12, 0.08)), hexc(TONGUE[0]))


@part("m_flat")
def _(c, f=0):
    x, y = MOUTH
    line(c, [(x - 0.14, y), (x + 0.14, y)], LW, seed=43)


@part("m_frown")
def _(c, f=0):
    x, y = MOUTH
    line(c, arc_pts(x, y - 0.12, 0.15, math.radians(30), math.radians(150), 16), LW, seed=45)


@part("m_smirk")
def _(c, f=0):
    x, y = MOUTH
    line(c, bezier((x - 0.18, y + 0.02), (x + 0.04, y - 0.08), (x + 0.2, y + 0.1), 16), LW, seed=47)


@part("m_grit", frames=2)
def _(c, f=0):
    x, y = MOUTH
    j = 0.012 * (1 if f else -1)
    d = box(c, x + j, y, 0.27, 0.11, 0.04)
    aa = c.px * 1.2
    c.over(INK, smooth(LW * 1.2 + aa, LW * 1.2 - aa, d))
    flat(c, d, WHITE)
    for i in range(-2, 3):
        line(c, [(x + j + i * 0.1, y + 0.1), (x + j + i * 0.1, y - 0.1)], LW * 0.5, seed=49 + i)
    line(c, [(x + j - 0.27, y), (x + j + 0.27, y)], LW * 0.5, seed=51)


@part("m_3")
def _(c, f=0):
    x, y = MOUTH
    line(c, arc_pts(x + 0.0, y + 0.07, 0.07, math.radians(110), math.radians(-90), 12)
         + arc_pts(x + 0.0, y - 0.07, 0.07, math.radians(90), math.radians(-110), 12), LW, seed=53)


@part("m_tongue")
def _(c, f=0):
    x, y = MOUTH
    line(c, arc_pts(x, y + 0.12, 0.18, math.radians(215), math.radians(325), 14), LW, seed=55)
    fill(c, union(ellipse(c, x + 0.06, y - 0.07, 0.09, 0.11), box(c, x + 0.06, y + 0.0, 0.09, 0.05)), TONGUE, outline=LW * 0.75)


@part("m_drool")
def _(c, f=0):
    x, y = MOUTH
    line(c, arc_pts(x, y + 0.14, 0.2, math.radians(210), math.radians(330), 16), LW, seed=57)


@part("m_wavy", frames=2)
def _(c, f=0):
    x, y = MOUTH
    ph = f * math.pi
    line(c, [(x - 0.22 + 0.44 * i / 30, y + 0.045 * math.sin(i / 30 * math.pi * 4 + ph)) for i in range(31)], LW * 0.95, seed=59)


@part("m_tsu")
def _(c, f=0):
    x, y = MOUTH
    line(c, bezier((x - 0.16, y + 0.12), (x + 0.12, y + 0.04), (x + 0.06, y - 0.16), 16), LW * 1.1, seed=61)


@part("m_grin")
def _(c, f=0):
    x, y = MOUTH
    d = inter(ellipse(c, x, y + 0.06, 0.26, 0.2), c.y - (y + 0.08))
    fill(c, d, MOUTH_IN, outline=LW * 0.8, shine=False)
    flat(c, inter(d + 0.015, c.y - (y - 0.0)) , WHITE)


@part("m_pout")
def _(c, f=0):
    x, y = MOUTH
    line(c, arc_pts(x - 0.06, y, 0.06, math.radians(80), math.radians(-80), 10)
         + arc_pts(x - 0.06, y - 0.12, 0.06, math.radians(80), math.radians(-80), 10), LW, seed=63)


@part("m_small_smile")
def _(c, f=0):
    x, y = MOUTH
    line(c, arc_pts(x, y + 0.1, 0.14, math.radians(220), math.radians(320), 14), LW, seed=65)


# ============================================================ face extras (bubble frame)
@part("x_stream", frames=3)
def _(c, f=0):
    """Waterfall tears from T-eyes down to the bubble rim, wavy edges flowing (3 frames)."""
    for (x, y), _s in ((EYE_L, -1), (EYE_R, 1)):
        top = y - 0.16
        n = 22
        ph = f * 2.1
        left = [(x - 0.065 - 0.025 * i / n + 0.02 * math.sin(i * 0.9 + ph), top - 0.66 * i / n) for i in range(n + 1)]
        right = [(x + 0.065 + 0.025 * i / n + 0.02 * math.sin(i * 0.9 + ph + 1.3), top - 0.66 * i / n) for i in range(n + 1)]
        d = polygon(c, left + right[::-1])
        fill(c, d, TEAR, outline=LW * 0.7, shine=False)
        for k in range(3):  # flowing highlight dashes
            yy = top - 0.1 - ((k * 0.22 + f * 0.07) % 0.6)
            flat(c, ellipse(c, x - 0.02, yy, 0.016, 0.05), WHITE, 0.85)


@part("x_tears_lol", frames=2)
def _(c, f=0):
    """Tears of laughter flying off the eye corners."""
    for (x, y), s in ((EYE_L, -1), (EYE_R, 1)):
        k = 0.03 * f
        fill(c, drop_sdf(c, x + s * (0.3 + k), y - 0.02 + k, 0.075, 2.0), TEAR, outline=LW * 0.6)


@part("x_tear")
def _(c, f=0):
    x, y = EYE_L
    fill(c, drop_sdf(c, x - 0.02, y - 0.3, 0.085, 2.1), TEAR, outline=LW * 0.65)


@part("x_blush")
def _(c, f=0):
    for (x, y) in (CHEEK_L, CHEEK_R):
        flat(c, ellipse(c, x, y, 0.2, 0.1), "#ff9ab4", 0.85)
        for i in range(3):
            line(c, [(x - 0.12 + i * 0.09, y - 0.06), (x - 0.07 + i * 0.09, y + 0.06)], LW * 0.45, seed=70 + i, a=0.8)


@part("x_cheeks")
def _(c, f=0):
    for (x, y) in (CHEEK_L, CHEEK_R):
        flat(c, ellipse(c, x * 0.95, y - 0.08, 0.19, 0.15), "#ffb3c6", 0.95)
        ink(c, np.abs(ellipse(c, x * 0.95, y - 0.08, 0.19, 0.15)), LW * 0.5, a=0.6)


@part("x_sweat")
def _(c, f=0):
    fill(c, drop_sdf(c, 0.86, 0.42, 0.11, 2.1), TEAR, outline=LW * 0.75)


@part("x_vein")
def _(c, f=0):
    cx, cy, s = 0.78, 0.48, 0.17
    d = None
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        pts = bezier((cx + (ux * 0.86 + vx * 0.34) * s, cy + (uy * 0.86 + vy * 0.34) * s), (cx + ux * 0.1 * s, cy + uy * 0.1 * s),
                     (cx + (ux * 0.86 - vx * 0.34) * s, cy + (uy * 0.86 - vy * 0.34) * s), 16)
        dd = polyline(c, pts, 0.03)
        d = dd if d is None else union(d, dd)
    fill(c, d, RED, outline=LW * 0.4, shine=False)


@part("x_gloom")
def _(c, f=0):
    """Dread lines hanging from the top of the face."""
    for i, x in enumerate((-0.5, -0.3, -0.1, 0.1, 0.3, 0.5, 0.7)):
        top = 0.66 - 0.06 * abs(x - 0.1)
        ln = 0.16 + 0.1 * ((i * 37) % 3) / 2
        flat(c, segment(c, x, top, x, top - ln, 0.022), "#7a8fd8", 0.85)


@part("x_snot", frames=1)
def _(c, f=0):
    x, y = at(MOUTH, 0.12, 0.2)
    d = circle(c, x, y, 0.13)
    flat(c, d, "#bfe6ff", 0.75)
    ink(c, np.abs(d), LW * 0.5, a=0.8)
    flat(c, circle(c, x - 0.04, y + 0.05, 0.03), WHITE, 0.95)


@part("x_drool")
def _(c, f=0):
    x, y = at(MOUTH, 0.17, -0.08)
    fill(c, union(box(c, x, y, 0.03, 0.08, 0.03), drop_sdf(c, x, y - 0.14, 0.06, 1.8)), TEAR, outline=LW * 0.6)


@part("x_arms")
def _(c, f=0):
    """Shrug arms ¯\\_ _/¯ on both sides of the face."""
    line(c, [(-0.86, 0.02), (-0.72, 0.02), (-0.62, -0.26), (-0.5, -0.26)], LW * 0.9, seed=81)
    line(c, [(0.98, 0.02), (0.84, 0.02), (0.74, -0.26), (0.62, -0.26)], LW * 0.9, seed=83)


@part("x_fist")
def _(c, f=0):
    x, y = 0.88, -0.22
    fill(c, box(c, x, y, 0.13, 0.12, 0.06), ("#ffe2cc", "#fff3e8", "#e8b89a"), outline=LW * 0.75, shine=False)
    for i in range(3):
        line(c, [(x - 0.1 + i * 0.07, y + 0.12), (x - 0.1 + i * 0.07, y + 0.04)], LW * 0.4, seed=85 + i)
    for i in range(3):
        line(c, [(x + 0.2, y + 0.18 - i * 0.12), (x + 0.32, y + 0.24 - i * 0.12)], LW * 0.45, seed=88 + i, a=0.8)


@part("x_dots", frames=3)
def _(c, f=0):
    """Thinking dots appearing one by one (frames 0..2 show 1..3 dots)."""
    for i in range(f + 1):
        flat(c, circle(c, 0.42 + i * 0.16, -0.32, 0.045), INK)


@part("x_shades_glint")
def _(c, f=0):
    for (x, y) in (EYE_L, EYE_R):
        flat(c, star(c, x + 0.12, y + 0.12, 4, 0.12, 0.025), WHITE)


@part("x_green")
def _(c, f=0):
    """Queasy green tint across the upper face."""
    a = smooth(-0.1, 0.5, c.y) * smooth(0.95, 0.6, np.hypot((c.x - 0.06) / 1.0, (c.y - 0.06) / 0.8)) * 0.45
    c.over(hexc("#8fd16a"), a)


# ============================================================ signs and particles
def sign_excl(c, f=0):
    d = union(polygon(c, [(-0.2, 0.86), (0.2, 0.86), (0.09, -0.32), (-0.09, -0.32)]) - 0.04, circle(c, 0, -0.68, 0.16))
    fill(c, d, GOLD, outline=0.07)


def sign_quest(c, f=0):
    pts = arc_pts(0, 0.38, 0.38, math.radians(165), math.radians(-60), 28)
    pts += bezier(pts[-1], (0.06, -0.04), (0.0, -0.28), 10)[1:]
    d = union(polyline(c, pts, 0.14), circle(c, 0, -0.68, 0.15))
    fill(c, d, ("#8f86ff", "#d2ccff", "#5a4fd0"), outline=0.07)


def sign_heart(c, f=0):
    fill(c, heart(c, 0, -0.02, 1.5), RED, outline=0.07)


def sign_note(c, f=0):
    head = ellipse(c, -0.3, -0.5, 0.32, 0.24, rot=0.45)
    stem = box(c, -0.02, 0.1, 0.07, 0.64)
    flag = polyline(c, bezier((0.0, 0.7), (0.5, 0.46), (0.44, 0.02), 16), 0.11, 0.05)
    fill(c, union(head, stem, flag), ("#7fe0d0", "#d0fff6", "#2fa898"), outline=0.07)


def sign_ghost(c, f=0):
    body = union(circle(c, 0, 0.25, 0.55), box(c, 0, -0.25, 0.55, 0.5))
    waves = union(*[circle(c, x, -0.75, 0.19) for x in (-0.37, 0.0, 0.37)])
    body = union(sub(body, box(c, 0, -1.1, 1, 0.35)), inter(waves, box(c, 0, -0.72, 0.56, 0.2)))
    fill(c, body, ("#f4f8ff", "#ffffff", "#b9c8ec"), outline=0.07)
    flat(c, union(ellipse(c, -0.18, 0.25, 0.07, 0.11), ellipse(c, 0.18, 0.25, 0.07, 0.11)), INK)
    flat(c, ellipse(c, 0, 0.0, 0.1, 0.12), INK)


def sign_z(c, f=0):
    d = polyline(c, [(-0.5, 0.52), (0.5, 0.52), (-0.5, -0.52), (0.5, -0.52)], 0.15)
    fill(c, d, ("#b8b0ff", "#e6e2ff", "#7a70e0"), outline=0.07, shine=False)


def sign_puff(c, f=0):
    d = union(circle(c, -0.3, -0.1, 0.42), circle(c, 0.2, 0.08, 0.5), circle(c, 0.0, -0.3, 0.38))
    fill(c, d, ("#ffffff", "#ffffff", "#d6d2e0"), outline=0.07, shine=False)


def sign_star(c, f=0):
    fill(c, star(c, 0, 0.02, 5, 0.86, 0.4) - 0.04, GOLD, outline=0.07)


def sign_drop(c, f=0):
    fill(c, drop_sdf(c, 0, -0.3, 0.5, 2.2), TEAR, outline=0.07)


def sign_vein(c, f=0):
    d = None
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        pts = bezier(((ux * 0.86 + vx * 0.34) * 0.9, (uy * 0.86 + vy * 0.34) * 0.9), (ux * 0.08, uy * 0.08),
                     ((ux * 0.86 - vx * 0.34) * 0.9, (uy * 0.86 - vy * 0.34) * 0.9), 18)
        dd = polyline(c, pts, 0.13)
        d = dd if d is None else union(d, dd)
    fill(c, d, RED, outline=0.06, shine=False)


def sign_confetti(c, f=0):
    fill(c, box(c, 0, 0, 0.62, 0.32, 0.12), ("#ffffff", "#ffffff", "#d8d4e4"), outline=0.0, shine=False)


def sign_flame(c, f=0):
    """Small cartoon flame for rage/determined auras (white, tinted by the emitter)."""
    d = drop_sdf(c, 0, -0.35, 0.45, 2.6)
    fill(c, d, ("#ffffff", "#ffffff", "#e6e0ee"), outline=0.07, shine=False)
    flat(c, drop_sdf(c, 0, -0.45, 0.2, 2.3), hexc("#fff6d8"), 0.9)


SIGNS = {"s_confetti": sign_confetti, "s_flame": sign_flame, "s_excl": sign_excl, "s_quest": sign_quest, "s_heart": sign_heart, "s_note": sign_note, "s_ghost": sign_ghost,
         "s_z": sign_z, "s_puff": sign_puff, "s_star": sign_star, "s_drop": sign_drop, "s_vein": sign_vein}


# ------------------------------------------------------------ additive white fx
def fx_out(c, a):
    c.rgba = np.concatenate([np.ones((*a.shape, 3), np.float32) * a[..., None], a[..., None]], -1).astype(np.float32)


def fx_sparkle(c):
    r = np.hypot(c.x, c.y)
    ax, ay = np.abs(c.x), np.abs(c.y)
    def w(t):
        return 0.012 + 0.045 * (1 - np.clip(t, 0, 1)) ** 3
    rays = np.maximum(np.exp(-(ay / w(ax)) ** 2) * (1 - np.clip(ax, 0, 1)) ** 1.6,
                      np.exp(-(ax / w(ay)) ** 2) * (1 - np.clip(ay, 0, 1)) ** 1.6)
    core = np.exp(-(r / 0.06) ** 2) + 0.45 * np.exp(-(r / 0.2) ** 2)
    fx_out(c, np.clip(rays + core, 0, 1))


def fx_mote(c):
    r = np.hypot(c.x, c.y)
    fx_out(c, np.clip(np.exp(-(r / 0.38) ** 2) * 1.1 + np.exp(-(r / 0.1) ** 2) * 0.5, 0, 1) * smooth(1.0, 0.85, r))


def fx_ring(c):
    r = np.hypot(c.x, c.y)
    fx_out(c, np.clip(np.exp(-((r - 0.86) / 0.022) ** 2) + 0.25 * np.exp(-((r - 0.84) / 0.08) ** 2), 0, 1))


def fx_lines(c):
    """Manga emphasis lines radiating outward (for shock / surprise)."""
    r = np.hypot(c.x, c.y)
    a = np.arctan2(c.y, c.x)
    rays = smooth(0.92, 0.985, np.cos(a * 14)) * smooth(0.45, 0.6, r) * smooth(1.0, 0.85, r)
    fx_out(c, np.clip(rays, 0, 1))


def fx_star4(c):
    """Crisp HSR-style four-point star: concave diamond with a hot core and a faint halo."""
    ax, ay = np.abs(c.x), np.abs(c.y)
    # concave astroid-like star: |x|^0.5 + |y|^0.5 <= r^0.5
    d = np.sqrt(ax) + np.sqrt(ay) - np.sqrt(0.82)
    body = smooth(0.02, -0.02, d)
    r = np.hypot(c.x, c.y)
    core = np.exp(-(r / 0.16) ** 2)
    halo = np.exp(-(r / 0.45) ** 2) * 0.35
    fx_out(c, np.clip(body * 0.85 + core * 0.6 + halo, 0, 1))


def fx_flash(c):
    r = np.hypot(c.x, c.y)
    fx_out(c, np.clip(np.exp(-(r / 0.5) ** 2) * 0.9 + np.exp(-(r / 0.15) ** 2) * 0.4, 0, 1) * smooth(1.0, 0.8, r))


def fx_streak(c):
    """Soft speed/aura line, long axis vertical."""
    fx_out(c, np.clip(np.exp(-(c.x / 0.07) ** 2) * np.clip(1 - np.abs(c.y), 0, 1) ** 1.2 * 1.2, 0, 1))


def fx_ring_soft(c):
    """Thick soft shock ring for impacts."""
    r = np.hypot(c.x, c.y)
    fx_out(c, np.clip(np.exp(-((r - 0.78) / 0.09) ** 2) * 0.9 + np.exp(-((r - 0.84) / 0.02) ** 2) * 0.5, 0, 1))


FX = {"sparkle": fx_sparkle, "mote": fx_mote, "ring": fx_ring, "lines": fx_lines, "star4": fx_star4, "flash": fx_flash,
      "streak": fx_streak, "ring_soft": fx_ring_soft}


# ============================================================ output
def save(img, sub_, name):
    assert name == name.lower(), f"Minecraft resource names must be lowercase: {name}"
    os.makedirs(os.path.join(TEX, sub_), exist_ok=True)
    img.save(os.path.join(TEX, sub_, name + ".png"), optimize=True)


def main(only=None):
    def want(n):
        return not only or n in only
    if want("bubble"):
        c = Canvas(*FRAME)
        bubble(c)
        save(c.image(), "emote", "bubble")
    for n, (fn, frames) in PARTS.items():
        if not want(n):
            continue
        for f in range(frames):
            c = Canvas(*FRAME)
            fn(c, f)
            save(c.image(), "emote", "f_" + n + ("" if f == 0 else f"_{f}"))
    for n, fn in SIGNS.items():
        if want(n):
            c = Canvas(48, 48, zoom=1.1)
            fn(c)
            save(c.image(), "emote", n)
    for n, fn in FX.items():
        if want(n):
            c = Canvas(96, 96)
            fn(c)
            save(c.image(), "fx", n)
    print(len(PARTS), "parts,", len(SIGNS), "signs,", len(FX), "fx")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
