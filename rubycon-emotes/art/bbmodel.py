"""Exports each emote as a Blockbench project (Generic Model format) for art review and tweaking.

The head is a textured 8x8x8 cube; every quad of the emote is a zero-thickness plane at the
icon frame (billboards are frozen facing +z). Textures are embedded so the files are portable.
These are reference files: the game reads assets/rubycon_emotes/emotes/*.json, not .bbmodel.
"""
import base64
import io
import json
import os
import uuid

import anim
import preview

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "..", "blockbench")


def b64png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def tex_entry(name, img, idx):
    return {"path": "", "name": name + ".png", "folder": "", "namespace": "", "id": str(idx), "particle": False,
            "render_mode": "default", "visible": True, "mode": "bitmap", "saved": True, "uuid": str(uuid.uuid4()),
            "relative_path": "", "width": img.width, "height": img.height, "uv_width": img.width, "uv_height": img.height,
            "source": b64png(img)}


def export(eid, em):
    textures, tex_index = [], {}

    def tex(name, img):
        if name not in tex_index:
            tex_index[name] = len(textures)
            textures.append(tex_entry(name, img, len(textures)))
        return tex_index[name]

    elements = []
    skin = tex("skin", preview.SKIN)
    # Blockbench units = pixels; head bottom at y=24 like a player model
    faces = {}
    uvs = {"north": (8, 8, 16, 16), "east": (0, 8, 8, 16), "south": (24, 8, 32, 16), "west": (16, 8, 24, 16),
           "up": (8, 0, 16, 8), "down": (16, 0, 24, 8)}
    for f, uv in uvs.items():
        faces[f] = {"uv": list(uv), "texture": skin}
    elements.append({"name": "head", "type": "cube", "uuid": str(uuid.uuid4()), "from": [-4, 24, -4], "to": [4, 32, 4],
                     "origin": [0, 24, 0], "rotation": [0, 0, 0], "faces": faces, "box_uv": False, "rescale": False,
                     "color": 0})
    quads = anim.evaluate(em, em.get("icon_time", 1.0))
    for n, q in enumerate(quads):
        img = preview.load_tex(q["tex"])
        if img is None:
            continue
        # bake tint and alpha into the texture copy so Blockbench shows what the game shows
        r, g, b, a = q["color"]
        tinted = img.copy()
        px = tinted.load()
        for y in range(tinted.height):
            for x in range(tinted.width):
                pr, pg, pb, pa = px[x, y]
                px[x, y] = (int(pr * r), int(pg * g), int(pb * b), int(pa * a * min(1.0, q["alpha"])))
        key = f'{q["tex"]}#{r:.2f}{g:.2f}{b:.2f}{q["alpha"]:.2f}'
        ti = tex(key.replace("/", "_").replace("#", "_"), tinted)
        x, y, z = q["pos"]
        if q["billboard"]:
            x += q["off"][0]
            y += q["off"][1]
            z = max(z, 0) + anim.BILLBOARD_BIAS
        cx, cy, cz = x, 28 + y, z
        w, h = q["w"], q["h"]
        px0, py0 = cx - w / 2 - q["pivot"][0] * w, cy - h / 2 - q["pivot"][1] * h
        u0, u1 = (img.width, 0) if q["flip"] else (0, img.width)
        elements.append({
            "name": f'{n:02d}_{q["tex"].split("/")[-1]}{"_glow" if q["blend"] == "add" else ""}',
            "type": "cube", "uuid": str(uuid.uuid4()), "box_uv": False, "rescale": False, "color": 1,
            "from": [round(px0, 3), round(py0, 3), round(cz, 3)], "to": [round(px0 + w, 3), round(py0 + h, 3), round(cz, 3)],
            "origin": [round(cx, 3), round(cy, 3), round(cz, 3)], "rotation": [0, 0, round(q["rot"], 2)],
            "faces": {"north": {"uv": [u1, 0, u0, img.height], "texture": ti},
                      "south": {"uv": [u0, 0, u1, img.height], "texture": ti}},
        })
    project = {
        "meta": {"format_version": "4.5", "model_format": "free", "box_uv": False},
        "name": "emote_" + eid, "model_identifier": "", "visible_box": [1, 1, 0],
        "resolution": {"width": 64, "height": 64},
        "elements": elements,
        "outliner": [e["uuid"] for e in elements],
        "textures": textures,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, eid + ".bbmodel"), "w", encoding="utf-8") as f:
        json.dump(project, f, separators=(",", ":"))
    return len(elements)


if __name__ == "__main__":
    for eid, em in preview.load_emotes():
        print(eid, export(eid, em), "elements")
