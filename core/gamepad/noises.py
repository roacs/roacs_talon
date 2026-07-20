from talon import noise, actions
from .xbox_buttons import Button

def on_pop(active):
    actions.user.controller_press_button(Button.X)

noise.register("pop", on_pop)

