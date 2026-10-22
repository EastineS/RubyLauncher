package su.rubycon.emotes.server;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Per-player activation timestamps. Entries outlive the session on purpose: clearing them on
 * logout would let a player reset the cooldown by relogging. {@link #prune} drops entries once
 * their window has passed, which keeps the map bounded.
 */
final class Cooldowns {
    private final Map<UUID, Long> last = new HashMap<>();

    /** Records an activation at {@code now} unless the player is still cooling down. */
    boolean tryAcquire(UUID player, long now, long cooldownMs) {
        Long t = last.get(player);
        if (t != null && now - t < cooldownMs) return false;
        last.put(player, now);
        return true;
    }

    void prune(long now, long cooldownMs) {
        last.values().removeIf(t -> now - t >= cooldownMs);
    }

    void clear() { last.clear(); }

    int size() { return last.size(); }
}
