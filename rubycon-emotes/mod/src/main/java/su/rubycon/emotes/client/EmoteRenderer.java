package su.rubycon.emotes.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.blaze3d.vertex.VertexSorting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.texture.AbstractTexture;
import net.minecraft.client.renderer.texture.MissingTextureAtlasSprite;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import su.rubycon.emotes.client.EmoteAnimator.Quad;

import java.util.HashMap;
import java.util.Map;

/**
 * Draws evaluated quads relative to a player head. Coordinates arrive in pixels with the head centre
 * as origin (y up, z out of the face) and are converted to model space (y down, face at -z).
 * Billboards are full-bright overlays; face/head marks take the entity's light so they sit on the skin.
 */
public final class EmoteRenderer {
    private static final float PX = 1 / 16f;
    private static final Map<ResourceLocation, Boolean> PRESENT = new HashMap<>();
    private static final EmoteAnimator.Out OUT = new EmoteAnimator.Out();
    private static final Matrix3f IDENTITY = new Matrix3f();

    public static void clearTextureCache() { PRESENT.clear(); }

    /** Missing or broken textures are skipped instead of drawing the purple checkerboard. */
    private static boolean present(ResourceLocation tex) {
        return PRESENT.computeIfAbsent(tex, t -> {
            AbstractTexture at = Minecraft.getInstance().getTextureManager().getTexture(t);
            return at != null && at != Minecraft.getInstance().getTextureManager().getTexture(MissingTextureAtlasSprite.getLocation());
        });
    }

    /**
     * @param ps    pose in player model space (as given to a RenderLayer)
     * @param light packed entity light, used by world-lit marks
     * @param lag   view-space offset (blocks) applied to billboards so they trail the head slightly; may be null
     */
    public static void render(EmoteDef def, float t, EmoteAnimator.Opts opts, PoseStack ps, MultiBufferSource buf, ModelPart head,
                              int light, Vector3f lag) {
        EmoteAnimator.evaluate(def, t, opts, OUT);
        if (OUT.size == 0) return;
        boolean gui = RenderSystem.getVertexSorting() == VertexSorting.ORTHOGRAPHIC_Z;

        ps.pushPose();
        head.translateAndRotate(ps);
        Matrix4f headM = new Matrix4f(ps.last().pose());
        Matrix3f headN = new Matrix3f(ps.last().normal());
        ps.popPose();
        ps.pushPose();
        ps.translate(head.x * PX, head.y * PX, head.z * PX);
        Matrix4f aboveM = new Matrix4f(ps.last().pose());
        ps.popPose();

        Vector3f tmp = new Vector3f();
        Matrix4f bill = new Matrix4f();
        Matrix4f local = new Matrix4f();
        float scale = headM.getScale(tmp).x;
        for (int i = 0; i < OUT.size; i++) {
            Quad q = OUT.get(i);
            if (q.a <= 0.004f || !present(q.tex)) continue;
            Matrix4f anchorM = q.anchor == EmoteDef.Anchor.ABOVE ? aboveM : headM;
            // px -> model space: head centre is 4px above the pivot, model y points down, face is -z
            float mx = q.px * PX, my = (-4 - q.py) * PX, mz = -q.pz * PX;
            Matrix4f m;
            boolean yUp;
            if (q.billboard) {
                anchorM.transformPosition(mx, my, mz, tmp);
                float bias = EmoteAnimator.BILLBOARD_BIAS * PX * scale;
                if (gui) tmp.z += bias;
                else {
                    if (lag != null && q.anchor == EmoteDef.Anchor.ABOVE) tmp.add(lag);
                    float len = tmp.length();
                    if (len > 1e-4f) tmp.mul(Math.max(0, 1 - bias / len));
                }
                // view space: identity rotation means the quad faces the camera
                bill.identity().translate(tmp).scale(scale, gui ? -scale : scale, scale);
                m = bill;
                yUp = true;
            } else {
                m = local.set(anchorM).translate(mx, my, mz);
                yUp = false;
            }
            VertexConsumer vc;
            int lightUv;
            if (q.lit && !q.billboard) {
                vc = buf.getBuffer(EmoteRenderTypes.lit(q.tex));
                lightUv = light;
            } else {
                vc = buf.getBuffer(q.blend == EmoteDef.Blend.ADD ? EmoteRenderTypes.additive(q.tex) : EmoteRenderTypes.translucent(q.tex));
                lightUv = LightTexture.FULL_BRIGHT;
            }
            emitQuad(vc, m, q, yUp, lightUv, q.billboard ? IDENTITY : headN, q.billboard ? 1 : -1);
        }
    }

    private static void emitQuad(VertexConsumer vc, Matrix4f m, Quad q, boolean yUp, int light, Matrix3f normal, float nz) {
        double r = Math.toRadians(q.rot);
        float cr = (float) Math.cos(r), sr = (float) Math.sin(r);
        float ys = yUp ? 1 : -1;
        float u0 = q.flip ? 1 : 0, u1 = q.flip ? 0 : 1;
        // corners: TL, BL, BR, TR (local px, y up)
        float[][] c = {{-0.5f, 0.5f}, {-0.5f, -0.5f}, {0.5f, -0.5f}, {0.5f, 0.5f}};
        float[][] uv = {{u0, 0}, {u0, 1}, {u1, 1}, {u1, 0}};
        for (int k = 0; k < 4; k++) {
            float lx = (c[k][0] - q.pvx) * q.w, ly = (c[k][1] - q.pvy) * q.h;
            float x = (lx * cr - ly * sr + q.ox) * PX;
            float y = (lx * sr + ly * cr + q.oy) * PX * ys;
            vc.vertex(m, x, y, 0).color(q.r, q.g, q.b, Math.min(1, q.a)).uv(uv[k][0], uv[k][1])
                    .overlayCoords(OverlayTexture.NO_OVERLAY).uv2(light).normal(normal, 0, 0, nz).endVertex();
        }
    }

    private EmoteRenderer() {}
}
