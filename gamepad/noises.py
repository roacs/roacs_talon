from talon import Module, noise, actions, ui

mod = Module()

@mod.action_class
class Actions:

    def noise_talon_pop():
        """Talon pop noise"""
        print(f"pop with no context override in {ui.active_app().name}")
    
    def noise_talon_hiss():
        """Talon hiss noise"""
        print(f"hiss with no context override in {ui.active_app().name}")

    def parrot_noise_whistle():
        """Parrot whistle"""
        print(f"whistle with no context override in {ui.active_app().name}")
        

# Talon Noise mapping 

def on_pop(active):
    actions.user.noise_talon_pop()

def on_hiss(active):
    actions.user.noise_talon_hiss()

noise.register("pop", on_pop)
noise.register("hiss", on_hiss)


