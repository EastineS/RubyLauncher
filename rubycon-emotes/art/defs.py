"""Source of truth for the 20 emotes. Writes:
  assets/rubycon_emotes/emotes/<id>.json   visual definition read by the client
  rubycon_emotes/index.json                id/duration list read by the server
  assets/rubycon_emotes/lang/*.json        names

Units: pixels (1/16 block), head centre origin, y up. Anchors:
  above / side  billboards that follow the head (above ignores head pitch)
  face / head   flat quads glued to the head; z = 4 is the face surface
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ROOT, "..", "mod", "src", "main", "resources")

POP = [[0, 0], [0.16, 1.22, "out"], [0.3, 1.0, "inout"]]
POP_SOFT = [[0, 0], [0.3, 1.0, "back"]]


def E(tex, **kw):
    return dict(tex="emote/" + tex, **kw)


def FX(tex, **kw):
    return dict(tex="fx/" + tex, **kw)


def signature(anchor, pos, color, glints=3, at=0.04, ring=9.0, shards=6, box=(8, 6)):
    """Shared activation flourish: a dashed holo-ring, starlight glints and shards."""
    return [
        FX("ring_dash", mode="burst", times=[at], count=1, anchor=anchor, pos=pos, color=color, size=[ring, ring],
           life=[0.75, 0.75], curve="grow", grow=1.7, spin=[90, 90], speed=[0, 0], alpha=0.9),
        FX("glint", mode="burst", times=[at + 0.06], count=glints, anchor=anchor, pos=pos, color=["#ffffff", color],
           size=[3.0, 5.5], life=[0.45, 0.65], curve="flash", box=list(box), speed=[0, 0], optional=True),
        FX("shard", mode="burst", times=[at], count=shards, anchor=anchor, pos=pos, color=["#ffffff", color],
           size=[1.4, 2.2], life=[0.4, 0.6], speed=[16, 26], spread=360, stretch=0.6, curve="shrink", optional=True),
    ]


def twinkle(anchor, pos, color, rate=2.5, box=(14, 10), start=0.4, end=None, size=(1.4, 2.6)):
    d = dict(anchor=anchor, pos=pos, color=["#ffffff", color], size=list(size), life=[0.5, 0.9], curve="flash",
             box=list(box), speed=[0, 2], rate=rate, start=start, mode="stream")
    if end is not None:
        d["end"] = end
    return FX("glint", **d)


EMOTES = []


def emote(id, ru, en, color, duration, layers, icon_time=1.0, fade_in=0.25, fade_out=0.45):
    EMOTES.append(dict(id=id, ru=ru, en=en, json={
        "duration": duration, "fade_in": fade_in, "fade_out": fade_out, "color": color,
        "icon_time": icon_time, "layers": layers}))


# 1 ---------------------------------------------------------------- anger
SIDE_HI = [6.6, 3.6, 0]
emote("anger", "Злость", "Anger", "#ff4a3a", 3.6, [
    *signature("side", SIDE_HI, "#ff6a3d", glints=2, ring=7),
    FX("ring", mode="burst", every=0.385, start=0.3, end=3.0, count=1, anchor="side", pos=SIDE_HI, color="#ff4a2a",
       size=[6, 6], life=[0.35, 0.35], curve="grow", grow=1.9, alpha=0.55, speed=[0, 0]),
    E("anger_vein", anchor="side", pos=SIDE_HI, size=[6.2, 6.2], glow=0.9, keys={"s": POP, "rot": [[0, -25], [0.3, 0, "back"]]},
      pulse=[0.13, 2.6], shake=[0.18, 3.2]),
    FX("spark", mode="burst", every=0.385, start=0.3, end=3.0, count=4, anchor="side", pos=SIDE_HI,
       color=["#ffd36b", "#ff6a3d"], size=[1.6, 2.4], life=[0.28, 0.38], speed=[20, 30], stretch=0.8, curve="shrink", optional=True),
], icon_time=0.7)

# 2 ---------------------------------------------------------------- rage
emote("rage", "Ярость", "Rage", "#ff2a2a", 4.4, [
    FX("orb", mode="stream", rate=7, anchor="above", pos=[0, 3.5, 0], box=[9, 1], color=["#ff3b2a", "#ff8a3d"], size=[5, 8],
       life=[0.5, 0.7], speed=[6, 10], dir=0, spread=20, curve="fade", alpha=0.45, start=0.1, end=4.1),
    FX("flame", mode="stream", rate=16, anchor="above", pos=[0, 4.2, 0], box=[8, 0.5], color=["#ffffff", "#ffd0a0"],
       size=[2.2, 3.6], life=[0.45, 0.7], speed=[7, 12], dir=0, spread=16, curve="pop", start=0.15, end=4.0, blend="add"),
    *signature("above", [0, 6, 0], "#ff4a2a", glints=3, ring=12, shards=8),
    FX("steam", mode="burst", every=0.75, start=0.35, end=3.7, count=2, mirror=True, anchor="side", pos=[5.5, 1.5, 0],
       color="#ffffff", size=[2.6, 3.4], life=[0.6, 0.8], speed=[16, 22], dir=70, spread=20, gravity=-8,
       curve="grow", grow=2.1, blend="normal", alpha=0.9),
    E("rage_vein", anchor="side", pos=[6.4, 3.4, 0], size=[6.4, 6.4], mirror=True, glow=1.0,
      keys={"s": POP}, pulse=[0.17, 3.3], shake=[0.32, 4.0]),
    E("rage_vein", anchor="above", pos=[0, 9.4, 0], size=[4.2, 4.2], start=0.35, glow=1.0,
      keys={"s": POP, "rot": [[0, 30], [0.35, 0, "back"]]}, pulse=[0.2, 3.3, 0.5], shake=[0.3, 4.0]),
    FX("spark", mode="stream", rate=14, anchor="above", pos=[0, 4.5, 0], box=[10, 1], color=["#ffd36b", "#ff6a3d"],
       size=[1.2, 2.0], life=[0.4, 0.7], speed=[10, 18], dir=0, spread=30, stretch=0.7, curve="shrink", start=0.2, end=4.0),
], icon_time=0.9)

# 3 ---------------------------------------------------------------- laugh
emote("laugh", "Смех", "Laugh", "#ffc83a", 4.0, [
    *signature("face", [0, 1, 4.4], "#ffc83a", glints=2, ring=10, shards=0),
    E("laugh_eyes", anchor="face", pos=[0, -0.2, 4.15], size=[7.4, 3.7], glow=0.7,
      keys={"s": POP_SOFT}, bob=[0.3, 3.6], squash=[0.06, 3.6]),
    FX("tear", mode="stream", rate=10, mirror=True, anchor="face", pos=[3.6, -0.6, 4.3], color="#ffffff",
       size=[1.5, 2.3], life=[0.55, 0.8], speed=[16, 24], dir=55, spread=30, gravity=55, curve="pop",
       spin=[-200, -60], blend="normal", glow=0.6, screen=False, start=0.25, end=3.6),
    FX("star5", mode="burst", every=0.55, start=0.3, end=3.4, count=2, anchor="side", pos=[0, 4.5, 0],
       color=["#ffffff", "#ffe36b"], size=[1.4, 2.2], life=[0.5, 0.7], speed=[10, 16], dir=0, spread=140,
       gravity=12, spin=[-180, 180], curve="pop", blend="normal", glow=0.6, optional=True),
    twinkle("side", [0, 2, 0], "#ffd36b", rate=3, box=(16, 10)),
], icon_time=0.9)

# 4 ---------------------------------------------------------------- sad
emote("sad", "Грусть", "Sad", "#6f8fd8", 5.0, [
    FX("orb", mode="stream", rate=3, anchor="above", pos=[0, 9.5, 0], box=[9, 2], color="#8fb4ff", size=[5, 8],
       life=[1.2, 1.6], speed=[0, 1], curve="fade", alpha=0.25, start=0.3, end=4.4),
    E("cloud_sad", anchor="above", pos=[0, 10.4, 0], size=[9.4, 7.0], glow=0.55,
      keys={"y": [[0, 3.5], [0.7, 0, "out"]], "s": POP_SOFT}, bob=[0.35, 0.6], sway=[3, 0.45]),
    FX("raindrop", mode="stream", rate=6, anchor="above", pos=[0, 8.3, 0], box=[6.5, 0.4], color="#ffffff",
       size=[1.1, 1.7], life=[0.45, 0.55], speed=[11, 13], dir=180, spread=4, gravity=24, curve="fade",
       blend="normal", glow=0.5, start=0.7, end=4.5),
    FX("ring", mode="stream", rate=2.2, anchor="above", pos=[0, 4.3, 0], box=[6, 0], color="#8fb4ff", size=[2, 2],
       life=[0.4, 0.4], curve="grow", grow=2.2, alpha=0.6, start=1.0, end=4.4, optional=True),
], icon_time=1.4)

# 5 ---------------------------------------------------------------- cry
emote("cry", "Рыдания", "Crying", "#4fb4ff", 4.6, [
    *signature("face", [0, 0, 4.4], "#5fd2ff", glints=2, ring=10, shards=0),
    E("stream", anchor="face", pos=[2.3, -0.4, 4.25], size=[2.6, 6.6], pivot=[0, 0.5], mirror=True, glow=0.6,
      keys={"sy": [[0, 0], [0.45, 1.0, "out"]]}, squash=[0.07, 6.5]),
    FX("tear", mode="stream", rate=16, mirror=True, anchor="face", pos=[2.4, -6.6, 4.4], color="#ffffff",
       size=[1.1, 1.9], life=[0.45, 0.7], speed=[10, 18], dir=130, spread=50, gravity=50, curve="pop",
       blend="normal", glow=0.5, screen=False, start=0.4, end=4.2),
    FX("orb", mode="stream", rate=6, mirror=True, anchor="face", pos=[2.4, -6.8, 4.4], color="#7fdcff", size=[2.5, 4],
       life=[0.3, 0.5], curve="flash", alpha=0.5, screen=False, start=0.45, end=4.2, optional=True),
    E("laugh_eyes", anchor="face", pos=[0, 0.2, 4.12], size=[7.2, 3.2], rot=180, glow=0.5, color="#bfe8ff",
      keys={"s": POP_SOFT}, squash=[0.05, 6.5]),
], icon_time=1.0)

# 6 ---------------------------------------------------------------- surprise
emote("surprise", "Удивление", "Surprise", "#ffc83a", 3.2, [
    FX("burst", mode="burst", times=[0.12], count=1, anchor="above", pos=[0, 9.5, 0], color="#ffd36b", size=[17, 17],
       life=[0.6, 0.6], curve="flash", alpha=0.95, spin=[40, 40]),
    *signature("above", [0, 9.5, 0], "#ffc83a", glints=4, ring=11, shards=10),
    E("exclaim", anchor="above", pos=[0, 5.6, 0], size=[4.4, 7.0], pivot=[0, -0.5], glow=1.0,
      keys={"y": [[0, -4], [0.22, 1.6, "out"], [0.42, 0, "inout"]],
            "sy": [[0, 0.3], [0.18, 1.45, "out"], [0.32, 0.8, "inout"], [0.44, 1.08, "inout"], [0.56, 1.0, "inout"]],
            "sx": [[0, 0.5], [0.18, 0.75, "out"], [0.32, 1.2, "inout"], [0.44, 0.95, "inout"], [0.56, 1.0, "inout"]]},
      bob=[0.25, 0.9]),
    twinkle("above", [0, 9, 0], "#ffd36b", rate=2.5, box=(12, 9), start=0.5),
], icon_time=0.5)

# 7 ---------------------------------------------------------------- shock
emote("shock", "Шок", "Shock", "#b45cff", 3.4, [
    FX("burst", mode="burst", times=[0.05], count=1, anchor="above", pos=[0, 9, 0], color="#c06cff", size=[18, 18],
       life=[0.45, 0.45], curve="flash", alpha=0.9),
    *signature("above", [0, 9, 0], "#c06cff", glints=4, ring=12, shards=10),
    E("bolt", anchor="side", pos=[6.4, 1.5, 0], size=[3.0, 6.0], mirror=True, glow=1.0, rot=-12,
      keys={"s": POP}, flicker=[0.75, 9], shake=[0.25, 6]),
    E("exclaim_violet", anchor="above", pos=[0, 6, 0], offset=[-3.6, -0.6], rot=24, size=[3.4, 5.4], pivot=[0, -0.5],
      glow=1.0, start=0.08, keys={"s": POP}, shake=[0.22, 5]),
    E("exclaim_violet", anchor="above", pos=[0, 6, 0], offset=[3.6, -0.6], rot=-24, size=[3.4, 5.4], pivot=[0, -0.5],
      glow=1.0, start=0.14, keys={"s": POP}, shake=[0.22, 5.5]),
    E("exclaim_violet", anchor="above", pos=[0, 6, 0], size=[4.0, 6.6], pivot=[0, -0.5], glow=1.0,
      keys={"s": POP, "y": [[0, -2], [0.2, 0.6, "out"], [0.35, 0]]}, shake=[0.28, 6]),
    FX("spark", mode="burst", every=0.3, start=0.2, end=3.0, count=3, anchor="above", pos=[0, 8, 0],
       color=["#ffffff", "#c06cff"], size=[1.4, 2.2], life=[0.2, 0.3], speed=[22, 34], stretch=1.0, curve="shrink",
       box=[10, 6], optional=True),
], icon_time=0.6)

# 8 ---------------------------------------------------------------- confused
emote("confused", "Непонимание", "Confused", "#7d74ff", 4.6, [
    *signature("above", [0, 10, 0], "#7d74ff", glints=2, ring=10),
    E("question", anchor="above", pos=[0, 6.2, 0], size=[5.2, 6.9], pivot=[0, -0.5], glow=0.9,
      keys={"s": POP}, sway=[16, 0.7]),
    E("question", anchor="above", pos=[0, 6.2, 0], offset=[-4.6, -0.6], rot=22, size=[2.8, 3.7], pivot=[0, -0.5],
      glow=0.9, start=1.2, keys={"s": POP}, sway=[14, 0.9, 0.3]),
    E("question", anchor="above", pos=[0, 6.2, 0], offset=[4.4, 0.4], rot=-18, size=[2.4, 3.2], pivot=[0, -0.5],
      glow=0.9, start=1.6, keys={"s": POP}, sway=[14, 0.8, 0.6]),
    FX("orb", mode="orbit", count=3, anchor="above", pos=[0, 9, 0], radius=[6.5, 6.5, 0.8], omega=110, color="#c9c2ff",
       size=[1.6, 1.6], start=0.3, end=4.4, glow=0),
    FX("hex", mode="burst", every=1.1, start=0.5, end=4.0, count=1, anchor="above", pos=[0, 9.5, 0], color="#7d74ff",
       size=[9, 9], life=[0.9, 0.9], curve="grow", grow=1.5, alpha=0.35, spin=[30, 30], optional=True),
], icon_time=2.0)

# 9 ---------------------------------------------------------------- think
BUB = [3.6, 11.0, 0]
emote("think", "Задумчивость", "Thinking", "#9aa6ff", 6.0, [
    E("bubble_small", anchor="above", pos=[1.4, 5.6, 0], size=[1.4, 1.4], glow=0.6, keys={"s": POP_SOFT}, bob=[0.15, 0.5]),
    E("bubble_small", anchor="above", pos=[2.3, 7.0, 0], size=[2.1, 2.1], glow=0.6, start=0.12, keys={"s": POP_SOFT},
      bob=[0.2, 0.5, 0.2]),
    FX("ring_dash", mode="burst", times=[0.3], count=1, anchor="above", pos=BUB, color="#c8d4ff", size=[11, 11],
       life=[0.9, 0.9], curve="grow", grow=1.4, spin=[60, 60], alpha=0.8),
    E("bubble", anchor="above", pos=BUB, size=[10.2, 8.9], glow=0.6, start=0.24, keys={"s": POP_SOFT}, bob=[0.25, 0.5, 0.4]),
    *[E("dot", anchor="above", pos=BUB, offset=[-2.3 + 2.3 * i, -0.2], size=[1.7, 1.7], glow=1.0, start=0.5,
        keys={"s": POP_SOFT}, seq=[1.2, -0.25 * i, 0.25], bob=[0.25, 0.5, 0.4]) for i in range(3)],
    twinkle("above", BUB, "#c8d4ff", rate=1.8, box=(13, 10), start=0.6),
], icon_time=2.1, fade_out=0.5)

# 10 --------------------------------------------------------------- embarrassed
emote("embarrassed", "Смущение", "Embarrassed", "#ff6fae", 4.2, [
    E("blush", anchor="face", pos=[2.55, -1.4, 4.12], size=[3.6, 1.8], mirror=True, glow=0.45,
      keys={"a": [[0, 0], [0.7, 1.0, "inout"]], "sx": [[0, 0.6], [0.7, 1.0, "out"]]}, pulse=[0.05, 0.9]),
    FX("orb", mode="stream", rate=2, mirror=True, anchor="face", pos=[2.6, -1.4, 4.2], color="#ff9fc4", size=[3, 4],
       life=[0.8, 1.0], curve="fade", alpha=0.25, screen=False, start=0.4, end=3.8, optional=True),
    E("heart", anchor="side", pos=[6.4, 3.8, 0], size=[2.8, 2.8], glow=0.8, start=0.35,
      keys={"s": POP, "y": [[0, 0], [0.25, 1.2, "out"], [0.5, 0, "bounce"], [1.3, 0], [1.5, 0.8, "out"], [1.75, 0, "bounce"],
                            [2.6, 0], [2.8, 0.7, "out"], [3.05, 0, "bounce"]]},
      sway=[10, 0.8]),
    twinkle("side", [6.2, 3.8, 0], "#ff9fc4", rate=1.6, box=(6, 5), start=0.5, size=(1.2, 2.0)),
], icon_time=1.2)

# 11 --------------------------------------------------------------- love
emote("love", "Любовь", "Love", "#ff3d5e", 4.6, [
    *signature("above", [0, 9, 0], "#ff5e8a", glints=3, ring=11, shards=6),
    FX("ring", mode="burst", every=0.8, start=0.3, end=4.0, count=1, anchor="above", pos=[0, 9.2, 0], color="#ff5e8a",
       size=[6, 6], life=[0.5, 0.5], curve="grow", grow=2.0, alpha=0.6, optional=True),
    E("heart_red", anchor="above", pos=[0, 9.2, 0], size=[5.4, 5.4], glow=0.9, keys={"s": POP}, beat=[0.22, 1.25], bob=[0.25, 0.6]),
    FX("heart", mode="stream", rate=4.5, anchor="above", pos=[0, 2.0, 0], box=[13, 4], color=["#ffffff", "#ffd0e0"],
       size=[1.8, 3.0], life=[1.3, 1.8], speed=[5, 8], dir=0, spread=24, curve="pop", wobble=[0.8, 1.2],
       spin=[-20, 20], blend="normal", glow=0.6, start=0.3, end=4.1),
    twinkle("above", [0, 6, 0], "#ff9fc4", rate=2.5, box=(14, 10)),
], icon_time=0.9)

# 12 --------------------------------------------------------------- delight
STARS = [([-6.4, 3.2, 0], 4.6, 0.0), ([6.8, 1.6, 0], 5.6, 0.33), ([-5.4, -2.6, 0], 3.6, 0.66)]
emote("delight", "Восторг", "Delight", "#ffd23a", 4.2, [
    FX("burst", mode="burst", times=[0.1], count=1, anchor="side", pos=[0, 1, 0], color="#ffe36b", size=[20, 20],
       life=[0.55, 0.55], curve="flash", alpha=0.7),
    *signature("side", [0, 1, 0], "#ffd23a", glints=5, ring=15, shards=10, box=(16, 10)),
    *[E("star4", anchor="side", pos=p, size=[s, s], glow=1.0, start=0.05 + 0.1 * i, keys={"s": POP},
        seq=[1.1, -ph, 0.55], spin=35 * (1 if i % 2 == 0 else -1)) for i, (p, s, ph) in enumerate(STARS)],
    FX("star5", mode="orbit", count=3, anchor="above", pos=[0, 5.8, 0], radius=[6.0, 6.0, 0.6], omega=-120,
       color="#ffffff", size=[1.5, 1.5], spin=[180, 180], blend="normal", glow=0.6, start=0.4, end=4.0),
    twinkle("side", [0, 1, 0], "#ffd23a", rate=4, box=(18, 12)),
], icon_time=0.8)

# 13 --------------------------------------------------------------- fright
emote("fright", "Испуг", "Fright", "#8aa6ff", 4.0, [
    E("gloom", anchor="face", pos=[0, 1.6, 4.14], size=[7.6, 6.2], pivot=[0, 0.5], glow=0.6, alpha=0.95,
      keys={"sy": [[0, 0], [0.5, 1.0, "out"]]}, shake=[0.12, 5]),
    FX("ring", mode="burst", times=[0.45], count=1, anchor="above", pos=[0, 5.5, 0], color="#bcd6ff", size=[5, 5],
       life=[0.5, 0.5], curve="grow", grow=2.4, alpha=0.7),
    E("ghost", anchor="above", pos=[0, 5.0, 0], size=[3.8, 5.0], glow=0.8, start=0.45, end=2.6, alpha=0.95,
      keys={"y": [[0, 0], [1.3, 7.5, "out"], [2.1, 8.5]], "a": [[0, 0], [0.15, 1], [1.4, 0.9], [2.1, 0]],
            "s": [[0, 0.4], [0.25, 1.1, "out"], [0.45, 1.0]]}, sway=[12, 1.4]),
    FX("orb", mode="stream", rate=5, anchor="above", pos=[0, 6, 0], box=[3, 2], color="#bcd6ff", size=[1.0, 1.8],
       life=[0.5, 0.8], speed=[2, 5], dir=180, spread=60, curve="fade", alpha=0.8, start=0.6, end=2.4, optional=True),
    FX("shard", mode="stream", rate=3, anchor="side", pos=[0, 0, 0], box=[16, 8], color=["#ffffff", "#8aa6ff"],
       size=[1.0, 1.6], life=[0.6, 0.9], speed=[2, 4], dir=180, spread=20, curve="fade", alpha=0.7, start=0.4, end=3.5),
], icon_time=1.0)

# 14 --------------------------------------------------------------- awkward
emote("awkward", "Неловкость", "Awkward", "#5fc8ff", 4.2, [
    E("sweat", anchor="side", pos=[6.0, 5.6, 0], size=[4.4, 5.8], pivot=[0, 0.5], glow=0.75,
      keys={"s": [[0, 0], [0.28, 1.18, "out"], [0.42, 1.0, "inout"]],
            "sy": [[0, 1], [0.4, 1], [1.8, 1.22, "inout"]],
            "sx": [[0, 1], [0.4, 1], [1.8, 1.12, "inout"]],
            "y": [[0, 0], [1.0, 0], [2.4, -3.8, "in"], [2.62, -2.6, "out"], [2.85, -3.8, "in"], [3.0, -3.4, "out"],
                  [3.12, -3.8, "in"]]}),
    FX("glint", mode="burst", times=[0.35, 1.9], count=1, anchor="side", pos=[5.2, 4.0, 0], color="#ffffff",
       size=[3.4, 3.4], life=[0.5, 0.5], curve="flash"),
    FX("raindrop", mode="burst", times=[2.42], count=5, anchor="side", pos=[6.0, -2.5, 0], color="#ffffff",
       size=[0.9, 1.4], life=[0.35, 0.5], speed=[10, 16], dir=0, spread=140, gravity=50, curve="shrink",
       blend="normal", glow=0.5),
    FX("ring", mode="burst", times=[2.42], count=1, anchor="side", pos=[6.0, -2.4, 0], color="#7fdcff", size=[3, 3],
       life=[0.4, 0.4], curve="grow", grow=2.2, alpha=0.7),
], icon_time=1.6)

# 15 --------------------------------------------------------------- suspicion
SUS = [0, 10.4, 0]
LOOK = [[0, 0], [0.7, 0], [1.0, -0.75, "inout"], [1.7, -0.75], [2.1, 0.75, "inout"], [2.9, 0.75], [3.2, 0, "inout"]]
emote("suspicion", "Подозрение", "Suspicion", "#7d74ff", 4.6, [
    FX("ring_dash", mode="burst", times=[0.05], count=1, anchor="above", pos=SUS, color="#7d74ff", size=[12, 12],
       life=[4.2, 4.2], curve="fade", spin=[25, 25], alpha=0.55),
    E("bubble", anchor="above", pos=SUS, size=[9.0, 7.8], glow=0.5, keys={"s": POP_SOFT}),
    E("eyes_narrow", anchor="above", pos=SUS, offset=[0, -0.1], size=[6.4, 3.2], keys={"s": POP_SOFT,
      "sy": [[0, 1], [0.6, 1], [0.75, 0.55, "inout"], [0.95, 1.0, "inout"]]}),
    E("pupil", anchor="above", pos=SUS, offset=[-1.7, -0.25], size=[1.25, 1.25], glow=0.8, keys={"s": POP_SOFT, "x": LOOK}),
    E("pupil", anchor="above", pos=SUS, offset=[1.7, -0.25], size=[1.25, 1.25], glow=0.8, keys={"s": POP_SOFT, "x": LOOK}),
    FX("spark", mode="burst", every=1.0, start=0.6, end=4.0, count=1, anchor="above", pos=SUS, color="#c9c2ff",
       size=[1.6, 1.6], life=[0.6, 0.6], speed=[14, 14], dir=90, spread=0, box=[0, 0], curve="fade", alpha=0.6,
       stretch=0.0, rot_jitter=0),
], icon_time=1.2)

# 16 --------------------------------------------------------------- smug
emote("smug", "Самодовольство", "Smug", "#ffd36b", 4.2, [
    E("shades", anchor="face", pos=[0, 0.3, 4.32], size=[8.8, 3.5], glow=0.45, helmet="push",
      keys={"y": [[0, 8], [0.5, 0, "bounce"], [1.5, 0], [2.0, -0.45, "inout"]], "rot": [[0, 0], [1.5, 0], [2.0, -6, "back"]],
            "a": [[0, 0], [0.1, 1]]}),
    FX("glint", mode="burst", times=[0.62], count=1, anchor="face", pos=[-3.3, 1.0, 4.5], color="#ffffff", size=[5, 5],
       life=[0.6, 0.6], curve="flash", screen=False),
    E("glint", anchor="face", pos=[0, 0.4, 4.42], size=[2.4, 4.4], rot=-25, blend="add", start=0.55, end=1.05,
      keys={"x": [[0, -4.2], [0.5, 4.2, "inout"]], "a": [[0, 0], [0.1, 1], [0.4, 1], [0.5, 0]]}, tex_dir="fx"),
    FX("star5", mode="burst", times=[0.55], count=6, anchor="side", pos=[0, 2, 0], color=["#ffffff", "#ffe36b"],
       size=[1.2, 1.9], life=[0.5, 0.8], speed=[14, 22], dir=0, spread=200, gravity=10, curve="pop",
       spin=[-200, 200], blend="normal", glow=0.6),
    twinkle("side", [0, 1, 0], "#ffd36b", rate=1.5, box=(14, 8), start=1.0),
], icon_time=1.2)

# 17 --------------------------------------------------------------- sleepy
emote("sleepy", "Сонливость", "Sleepy", "#7d74ff", 6.0, [
    FX("z", mode="stream", rate=1.25, anchor="side", pos=[4.6, 4.8, 0], color="#ffffff", size=[2.0, 2.0],
       life=[2.3, 2.3], speed=[5.5, 5.5], dir=32, spread=0, curve="grow", grow=2.0, wobble=[0.9, 0.6],
       spin=[-8, -8], rot_jitter=0, blend="normal", glow=0.7, start=0.05, end=5.0, optional=False),
    FX("orb", mode="stream", rate=2, anchor="side", pos=[6, 7, 0], box=[6, 6], color="#9a92ff", size=[3, 5],
       life=[1.2, 1.6], curve="fade", alpha=0.25, start=0.2, end=5.5),
    twinkle("side", [6, 8, 0], "#c9c2ff", rate=1.6, box=(10, 10), start=0.3, size=(1.0, 1.8)),
], icon_time=2.4, fade_out=0.8)

# 18 --------------------------------------------------------------- dizzy
emote("dizzy", "Головокружение", "Dizzy", "#3fe0a6", 4.6, [
    E("spiral", anchor="face", pos=[2.0, -0.5, 4.16], size=[3.4, 3.4], mirror=True, glow=0.6, keys={"s": POP_SOFT}, spin=-420),
    FX("star5", mode="orbit", count=4, anchor="above", pos=[0, 5.6, 0], radius=[6.2, 6.2, 0.9], omega=220,
       color="#ffffff", size=[2.0, 2.0], spin=[260, 260], blend="normal", glow=0.7, start=0.15, end=4.5),
    FX("ring", mode="orbit", count=1, anchor="above", pos=[0, 5.6, 0], radius=[0.001, 0.001], omega=0, color="#3fe0a6",
       size=[1, 1], start=0, end=0.01),
    FX("glint", mode="stream", rate=4, anchor="above", pos=[0, 5.6, 0], box=[12, 2], color=["#ffffff", "#3fe0a6"],
       size=[1.2, 2.2], life=[0.35, 0.6], curve="flash", start=0.3, end=4.2, optional=True),
    FX("spark", mode="stream", rate=6, anchor="above", pos=[0, 5.6, 0], box=[0, 0], color="#b8ffe2",
       size=[1.0, 1.6], life=[0.4, 0.6], speed=[8, 12], dir=90, spread=360, stretch=0.5, curve="shrink", alpha=0.7,
       start=0.3, end=4.2, optional=True),
], icon_time=1.0)

# 19 --------------------------------------------------------------- facepalm
HIT = 0.36
emote("facepalm", "Фейспалм", "Facepalm", "#f4f1ec", 3.8, [
    E("hand", anchor="face", pos=[0.6, 0.6, 4.7], size=[7.6, 7.6], glow=0.35, helmet="push",
      keys={"x": [[0, 6], [HIT, 0, "in"]], "y": [[0, -7], [HIT, 0, "in"], [1.2, 0], [3.4, -1.2, "inout"]],
            "rot": [[0, -45], [HIT, -8, "in"], [3.4, -12, "inout"]],
            "sx": [[0, 1], [HIT, 1], [HIT + 0.05, 1.14, "out"], [HIT + 0.2, 1.0, "inout"]],
            "sy": [[0, 1], [HIT, 1], [HIT + 0.05, 0.86, "out"], [HIT + 0.2, 1.0, "inout"]],
            "a": [[0, 0], [0.12, 1]]}),
    FX("burst", mode="burst", times=[HIT], count=1, anchor="side", pos=[4.5, 4.6, 0], color="#fff3a0", size=[10, 10],
       life=[0.35, 0.35], curve="flash", alpha=0.9),
    E("impact", anchor="side", pos=[5.6, 5.2, 0], size=[4.2, 4.2], glow=0.9, start=HIT, end=HIT + 1.1,
      keys={"s": [[0, 0], [0.08, 1.35, "out"], [0.2, 1.0, "inout"], [0.8, 1.0], [1.1, 0, "in"]]}, spin=20),
    FX("ring", mode="burst", times=[HIT], count=1, anchor="side", pos=[4.5, 4.6, 0], color="#ffffff", size=[5, 5],
       life=[0.45, 0.45], curve="grow", grow=2.6, alpha=0.9),
    FX("spark", mode="burst", times=[HIT], count=8, anchor="side", pos=[4.5, 4.6, 0], color=["#ffffff", "#ffe36b"],
       size=[1.6, 2.4], life=[0.25, 0.35], speed=[26, 36], stretch=1.0, curve="shrink"),
    FX("glint", mode="burst", times=[HIT + 0.05], count=2, anchor="side", pos=[4.5, 4.6, 0], color="#ffffff",
       size=[3.5, 5], life=[0.4, 0.5], curve="flash", box=[6, 4]),
], icon_time=1.0)

# 20 --------------------------------------------------------------- mischief
GRIN = [8.2, 8.0, 0]
WINK = [[0, 1], [1.4, 1], [1.45, 0, "step"], [1.85, 0], [1.9, 1, "step"], [3.0, 1], [3.05, 0, "step"], [3.45, 0], [3.5, 1, "step"]]
WINK_ON = [[k[0], 1 - k[1]] + k[2:] for k in WINK]
emote("mischief", "Озорство", "Mischief", "#b45cff", 4.6, [
    FX("smoke", mode="burst", times=[0.1], count=4, mirror=True, anchor="head", pos=[2.6, 4.6, 0.8], color="#ffffff",
       size=[2.2, 3.2], life=[0.5, 0.7], speed=[4, 8], dir=0, spread=90, curve="grow", grow=1.8, blend="normal",
       alpha=0.85, emote_tex=True),
    E("horn", anchor="head", pos=[2.5, 4.0, 0.9], size=[2.2, 3.4], pivot=[0, -0.5], mirror=True, glow=0.8, rot=-14,
      helmet="push", keys={"sy": [[0, 0], [0.12, 0], [0.26, 1.3, "out"], [0.4, 1.0, "inout"]]}, sway=[4, 1.2]),
    *signature("side", GRIN, "#b45cff", glints=2, ring=10, shards=4, at=0.35),
    E("bubble", anchor="side", pos=GRIN, size=[8.4, 7.3], glow=0.45, start=0.3, color="#f0e8ff", keys={"s": POP_SOFT}),
    E("grin", anchor="side", pos=GRIN, offset=[0, -1.0], size=[4.8, 3.0], start=0.45,
      keys={"sx": [[0, 0.5], [0.3, 1.0, "out"], [0.9, 1.0], [1.15, 1.18, "out"], [1.6, 1.0, "inout"]], "s": POP_SOFT}),
    E("pupil", anchor="side", pos=GRIN, offset=[-1.6, 1.2], size=[1.2, 1.2], start=0.45, color="#d9b8ff", keys={"s": POP_SOFT}),
    E("pupil", anchor="side", pos=GRIN, offset=[1.6, 1.2], size=[1.2, 1.2], start=0.45, color="#d9b8ff",
      keys={"s": POP_SOFT, "a": WINK}),
    E("wink_eye", anchor="side", pos=GRIN, offset=[1.6, 1.2], size=[1.8, 1.8], start=0.45, keys={"a": WINK_ON}),
    FX("glint", mode="burst", times=[1.45, 3.05], count=1, anchor="side", pos=GRIN, color="#ffffff", size=[3, 3],
       life=[0.4, 0.4], curve="flash", box=[0, 0]),
    twinkle("side", GRIN, "#b45cff", rate=1.6, box=(10, 8), start=0.6),
], icon_time=1.6)


def fix_tex(layer):
    """layers default to emote/ for parts and fx/ for emitters; allow overrides."""
    if layer.pop("tex_dir", None) == "fx":
        layer["tex"] = "fx/" + layer["tex"].split("/", 1)[1]
    if layer.pop("emote_tex", False):
        layer["tex"] = "emote/" + layer["tex"].split("/", 1)[1]
    return layer


EMITTER_EMOTE_TEX = {"flame", "steam", "tear", "raindrop", "heart", "heart_red", "star5", "z", "smoke"}


def main():
    ed = os.path.join(RES, "assets", "rubycon_emotes", "emotes")
    os.makedirs(ed, exist_ok=True)
    for f in os.listdir(ed):
        os.remove(os.path.join(ed, f))
    index = []
    lang = {"ru_ru": {}, "en_us": {}}
    for e in EMOTES:
        for layer in e["json"]["layers"]:
            fix_tex(layer)
            name = layer["tex"].split("/", 1)[1]
            if "mode" in layer and name in EMITTER_EMOTE_TEX:
                layer["tex"] = "emote/" + name
        with open(os.path.join(ed, e["id"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(e["json"], f, ensure_ascii=False, separators=(",", ":"))
        index.append({"id": e["id"], "name": e["ru"], "duration": e["json"]["duration"]})
        lang["ru_ru"]["emote.rubycon_emotes." + e["id"]] = e["ru"]
        lang["en_us"]["emote.rubycon_emotes." + e["id"]] = e["en"]
    os.makedirs(os.path.join(RES, "rubycon_emotes"), exist_ok=True)
    with open(os.path.join(RES, "rubycon_emotes", "index.json"), "w", encoding="utf-8") as f:
        json.dump({"emotes": index}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT, "lang_emotes.json"), "w", encoding="utf-8") as f:
        json.dump(lang, f, ensure_ascii=False, indent=2)
    print(len(EMOTES), "emotes written")


if __name__ == "__main__":
    main()
