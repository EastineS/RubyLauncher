"""Composites an emote emblem (halo + tinted plate + gold rim + white glyph) into a flat image.
Used for menu icons; the game draws the same layers as separate quads."""
import os
import numpy as np
from PIL import Image

T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mod", "src", "main", "resources", "assets", "rubycon_emotes", "textures")
GOLD = (0xf4, 0xdf, 0xa6)


def _tint(img, rgb, alpha=1.0):
    a = np.asarray(img.convert("RGBA")).astype(np.float32) / 255
    a[..., :3] *= np.array(rgb, np.float32) / 255
    a[..., 3] *= alpha
    return Image.fromarray((a * 255 + 0.5).astype(np.uint8), "RGBA")


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def badge(glyph, accent, px=64, halo=True):
    big = px * 4
    out = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    acc = _hex(accent)
    if halo:
        h = _tint(Image.open(f"{T}/emote/halo.png"), acc, 0.55).resize((big, big), Image.LANCZOS)
        out.alpha_composite(h)
    s = int(big * 0.78)
    o = (big - s) // 2
    plate = _tint(Image.open(f"{T}/emote/plate.png"), acc).resize((s, s), Image.LANCZOS)
    out.alpha_composite(plate, (o, o))
    rs = int(s * 1.09)
    ro = (big - rs) // 2
    out.alpha_composite(_tint(Image.open(f"{T}/emote/rim.png"), GOLD).resize((rs, rs), Image.LANCZOS), (ro, ro))
    gs = int(s * 0.64)
    go = (big - gs) // 2
    out.alpha_composite(Image.open(f"{T}/emote/{glyph}.png").convert("RGBA").resize((gs, gs), Image.LANCZOS), (go, go))
    return out.resize((px, px), Image.LANCZOS)
