package su.rubycon.emotes.client.gui;

import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import org.lwjgl.glfw.GLFW;
import su.rubycon.emotes.client.ClientEmotes;

import java.util.List;

/** Hold-to-open radial of the 8 favourites; releasing the key activates the hovered sector. */
public final class EmoteWheelScreen extends Screen {
    private static final float R_IN = 34, R_OUT = 100, R_CENTER = 26;
    private final KeyMapping holdKey;
    private List<String> favs;
    private int hovered = -1;
    private final long opened = System.currentTimeMillis();
    private Component status;

    public EmoteWheelScreen(KeyMapping holdKey) {
        super(Component.translatable("rubycon_emotes.wheel.title"));
        this.holdKey = holdKey;
    }

    @Override
    protected void init() { favs = ClientEmotes.favorites(); }

    private boolean keyHeld() {
        if (holdKey == null || holdKey.isUnbound()) return true;
        InputConstants.Key k = holdKey.getKey();
        long win = minecraft.getWindow().getWindow();
        if (k.getType() == InputConstants.Type.MOUSE) return GLFW.glfwGetMouseButton(win, k.getValue()) == GLFW.GLFW_PRESS;
        return InputConstants.isKeyDown(win, k.getValue());
    }

    @Override
    public void tick() {
        if (!keyHeld()) activate();
    }

    private void activate() {
        if (hovered >= 0 && hovered < favs.size()) {
            Component err = ClientEmotes.request(favs.get(hovered));
            if (err != null && minecraft.player != null) minecraft.player.displayClientMessage(err, true);
        }
        onClose();
    }

    private int sectorAt(double mx, double my) {
        double dx = mx - width / 2.0, dy = my - height / 2.0;
        double d = Math.hypot(dx, dy);
        if (d < R_CENTER + 4) return -1;
        double a = Math.atan2(dx, -dy);
        if (a < 0) a += Math.PI * 2;
        return (int) Math.floor((a + Math.PI / 8) / (Math.PI / 4)) % 8;
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float pt) {
        float open = Mth.clamp((System.currentTimeMillis() - opened) / 160f, 0, 1);
        float ease = 1 - (1 - open) * (1 - open) * (1 - open);
        g.fillGradient(0, 0, width, height, (int) (0x60 * ease) << 24, (int) (0x90 * ease) << 24);
        hovered = sectorAt(mx, my);
        float cx = width / 2f, cy = height / 2f;
        g.pose().pushPose();
        g.pose().translate(cx, cy, 0);
        g.pose().scale(0.85f + 0.15f * ease, 0.85f + 0.15f * ease, 1);
        g.pose().translate(-cx, -cy, 0);
        float step = (float) (Math.PI / 4), gap = 0.025f;
        for (int i = 0; i < 8; i++) {
            float a0 = i * step - step / 2 + gap, a1 = i * step + step / 2 - gap;
            boolean hov = i == hovered;
            String id = i < favs.size() ? favs.get(i) : null;
            int acc = id != null ? Ui.accent(id) : 0x404660;
            Ui.ring(g, cx, cy, R_IN, R_OUT + (hov ? 6 : 0), a0, a1, hov ? 0xE0283052 : 0xD0141828, hov ? Ui.withAlpha(acc, 0xE0) : 0xD01C2136);
            Ui.ring(g, cx, cy, R_OUT + (hov ? 6 : 0), R_OUT + (hov ? 7.5f : 1), a0, a1, hov ? Ui.GOLD : Ui.GOLD_DIM, hov ? Ui.GOLD : Ui.GOLD_DIM);
            float am = i * step;
            float ir = (R_IN + R_OUT) / 2f + (hov ? 3 : 0);
            int ix = (int) (cx + Mth.sin(am) * ir), iy = (int) (cy - Mth.cos(am) * ir);
            if (id != null) {
                int s = hov ? 36 : 30;
                Ui.icon(g, id, ix - s / 2, iy - s / 2, s, ClientEmotes.allowed(id) ? 1 : 0.35f);
            } else g.drawCenteredString(font, "+", ix, iy - 4, Ui.MUTED);
            Ui.diamond(g, (int) (cx + Mth.sin(am) * (R_OUT + 12)), (int) (cy - Mth.cos(am) * (R_OUT + 12)), hov ? 3 : 1, hov ? Ui.GOLD : Ui.GOLD_DIM);
        }
        // centre: cancel
        boolean centre = hovered < 0;
        Ui.ring(g, cx, cy, 0, R_CENTER, 0, (float) (Math.PI * 2), centre ? 0xE02A3150 : 0xD0101422, centre ? 0xE02A3150 : 0xD0101422);
        Ui.ring(g, cx, cy, R_CENTER, R_CENTER + 1.2f, 0, (float) (Math.PI * 2), Ui.GOLD_DIM, Ui.GOLD_DIM);
        // spinning holo ring
        float spin = (System.currentTimeMillis() % 6000) / 6000f * (float) Math.PI * 2;
        for (int k = 0; k < 6; k++) {
            float a = spin + k * (float) Math.PI / 3;
            Ui.ring(g, cx, cy, R_OUT + 18, R_OUT + 19, a, a + 0.6f, Ui.GOLD_FAINT, Ui.GOLD_FAINT);
        }
        g.pose().popPose();
        Component label = hovered >= 0 && hovered < favs.size() ? Ui.name(favs.get(hovered)) : Component.translatable("rubycon_emotes.wheel.cancel");
        g.drawCenteredString(font, label, (int) cx, (int) cy - 4, centre ? Ui.MUTED : Ui.GOLD);
        g.drawCenteredString(font, Component.translatable("rubycon_emotes.wheel.hint"), (int) cx, (int) (cy + R_OUT + 28), Ui.MUTED);
        if (favs.isEmpty()) g.drawCenteredString(font, Component.translatable("rubycon_emotes.wheel.empty"), (int) cx, (int) (cy - R_OUT - 34), Ui.TEXT);
        super.render(g, mx, my, pt);
    }

    @Override
    public boolean mouseClicked(double mx, double my, int b) {
        hovered = sectorAt(mx, my);
        activate();
        return true;
    }

    @Override
    public boolean isPauseScreen() { return false; }
}
