"""Debug contact sheet: every sprite on dark and light backgrounds, glow composited additively."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mod/src/main/resources/assets/rubycon_emotes/textures")
names = sorted(f[:-4] for f in os.listdir(T + "/emote") if f.endswith(".png") and not f.endswith("_glow.png"))
fx = sorted(f[:-4] for f in os.listdir(T + "/fx"))
cell = 150
items = [("emote", n) for n in names] + [("fx", n) for n in fx]
cols = 8
rows = (len(items) + cols - 1) // cols
sheet = Image.new("RGB", (cols * cell, rows * cell * 2), (0, 0, 0))
for i, (kind, n) in enumerate(items):
    for half, bg in enumerate([(18, 20, 34), (170, 200, 230)]):
        x, y = (i % cols) * cell, (i // cols) * cell * 2 + half * cell
        base = np.full((cell, cell, 3), bg, np.float32) / 255
        img = Image.open(f"{T}/{kind}/{n}.png").convert("RGBA")
        k = 120 / max(img.size); img = img.resize((int(img.width * k), int(img.height * k)), Image.LANCZOS)
        ox, oy = (cell - img.width) // 2, (cell - img.height) // 2
        g = f"{T}/{kind}/{n}_glow.png"
        if os.path.exists(g):
            gi = np.asarray(Image.open(g).convert("RGBA").resize(img.size, Image.LANCZOS)).astype(np.float32) / 255
            base[oy:oy + img.height, ox:ox + img.width] += gi[..., :3] * gi[..., 3:]
        a = np.asarray(img).astype(np.float32) / 255
        sl = base[oy:oy + img.height, ox:ox + img.width]
        base[oy:oy + img.height, ox:ox + img.width] = sl * (1 - a[..., 3:]) + a[..., :3] * a[..., 3:]
        tile = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8))
        ImageDraw.Draw(tile).text((3, 2), n, fill=(255, 80, 80))
        sheet.paste(tile, (x, y))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/contact.png")
