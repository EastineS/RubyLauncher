package su.rubycon.emotes.client;

import net.minecraft.client.CameraType;
import net.minecraft.client.Minecraft;
import net.minecraft.client.Screenshot;
import net.minecraft.server.MinecraftServer;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import su.rubycon.emotes.RubyconEmotes;
import su.rubycon.emotes.client.gui.EmoteMenuScreen;
import su.rubycon.emotes.client.gui.EmoteWheelScreen;

import java.util.ArrayList;
import java.util.List;

/**
 * Development-only scripted capture, enabled with -Drubycon_emotes.autotest=true.
 * Plays every emote in third person and screenshots it, then the chat picker, menu and wheel,
 * and quits. Used to verify rendering in a real client; inert in normal play.
 */
public final class DevAutotest {
    private record Step(int atTick, Runnable action) {}

    private static final List<Step> STEPS = new ArrayList<>();
    private static int tick = -1, next;

    public static void init() {
        if (!Boolean.getBoolean("rubycon_emotes.autotest")) return;
        MinecraftForge.EVENT_BUS.addListener(DevAutotest::onTick);
        // production launchers have no --quickPlaySingleplayer; open saves/test from the title screen
        MinecraftForge.EVENT_BUS.addListener((net.minecraftforge.client.event.ScreenEvent.Init.Post e) -> {
            if (e.getScreen() instanceof net.minecraft.client.gui.screens.TitleScreen && !worldRequested) {
                worldRequested = true;
                Minecraft mc = Minecraft.getInstance();
                mc.tell(() -> mc.createWorldOpenFlows().loadLevel(e.getScreen(), "test"));
            }
        });
    }

    private static boolean worldRequested;

    private static void server(String cmd) {
        MinecraftServer s = Minecraft.getInstance().getSingleplayerServer();
        if (s != null) s.execute(() -> s.getCommands().performPrefixedCommand(s.createCommandSourceStack(), cmd));
    }

    private static void shot(String name) {
        Minecraft mc = Minecraft.getInstance();
        Screenshot.grab(mc.gameDirectory, "autotest_" + name + ".png", mc.getMainRenderTarget(), c -> RubyconEmotes.LOG.info("autotest shot {}", name));
    }

    private static void build() {
        Minecraft mc = Minecraft.getInstance();
        int t = 40;
        STEPS.add(new Step(t, () -> {
            mc.setScreen(null);
            server("difficulty peaceful");
            server("time set 6000");
            server("weather clear");
            server("gamerule doDaylightCycle false");
            mc.options.hideGui = true;
            mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
            mc.player.setYRot(0); mc.player.setXRot(10);
        }));
        t += 60;
        // emote list comes from the server sync, not the bundled index
        for (String id : ClientEmotes.ids().isEmpty() ? List.of("laugh") : ClientEmotes.ids()) {
            int start = t;
            STEPS.add(new Step(start, () -> mc.player.connection.sendCommand("emote " + id)));
            STEPS.add(new Step(start + 14, () -> shot(id + "_a")));
            STEPS.add(new Step(start + 34, () -> shot(id + "_b")));
            t += 48;
        }
        STEPS.add(new Step(t, () -> { mc.options.hideGui = false; mc.options.setCameraType(CameraType.FIRST_PERSON); mc.player.connection.sendCommand("emote love"); }));
        STEPS.add(new Step(t + 20, () -> shot("hud")));
        // press the chat key so UI mods (Rubycon) open their own chat screen, as for a player
        STEPS.add(new Step(t + 26, () -> mc.setScreen(null)));  // e.g. a modpack's character picker
        STEPS.add(new Step(t + 30, () -> net.minecraft.client.KeyMapping.click(mc.options.keyChat.getKey())));
        STEPS.add(new Step(t + 38, () -> RubyconEmotes.LOG.info("autotest chat screen: {}", mc.screen == null ? "none" : mc.screen.getClass().getName())));
        STEPS.add(new Step(t + 40, () -> shot("chat_button")));
        STEPS.add(new Step(t + 44, () -> {
            // simulate a click on the emote button: same path as a real mouse press
            if (mc.screen != null) {
                var in = mc.screen;
                // click the centre of the emote button wherever the chat screen placed it
                int[] b = su.rubycon.emotes.client.gui.ChatEmoteButton.buttonRect(in);
                if (b == null) { RubyconEmotes.LOG.warn("autotest: no chat input found"); return; }
                double x = b[0] + b[2] / 2.0, y = b[1] + b[3] / 2.0;
                net.minecraftforge.client.ForgeHooksClient.onScreenMouseClickedPre(in, x, y, 0);
            }
        }));
        STEPS.add(new Step(t + 70, () -> shot("chat_popup")));
        STEPS.add(new Step(t + 80, () -> mc.setScreen(new EmoteMenuScreen(null))));
        STEPS.add(new Step(t + 110, () -> shot("menu")));
        STEPS.add(new Step(t + 120, () -> mc.setScreen(new EmoteWheelScreen(null))));
        STEPS.add(new Step(t + 140, () -> shot("wheel")));
        STEPS.add(new Step(t + 150, () -> { mc.setScreen(null); mc.player.getInventory().armor.set(3, new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.DIAMOND_HELMET));
            mc.options.hideGui = true; mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT); }));
        STEPS.add(new Step(t + 160, () -> mc.player.connection.sendCommand("emote facepalm")));
        STEPS.add(new Step(t + 180, () -> shot("helmet_facepalm")));
        STEPS.add(new Step(t + 210, () -> mc.player.connection.sendCommand("emote smug")));
        STEPS.add(new Step(t + 240, () -> shot("helmet_smug")));
        STEPS.add(new Step(t + 260, () -> { RubyconEmotes.LOG.info("autotest done"); mc.stop(); }));
    }

    private static void onTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null) return;
        if (tick < 0) { tick = 0; return; }
        tick++;
        if (tick == 39 && STEPS.isEmpty()) build();
        while (next < STEPS.size() && STEPS.get(next).atTick() <= tick) {
            try { STEPS.get(next).action().run(); } catch (Exception ex) { RubyconEmotes.LOG.error("autotest step failed", ex); }
            next++;
        }
    }

    private DevAutotest() {}
}
