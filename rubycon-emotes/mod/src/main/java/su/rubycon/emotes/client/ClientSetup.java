package su.rubycon.emotes.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.entity.player.PlayerRenderer;
import net.minecraftforge.client.event.*;
import net.minecraftforge.client.gui.overlay.VanillaGuiOverlay;
import net.minecraftforge.client.settings.KeyConflictContext;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import org.lwjgl.glfw.GLFW;
import su.rubycon.emotes.client.gui.ChatEmoteButton;
import su.rubycon.emotes.client.gui.EmoteHud;
import su.rubycon.emotes.client.gui.EmoteMenuScreen;
import su.rubycon.emotes.client.gui.EmoteWheelScreen;

public final class ClientSetup {
    private static final String CAT = "key.categories.rubycon_emotes";
    /** Tap: full menu. Hold: favourites wheel. */
    public static final KeyMapping EMOTES = new KeyMapping("key.rubycon_emotes.emotes", KeyConflictContext.IN_GAME,
            InputConstants.Type.KEYSYM, GLFW.GLFW_KEY_G, CAT);
    public static final KeyMapping MENU = new KeyMapping("key.rubycon_emotes.menu", KeyConflictContext.IN_GAME,
            InputConstants.UNKNOWN, CAT);
    public static final KeyMapping WHEEL = new KeyMapping("key.rubycon_emotes.wheel", KeyConflictContext.IN_GAME,
            InputConstants.UNKNOWN, CAT);
    private static final long HOLD_MS = 250;
    private static long pressedAt = -1;

    public static void init(IEventBus modBus) {
        modBus.addListener((RegisterKeyMappingsEvent e) -> { e.register(EMOTES); e.register(MENU); e.register(WHEEL); });
        modBus.addListener((RegisterClientReloadListenersEvent e) -> e.registerReloadListener(new EmoteDefs()));
        modBus.addListener((RegisterGuiOverlaysEvent e) -> e.registerAbove(VanillaGuiOverlay.HOTBAR.id(), "emote_indicator", new EmoteHud()));
        modBus.addListener(ClientSetup::addLayers);
        DevAutotest.init();
        var bus = MinecraftForge.EVENT_BUS;
        bus.register(ChatEmoteButton.class);
        bus.addListener(ClientSetup::onTick);
        bus.addListener((ClientPlayerNetworkEvent.LoggingOut e) -> ClientEmotes.onDisconnect());
        bus.addListener((ClientPlayerNetworkEvent.Clone e) -> ClientEmotes.clear());
        bus.addListener((RenderLevelStageEvent e) -> {
            if (e.getStage() == RenderLevelStageEvent.Stage.AFTER_WEATHER) ClientEmotes.endFrame();
        });
    }

    private static void addLayers(EntityRenderersEvent.AddLayers e) {
        for (String skin : e.getSkins()) {
            if (e.getSkin(skin) instanceof PlayerRenderer r) r.addLayer(new EmoteLayer(r));
        }
    }

    private static void onTick(TickEvent.ClientTickEvent e) {
        if (e.phase != TickEvent.Phase.END) return;
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null) { pressedAt = -1; return; }
        if (mc.screen != null) {
            pressedAt = -1;
            return;
        }
        long now = System.currentTimeMillis();
        // a press and release between two ticks leaves isDown() false but still records a click
        boolean clicked = false;
        while (EMOTES.consumeClick()) clicked = true;
        if (EMOTES.isDown()) {
            if (pressedAt < 0) pressedAt = now;
            else if (now - pressedAt >= HOLD_MS) {
                pressedAt = -1;
                mc.setScreen(new EmoteWheelScreen(EMOTES));
            }
        } else if (pressedAt >= 0 || clicked) {
            pressedAt = -1;
            mc.setScreen(new EmoteMenuScreen(null));
        }
        if (mc.screen != null) return;
        while (MENU.consumeClick()) mc.setScreen(new EmoteMenuScreen(null));
        if (WHEEL.isDown() && mc.screen == null) mc.setScreen(new EmoteWheelScreen(WHEEL));
        while (WHEEL.consumeClick()) { }
    }

    private ClientSetup() {}
}
