from talon import noise, actions
import sys

def on_pop(active):
    actions.user.x_button_press()

noise.register("pop", on_pop)

