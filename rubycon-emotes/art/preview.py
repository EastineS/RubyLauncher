"""Software renderer for emote previews: overview sheets, GIFs and menu icons.

Draws a full player model (original 64x64 skin, standard player UV layout) and the emote quads with
the same rules as the game: the body writes depth, emote quads test against it without writing,
'add' quads use additive blending, everything else is alpha-over. Icons are the emblem itself.
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
        _tex_cache[name] = Image.open(p).convert("RGBA") if os.path.exists(p) else None
    return _tex_cache[name]


# ------------------------------------------------------------------ player model
# (name, min corner, max corner, skin uv) in pixels, head centre at the origin, y up, +z = facing the viewer.
BOXES = [
    ("head", (-4, -4, -4), (4, 4, 4), (0, 0)),
    ("body", (-4, -16, -2), (4, -4, 2), (16, 16)),
    ("right_arm", (-8, -16, -2), (-4, -4, 2), (40, 16)),
    ("left_arm", (4, -16, -2), (8, -4, 2), (32, 48)),
    ("right_leg", (-4, -28, -2), (0, -16, 2), (0, 16)),
    ("left_leg", (0, -28, -2), (4, -16, 2), (16, 48)),
]


def uv_faces(u, v, w, h, d):
    """Standard Minecraft box UV: face -> (x, y, width, height) in the skin."""
    return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d), "right": (u, v + d, d, h),
            "front": (u + d, v + d, w, h), "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h)}


def make_skin():
    """Original skin (no Mojang assets): dark-haired traveller in a navy coat with gold trim."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = img.load()
    C = dict(skin=(238, 204, 178), skin_d=(220, 182, 156), hair=(46, 40, 66), hair_d=(32, 28, 48), hair_l=(78, 70, 110),
             eye=(86, 150, 236), eye_w=(250, 250, 255), lip=(206, 140, 130), coat=(38, 48, 86), coat_d=(28, 36, 66),
             coat_l=(56, 70, 120), gold=(226, 190, 112), shirt=(236, 232, 224), pants=(40, 38, 50), boot=(70, 50, 44),
             boot_d=(48, 34, 30), belt=(84, 58, 44))

    def paint(rect, fn):
        x0, y0, w, h = rect
        for y in range(h):
            for x in range(w):
                px[x0 + x, y0 + y] = fn(x, y, w, h) + (255,)

    head = uv_faces(0, 0, 8, 8, 8)
    paint(head["top"], lambda x, y, w, h: C["hair_l"] if (x + 2 * y) % 7 == 0 else C["hair"])
    paint(head["bottom"], lambda x, y, w, h: C["skin_d"])

    def face(x, y, w, h):
        if y < 2 or (y == 2 and x not in (3, 4)) or (y == 3 and x in (0, 7)):
            return C["hair_l"] if (x + y) % 4 == 1 else C["hair"]
        if y == 4 and x in (1, 6):
            return C["eye_w"]
        if y == 4 and x in (2, 5):
            return C["eye"]
        if y == 3 and x in (1, 2, 5, 6):
            return C["skin_d"]
        if y == 6 and x in (3, 4):
            return C["lip"]
        return C["skin"]
    paint(head["front"], face)
    side = lambda x, y, w, h: (C["hair"] if (x + y) % 3 else C["hair_d"]) if y < 3 or (y < 7 and x < 3) else C["skin_d"]
    paint(head["right"], side)
    paint(head["left"], lambda x, y, w, h: side(7 - x, y, w, h))
    paint(head["back"], lambda x, y, w, h: C["hair_d"] if (x * 2 + y) % 5 == 0 else C["hair"])

    def coat_front(x, y, w, h):
        if y < 2 and 2 <= x <= 5 and abs(x - 3.5) <= 2 - y:
            return C["shirt"]
        if y == 7:
            return C["gold"] if x in (3, 4) else C["belt"]
        if x in (3, 4) and y >= 2:
            return C["gold"] if x == 4 else C["coat_d"]
        if y == 11:
            return C["gold"]
        return C["coat_l"] if x in (1, 6) and y < 7 else C["coat"]
    body = uv_faces(16, 16, 8, 12, 4)
    paint(body["front"], coat_front)
    for f in ("back", "right", "left", "top", "bottom"):
        paint(body[f], lambda x, y, w, h: C["belt"] if y == 7 and f != "top" and f != "bottom" else C["coat_d"] if f == "back" and x in (3, 4) else C["coat"])

    def arm(x, y, w, h):
        if h == 4:
            return C["coat"] if y < 2 else C["skin"]
        if y >= 10:
            return C["skin"]
        if y == 9:
            return C["gold"]
        return C["coat_l"] if x == 1 and y < 8 else C["coat"]
    for u, v in ((40, 16), (32, 48)):
        for f, r in uv_faces(u, v, 4, 12, 4).items():
            paint(r, arm)

    def leg(x, y, w, h):
        if h == 4:
            return C["pants"] if y < 2 else C["boot_d"]
        if y >= 9:
            return C["boot"] if y < 11 else C["boot_d"]
        return C["pants"]
    for u, v in ((0, 16), (16, 48)):
        for f, r in uv_faces(u, v, 4, 12, 4).items():
            paint(r, leg)
    return img


SKIN = make_skin()


def face_corners(lo, hi, face):
    """TL, TR, BL corners of a face as seen from outside the box."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    return {
        "front": ((x0, y1, z1), (x1, y1, z1), (x0, y0, z1)),
        "back": ((x1, y1, z0), (x0, y1, z0), (x1, y0, z0)),
        "right": ((x0, y1, z0), (x0, y1, z1), (x0, y0, z0)),
        "left": ((x1, y1, z1), (x1, y1, z0), (x1, y0, z1)),
        "top": ((x0, y1, z0), (x1, y1, z0), (x0, y1, z1)),
        "bottom": ((x0, y0, z1), (x1, y0, z1), (x0, y0, z0)),
    }[face]


SHADE = {"front": 1.0, "top": 1.08, "left": 0.84, "right": 0.84, "back": 0.72, "bottom": 0.6}


# ------------------------------------------------------------------ camera
class Cam:
    def __init__(self, size, scale, cx, cy, yaw=24.0, pitch=10.0):
        self.size, self.S, self.cx, self.cy = size, scale, cx, cy
        self.cyaw, self.syaw = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        self.cp, self.sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def view(self, p):
        x, y, z = p
        vx = x * self.cyaw + z * self.syaw
        vz = -x * self.syaw + z * self.cyaw
        return vx, y * self.cp - vz * self.sp, vz * self.cp + y * self.sp

    def screen(self, v):
        return self.cx + v[0] * self.S, self.cy - v[1] * self.S, v[2]


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
    out = src.transform(size, Image.AFFINE, (ia, ib, tx, ic, id_, ty), resample=Image.NEAREST if nearest else Image.BILINEAR)
    return np.asarray(out).astype(np.float32) / 255


def _depth_plane(s00, s10, s01, size):
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


def draw_player(fr, cam):
    for name, lo, hi, (u, v) in BOXES:
        w, h, d = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
        for face, rect in uv_faces(u, v, w, h, d).items():
            a, b, c = face_corners(lo, hi, face)
            sa, sb, sc = (cam.screen(cam.view(p)) for p in (a, b, c))
            tex = SKIN.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))
            arr = _affine_draw(tex, sa, sb, sc, fr.size, nearest=True)
            if arr is None:
                continue
            dz = _depth_plane(sa, sb, sc, fr.size)
            m = (arr[..., 3] > 0.5) & (dz > fr.z)
            fr.rgb[m] = np.clip(arr[..., :3][m] * SHADE[face], 0, 1)
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
    for (cx, cy) in ((-0.5, 0.5), (0.5, 0.5), (-0.5, -0.5)):
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
    """Soft dusk gradient with a faint ground line, so bright and dark effects both read."""
    W, H = size
    y = np.linspace(0, 1, H)[:, None, None]
    top, mid, bot = np.array([0.36, 0.45, 0.62]), np.array([0.62, 0.66, 0.74]), np.array([0.42, 0.44, 0.48])
    bg = np.where(y < 0.75, top * (1 - y / 0.75) + mid * (y / 0.75), mid * (1 - (y - 0.75) / 0.25) + bot * ((y - 0.75) / 0.25))
    return np.broadcast_to(bg, (H, W, 3)).astype(np.float32).copy()


def render(em, t, size=(200, 200), yaw=24.0, scale=5.6, cx=None, cy=None, bg=True, opts=None, player=True):
    cam = Cam(size, scale, cx if cx is not None else size[0] * 0.26, cy if cy is not None else size[1] * 0.42, yaw)
    fr = Frame(size, background(size) if bg else None)
    if player:
        draw_player(fr, cam)
    for q in anim.evaluate(em, t, opts or anim.Opts()):
        draw_quad(fr, cam, q)
    return fr


def to_image(fr):
    rgb = np.clip(fr.rgb, 0, 1)
    a = np.clip(fr.alpha, 0, 1)
    return Image.fromarray((np.concatenate([rgb, a[..., None]], -1) * 255 + 0.5).astype(np.uint8), "RGBA")


def load_emotes():
    d = os.path.join(RES, "emotes")
    order = json.load(open(os.path.join(ROOT, "..", "mod", "src", "main", "resources", "rubycon_emotes", "index.json"), encoding="utf-8"))
    return [(e["id"], json.load(open(os.path.join(d, e["id"] + ".json"), encoding="utf-8"))) for e in order["emotes"]]


def gif(em, path, fps=20, size=(240, 240)):
    n = int(em["duration"] * fps)
    frames = [to_image(render(em, i / fps, size, scale=6.6)).convert("RGB") for i in range(n)]
    pal = frames[len(frames) // 3].quantize(256, method=Image.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in frames]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=True)


def overview(emotes, path, t=1.6, cols=6, size=(200, 200)):
    rows = (len(emotes) + cols - 1) // cols
    out = Image.new("RGB", (size[0] * cols, size[1] * rows))
    for i, (eid, em) in enumerate(emotes):
        im = to_image(render(em, min(t, em["duration"] - 0.6), size)).convert("RGB")
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, size[1] - 16, size[0], size[1]), fill=(20, 24, 40))
        dr.text((6, size[1] - 14), eid, fill=(244, 223, 166))
        out.paste(im, ((i % cols) * size[0], (i // cols) * size[1]))
    out.save(path, optimize=True)


def timeline(emotes, path, times=(0.1, 0.3, 1.2, 2.6), size=(180, 180)):
    out = Image.new("RGB", (size[0] * len(times), size[1] * len(emotes)))
    for r, (eid, em) in enumerate(emotes):
        for c, t in enumerate(times):
            im = to_image(render(em, t, size, scale=5.0)).convert("RGB")
            ImageDraw.Draw(im).text((4, 3), f"{eid} t={t}", fill=(255, 255, 255))
            out.paste(im, (c * size[0], r * size[1]))
    out.save(path, optimize=True)


def icon(em, px=64):
    """Menu icon: the bubble and its face at icon_time, cropped square. Particles are left out."""
    big = 512
    parts = dict(em, layers=[l for l in em["layers"] if "mode" not in l and "/s_" not in l["tex"]])
    img = to_image(render(parts, em.get("icon_time", 1.4), (big, big), yaw=0, scale=26, cx=big * 0.05, cy=big * 0.75,
                          bg=False, player=False))
    a = np.asarray(img)[..., 3]
    ys, xs = np.nonzero(a > 8)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    side = int(max(x1 - x0, y1 - y0) * 1.04) + 2
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    img = img.crop((cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side))
    return img.resize((px, px), Image.LANCZOS)


def icons(emotes):
    os.makedirs(os.path.join(TEX, "icon"), exist_ok=True)
    for eid, em in emotes:
        icon(em).save(os.path.join(TEX, "icon", eid + ".png"), optimize=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    ems = load_emotes()
    sel = [e for e in ems if len(sys.argv) < 4 or e[0] in sys.argv[3].split(",")]
    if cmd == "overview":
        overview(sel, sys.argv[2])
    elif cmd == "timeline":
        timeline(sel, sys.argv[2])
    elif cmd == "gif":
        os.makedirs(sys.argv[2], exist_ok=True)
        for eid, em in sel:
            gif(em, os.path.join(sys.argv[2], eid + ".gif"))
            print("gif", eid)
    elif cmd == "icons":
        icons(sel)
        print(len(sel), "icons")
