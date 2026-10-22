package su.rubycon.emotes.client;

import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import su.rubycon.emotes.EmoteIndex;
import su.rubycon.emotes.EmotesConfig;
import su.rubycon.emotes.net.EmoteNetwork;

import java.util.*;

/** Client mirror of server emote state plus local request throttling and preview overrides. */
public final class ClientEmotes {
    public record Playing(String id, long startMs, int durationMs) {
        public float time(long now) { return (now - startMs) / 1000f; }
        public boolean expired(long now) { return now - startMs >= durationMs; }
        public float progress(long now) { return Math.min(1f, (now - startMs) / (float) durationMs); }
    }

    private static final Map<Integer, Playing> ACTIVE = new HashMap<>();
    private static EmoteNetwork.Sync sync;
    private static long lastRequest;
    private static int renderedLastFrame, renderedThisFrame;

    /** Set while a menu preview renders the local player; never sent to the server. */
    public static Playing previewOverride;

    public static void onState(EmoteNetwork.State s) {
        if (s.id().isEmpty()) ACTIVE.remove(s.entityId());
        else ACTIVE.put(s.entityId(), new Playing(s.id(), System.currentTimeMillis() - s.elapsedMs(), s.durationMs()));
    }

    public static void onSync(EmoteNetwork.Sync s) { sync = s; }

    public static void clear() {
        ACTIVE.clear();
        previewOverride = null;
    }

    public static void onDisconnect() {
        clear();
        sync = null;
    }

    public static Playing get(int entityId) {
        Playing p = ACTIVE.get(entityId);
        if (p != null && p.expired(System.currentTimeMillis())) { ACTIVE.remove(entityId); return null; }
        return p;
    }

    public static Playing own() {
        var pl = Minecraft.getInstance().player;
        return pl == null ? null : get(pl.getId());
    }

    // ------------------------------------------------------------------ server rules
    public static boolean serverReady() { return sync != null; }
    public static boolean enabled() { return sync != null && sync.enabled(); }
    public static int distance() { return sync != null ? sync.distance() : 24; }
    public static int cooldownMs() { return sync != null ? sync.cooldownMs() : 2000; }

    /** Emotes the player may pick: server list when known, otherwise the bundled index. */
    public static List<String> ids() {
        List<String> out = new ArrayList<>();
        if (sync != null) for (EmoteNetwork.Entry e : sync.entries()) out.add(e.id());
        else for (EmoteIndex.Info i : EmoteIndex.all()) out.add(i.id());
        out.removeIf(id -> EmoteDefs.get(id) == null);
        return out;
    }

    public static boolean allowed(String id) {
        if (sync == null) return false;
        for (EmoteNetwork.Entry e : sync.entries()) if (e.id().equals(id)) return e.allowed() && sync.enabled();
        return false;
    }

    public static int durationMs(String id) {
        if (sync != null) for (EmoteNetwork.Entry e : sync.entries()) if (e.id().equals(id)) return e.durationMs();
        EmoteDef d = EmoteDefs.get(id);
        return d == null ? 4000 : Math.round(d.duration * 1000);
    }

    public static float cooldownLeft() {
        long left = lastRequest + cooldownMs() - System.currentTimeMillis();
        return left <= 0 ? 0 : left / 1000f;
    }

    /** @return null when sent, otherwise a user-facing reason */
    public static Component request(String id) {
        if (!serverReady()) return Component.translatable("rubycon_emotes.msg.no_server");
        if (!enabled()) return Component.translatable("rubycon_emotes.msg.disabled");
        if (!allowed(id)) return Component.translatable("rubycon_emotes.msg.unknown");
        float cd = cooldownLeft();
        if (cd > 0) return Component.translatable("rubycon_emotes.msg.cooldown_left", String.format(Locale.ROOT, "%.1f", cd));
        lastRequest = System.currentTimeMillis();
        EmoteNetwork.CH.sendToServer(new EmoteNetwork.Play(id));
        return null;
    }

    public static void cancel() {
        if (serverReady() && own() != null) EmoteNetwork.CH.sendToServer(new EmoteNetwork.Play(""));
    }

    // ------------------------------------------------------------------ favourites
    public static List<String> favorites() { return EmotesConfig.favorites(); }

    public static boolean isFavorite(String id) { return favorites().contains(id); }

    public static boolean toggleFavorite(String id) {
        List<String> f = new ArrayList<>(favorites());
        boolean added;
        if (f.remove(id)) added = false;
        else if (f.size() < 8) { f.add(id); added = true; }
        else return false;
        EmotesConfig.setFavorites(f);
        return added;
    }

    public static void moveFavorite(String id, int delta) {
        List<String> f = new ArrayList<>(favorites());
        int i = f.indexOf(id), j = i + delta;
        if (i < 0 || j < 0 || j >= f.size()) return;
        Collections.swap(f, i, j);
        EmotesConfig.setFavorites(f);
    }

    // ------------------------------------------------------------------ load budget
    public static void countRendered() { renderedThisFrame++; }

    public static void endFrame() {
        renderedLastFrame = renderedThisFrame;
        renderedThisFrame = 0;
    }

    /** Secondary particles thin out once more than ten emotes are on screen. */
    public static float budget() {
        int n = renderedLastFrame;
        return n <= 10 ? 1f : Math.max(0.35f, 1f - (n - 10) / 30f);
    }

    private ClientEmotes() {}
}
