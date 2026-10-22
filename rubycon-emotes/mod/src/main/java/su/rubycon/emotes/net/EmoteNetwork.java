package su.rubycon.emotes.net;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.network.*;
import net.minecraftforge.network.simple.SimpleChannel;
import su.rubycon.emotes.EmoteIndex;
import su.rubycon.emotes.RubyconEmotes;
import su.rubycon.emotes.server.EmoteServer;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;

public final class EmoteNetwork {
    private static final String VERSION = "1";
    public static final SimpleChannel CH = NetworkRegistry.newSimpleChannel(
            new ResourceLocation(RubyconEmotes.MODID, "main"), () -> VERSION,
            NetworkRegistry.acceptMissingOr(VERSION), NetworkRegistry.acceptMissingOr(VERSION));

    /** C2S: play emote (id) or stop (empty id). Only the id is sent — duration is decided by the server. */
    public record Play(String id) {
        static void enc(Play p, FriendlyByteBuf b) { b.writeUtf(p.id, 32); }
        static Play dec(FriendlyByteBuf b) { return new Play(b.readUtf(32)); }
        static void handle(Play p, Supplier<NetworkEvent.Context> ctx) {
            ServerPlayer sp = ctx.get().getSender();
            ctx.get().enqueueWork(() -> {
                if (sp == null) return;
                if (p.id.isEmpty()) { EmoteServer.stop(sp, true); return; }
                String err = EmoteServer.play(sp, p.id);
                if (err != null) sp.displayClientMessage(Component.translatable(err), true);
            });
            ctx.get().setPacketHandled(true);
        }
    }

    /** S2C: emote state of an entity; empty id = cleared. elapsedMs lets late observers join mid-animation. */
    public record State(int entityId, String id, int elapsedMs, int durationMs) {
        static void enc(State s, FriendlyByteBuf b) { b.writeVarInt(s.entityId); b.writeUtf(s.id, 32); b.writeVarInt(s.elapsedMs); b.writeVarInt(s.durationMs); }
        static State dec(FriendlyByteBuf b) { return new State(b.readVarInt(), b.readUtf(32), b.readVarInt(), b.readVarInt()); }
        static void handle(State s, Supplier<NetworkEvent.Context> ctx) {
            ctx.get().enqueueWork(() -> DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> su.rubycon.emotes.client.ClientEmotes.onState(s)));
            ctx.get().setPacketHandled(true);
        }
    }

    public record Entry(String id, String name, int durationMs, boolean allowed) {}
    /** S2C: server emote list + rules. */
    public record Sync(boolean enabled, int cooldownMs, int distance, List<Entry> entries) {
        static void enc(Sync s, FriendlyByteBuf b) {
            b.writeBoolean(s.enabled); b.writeVarInt(s.cooldownMs); b.writeVarInt(s.distance); b.writeVarInt(s.entries.size());
            for (Entry e : s.entries) { b.writeUtf(e.id, 32); b.writeUtf(e.name, EmoteIndex.MAX_NAME); b.writeVarInt(e.durationMs); b.writeBoolean(e.allowed); }
        }
        static Sync dec(FriendlyByteBuf b) {
            boolean en = b.readBoolean(); int cd = b.readVarInt(); int d = b.readVarInt(); int n = Math.min(b.readVarInt(), 512);
            List<Entry> l = new ArrayList<>();
            for (int i = 0; i < n; i++) l.add(new Entry(b.readUtf(32), b.readUtf(EmoteIndex.MAX_NAME), b.readVarInt(), b.readBoolean()));
            return new Sync(en, cd, d, l);
        }
        static void handle(Sync s, Supplier<NetworkEvent.Context> ctx) {
            ctx.get().enqueueWork(() -> DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> su.rubycon.emotes.client.ClientEmotes.onSync(s)));
            ctx.get().setPacketHandled(true);
        }
    }

    public static void register() {
        int i = 0;
        CH.messageBuilder(Play.class, i++, NetworkDirection.PLAY_TO_SERVER).encoder(Play::enc).decoder(Play::dec).consumerNetworkThread(Play::handle).add();
        CH.messageBuilder(State.class, i++, NetworkDirection.PLAY_TO_CLIENT).encoder(State::enc).decoder(State::dec).consumerNetworkThread(State::handle).add();
        CH.messageBuilder(Sync.class, i++, NetworkDirection.PLAY_TO_CLIENT).encoder(Sync::enc).decoder(Sync::dec).consumerNetworkThread(Sync::handle).add();
    }
}
