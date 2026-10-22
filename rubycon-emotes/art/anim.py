"""Reference evaluator for emote JSON. EmoteAnimator.java mirrors this file line for line,
so previews, icons and Blockbench exports match what the game draws.

evaluate(emote, t) -> list of Quad dicts, coordinates in pixels (1 px = 1/16 block),
origin at the head centre, y up, x = viewer's right when looking at the face, z = out of the face.
"""
import math

GLOW_PAD = 1.5
BILLBOARD_BIAS = 3.0  # px toward the camera so side effects are not swallowed by the head


def rnd(seed, i, k):
    h = (seed * 0x9E3779B1 + i * 0x85EBCA77 + k * 0xC2B2AE3D) & 0xFFFFFFFF
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & 0xFFFFFFFF
    h ^= h >> 12
    h = (h * 0x297A2D39) & 0xFFFFFFFF
    h ^= h >> 15
    return h / 4294967296.0


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a, b):
    return a if x < a else b if x > b else x


def sstep(e0, e1, x):
    if e0 == e1:
        return 1.0 if x >= e1 else 0.0
    t = clamp((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ease(name, t):
    if name == "out":
        return 1 - (1 - t) ** 3
    if name == "in":
        return t ** 3
    if name == "inout":
        return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
    if name == "back":
        c1, c3 = 1.9, 2.9
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
    if name == "bounce":
        n, d = 7.5625, 2.75
        if t < 1 / d:
            return n * t * t
        if t < 2 / d:
            t -= 1.5 / d
            return n * t * t + 0.75
        if t < 2.5 / d:
            t -= 2.25 / d
            return n * t * t + 0.9375
        t -= 2.625 / d
        return n * t * t + 0.984375
    if name == "step":
        return 0.0
    return t


def track(keys, t, default):
    """keys: [[time, value, ease?], ...] sorted; ease belongs to the segment ending at that key."""
    if not keys:
        return default
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        k1 = keys[i]
        if t < k1[0]:
            k0 = keys[i - 1]
            u = (t - k0[0]) / max(1e-6, k1[0] - k0[0])
            return lerp(k0[1], k1[1], ease(k1[2] if len(k1) > 2 else "linear", u))
    return keys[-1][1]


def parse_color(c):
    if isinstance(c, (list, tuple)):
        return list(c) + [1.0] * (4 - len(c))
    c = c.lstrip("#")
    v = [int(c[i:i + 2], 16) / 255 for i in range(0, len(c), 2)]
    return v + [1.0] * (4 - len(v))


def beat(x):
    """double heart-thump shape, period 1"""
    f = x - math.floor(x)
    return math.exp(-((f - 0.08) / 0.05) ** 2) + 0.6 * math.exp(-((f - 0.26) / 0.06) ** 2)


def seq(x, duty=0.45):
    """smooth hump once per period, used for sequential blinking"""
    f = x - math.floor(x)
    return sstep(0.0, duty * 0.35, f) * (1 - sstep(duty * 0.65, duty, f))


class Opts:
    def __init__(self, scale=1.0, reduced=False, helmet=False, budget=1.0):
        self.scale, self.reduced, self.helmet, self.budget = scale, reduced, helmet, budget


def envelope(em, t):
    d = em["duration"]
    return sstep(0, em.get("fade_in", 0.3), t) * (1 - sstep(d - em.get("fade_out", 0.4), d, t))


def quad(tex, blend, anchor, pos, off, w, h, rot, color, alpha, flip=False, pivot=(0, 0), billboard=True):
    return {"tex": tex, "blend": blend, "anchor": anchor, "pos": pos, "off": off, "w": w, "h": h, "rot": rot,
            "color": color, "alpha": alpha, "flip": flip, "pivot": pivot, "billboard": billboard}


def _face_adjust(p, opts, pos):
    if opts.helmet and p.get("anchor") in ("face", "head"):
        mode = p.get("helmet", "push")
        if mode == "push":
            # helmet shell sits ~1px outside the head; inflate around the head centre
            return [pos[0] * 1.15, pos[1] * 1.15, pos[2] + 1.1], 1.15
        if mode == "hide":
            return None, 0
    return pos, 1.0


def eval_part(p, t, opts, out):
    start, end = p.get("start", 0.0), p.get("end", 1e9)
    if t < start or t > end:
        return
    lt = t - start
    keys = p.get("keys", {})
    reduced = opts.reduced
    x = track(keys.get("x"), lt, 0.0)
    y = track(keys.get("y"), lt, 0.0)
    s = track(keys.get("s"), lt, 1.0)
    sx = track(keys.get("sx"), lt, 1.0) * s
    sy = track(keys.get("sy"), lt, 1.0) * s
    rot = p.get("rot", 0.0) + track(keys.get("rot"), lt, 0.0)
    a = track(keys.get("a"), lt, 1.0) * p.get("alpha", 1.0)
    if "pulse" in p:
        amp, fq = p["pulse"][:2]
        k = 1 + amp * (0.5 if reduced else 1) * math.sin(lt * fq * 2 * math.pi)
        sx *= k
        sy *= k
    if "beat" in p:
        amp, fq = p["beat"]
        k = 1 + amp * (0.4 if reduced else 1) * beat(lt * fq)
        sx *= k
        sy *= k
    if "squash" in p:
        amp, fq = p["squash"]
        k = amp * math.sin(lt * fq * 2 * math.pi)
        sx *= 1 + k
        sy *= 1 - k
    if "bob" in p:
        amp, fq = p["bob"][:2]
        ph = p["bob"][2] if len(p["bob"]) > 2 else 0
        y += amp * math.sin((lt * fq + ph) * 2 * math.pi)
    if "sway" in p:
        amp, fq = p["sway"][:2]
        ph = p["sway"][2] if len(p["sway"]) > 2 else 0
        rot += amp * math.sin((lt * fq + ph) * 2 * math.pi)
    if "spin" in p:
        rot += p["spin"] * lt * (0.5 if reduced else 1)
    if "shake" in p and not reduced:
        amp, fq = p["shake"]
        x += amp * math.sin(lt * fq * 6.283 + 1.3) * math.sin(lt * fq * 2.1)
        y += amp * math.cos(lt * fq * 5.1) * math.sin(lt * fq * 1.7 + 0.4)
    if "flicker" in p and not reduced:
        amt, fq = p["flicker"]
        n = 0.5 + 0.5 * math.sin(lt * fq * 6.283) * math.sin(lt * fq * 2.7 + 1.1)
        a *= 1 - amt + amt * n
    if "seq" in p:
        period, phase = p["seq"][:2]
        lo = p["seq"][2] if len(p["seq"]) > 2 else 0.25
        hump = seq(lt / period - phase)
        a *= lo + (1 - lo) * hump
        k = 1 + 0.25 * hump * (0.5 if reduced else 1)
        sx *= k
        sy *= k
    if a <= 0.003 or sx == 0 or sy == 0:
        return
    base = p.get("pos", [0, 0, 0])
    pos, k = _face_adjust(p, opts, [base[0] + 0.0, base[1] + 0.0, base[2]])
    if pos is None:
        return
    anchor = p.get("anchor", "above")
    billboard = anchor in ("above", "side")
    size = p.get("size", [4, 4])
    if not isinstance(size, list):
        size = [size, size]
    sc = (opts.scale if billboard else 1.0) * k
    w, h = size[0] * sx * sc, size[1] * sy * sc
    off = p.get("offset", [0, 0])
    color = parse_color(p.get("color", "#ffffff"))
    tex = p["tex"]
    blend = p.get("blend", "normal")
    pivot = tuple(p.get("pivot", [0, 0]))
    copies = [1, -1] if p.get("mirror") else [1]
    for m in copies:
        if billboard:
            q_pos = [pos[0] * m, pos[1], pos[2]]
            q_off = [(off[0] + x) * m * sc, (off[1] + y) * sc]
        else:
            q_pos = [(pos[0] + x * k) * m, pos[1] + y * k, pos[2]]
            q_off = [0, 0]
        r = rot * m
        flip = (m < 0) != bool(p.get("flip", False))
        g = p.get("glow", 0.0)
        if g > 0:
            out.append(quad(tex + "_glow", "add", anchor, q_pos, q_off, w * GLOW_PAD, h * GLOW_PAD, r, color,
                            a * g, flip, (pivot[0] / GLOW_PAD, pivot[1] / GLOW_PAD), billboard))
        out.append(quad(tex, blend, anchor, q_pos, q_off, w, h, r, color, a, flip, pivot, billboard))


def particle_life_curves(mode, u, grow):
    """returns (size multiplier, alpha multiplier) for normalized age u."""
    if mode == "flash":
        s = sstep(0, 0.18, u) * (1.25 - 0.45 * u)
        return s, 1 - sstep(0.45, 1.0, u)
    if mode == "grow":
        return 1 + (grow - 1) * (1 - (1 - u) ** 2), sstep(0, 0.08, u) * (1 - sstep(0.35, 1.0, u))
    if mode == "shrink":
        return 1 - u, sstep(0, 0.1, u)
    if mode == "fade":
        return 1.0, sstep(0, 0.2, u) * (1 - sstep(0.6, 1.0, u))
    # pop
    s = sstep(0, 0.15, u) * (1 + 0.15 * math.sin(clamp(u / 0.3, 0, 1) * math.pi)) * (1 - sstep(0.75, 1.0, u) * 0.7)
    return s, sstep(0, 0.08, u) * (1 - sstep(0.7, 1.0, u))


def eval_emitter(e, t, opts, out, ei):
    start, end = e.get("start", 0.0), e.get("end", 1e9)
    seed = e.get("seed", 17 + ei * 31)
    mode = e.get("mode", "stream")
    life = e.get("life", [0.6, 0.6])
    anchor = e.get("anchor", "above")
    billboard = anchor in ("above", "side")
    pos = e.get("pos", [0, 0, 0])
    tex, blend = e["tex"], e.get("blend", "add")
    colors = [parse_color(c) for c in (e["color"] if isinstance(e.get("color"), list) else [e.get("color", "#ffffff")])]
    size = e.get("size", [2, 2])
    speed = e.get("speed", [0, 0])
    direction, spread = e.get("dir", 0.0), e.get("spread", 360.0)
    gravity = e.get("gravity", 0.0)
    box = e.get("box", [0, 0])
    curve, grow = e.get("curve", "pop"), e.get("grow", 2.0)
    spin = e.get("spin", [0, 0])
    stretch = e.get("stretch", 0.0)
    mirror = e.get("mirror", False)
    wob = e.get("wobble", [0, 0])
    alpha0 = e.get("alpha", 1.0)
    glow = e.get("glow", 0.0)
    sc = opts.scale if billboard else 1.0
    spawns = []
    if mode == "stream":
        rate = e.get("rate", 5.0) * (opts.budget if e.get("optional", True) else 1)
        if rate > 0:
            lmax = life[1]
            i0 = max(0, int(math.floor((t - lmax - start) * rate)))
            i1 = int(math.floor((min(t, end) - start) * rate))
            for i in range(i0, i1 + 1):
                spawns.append((i, start + i / rate))
    elif mode == "burst":
        times = list(e.get("times", []))
        if "every" in e:
            tt = start
            while tt <= end + 1e-6 and len(times) < 64:
                times.append(tt)
                tt += e["every"]
        count = e.get("count", 6)
        if e.get("optional", False):
            count = max(1, int(round(count * opts.budget)))
        for bi, bt in enumerate(times):
            for j in range(count):
                spawns.append((bi * 97 + j, bt))
    elif mode == "orbit":
        count = e.get("count", 4)
        if start <= t <= end:
            r = e.get("radius", [6, 2])
            om = e.get("omega", 90.0) * (0.5 if opts.reduced else 1)
            sz = size[0]
            lt = t - start
            fade = sstep(0, 0.3, lt) * (1 - sstep(end - start - 0.3, end - start, lt)) if end < 1e8 else sstep(0, 0.3, lt)
            for j in range(count):
                ang = math.radians(om * lt + 360.0 * j / count)
                px = pos[0] + math.cos(ang) * r[0]
                pz = pos[2] + math.sin(ang) * r[1]
                py = pos[1] + (r[2] if len(r) > 2 else 0) * math.sin(ang * 2)
                col = colors[j % len(colors)]
                rr = spin[0] * lt + j * 40
                if glow > 0:
                    out.append(quad(tex + "_glow", "add", anchor, [px, py, pz], [0, 0], sz * GLOW_PAD * sc, sz * GLOW_PAD * sc, rr, col, alpha0 * fade * glow))
                out.append(quad(tex, blend, anchor, [px, py, pz], [0, 0], sz * sc, sz * sc, rr, col, alpha0 * fade, billboard=True))
        return
    for (i, t0) in spawns:
        if t0 < start - 1e-6 or t0 > end + 1e-6:
            continue
        L = lerp(life[0], life[1], rnd(seed, i, 1))
        age = t - t0
        if age < 0 or age >= L:
            continue
        u = age / L
        ang = math.radians(direction + (rnd(seed, i, 2) - 0.5) * spread)
        v = lerp(speed[0], speed[1], rnd(seed, i, 3))
        vx, vy = math.sin(ang) * v, math.cos(ang) * v
        ox = (rnd(seed, i, 4) - 0.5) * box[0]
        oy = (rnd(seed, i, 5) - 0.5) * box[1]
        px = ox + vx * age
        py = oy + vy * age - 0.5 * gravity * age * age
        if wob[0]:
            px += wob[0] * math.sin((age * wob[1] + rnd(seed, i, 9)) * 6.283)
        smul, amul = particle_life_curves(curve, u, grow)
        sz = lerp(size[0], size[1], rnd(seed, i, 6)) * smul
        if sz <= 0.01:
            continue
        col = colors[int(rnd(seed, i, 7) * len(colors)) % len(colors)]
        rr = lerp(spin[0], spin[1], rnd(seed, i, 8)) * age + rnd(seed, i, 10) * e.get("rot_jitter", 0.0)
        w = h = sz
        if stretch:
            cvx, cvy = vx, vy - gravity * age
            rr = -math.degrees(math.atan2(cvx, cvy))
            h = sz * (1 + stretch * math.hypot(cvx, cvy) / max(1e-3, max(abs(speed[1]), 1)))
            w = sz * 0.35
        m = -1 if (mirror and i % 2 == 1) else 1
        a = alpha0 * amul
        if billboard and e.get("screen", True):
            qp, qo = [pos[0] * m, pos[1], pos[2]], [px * m * sc, py * sc]
        else:
            qp, qo = [pos[0] * m + px * m, pos[1] + py, pos[2]], [0, 0]
        if glow > 0:
            out.append(quad(tex + "_glow", "add", anchor, qp, qo, w * GLOW_PAD * sc, h * GLOW_PAD * sc, rr * m, col, a * glow, m < 0, billboard=billboard))
        out.append(quad(tex, blend, anchor, qp, qo, w * sc, h * sc, rr * m, col, a, m < 0, billboard=billboard))


def evaluate(em, t, opts=None):
    opts = opts or Opts()
    out = []
    env = envelope(em, t)
    if env <= 0:
        return out
    layers = em.get("layers", [])
    for li, layer in enumerate(layers):
        if "tex" in layer and "mode" in layer:
            eval_emitter(layer, t, opts, out, li)
        else:
            eval_part(layer, t, opts, out)
    for q in out:
        q["alpha"] *= env
    return out
