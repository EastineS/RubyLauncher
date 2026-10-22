package su.rubycon.emotes.client.gui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.ChatScreen;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.util.ObfuscationReflectionHelper;
import org.lwjgl.glfw.GLFW;
import su.rubycon.emotes.EmotesConfig;
import su.rubycon.emotes.client.ClientEmotes;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

/**
 * Emote button at the right end of the chat input of any ChatScreen (vanilla, Rubycon UI chat,
 * roleplay chat) and the quick picker popup it opens.
 */
public final class ChatEmoteButton {
    private static final int BTN = 12, CELL = 26, COLS = 5, PREV_W = 74;
    private static Field inputField;
    private static final Map<EditBox, Integer> SHRUNK = new WeakHashMap<>();
    private static boolean open;
    private static boolean favTab;
    private static final EmotePreview PREVIEW = new EmotePreview();
    private static Component status;
    private static long statusUntil;
    private static long openedAt;

    private static EditBox input(Screen s) {
        if (!(s instanceof ChatScreen)) return null;
        try {
            if (inputField == null) inputField = ObfuscationReflectionHelper.findField(ChatScreen.class, "f_95573_");
            return (EditBox) inputField.get(s);
        } catch (Exception e) {
            return null;
        }
    }

    /** Keeps 16px free at the end of the input; re-applies if the chat screen re-laid itself out. */
    private static int[] button(EditBox in) {
        Integer w = SHRUNK.get(in);
        if (w == null || in.getWidth() != w) {
            int nw = Math.max(40, in.getWidth() - (BTN + 4));
            in.setWidth(nw);
            SHRUNK.put(in, nw);
        }
        int x = in.getX() + in.getWidth() + 2;
        int y = in.getY() + (in.getHeight() - BTN) / 2 - 1;
        return new int[]{x, y, BTN, BTN};
    }

    private static List<String> list() { return favTab ? ClientEmotes.favorites() : ClientEmotes.ids(); }

    private static int[] popup(int[] b, Screen s) {
        int rows = Math.max(2, (list().size() + COLS - 1) / COLS);
        int w = PREV_W + 10 + COLS * CELL + 8, h = 24 + rows * CELL + 22;
        int x = Math.max(2, Math.min(s.width - w - 2, b[0] + b[2] - w));
        int y = Math.max(2, b[1] - h - 6);
        return new int[]{x, y, w, h};
    }

    private static boolean in(double mx, double my, int[] r) { return mx >= r[0] && mx < r[0] + r[2] && my >= r[1] && my < r[1] + r[3]; }

    @SubscribeEvent
    public static void onRender(ScreenEvent.Render.Post e) {
        if (!EmotesConfig.CHAT_BUTTON.get()) { open = false; return; }
        EditBox in = input(e.getScreen());
        if (in == null || !in.visible) return;
        GuiGraphics g = e.getGuiGraphics();
        int mx = e.getMouseX(), my = e.getMouseY();
        int[] b = button(in);
        g.pose().pushPose();
        g.pose().translate(0, 0, 300);
        boolean hov = in(mx, my, b);
        g.fill(b[0], b[1], b[0] + b[2], b[1] + b[3], hov || open ? 0xE0283052 : 0xC0141828);
        Ui.frame(g, b[0], b[1], b[2], b[3], hov || open ? Ui.GOLD : Ui.GOLD_DIM);
        String icon = ClientEmotes.own() != null ? ClientEmotes.own().id() : "laugh";
        Ui.icon(g, icon, b[0] + 1, b[1] + 1, 10, hov || open ? 1 : 0.85f);
        if (open) drawPopup(g, e.getScreen(), b, mx, my);
        else if (hov) g.renderTooltip(Minecraft.getInstance().font, Component.translatable("rubycon_emotes.chat.tooltip"), mx, my);
        g.pose().popPose();
    }

    private static int cellAt(int[] p, double mx, double my) {
        List<String> l = list();
        int gx = p[0] + PREV_W + 10, gy = p[1] + 22;
        for (int i = 0; i < l.size(); i++) {
            int x = gx + (i % COLS) * CELL, y = gy + (i / COLS) * CELL;
            if (mx >= x && mx < x + CELL - 2 && my >= y && my < y + CELL - 2) return i;
        }
        return -1;
    }

    private static int[] tabRect(int[] p, int i) { return new int[]{p[0] + PREV_W + 10 + i * 64, p[1] + 5, 62, 13}; }
    private static int[] footRect(int[] p, int i) { return new int[]{p[0] + PREV_W + 10 + i * 66, p[1] + p[3] - 18, 64, 13}; }

    private static void drawPopup(GuiGraphics g, Screen s, int[] b, int mx, int my) {
        Font f = Minecraft.getInstance().font;
        int[] p = popup(b, s);
        float open01 = Math.min(1, (System.currentTimeMillis() - openedAt) / 140f);
        g.pose().pushPose();
        g.pose().translate(0, (1 - open01) * 6, 0);
        Ui.panel(g, p[0], p[1], p[2], p[3]);
        List<String> l = list();
        int hover = cellAt(p, mx, my);
        String shown = hover >= 0 ? l.get(hover) : (PREVIEW.id() != null ? PREVIEW.id() : (l.isEmpty() ? null : l.get(0)));
        if (shown != null) PREVIEW.select(shown);
        int pvx = p[0] + 6, pvy = p[1] + 6, pvh = p[3] - 12;
        if (shown != null) {
            PREVIEW.render(g, pvx, pvy, PREV_W, pvh);
            Component n = Ui.name(shown);
            g.drawString(f, f.plainSubstrByWidth(n.getString(), PREV_W - 6), pvx + 3, pvy + 3, Ui.TEXT, true);
        }
        for (int t = 0; t < 2; t++) {
            int[] r = tabRect(p, t);
            boolean act = (t == 1) == favTab, h = in(mx, my, r);
            g.fill(r[0], r[1], r[0] + r[2], r[1] + r[3], act ? 0xCC2A3150 : (h ? 0x99202640 : 0x66141828));
            if (act) g.fill(r[0], r[1] + r[3] - 1, r[0] + r[2], r[1] + r[3], Ui.GOLD);
            Component tc = Component.translatable(t == 0 ? "rubycon_emotes.chat.all" : "rubycon_emotes.chat.favorites");
            g.drawString(f, tc, r[0] + (r[2] - f.width(tc)) / 2, r[1] + 3, act ? Ui.GOLD : Ui.MUTED, false);
        }
        int gx = p[0] + PREV_W + 10, gy = p[1] + 22;
        for (int i = 0; i < l.size(); i++) {
            String id = l.get(i);
            int x = gx + (i % COLS) * CELL, y = gy + (i / COLS) * CELL;
            Ui.tile(g, x, y, CELL - 2, CELL - 2, id, i == hover, id.equals(PREVIEW.id()) && hover < 0);
            Ui.icon(g, id, x + 1, y + 1 - (i == hover ? 1 : 0), CELL - 4, ClientEmotes.allowed(id) ? 1 : 0.35f);
            if (!favTab && ClientEmotes.isFavorite(id)) Ui.diamond(g, x + CELL - 6, y + 3, 2, Ui.GOLD);
        }
        if (l.isEmpty()) g.drawString(f, Component.translatable("rubycon_emotes.wheel.empty"), gx, gy + 6, Ui.MUTED, false);
        for (int i = 0; i < 2; i++) {
            int[] r = footRect(p, i);
            boolean h = in(mx, my, r);
            boolean active = i == 1 || ClientEmotes.own() != null;
            g.fill(r[0], r[1], r[0] + r[2], r[1] + r[3], h && active ? 0xCC2A3150 : 0x88141828);
            Ui.frame(g, r[0], r[1], r[2], r[3], h && active ? Ui.GOLD : Ui.GOLD_FAINT);
            Component c = Component.translatable(i == 0 ? "rubycon_emotes.menu.cancel" : "rubycon_emotes.chat.menu");
            g.drawString(f, c, r[0] + (r[2] - f.width(c)) / 2, r[1] + 3, active ? Ui.TEXT : Ui.MUTED, false);
        }
        Component foot = null;
        if (status != null && System.currentTimeMillis() < statusUntil) foot = status;
        else if (ClientEmotes.cooldownLeft() > 0)
            foot = Component.translatable("rubycon_emotes.msg.cooldown_left", String.format(java.util.Locale.ROOT, "%.1f", ClientEmotes.cooldownLeft()));
        if (foot != null) g.drawString(f, foot, gx + 134, p[1] + p[3] - 15, Ui.DANGER, false);
        g.pose().popPose();
        if (hover >= 0) g.renderTooltip(f, List.of(Ui.name(l.get(hover)), Component.translatable("rubycon_emotes.chat.click_hint")),
                java.util.Optional.empty(), mx, my);
    }

    @SubscribeEvent
    public static void onClick(ScreenEvent.MouseButtonPressed.Pre e) {
        if (!EmotesConfig.CHAT_BUTTON.get()) return;
        EditBox in = input(e.getScreen());
        if (in == null) return;
        double mx = e.getMouseX(), my = e.getMouseY();
        int[] b = button(in);
        if (in(mx, my, b)) {
            if (e.getButton() == 1) Minecraft.getInstance().setScreen(new EmoteMenuScreen(e.getScreen()));
            else { open = !open; openedAt = System.currentTimeMillis(); }
            e.setCanceled(true);
            return;
        }
        if (!open) return;
        int[] p = popup(b, e.getScreen());
        if (!in(mx, my, p)) { open = false; return; }
        e.setCanceled(true);
        for (int t = 0; t < 2; t++) if (in(mx, my, tabRect(p, t))) { favTab = t == 1; return; }
        if (in(mx, my, footRect(p, 0))) { ClientEmotes.cancel(); return; }
        if (in(mx, my, footRect(p, 1))) { open = false; Minecraft.getInstance().setScreen(new EmoteMenuScreen(e.getScreen())); return; }
        int c = cellAt(p, mx, my);
        if (c < 0) { PREVIEW.mouseClicked(mx, my, p[0] + 6, p[1] + 6, PREV_W, p[3] - 12); return; }
        String id = list().get(c);
        if (e.getButton() == 1) { ClientEmotes.toggleFavorite(id); return; }
        Component err = ClientEmotes.request(id);
        if (err == null) open = false;
        else { status = err; statusUntil = System.currentTimeMillis() + 2000; }
    }

    @SubscribeEvent
    public static void onDrag(ScreenEvent.MouseDragged.Pre e) {
        if (open && input(e.getScreen()) != null) PREVIEW.mouseDragged(e.getMouseX(), e.getMouseY());
    }

    @SubscribeEvent
    public static void onRelease(ScreenEvent.MouseButtonReleased.Pre e) { PREVIEW.mouseReleased(); }

    @SubscribeEvent
    public static void onScroll(ScreenEvent.MouseScrolled.Pre e) {
        EditBox in = input(e.getScreen());
        if (open && in != null && in(e.getMouseX(), e.getMouseY(), popup(button(in), e.getScreen()))) e.setCanceled(true);
    }

    @SubscribeEvent
    public static void onKey(ScreenEvent.KeyPressed.Pre e) {
        if (open && e.getKeyCode() == GLFW.GLFW_KEY_ESCAPE && input(e.getScreen()) != null) {
            open = false;
            e.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void onClose(ScreenEvent.Closing e) {
        if (e.getScreen() instanceof ChatScreen) open = false;
    }

    private ChatEmoteButton() {}
}
