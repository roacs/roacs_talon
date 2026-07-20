from talon import Module, app, actions
from .xbox_buttons import Button, Trigger

mod = Module()

layouts = {
    "path_of_exile": {
        "f13": Button.X,
    },
    "grounded": {
        "f13": Trigger.RIGHT,
        "f14": Button.X,
    },
    "default": {
        "f13": None,
        "f14": None,
        "f15": None,
        "f16": None,
    },
}

layout_names = list(layouts.keys())
current_layout_index = 0
current_layout = layout_names[0]

@mod.action_class
class Actions:

    def footpedal_down(action: str):
        """Activate logical footpedal action."""
        button = layouts[current_layout].get(action)
        if button:
            actions.user.controller_button_down(button)

    def footpedal_up(action: str):
        """Release logical footpedal action."""
        button = layouts[current_layout].get(action)
        if button:
            actions.user.controller_button_up(button)

    def cycle_footpedal_layout():
        """Cycle footpedal layout."""
        global current_layout_index
        global current_layout

        current_layout_index += 1
        if current_layout_index >= len(layout_names):
            current_layout_index = 0

        current_layout = layout_names[current_layout_index]
        print(current_layout)
        app.notify("Footpedal layout " + current_layout)
