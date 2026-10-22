"""Signed-distance drawing kit for the HSR-inspired emote sprites.

Every sprite is described as an SDF on a supersampled grid and then shaded by one
shared function, so all 20 emotes get the same light direction, rim, core glow,
outline and bloom. Coordinates: y up, the shorter canvas side spans [-1, 1].
"""
import math
import numpy as np
from PIL import Image, ImageFilter

SS = 4  # supersampling factor


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        W, H = w * SS, h * SS
        s = min(W, H) / 2.0
        xs = (np.arange(W) + 0.5 - W / 2.0) / s
        ys = (H / 2.0 - (np.arange(H) + 0.5)) / s
        self.x, self.y = np.meshgrid(xs, ys)
        self.px = 1.0 / s  # one supersampled pixel in sdf units
        self.rgba = np.zeros((H, W, 4), np.float32)  # premultiplied

    # --- compositing -------------------------------------------------------
    def over(self, rgb, a):
        a = np.clip(a, 0, 1)[..., None]
        src = np.concatenate([np.asarray(rgb, np.float32) * a, a], -1) if np.ndim(rgb) == 3 else \
            np.concatenate([np.broadcast_to(np.asarray(rgb, np.float32), a.shape[:2] + (3,)) * a, a], -1)
        self.rgba = src + self.rgba * (1 - a)

    def image(self):
        a = self.rgba[..., 3:4]
        rgb = np.where(a > 1e-5, self.rgba[..., :3] / np.maximum(a, 1e-5), 0)
        out = np.concatenate([rgb, a], -1)
        img = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
        # premultiplied downsample avoids dark fringes
        pm = Image.fromarray((np.clip(self.rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
        pm = pm.resize((self.w, self.h), Image.LANCZOS)
        arr = np.asarray(pm).astype(np.float32) / 255
        a = arr[..., 3:4]
        rgb = np.where(a > 1e-3, arr[..., :3] / np.maximum(a, 1e-3), 0)
        return Image.fromarray((np.clip(np.concatenate([rgb, a], -1), 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def hexc(h, a=1.0):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def mix(a, b, t):
    t = np.asarray(t, np.float32)
    if t.ndim:
        t = t[..., None]
    return np.asarray(a, np.float32) * (1 - t) + np.asarray(b, np.float32) * t


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# --- primitives -------------------------------------------------------------
def circle(c, cx, cy, r):
    return np.hypot(c.x - cx, c.y - cy) - r


def ellipse(c, cx, cy, rx, ry, rot=0.0):
    x, y = rotate(c.x - cx, c.y - cy, -rot)
    k = np.hypot(x / rx, y / ry)
    return (k - 1) * min(rx, ry)


def rotate(x, y, a):
    ca, sa = math.cos(a), math.sin(a)
    return x * ca - y * sa, x * sa + y * ca


def box(c, cx, cy, hw, hh, r=0.0, rot=0.0):
    x, y = rotate(c.x - cx, c.y - cy, -rot)
    qx, qy = np.abs(x) - hw + r, np.abs(y) - hh + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def segment(c, ax, ay, bx, by, r):
    px, py = c.x - ax, c.y - ay
    dx, dy = bx - ax, by - ay
    h = np.clip((px * dx + py * dy) / (dx * dx + dy * dy + 1e-9), 0, 1)
    return np.hypot(px - dx * h, py - dy * h) - r


def polyline(c, pts, r0, r1=None):
    """Stroke through points; radius tapers linearly from r0 to r1."""
    r1 = r0 if r1 is None else r1
    n = len(pts) - 1
    d = np.full(c.x.shape, 1e9, np.float32)
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        px, py = c.x - ax, c.y - ay
        dx, dy = bx - ax, by - ay
        h = np.clip((px * dx + py * dy) / (dx * dx + dy * dy + 1e-9), 0, 1)
        t = (i + h) / n
        d = np.minimum(d, np.hypot(px - dx * h, py - dy * h) - (r0 + (r1 - r0) * t))
    return d


def bezier(p0, p1, p2, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def arc_pts(cx, cy, r, a0, a1, n=32):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def polygon(c, pts):
    pts = np.asarray(pts, np.float32)
    d = np.full(c.x.shape, 1e9, np.float32)
    s = np.ones(c.x.shape, np.float32)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[i - 1]
        ex, ey = b[0] - a[0], b[1] - a[1]
        wx, wy = c.x - a[0], c.y - a[1]
        h = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        d = np.minimum(d, (wx - ex * h) ** 2 + (wy - ey * h) ** 2)
        c1 = c.y >= a[1]
        c2 = c.y < b[1]
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return s * np.sqrt(d)


def star(c, cx, cy, n, r_out, r_in, rot=0.0, round_=0.0):
    pts = []
    for i in range(n * 2):
        a = rot + math.pi / 2 + i * math.pi / n
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return polygon(c, pts) - round_


def heart(c, cx, cy, size, rot=0.0):
    # Inigo Quilez heart SDF, y-up, origin at the bottom tip; recentred.
    x, y = rotate(c.x - cx, c.y - cy, -rot)
    x = np.abs(x) / size
    y = y / size + 0.55
    d1 = np.hypot(x - 0.25, y - 0.75) - math.sqrt(2) / 4
    m = 0.5 * np.maximum(x + y, 0)
    d2 = np.sqrt(np.minimum((x - 0.0) ** 2 + (y - 1.0) ** 2, (x - m) ** 2 + (y - m) ** 2)) * np.sign(x - y)
    return np.where(y + x > 1.0, d1, d2) * size


def union(*ds):
    out = ds[0]
    for d in ds[1:]:
        out = np.minimum(out, d)
    return out


def sunion(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def sub(a, b):
    return np.maximum(a, -b)


def inter(a, b):
    return np.maximum(a, b)


# --- shading ----------------------------------------------------------------
class Pal:
    """core: white-hot centre, light/mid: body gradient, edge: saturated rim, line: outline."""

    def __init__(self, core, light, mid, edge, line, glow=None):
        self.core, self.light, self.mid, self.edge, self.line = map(hexc, (core, light, mid, edge, line))
        self.glow = hexc(glow) if glow else self.mid


PAL = {
    "fire": Pal("#fffbe8", "#ffd36b", "#ff6a3d", "#e0213b", "#4a0716", "#ff4a2a"),
    "ice": Pal("#ffffff", "#c9f6ff", "#5fd2ff", "#2a7de0", "#0b2350", "#58c8ff"),
    "imaginary": Pal("#fffff2", "#ffeaa0", "#ffc83a", "#e08a12", "#4a2600", "#ffbe3a"),
    "lightning": Pal("#fff6ff", "#f1c6ff", "#c06cff", "#7a2ee0", "#24063f", "#b45cff"),
    "quantum": Pal("#f6f4ff", "#c9c2ff", "#7d74ff", "#4636d6", "#120c45", "#6f62ff"),
    "wind": Pal("#f2fff9", "#b8ffe2", "#3fe0a6", "#119a7a", "#03302a", "#3ee6aa"),
    "harmony": Pal("#fff5fa", "#ffc3dc", "#ff6fae", "#e02f7c", "#4a0a2a", "#ff5ea8"),
    "physical": Pal("#ffffff", "#f4f2ee", "#cfcac2", "#8f8a84", "#1f1d22", "#ffffff"),
    "void": Pal("#d8d4ff", "#4a4466", "#24203a", "#120f22", "#06050c", "#7d74ff"),
}


def gaussian(arr, radius_px):
    img = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), "L")
    img = img.filter(ImageFilter.GaussianBlur(radius_px))
    return np.asarray(img).astype(np.float32) / 255


def shade(c, d, pal, outline=0.045, bevel=0.22, core=0.55, light=(-0.55, 0.85), gloss=True,
          rim=1.0, core_amt=1.0, line_alpha=0.92, flat=False):
    """Paint one HSR-style glossy energy shape into the canvas."""
    aa = c.px * 1.2
    # outline (outside the shape)
    if outline > 0:
        a_line = smooth(outline + aa, outline - aa, d) * line_alpha
        c.over(pal.line, a_line)
    fill = smooth(aa, -aa, d)
    depth = np.clip(-d / bevel, 0, 1)
    gy, gx = np.gradient(d)
    n = np.hypot(gx, gy) + 1e-9
    nx, ny = -gx / n, gy / n  # outward normal (rows go down so flip y)
    nx, ny = -nx, -ny
    lit = np.clip(nx * light[0] + ny * light[1], -1, 1)
    # vertical body gradient light->mid, edges toward saturated rim
    vy = np.clip((c.y - c.y.min()) / (c.y.max() - c.y.min()), 0, 1)
    body = mix(pal.mid, pal.light, smooth(0.15, 0.95, vy))
    col = mix(pal.edge, body, smooth(0.0, 0.55, depth))
    if not flat:
        col = mix(col, pal.core, smooth(core, 1.0, depth) * core_amt)
        # rim light on the lit side, rim shadow on the other
        band = smooth(0.0, 0.08, depth) * (1 - smooth(0.12, 0.3, depth))
        col = mix(col, pal.core, np.clip(lit, 0, 1) * band * 0.85 * rim)
        col = mix(col, pal.edge * 0.75, np.clip(-lit, 0, 1) * band * 0.45 * rim)
    c.over(col, fill)
    if gloss and not flat:
        # specular streak: offset copy of the shape clipped inside
        shift = bevel * 0.55
        dd = np.roll(np.roll(d, int(shift / c.px * 0.6), axis=0), int(shift / c.px * 0.45), axis=1)
        spec = smooth(aa, -aa, np.maximum(d + bevel * 0.35, -(dd + bevel * 0.1) * 0 + (d - dd) * 0 + dd + bevel * 0.55))
        c.over(pal.core, spec * 0.55)
    return fill


def glow_image(c, mask, pal_glow, radius=0.18, strength=1.0, core=0.0):
    """Additive bloom texture (straight alpha) built from a coverage mask."""
    r_px = radius / c.px
    g = gaussian(mask, r_px) * 1.6 + gaussian(mask, r_px * 0.35) * 0.9 * core
    g = np.clip(g * strength, 0, 1)
    out = Canvas(c.w, c.h)
    out.rgba = np.concatenate([np.broadcast_to(pal_glow, g.shape + (3,)) * g[..., None], g[..., None]], -1).astype(np.float32)
    return out.image()


def trim_save(img, path):
    img.save(path, optimize=True)
