"""Source of truth for the 30 roleplay emotes. Writes:
  assets/rubycon_emotes/emotes/<id>.json   visual definition read by the client
  rubycon_emotes/index.json                id/duration list read by the server
  assets/rubycon_emotes/lang/*.json        names (merged with the UI strings)

Every emote is an emblem (tinted plate, gold rim, white glyph) floating at the upper right of the
head, where it does not collide with the name tag, plus a small mood effect. Units are pixels
(1/16 block); origin is the head centre, y up. Anchors: above (billboard, ignores head turns),
face/head (flat on the head, lit by the world). z = 4 is the face surface.
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ROOT, "..", "mod", "src", "main", "resources")

GOLD = "#f4dfa6"
EP = [0, 0.5, 0]          # emblem anchor: head centre (billboard)
EO = [8.6, 5.6]           # screen-plane offset: upper right of the head
PLATE, BOB = 6.6, [0.22, 0.42]
HEAD = [0, 0, 0]


def E(tex, **kw):
    return dict(tex="emote/" + tex, **kw)


def FX(tex, **kw):
    return dict(tex="fx/" + tex, **kw)


def off(dx=0.0, dy=0.0):
    return [round(EO[0] + dx, 3), round(EO[1] + dy, 3)]


def bob(start=0.0):
    return [BOB[0], BOB[1], round(start * BOB[1], 4)]


def emblem(glyph, accent, dur, glyph_keys=None, glyph_mods=None, plate_mods=None, jolt=False, glyph_size=4.25):
    pop = [[0, 0.5], [0.3, 1.0, "back"]]
    common = dict(anchor="above", pos=EP)
    j = {"x": [[0, 0], [0.08, -0.6], [0.16, 0.5], [0.24, -0.35], [0.32, 0.2], [0.4, 0]]} if jolt else {}
    layers = [
        E("halo", blend="add", color=accent, size=[12, 12], alpha=0.45, offset=off(), keys={"a": [[0, 0], [0.35, 1, "out"]], **j},
          bob=bob(), **common),
        FX("ring_dash", mode="burst", times=[0.02], count=1, color=GOLD, size=[7, 7], life=[0.7, 0.7], curve="grow",
           grow=1.45, spin=[70, 70], alpha=0.85, offset=off(), **common),
        E("plate", color=accent, size=[PLATE, PLATE], offset=off(), keys={"s": pop, **j}, **common,
          **{"bob": bob(), **(plate_mods or {})}),
        E("rim", color=GOLD, size=[PLATE * 1.09] * 2, offset=off(), keys={"s": pop, "rot": [[0, -60], [0.45, 0, "out"]], **j},
          bob=bob(), **common),
    ]
    if glyph:
        keys = {"s": [[0, 0.4], [0.26, 1.0, "back"]], "a": [[0, 0], [0.12, 1]], **j}
        keys.update(glyph_keys or {})
        mods = {"bob": bob(0.06), **(glyph_mods or {})}
        layers.append(E(glyph, size=[glyph_size, glyph_size], start=0.06, offset=off(), keys=keys, **common, **mods))
    layers += [
        FX("sparkle", mode="burst", times=[0.22], count=1, color="#ffffff", size=[3.6, 3.6], life=[0.5, 0.5],
           curve="flash", offset=off(2.6, 2.6), **common),
        FX("mote", mode="burst", times=[dur - 0.5], count=6, color=[accent, "#ffffff"], size=[0.8, 1.4], life=[0.4, 0.6],
           speed=[5, 9], curve="fade", alpha=0.9, offset=off(), optional=True, **common),
    ]
    return layers


def sparkles(rate, color, box=(14, 10), pos=None, offset=None, size=(1.7, 3.2), start=0.4, end=None, anchor="above"):
    d = dict(mode="stream", rate=rate, anchor=anchor, pos=pos or HEAD, color=["#ffffff", color], size=list(size),
             life=[0.5, 0.9], curve="flash", box=list(box), start=start)
    if offset:
        d["offset"] = offset
    if end:
        d["end"] = end
    return FX("sparkle", **d)


def motes(rate, color, dir_=0, speed=(1.5, 3), box=(12, 8), pos=None, offset=None, start=0.3, end=None, alpha=0.7, size=(0.8, 1.5)):
    d = dict(mode="stream", rate=rate, anchor="above", pos=pos or HEAD, color=[color, "#ffffff"], size=list(size),
             life=[1.0, 1.6], curve="fade", box=list(box), speed=list(speed), dir=dir_, spread=30, alpha=alpha, start=start)
    if offset:
        d["offset"] = offset
    if end:
        d["end"] = end
    return FX("mote", **d)


def icons(tex, rate, color, dir_=0, speed=(2.5, 4), size=(1.0, 1.5), box=(10, 4), pos=None, offset=None, life=(1.4, 1.9),
          start=0.4, end=None, wobble=(0.6, 0.9), spin=(-20, 20), gravity=0.0, mode="stream", curve="pop", spread=24,
          glow=0.35, **kw):
    d = dict(mode=mode, anchor="above", pos=pos or HEAD, color=color if isinstance(color, list) else [color],
             size=[v * 1.3 for v in size], life=list(life), curve=curve, box=list(box), speed=list(speed), dir=dir_, spread=spread,
             wobble=list(wobble), spin=list(spin), gravity=gravity, blend="normal", glow=glow, start=start, **kw)
    if mode == "stream":
        d["rate"] = rate
    if offset:
        d["offset"] = offset
    if end:
        d["end"] = end
    return E(tex, **d)


EMOTES = []


def emote(id, ru, en, color, dur, glyph, extra=(), fade_in=0.2, fade_out=0.5, **emb):
    layers = emblem(glyph, color, dur, **emb) + list(extra)
    EMOTES.append(dict(id=id, ru=ru, en=en, glyph=glyph or "g_dots", json={
        "duration": dur, "fade_in": fade_in, "fade_out": fade_out, "color": color, "glyph": glyph or "g_dots",
        "layers": layers}))


CHEEK = [2.6, -1.6, 4.2]
TEMPLE = [3.0, 2.5, 4.22]
LOOK = [[0, 0], [0.8, 0], [1.1, -0.9, "inout"], [1.9, -0.9], [2.3, 0.9, "inout"], [3.1, 0.9], [3.4, 0, "inout"]]

# ---------------------------------------------------------------- warm
emote("joy", "Радость", "Joy", "#f2b53c", 5.0, "g_joy", glyph_mods={"pulse": [0.05, 0.8]}, extra=[
    sparkles(2.6, "#ffd36b"),
])
emote("laugh", "Смех", "Laugh", "#f59f3a", 4.5, "g_laugh", glyph_mods={"bob": [0.32, 2.4]}, extra=[
    sparkles(2.0, "#ffd36b", box=(6, 5), offset=off()),
])
emote("love", "Влюблённость", "In love", "#ec5a86", 5.0, "g_heart", glyph_mods={"beat": [0.14, 1.1]}, extra=[
    icons("p_heart", 1.4, ["#ff8fb0", "#ffc3d6"], offset=off(0, -1), box=(5, 2), size=(0.9, 1.4)),
])
emote("tender", "Нежность", "Tenderness", "#ef8fb4", 5.5, "g_flower", glyph_mods={"sway": [6, 0.35]}, extra=[
    icons("p_petal", 1.6, ["#ffb7cf", "#ffe1ea"], dir_=180, speed=(0.8, 1.6), box=(16, 2), pos=[0, 9, 0], life=(2.4, 3.0),
          gravity=0.6, wobble=(1.2, 0.5), spin=(-90, 90), size=(0.8, 1.2)),
])
emote("blush", "Смущение", "Flustered", "#f07a9c", 5.0, "g_blush", extra=[
    E("face_blush", anchor="face", pos=CHEEK, size=[3.2, 1.7], mirror=True, keys={"a": [[0, 0], [0.8, 1.0, "inout"]]},
      pulse=[0.04, 0.6]),
])
emote("excited", "Восторг", "Excited", "#f08a3a", 4.5, "g_star", glyph_mods={"spin": 40}, extra=[
    icons("p_star", 0, ["#ffe08a", "#ffffff", "#ffb3c8"], mode="burst", times=[0.12], count=7, speed=(9, 14), dir_=0,
          spread=200, gravity=14, life=(0.8, 1.1), size=(0.8, 1.3), spin=(-240, 240), offset=off(), box=(0, 0)),
    sparkles(3.0, "#ffd36b", box=(16, 11)),
])
emote("music", "Напевание", "Humming", "#2fb3a6", 6.0, "g_note", glyph_mods={"sway": [8, 0.9]}, extra=[
    icons("p_note", 1.1, ["#a8f0e4", "#ffffff"], offset=off(-2, -1), box=(3, 1), speed=(2.5, 3.5), dir_=-20,
          wobble=(1.0, 0.7), size=(1.0, 1.4)),
])
emote("pride", "Гордость", "Pride", "#d9a62e", 5.0, "g_crown", extra=[
    sparkles(1.8, "#ffe08a", box=(7, 5), offset=off()),
    motes(2.0, "#ffd36b", speed=(1.5, 2.5), box=(10, 2), pos=[0, 4, 0]),
])
emote("confident", "Уверенность", "Confident", "#e8b440", 4.5, "g_glint", glyph_mods={"spin": 18}, extra=[
    FX("sparkle", mode="burst", times=[0.5, 2.2, 3.6], count=1, anchor="above", pos=HEAD, offset=[-5.2, 3.0],
       color="#ffffff", size=[3.2, 3.2], life=[0.45, 0.45], curve="flash"),
])
emote("determined", "Решимость", "Determined", "#ec6a2c", 5.0, "g_flame", glyph_mods={"pulse": [0.06, 2.2]}, extra=[
    FX("streak", mode="stream", rate=5, anchor="above", pos=EP, offset=off(0, 1), box=[4, 2], color=["#ffb36b", "#ffe0b0"],
       size=[1.0, 1.6], life=[0.5, 0.8], speed=[4, 7], dir=0, spread=20, curve="shrink", alpha=0.85, stretch=0.4, start=0.3),
])

# ---------------------------------------------------------------- reactions
emote("surprise", "Удивление", "Surprise", "#f0b030", 4.0, "g_exclaim",
      glyph_keys={"s": [[0, 0.3], [0.18, 1.3, "out"], [0.34, 1.0, "inout"]]}, extra=[
    FX("ring", mode="burst", times=[0.08], count=1, anchor="above", pos=EP, offset=off(), color="#ffe08a", size=[7, 7],
       life=[0.45, 0.45], curve="grow", grow=1.8, alpha=0.9),
    FX("streak", mode="burst", times=[0.1], count=3, anchor="above", pos=EP, offset=off(-0.2, 3.6), dir=-10, spread=50,
       color="#ffffff", size=[1.0, 1.0], life=[0.3, 0.3], speed=[6, 6], stretch=0.5, curve="shrink", box=[0, 0]),
])
emote("shock", "Шок", "Shock", "#a457e0", 4.0, "g_exclaim2", jolt=True, extra=[
    FX("ring", mode="burst", times=[0.05, 0.2], count=1, anchor="above", pos=EP, offset=off(), color="#d9b0ff", size=[7, 7],
       life=[0.5, 0.5], curve="grow", grow=1.9, alpha=0.9),
])
emote("confused", "Недоумение", "Confused", "#6f6ae0", 5.0, "g_question", glyph_mods={"sway": [10, 0.55]}, extra=[
    FX("mote", mode="orbit", count=3, anchor="above", pos=EP, offset=off(), radius=[4.6, 4.6, 0.4], omega=70,
       color="#c9c2ff", size=[0.8, 0.8], alpha=0.8, start=0.3),
])
emote("idea", "Озарение", "Idea", "#f2c94c", 4.5, "g_idea", glyph_mods={"spin": 12},
      glyph_keys={"s": [[0, 0.3], [0.2, 1.25, "out"], [0.4, 1.0, "inout"]]}, extra=[
    FX("ring", mode="burst", times=[0.12], count=1, anchor="above", pos=EP, offset=off(), color="#fff2b0", size=[6, 6],
       life=[0.55, 0.55], curve="grow", grow=2.1, alpha=0.95),
    FX("sparkle", mode="burst", times=[0.14], count=4, anchor="above", pos=EP, offset=off(), color=["#ffffff", "#ffe08a"],
       size=[1.6, 2.6], life=[0.45, 0.7], speed=[6, 10], curve="flash", box=[0, 0]),
])
emote("think", "Раздумье", "Thinking", "#8f86d8", 6.0, None, extra=[
    *[E("g_pupil", anchor="above", pos=EP, offset=off(-1.4 + 1.4 * i, -0.1), size=[1.15, 1.15], start=0.2,
        keys={"s": [[0, 0], [0.25, 1, "back"]]}, seq=[1.3, -0.22 * i, 0.3], bob=bob(0.2)) for i in range(3)],
    FX("mote", mode="stream", rate=1.3, anchor="above", pos=[0, 3.5, 0], offset=[3.0, 1.2], box=[1, 0], dir=50, spread=10,
       speed=[3.2, 3.6], color="#ffffff", size=[0.5, 0.9], life=[1.2, 1.3], curve="fade", alpha=0.8, start=0.4),
])
emote("suspicion", "Подозрение", "Suspicion", "#5f58b0", 5.0, "g_eye", extra=[
    E("g_pupil", anchor="above", pos=EP, offset=off(), size=[1.25, 1.25], start=0.2, bob=bob(0.2),
      keys={"s": [[0, 0], [0.25, 1, "back"]], "x": LOOK}),
])

# ---------------------------------------------------------------- low
emote("sad", "Грусть", "Sad", "#5b8fe0", 6.0, "g_drop", glyph_mods={"bob": [0.3, 0.3]}, extra=[
    motes(1.6, "#8fb4ff", dir_=180, speed=(0.8, 1.4), box=(14, 3), pos=[0, 8, 0], alpha=0.55),
])
emote("cry", "Слёзы", "Crying", "#4a7ed8", 6.0, "g_drops", extra=[
    E("face_tear", mode="stream", rate=1.1, anchor="face", pos=[1.6, -1.1, 4.2], mirror=True, size=[1.5, 1.5],
      life=[1.5, 1.5], speed=[1.6, 1.6], dir=180, spread=0, gravity=1.6, curve="fade", blend="normal", screen=False,
      start=0.4, optional=False),
])
emote("tired", "Усталость", "Tired", "#7d8bb0", 5.5, "g_sigh", glyph_mods={"bob": [0.3, 0.3]}, extra=[
    icons("p_puff", 0, ["#ffffff"], mode="burst", times=[0.6, 2.8], count=2, offset=[-3.4, -2.4], dir_=-70, speed=(2, 3),
          box=(0.5, 0.5), life=(1.2, 1.5), size=(1.0, 1.6), wobble=(0.3, 0.6), spin=(-30, 30), alpha=0.7, curve="fade"),
])
emote("sleepy", "Сонливость", "Sleepy", "#6a66c8", 6.0, "g_z", glyph_mods={"sway": [5, 0.3]}, extra=[
    icons("p_z", 0.8, ["#d9d4ff", "#ffffff"], offset=off(2.2, 2.2), box=(0.5, 0.5), dir_=25, speed=(2.2, 2.6),
          life=(2.0, 2.2), size=(0.9, 1.1), wobble=(0.5, 0.5), spin=(-10, -10), curve="grow", grow=1.6),
])
emote("silence", "Молчание", "Silence", "#8f97b0", 5.0, "g_dots", glyph_mods={"pulse": [0.03, 0.4]})

# ---------------------------------------------------------------- tense
emote("anger", "Злость", "Anger", "#e0484c", 4.5, "g_vein", plate_mods={"pulse": [0.05, 1.6]}, extra=[
    E("face_vein", anchor="face", pos=TEMPLE, size=[2.4, 2.4], keys={"s": [[0, 0], [0.25, 1.15, "out"], [0.4, 1, "inout"]]},
      pulse=[0.12, 1.6]),
])
emote("annoyed", "Раздражение", "Annoyed", "#7e6aa8", 4.5, "g_scribble", glyph_mods={"sway": [7, 0.5]}, extra=[
    icons("p_puff", 0, ["#b9b2c9"], mode="burst", times=[0.4, 2.0, 3.4], count=1, offset=off(-2.6, -2.8), dir_=-60,
          speed=(2.5, 2.5), box=(0, 0), life=(0.8, 0.8), size=(1.2, 1.2), wobble=(0, 0), spin=(0, 0), alpha=0.8, curve="fade"),
])
emote("nervous", "Волнение", "Nervous", "#32b4c8", 5.0, "g_ecg", glyph_mods={"beat": [0.1, 1.5]}, plate_mods={"beat": [0.04, 1.5]})
emote("awkward", "Неловкость", "Awkward", "#4ea8e0", 5.0, "g_awkward", extra=[
    E("face_sweat", anchor="face", pos=TEMPLE, size=[2.2, 2.2], start=0.3,
      keys={"s": [[0, 0], [0.25, 1, "back"]], "y": [[0, 0], [1.2, 0], [3.4, -1.4, "inout"]]}),
])
emote("fear", "Страх", "Fear", "#6f8fd0", 5.0, "g_shiver", glyph_mods={"shake": [0.12, 5]}, plate_mods={"shake": [0.08, 5]}, extra=[
    motes(2.0, "#cfe0ff", dir_=180, speed=(0.6, 1.2), box=(14, 6), pos=[0, 4, 0], alpha=0.5, size=(0.4, 0.8)),
])
emote("disgust", "Отвращение", "Disgust", "#86a83a", 4.5, "g_disgust", glyph_mods={"sway": [6, 0.6]}, extra=[
    icons("p_puff", 0.9, ["#b6cf78"], offset=[-1.5, -3.0], box=(4, 1), dir_=0, speed=(1.2, 1.8), life=(1.4, 1.8),
          size=(0.9, 1.4), alpha=0.45, curve="fade", glow=0.0),
])
emote("dizzy", "Головокружение", "Dizzy", "#34c08e", 5.0, "g_spiral", glyph_mods={"spin": -160}, extra=[
    E("p_star", mode="orbit", count=3, anchor="above", pos=[0, 5.2, 0], radius=[5.6, 5.6, 0.6], omega=150,
      color="#fff3b0", size=[1.2, 1.2], spin=[200, 200], blend="normal", glow=0.4, start=0.2),
])

# ---------------------------------------------------------------- answers
emote("agree", "Согласие", "Agree", "#37b98a", 3.5, "g_check",
      glyph_keys={"y": [[0, 0], [0.45, 0], [0.58, -0.7, "out"], [0.75, 0, "inout"], [0.9, -0.55, "out"], [1.08, 0, "inout"]]})
emote("disagree", "Несогласие", "Disagree", "#e05a5a", 3.5, "g_cross",
      glyph_keys={"x": [[0, 0], [0.45, 0], [0.55, -0.6], [0.66, 0.6], [0.77, -0.45], [0.88, 0.3], [1.0, 0]]})


def main():
    assert len(EMOTES) == 30, len(EMOTES)
    ed = os.path.join(RES, "assets", "rubycon_emotes", "emotes")
    os.makedirs(ed, exist_ok=True)
    for f in os.listdir(ed):
        os.remove(os.path.join(ed, f))
    index = []
    lang = {"ru_ru": {}, "en_us": {}}
    for e in EMOTES:
        with open(os.path.join(ed, e["id"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(e["json"], f, ensure_ascii=False, separators=(",", ":"))
        index.append({"id": e["id"], "name": e["ru"], "duration": e["json"]["duration"]})
        lang["ru_ru"]["emote.rubycon_emotes." + e["id"]] = e["ru"]
        lang["en_us"]["emote.rubycon_emotes." + e["id"]] = e["en"]
    os.makedirs(os.path.join(RES, "rubycon_emotes"), exist_ok=True)
    with open(os.path.join(RES, "rubycon_emotes", "index.json"), "w", encoding="utf-8") as f:
        json.dump({"emotes": index}, f, ensure_ascii=False, indent=2)
    # merge emote names into the UI lang files (UI strings live there already)
    for code, names in lang.items():
        lp = os.path.join(RES, "assets", "rubycon_emotes", "lang", code + ".json")
        data = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else {}
        data = {k: v for k, v in data.items() if not k.startswith("emote.rubycon_emotes.")}
        data.update(names)
        with open(lp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    print(len(EMOTES), "emotes written")


if __name__ == "__main__":
    main()
