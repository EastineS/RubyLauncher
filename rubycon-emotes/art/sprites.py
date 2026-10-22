"""Draws every emote texture.

Style: small HSR / Genshin-like emblems for roleplay. A tinted glass plate with a thin gold rim
carries a clean white glyph; soft sparkles and motes carry the mood. Face marks (blush, tears,
sweat) are small, soft and lit by the world like the skin they sit on.

Output (mod resources, textures/):
  emote/<glyph>.png         white glyphs drawn on the plate (tinted white in game)
  emote/plate|rim|halo.png  emblem parts, tinted per emote
  emote/p_<name>.png        soft particles, white, tinted per emitter (+ _glow)
  emote/face_<name>.png     pre-coloured face marks, world-lit
  fx/<name>.png             additive white fx (sparkle, mote, rings)
"""
import math
import os
import sys

import numpy as np
from PIL import Image

from sdf import (Canvas, GLOW_PAD, arc_pts, bezier, circle, ellipse, gaussian, glow_image, heart, hexc, mix,
                 polygon, polyline, segment, smooth, star, sub, union, inter, box)

ROOT = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(ROOT, "..", "mod", "src", "main", "resources", "assets", "rubycon_emotes", "textures")

WHITE = hexc("#ffffff")
SHADOW = hexc("#141832")


# ============================================================ painters
def paint_glyph(c, d, shadow=0.5):
    """White glyph with a soft drop shadow so it reads on any plate colour."""
    aa = c.px * 1.2
    if shadow:
        k = max(1, int(0.07 / c.px))
        sh = np.roll(smooth(aa, -aa, d), k, axis=0)
        sh = gaussian(sh, 0.05 / c.px)
        c.over(SHADOW, sh * shadow)
    fill = smooth(aa, -aa, d)
    col = mix(hexc("#e4eafb"), WHITE, smooth(-0.7, 0.5, c.y))
    c.over(col, fill)
    return fill


def paint_soft(c, d, outline=0.06, line=0.42):
    """White particle icon with a soft grey edge; vertex colour tints it, the edge stays darker."""
    aa = c.px * 1.2
    if outline:
        c.over(np.full(3, line, np.float32), smooth(outline + aa, outline - aa, d) * 0.75)
    fill = smooth(aa, -aa, d)
    depth = np.clip(-d / 0.35, 0, 1)
    col = mix(hexc("#d9dcea"), WHITE, smooth(0.0, 0.8, depth) * 0.6 + smooth(-0.6, 0.6, c.y) * 0.4)
    c.over(col, fill)
    # small specular dot, upper left
    spec = smooth(aa, -aa, d + 0.18) * smooth(0.2, 0.6, -c.x * 0.6 + c.y * 0.8)
    c.over(WHITE, spec * 0.6)
    return fill


def paint_flat(c, d, rgb, a=1.0):
    aa = c.px * 1.2
    fill = smooth(aa, -aa, d)
    c.over(rgb, fill * a)
    return fill


# ============================================================ shapes
def drop_sdf(c, cx, cy, r, tip=1.9, rot=0.0):
    x, y = c.x - cx, c.y - cy
    ca, sa = math.cos(rot), math.sin(rot)
    class R:  # rotated view of the canvas for the primitives
        pass
    r_ = R()
    r_.x, r_.y, r_.px = x * ca + y * sa, -x * sa + y * ca, c.px
    d1 = circle(r_, 0, 0, r)
    tri = polygon(r_, [(-r * 0.86, r * 0.5), (0, r * tip), (r * 0.86, r * 0.5)])
    k = r * 0.25
    h = np.clip(0.5 + 0.5 * (tri - d1) / k, 0, 1)
    return tri * (1 - h) + d1 * h - k * h * (1 - h)


def ring_sdf(c, cx, cy, r, w):
    return np.abs(np.hypot(c.x - cx, c.y - cy) - r) - w


def vein_sdf(c, s=1.0):
    d = None
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        p0 = (ux * 0.86 * s + vx * 0.34 * s, uy * 0.86 * s + vy * 0.34 * s)
        p2 = (ux * 0.86 * s - vx * 0.34 * s, uy * 0.86 * s - vy * 0.34 * s)
        p1 = (ux * 0.05 * s, uy * 0.05 * s)
        pts = bezier(p0, p1, p2, 20)
        half = len(pts) // 2
        dd = union(polyline(c, pts[:half + 1], 0.05 * s, 0.14 * s), polyline(c, pts[half:], 0.14 * s, 0.05 * s))
        d = dd if d is None else union(d, dd)
    return d


def note_sdf(c, s=1.0, cx=0.0, cy=0.0):
    head = ellipse(c, cx - 0.28 * s, cy - 0.5 * s, 0.3 * s, 0.22 * s, rot=0.45)
    stem = box(c, cx - 0.02 * s, cy + 0.1 * s, 0.065 * s, 0.62 * s)
    flag = polyline(c, bezier((cx, cy + 0.68 * s), (cx + 0.5 * s, cy + 0.45 * s), (cx + 0.42 * s, cy + 0.02 * s), 16),
                    0.1 * s, 0.05 * s)
    return union(head, stem, flag)


def wave_pts(x0, x1, y, amp, waves, n=48, vertical=False):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = x0 + (x1 - x0) * t
        v = y + amp * math.sin(t * waves * 2 * math.pi)
        pts.append((v, u) if vertical else (u, v))
    return pts


STROKE = 0.15

GLYPHS = {}


def glyph(name):
    def deco(fn):
        GLYPHS[name] = fn
        return fn
    return deco


@glyph("g_joy")
def _(c):
    return union(star(c, -0.12, 0.08, 4, 0.78, 0.17), star(c, 0.56, -0.52, 4, 0.34, 0.09), circle(c, 0.56, 0.58, 0.1))


@glyph("g_laugh")
def _(c):
    eyes = union(*[polyline(c, arc_pts(sx * 0.42, 0.02, 0.27, math.radians(15), math.radians(165), 20), STROKE)
                   for sx in (-1, 1)])
    mouth = inter(circle(c, 0, -0.32, 0.36), c.y + 0.32)
    return union(eyes, mouth)


@glyph("g_heart")
def _(c):
    return heart(c, 0, -0.04, 1.5)


@glyph("g_flower")
def _(c):
    petals = union(*[ellipse(c, math.cos(a) * 0.43, math.sin(a) * 0.43, 0.36, 0.24, rot=a)
                     for a in [math.pi / 2 + k * 2 * math.pi / 5 for k in range(5)]])
    return union(sub(petals, circle(c, 0, 0, 0.24)), circle(c, 0, 0, 0.13))


@glyph("g_blush")
def _(c):
    return union(*[segment(c, -0.62 + i * 0.5, -0.38, -0.32 + i * 0.5, 0.38, 0.11) for i in range(3)])


@glyph("g_drop")
def _(c):
    return drop_sdf(c, 0, -0.28, 0.5, 2.1)


@glyph("g_drops")
def _(c):
    return union(drop_sdf(c, -0.28, -0.12, 0.38, 2.1), drop_sdf(c, 0.4, -0.5, 0.26, 2.1))


@glyph("g_vein")
def _(c):
    return vein_sdf(c, 0.92)


@glyph("g_scribble")
def _(c):
    pts = []
    for i in range(160):
        t = i / 159
        a = t * math.pi * 2 * 3.2
        r = 0.32 + 0.12 * math.sin(t * 9)
        pts.append((-0.55 + 1.1 * t + math.cos(a) * r * 0.55, math.sin(a) * r))
    return polyline(c, pts, 0.075)


def exclaim_sdf(c, cx=0.0, s=1.0):
    bar = polygon(c, [(cx - 0.17 * s, 0.88 * s), (cx + 0.17 * s, 0.88 * s), (cx + 0.08 * s, -0.3 * s),
                      (cx - 0.08 * s, -0.3 * s)]) - 0.04 * s
    return union(bar, circle(c, cx, -0.68 * s, 0.15 * s))


@glyph("g_exclaim")
def _(c):
    return exclaim_sdf(c, 0, 0.95)


@glyph("g_exclaim2")
def _(c):
    return union(exclaim_sdf(c, -0.3, 0.9), exclaim_sdf(c, 0.3, 0.9))


@glyph("g_question")
def _(c):
    pts = arc_pts(0, 0.38, 0.36, math.radians(165), math.radians(-60), 28)
    pts += bezier(pts[-1], (0.06, -0.04), (0.0, -0.26), 10)[1:]
    return union(polyline(c, pts, STROKE * 0.95), circle(c, 0, -0.66, 0.14))


@glyph("g_dots")
def _(c):
    return union(*[circle(c, x, -0.1, 0.15) for x in (-0.52, 0, 0.52)])


@glyph("g_idea")
def _(c):
    rays = union(*[segment(c, math.cos(a) * 0.7, math.sin(a) * 0.7, math.cos(a) * 0.9, math.sin(a) * 0.9, 0.055)
                   for a in [k * math.pi / 4 + math.pi / 8 for k in range(8)]])
    return union(star(c, 0, 0, 4, 0.62, 0.15), rays)


@glyph("g_check")
def _(c):
    return polyline(c, [(-0.56, 0.02), (-0.16, -0.4), (0.6, 0.46)], STROKE * 1.1)


@glyph("g_cross")
def _(c):
    return union(segment(c, -0.48, -0.48, 0.48, 0.48, STROKE * 1.05), segment(c, -0.48, 0.48, 0.48, -0.48, STROKE * 1.05))


@glyph("g_z")
def _(c):
    big = polyline(c, [(-0.55, 0.42), (0.2, 0.42), (-0.55, -0.42), (0.2, -0.42)], 0.12)
    small = polyline(c, [(0.36, 0.72), (0.7, 0.72), (0.36, 0.34), (0.7, 0.34)], 0.07)
    return union(big, small)


@glyph("g_sigh")
def _(c):
    cloud = union(circle(c, -0.3, -0.05, 0.3), circle(c, 0.1, 0.1, 0.36), circle(c, 0.45, -0.08, 0.26),
                  box(c, 0.08, -0.22, 0.5, 0.14, 0.12))
    tail = polyline(c, bezier((-0.55, -0.15), (-0.85, -0.2), (-0.78, -0.5), 12), 0.08, 0.03)
    return union(cloud, tail)


@glyph("g_ecg")
def _(c):
    return polyline(c, [(-0.86, -0.02), (-0.36, -0.02), (-0.2, 0.46), (0.0, -0.52), (0.16, 0.2), (0.3, -0.02),
                        (0.86, -0.02)], 0.1)


@glyph("g_awkward")
def _(c):
    mouth = segment(c, -0.5, -0.38, 0.12, -0.38, 0.1)
    eyes = union(segment(c, -0.5, 0.12, -0.24, 0.12, 0.09), segment(c, -0.1, 0.12, 0.16, 0.12, 0.09))
    return union(mouth, eyes, drop_sdf(c, 0.5, 0.22, 0.2, 2.1, rot=0.0))


@glyph("g_shiver")
def _(c):
    return union(*[polyline(c, wave_pts(-0.7, 0.7, x, 0.09, 2.5, vertical=True), 0.08) for x in (-0.45, 0, 0.45)])


@glyph("g_disgust")
def _(c):
    return union(polyline(c, wave_pts(-0.7, 0.7, 0.2, 0.12, 2.0), 0.09), polyline(c, wave_pts(-0.7, 0.7, -0.25, 0.12, 2.0), 0.09))


@glyph("g_eye")
def _(c):
    almond = inter(circle(c, 0, -0.62, 0.95), circle(c, 0, 0.62, 0.95))
    return np.abs(almond) - 0.07


@glyph("g_pupil")
def _(c):
    return circle(c, 0, 0, 0.7)


@glyph("g_glint")
def _(c):
    main = star(c, -0.1, 0.05, 4, 0.82, 0.12)
    diag = star(c, -0.1, 0.05, 4, 0.42, 0.1, rot=math.pi / 4)
    return union(main, diag, star(c, 0.55, 0.55, 4, 0.22, 0.06))


@glyph("g_crown")
def _(c):
    body = polygon(c, [(-0.66, -0.4), (-0.7, 0.32), (-0.33, -0.02), (0, 0.5), (0.33, -0.02), (0.7, 0.32), (0.66, -0.4)]) - 0.03
    return union(body, circle(c, -0.7, 0.4, 0.09), circle(c, 0, 0.6, 0.1), circle(c, 0.7, 0.4, 0.09),
                 box(c, 0, -0.52, 0.66, 0.07, 0.03))


@glyph("g_note")
def _(c):
    return note_sdf(c, 1.05, 0.05, 0.0)


@glyph("g_flame")
def _(c):
    pts = bezier((0.0, -0.75), (0.75, -0.6), (0.38, 0.1), 16) + bezier((0.38, 0.1), (0.25, 0.45), (0.0, 0.85), 12)[1:] \
        + bezier((0.0, 0.85), (-0.05, 0.4), (-0.32, 0.2), 10)[1:] + bezier((-0.32, 0.2), (-0.75, -0.55), (0.0, -0.75), 16)[1:]
    pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
    outer = polygon(c, pts)
    inner = drop_sdf(c, 0.02, -0.42, 0.2, 2.2)
    return sub(outer, inner)


@glyph("g_spiral")
def _(c):
    pts = []
    for i in range(140):
        t = i / 139
        a = t * math.pi * 2 * 2.3
        r = 0.06 + 0.72 * t
        pts.append((math.cos(a) * r, math.sin(a) * r))
    return polyline(c, pts, 0.07, 0.1)


@glyph("g_star")
def _(c):
    return star(c, 0, 0.02, 5, 0.86, 0.38) - 0.04


# ------------------------------------------------------------ particles (white, tinted)
PARTICLES = {
    "p_heart": lambda c: heart(c, 0, -0.04, 1.45),
    "p_petal": lambda c: inter(circle(c, -0.3, 0, 0.75), circle(c, 0.3, 0, 0.75)) * 1.0,
    "p_note": lambda c: note_sdf(c, 1.0),
    "p_z": lambda c: polyline(c, [(-0.5, 0.5), (0.5, 0.5), (-0.5, -0.5), (0.5, -0.5)], 0.15),
    "p_drop": lambda c: drop_sdf(c, 0, -0.32, 0.5, 2.2),
    "p_star": lambda c: star(c, 0, 0.02, 5, 0.85, 0.4) - 0.05,
    "p_puff": lambda c: union(circle(c, -0.3, -0.1, 0.42), circle(c, 0.2, 0.08, 0.5), circle(c, 0.0, -0.3, 0.38)),
}


# ------------------------------------------------------------ emblem parts
def plate_tex(c):
    r = np.hypot(c.x, c.y)
    R = 0.9
    a = smooth(R + c.px, R - c.px, r)
    v = 1.0 - 0.32 * (r / R) ** 2
    v += 0.16 * smooth(0.25, 0.85, c.y / R) * smooth(R, R * 0.6, r)  # glassy top sheen
    v -= 0.12 * smooth(R * 0.84, R * 0.92, r)  # inner bevel line
    inner = np.exp(-((r - R * 0.8) / 0.012) ** 2) * 0.35  # thin etched ring
    v = np.clip(v + inner, 0, 1)
    rgb = np.repeat(v[..., None], 3, -1)
    c.rgba = np.concatenate([rgb * a[..., None] * 0.94, a[..., None] * 0.94], -1).astype(np.float32)


def rim_tex(c):
    r = np.hypot(c.x, c.y)
    ring = smooth(0.035 + c.px, 0.035 - c.px, np.abs(r - 0.86))
    a = ring
    for k in range(4):  # small diamonds at the cardinal points
        ang = k * math.pi / 2
        dx, dy = c.x - math.cos(ang) * 0.86, c.y - math.sin(ang) * 0.86
        a = np.maximum(a, smooth(0.11 + c.px, 0.11 - c.px, np.abs(dx) + np.abs(dy)))
    for k in range(4):  # short outer ticks between them
        ang = k * math.pi / 2 + math.pi / 4
        along = c.x * math.cos(ang) + c.y * math.sin(ang)
        across = -c.x * math.sin(ang) + c.y * math.cos(ang)
        a = np.maximum(a, smooth(0.018 + c.px, 0.018 - c.px, np.abs(across)) * smooth(0.9, 0.92, along) * smooth(1.0, 0.98, along))
    shade = 0.85 + 0.15 * smooth(-0.6, 0.8, c.y)
    rgb = np.repeat(shade[..., None], 3, -1)
    c.rgba = np.concatenate([rgb * a[..., None], a[..., None]], -1).astype(np.float32)


def halo_tex(c):
    r = np.hypot(c.x, c.y)
    a = np.clip(np.exp(-(r / 0.5) ** 2) * 0.9 + np.exp(-(r / 0.22) ** 2) * 0.3, 0, 1) * smooth(1.0, 0.85, r)
    c.rgba = np.concatenate([np.repeat(a[..., None], 3, -1), a[..., None]], -1).astype(np.float32)


# ------------------------------------------------------------ face marks (pre-coloured, lit)
def face_blush(c):
    r = np.hypot(c.x / 1.0, c.y / 0.55)
    a = np.clip(1 - r, 0, 1) ** 1.6 * 0.85
    rgb = mix(hexc("#ff7a9a"), hexc("#ff9fb6"), smooth(-0.5, 0.5, c.y))
    c.rgba = np.concatenate([rgb * a[..., None], a[..., None]], -1).astype(np.float32)


def face_tear(c):
    d = drop_sdf(c, 0, -0.3, 0.5, 2.2)
    paint_flat(c, d, hexc("#5fb6ff"), 0.9)
    paint_flat(c, d + 0.08, hexc("#bfe6ff"), 0.95)
    paint_flat(c, circle(c, -0.15, -0.2, 0.13), WHITE, 0.95)


def face_sweat(c):
    d = drop_sdf(c, 0, -0.3, 0.5, 2.2)
    paint_flat(c, d - 0.07, hexc("#2c6fb8"), 0.9)
    paint_flat(c, d, hexc("#d8f2ff"), 1.0)
    paint_flat(c, d + 0.12, hexc("#a8dcff"), 0.6)
    paint_flat(c, ellipse(c, -0.16, -0.12, 0.1, 0.2), WHITE, 0.95)


def face_vein(c):
    d = vein_sdf(c, 0.9)
    paint_flat(c, d - 0.06, hexc("#5a0a18"), 0.85)
    paint_flat(c, d, hexc("#ff4a52"), 1.0)
    paint_flat(c, d + 0.05, hexc("#ff8a8a"), 0.5)


FACE = {"face_blush": face_blush, "face_tear": face_tear, "face_sweat": face_sweat, "face_vein": face_vein}


# ------------------------------------------------------------ additive white fx
def fx_out(c, a):
    c.rgba = np.concatenate([np.ones(a.shape + (3,), np.float32) * a[..., None], a[..., None]], -1).astype(np.float32)


def fx_sparkle(c):
    """Genshin-style four-ray sparkle: hairline rays tapering out of a soft core."""
    r = np.hypot(c.x, c.y)
    ax, ay = np.abs(c.x), np.abs(c.y)
    w = lambda t: 0.012 + 0.045 * (1 - np.clip(t, 0, 1)) ** 3
    rays = np.maximum(np.exp(-(ay / w(ax)) ** 2) * (1 - np.clip(ax, 0, 1)) ** 1.6,
                      np.exp(-(ax / w(ay)) ** 2) * (1 - np.clip(ay, 0, 1)) ** 1.6)
    diag = (np.exp(-(np.abs(c.x - c.y) / 0.025) ** 2) + np.exp(-(np.abs(c.x + c.y) / 0.025) ** 2)) * np.clip(1 - r / 0.35, 0, 1)
    core = np.exp(-(r / 0.06) ** 2) + 0.45 * np.exp(-(r / 0.2) ** 2)
    fx_out(c, np.clip(rays + core + diag * 0.3, 0, 1))


def fx_mote(c):
    r = np.hypot(c.x, c.y)
    fx_out(c, np.clip(np.exp(-(r / 0.38) ** 2) * 1.1 + np.exp(-(r / 0.1) ** 2) * 0.5, 0, 1) * smooth(1.0, 0.85, r))


def fx_ring(c):
    r = np.hypot(c.x, c.y)
    fx_out(c, np.clip(np.exp(-((r - 0.86) / 0.022) ** 2) + 0.25 * np.exp(-((r - 0.84) / 0.08) ** 2), 0, 1))


def fx_ring_dash(c):
    r = np.hypot(c.x, c.y)
    a = np.arctan2(c.y, c.x)
    band = np.exp(-((r - 0.86) / 0.016) ** 2)
    seg = smooth(0.0, 0.03, np.cos(a * 18) + 0.55)
    ticks = np.exp(-((r - 0.95) / 0.02) ** 2) * smooth(0.985, 0.998, np.cos(a * 4))
    fx_out(c, np.clip(band * seg + ticks, 0, 1))


def fx_streak(c):
    fx_out(c, np.clip(np.exp(-(c.x / 0.05) ** 2) * np.clip(1 - np.abs(c.y), 0, 1) ** 1.5 * 1.3, 0, 1))


FX = {"sparkle": fx_sparkle, "mote": fx_mote, "ring": fx_ring, "ring_dash": fx_ring_dash, "streak": fx_streak}


# ============================================================ output
def save(img, sub_, name):
    os.makedirs(os.path.join(TEX, sub_), exist_ok=True)
    img.save(os.path.join(TEX, sub_, name + ".png"), optimize=True)


def main(only=None):
    want = lambda n: not only or n in only
    for n, fn in GLYPHS.items():
        if want(n):
            c = Canvas(64, 64, zoom=1.08)
            paint_glyph(c, fn(c))
            save(c.image(), "emote", n)
    for n, fn in PARTICLES.items():
        if want(n):
            c = Canvas(48, 48, zoom=1.1)
            m = paint_soft(c, fn(c))
            save(c.image(), "emote", n)
            save(glow_image(c, m, WHITE, 0.25, 0.7), "emote", n + "_glow")
    for n, fn in (("plate", plate_tex), ("rim", rim_tex), ("halo", halo_tex)):
        if want(n):
            c = Canvas(96, 96)
            fn(c)
            save(c.image(), "emote", n)
    for n, fn in FACE.items():
        if want(n):
            c = Canvas(48, 48, zoom=1.08)
            fn(c)
            save(c.image(), "emote", n)
    for n, fn in FX.items():
        if want(n):
            c = Canvas(96, 96)
            fn(c)
            save(c.image(), "fx", n)
    print(len(GLYPHS), "glyphs,", len(PARTICLES), "particles,", len(FACE), "face marks,", len(FX), "fx")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
