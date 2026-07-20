from talon import Module, app, noise, actions
from .xbox_buttons import Button, Trigger

mod = Module()

layouts = {
    "path_of_exile": {
        "pop": Button.X,
        "hiss": None,
    },
    "grounded": {
        "pop": None,
        "hiss": None,
    },
    "default": {
        "pop": None,
        "hiss": None,
    },
}

layout_names = list(layouts.keys())
current_layout_index = 0
current_layout = layout_names[0]

@mod.action_class
class Actions:

    def cycle_noises_layout():
        """Cycle noise layout."""
        global current_layout_index
        global current_layout

        current_layout_index += 1
        if current_layout_index >= len(layout_names):
            current_layout_index = 0

        current_layout = layout_names[current_layout_index]
        print("Noise layout " + current_layout)
        app.notify("Noise layout " + current_layout)


# Noise listeners

def on_pop(active):
    button = layouts[current_layout].get("pop")
    if button:
        actions.user.controller_button_press(button)

def on_hiss(active):
    button = layouts[current_layout].get("hiss")
    if button:
        actions.user.controller_button_press(button)

# Noise registrations

noise.register("pop", on_pop)
noise.register("hiss", on_hiss)
