package su.rubycon.emotes.client.gui;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.*;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.renderer.GameRenderer;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import org.joml.Matrix4f;
import su.rubycon.emotes.client.EmoteDef;
import su.rubycon.emotes.client.EmoteDefs;

/** HSR-flavoured UI kit: night-glass panels, gold hairlines, diamond ornaments. */
public final class Ui {
    public static final int GOLD = 0xFFE3C27A, GOLD_DIM = 0x88E3C27A, GOLD_FAINT = 0x33E3C27A;
    public static final int TEXT = 0xFFF2EEE6, MUTED = 0xFF9AA0B8, DANGER = 0xFFFF7A7A;
    public static final int GLASS_TOP = 0xEE161A2C, GLASS_BOTTOM = 0xEE0B0D18, TILE = 0xAA1C2136, TILE_HOVER = 0xCC283052;

    public static void panel(GuiGraphics g, int x, int y, int w, int h) {
        g.fillGradient(x, y, x + w, y + h, GLASS_TOP, GLASS_BOTTOM);
        // faint inner starfield
        long seed = 1234567L;
        for (int i = 0; i < w * h / 900; i++) {
            seed = seed * 6364136223846793005L + 1442695040888963407L;
            int sx = x + 2 + (int) ((seed >>> 33) % Math.max(1, w - 4));
            int sy = y + 2 + (int) ((seed >>> 17) % Math.max(1, h - 4));
            g.fill(sx, sy, sx + 1, sy + 1, 0x30FFFFFF);
        }
        frame(g, x, y, w, h, GOLD_DIM);
        g.fill(x + 8, y + 1, x + w - 8, y + 2, 0x22FFFFFF);
        diamond(g, x, y, 3, GOLD);
        diamond(g, x + w - 1, y, 3, GOLD);
        diamond(g, x, y + h - 1, 3, GOLD);
        diamond(g, x + w - 1, y + h - 1, 3, GOLD);
    }

    public static void frame(GuiGraphics g, int x, int y, int w, int h, int c) {
        g.fill(x, y, x + w, y + 1, c);
        g.fill(x, y + h - 1, x + w, y + h, c);
        g.fill(x, y + 1, x + 1, y + h - 1, c);
        g.fill(x + w - 1, y + 1, x + w, y + h - 1, c);
    }

    public static void diamond(GuiGraphics g, int cx, int cy, int r, int c) {
        for (int i = -r; i <= r; i++) {
            int span = r - Math.abs(i);
            g.fill(cx - span, cy + i, cx + span + 1, cy + i + 1, c);
        }
    }

    /** Title with a gold rule and diamonds, centred over [x, x+w]. */
    public static void title(GuiGraphics g, Font f, Component text, int x, int y, int w) {
        int tw = f.width(text);
        int cx = x + w / 2;
        g.drawString(f, text, cx - tw / 2, y, TEXT, false);
        int ly = y + 4;
        g.fill(x + 10, ly, cx - tw / 2 - 8, ly + 1, GOLD_FAINT);
        g.fill(cx + tw / 2 + 8, ly, x + w - 10, ly + 1, GOLD_FAINT);
        diamond(g, cx - tw / 2 - 5, ly, 2, GOLD);
        diamond(g, cx + tw / 2 + 4, ly, 2, GOLD);
    }

    public static void icon(GuiGraphics g, String id, int x, int y, int size, float alpha) {
        EmoteDef d = EmoteDefs.get(id);
        if (d == null) return;
        RenderSystem.enableBlend();
        g.setColor(1, 1, 1, alpha);
        g.blit(d.icon, x, y, size, size, 0, 0, 64, 64, 64, 64);
        g.setColor(1, 1, 1, 1);
    }

    public static int accent(String id) {
        EmoteDef d = EmoteDefs.get(id);
        return d == null ? GOLD : d.color;
    }

    public static int withAlpha(int rgb, int a) { return (a << 24) | (rgb & 0xFFFFFF); }

    public static Component name(String id) { return Component.translatable("emote.rubycon_emotes." + id); }

    /** Tile with accent glow when selected / hovered. */
    public static void tile(GuiGraphics g, int x, int y, int w, int h, String id, boolean hover, boolean selected) {
        int acc = accent(id);
        g.fill(x, y, x + w, y + h, hover || selected ? TILE_HOVER : TILE);
        if (selected) {
            g.fillGradient(x, y, x + w, y + h, withAlpha(acc, 0x10), withAlpha(acc, 0x55));
            frame(g, x, y, w, h, GOLD);
            diamond(g, x + w / 2, y, 2, GOLD);
        } else frame(g, x, y, w, h, hover ? GOLD_DIM : 0x22FFFFFF);
        g.fill(x + 1, y + h - 2, x + w - 1, y + h - 1, withAlpha(acc, hover || selected ? 0xFF : 0x66));
    }

    /** Filled annulus sector, angles in radians clockwise from 12 o'clock. */
    public static void ring(GuiGraphics g, float cx, float cy, float r0, float r1, float a0, float a1, int c0, int c1) {
        Matrix4f m = g.pose().last().pose();
        RenderSystem.enableBlend();
        RenderSystem.defaultBlendFunc();
        RenderSystem.setShader(GameRenderer::getPositionColorShader);
        BufferBuilder bb = Tesselator.getInstance().getBuilder();
        bb.begin(VertexFormat.Mode.TRIANGLE_STRIP, DefaultVertexFormat.POSITION_COLOR);
        int n = Math.max(2, (int) (Math.abs(a1 - a0) * 24));
        for (int i = 0; i <= n; i++) {
            float a = Mth.lerp(i / (float) n, a0, a1);
            float sx = Mth.sin(a), sy = -Mth.cos(a);
            bb.vertex(m, cx + sx * r1, cy + sy * r1, 0).color(c1 >> 16 & 255, c1 >> 8 & 255, c1 & 255, c1 >>> 24).endVertex();
            bb.vertex(m, cx + sx * r0, cy + sy * r0, 0).color(c0 >> 16 & 255, c0 >> 8 & 255, c0 & 255, c0 >>> 24).endVertex();
        }
        BufferUploader.drawWithShader(bb.end());
    }

    /** Gold-trimmed button; primary buttons are filled gold with dark text. */
    public static class HButton extends Button {
        private final boolean primary;

        public HButton(int x, int y, int w, int h, Component text, OnPress press, boolean primary) {
            super(x, y, w, h, text, press, DEFAULT_NARRATION);
            this.primary = primary;
        }

        @Override
        protected void renderWidget(GuiGraphics g, int mx, int my, float pt) {
            int x = getX(), y = getY(), w = width, h = height;
            boolean hov = isHoveredOrFocused() && active;
            if (primary) {
                g.fillGradient(x, y, x + w, y + h, active ? (hov ? 0xFFFFE3A6 : 0xFFF0D08E) : 0xFF6B6250, active ? (hov ? 0xFFE0B860 : 0xFFC99A4A) : 0xFF4A4436);
                frame(g, x, y, w, h, active ? 0xFFFFF2CC : 0xFF5A5446);
            } else {
                g.fill(x, y, x + w, y + h, hov ? 0xCC2A3150 : 0xAA171B2C);
                frame(g, x, y, w, h, hov ? GOLD : GOLD_FAINT);
                if (hov) { diamond(g, x, y + h / 2, 2, GOLD); diamond(g, x + w - 1, y + h / 2, 2, GOLD); }
            }
            Font f = Minecraft.getInstance().font;
            int color = primary ? (active ? 0xFF2A1C08 : 0xFF2A2A2A) : (active ? TEXT : MUTED);
            Component msg = getMessage();
            g.drawString(f, msg, x + (w - f.width(msg)) / 2, y + (h - 8) / 2, color, false);
        }
    }

    private Ui() {}
}
