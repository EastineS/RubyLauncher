"""Source of truth for the 30 roleplay emotes. Writes:
  assets/rubycon_emotes/emotes/<id>.json   visual definition read by the client
  rubycon_emotes/index.json                id/duration list read by the server
  assets/rubycon_emotes/lang/*.json        names (merged with the UI strings)

Each emote is a speech bubble at the right of the head (tail pointing at the head, clear of the
name tag) holding an exaggerated kaomoji face built from parts drawn in the bubble's frame.
All bubble layers start together and share the same motion so the face never drifts off the
bubble; parts "appear" through alpha/scale keys. Units are pixels (1/16 block), head centre origin.
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(ROOT, "..", "mod", "src", "main", "resources")

HX = 128 / 112                    # bubble frame half-width in frame units (half-height = 1)
W, H = 11.4, 10.0                 # bubble quad, px
U = W / (2 * HX)                  # px per frame unit
EO = (10.0, 5.2)                  # bubble centre, screen-plane offset from the head centre
POS = [0, 0.5, 0]
TAIL = (-1.08, -0.94)             # bubble pops out of its tail
EYES = (0.04, 0.26)
EYE_L, EYE_R = (-0.36, 0.26), (0.44, 0.26)
MOUTH = (0.04, -0.3)
APPEAR = 0.16                     # face appears as the bubble pops


def u2px(ux, uy):
    return [round(EO[0] + ux * U, 3), round(EO[1] + uy * U, 3)]


def mixhex(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02x}" for i in (0, 2, 4))


class Emote:
    def __init__(self, eid, ru, en, accent, dur, motion=None):
        self.id, self.ru, self.en, self.accent, self.dur = eid, ru, en, accent, dur
        self.motion = {"bob": [0.25, 0.45]}
        self.motion.update(motion or {})
        self.layers = []
        self.icon_time = 1.4
        self.layers.append(self._layer("bubble", TAIL, color=mixhex(accent, "#ffffff", 0.8),
                                       keys={"s": [[0, 0], [0.16, 1.14, "out"], [0.3, 0.95, "inout"], [0.42, 1.0, "inout"]]}))

    def _layer(self, tex, pivot, **kw):
        d = dict(tex="emote/" + tex, anchor="above", pos=POS, size=[W, H], pivot=[round(pivot[0] / (2 * HX), 4), round(pivot[1] / 2, 4)],
                 offset=u2px(*pivot))
        for k, v in self.motion.items():
            d[k] = v
        for k, v in kw.items():
            if k == "keys":
                d.setdefault("keys", {}).update(v)
            else:
                d[k] = v
        return d

    def part(self, name, pivot=EYES, at=APPEAR, pop=True, keys=None, **kw):
        k = {"a": [[0, 0], [at, 0], [at + 0.06, 1]]}
        if pop:
            k["s"] = [[0, 0.4], [at, 0.4], [at + 0.2, 1.0, "back"]]
        k.update(keys or {})
        self.layers.append(self._layer("f_" + name, pivot, keys=k, **kw))
        return self

    def eyes(self, name, blink=False, **kw):
        if blink:
            kw.setdefault("keys", {})["sy"] = blink_keys(self.dur)
        return self.part(name, EYES, **kw)

    def mouth(self, name, **kw):
        return self.part(name, MOUTH, **kw)

    def fx(self, layer, behind=False):
        """behind: draw under the bubble (layers draw in order), for bursts that would cover the face."""
        if behind:
            self.layers.insert(0, layer)
        else:
            self.layers.append(layer)
        return self

    def to_json(self):
        return {"duration": self.dur, "fade_in": 0.05, "fade_out": 0.45, "color": self.accent, "icon_time": self.icon_time,
                "layers": common_vfx(self)}


def blink_keys(dur):
    k = [[0, 1]]
    t = 1.5
    while t < dur - 0.6:
        k += [[t, 1], [t + 0.06, 0.1, "in"], [t + 0.14, 1, "out"]]
        t += 1.7
    return k


# ------------------------------------------------------------------ outside-the-bubble effects
def sign(tex, at_u, size=2.6, start=0.35, keys=None, **kw):
    """A sign (!, ?, heart...) popping next to the bubble."""
    k = {"s": [[0, 0], [0.18, 1.25, "out"], [0.32, 1.0, "inout"]]}
    k.update(keys or {})
    return dict(tex="emote/" + tex, anchor="above", pos=POS, offset=u2px(*at_u), size=[size, size], start=start, keys=k, **kw)


def sprinkle(tex, at_u, rate=1.2, color="#ffffff", size=(1.2, 1.8), dir_=0, spread=30, speed=(2.5, 4), life=(1.2, 1.6),
             gravity=0.0, box=(1.0, 0.5), start=0.4, end=None, wobble=(0.5, 0.8), spin=(-30, 30), curve="pop", mode="stream", **kw):
    d = dict(tex="emote/" + tex, mode=mode, anchor="above", pos=POS, offset=u2px(*at_u), color=color, size=list(size),
             dir=dir_, spread=spread, speed=list(speed), life=list(life), gravity=gravity, box=list(box), start=start,
             wobble=list(wobble), spin=list(spin), curve=curve, blend="normal")
    if mode == "stream":
        d["rate"] = rate
    if end:
        d["end"] = end
    d.update(kw)
    if mode == "burst":
        # bursts fire at their own times; the stream start would silently drop earlier ones
        d["start"] = min([d["start"], *d.get("times", [])])
    return d


def sparkles(rate=1.6, color="#ffe08a", box=(14, 11), at_u=(0, 0), start=0.4, size=(1.4, 2.6)):
    return dict(tex="fx/sparkle", mode="stream", rate=rate, anchor="above", pos=POS, offset=u2px(*at_u),
                color=["#ffffff", color], size=list(size), life=[0.5, 0.8], curve="flash", box=list(box), start=start)


def burst_fx(tex, at_u=(0, 0), size=14, t=0.1, color="#ffffff", alpha=0.9, grow=1.5, life=0.5, curve="grow"):
    return dict(tex="fx/" + tex, mode="burst", times=[t], count=1, anchor="above", pos=POS, offset=u2px(*at_u), color=color,
                size=[size, size], life=[life, life], curve=curve, grow=grow, alpha=alpha)


def appear_ring(accent):
    return burst_fx("ring", (0, 0), 12, 0.05, mixhex(accent, "#ffffff", 0.4), 0.7, 1.35, 0.45)


def star_burst(at_u=(0, 0), t=0.06, count=7, color=("#ffffff", "#ffe08a"), size=(2.6, 4.0), speed=(9, 14), optional=False):
    """Crisp four-point stars flying out and fading (the HSR 'pop')."""
    return dict(tex="fx/star4", mode="burst", times=[t], count=count, anchor="above", pos=POS, offset=u2px(*at_u),
                color=list(color), size=list(size), speed=list(speed), spread=360, life=[0.5, 0.8], curve="flash",
                spin=[-180, 180], box=[1.5, 1.5], optional=optional)


def confetti(at_u=(0, 0), t=0.08, count=10, colors=("#ff8fb0", "#ffd34d", "#7fe0d0", "#9a90ff", "#ffffff"), speed=(8, 13),
             spread=150, gravity=16, size=(1.5, 2.1), times=None, optional=True):
    return dict(tex="emote/s_confetti", mode="burst", times=times or [t], count=count, anchor="above", pos=POS,
                offset=u2px(*at_u), color=list(colors), size=list(size), speed=list(speed), dir=0, spread=spread,
                gravity=gravity, life=[0.9, 1.3], curve="fade", spin=[-540, 540], wobble=[0.5, 1.6], blend="normal",
                box=[1, 1], optional=optional)


def aura(color, rate=5, at_u=(0, -0.2), box=(9, 3), size=(1.2, 2.2), speed=(5, 8), start=0.3):
    """Rising soft streaks behind the bubble: energy for hyped emotes."""
    return dict(tex="fx/streak", mode="stream", rate=rate, anchor="above", pos=POS, offset=u2px(*at_u), color=["#ffffff", color],
                size=list(size), speed=list(speed), dir=0, spread=12, life=[0.4, 0.7], curve="shrink", stretch=0.8,
                box=list(box), alpha=0.85, start=start)


def common_vfx(e):
    """Every emote: flash + ring + star burst on appear, gentle twinkle while shown, poof on exit.
    Returns a new layer list; e.layers is left untouched so generation can run more than once."""
    light = mixhex(e.accent, "#ffffff", 0.45)
    layers = list(e.layers)
    # flash goes under the bubble (layers draw in order) so it rims it instead of washing it out
    layers.insert(0, burst_fx("flash", (0, 0), 15, 0.0, light, 0.6, 1.1, 0.22, curve="flash"))
    layers.insert(1, star_burst((0, 0), 0.05, 7, ("#ffffff", light), (2.6, 4.0), (12, 17)))  # behind the bubble too
    layers.insert(3, appear_ring(e.accent))
    layers.append(dict(tex="fx/star4", mode="stream", rate=1.8, anchor="above", pos=POS, offset=u2px(0, 0),
                       color=["#ffffff", light], size=[1.8, 3.0], life=[0.6, 0.9], curve="flash", box=[16, 13], start=0.6,
                       end=e.dur - 0.6))
    layers.append(dict(tex="emote/s_puff", mode="burst", times=[e.dur - 0.42], count=6, anchor="above", pos=POS,
                       offset=u2px(0, 0), color=["#ffffff"], size=[1.3, 2.0], speed=[5, 8], spread=360, life=[0.4, 0.5],
                       curve="grow", grow=1.6, alpha=0.9, blend="normal", box=[6, 5], optional=True))
    layers.append(star_burst((0, 0), e.dur - 0.4, 5, ("#ffffff", light), (2.0, 3.0), (6, 9), optional=True))
    return layers


def SHAKE(amp, fq=6):
    return {"shake": [amp, fq]}
JOLT = {"x": [[0, 0], [0.06, -0.8], [0.12, 0.7], [0.18, -0.5], [0.24, 0.3], [0.3, 0]]}

EMOTES = []


def add(e):
    EMOTES.append(e)
    return e


# ================================================================== 30 emotes
e = add(Emote("cry", "Рыдания", "Sobbing", "#5aa8ff", 6.0, {"squash": [0.035, 2.2]}))
e.eyes("e_tt").mouth("m_wobble", frames=3, fps=10)
e.part("x_stream", (0.04, 0.1), frames=3, fps=9, pop=False, keys={"sy": [[0, 0], [0.45, 0], [0.95, 1.0, "out"]]})
e.fx(dict(tex="emote/s_drop", mode="stream", rate=5, anchor="above", pos=POS, offset=u2px(0.04, -1.0), color="#ffffff",
          size=[1.1, 1.6], dir=0, spread=120, speed=[5, 8], gravity=22, life=[0.45, 0.6], box=[6, 0.3], start=1.0,
          curve="fade", blend="normal", optional=True))
e.fx(burst_fx("ring_soft", (0.04, -1.0), 5, 0.95, "#bfe6ff", 0.8, 2.2, 0.5))
e.fx(sprinkle("s_drop", (0.04, -0.9), rate=3.0, color="#ffffff", size=(1.2, 1.7), dir_=180, spread=50, speed=(2, 4),
              gravity=14, life=(0.5, 0.7), box=(6, 0.5), start=0.9, wobble=(0, 0), spin=(0, 0), curve="fade"))

e = add(Emote("laugh", "Ржу", "LOL", "#ffb84a", 5.0, {"bob": [0.45, 3.0], "squash": [0.05, 3.0]}))
e.eyes("e_xx").mouth("m_open").part("x_tears_lol", EYES, frames=2, fps=6)
e.fx(sparkles(2.0, "#ffd36b"))
e.fx(confetti((0, 0.6), times=[0.15, 1.6, 3.1], count=8))
e.fx(burst_fx("lines", (0, 0), 20, 0.12, "#fff2c0", 0.6, 1.2, 0.4))

e = add(Emote("joy", "Радость", "Joy", "#ffc94a", 5.0, {"bob": [0.3, 1.2]}))
e.eyes("e_happy").mouth("m_smile").part("x_blush", (0.05, -0.1))
e.fx(sparkles(2.2, "#ffd36b"))
e.fx(confetti((0, 0.7), t=0.12, count=12))

e = add(Emote("love", "Влюблённость", "In love", "#ff6f95", 5.5))
e.eyes("e_heart", beat=[0.16, 1.2]).mouth("m_small_smile").part("x_blush", (0.05, -0.1))
e.fx(sprinkle("s_heart", (0.7, 0.75), rate=1.3, color="#ffffff", size=(1.3, 1.9), dir_=20, speed=(2.5, 3.5), box=(4, 1)))
e.fx(sprinkle("s_heart", (0, 0.2), mode="burst", times=[0.1], count=8, color=["#ffffff", "#ffd0dc"], size=(1.6, 2.4),
              spread=360, speed=(14, 19), gravity=6, life=(0.6, 0.85), box=(0, 0), spin=(-90, 90), wobble=(0, 0)), behind=True)
e.fx(dict(tex="fx/ring_soft", mode="burst", every=0.83, start=0.4, count=1, anchor="above", pos=POS, offset=u2px(0, 0.26),
          color="#ff8fb0", size=[6, 6], life=[0.5, 0.5], curve="grow", grow=1.8, alpha=0.55, optional=True))

e = add(Emote("flustered", "Смущение", "Flustered", "#ff8fb4", 5.0, SHAKE(0.05, 8)))
e.eyes("e_xx").mouth("m_wavy", frames=2, fps=8).part("x_blush", (0.05, -0.1), pulse=[0.06, 1.4])
e.fx(sprinkle("s_puff", (0.1, 0.95), rate=1.6, size=(1.4, 2.0), dir_=0, spread=70, speed=(2.5, 4), box=(8, 0.5),
              life=(0.8, 1.0), curve="grow", grow=1.6, alpha=0.9, wobble=(0.2, 0.5)))

e = add(Emote("shock", "Шок", "Shock", "#b06cff", 4.5, SHAKE(0.12, 7)))
e.layers[0]["keys"].update(JOLT)
e.eyes("e_big", at=0.12, keys=JOLT).mouth("m_scream", at=0.12, frames=2, fps=12, keys=JOLT)
e.fx(burst_fx("lines", (0, 0), 24, 0.06, "#ffffff", 0.95, 1.25, 0.55))
e.fx(burst_fx("ring_soft", (0, 0), 10, 0.05, "#d9b0ff", 0.9, 2.4, 0.45))
e.fx(burst_fx("flash", (0, 0), 17, 0.04, "#ffffff", 0.55, 1.0, 0.2, curve="flash"))
e.fx(dict(tex="fx/streak", mode="burst", times=[0.06], count=10, anchor="above", pos=POS, offset=u2px(0, 0), color="#ffffff",
          size=[1.2, 1.6], speed=[22, 30], spread=360, life=[0.22, 0.3], curve="shrink", stretch=1.4, box=[3, 3]))
e.fx(sign("s_excl", (1.15, 0.95), 3.0, start=0.1, rot=12, shake=[0.15, 7]))

e = add(Emote("surprise", "Удивление", "Surprise", "#ffc94a", 4.5))
e.eyes("e_ring", blink=True).mouth("m_o", keys={"s": [[0, 0.4], [APPEAR, 0.4], [APPEAR + 0.15, 1.3, "out"], [APPEAR + 0.3, 1.0, "inout"]]})
e.fx(sign("s_excl", (1.15, 0.95), 2.8, start=0.25, rot=10, bob=[0.2, 0.8]))
e.fx(burst_fx("lines", (0, 0), 20, 0.25, "#fff2c0", 0.7, 1.2, 0.45))
e.fx(star_burst((1.15, 0.95), 0.3, 5, ("#ffffff", "#ffe08a"), (2.0, 3.2), (6, 9)))

e = add(Emote("confused", "Непонимание", "Confused", "#8f86ff", 5.5, {"sway": [4, 0.4]}))
e.eyes("e_dot", blink=True).mouth("m_wavy", frames=2, fps=3)
e.fx(sign("s_quest", (1.15, 0.9), 3.0, start=0.35, sway=[14, 0.6]))
e.fx(sign("s_quest", (1.45, 0.35), 1.8, start=0.9, rot=18, sway=[12, 0.8, 0.3]))

e = add(Emote("dizzy", "Головокружение", "Dizzy", "#4fd6a0", 5.0, {"sway": [6, 0.5]}))
e.part("e_spiral_l", EYE_L, spin=-300).part("e_spiral_r", EYE_R, spin=-300).mouth("m_wavy", frames=2, fps=6)
e.fx(dict(tex="emote/s_star", mode="orbit", count=3, anchor="above", pos=[0, 5.0, 0], radius=[5.4, 5.4, 0.5], omega=160,
          color="#ffffff", size=[1.4, 1.4], spin=[220, 220], blend="normal", start=0.3))
e.fx(dict(tex="fx/star4", mode="orbit", count=4, anchor="above", pos=[0, 5.0, 0], radius=[6.6, 6.6, 0.8], omega=-110,
          color="#b8ffe2", size=[1.0, 1.0], spin=[90, 90], start=0.5))

e = add(Emote("sleepy", "Сон", "Sleepy", "#8f86ff", 6.5, {"bob": [0.3, 0.3], "sway": [3, 0.25]}))
e.eyes("e_flat").mouth("m_o", keys={"s": [[0, 0.6], [APPEAR, 0.6], [APPEAR + 0.2, 0.8, "back"]]})
e.part("x_snot", (0.16, -0.1), pulse=[0.32, 0.35])
e.fx(sprinkle("s_z", (0.9, 0.85), rate=0.7, size=(1.9, 2.3), dir_=30, spread=8, speed=(2.2, 2.6), life=(2.0, 2.2),
              box=(0.5, 0.5), curve="grow", grow=1.6, wobble=(0.5, 0.5), spin=(-8, -8)))

e = add(Emote("deadpan", "Покерфейс", "Deadpan", "#9aa4c0", 5.5))
e.eyes("e_flat").mouth("m_flat").part("x_dots", (0.58, -0.32), frames=3, fps=1.6, pop=False)

e = add(Emote("smug", "Хе-хе", "Smug", "#e8b440", 5.0, {"sway": [3, 0.5]}))
e.eyes("e_half").mouth("m_smirk").part("x_shades_glint", EYES, at=0.6, spin=0, pulse=[0.25, 1.1])
e.fx(sparkles(1.0, "#ffe08a", box=(10, 8)))

e = add(Emote("angry", "Злость", "Angry", "#ff6a5a", 5.0, {"squash": [0.03, 1.6]}))
e.eyes("e_angry", blink=True).mouth("m_frown").part("x_vein", (0.78, 0.48), beat=[0.3, 1.6])
e.fx(dict(tex="fx/ring_soft", mode="burst", every=0.625, start=0.4, count=1, anchor="above", pos=POS, offset=u2px(0.78, 0.48),
          color="#ff6a5a", size=[3, 3], life=[0.35, 0.35], curve="grow", grow=2.0, alpha=0.7, optional=True))
e.fx(sprinkle("s_puff", (-0.6, 0.9), rate=1.4, size=(1.3, 1.8), dir_=-40, spread=25, speed=(3, 4), box=(1, 0.5),
              life=(0.7, 0.9), curve="grow", grow=1.8, alpha=0.9))
e.fx(sprinkle("s_puff", (0.95, 0.9), rate=1.4, size=(1.3, 1.8), dir_=40, spread=25, speed=(3, 4), box=(1, 0.5),
              life=(0.7, 0.9), curve="grow", grow=1.8, alpha=0.9, seed=411))

e = add(Emote("rage", "Ярость", "Rage", "#e83a3a", 4.5, SHAKE(0.22, 9)))
e.eyes("e_angry").mouth("m_grit", frames=2, fps=14).part("x_vein", (0.78, 0.48), beat=[0.35, 2.4])
e.fx(burst_fx("lines", (0, 0), 24, 0.08, "#ff8a7a", 0.9, 1.3, 0.5))
e.fx(aura("#ff5a3a", rate=9, box=(12, 3), size=(1.4, 2.6), speed=(7, 11)))
e.fx(dict(tex="emote/s_flame", mode="stream", rate=7, anchor="above", pos=POS, offset=u2px(0.04, -0.85), color=["#ff6a3a", "#ffb03a"],
          size=[1.8, 2.8], speed=[4, 7], dir=0, spread=20, life=[0.5, 0.7], curve="pop", box=[10, 0.5], blend="normal",
          wobble=[0.4, 2.0], start=0.25))
e.fx(sprinkle("s_vein", (0.2, 0.8), rate=2.2, size=(1.3, 2.0), dir_=0, spread=140, speed=(3, 5), box=(10, 3),
              life=(0.5, 0.7), curve="pop", wobble=(0, 0), spin=(-60, 60)))

e = add(Emote("sad", "Грусть", "Sad", "#6f9be0", 6.0, {"bob": [0.25, 0.3]}))
e.eyes("e_worried", blink=True).mouth("m_frown").part("x_gloom", (0.1, 0.6), pop=False,
                                                      keys={"sy": [[0, 0], [APPEAR, 0], [APPEAR + 0.6, 1, "out"]]})
e.part("x_tear", EYE_L, at=0.8, keys={"y": [[0, 0], [0.8, 0], [2.6, -1.4, "in"]], "a": [[0, 0], [0.8, 0], [0.9, 1], [2.4, 1], [2.6, 0]]})

e = add(Emote("pout", "Обида", "Pout", "#ff9a7a", 5.0, {"sway": [3, 0.6]}))
e.eyes("e_xx").mouth("m_pout").part("x_cheeks", (0.05, -0.18), pulse=[0.08, 0.9])
e.fx(sprinkle("s_puff", (-1.15, -0.2), rate=0.9, size=(1.2, 1.6), dir_=-100, spread=15, speed=(3, 4), box=(0.5, 0.5),
              life=(0.6, 0.8), curve="grow", grow=1.8, alpha=0.85))

e = add(Emote("nervous", "Нервничаю", "Nervous", "#4fc4e8", 5.0, SHAKE(0.06, 10)))
e.eyes("e_happy").mouth("m_wavy", frames=2, fps=10).part("x_sweat", (0.86, 0.42), at=0.5,
                                                          keys={"y": [[0, 0], [1.0, 0], [3.0, -1.2, "inout"]]})

e = add(Emote("awkward", "Неловко", "Awkward", "#6fb4e8", 5.0))
e.eyes("e_dot", blink=True).mouth("m_small_smile").part("x_sweat", (0.86, 0.42), at=0.5,
                                                         keys={"sy": [[0, 1], [0.5, 1], [2.0, 1.25, "inout"]],
                                                               "y": [[0, 0], [2.0, 0], [3.4, -1.6, "in"]]})
e.part("x_gloom", (0.1, 0.6), at=1.0, pop=False, alpha=0.55)

e = add(Emote("scared", "Страх", "Scared", "#7f9ad8", 5.0, SHAKE(0.12, 8)))
e.eyes("e_big").mouth("m_wavy", frames=2, fps=12).part("x_gloom", (0.1, 0.6), pop=False,
                                                       keys={"sy": [[0, 0], [APPEAR, 0], [APPEAR + 0.4, 1, "out"]]})

e = add(Emote("starstruck", "Восторг", "Starstruck", "#ffb84a", 5.0, {"bob": [0.35, 1.6]}))
e.eyes("e_star", spin=0, pulse=[0.12, 2.0]).mouth("m_open")
e.fx(sprinkle("s_star", (0.1, 0.4), mode="burst", times=[0.3], count=7, size=(1.0, 1.6), dir_=0, spread=220,
              speed=(6, 10), gravity=10, life=(0.8, 1.1), box=(0, 0), spin=(-240, 240), wobble=(0, 0)), behind=True)
e.fx(sparkles(3.0, "#ffd36b", box=(16, 12)))
e.fx(confetti((0, 0.8), times=[0.2, 2.0], count=14, speed=(10, 15), spread=170))
e.fx(burst_fx("lines", (0, 0), 22, 0.2, "#fff2c0", 0.7, 1.2, 0.45))
e.fx(aura("#ffd34d", rate=4, size=(1.0, 1.8)))

e = add(Emote("hungry", "Вкусняшка", "Yummy", "#ffa86a", 5.0, {"bob": [0.25, 0.8]}))
e.eyes("e_happy").mouth("m_drool").part("x_blush", (0.05, -0.1))
e.part("x_drool", (0.21, -0.3), at=0.6, keys={"sy": [[0, 0.3], [0.6, 0.3], [1.6, 1.3, "inout"], [2.4, 1.0, "inout"]]})
e.fx(sprinkle("s_star", (1.0, 0.85), mode="burst", times=[0.4, 2.2], count=4, size=(1.0, 1.3), dir_=30, spread=60,
              speed=(3, 4), box=(1, 1), life=(0.7, 0.9), spin=(-120, 120), wobble=(0, 0)))

e = add(Emote("wink", "Подмигивание", "Wink", "#c07aff", 4.5))
e.eyes("e_wink").mouth("m_tongue")
e.fx(sign("s_star", (-0.85, 0.75), 2.0, start=0.45, spin=90))

e = add(Emote("tease", "Бе-бе", "Tease", "#ff8fc0", 4.5, {"sway": [8, 1.6]}))
e.eyes("e_xx").mouth("m_tongue", squash=[0.08, 3.2])

e = add(Emote("disgust", "Фу", "Ew", "#8fbf4a", 5.0, {"sway": [4, 0.7]}))
e.part("x_green", (0.05, 0.3), pop=False).eyes("e_glare").mouth("m_wavy", frames=2, fps=5)
e.fx(sprinkle("s_puff", (0.2, 0.6), rate=0.8, color="#cfe8a8", size=(1.2, 1.7), dir_=0, spread=40, speed=(1.5, 2),
              box=(6, 1), life=(1.2, 1.6), curve="fade", alpha=0.75))

e = add(Emote("think", "Хмм", "Hmm", "#9a90e8", 6.0, {"sway": [3, 0.3]}))
e.eyes("e_up").mouth("m_flat", keys={"x": [[0, 0], [1.0, 0], [1.6, 0.25, "inout"], [3.0, 0.25], [3.6, -0.2, "inout"]]})
e.part("x_dots", (0.58, -0.32), frames=3, fps=2.0, pop=False)

e = add(Emote("kiss", "Чмок", "Kiss", "#ff7aa8", 4.5))
e.eyes("e_happy").mouth("m_3", keys={"s": [[0, 0.4], [APPEAR, 0.4], [APPEAR + 0.2, 1, "back"], [1.0, 1], [1.12, 1.3, "out"], [1.3, 1, "inout"]]})
e.part("x_blush", (0.05, -0.1))
e.fx(burst_fx("ring_soft", (0.55, -0.35), 3, 1.12, "#ff8fb0", 0.8, 2.4, 0.4))
e.fx(sprinkle("s_heart", (0.55, -0.35), mode="burst", times=[1.12], count=6, size=(1.2, 1.7), dir_=50, spread=40,
              speed=(3, 5), box=(0.5, 0.5), life=(1.0, 1.3), spin=(-30, 30)))

e = add(Emote("determined", "Решимость", "Let's go!", "#ff8a3a", 4.5, {"bob": [0.3, 1.4]}))
e.eyes("e_fierce").mouth("m_grin").part("x_fist", (0.88, -0.22), at=0.45,
                                        keys={"y": [[0, 0], [0.45, 0], [0.6, 0.35, "out"], [0.75, 0, "in"], [0.9, 0.25, "out"], [1.05, 0, "in"]]})
e.fx(sparkles(1.6, "#ffb36b", box=(12, 9)))
e.fx(aura("#ff9a3a", rate=6))
e.fx(burst_fx("ring_soft", (0.88, -0.22), 3.5, 0.6, "#ffd0a0", 0.85, 2.4, 0.35))
e.fx(star_burst((0.88, -0.1), 0.6, 4, ("#ffffff", "#ffb36b"), (1.8, 2.8), (6, 9)))

e = add(Emote("dead", "Помер", "Dead", "#9aa4c0", 5.5, {"sway": [2, 0.3]}))
e.eyes("e_dead").mouth("m_tongue")
e.fx(dict(tex="fx/mote", mode="stream", rate=4, anchor="above", pos=POS, offset=u2px(0.3, 1.1), color=["#d8e4ff", "#ffffff"],
          size=[0.6, 1.0], speed=[2, 3.5], dir=0, spread=40, life=[0.8, 1.1], curve="fade", box=[2, 1], start=0.8, end=3.0,
          alpha=0.8))
e.fx(sign("s_ghost", (0.3, 1.15), 4.4, start=0.7, keys={"y": [[0, 0], [2.4, 4.0, "out"]], "a": [[0, 0], [0.2, 0.9], [2.0, 0.9], [2.4, 0]],
                                                      "s": [[0, 0.4], [0.3, 1, "back"]]}, sway=[10, 1.0]))

e = add(Emote("shrug", "Пофиг", "Whatever", "#b0a8c8", 4.5))
e.eyes("e_tsu").mouth("m_tsu").part("x_arms", (0.0, 0.0), pop=False,
                                    keys={"y": [[0, 0], [APPEAR, 0], [0.5, 0.3, "out"], [0.8, 0, "inout"], [1.1, 0.25, "out"], [1.4, 0, "inout"]]})

e = add(Emote("uwu", "Умиление", "UwU", "#ff9ac0", 5.5, {"bob": [0.3, 0.6], "sway": [3, 0.4]}))
e.eyes("e_u").mouth("m_w").part("x_blush", (0.05, -0.1), pulse=[0.05, 0.8])
e.fx(sparkles(1.4, "#ffc3d6", box=(12, 10)))
e.fx(sprinkle("s_heart", (0.1, 0.9), rate=1.0, color=["#ffd0dc", "#ffffff"], size=(0.9, 1.3), dir_=0, spread=60,
              speed=(2, 3), box=(8, 1), life=(1.2, 1.6)))


def main():
    assert len(EMOTES) == 30, len(EMOTES)
    assert len({e.id for e in EMOTES}) == 30
    ed = os.path.join(RES, "assets", "rubycon_emotes", "emotes")
    os.makedirs(ed, exist_ok=True)
    for f in os.listdir(ed):
        os.remove(os.path.join(ed, f))
    index, lang = [], {"ru_ru": {}, "en_us": {}}
    for e in EMOTES:
        with open(os.path.join(ed, e.id + ".json"), "w", encoding="utf-8") as f:
            json.dump(e.to_json(), f, ensure_ascii=False, separators=(",", ":"))
        index.append({"id": e.id, "name": e.ru, "duration": e.dur})
        lang["ru_ru"]["emote.rubycon_emotes." + e.id] = e.ru
        lang["en_us"]["emote.rubycon_emotes." + e.id] = e.en
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
