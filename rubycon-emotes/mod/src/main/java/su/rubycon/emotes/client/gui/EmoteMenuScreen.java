package su.rubycon.emotes.client.gui;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import su.rubycon.emotes.client.ClientEmotes;

import java.util.List;

/** Full emote menu: grid of all emotes, live preview, favourites and the "use" action. */
public final class EmoteMenuScreen extends Screen {
    private static final int COLS = 5, TILE_W = 46, TILE_H = 48, GAP = 4;
    private static String lastSelected;
    private final Screen parent;
    private final EmotePreview preview = new EmotePreview();
    private List<String> ids;
    private int px, py, pw, ph, gridX, gridY, prevX, prevY, prevW, prevH;
    private Ui.HButton useBtn, favBtn, helmetBtn, leftBtn, rightBtn, cancelBtn;
    private Component status;
    private long statusUntil;

    public EmoteMenuScreen(Screen parent) {
        super(Component.translatable("rubycon_emotes.menu.title"));
        this.parent = parent;
    }

    @Override
    protected void init() {
        ids = ClientEmotes.ids();
        int rows = (ids.size() + COLS - 1) / COLS;
        int gridW = COLS * TILE_W + (COLS - 1) * GAP, gridH = Math.max(4, rows) * (TILE_H + GAP) - GAP;
        prevW = 150;
        pw = 16 + gridW + 12 + prevW + 16;
        ph = Math.max(28 + gridH + 14, 28 + 150 + 4 * 22 + 10);
        px = (width - pw) / 2;
        py = Math.max(4, (height - ph) / 2);
        gridX = px + 16;
        gridY = py + 28;
        prevX = gridX + gridW + 12;
        prevY = py + 28;
        prevH = 150;
        String sel = lastSelected != null && ids.contains(lastSelected) ? lastSelected : (ids.isEmpty() ? null : ids.get(0));
        if (sel != null) preview.select(sel);

        int bx = prevX, by = prevY + prevH + 6;
        useBtn = addRenderableWidget(new Ui.HButton(bx, by, prevW, 20, Component.translatable("rubycon_emotes.menu.use"), b -> use(), true));
        favBtn = addRenderableWidget(new Ui.HButton(bx, by + 24, prevW - 44, 18, Component.empty(), b -> toggleFav(), false));
        leftBtn = addRenderableWidget(new Ui.HButton(bx + prevW - 42, by + 24, 20, 18, Component.literal("◀"), b -> move(-1), false));
        rightBtn = addRenderableWidget(new Ui.HButton(bx + prevW - 20, by + 24, 20, 18, Component.literal("▶"), b -> move(1), false));
        helmetBtn = addRenderableWidget(new Ui.HButton(bx, by + 46, prevW, 18, Component.empty(), b -> preview.helmet = !preview.helmet, false));
        cancelBtn = addRenderableWidget(new Ui.HButton(bx, by + 68, prevW / 2 - 2, 18, Component.translatable("rubycon_emotes.menu.cancel"), b -> {
            ClientEmotes.cancel();
            flash(Component.translatable("rubycon_emotes.msg.cancelled"));
        }, false));
        addRenderableWidget(new Ui.HButton(bx + prevW / 2 + 2, by + 68, prevW / 2 - 2, 18, Component.translatable("rubycon_emotes.menu.settings"),
                b -> minecraft.setScreen(new EmoteSettingsScreen(this)), false));
        refreshButtons();
    }

    private void refreshButtons() {
        String id = preview.id();
        boolean fav = id != null && ClientEmotes.isFavorite(id);
        favBtn.setMessage(Component.translatable(fav ? "rubycon_emotes.menu.unfavorite" : "rubycon_emotes.menu.favorite"));
        favBtn.active = id != null && (fav || ClientEmotes.favorites().size() < 8);
        leftBtn.active = rightBtn.active = fav;
        helmetBtn.setMessage(Component.translatable(preview.helmet ? "rubycon_emotes.menu.helmet_on" : "rubycon_emotes.menu.helmet_off"));
        useBtn.active = id != null && ClientEmotes.allowed(id) && ClientEmotes.cooldownLeft() <= 0;
        cancelBtn.active = ClientEmotes.own() != null;
    }

    private void use() {
        String id = preview.id();
        if (id == null) return;
        Component err = ClientEmotes.request(id);
        if (err == null) onClose();
        else flash(err);
    }

    private void toggleFav() {
        String id = preview.id();
        if (id != null) ClientEmotes.toggleFavorite(id);
        refreshButtons();
    }

    private void move(int d) {
        if (preview.id() != null) ClientEmotes.moveFavorite(preview.id(), d);
    }

    private void flash(Component c) { status = c; statusUntil = System.currentTimeMillis() + 2500; }

    @Override
    public void tick() { refreshButtons(); }

    private int tileAt(double mx, double my) {
        for (int i = 0; i < ids.size(); i++) {
            int tx = gridX + (i % COLS) * (TILE_W + GAP), ty = gridY + (i / COLS) * (TILE_H + GAP);
            if (mx >= tx && mx < tx + TILE_W && my >= ty && my < ty + TILE_H) return i;
        }
        return -1;
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float pt) {
        renderBackground(g);
        Ui.panel(g, px, py, pw, ph);
        Ui.title(g, font, title, px, py + 9, pw);
        int hover = tileAt(mx, my);
        List<String> favs = ClientEmotes.favorites();
        for (int i = 0; i < ids.size(); i++) {
            String id = ids.get(i);
            int tx = gridX + (i % COLS) * (TILE_W + GAP), ty = gridY + (i / COLS) * (TILE_H + GAP);
            boolean sel = id.equals(preview.id());
            Ui.tile(g, tx, ty, TILE_W, TILE_H, id, hover == i, sel);
            boolean ok = ClientEmotes.allowed(id) || !ClientEmotes.serverReady();
            float bounce = hover == i ? (float) Math.sin(System.currentTimeMillis() / 120.0) : 0;
            Ui.icon(g, id, tx + (TILE_W - 32) / 2, ty + 3 - (int) bounce, 32, ok ? 1f : 0.35f);
            Component n = Ui.name(id);
            g.pose().pushPose();
            float s = 0.62f;
            g.pose().translate(tx + TILE_W / 2f, ty + TILE_H - 10, 0);
            g.pose().scale(s, s, 1);
            String str = font.plainSubstrByWidth(n.getString(), (int) ((TILE_W - 2) / s));
            g.drawString(font, str, -font.width(str) / 2, 0, sel ? Ui.GOLD : Ui.TEXT, false);
            g.pose().popPose();
            int fi = favs.indexOf(id);
            if (fi >= 0) {
                Ui.diamond(g, tx + TILE_W - 6, ty + 5, 3, Ui.GOLD);
                g.pose().pushPose();
                g.pose().translate(tx + TILE_W - 7.5f, ty + 3, 0);
                g.pose().scale(0.5f, 0.5f, 1);
                g.drawString(font, String.valueOf(fi + 1), 0, 0, 0xFF2A1C08, false);
                g.pose().popPose();
            }
        }
        preview.render(g, prevX, prevY, prevW, prevH);
        String sel = preview.id();
        if (sel != null) {
            g.drawString(font, Ui.name(sel), prevX + 6, prevY + 5, Ui.TEXT, true);
            g.fill(prevX + 6, prevY + 15, prevX + 6 + font.width(Ui.name(sel)), prevY + 16, Ui.withAlpha(Ui.accent(sel), 0xFF));
            String dur = String.format(java.util.Locale.ROOT, "%.1f", ClientEmotes.durationMs(sel) / 1000f);
            Component hint = Component.translatable("rubycon_emotes.menu.duration", dur);
            g.drawString(font, hint, prevX + prevW - font.width(hint) - 5, prevY + 5, Ui.MUTED, false);
        }
        g.drawString(font, Component.translatable("rubycon_emotes.menu.drag"), prevX + 6, prevY + prevH - 11, 0xAAFFFFFF, false);
        super.render(g, mx, my, pt);
        Component foot = null;
        int footColor = Ui.MUTED;
        if (status != null && System.currentTimeMillis() < statusUntil) { foot = status; footColor = Ui.DANGER; }
        else if (!ClientEmotes.serverReady()) { foot = Component.translatable("rubycon_emotes.msg.no_server"); footColor = Ui.DANGER; }
        else if (ClientEmotes.cooldownLeft() > 0)
            foot = Component.translatable("rubycon_emotes.msg.cooldown_left", String.format(java.util.Locale.ROOT, "%.1f", ClientEmotes.cooldownLeft()));
        else foot = Component.translatable("rubycon_emotes.menu.hint");
        g.drawString(font, foot, gridX, py + ph - 12, footColor, false);
        if (hover >= 0) g.renderTooltip(font, Ui.name(ids.get(hover)), mx, my);
    }

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        int i = tileAt(mx, my);
        if (i >= 0) {
            String id = ids.get(i);
            if (button == 1) { ClientEmotes.toggleFavorite(id); refreshButtons(); return true; }
            if (id.equals(preview.id()) && button == 0 && System.currentTimeMillis() - lastClick < 350) { use(); return true; }
            lastClick = System.currentTimeMillis();
            preview.select(id);
            preview.restart();
            lastSelected = id;
            refreshButtons();
            return true;
        }
        if (preview.mouseClicked(mx, my, prevX, prevY, prevW, prevH)) return true;
        return super.mouseClicked(mx, my, button);
    }

    private long lastClick;

    @Override
    public boolean mouseDragged(double mx, double my, int b, double dx, double dy) {
        preview.mouseDragged(mx, my);
        return super.mouseDragged(mx, my, b, dx, dy);
    }

    @Override
    public boolean mouseReleased(double mx, double my, int b) {
        preview.mouseReleased();
        return super.mouseReleased(mx, my, b);
    }

    @Override
    public void onClose() { minecraft.setScreen(parent); }

    @Override
    public boolean isPauseScreen() { return false; }
}
