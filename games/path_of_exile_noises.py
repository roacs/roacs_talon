from talon import Context, actions
from ..gamepad.xbox_buttons import Button, Trigger

ctx = Context()
ctx.matches = r"""
app: PathOfExileSteam.exe
"""

@ctx.action_class("user")
class Actions:

    def noise_talon_pop():
        """Talon pop noise"""
        actions.user.controller_button_press(Button.Y)
    
    def noise_talon_hiss():
        """Talon hiss noise"""
        pass

    def parrot_noise_whistle():
        """Parrot whistle"""
        actions.user.controller_button_press(Button.A)
