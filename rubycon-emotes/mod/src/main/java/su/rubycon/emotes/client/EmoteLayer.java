package su.rubycon.emotes.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexSorting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.PlayerModel;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.world.entity.EquipmentSlot;
import su.rubycon.emotes.EmotesConfig;

public final class EmoteLayer extends RenderLayer<AbstractClientPlayer, PlayerModel<AbstractClientPlayer>> {
    private static final EmoteAnimator.Opts OPTS = new EmoteAnimator.Opts();
    /** Set by the preview to force the helmet variant regardless of equipment. */
    public static Boolean previewHelmet;

    public EmoteLayer(RenderLayerParent<AbstractClientPlayer, PlayerModel<AbstractClientPlayer>> parent) {
        super(parent);
    }

    @Override
    public void render(PoseStack ps, MultiBufferSource buf, int light, AbstractClientPlayer player, float limbSwing, float limbAmount,
                       float partial, float age, float headYaw, float headPitch) {
        Minecraft mc = Minecraft.getInstance();
        boolean gui = RenderSystem.getVertexSorting() == VertexSorting.ORTHOGRAPHIC_Z;
        boolean self = player == mc.player;
        ClientEmotes.Playing playing = gui && self && ClientEmotes.previewOverride != null ? ClientEmotes.previewOverride : ClientEmotes.get(player.getId());
        if (playing == null) return;
        long now = System.currentTimeMillis();
        if (!gui) {
            // emotes must never reveal hidden players
            if (player.isInvisible() || player.isSpectator()) return;
            if (self ? !EmotesConfig.SHOW_OWN.get() || mc.options.getCameraType().isFirstPerson() : !EmotesConfig.SHOW_OTHERS.get()) return;
            double d = ClientEmotes.distance();
            if (mc.gameRenderer.getMainCamera().getPosition().distanceToSqr(player.position()) > d * d) return;
        }
        EmoteDef def = EmoteDefs.get(playing.id());
        if (def == null) return;
        float t = playing == ClientEmotes.previewOverride ? (playing.time(now) % def.duration) : playing.time(now);
        if (t > playing.durationMs() / 1000f + 0.05f) return;
        OPTS.scale = EmotesConfig.SIZE.get().factor;
        OPTS.reduced = EmotesConfig.REDUCED_MOTION.get();
        OPTS.helmet = gui && previewHelmet != null ? previewHelmet : !player.getItemBySlot(EquipmentSlot.HEAD).isEmpty();
        OPTS.budget = gui ? 1f : ClientEmotes.budget();
        if (!gui) ClientEmotes.countRendered();
        EmoteRenderer.render(def, t, OPTS, ps, buf, getParentModel().head);
    }
}
