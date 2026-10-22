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
    /** Smoothed head positions: emblems trail the head a little instead of moving rigidly with it. */
    private static final java.util.Map<Integer, double[]> FOLLOW = new java.util.HashMap<>();
    private static final float MAX_LAG = 0.35f;
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
        EmoteRenderer.render(def, t, OPTS, ps, buf, getParentModel().head, light, gui ? null : lag(player, partial, now));
    }

    private static org.joml.Vector3f lag(AbstractClientPlayer player, float partial, long now) {
        net.minecraft.world.phys.Vec3 p = player.getPosition(partial);
        double[] s = FOLLOW.get(player.getId());
        if (s == null || now - (long) s[3] > 1000 || p.distanceToSqr(s[0], s[1], s[2]) > 9) {
            s = new double[]{p.x, p.y, p.z, now};
            FOLLOW.put(player.getId(), s);
        }
        double dt = Math.min(0.1, (now - (long) s[3]) / 1000.0);
        double k = 1 - Math.exp(-dt * 9);
        s[0] += (p.x - s[0]) * k; s[1] += (p.y - s[1]) * k; s[2] += (p.z - s[2]) * k;
        s[3] = now;
        org.joml.Vector3f off = new org.joml.Vector3f((float) (s[0] - p.x), (float) (s[1] - p.y), (float) (s[2] - p.z));
        if (off.length() > MAX_LAG) off.normalize(MAX_LAG);
        if (FOLLOW.size() > 256) FOLLOW.entrySet().removeIf(en -> now - (long) en.getValue()[3] > 5000);
        // world -> view space, same rotation the level renderer applies before entities
        var cam = Minecraft.getInstance().gameRenderer.getMainCamera();
        new org.joml.Quaternionf().rotateX((float) Math.toRadians(cam.getXRot())).rotateY((float) Math.toRadians(cam.getYRot() + 180)).transform(off);
        return off;
    }
}
