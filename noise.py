from talon import noise, ctrl, scope

def on_pop(active):
    if "command" in scope.get("mode"):
        ctrl.mouse_click(button=0)
        print ("on_pop", active)

def on_hiss(active):
    if "command" in scope.get("mode"):
        ctrl.mouse_click(button=1)
        print ("on_hiss", active)

noise.register("pop", on_pop)
noise.register("hiss", on_hiss)
