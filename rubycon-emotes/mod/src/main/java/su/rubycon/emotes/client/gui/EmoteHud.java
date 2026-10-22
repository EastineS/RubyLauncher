package su.rubycon.emotes.client.gui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraftforge.client.gui.overlay.ForgeGui;
import net.minecraftforge.client.gui.overlay.IGuiOverlay;
import su.rubycon.emotes.EmotesConfig;
import su.rubycon.emotes.client.ClientEmotes;

/** First-person indicator of the player's own active emote, placed beside the hotbar, away from the crosshair. */
public final class EmoteHud implements IGuiOverlay {
    @Override
    public void render(ForgeGui gui, GuiGraphics g, float pt, int w, int h) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.options.hideGui || !EmotesConfig.SHOW_INDICATOR.get() || !mc.options.getCameraType().isFirstPerson()) return;
        ClientEmotes.Playing p = ClientEmotes.own();
        if (p == null) return;
        long now = System.currentTimeMillis();
        float prog = p.progress(now);
        float appear = Math.min(1, (now - p.startMs()) / 200f);
        int cx = w / 2 + 91 + 22, cy = h - 12;
        int acc = Ui.accent(p.id());
        Ui.ring(g, cx, cy, 0, 11, 0, (float) Math.PI * 2, 0xC0101422, 0xC0101422);
        Ui.ring(g, cx, cy, 11, 12.5f, (float) (Math.PI * 2 * prog), (float) Math.PI * 2, Ui.withAlpha(acc, 0xFF), Ui.GOLD);
        int s = (int) (18 * appear);
        Ui.icon(g, p.id(), cx - s / 2, cy - s / 2, s, 1 - Math.max(0, prog - 0.85f) / 0.15f);
    }
}
