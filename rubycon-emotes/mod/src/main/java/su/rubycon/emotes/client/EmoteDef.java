package su.rubycon.emotes.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import net.minecraft.resources.ResourceLocation;

import java.util.ArrayList;
import java.util.List;

/** Parsed emote definition (assets/&lt;ns&gt;/emotes/&lt;id&gt;.json). Field meanings match art/anim.py. */
public final class EmoteDef {
    public enum Anchor { ABOVE, SIDE, FACE, HEAD;
        public boolean billboard() { return this == ABOVE || this == SIDE; }
    }
    public enum Blend { NORMAL, ADD }
    public enum Mode { PART, STREAM, BURST, ORBIT }
    public enum Curve { POP, FLASH, GROW, SHRINK, FADE }
    public enum Helmet { PUSH, KEEP, HIDE }

    /** keyframe track: times, values, ease ids */
    public static final class Track {
        final float[] t, v; final byte[] e;
        Track(float[] t, float[] v, byte[] e) { this.t = t; this.v = v; this.e = e; }
    }

    public static final class Layer {
        public Mode mode = Mode.PART;
        public ResourceLocation tex, glowTex;
        public Blend blend = Blend.NORMAL;
        public Anchor anchor = Anchor.ABOVE;
        public Helmet helmet = Helmet.PUSH;
        public float[] pos = {0, 0, 0}, offset = {0, 0}, size = {4, 4}, pivot = {0, 0};
        public float[][] colors = {{1, 1, 1, 1}};
        public float alpha = 1, rot = 0, glow = 0, start = 0, end = 1e9f;
        public boolean mirror, flip;
        /** world-lit (face/head marks) rather than full-bright */
        public boolean lit;
        // part modifiers (null = absent)
        public float[] pulse, beat, squash, bob, sway, shake, flicker, seq;
        public float spin;
        public boolean hasSpin;
        public Track tx, ty, ts, tsx, tsy, trot, ta;
        // emitter
        public int seed, count = 6;
        public float rate = 5, every = -1, dir = 0, spread = 360, gravity = 0, grow = 2, stretch = 0, rotJitter = 0;
        public float[] life = {0.6f, 0.6f}, psize = {2, 2}, speed = {0, 0}, box = {0, 0}, spinR = {0, 0}, wobble = {0, 0}, radius = {6, 2, 0};
        public float[] times = new float[0];
        public float omega = 90;
        public Curve curve = Curve.POP;
        public boolean screen = true, optional;
    }

    public final String id;
    public final float duration, fadeIn, fadeOut, iconTime;
    public final int color;
    public final List<Layer> layers;
    public final ResourceLocation icon;

    EmoteDef(String id, float duration, float fadeIn, float fadeOut, float iconTime, int color, List<Layer> layers, ResourceLocation icon) {
        this.id = id; this.duration = duration; this.fadeIn = fadeIn; this.fadeOut = fadeOut; this.iconTime = iconTime;
        this.color = color; this.layers = layers; this.icon = icon;
    }

    // Workload limits: definitions come from resource packs, so every value that drives a loop is bounded here.
    static final int MAX_LAYERS = 64, MAX_COUNT = 64, MAX_TIMES = 32, MAX_KEYS = 64;
    static final float MAX_RATE = 40, MIN_LIFE = 0.05f, MAX_LIFE = 8, MIN_EVERY = 0.05f;

    // ------------------------------------------------------------------ parsing
    static EmoteDef parse(String ns, String id, JsonObject o) {
        List<Layer> layers = new ArrayList<>();
        JsonArray arr = o.getAsJsonArray("layers");
        int li = 0;
        if (arr != null) for (JsonElement el : arr) {
            if (layers.size() >= MAX_LAYERS) break;
            layers.add(layer(ns, el.getAsJsonObject(), li++));
        }
        return new EmoteDef(id, clamp(f(o, "duration", 4), 0.5f, 30f), f(o, "fade_in", 0.3f), f(o, "fade_out", 0.4f),
                f(o, "icon_time", 1f), argb(o.has("color") ? o.get("color").getAsString() : "#ffffff"), layers,
                new ResourceLocation(ns, "textures/icon/" + id + ".png"));
    }

    private static Layer layer(String ns, JsonObject o, int index) {
        Layer l = new Layer();
        String tex = o.get("tex").getAsString();
        ResourceLocation base = tex.contains(":") ? new ResourceLocation(tex) : new ResourceLocation(ns, tex);
        l.tex = new ResourceLocation(base.getNamespace(), "textures/" + base.getPath() + ".png");
        l.glowTex = new ResourceLocation(base.getNamespace(), "textures/" + base.getPath() + "_glow.png");
        if (o.has("mode")) l.mode = switch (o.get("mode").getAsString()) {
            case "burst" -> Mode.BURST; case "orbit" -> Mode.ORBIT; default -> Mode.STREAM;
        };
        boolean emitter = l.mode != Mode.PART;
        l.blend = "add".equals(str(o, "blend", emitter ? "add" : "normal")) ? Blend.ADD : Blend.NORMAL;
        l.anchor = switch (str(o, "anchor", "above")) {
            case "side" -> Anchor.SIDE; case "face" -> Anchor.FACE; case "head" -> Anchor.HEAD; default -> Anchor.ABOVE;
        };
        l.helmet = switch (str(o, "helmet", "push")) { case "keep" -> Helmet.KEEP; case "hide" -> Helmet.HIDE; default -> Helmet.PUSH; };
        l.pos = vec(o, "pos", l.pos, 3);
        l.offset = vec(o, "offset", l.offset, 2);
        l.pivot = vec(o, "pivot", l.pivot, 2);
        if (o.has("size")) {
            JsonElement s = o.get("size");
            float[] v = s.isJsonArray() ? vec(o, "size", l.size, 2) : new float[]{s.getAsFloat(), s.getAsFloat()};
            if (emitter) l.psize = v; else l.size = v;
        }
        if (o.has("color")) {
            JsonElement c = o.get("color");
            if (c.isJsonArray()) {
                l.colors = new float[c.getAsJsonArray().size()][];
                for (int i = 0; i < l.colors.length; i++) l.colors[i] = rgba(c.getAsJsonArray().get(i).getAsString());
            } else l.colors = new float[][]{rgba(c.getAsString())};
        }
        l.alpha = f(o, "alpha", 1); l.rot = f(o, "rot", 0); l.glow = f(o, "glow", 0);
        l.start = f(o, "start", 0); l.end = f(o, "end", 1e9f);
        l.mirror = b(o, "mirror"); l.flip = b(o, "flip");
        l.lit = o.has("lit") ? o.get("lit").getAsBoolean() : (l.anchor == Anchor.FACE || l.anchor == Anchor.HEAD);
        l.pulse = arr(o, "pulse"); l.beat = arr(o, "beat"); l.squash = arr(o, "squash"); l.bob = arr(o, "bob");
        l.sway = arr(o, "sway"); l.shake = arr(o, "shake"); l.flicker = arr(o, "flicker"); l.seq = arr(o, "seq");
        if (o.has("spin") && o.get("spin").isJsonPrimitive()) { l.spin = o.get("spin").getAsFloat(); l.hasSpin = true; }
        if (o.has("keys")) {
            JsonObject k = o.getAsJsonObject("keys");
            l.tx = track(k, "x"); l.ty = track(k, "y"); l.ts = track(k, "s"); l.tsx = track(k, "sx");
            l.tsy = track(k, "sy"); l.trot = track(k, "rot"); l.ta = track(k, "a");
        }
        if (emitter) {
            l.seed = o.has("seed") ? o.get("seed").getAsInt() : 17 + index * 31;
            l.count = o.has("count") ? Math.max(0, Math.min(MAX_COUNT, o.get("count").getAsInt())) : 6;
            l.rate = clamp(f(o, "rate", 5), 0, MAX_RATE);
            l.every = f(o, "every", -1);
            if (l.every > 0) l.every = Math.max(MIN_EVERY, l.every);
            l.dir = f(o, "dir", 0); l.spread = f(o, "spread", 360); l.gravity = f(o, "gravity", 0);
            l.grow = f(o, "grow", 2); l.stretch = f(o, "stretch", 0); l.rotJitter = f(o, "rot_jitter", 0);
            l.omega = f(o, "omega", 90);
            l.life = vec(o, "life", l.life, 2);
            l.life[0] = clamp(l.life[0], MIN_LIFE, MAX_LIFE); l.life[1] = clamp(l.life[1], l.life[0], MAX_LIFE);
            l.speed = vec(o, "speed", l.speed, 2); l.box = vec(o, "box", l.box, 2);
            if (o.has("spin") && o.get("spin").isJsonArray()) l.spinR = vec(o, "spin", l.spinR, 2);
            l.wobble = vec(o, "wobble", l.wobble, 2);
            if (o.has("radius")) {
                float[] r = arr(o, "radius");
                l.radius = new float[]{r[0], r.length > 1 ? r[1] : r[0], r.length > 2 ? r[2] : 0};
            }
            l.times = o.has("times") ? arr(o, "times") : new float[0];
            if (l.times.length > MAX_TIMES) l.times = java.util.Arrays.copyOf(l.times, MAX_TIMES);
            l.curve = switch (str(o, "curve", "pop")) {
                case "flash" -> Curve.FLASH; case "grow" -> Curve.GROW; case "shrink" -> Curve.SHRINK; case "fade" -> Curve.FADE;
                default -> Curve.POP;
            };
            l.screen = !o.has("screen") || o.get("screen").getAsBoolean();
            // streams are thinned by default under load, bursts only when marked optional
            l.optional = o.has("optional") ? o.get("optional").getAsBoolean() : l.mode == Mode.STREAM;
        }
        return l;
    }

    private static Track track(JsonObject k, String name) {
        if (!k.has(name)) return null;
        JsonArray a = k.getAsJsonArray(name);
        int n = Math.min(a.size(), MAX_KEYS);
        float[] t = new float[n], v = new float[n];
        byte[] e = new byte[n];
        for (int i = 0; i < n; i++) {
            JsonArray kf = a.get(i).getAsJsonArray();
            t[i] = finite(kf.get(0).getAsFloat(), 0);
            v[i] = finite(kf.get(1).getAsFloat(), 0);
            e[i] = kf.size() > 2 ? EmoteAnimator.easeId(kf.get(2).getAsString()) : 0;
        }
        return new Track(t, v, e);
    }

    private static float f(JsonObject o, String k, float d) { return o.has(k) ? finite(o.get(k).getAsFloat(), d) : d; }

    private static float finite(float v, float d) { return Float.isFinite(v) ? v : d; }
    private static boolean b(JsonObject o, String k) { return o.has(k) && o.get(k).getAsBoolean(); }
    private static String str(JsonObject o, String k, String d) { return o.has(k) ? o.get(k).getAsString() : d; }
    private static float clamp(float v, float a, float b) { return Math.max(a, Math.min(b, v)); }

    private static float[] arr(JsonObject o, String k) {
        if (!o.has(k)) return null;
        JsonArray a = o.getAsJsonArray(k);
        float[] out = new float[Math.min(a.size(), MAX_KEYS)];
        for (int i = 0; i < out.length; i++) out[i] = finite(a.get(i).getAsFloat(), 0);
        return out;
    }

    private static float[] vec(JsonObject o, String k, float[] d, int n) {
        float[] a = arr(o, k);
        if (a == null) return d;
        float[] out = d.clone();
        for (int i = 0; i < Math.min(n, a.length); i++) out[i] = a[i];
        return out;
    }

    static float[] rgba(String hex) {
        String h = hex.startsWith("#") ? hex.substring(1) : hex;
        float[] c = {1, 1, 1, 1};
        try {
            for (int i = 0; i < Math.min(4, h.length() / 2); i++) c[i] = Integer.parseInt(h.substring(i * 2, i * 2 + 2), 16) / 255f;
        } catch (NumberFormatException ignored) {}
        return c;
    }

    static int argb(String hex) {
        float[] c = rgba(hex);
        return 0xFF000000 | ((int) (c[0] * 255) << 16) | ((int) (c[1] * 255) << 8) | (int) (c[2] * 255);
    }
}
