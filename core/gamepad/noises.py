from talon import noise, actions
from .xbox_buttons import Button

def on_pop(active):
    actions.user.controller_button_press(Button.X)

noise.register("pop", on_pop)

