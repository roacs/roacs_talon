from talon import Module, actions
from .xbox_buttons import Button, Trigger

mod = Module()

@mod.action_class
class Actions:

    def press_dpad_up():
        """Send DPAD UP"""
        actions.user.controller_button_press(Button.DPAD_UP)

    def press_dpad_right():
        """Send DPAD RIGHT"""
        actions.user.controller_button_press(Button.DPAD_RIGHT)

    def press_dpad_down():
        """Send DPAD DOWN"""
        actions.user.controller_button_press(Button.DPAD_DOWN)

    def press_dpad_left():
        """Send DPAD LEFT"""
        actions.user.controller_button_press(Button.DPAD_LEFT)
