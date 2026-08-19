from talon import Module, Context, actions, cron
from ..plugin.gamepad.xinput_buttons import Button, Trigger
from .character_regexes import get_regex
import random

ctx = Context()
ctx.matches = r"""
app: Grounded
"""
ctx.tags = ["user.game"]

# Overriden Contextualized Actions

@ctx.action_class("user")
class Actions:

    def talon_noise_pop():
        """Talon pop noise"""
        actions.skip()
    
    def talon_noise_hiss(active: bool):
        """Talon hiss noise"""
        actions.skip()

    def parrot_noise_cluck():
        """Parrot cluck"""
        actions.skip()

    def parrot_noise_hiss():
        """Parrot hiss"""
        actions.skip()

    def parrot_noise_horse_click():
        """Parrot horse_click"""
        actions.skip()

    def parrot_noise_lateral_click():
        """Parrot lateral_click"""
        actions.skip()

    def parrot_noise_whistle():
        """Parrot whistle"""
        actions.skip()

@ctx.action_class("user")
class Actions:

    def footpedal_ikkegol_dual_left_down():
        """pedal down"""
        actions.user.controller_button_down(Trigger.LEFT)

    def footpedal_ikkegol_dual_left_up():
        """pedal up"""
        actions.user.controller_button_up(Trigger.LEFT)

    def footpedal_ikkegol_dual_right_down():
        """pedal down"""
        actions.user.controller_button_down(Button.X)

    def footpedal_ikkegol_dual_right_up():
        """pedal up"""
        actions.user.controller_button_up(Button.X)

    def footpedal_ikkegol_single_down():
        """pedal down"""
        pass

    def footpedal_ikkegol_single_up():
        """pedal up"""
        pass

    def footpedal_olympus_left_down():
        """pedal down"""
        actions.skip()

    def footpedal_olympus_left_up():
        """pedal up"""
        actions.skip()

    def footpedal_olympus_center_down():
        """pedal down"""
        actions.skip()

    def footpedal_olympus_center_up():
        """pedal up"""
        actions.skip()

    def footpedal_olympus_right_down():
        """pedal down"""
        actions.skip()

    def footpedal_olympus_right_up():
        """pedal up"""
        actions.skip()

    def footpedal_olympus_top_down():
        """pedal down"""
        actions.skip()

    def footpedal_olympus_top_up():
        """pedal up"""
        actions.skip()
