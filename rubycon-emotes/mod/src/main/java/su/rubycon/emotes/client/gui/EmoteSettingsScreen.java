package su.rubycon.emotes.client.gui;

import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraftforge.common.ForgeConfigSpec;
import su.rubycon.emotes.EmotesConfig;

import java.util.function.Supplier;

public final class EmoteSettingsScreen extends Screen {
    private final Screen parent;
    private int px, py, pw, ph;

    public EmoteSettingsScreen(Screen parent) {
        super(Component.translatable("rubycon_emotes.settings.title"));
        this.parent = parent;
    }

    @Override
    protected void init() {
        pw = 260;
        ph = 28 + 7 * 24 + 34;
        px = (width - pw) / 2;
        py = (height - ph) / 2;
        int x = px + 16, w = pw - 32, y = py + 28;
        toggle(x, y, w, "show_others", EmotesConfig.SHOW_OTHERS); y += 24;
        toggle(x, y, w, "show_own", EmotesConfig.SHOW_OWN); y += 24;
        toggle(x, y, w, "indicator", EmotesConfig.SHOW_INDICATOR); y += 24;
        toggle(x, y, w, "reduced", EmotesConfig.REDUCED_MOTION); y += 24;
        toggle(x, y, w, "chat_button", EmotesConfig.CHAT_BUTTON); y += 24;
        Supplier<Component> size = () -> Component.translatable("rubycon_emotes.settings.size",
                Component.translatable("rubycon_emotes.size." + EmotesConfig.SIZE.get().name().toLowerCase()));
        Ui.HButton sb = new Ui.HButton(x, y, w, 20, size.get(), b -> {}, false);
        sb = addRenderableWidget(new Ui.HButton(x, y, w, 20, size.get(), b -> {
            EmotesConfig.Size[] v = EmotesConfig.Size.values();
            EmotesConfig.SIZE.set(v[(EmotesConfig.SIZE.get().ordinal() + 1) % v.length]);
            EmotesConfig.SIZE.save();
            b.setMessage(size.get());
        }, false));
        y += 24;
        addRenderableWidget(new Ui.HButton(x, y, w, 20, Component.translatable("rubycon_emotes.settings.keys"),
                b -> minecraft.setScreen(new net.minecraft.client.gui.screens.controls.KeyBindsScreen(this, minecraft.options)), false));
        addRenderableWidget(new Ui.HButton(px + pw / 2 - 50, py + ph - 28, 100, 20, Component.translatable("gui.done"), b -> onClose(), true));
    }

    private void toggle(int x, int y, int w, String key, ForgeConfigSpec.BooleanValue v) {
        Supplier<Component> label = () -> Component.translatable("rubycon_emotes.settings." + key)
                .append(": ").append(Component.translatable(v.get() ? "options.on" : "options.off"));
        addRenderableWidget(new Ui.HButton(x, y, w, 20, label.get(), b -> {
            v.set(!v.get());
            v.save();
            b.setMessage(label.get());
        }, false));
    }

    @Override
    public void render(GuiGraphics g, int mx, int my, float pt) {
        renderBackground(g);
        Ui.panel(g, px, py, pw, ph);
        Ui.title(g, font, title, px, py + 9, pw);
        super.render(g, mx, my, pt);
    }

    @Override
    public void onClose() { minecraft.setScreen(parent); }
}
