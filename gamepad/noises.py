from talon import Module, noise, actions

mod = Module()

@mod.action_class
class Actions:

    def noise_talon_pop():
        """Talon pop noise"""
        pass
    
    def noise_talon_hiss():
        """Talon hiss noise"""
        pass

    def parrot_noise_whistle():
        """Parrot whistle"""
        pass
        

# Talon Noise mapping 

def on_pop(active):
    actions.user.noise_talon_pop()

def on_hiss(active):
    actions.user.noise_talon_hiss()

noise.register("pop", on_pop)
noise.register("hiss", on_hiss)
