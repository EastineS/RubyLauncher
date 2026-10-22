package su.rubycon.emotes.server;

import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class CooldownsTest {
    private static final UUID A = UUID.randomUUID(), B = UUID.randomUUID();

    @Test
    void enforcesWindowPerPlayer() {
        Cooldowns c = new Cooldowns();
        assertTrue(c.tryAcquire(A, 1000, 2000));
        assertFalse(c.tryAcquire(A, 2999, 2000));
        assertTrue(c.tryAcquire(B, 2999, 2000));
        assertTrue(c.tryAcquire(A, 3000, 2000));
    }

    /** Logout no longer clears history: a relog inside the window is still refused. */
    @Test
    void historySurvivesUntilWindowPasses() {
        Cooldowns c = new Cooldowns();
        assertTrue(c.tryAcquire(A, 1000, 2000));
        c.prune(2500, 2000);  // periodic cleanup during the window keeps the entry
        assertFalse(c.tryAcquire(A, 2500, 2000));
        c.prune(3000, 2000);  // after the window it is dropped
        assertEquals(0, c.size());
        assertTrue(c.tryAcquire(A, 3000, 2000));
    }
}
