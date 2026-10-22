package su.rubycon.emotes.client.gui;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import org.joml.Quaternionf;
import su.rubycon.emotes.client.ClientEmotes;
import su.rubycon.emotes.client.EmoteDefs;
import su.rubycon.emotes.client.EmoteLayer;

/** Local-only preview: the player's own model with the emote looping. Never touches the network. */
public final class EmotePreview {
    public float yaw = -25, pitch = 8;
    public boolean helmet;
    private String id;
    private long start;
    private boolean dragging;
    private double lastX, lastY;

    public void select(String id) {
        if (!id.equals(this.id)) { this.id = id; start = System.currentTimeMillis(); }
    }

    public void restart() { start = System.currentTimeMillis(); }

    public String id() { return id; }

    /** Renders a bust inside [x, y, w, h]. */
    public void render(GuiGraphics g, int x, int y, int w, int h) {
        Minecraft mc = Minecraft.getInstance();
        LocalPlayer p = mc.player;
        g.fillGradient(x, y, x + w, y + h, 0xFF3A4258, 0xFF5A6278);
        Ui.frame(g, x, y, w, h, Ui.GOLD_FAINT);
        if (id == null || EmoteDefs.get(id) == null) return;
        if (p == null) {
            Ui.icon(g, id, x + w / 2 - 32, y + h / 2 - 32, 64, 1);
            return;
        }
        int scale = (int) (h * 0.62f);
        int feetY = y + h + (int) (scale * 0.62f);
        ItemStack oldHelmet = p.getInventory().armor.get(3);
        float bodyRot = p.yBodyRot, yRot = p.getYRot(), xRot = p.getXRot(), head = p.yHeadRot, headO = p.yHeadRotO, bodyO = p.yBodyRotO;
        g.enableScissor(x + 1, y + 1, x + w - 1, y + h - 1);
        try {
            ClientEmotes.previewOverride = new ClientEmotes.Playing(id, start, Integer.MAX_VALUE);
            EmoteLayer.previewHelmet = helmet;
            // client-side only swap so the helmet toggle can be judged regardless of equipment
            p.getInventory().armor.set(3, helmet ? (oldHelmet.isEmpty() ? new ItemStack(Items.IRON_HELMET) : oldHelmet) : ItemStack.EMPTY);
            p.yBodyRot = p.yBodyRotO = 180 + yaw;
            p.setYRot(180 + yaw);
            p.setXRot(0);
            p.yHeadRot = p.yHeadRotO = 180 + yaw;
            Quaternionf pose = new Quaternionf().rotateZ((float) Math.PI);
            Quaternionf cam = new Quaternionf().rotateX((float) Math.toRadians(pitch));
            pose.mul(cam);
            InventoryScreen.renderEntityInInventory(g, x + w / 2, feetY, scale, pose, cam, p);
        } finally {
            p.getInventory().armor.set(3, oldHelmet);
            p.yBodyRot = bodyRot; p.yBodyRotO = bodyO; p.setYRot(yRot); p.setXRot(xRot); p.yHeadRot = head; p.yHeadRotO = headO;
            ClientEmotes.previewOverride = null;
            EmoteLayer.previewHelmet = null;
            g.disableScissor();
        }
    }

    public boolean mouseClicked(double mx, double my, int x, int y, int w, int h) {
        if (mx >= x && mx < x + w && my >= y && my < y + h) { dragging = true; lastX = mx; lastY = my; return true; }
        return false;
    }

    public boolean mouseOver(double mx, double my, int x, int y, int w, int h) {
        return dragging || (mx >= x && mx < x + w && my >= y && my < y + h);
    }

    public void mouseDragged(double mx, double my) {
        if (!dragging) return;
        yaw += (float) (mx - lastX) * 1.2f;
        pitch = Math.max(-30, Math.min(40, pitch + (float) (my - lastY) * 0.6f));
        lastX = mx; lastY = my;
    }

    public void mouseReleased() { dragging = false; }
}
