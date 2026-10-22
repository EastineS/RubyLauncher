package su.rubycon.emotes.client;

import su.rubycon.emotes.client.EmoteDef.*;

import java.util.ArrayList;
import java.util.List;

/** Stateless evaluator: (definition, time) -> quads. Mirrors art/anim.py so previews match the game. */
public final class EmoteAnimator {
    public static final float GLOW_PAD = 1.5f;
    public static final float BILLBOARD_BIAS = 3.0f;

    public static final class Opts {
        public float scale = 1, budget = 1;
        public boolean reduced, helmet;
    }

    /** One textured quad; pos is in anchor space (px), off is the screen-plane offset for billboards. */
    public static final class Quad {
        public net.minecraft.resources.ResourceLocation tex;
        public Blend blend;
        public Anchor anchor;
        public boolean billboard, flip, lit;
        public float px, py, pz, ox, oy, w, h, rot, pvx, pvy, r, g, b, a;
    }

    /** Hard cap on quads per emote per frame, independent of what a definition asks for. */
    public static final int MAX_QUADS = 1024;

    /** Reused quad pool to avoid per-frame garbage. */
    public static final class Out {
        private final List<Quad> pool = new ArrayList<>();
        private final Quad overflow = new Quad();
        public int size;
        public Quad get(int i) { return pool.get(i); }
        boolean full() { return size >= MAX_QUADS; }
        Quad next() {
            if (full()) return overflow;  // written but never drawn
            if (size == pool.size()) pool.add(new Quad());
            return pool.get(size++);
        }
        public void clear() { size = 0; }
    }

    // ------------------------------------------------------------------ math helpers
    static double rnd(int seed, int i, int k) {
        int h = seed * 0x9E3779B1 + i * 0x85EBCA77 + k * 0xC2B2AE3D;
        h ^= h >>> 15;
        h *= 0x2C1B3C6D;
        h ^= h >>> 12;
        h *= 0x297A2D39;
        h ^= h >>> 15;
        return (h & 0xFFFFFFFFL) / 4294967296.0;
    }

    static float lerp(float a, float b, float t) { return a + (b - a) * t; }
    static float clamp(float x, float a, float b) { return x < a ? a : Math.min(x, b); }

    static float sstep(float e0, float e1, float x) {
        if (e0 == e1) return x >= e1 ? 1 : 0;
        float t = clamp((x - e0) / (e1 - e0), 0, 1);
        return t * t * (3 - 2 * t);
    }

    static byte easeId(String s) {
        return switch (s) {
            case "out" -> 1; case "in" -> 2; case "inout" -> 3; case "back" -> 4; case "bounce" -> 5; case "step" -> 6;
            default -> 0;
        };
    }

    static float ease(byte id, float t) {
        switch (id) {
            case 1: return 1 - (1 - t) * (1 - t) * (1 - t);
            case 2: return t * t * t;
            case 3: return t < 0.5f ? 4 * t * t * t : 1 - (float) Math.pow(-2 * t + 2, 3) / 2;
            case 4: { float u = t - 1; return 1 + 2.9f * u * u * u + 1.9f * u * u; }
            case 5: {
                float n = 7.5625f, d = 2.75f;
                if (t < 1 / d) return n * t * t;
                if (t < 2 / d) { t -= 1.5f / d; return n * t * t + 0.75f; }
                if (t < 2.5f / d) { t -= 2.25f / d; return n * t * t + 0.9375f; }
                t -= 2.625f / d; return n * t * t + 0.984375f;
            }
            case 6: return 0;
            default: return t;
        }
    }

    static float track(Track k, float t, float def) {
        if (k == null || k.t.length == 0) return def;
        if (t <= k.t[0]) return k.v[0];
        for (int i = 1; i < k.t.length; i++) {
            if (t < k.t[i]) {
                float u = (t - k.t[i - 1]) / Math.max(1e-6f, k.t[i] - k.t[i - 1]);
                return lerp(k.v[i - 1], k.v[i], ease(k.e[i], u));
            }
        }
        return k.v[k.v.length - 1];
    }

    static float beat(float x) {
        float f = x - (float) Math.floor(x);
        return (float) (Math.exp(-sq((f - 0.08f) / 0.05f)) + 0.6 * Math.exp(-sq((f - 0.26f) / 0.06f)));
    }

    static float seq(float x, float duty) {
        float f = x - (float) Math.floor(x);
        return sstep(0, duty * 0.35f, f) * (1 - sstep(duty * 0.65f, duty, f));
    }

    private static float sq(float v) { return v * v; }
    private static final float TAU = (float) (Math.PI * 2);

    public static float envelope(EmoteDef em, float t) {
        return sstep(0, em.fadeIn, t) * (1 - sstep(em.duration - em.fadeOut, em.duration, t));
    }

    // ------------------------------------------------------------------ evaluation
    public static void evaluate(EmoteDef em, float t, Opts o, Out out) {
        out.clear();
        float env = envelope(em, t);
        if (env <= 0) return;
        for (Layer l : em.layers) {
            if (l.mode == Mode.PART) part(l, t, o, out);
            else emitter(l, t, o, out);
        }
        for (int i = 0; i < out.size; i++) out.get(i).a *= env;
    }

    private static void emit(Out out, Layer l, boolean glow, Anchor anchor, boolean billboard, float px, float py, float pz,
                             float ox, float oy, float w, float h, float rot, float[] col, float a, boolean flip, float pvx, float pvy) {
        emit(out, l, -1, glow, anchor, billboard, px, py, pz, ox, oy, w, h, rot, col, a, flip, pvx, pvy);
    }

    private static void emit(Out out, Layer l, int frame, boolean glow, Anchor anchor, boolean billboard, float px, float py, float pz,
                             float ox, float oy, float w, float h, float rot, float[] col, float a, boolean flip, float pvx, float pvy) {
        Quad q = out.next();
        if (frame >= 0 && l.frames != null) q.tex = glow ? l.glowFrames[frame] : l.frames[frame];
        else q.tex = glow ? l.glowTex : l.tex;
        q.blend = glow ? Blend.ADD : l.blend;
        q.anchor = anchor; q.billboard = billboard; q.flip = flip;
        q.lit = !glow && l.lit;
        q.px = px; q.py = py; q.pz = pz; q.ox = ox; q.oy = oy; q.w = w; q.h = h; q.rot = rot;
        q.pvx = pvx; q.pvy = pvy;
        q.r = col[0]; q.g = col[1]; q.b = col[2]; q.a = a * col[3];
    }

    private static void part(Layer p, float t, Opts o, Out out) {
        if (t < p.start || t > p.end) return;
        float lt = t - p.start;
        boolean reduced = o.reduced;
        float x = track(p.tx, lt, 0), y = track(p.ty, lt, 0);
        float s = track(p.ts, lt, 1);
        float sx = track(p.tsx, lt, 1) * s, sy = track(p.tsy, lt, 1) * s;
        float rot = p.rot + track(p.trot, lt, 0);
        float a = track(p.ta, lt, 1) * p.alpha;
        if (p.pulse != null) {
            float k = 1 + p.pulse[0] * (reduced ? 0.5f : 1) * (float) Math.sin(lt * p.pulse[1] * TAU);
            sx *= k; sy *= k;
        }
        if (p.beat != null) {
            float k = 1 + p.beat[0] * (reduced ? 0.4f : 1) * beat(lt * p.beat[1]);
            sx *= k; sy *= k;
        }
        if (p.squash != null) {
            float k = p.squash[0] * (float) Math.sin(lt * p.squash[1] * TAU);
            sx *= 1 + k; sy *= 1 - k;
        }
        if (p.bob != null) {
            float ph = p.bob.length > 2 ? p.bob[2] : 0;
            y += p.bob[0] * (float) Math.sin((lt * p.bob[1] + ph) * TAU);
        }
        if (p.sway != null) {
            float ph = p.sway.length > 2 ? p.sway[2] : 0;
            rot += p.sway[0] * (float) Math.sin((lt * p.sway[1] + ph) * TAU);
        }
        if (p.hasSpin) rot += p.spin * lt * (reduced ? 0.5f : 1);
        if (p.shake != null && !reduced) {
            float amp = p.shake[0], fq = p.shake[1];
            x += amp * (float) (Math.sin(lt * fq * 6.283 + 1.3) * Math.sin(lt * fq * 2.1));
            y += amp * (float) (Math.cos(lt * fq * 5.1) * Math.sin(lt * fq * 1.7 + 0.4));
        }
        if (p.flicker != null && !reduced) {
            float n = 0.5f + 0.5f * (float) (Math.sin(lt * p.flicker[1] * 6.283) * Math.sin(lt * p.flicker[1] * 2.7 + 1.1));
            a *= 1 - p.flicker[0] + p.flicker[0] * n;
        }
        if (p.seq != null) {
            float lo = p.seq.length > 2 ? p.seq[2] : 0.25f;
            float hump = seq(lt / p.seq[0] - p.seq[1], 0.45f);
            a *= lo + (1 - lo) * hump;
            float k = 1 + 0.25f * hump * (reduced ? 0.5f : 1);
            sx *= k; sy *= k;
        }
        if (a <= 0.003f || sx == 0 || sy == 0) return;

        float bx = p.pos[0], by = p.pos[1], bz = p.pos[2], k = 1;
        if (o.helmet && (p.anchor == Anchor.FACE || p.anchor == Anchor.HEAD)) {
            if (p.helmet == Helmet.HIDE) return;
            if (p.helmet == Helmet.PUSH) { bx *= 1.15f; by *= 1.15f; bz += 1.1f; k = 1.15f; }
        }
        boolean bill = p.anchor.billboard();
        float sc = (bill ? o.scale : 1) * k;
        float w = p.size[0] * sx * sc, h = p.size[1] * sy * sc;
        float[] col = p.colors[0];
        int frame = p.frames == null ? -1 : p.frameSeq[(int) Math.floor(lt * p.fps) % p.frameSeq.length];
        for (int m = 1; m >= -1; m -= 2) {
            if (m < 0 && !p.mirror) break;
            float qpx, qpy, qpz, qox, qoy;
            if (bill) {
                qpx = bx * m; qpy = by; qpz = bz;
                qox = (p.offset[0] + x) * m * sc; qoy = (p.offset[1] + y) * sc;
            } else {
                qpx = (bx + x * k) * m; qpy = by + y * k; qpz = bz;
                qox = 0; qoy = 0;
            }
            float r = rot * m;
            boolean flip = (m < 0) != p.flip;
            if (p.glow > 0)
                emit(out, p, frame, true, p.anchor, bill, qpx, qpy, qpz, qox, qoy, w * GLOW_PAD, h * GLOW_PAD, r, col, a * p.glow, flip,
                        p.pivot[0] / GLOW_PAD, p.pivot[1] / GLOW_PAD);
            emit(out, p, frame, false, p.anchor, bill, qpx, qpy, qpz, qox, qoy, w, h, r, col, a, flip, p.pivot[0], p.pivot[1]);
        }
    }

    private static float curveSize(Curve c, float u, float grow) {
        return switch (c) {
            case FLASH -> sstep(0, 0.18f, u) * (1.25f - 0.45f * u);
            case GROW -> 1 + (grow - 1) * (1 - (1 - u) * (1 - u));
            case SHRINK -> 1 - u;
            case FADE -> 1;
            default -> sstep(0, 0.15f, u) * (1 + 0.15f * (float) Math.sin(clamp(u / 0.3f, 0, 1) * Math.PI)) * (1 - sstep(0.75f, 1, u) * 0.7f);
        };
    }

    private static float curveAlpha(Curve c, float u) {
        return switch (c) {
            case FLASH -> 1 - sstep(0.45f, 1, u);
            case GROW -> sstep(0, 0.08f, u) * (1 - sstep(0.35f, 1, u));
            case SHRINK -> sstep(0, 0.1f, u);
            case FADE -> sstep(0, 0.2f, u) * (1 - sstep(0.6f, 1, u));
            default -> sstep(0, 0.08f, u) * (1 - sstep(0.7f, 1, u));
        };
    }

    private static void emitter(Layer e, float t, Opts o, Out out) {
        float start = e.start, end = e.end;
        boolean bill = e.anchor.billboard();
        float sc = bill ? o.scale : 1;
        int seed = e.seed;
        if (e.mode == Mode.ORBIT) {
            if (t < start || t > end) return;
            float om = e.omega * (o.reduced ? 0.5f : 1);
            float lt = t - start;
            float fade = end < 1e8f ? sstep(0, 0.3f, lt) * (1 - sstep(end - start - 0.3f, end - start, lt)) : sstep(0, 0.3f, lt);
            float sz = e.psize[0];
            for (int j = 0; j < e.count && !out.full(); j++) {
                double ang = Math.toRadians(om * lt + 360.0 * j / e.count);
                float px = e.pos[0] + (float) Math.cos(ang) * e.radius[0];
                float pz = e.pos[2] + (float) Math.sin(ang) * e.radius[1];
                float py = e.pos[1] + e.radius[2] * (float) Math.sin(ang * 2);
                float[] col = e.colors[j % e.colors.length];
                float rr = e.spinR[0] * lt + j * 40;
                float ox = e.offset[0] * sc, oy = e.offset[1] * sc;
                if (e.glow > 0)
                    emit(out, e, true, e.anchor, bill, px, py, pz, ox, oy, sz * GLOW_PAD * sc, sz * GLOW_PAD * sc, rr, col, e.alpha * fade * e.glow, false, 0, 0);
                emit(out, e, false, e.anchor, bill, px, py, pz, ox, oy, sz * sc, sz * sc, rr, col, e.alpha * fade, false, 0, 0);
            }
            return;
        }
        if (e.mode == Mode.STREAM) {
            float rate = e.rate * (e.optional ? o.budget : 1);
            if (rate <= 0) return;
            int i0 = Math.max(0, (int) Math.floor((t - e.life[1] - start) * rate));
            int i1 = (int) Math.floor((Math.min(t, end) - start) * rate);
            for (int i = i0; i <= i1 && !out.full(); i++) particle(e, t, o, out, i, start + i / rate, bill, sc);
        } else {
            int count = e.optional ? Math.max(1, Math.round(e.count * o.budget)) : e.count;
            int bi = 0;
            for (float bt : e.times) { for (int j = 0; j < count && !out.full(); j++) particle(e, t, o, out, bi * 97 + j, bt, bill, sc); bi++; }
            if (e.every > 0) {
                float tt = start;
                // continues numbering after explicit times, matching the python list order
                while (tt <= end + 1e-6f && bi < 64 + e.times.length) {
                    for (int j = 0; j < count && !out.full(); j++) particle(e, t, o, out, bi * 97 + j, tt, bill, sc);
                    tt += e.every;
                    bi++;
                }
            }
        }
    }

    private static void particle(Layer e, float t, Opts o, Out out, int i, float t0, boolean bill, float sc) {
        if (t0 < e.start - 1e-6f || t0 > e.end + 1e-6f) return;
        float L = lerp(e.life[0], e.life[1], (float) rnd(e.seed, i, 1));
        float age = t - t0;
        if (age < 0 || age >= L) return;
        float u = age / L;
        double ang = Math.toRadians(e.dir + (rnd(e.seed, i, 2) - 0.5) * e.spread);
        float v = lerp(e.speed[0], e.speed[1], (float) rnd(e.seed, i, 3));
        float vx = (float) Math.sin(ang) * v, vy = (float) Math.cos(ang) * v;
        float ox = (float) (rnd(e.seed, i, 4) - 0.5) * e.box[0];
        float oy = (float) (rnd(e.seed, i, 5) - 0.5) * e.box[1];
        float px = ox + vx * age;
        float py = oy + vy * age - 0.5f * e.gravity * age * age;
        if (e.wobble[0] != 0) px += e.wobble[0] * (float) Math.sin((age * e.wobble[1] + rnd(e.seed, i, 9)) * 6.283);
        float smul = curveSize(e.curve, u, e.grow), amul = curveAlpha(e.curve, u);
        float sz = lerp(e.psize[0], e.psize[1], (float) rnd(e.seed, i, 6)) * smul;
        if (sz <= 0.01f) return;
        float[] col = e.colors[((int) (rnd(e.seed, i, 7) * e.colors.length)) % e.colors.length];
        float rr = lerp(e.spinR[0], e.spinR[1], (float) rnd(e.seed, i, 8)) * age + (float) rnd(e.seed, i, 10) * e.rotJitter;
        float w = sz, h = sz;
        if (e.stretch != 0) {
            float cvx = vx, cvy = vy - e.gravity * age;
            rr = (float) -Math.toDegrees(Math.atan2(cvx, cvy));
            h = sz * (1 + e.stretch * (float) Math.hypot(cvx, cvy) / Math.max(1e-3f, Math.max(Math.abs(e.speed[1]), 1)));
            w = sz * 0.35f;
        }
        int m = (e.mirror && i % 2 == 1) ? -1 : 1;
        float a = e.alpha * amul;
        float qpx, qpy, qpz, qox, qoy;
        if (bill && e.screen) { qpx = e.pos[0] * m; qpy = e.pos[1]; qpz = e.pos[2]; qox = (px + e.offset[0]) * m * sc; qoy = (py + e.offset[1]) * sc; }
        else { qpx = e.pos[0] * m + px * m; qpy = e.pos[1] + py; qpz = e.pos[2]; qox = 0; qoy = 0; }
        if (e.glow > 0)
            emit(out, e, true, e.anchor, bill, qpx, qpy, qpz, qox, qoy, w * GLOW_PAD * sc, h * GLOW_PAD * sc, rr * m, col, a * e.glow, m < 0, 0, 0);
        emit(out, e, false, e.anchor, bill, qpx, qpy, qpz, qox, qoy, w * sc, h * sc, rr * m, col, a, m < 0, 0, 0);
    }

    private EmoteAnimator() {}
}
