package su.rubycon.emotes.client;

import com.mojang.blaze3d.vertex.DefaultVertexFormat;
import com.mojang.blaze3d.vertex.VertexFormat;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.resources.ResourceLocation;

import java.util.HashMap;
import java.util.Map;

/**
 * Unlit, depth-tested, non-depth-writing sprite types. The eyes shader is texture * vertex colour,
 * so effects stay bright at night and fog still fades them with distance.
 */
public final class EmoteRenderTypes extends RenderType {
    private static final Map<ResourceLocation, RenderType> ADD = new HashMap<>();
    private static final Map<ResourceLocation, RenderType> NORMAL = new HashMap<>();
    private static final Map<ResourceLocation, RenderType> LIT = new HashMap<>();

    /** Marks painted on the head (blush, tears): lit like skin, nudged toward the camera to avoid z-fighting. */
    public static RenderType lit(ResourceLocation tex) {
        return LIT.computeIfAbsent(tex, t -> create("rubycon_emote_lit", DefaultVertexFormat.NEW_ENTITY, VertexFormat.Mode.QUADS, 256,
                true, true, CompositeState.builder()
                        .setShaderState(RENDERTYPE_ENTITY_TRANSLUCENT_SHADER)
                        .setTextureState(new TextureStateShard(t, false, false))
                        .setTransparencyState(TRANSLUCENT_TRANSPARENCY)
                        .setCullState(NO_CULL)
                        .setLightmapState(LIGHTMAP)
                        .setOverlayState(OVERLAY)
                        .setLayeringState(VIEW_OFFSET_Z_LAYERING)
                        .setWriteMaskState(COLOR_WRITE)
                        .createCompositeState(false)));
    }

    public static RenderType additive(ResourceLocation tex) {
        return ADD.computeIfAbsent(tex, t -> create("rubycon_emote_add", DefaultVertexFormat.NEW_ENTITY, VertexFormat.Mode.QUADS, 256,
                false, false, CompositeState.builder()
                        .setShaderState(RENDERTYPE_EYES_SHADER)
                        .setTextureState(new TextureStateShard(t, false, false))
                        .setTransparencyState(LIGHTNING_TRANSPARENCY)
                        .setCullState(NO_CULL)
                        .setWriteMaskState(COLOR_WRITE)
                        .createCompositeState(false)));
    }

    public static RenderType translucent(ResourceLocation tex) {
        return NORMAL.computeIfAbsent(tex, t -> create("rubycon_emote", DefaultVertexFormat.NEW_ENTITY, VertexFormat.Mode.QUADS, 256,
                false, false, CompositeState.builder()
                        .setShaderState(RENDERTYPE_EYES_SHADER)
                        .setTextureState(new TextureStateShard(t, false, false))
                        .setTransparencyState(TRANSLUCENT_TRANSPARENCY)
                        .setCullState(NO_CULL)
                        .setWriteMaskState(COLOR_WRITE)
                        .createCompositeState(false)));
    }

    private EmoteRenderTypes(String n, VertexFormat f, VertexFormat.Mode m, int s, boolean a, boolean b, Runnable c, Runnable d) {
        super(n, f, m, s, a, b, c, d);
    }
}
