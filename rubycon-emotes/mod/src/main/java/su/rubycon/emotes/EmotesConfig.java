package su.rubycon.emotes;

import net.minecraftforge.common.ForgeConfigSpec;

import java.util.ArrayList;
import java.util.List;

public final class EmotesConfig {
    public enum Size {
        SMALL(0.75f), NORMAL(1f), LARGE(1.3f);
        public final float factor;
        Size(float f) { factor = f; }
    }

    // ---- server (per world, synced to clients in EmoteNetwork.Sync)
    public static final ForgeConfigSpec SERVER_SPEC;
    public static final ForgeConfigSpec.BooleanValue ENABLED;
    public static final ForgeConfigSpec.ConfigValue<List<? extends String>> ALLOWED;
    public static final ForgeConfigSpec.IntValue COOLDOWN_MS;
    public static final ForgeConfigSpec.DoubleValue MAX_DURATION;
    public static final ForgeConfigSpec.IntValue DISTANCE;
    public static final ForgeConfigSpec.ConfigValue<List<? extends String>> DISABLED_DIMENSIONS;
    public static final ForgeConfigSpec.ConfigValue<List<? extends String>> DISABLED_GAMEMODES;

    // ---- client
    public static final ForgeConfigSpec CLIENT_SPEC;
    public static final ForgeConfigSpec.BooleanValue SHOW_OTHERS;
    public static final ForgeConfigSpec.BooleanValue SHOW_OWN;
    public static final ForgeConfigSpec.BooleanValue SHOW_INDICATOR;
    public static final ForgeConfigSpec.EnumValue<Size> SIZE;
    public static final ForgeConfigSpec.BooleanValue REDUCED_MOTION;
    public static final ForgeConfigSpec.BooleanValue CHAT_BUTTON;
    public static final ForgeConfigSpec.ConfigValue<List<? extends String>> FAVORITES;

    static {
        ForgeConfigSpec.Builder b = new ForgeConfigSpec.Builder();
        b.push("emotes");
        ENABLED = b.comment("Включить систему эмоций").define("enabled", true);
        ALLOWED = b.comment("Разрешённые эмоции (пусто = все)")
                .defineListAllowEmpty(List.of("allowed"), List::of, o -> o instanceof String);
        COOLDOWN_MS = b.comment("Минимальный интервал между активациями, мс").defineInRange("cooldownMs", 2000, 250, 60000);
        MAX_DURATION = b.comment("Максимальная длительность эмоции, сек").defineInRange("maxDuration", 6.0, 1.0, 30.0);
        DISTANCE = b.comment("Дистанция отображения, блоков").defineInRange("displayDistance", 24, 4, 128);
        DISABLED_DIMENSIONS = b.comment("Измерения, где эмоции отключены, например minecraft:the_end")
                .defineListAllowEmpty(List.of("disabledDimensions"), List::of, o -> o instanceof String);
        DISABLED_GAMEMODES = b.comment("Режимы игры, где эмоции отключены: survival, creative, adventure, spectator")
                .defineListAllowEmpty(List.of("disabledGameModes"), () -> List.of("spectator"), o -> o instanceof String);
        b.pop();
        SERVER_SPEC = b.build();

        ForgeConfigSpec.Builder c = new ForgeConfigSpec.Builder();
        c.push("emotes");
        SHOW_OTHERS = c.comment("Показывать эмоции других игроков").define("showOthers", true);
        SHOW_OWN = c.comment("Показывать собственную эмоцию в третьем лице").define("showOwnThirdPerson", true);
        SHOW_INDICATOR = c.comment("Показывать индикатор собственной эмоции в первом лице").define("firstPersonIndicator", true);
        SIZE = c.comment("Масштаб эффектов").defineEnum("size", Size.NORMAL);
        REDUCED_MOTION = c.comment("Уменьшенная анимация: без дрожания и частых вспышек").define("reducedMotion", false);
        CHAT_BUTTON = c.comment("Кнопка эмоций рядом с полем ввода чата").define("chatButton", true);
        FAVORITES = c.comment("Избранное для колеса (до 8, по порядку секторов)")
                .defineListAllowEmpty(List.of("favorites"),
                        () -> List.of("joy", "laugh", "agree", "disagree", "think", "surprise", "sad", "blush"),
                        o -> o instanceof String);
        c.pop();
        CLIENT_SPEC = c.build();
    }

    public static List<String> favorites() {
        List<String> out = new ArrayList<>();
        for (String s : FAVORITES.get()) if (!out.contains(s) && out.size() < 8) out.add(s);
        return out;
    }

    public static void setFavorites(List<String> favs) {
        FAVORITES.set(new ArrayList<>(favs.subList(0, Math.min(8, favs.size()))));
        FAVORITES.save();
    }

    private EmotesConfig() {}
}
