package su.rubycon.emotes.server;

import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.GameType;
import net.minecraftforge.event.RegisterCommandsEvent;
import net.minecraftforge.event.TickEvent;
import net.minecraftforge.event.entity.living.LivingDeathEvent;
import net.minecraftforge.event.entity.player.PlayerEvent;
import net.minecraftforge.event.server.ServerStartingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.event.config.ModConfigEvent;
import net.minecraftforge.network.PacketDistributor;
import net.minecraftforge.server.ServerLifecycleHooks;
import su.rubycon.emotes.EmoteIndex;
import su.rubycon.emotes.EmotesConfig;
import su.rubycon.emotes.RubyconEmotes;
import su.rubycon.emotes.net.EmoteNetwork;

import java.util.*;

/** Authoritative emote state: validates ids, enforces cooldown and duration, broadcasts to observers. */
@Mod.EventBusSubscriber(modid = RubyconEmotes.MODID)
public final class EmoteServer {
    private record Active(String id, long startMs, int durationMs) {
        int elapsed(long now) { return (int) Math.max(0, now - startMs); }
        boolean expired(long now) { return now - startMs >= durationMs; }
    }

    private static final Map<UUID, Active> ACTIVE = new HashMap<>();
    private static final Map<UUID, Long> LAST_PLAY = new HashMap<>();
    private static int tick;

    public static boolean allowed(String id) {
        if (EmoteIndex.get(id) == null) return false;
        List<? extends String> allow = EmotesConfig.ALLOWED.get();
        return allow.isEmpty() || allow.contains(id);
    }

    private static boolean blockedHere(ServerPlayer p) {
        if (!EmotesConfig.ENABLED.get()) return true;
        String dim = p.level().dimension().location().toString();
        if (EmotesConfig.DISABLED_DIMENSIONS.get().contains(dim)) return true;
        return EmotesConfig.DISABLED_GAMEMODES.get().contains(p.gameMode.getGameModeForPlayer().getName());
    }

    private static int durationOf(EmoteIndex.Info info) {
        return (int) Math.min(info.durationMs(), Math.round(EmotesConfig.MAX_DURATION.get() * 1000));
    }

    /** @return null on success, otherwise a translation key describing the refusal. */
    public static String play(ServerPlayer p, String id) {
        if (blockedHere(p)) return "rubycon_emotes.msg.disabled";
        if (!allowed(id)) return "rubycon_emotes.msg.unknown";
        long now = System.currentTimeMillis();
        Long last = LAST_PLAY.get(p.getUUID());
        if (last != null && now - last < EmotesConfig.COOLDOWN_MS.get()) return "rubycon_emotes.msg.cooldown";
        LAST_PLAY.put(p.getUUID(), now);
        Active a = new Active(id, now, durationOf(EmoteIndex.get(id)));
        ACTIVE.put(p.getUUID(), a);
        send(p, new EmoteNetwork.State(p.getId(), id, 0, a.durationMs()));
        return null;
    }

    public static void stop(ServerPlayer p, boolean broadcast) {
        if (ACTIVE.remove(p.getUUID()) != null && broadcast) send(p, new EmoteNetwork.State(p.getId(), "", 0, 0));
    }

    private static void send(ServerPlayer p, EmoteNetwork.State s) {
        EmoteNetwork.CH.send(PacketDistributor.TRACKING_ENTITY_AND_SELF.with(() -> p), s);
    }

    public static EmoteNetwork.Sync syncPacket() {
        List<EmoteNetwork.Entry> entries = new ArrayList<>();
        for (EmoteIndex.Info i : EmoteIndex.all()) entries.add(new EmoteNetwork.Entry(i.id(), i.name(), durationOf(i), allowed(i.id())));
        return new EmoteNetwork.Sync(EmotesConfig.ENABLED.get(), EmotesConfig.COOLDOWN_MS.get(), EmotesConfig.DISTANCE.get(), entries);
    }

    private static void syncAll() {
        var server = ServerLifecycleHooks.getCurrentServer();
        if (server == null) return;
        // config reloads arrive on the file-watcher thread
        server.execute(() -> {
            EmoteNetwork.Sync s = syncPacket();
            for (ServerPlayer p : server.getPlayerList().getPlayers()) EmoteNetwork.CH.send(PacketDistributor.PLAYER.with(() -> p), s);
        });
    }

    // ------------------------------------------------------------------ lifecycle
    @SubscribeEvent
    public static void onStart(ServerStartingEvent e) {
        EmoteIndex.reload();
        ACTIVE.clear();
        LAST_PLAY.clear();
    }

    @SubscribeEvent
    public static void onLogin(PlayerEvent.PlayerLoggedInEvent e) {
        if (e.getEntity() instanceof ServerPlayer sp) EmoteNetwork.CH.send(PacketDistributor.PLAYER.with(() -> sp), syncPacket());
    }

    @SubscribeEvent
    public static void onLogout(PlayerEvent.PlayerLoggedOutEvent e) {
        if (e.getEntity() instanceof ServerPlayer sp) {
            stop(sp, true);
            LAST_PLAY.remove(sp.getUUID());
        }
    }

    @SubscribeEvent
    public static void onDeath(LivingDeathEvent e) {
        if (e.getEntity() instanceof ServerPlayer sp) stop(sp, true);
    }

    @SubscribeEvent
    public static void onDimension(PlayerEvent.PlayerChangedDimensionEvent e) {
        if (e.getEntity() instanceof ServerPlayer sp) stop(sp, true);
    }

    @SubscribeEvent
    public static void onRespawn(PlayerEvent.PlayerRespawnEvent e) {
        if (e.getEntity() instanceof ServerPlayer sp) stop(sp, true);
    }

    @SubscribeEvent
    public static void onGameMode(PlayerEvent.PlayerChangeGameModeEvent e) {
        GameType mode = e.getNewGameMode();
        if (e.getEntity() instanceof ServerPlayer sp && EmotesConfig.DISABLED_GAMEMODES.get().contains(mode.getName())) stop(sp, true);
    }

    /** Late observers get the remaining part of the animation, not a restart. */
    @SubscribeEvent
    public static void onTrack(PlayerEvent.StartTracking e) {
        if (!(e.getTarget() instanceof Player target) || !(e.getEntity() instanceof ServerPlayer viewer)) return;
        Active a = ACTIVE.get(target.getUUID());
        long now = System.currentTimeMillis();
        if (a != null && !a.expired(now))
            EmoteNetwork.CH.send(PacketDistributor.PLAYER.with(() -> viewer), new EmoteNetwork.State(target.getId(), a.id(), a.elapsed(now), a.durationMs()));
    }

    @SubscribeEvent
    public static void onTick(TickEvent.ServerTickEvent e) {
        if (e.phase != TickEvent.Phase.END || ++tick % 20 != 0) return;
        long now = System.currentTimeMillis();
        ACTIVE.values().removeIf(a -> a.expired(now));
        LAST_PLAY.values().removeIf(t -> now - t > 120_000);
    }

    @SubscribeEvent
    public static void onCommands(RegisterCommandsEvent e) {
        e.getDispatcher().register(Commands.literal("emote")
                .then(Commands.literal("stop").executes(c -> {
                    stop(c.getSource().getPlayerOrException(), true);
                    return 1;
                }))
                .then(Commands.literal("list").executes(c -> {
                    StringBuilder sb = new StringBuilder();
                    for (EmoteIndex.Info i : EmoteIndex.all()) if (allowed(i.id())) sb.append(sb.isEmpty() ? "" : ", ").append(i.id());
                    c.getSource().sendSuccess(() -> Component.literal(sb.toString()), false);
                    return 1;
                }))
                .then(Commands.argument("id", StringArgumentType.word())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(EmoteIndex.all().stream().map(EmoteIndex.Info::id).filter(EmoteServer::allowed), b))
                        .executes(c -> {
                            CommandSourceStack src = c.getSource();
                            String err = play(src.getPlayerOrException(), StringArgumentType.getString(c, "id"));
                            if (err != null) src.sendFailure(Component.translatable(err));
                            return err == null ? 1 : 0;
                        })));
    }

    @Mod.EventBusSubscriber(modid = RubyconEmotes.MODID, bus = Mod.EventBusSubscriber.Bus.MOD)
    public static final class ModEvents {
        @SubscribeEvent
        public static void onConfig(ModConfigEvent.Reloading e) {
            if (e.getConfig().getType() == ModConfig.Type.SERVER) syncAll();
        }
    }

    private EmoteServer() {}
}
