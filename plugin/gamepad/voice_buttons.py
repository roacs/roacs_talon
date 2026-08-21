from talon import Module, actions
from .xinput_buttons import Button, Trigger

mod = Module()

mod.list("voice_button_phrase", desc="Voice button phrases")

BUTTON_PHRASES = {
    "pad up": Button.DPAD_UP,
    "pad down": Button.DPAD_DOWN,
    "pad left": Button.DPAD_LEFT,
    "pad right": Button.DPAD_RIGHT,
    "bump left": Button.LB,
    "bump right": Button.RB,
    "butt a": Button.A,
    "butt b": Button.B,
    "butt x": Button.X,
    "butt y": Button.Y,
    "back": Button.BACK,
    "start": Button.START,
}

@mod.action_class
class Actions:

    def press_voice_button(voice_button_phrase: str):
        """Press the voice button mapped to voice command"""
        button = BUTTON_PHRASES.get(voice_button_phrase)
        print(button)
        if button is not None:
            actions.user.controller_button_press(button)
