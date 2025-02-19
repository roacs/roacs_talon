from talon import Module, actions, app

mod = Module()

@mod.action_class
class Actions:
    def talon_sleep():
        """Put Talon to sleep"""
        actions.speech.disable()
        app.notify("Talon asleep")

    def talon_wake():
        """Wake Talon from sleep"""
        actions.speech.enable()
        actions.mode.enable("command")
        app.notify("Talon awake")

