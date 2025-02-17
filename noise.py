from talon import noise, ctrl

def on_pop(active):
    ctrl.mouse_click(button=0)
    print ("on_pop", active)

def on_hiss(active):
    print ("on_hiss", active)
    ctrl.mouse_click(button=1)

noise.register("pop", on_pop)
#noise.register("hiss", on_hiss)
