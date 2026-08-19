from talon import Module, actions, cron, noise, settings, ui

mod = Module()
hiss_cron = None

mod.setting(
    "hiss_scroll_debounce_time",
    type=int,
    default=100,
    desc="How much time a hiss must last for to be considered a hiss rather than part of speech, in ms",
)

@mod.action_class
class Actions:

    def talon_noise_pop():
        """Talon pop noise"""
        print(f"talon pop with no context override in {ui.active_app().name}")
    
    def talon_noise_hiss(active: bool):
        """Talon hiss noise"""
        print(f"talon hiss with no context override in {ui.active_app().name} active {active}")

    def parrot_noise_cluck():
        """Parrot cluck"""
        print(f"parrot cluck with no context override in {ui.active_app().name}")

    def parrot_noise_hiss():
        """Parrot hiss"""
        print(f"parrot hiss with no context override in {ui.active_app().name}")

    def parrot_noise_horse_click():
        """Parrot horse_click"""
        print(f"parrot horse_click with no context override in {ui.active_app().name}")

    def parrot_noise_lateral_click():
        """Parrot lateral_click"""
        print(f"parrot lateral_click with no context override in {ui.active_app().name}")

    def parrot_noise_whistle():
        """Parrot whistle"""
        print(f"parrot whistle with no context override in {ui.active_app().name}")
        

def noise_trigger_hiss_debounce(active: bool):
    """Since the hiss noise triggers while you're talking we need to debounce it"""
    global hiss_cron
    if active:
        hiss_cron = cron.after(
            str(f"{settings.get('user.hiss_scroll_debounce_time')}ms"),
            lambda: actions.user.talon_noise_hiss(active),
        )
    else:
        cron.cancel(hiss_cron)
        actions.user.talon_noise_hiss(active)


noise.register("pop", lambda _: actions.user.talon_noise_pop())
noise.register("hiss", noise_trigger_hiss_debounce)

