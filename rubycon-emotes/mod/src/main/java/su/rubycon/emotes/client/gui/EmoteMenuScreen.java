package su.rubycon.emotes.client.gui;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import su.rubycon.emotes.client.ClientEmotes;

import java.util.List;

/** Full emote menu: grid of all emotes, live preview, favourites and the "use" action. */
public final class EmoteMenuScreen extends Screen {
    private static final int COLS = 6, GAP = 3;
    private int TILE_W = 46, TILE_H = 48;
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
        int rows = Math.max(4, (ids.size() + COLS - 1) / COLS);
        // fit 720p at GUI scale 3 (427x240): tiles shrink before anything else
        TILE_H = Math.max(30, Math.min(48, (height - 8 - 26 - 16 - (rows - 1) * GAP) / rows));
        TILE_W = Math.max(30, Math.min(46, TILE_H - 2));
        int gridW = COLS * TILE_W + (COLS - 1) * GAP, gridH = rows * (TILE_H + GAP) - GAP;
        prevW = Math.max(110, Math.min(150, width - 8 - 16 - gridW - 10 - 12));
        pw = 12 + gridW + 10 + prevW + 12;
        ph = 26 + gridH + 16;
        px = (width - pw) / 2;
        py = Math.max(4, (height - ph) / 2);
        gridX = px + 12;
        gridY = py + 26;
        prevX = gridX + gridW + 10;
        prevY = gridY;
        int buttons = 20 + 3 * 20 + 4;
        prevH = Math.max(70, gridH - buttons);
        String sel = lastSelected != null && ids.contains(lastSelected) ? lastSelected : (ids.isEmpty() ? null : ids.get(0));
        if (sel != null) preview.select(sel);

        int bx = prevX, by = prevY + prevH + 4;
        useBtn = addRenderableWidget(new Ui.HButton(bx, by, prevW, 18, Component.translatable("rubycon_emotes.menu.use"), b -> use(), true));
        favBtn = addRenderableWidget(new Ui.HButton(bx, by + 20, prevW - 38, 16, Component.empty(), b -> toggleFav(), false));
        leftBtn = addRenderableWidget(new Ui.HButton(bx + prevW - 36, by + 20, 17, 16, Component.literal("◀"), b -> move(-1), false));
        rightBtn = addRenderableWidget(new Ui.HButton(bx + prevW - 17, by + 20, 17, 16, Component.literal("▶"), b -> move(1), false));
        helmetBtn = addRenderableWidget(new Ui.HButton(bx, by + 40, prevW, 16, Component.empty(), b -> preview.helmet = !preview.helmet, false));
        cancelBtn = addRenderableWidget(new Ui.HButton(bx, by + 60, prevW / 2 - 2, 16, Component.translatable("rubycon_emotes.menu.cancel"), b -> {
            ClientEmotes.cancel();
            flash(Component.translatable("rubycon_emotes.msg.cancelled"));
        }, false));
        addRenderableWidget(new Ui.HButton(bx + prevW / 2 + 2, by + 60, prevW / 2 - 2, 16, Component.translatable("rubycon_emotes.menu.settings"),
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
            int is = Math.min(32, TILE_H - 13);
            Ui.icon(g, id, tx + (TILE_W - is) / 2, ty + 2 - (int) bounce, is, ok ? 1f : 0.35f);
            Component n = Ui.name(id);
            g.pose().pushPose();
            float s = 0.55f;
            g.pose().translate(tx + TILE_W / 2f, ty + TILE_H - 8, 0);
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
        if (preview.mouseOver(mx, my, prevX, prevY, prevW, prevH)) {
            g.fill(prevX + 1, prevY + prevH - 11, prevX + prevW - 1, prevY + prevH - 1, 0x99101422);
            g.pose().pushPose();
            g.pose().translate(prevX + 5, prevY + prevH - 8, 0);
            g.pose().scale(0.75f, 0.75f, 1);
            g.drawString(font, Component.translatable("rubycon_emotes.menu.drag"), 0, 0, 0xCCFFFFFF, false);
            g.pose().popPose();
        }
        super.render(g, mx, my, pt);
        Component foot = null;
        int footColor = Ui.MUTED;
        if (status != null && System.currentTimeMillis() < statusUntil) { foot = status; footColor = Ui.DANGER; }
        else if (!ClientEmotes.serverReady()) { foot = Component.translatable("rubycon_emotes.msg.no_server"); footColor = Ui.DANGER; }
        else if (ClientEmotes.cooldownLeft() > 0)
            foot = Component.translatable("rubycon_emotes.msg.cooldown_left", String.format(java.util.Locale.ROOT, "%.1f", ClientEmotes.cooldownLeft()));
        else foot = Component.translatable("rubycon_emotes.menu.hint");
        g.pose().pushPose();
        g.pose().translate(gridX, py + ph - 11, 0);
        g.pose().scale(0.75f, 0.75f, 1);
        g.drawString(font, foot, 0, 0, footColor, false);
        g.pose().popPose();
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
