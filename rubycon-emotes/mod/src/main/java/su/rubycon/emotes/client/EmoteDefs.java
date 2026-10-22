package su.rubycon.emotes.client;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.SimplePreparableReloadListener;
import net.minecraft.util.profiling.ProfilerFiller;
import su.rubycon.emotes.RubyconEmotes;

import java.io.Reader;
import java.util.HashMap;
import java.util.Map;

/** Loads every assets/&lt;ns&gt;/emotes/*.json, so resource packs can add or restyle emotes without code. */
public final class EmoteDefs extends SimplePreparableReloadListener<Map<String, EmoteDef>> {
    private static Map<String, EmoteDef> defs = Map.of();

    public static EmoteDef get(String id) { return defs.get(id); }

    @Override
    protected Map<String, EmoteDef> prepare(ResourceManager rm, ProfilerFiller profiler) {
        Map<String, EmoteDef> out = new HashMap<>();
        for (Map.Entry<ResourceLocation, Resource> e : rm.listResources("emotes", p -> p.getPath().endsWith(".json")).entrySet()) {
            ResourceLocation rl = e.getKey();
            String id = rl.getPath().substring("emotes/".length(), rl.getPath().length() - ".json".length());
            try (Reader r = e.getValue().openAsReader()) {
                JsonObject o = JsonParser.parseReader(r).getAsJsonObject();
                out.put(id, EmoteDef.parse(rl.getNamespace(), id, o));
            } catch (Exception ex) {
                RubyconEmotes.LOG.error("Bad emote definition {}: {}", rl, ex.toString());
            }
        }
        return out;
    }

    @Override
    protected void apply(Map<String, EmoteDef> map, ResourceManager rm, ProfilerFiller profiler) {
        defs = Map.copyOf(map);
        EmoteRenderer.clearTextureCache();
        RubyconEmotes.LOG.info("Loaded {} emote definitions", defs.size());
    }
}
