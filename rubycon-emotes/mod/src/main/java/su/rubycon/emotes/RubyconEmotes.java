package su.rubycon.emotes;

import com.mojang.logging.LogUtils;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.DistExecutor;
import net.minecraftforge.fml.ModLoadingContext;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.config.ModConfig;
import net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;
import su.rubycon.emotes.net.EmoteNetwork;

@Mod(RubyconEmotes.MODID)
public final class RubyconEmotes {
    public static final String MODID = "rubycon_emotes";
    public static final Logger LOG = LogUtils.getLogger();

    public RubyconEmotes() {
        ModLoadingContext.get().registerConfig(ModConfig.Type.SERVER, EmotesConfig.SERVER_SPEC);
        ModLoadingContext.get().registerConfig(ModConfig.Type.CLIENT, EmotesConfig.CLIENT_SPEC);
        var bus = FMLJavaModLoadingContext.get().getModEventBus();
        bus.addListener((FMLCommonSetupEvent e) -> e.enqueueWork(() -> { EmoteNetwork.register(); EmoteIndex.reload(); }));
        DistExecutor.unsafeRunWhenOn(Dist.CLIENT, () -> () -> su.rubycon.emotes.client.ClientSetup.init(bus));
    }
}
