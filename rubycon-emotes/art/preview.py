"""Software renderer for emote previews: GIFs, contact sheets and menu icons.

Mirrors the in-game rules: the head writes depth, emote quads test against it but do not
write depth, 'add' quads use SRC_ALPHA/ONE blending, everything else is alpha-over.
"""
import json
import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

import anim

ROOT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ROOT, "..", "mod", "src", "main", "resources", "assets", "rubycon_emotes")
TEX = os.path.join(RES, "textures")
_tex_cache = {}


def load_tex(name):
    if name not in _tex_cache:
        p = os.path.join(TEX, name + ".png")
        if not os.path.exists(p):
            _tex_cache[name] = None
        else:
            _tex_cache[name] = Image.open(p).convert("RGBA")
    return _tex_cache[name]


# ------------------------------------------------------------------ skin
def make_skin():
    """Original 64x64 skin used only for previews and Blockbench files (no Mojang assets)."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = img.load()
    skin, skin_d = (236, 196, 164), (214, 168, 136)
    hair, hair_d, hair_l = (58, 44, 66), (40, 30, 48), (88, 70, 102)
    eye_w, eye = (250, 250, 255), (92, 150, 255)

    def face(ox, oy, fill):
        for y in range(8):
            for x in range(8):
                px[ox + x, oy + y] = fill(x, y)
    # head: top(8,0) bottom(16,0) right(0,8) front(8,8) left(16,8) back(24,8)
    face(8, 0, lambda x, y: hair_l if (x + y) % 5 == 0 else hair)
    face(16, 0, lambda x, y: skin_d)

    def front(x, y):
        if y < 2 or (y == 2 and x in (0, 1, 5, 6, 7)) or (y == 3 and x in (0, 7)):
            return hair if (x * 3 + y) % 4 else hair_d
        if y == 4 and x in (1, 5):
            return eye_w
        if y == 4 and x in (2, 6):
            return eye
        if y == 6 and x in (3, 4):
            return (196, 120, 110)
        return skin
    face(8, 8, front)

    def side(x, y):
        if y < 3 or (y < 6 and x > 4):
            return hair if (x + y) % 3 else hair_d
        return skin_d if x < 2 else skin
    face(0, 8, side)
    face(16, 8, lambda x, y: side(7 - x, y))
    face(24, 8, lambda x, y: hair if (x + 2 * y) % 5 else hair_d)
    return img


SKIN = make_skin()


def skin_face(name):
    uv = {"top": (8, 0), "front": (8, 8), "right": (0, 8), "left": (16, 8), "back": (24, 8)}[name]
    return SKIN.crop((uv[0], uv[1], uv[0] + 8, uv[1] + 8))


# ------------------------------------------------------------------ camera
class Cam:
    def __init__(self, size, scale, cy, yaw=24.0, pitch=10.0):
        self.size, self.S, self.cy = size, scale, cy
        self.cyaw, self.syaw = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        self.cp, self.sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def view(self, p):
        x, y, z = p
        vx = x * self.cyaw + z * self.syaw
        vz = -x * self.syaw + z * self.cyaw
        vy = y * self.cp - vz * self.sp
        vz2 = vz * self.cp + y * self.sp
        return vx, vy, vz2

    def screen(self, v):
        return self.size[0] / 2 + v[0] * self.S, self.cy - v[1] * self.S, v[2]


def _affine_draw(src, p00, p10, p01, size, flip=False, nearest=False):
    """Warp src so its (0,0),(1,0),(0,1) corners land on p00,p10,p01 (screen px)."""
    if flip:
        src = src.transpose(Image.FLIP_LEFT_RIGHT)
    w, h = src.size
    ax, ay = (p10[0] - p00[0]) / w, (p10[1] - p00[1]) / w
    bx, by = (p01[0] - p00[0]) / h, (p01[1] - p00[1]) / h
    det = ax * by - ay * bx
    if abs(det) < 1e-9:
        return None
    ia, ib, ic, id_ = by / det, -bx / det, -ay / det, ax / det
    tx = -(ia * p00[0] + ib * p00[1])
    ty = -(ic * p00[0] + id_ * p00[1])
    out = src.transform(size, Image.AFFINE, (ia, ib, tx, ic, id_, ty),
                        resample=Image.NEAREST if nearest else Image.BILINEAR)
    return np.asarray(out).astype(np.float32) / 255


def _depth_plane(s00, s10, s01, size):
    """per-pixel depth of the plane through three screen points (x, y, depth)."""
    ax, ay, az = s10[0] - s00[0], s10[1] - s00[1], s10[2] - s00[2]
    bx, by, bz = s01[0] - s00[0], s01[1] - s00[1], s01[2] - s00[2]
    det = ax * by - ay * bx
    W, H = size
    if abs(det) < 1e-9:
        return np.full((H, W), s00[2], np.float32)
    X, Y = np.meshgrid(np.arange(W) + 0.5 - s00[0], np.arange(H) + 0.5 - s00[1])
    u = (X * by - Y * bx) / det
    v = (-X * ay + Y * ax) / det
    return (s00[2] + u * az + v * bz).astype(np.float32)


class Frame:
    def __init__(self, size, bg=None):
        W, H = size
        self.size = size
        self.rgb = np.zeros((H, W, 3), np.float32) if bg is None else bg.copy()
        self.alpha = np.zeros((H, W), np.float32) if bg is None else np.ones((H, W), np.float32)
        self.z = np.full((H, W), -1e9, np.float32)


def draw_head(fr, cam, helmet=False):
    faces = {
        "front": ((-4, 4, 4), (4, 4, 4), (-4, -4, 4)),
        "top": ((-4, 4, -4), (4, 4, -4), (-4, 4, 4)),
        "left": ((4, 4, 4), (4, 4, -4), (4, -4, 4)),     # viewer's right side of the face
        "right": ((-4, 4, -4), (-4, 4, 4), (-4, -4, -4)),
        "back": ((4, 4, -4), (-4, 4, -4), (4, -4, -4)),
    }
    for name, (a, b, c) in faces.items():
        k = 1.12 if helmet else 1.0
        a, b, c = [tuple(v * k for v in p) for p in (a, b, c)]
        sa, sb, sc = (cam.screen(cam.view(p)) for p in (a, b, c))
        # back-face cull via screen-space winding
        cross = (sb[0] - sa[0]) * (sc[1] - sa[1]) - (sb[1] - sa[1]) * (sc[0] - sa[0])
        if cross <= 0:
            continue
        tex = skin_face(name)
        if helmet:
            tex = Image.new("RGBA", (8, 8), (150, 158, 170, 255))
            d = ImageDraw.Draw(tex)
            if name == "front":
                d.rectangle((1, 3, 6, 4), fill=(30, 34, 44, 255))
            d.line((0, 0, 7, 0), fill=(200, 206, 216, 255))
        arr = _affine_draw(tex, sa, sb, sc, fr.size, nearest=True)
        if arr is None:
            continue
        shade = {"front": 1.0, "top": 1.08, "left": 0.82, "right": 0.82, "back": 0.7}[name]
        dz = _depth_plane(sa, sb, sc, fr.size)
        m = (arr[..., 3] > 0.5) & (dz > fr.z)
        fr.rgb[m] = np.clip(arr[..., :3][m] * shade, 0, 1)
        fr.alpha[m] = 1
        fr.z[m] = dz[m]


def draw_quad(fr, cam, q):
    tex = load_tex(q["tex"])
    if tex is None:
        return
    w, h = q["w"], q["h"]
    pvx, pvy = q["pivot"]
    r = math.radians(q["rot"])
    cr, sr = math.cos(r), math.sin(r)
    corners = []
    for (cx, cy) in ((-0.5, 0.5), (0.5, 0.5), (-0.5, -0.5)):  # top-left, top-right, bottom-left
        lx, ly = (cx - pvx) * w, (cy - pvy) * h
        corners.append((lx * cr - ly * sr, lx * sr + ly * cr))
    if q["billboard"]:
        v = cam.view(q["pos"])
        base = (v[0] + q["off"][0], v[1] + q["off"][1], v[2] + anim.BILLBOARD_BIAS)
        pts = [cam.screen((base[0] + cx, base[1] + cy, base[2])) for cx, cy in corners]
    else:
        p = q["pos"]
        pts = [cam.screen(cam.view((p[0] + cx, p[1] + cy, p[2]))) for cx, cy in corners]
    arr = _affine_draw(tex, pts[0], pts[1], pts[2], fr.size, flip=q["flip"])
    if arr is None:
        return
    dz = _depth_plane(pts[0], pts[1], pts[2], fr.size)
    vis = (dz >= fr.z - 0.05).astype(np.float32)
    col = np.array(q["color"][:3], np.float32)
    a = arr[..., 3] * q["alpha"] * q["color"][3] * vis
    rgb = arr[..., :3] * col
    if q["blend"] == "add":
        fr.rgb += rgb * a[..., None]
        fr.alpha = np.clip(fr.alpha + a * rgb.max(-1) * 0.8, 0, 1)
    else:
        fr.rgb = fr.rgb * (1 - a[..., None]) + rgb * a[..., None]
        fr.alpha = fr.alpha * (1 - a) + a


def background(size):
    W, H = size
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([0.13, 0.15, 0.24]), np.array([0.30, 0.33, 0.43])
    bg = np.broadcast_to(top * (1 - y) + bot * y, (H, W, 3)).copy()
    rng = np.random.default_rng(3)
    for _ in range(40):  # faint starfield
        x0, y0 = rng.integers(0, W), rng.integers(0, H)
        bg[y0, x0] += rng.uniform(0.1, 0.35)
    return bg.astype(np.float32)


def render(em, t, size=(256, 256), yaw=24.0, helmet=False, head=True, bg=True, scale=8.5, cy=None, opts=None):
    cam = Cam(size, scale, cy if cy is not None else size[1] * 0.64, yaw)
    fr = Frame(size, background(size) if bg else None)
    if head:
        draw_head(fr, cam, helmet)
    o = opts or anim.Opts(helmet=helmet)
    for q in anim.evaluate(em, t, o):
        draw_quad(fr, cam, q)
    return fr


def to_image(fr):
    rgb = np.clip(fr.rgb, 0, 1)
    if fr.alpha is None:
        return Image.fromarray((rgb * 255).astype(np.uint8))
    a = np.clip(fr.alpha, 0, 1)
    return Image.fromarray((np.concatenate([rgb, a[..., None]], -1) * 255 + 0.5).astype(np.uint8), "RGBA")


def load_emotes():
    d = os.path.join(RES, "emotes")
    order = json.load(open(os.path.join(ROOT, "..", "mod", "src", "main", "resources", "rubycon_emotes", "index.json"), encoding="utf-8"))
    return [(e["id"], json.load(open(os.path.join(d, e["id"] + ".json"), encoding="utf-8"))) for e in order["emotes"]]


def gif(em, path, fps=20, size=(256, 256)):
    n = int(em["duration"] * fps)
    frames = [to_image(render(em, i / fps, size)).convert("RGB") for i in range(n)]
    frames += [frames[-1]] * 4
    pal = frames[len(frames) // 3].quantize(256, method=Image.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=True)


def icon(em, path, px=64):
    """Sticker-style icon: head plus effect, auto-cropped so the emote fills the tile."""
    big = 320
    t = em.get("icon_time", 1.0)
    kw = dict(yaw=14, bg=False, scale=7.0, cy=big * 0.62)
    # crop box comes from head + solid parts only; particles may spill over the edge
    parts = dict(em, layers=[l for l in em["layers"] if "mode" not in l])
    a = np.asarray(to_image(render(parts, t, (big, big), **kw)))[..., 3]
    full = dict(em, layers=[l for l in em["layers"] if not ("mode" in l and l["tex"].startswith("fx/"))])
    img = to_image(render(full, t, (big, big), **kw))
    ys, xs = np.nonzero(a > 150)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        side = int(max(x1 - x0, y1 - y0) * 1.1) + 4
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        img = img.crop((cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side))
    img = img.resize((px, px), Image.LANCZOS)
    img.save(path, optimize=True)


def sheet(emotes, path, times=(0.15, 0.4, 1.0, 2.0, 3.0), size=(200, 200)):
    W = size[0] * len(times)
    out = Image.new("RGB", (W, size[1] * len(emotes)))
    for r, (eid, em) in enumerate(emotes):
        for c, t in enumerate(times):
            im = to_image(render(em, min(t, em["duration"] - 0.05), size, scale=6.8)).convert("RGB")
            ImageDraw.Draw(im).text((4, 3), f"{eid} t={t}", fill=(255, 120, 120))
            out.paste(im, (c * size[0], r * size[1]))
    out.save(path)


if __name__ == "__main__":
    cmd = sys.argv[1]
    ems = load_emotes()
    sel = [e for e in ems if len(sys.argv) < 4 or e[0] in sys.argv[3].split(",")]
    if cmd == "sheet":
        sheet(sel, sys.argv[2])
    elif cmd == "gif":
        os.makedirs(sys.argv[2], exist_ok=True)
        for eid, em in sel:
            gif(em, os.path.join(sys.argv[2], eid + ".gif"))
            print("gif", eid)
    elif cmd == "icons":
        os.makedirs(os.path.join(TEX, "icon"), exist_ok=True)
        for eid, em in sel:
            icon(em, os.path.join(TEX, "icon", eid + ".png"))
            print("icon", eid)
