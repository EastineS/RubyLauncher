package su.rubycon.emotes;

import com.google.gson.*;
import net.minecraftforge.fml.loading.FMLPaths;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Common list of emotes (ids, names, durations). Visuals live in client resource packs. */
public final class EmoteIndex {
    public record Info(String id, String name, int durationMs) {}
    private static List<Info> list = List.of();
    private static Map<String, Info> byId = Map.of();
    public static final String CONFIG_FILE = "rubycon_emotes-index.json";

    public static List<Info> all() { return list; }
    public static Info get(String id) { return byId.get(id); }

    public static void reload() {
        String json = null;
        Path cfg = FMLPaths.CONFIGDIR.get().resolve(CONFIG_FILE);
        try {
            if (Files.isRegularFile(cfg)) json = Files.readString(cfg, StandardCharsets.UTF_8);
        } catch (Exception e) { RubyconEmotes.LOG.warn("Cannot read {}: {}", cfg, e.toString()); }
        String builtin = readBuiltin();
        List<Info> parsed = json == null ? null : parse(json);
        if (parsed == null || parsed.isEmpty()) {
            parsed = parse(builtin);
            if (json == null && builtin != null) {
                try { Files.writeString(cfg, builtin, StandardCharsets.UTF_8); } catch (Exception ignored) {}
            }
        }
        set(parsed == null ? List.of() : parsed);
    }

    public static void set(List<Info> infos) {
        Map<String, Info> m = new LinkedHashMap<>();
        for (Info i : infos) m.putIfAbsent(i.id(), i);
        list = List.copyOf(m.values());
        byId = m;
    }

    private static String readBuiltin() {
        try (InputStream in = EmoteIndex.class.getResourceAsStream("/rubycon_emotes/index.json")) {
            return in == null ? null : new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) { return null; }
    }

    private static List<Info> parse(String json) {
        if (json == null) return null;
        try {
            JsonObject o = JsonParser.parseString(json).getAsJsonObject();
            List<Info> out = new ArrayList<>();
            for (JsonElement el : o.getAsJsonArray("emotes")) {
                JsonObject e = el.getAsJsonObject();
                String id = e.get("id").getAsString();
                if (!id.matches("[a-z0-9_]{1,32}")) continue;
                String name = e.has("name") ? e.get("name").getAsString() : id;
                float dur = e.has("duration") ? e.get("duration").getAsFloat() : 4f;
                out.add(new Info(id, name, Math.round(Math.max(0.5f, Math.min(dur, 30f)) * 1000)));
            }
            return out;
        } catch (Exception ex) {
            RubyconEmotes.LOG.error("Bad emote index json: {}", ex.toString());
            return null;
        }
    }
}
