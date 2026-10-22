package su.rubycon.emotes.client;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

/** Resource-pack definitions are untrusted: malformed arrays must not crash parsing or rendering. */
class EmoteDefTest {
    private static EmoteDef parse(String json) {
        return EmoteDef.parse("test", "t", JsonParser.parseString(json).getAsJsonObject());
    }

    /** Runs the animator across the whole duration, as the renderer would. */
    private static int evaluateAll(EmoteDef def) {
        EmoteAnimator.Out out = new EmoteAnimator.Out();
        EmoteAnimator.Opts opts = new EmoteAnimator.Opts();
        int max = 0;
        for (float t = 0; t <= def.duration; t += 0.05f) {
            EmoteAnimator.evaluate(def, t, opts, out);
            max = Math.max(max, out.size);
        }
        return max;
    }

    @Test
    void shortModifierArraysAreIgnored() {
        EmoteDef d = parse("{\"duration\":2,\"layers\":[{\"tex\":\"emote/x\",\"pulse\":[0.1],\"beat\":[],\"sway\":[5],"
                + "\"bob\":[0.2],\"squash\":[0.1],\"shake\":[1],\"flicker\":[0.5],\"seq\":[1]}]}");
        EmoteDef.Layer l = d.layers.get(0);
        assertNull(l.pulse);
        assertNull(l.beat);
        assertNull(l.sway);
        assertNull(l.seq);
        assertDoesNotThrow(() -> evaluateAll(d));
    }

    @Test
    void validModifiersAreKept() {
        EmoteDef d = parse("{\"duration\":2,\"layers\":[{\"tex\":\"emote/x\",\"pulse\":[0.1,2],\"bob\":[0.2,1,0.5]}]}");
        assertArrayEquals(new float[]{0.1f, 2}, d.layers.get(0).pulse);
        assertArrayEquals(new float[]{0.2f, 1, 0.5f}, d.layers.get(0).bob);
    }

    @Test
    void zeroSeqPeriodIsIgnored() {
        EmoteDef d = parse("{\"duration\":2,\"layers\":[{\"tex\":\"emote/x\",\"seq\":[0,0]}]}");
        assertNull(d.layers.get(0).seq);
        assertDoesNotThrow(() -> evaluateAll(d));
    }

    @Test
    void emptyColorListKeepsDefault() {
        EmoteDef d = parse("{\"duration\":2,\"layers\":[{\"tex\":\"emote/x\",\"color\":[]},"
                + "{\"tex\":\"fx/y\",\"mode\":\"stream\",\"rate\":10,\"color\":[]},"
                + "{\"tex\":\"fx/y\",\"mode\":\"orbit\",\"count\":3,\"color\":[]}]}");
        for (EmoteDef.Layer l : d.layers) assertTrue(l.colors.length > 0);
        assertTrue(evaluateAll(d) > 0);
    }

    @Test
    void emptyRadiusKeepsDefault() {
        EmoteDef d = assertDoesNotThrow(() -> parse("{\"duration\":2,\"layers\":[{\"tex\":\"fx/y\",\"mode\":\"orbit\",\"radius\":[]}]}"));
        assertEquals(3, d.layers.get(0).radius.length);
        assertDoesNotThrow(() -> evaluateAll(d));
    }

    @Test
    void hugeCountsStayWithinQuadBudget() {
        EmoteDef d = parse("{\"duration\":2,\"layers\":[{\"tex\":\"fx/y\",\"mode\":\"orbit\",\"count\":100000000},"
                + "{\"tex\":\"fx/y\",\"mode\":\"stream\",\"rate\":1e9,\"life\":[1e9,1e9]},"
                + "{\"tex\":\"fx/y\",\"mode\":\"burst\",\"count\":100000,\"every\":0.0001}]}");
        assertTrue(evaluateAll(d) <= EmoteAnimator.MAX_QUADS);
    }

    /** Extreme finite schedule values must not make the stream loop run forever (int saturation). */
    @Test
    @org.junit.jupiter.api.Timeout(value = 5)
    void extremeScheduleTerminates() {
        for (String start : new String[]{"-3e38", "3e38", "-1e9", "1e9"}) {
            EmoteDef d = parse("{\"duration\":2,\"layers\":[{\"tex\":\"fx/y\",\"mode\":\"stream\",\"rate\":40,"
                    + "\"start\":" + start + ",\"end\":3e38},"
                    + "{\"tex\":\"fx/y\",\"mode\":\"burst\",\"every\":0.05,\"start\":" + start + ",\"end\":3e38}]}");
            assertDoesNotThrow(() -> evaluateAll(d), start);
        }
    }

    /** Every bundled emote parses and evaluates without errors. */
    @Test
    void bundledEmotesEvaluate() throws IOException {
        JsonObject index;
        try (InputStream in = getClass().getResourceAsStream("/rubycon_emotes/index.json")) {
            assertNotNull(in);
            index = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
        }
        int n = 0;
        for (var e : index.getAsJsonArray("emotes")) {
            String id = e.getAsJsonObject().get("id").getAsString();
            try (InputStream in = getClass().getResourceAsStream("/assets/rubycon_emotes/emotes/" + id + ".json")) {
                assertNotNull(in, id);
                JsonObject o = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
                EmoteDef d = EmoteDef.parse("rubycon_emotes", id, o);
                assertTrue(evaluateAll(d) > 0, id);
                n++;
            }
        }
        assertEquals(30, n);
    }
}
