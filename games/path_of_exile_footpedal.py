from talon import Context, actions
from ..gamepad.xbox_buttons import Button, Trigger

ctx = Context()
ctx.matches = r"""
app: PathOfExileSteam.exe
"""

@ctx.action_class("user")
class Actions:

    def footpedal_ikkegol_dual_left_down():
        """pedal down"""
        actions.user.controller_button_down(Button.X)

    def footpedal_ikkegol_dual_left_up():
        """pedal up"""
        actions.user.controller_button_up(Button.X)

    def footpedal_ikkegol_dual_right_down():
        """pedal down"""
        pass

    def footpedal_ikkegol_dual_right_up():
        """pedal up"""
        pass

    def footpedal_olympus_left_down():
        """pedal down"""
        pass

    def footpedal_olympus_left_up():
        """pedal up"""
        pass

    def footpedal_olympus_center_down():
        """pedal down"""
        pass

    def footpedal_olympus_center_up():
        """pedal up"""
        pass

    def footpedal_olympus_right_down():
        """pedal down"""
        pass

    def footpedal_olympus_right_up():
        """pedal up"""
        pass

    def footpedal_olympus_top_down():
        """pedal down"""
        pass

    def footpedal_olympus_top_up():
        """pedal up"""
        pass
