"""Draws every emote sprite and shared FX texture.

Output: <mod>/src/main/resources/assets/rubycon_emotes/textures/emote/<name>.png
plus <name>_glow.png (additive bloom) for each solid sprite, and white tintable
FX textures under textures/fx/.
"""
import math
import os
import sys
import numpy as np
from sdf import *

ROOT = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(ROOT, "..", "mod", "src", "main", "resources", "assets", "rubycon_emotes", "textures")
SPRITES = {}


def sprite(name, w=128, h=128, glow="auto", radius=0.2, strength=0.9):
    def deco(fn):
        SPRITES[name] = (fn, w, h, glow, radius, strength)
        return fn
    return deco


def P(name):
    return PAL[name]


def W(c, d):
    """coverage mask of an sdf"""
    return smooth(c.px, -c.px, d)


# ============================================================ shapes
def vein_sdf(c, s=1.0, cx=0.0, cy=0.0):
    """Anime anger mark: four bulging arcs bending toward the centre."""
    d = None
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        # each arc bulges toward the centre; tips flare outward, gaps stay on the axes
        p0 = (cx + ux * 0.86 * s + vx * 0.34 * s, cy + uy * 0.86 * s + vy * 0.34 * s)
        p2 = (cx + ux * 0.86 * s - vx * 0.34 * s, cy + uy * 0.86 * s - vy * 0.34 * s)
        p1 = (cx + ux * 0.05 * s, cy + uy * 0.05 * s)
        pts = bezier(p0, p1, p2, 20)
        half = len(pts) // 2
        dd = union(polyline(c, pts[:half + 1], 0.045 * s, 0.15 * s), polyline(c, pts[half:], 0.15 * s, 0.045 * s))
        d = dd if d is None else union(d, dd)
    return d


@sprite("anger_vein")
def _(c):
    d = vein_sdf(c, 0.95)
    return [(d, P("red"), {})]


@sprite("rage_vein")
def _(c):
    d = vein_sdf(c, 1.0)
    # flame tips licking off each arc
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        d = sunion(d, polyline(c, [(ux * 0.55, uy * 0.55), (ux * 0.78 - uy * 0.06, uy * 0.78 + ux * 0.06), (ux * 0.95, uy * 0.95)], 0.1, 0.0), 0.05)
    return [(d, P("red"), {"core": 0.35})]


@sprite("steam", strength=0.5)
def _(c):
    d = union(circle(c, -0.35, -0.2, 0.42), circle(c, 0.2, -0.25, 0.48), circle(c, 0.0, 0.25, 0.45), circle(c, 0.5, 0.18, 0.3))
    d = sunion(d, circle(c, -0.55, 0.15, 0.28), 0.15)
    pal = Pal("#ffffff", "#ffffff", "#f3eef2", "#c9bfc8", "#3a2e38", "#ffffff")
    return [(d, pal, {"outline": 0.035, "core": 0.75, "line_alpha": 0.55})]


@sprite("flame")
def _(c):
    pts = []
    for i in range(41):
        t = i / 40
        a = math.pi * 2 * t
        r = 0.45 + 0.0 * t
        x = math.sin(a) * r * (1 - 0.15 * math.cos(a))
        y = -math.cos(a) * r
        if y > 0:
            y = y * 2.0
            x = x * (1 - y / 2.0) ** 0.8
        pts.append((x, y - 0.35))
    d = polygon(c, pts)
    return [(d, Pal("#fffbe8", "#fff1a8", "#ffa53d", "#ff3b2a", "#4a0716", "#ff6a2a"), {"outline": 0.0, "core": 0.3})]


@sprite("laugh_eyes", 128, 64)
def _(c):
    out = []
    for sx in (-1, 1):
        pts = arc_pts(sx * 1.0, -0.45, 0.62, math.radians(25), math.radians(155), 24)
        out.append(polyline(c, pts, 0.13, 0.13))
    return [(union(*out), P("gold"), {"bevel": 0.12})]


def drop_sdf(c, cx, cy, r, tip=1.9):
    d1 = circle(c, cx, cy, r)
    tri = polygon(c, [(cx - r * 0.86, cy + r * 0.5), (cx, cy + r * tip), (cx + r * 0.86, cy + r * 0.5)])
    return sunion(d1, tri, r * 0.25)


@sprite("tear")
def _(c):
    d = drop_sdf(c, 0, -0.25, 0.48, 2.05)
    return [(d, P("blue"), {"core": 0.7})]


@sprite("sweat", 96, 128)
def _(c):
    d = drop_sdf(c, 0, -0.35, 0.52, 2.2)
    return [(d, Pal("#ffffff", "#dff9ff", "#7fdcff", "#2f8fe6", "#0b2350", "#7fdcff"), {"bevel": 0.3, "core": 0.6})]


@sprite("cloud_sad", 128, 96)
def _(c):
    d = union(circle(c, -0.62, -0.18, 0.36), circle(c, -0.15, 0.12, 0.52), circle(c, 0.45, 0.0, 0.44),
              box(c, 0, -0.32, 0.9, 0.22, 0.2))
    d = sunion(d, circle(c, 0.88, -0.2, 0.26), 0.12)
    pal = Pal("#f1f6ff", "#b9c9ea", "#7f93c4", "#4a5c94", "#141a35", "#8fb4ff")
    return [(d, pal, {"core": 0.85, "core_amt": 0.6})]


@sprite("raindrop", 48, 96)
def _(c):
    d = drop_sdf(c, 0, -0.45, 0.38, 2.6)
    return [(d, P("blue"), {"core": 0.6, "outline": 0.06})]


@sprite("stream", 64, 160)
def _(c):
    # waterfall of tears: wide wobbling ribbon that widens downward
    pts = [(0.08 * math.sin(i * 0.9), 1.6 - i * 0.14) for i in range(20)]
    rs = [0.2 + i * 0.022 for i in range(20)]
    d = None
    for i in range(19):
        dd = polyline(c, [pts[i], pts[i + 1]], rs[i], rs[i + 1])
        d = dd if d is None else union(d, dd)
    d = sunion(d, circle(c, 0.0, -1.3, 0.52), 0.2)
    pal = P("blue")
    # flowing highlight lines
    return [(d, pal, {"core": 0.5}), (polyline(c, [(-0.1, 1.3), (-0.05, 0.2), (-0.14, -1.0)], 0.04, 0.07), Pal("#ffffff", "#ffffff", "#ffffff", "#dff6ff", "#000000"), {"outline": 0, "gloss": False, "flat": True})]


def exclaim_sdf(c, cx=0.0, s=1.0, lean=0.0):
    bar = polygon(c, [(cx - 0.27 * s + lean, 0.95 * s), (cx + 0.27 * s + lean, 0.95 * s), (cx + 0.12 * s, -0.28 * s), (cx - 0.12 * s, -0.28 * s)]) - 0.05 * s
    dot = circle(c, cx, -0.66 * s, 0.19 * s)
    return union(bar, dot)


@sprite("exclaim", 80, 128)
def _(c):
    return [(exclaim_sdf(c, 0, 0.92), P("gold"), {"bevel": 0.25})]


@sprite("exclaim_violet", 80, 128)
def _(c):
    return [(exclaim_sdf(c, 0, 0.92, 0.05), P("violet"), {"bevel": 0.25})]


@sprite("bolt", 64, 128)
def _(c):
    pts = [(0.25, 0.98), (-0.32, 0.12), (0.06, 0.08), (-0.28, -0.98), (0.4, -0.02), (0.02, 0.02), (0.38, 0.98)]
    d = polygon(c, pts)
    return [(d, P("violet"), {"outline": 0.05, "bevel": 0.12, "core": 0.4})]


@sprite("question", 96, 128)
def _(c):
    pts = arc_pts(0, 0.42, 0.42, math.radians(170), math.radians(-60), 28)
    pts += bezier(pts[-1], (0.05, -0.05), (0.0, -0.3), 10)[1:]
    d = polyline(c, pts, 0.15, 0.15)
    d = union(d, circle(c, 0.0, -0.74, 0.17))
    return [(d, P("indigo"), {"bevel": 0.2})]


@sprite("bubble", 128, 112)
def _(c):
    d = union(circle(c, -0.5, 0.0, 0.42), circle(c, 0.0, 0.25, 0.5), circle(c, 0.52, 0.02, 0.42), circle(c, 0.05, -0.25, 0.45))
    d = sunion(d, box(c, 0, -0.02, 0.6, 0.3, 0.2), 0.2)
    pal = Pal("#ffffff", "#ffffff", "#eef2ff", "#b8c4ee", "#1a1f45", "#c8d4ff")
    return [(d, pal, {"core": 0.95, "core_amt": 0.4, "outline": 0.05})]


@sprite("bubble_small", 48, 48)
def _(c):
    pal = Pal("#ffffff", "#ffffff", "#eef2ff", "#b8c4ee", "#1a1f45", "#c8d4ff")
    return [(circle(c, 0, 0, 0.78), pal, {"outline": 0.14, "bevel": 0.4, "core_amt": 0.4})]


@sprite("dot", 48, 48, radius=0.45)
def _(c):
    return [(circle(c, 0, 0, 0.6), P("indigo"), {"outline": 0.0, "bevel": 0.5})]


@sprite("blush", 128, 64, strength=0.6)
def _(c):
    d = ellipse(c, 0, 0, 1.55, 0.62)
    pal = Pal("#ffe4ef", "#ff9fc4", "#ff7fb0", "#ff5f9c", "#000000", "#ff6fae")
    lines = union(*[segment(c, -0.75 + i * 0.6, -0.32, -0.45 + i * 0.6, 0.32, 0.075) for i in range(3)])
    return [(d, pal, {"outline": 0.0, "gloss": False, "core_amt": 0.0, "flat": True, "alpha": 0.75}),
            (lines, Pal("#ffffff", "#ffffff", "#ffe9f2", "#ff9fc4", "#c21e5e"), {"outline": 0.0, "gloss": False})]


@sprite("heart")
def _(c):
    return [(heart(c, 0, 0.0, 1.45), P("pink"), {"bevel": 0.3, "core": 0.65})]


@sprite("heart_red")
def _(c):
    return [(heart(c, 0, 0.0, 1.45), Pal("#fff4f4", "#ff9aa8", "#ff3d5e", "#d0103e", "#3d0414", "#ff3d5e"), {"bevel": 0.3, "core": 0.65})]


@sprite("star4", radius=0.3)
def _(c):
    # HSR four-point star with concave flanks
    d = star(c, 0, 0, 4, 0.98, 0.2, rot=0.0)
    d = sunion(d, circle(c, 0, 0, 0.26), 0.12)
    return [(d, P("gold"), {"bevel": 0.35, "core": 0.25, "outline": 0.04})]


@sprite("star5", 64, 64)
def _(c):
    return [(star(c, 0, 0, 5, 0.9, 0.42, round_=0.06), Pal("#ffffff", "#fff3a0", "#ffd23a", "#f08a12", "#4a2600", "#ffd23a"), {"bevel": 0.3})]


@sprite("gloom", 128, 128, strength=0.5)
def _(c):
    xs = [-0.7, -0.35, 0.0, 0.35, 0.7]
    lens = [0.55, 0.85, 1.0, 0.8, 0.6]
    d = union(*[polyline(c, [(x, 0.95), (x, 0.95 - 1.7 * l)], 0.075, 0.02) for x, l in zip(xs, lens)])
    pal = Pal("#ffffff", "#d9e7ff", "#8aa6e8", "#4c66b8", "#0e1838", "#8aa6ff")
    return [(d, pal, {"outline": 0.03, "gloss": False, "core": 0.8, "line_alpha": 0.6})]


@sprite("ghost", 96, 128)
def _(c):
    body = sunion(circle(c, 0, 0.3, 0.6), box(c, 0, -0.25, 0.6, 0.55, 0.0), 0.05)
    waves = union(*[circle(c, x, -0.82, 0.21) for x in (-0.42, 0.0, 0.42)])
    body = sub(body, union(*[circle(c, x, -0.84, 0.13) for x in (-0.21, 0.21)]))
    body = sub(body, box(c, 0, -1.2, 1, 0.3))
    body = union(body, inter(waves, box(c, 0, -0.8, 0.62, 0.2)))
    pal = Pal("#ffffff", "#ffffff", "#e8f2ff", "#9fb8e8", "#16224a", "#bcd6ff")
    eyes = union(ellipse(c, -0.2, 0.3, 0.09, 0.14), ellipse(c, 0.2, 0.3, 0.09, 0.14))
    mouth = ellipse(c, 0, 0.0, 0.11, 0.15)
    return [(body, pal, {"core_amt": 0.5, "alpha": 0.92}),
            (union(eyes, mouth), Pal("#3a4a7a", "#1a2244", "#1a2244", "#0a1024", "#000000"), {"outline": 0.0, "gloss": False, "flat": True})]


@sprite("eyes_narrow", 128, 64)
def _(c):
    out = []
    for sx in (-1, 1):
        lid = ellipse(c, sx * 0.85, 0.0, 0.62, 0.3)
        lid = sub(lid, box(c, sx * 0.85, 0.5, 0.8, 0.32, rot=-0.18 * sx))
        out.append(lid)
    return [(union(*out), Pal("#ffffff", "#ffffff", "#f2f0ff", "#c9c2ff", "#120c45", "#c9c2ff"), {"outline": 0.07, "core_amt": 0.3})]


@sprite("pupil", 48, 48, radius=0.3)
def _(c):
    return [(circle(c, 0, 0, 0.62), P("indigo"), {"outline": 0.1, "bevel": 0.4, "core": 0.8})]


@sprite("shades", 160, 64, radius=0.15, strength=0.6)
def _(c):
    def lens(cx):
        return polygon(c, [(cx - 0.95, 0.45), (cx + 0.95, 0.45), (cx + 0.8, -0.1), (cx + 0.3, -0.5), (cx - 0.6, -0.42), (cx - 0.95, 0.0)]) - 0.03
    d = union(lens(-1.25), lens(1.25), box(c, 0, 0.32, 0.4, 0.09), box(c, 0, 0.5, 2.4, 0.06))
    pal = Pal("#7a6cff", "#3a3355", "#1c1830", "#0c0a16", "#000000", "#ffd36b")
    glint = union(segment(c, -1.65, 0.1, -1.35, 0.38, 0.06), segment(c, 0.85, 0.1, 1.15, 0.38, 0.06))
    return [(d, pal, {"outline": 0.05, "core_amt": 0.0, "bevel": 0.2, "rim": 1.6}),
            (glint, Pal("#ffffff", "#ffffff", "#ffffff", "#ffffff", "#000000"), {"outline": 0, "gloss": False, "flat": True, "alpha": 0.85})]


@sprite("z", 96, 96)
def _(c):
    d = polyline(c, [(-0.6, 0.62), (0.6, 0.62), (-0.6, -0.62), (0.6, -0.62)], 0.16, 0.16)
    return [(d, P("indigo"), {"bevel": 0.2})]


@sprite("spiral")
def _(c):
    pts = []
    for i in range(160):
        t = i / 159
        a = t * math.pi * 2 * 2.6
        r = 0.08 + 0.85 * t
        pts.append((math.cos(a) * r, math.sin(a) * r))
    d = polyline(c, pts, 0.06, 0.11)
    return [(d, P("mint"), {"bevel": 0.1, "outline": 0.045})]


@sprite("hand", 128, 128)
def _(c):
    palm = box(c, 0.05, -0.1, 0.42, 0.48, 0.22)
    fingers = union(*[box(c, x, 0.45 + dy, 0.105, 0.32, 0.1) for x, dy in ((-0.3, -0.04), (-0.08, 0.06), (0.14, 0.04), (0.36, -0.06))])
    thumb = box(c, -0.48, -0.08, 0.13, 0.3, 0.12, rot=0.6)
    cuff = box(c, 0.05, -0.68, 0.5, 0.17, 0.08)
    hand = sunion(union(palm, fingers), thumb, 0.06)
    pal = Pal("#ffffff", "#ffffff", "#f4f1ec", "#c9c2b8", "#22202a", "#ffffff")
    creases = union(*[segment(c, x, 0.12, x, 0.3, 0.025) for x in (-0.19, 0.03, 0.25)])
    return [(hand, pal, {"core_amt": 0.2}), (cuff, Pal("#ffffff", "#ffe39a", "#ffc83a", "#c07a10", "#3a2000"), {"bevel": 0.12}),
            (creases, Pal("#b9b2a8", "#b9b2a8", "#b9b2a8", "#b9b2a8", "#000000"), {"outline": 0, "gloss": False, "flat": True})]


@sprite("impact", radius=0.25)
def _(c):
    d = star(c, 0, 0, 8, 0.98, 0.45, rot=0.2, round_=0.02)
    return [(d, Pal("#ffffff", "#fffbd0", "#ffe36b", "#ff9a2a", "#3a1a00", "#ffe36b"), {"bevel": 0.3, "core": 0.4})]


@sprite("horn", 64, 96)
def _(c):
    pts = bezier((-0.42, -0.9), (-0.45, 0.2), (0.25, 0.95), 18) + bezier((0.25, 0.95), (0.02, 0.15), (0.42, -0.9), 18)[1:]
    d = polygon(c, pts) - 0.02
    return [(d, P("violet"), {"bevel": 0.18})]


@sprite("grin", 128, 80)
def _(c):
    mouth = inter(ellipse(c, 0, 0.32, 1.3, 0.85), -ellipse(c, 0, 0.75, 1.45, 0.95))
    fang = polygon(c, [(0.28, -0.08), (0.52, -0.06), (0.4, -0.38)])
    teeth = inter(mouth, box(c, 0, -0.08, 2, 0.12))
    return [(mouth, Pal("#ff8fb8", "#6a1f4a", "#3a0d2a", "#22081a", "#12040c"), {"outline": 0.08, "gloss": False, "core_amt": 0}),
            (union(teeth, fang), Pal("#ffffff", "#ffffff", "#f6f0ff", "#c9b8e8", "#22081a"), {"outline": 0.0, "bevel": 0.08})]


@sprite("wink_eye", 64, 64)
def _(c):
    d = polyline(c, arc_pts(0, -0.55, 0.7, math.radians(35), math.radians(145), 16), 0.14)
    return [(d, P("violet"), {"bevel": 0.12})]


@sprite("smoke", strength=0.4)
def _(c):
    d = union(circle(c, -0.3, -0.1, 0.45), circle(c, 0.25, 0.1, 0.5), circle(c, 0.05, -0.35, 0.4))
    return [(d, Pal("#f0e6ff", "#c8b4f0", "#8d6cd6", "#5a3ca8", "#1a0f35", "#a07cff"), {"outline": 0.0, "core_amt": 0.3, "alpha": 0.85, "gloss": False})]


# ============================================================ white FX (tinted in game)
def fx_out(c, a):
    c.rgba = np.concatenate([np.ones(a.shape + (3,), np.float32) * a[..., None], a[..., None]], -1).astype(np.float32)
    return c.image()


def fx_glint(c):
    r = np.hypot(c.x, c.y)
    ax, ay = np.abs(c.x), np.abs(c.y)
    rays = np.exp(-(ay / (0.018 + 0.05 * (1 - np.clip(ax, 0, 1)) ** 3)) ** 2) * (1 - np.clip(ax, 0, 1)) ** 1.4
    rays = np.maximum(rays, np.exp(-(ax / (0.018 + 0.05 * (1 - np.clip(ay, 0, 1)) ** 3)) ** 2) * (1 - np.clip(ay, 0, 1)) ** 1.4)
    diag = np.exp(-(np.abs(c.x - c.y) / 0.03) ** 2) * np.clip(1 - r / 0.45, 0, 1) + np.exp(-(np.abs(c.x + c.y) / 0.03) ** 2) * np.clip(1 - r / 0.45, 0, 1)
    core = np.exp(-(r / 0.07) ** 2) + 0.5 * np.exp(-(r / 0.22) ** 2)
    return np.clip(rays + core + diag * 0.35, 0, 1)


def fx_orb(c):
    r = np.hypot(c.x, c.y)
    return np.clip(np.exp(-(r / 0.42) ** 2) * 1.1 + np.exp(-(r / 0.12) ** 2) * 0.6, 0, 1) * smooth(1.0, 0.85, r)


def fx_ring(c):
    r = np.hypot(c.x, c.y)
    return np.clip(np.exp(-((r - 0.86) / 0.03) ** 2) + 0.35 * np.exp(-((r - 0.83) / 0.1) ** 2), 0, 1)


def fx_ring_dash(c):
    r = np.hypot(c.x, c.y)
    a = np.arctan2(c.y, c.x)
    band = np.exp(-((r - 0.84) / 0.022) ** 2)
    seg = smooth(0.0, 0.02, np.cos(a * 12) + 0.35)
    ticks = np.exp(-((r - 0.94) / 0.03) ** 2) * smooth(0.97, 0.995, np.cos(a * 4))
    inner = np.exp(-((r - 0.72) / 0.012) ** 2) * 0.6 * smooth(0.0, 0.05, np.cos(a * 3 + 0.5) + 0.6)
    diamonds = np.zeros_like(r)
    for k in range(4):
        aa = k * math.pi / 2 + math.pi / 4
        dx, dy = c.x - math.cos(aa) * 0.84, c.y - math.sin(aa) * 0.84
        diamonds = np.maximum(diamonds, smooth(0.06, 0.04, np.abs(dx) + np.abs(dy)))
    return np.clip(band * seg + ticks + inner + diamonds, 0, 1)


def fx_shard(c):
    d = np.abs(c.x) / 0.32 + np.abs(c.y) / 0.95
    edge = smooth(1.0, 0.92, d)
    core = np.exp(-((np.abs(c.x) / 0.08) ** 2)) * (1 - np.clip(np.abs(c.y), 0, 1))
    return np.clip(edge * 0.75 + core * 0.6, 0, 1)


def fx_spark(c):
    return np.clip(np.exp(-(c.x / 0.06) ** 2) * np.clip(1 - np.abs(c.y), 0, 1) ** 1.5 * 1.3, 0, 1)


def fx_smoke(c):
    r = np.hypot(c.x, c.y)
    n = 0.5 + 0.5 * np.sin(c.x * 7 + np.sin(c.y * 5) * 2) * np.cos(c.y * 6 - c.x * 3)
    return np.clip(np.exp(-(r / 0.55) ** 2) * (0.7 + 0.3 * n), 0, 1) * smooth(1.0, 0.8, r)


def fx_hex(c):
    ax, ay = np.abs(c.x), np.abs(c.y)
    d = np.maximum(ax * 0.866 + ay * 0.5, ay) - 0.8
    return np.clip(np.exp(-(d / 0.025) ** 2) + 0.18 * smooth(0, -0.1, d), 0, 1)


def fx_burst(c):
    r = np.hypot(c.x, c.y)
    a = np.arctan2(c.y, c.x)
    spikes = np.abs(np.cos(a * 8)) ** 18 * 0.9 + np.abs(np.cos(a * 8 + math.pi / 2)) ** 30 * 0.5
    return np.clip(spikes * (1 - r) ** 1.2 * smooth(0.05, 0.2, r) + np.exp(-(r / 0.25) ** 2) * 0.7, 0, 1) * smooth(1.0, 0.9, r)


FX = {"glint": fx_glint, "orb": fx_orb, "ring": fx_ring, "ring_dash": fx_ring_dash, "shard": fx_shard,
      "spark": fx_spark, "smoke": fx_smoke, "hex": fx_hex, "burst": fx_burst}


def render_sprite(name):
    fn, w, h, glow, radius, strength = SPRITES[name]
    c = Canvas(w, h, zoom=1.14)
    mask = np.zeros(c.x.shape, np.float32)
    glow_col = None
    for d, pal, opt in fn(c):
        opt = dict(opt)
        alpha = opt.pop("alpha", 1.0)
        before = c.rgba.copy()
        m = shade(c, d, pal, **opt)
        if alpha < 1:
            c.rgba = before * (1 - alpha) + c.rgba * alpha
        mask = np.maximum(mask, m * alpha)
        if glow_col is None:
            glow_col = pal.glow
    img = c.image()
    g = glow_image(c, mask, glow_col, radius, strength) if glow else None
    return img, g


def main(only=None):
    os.makedirs(os.path.join(TEX, "emote"), exist_ok=True)
    os.makedirs(os.path.join(TEX, "fx"), exist_ok=True)
    for name in SPRITES:
        if only and name not in only:
            continue
        img, g = render_sprite(name)
        img.save(os.path.join(TEX, "emote", name + ".png"), optimize=True)
        if g is not None:
            g.save(os.path.join(TEX, "emote", name + "_glow.png"), optimize=True)
        print("sprite", name, img.size)
    for name, fn in FX.items():
        if only and name not in only:
            continue
        c = Canvas(128, 128)
        fx_out(c, fn(c)).save(os.path.join(TEX, "fx", name + ".png"), optimize=True)
        print("fx", name)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
