from talon import Module, actions, app

mod = Module()


@mod.action_class
class Actions:
    def command_mode():
        """Enter command mode"""
        actions.mode.disable("dictation")
        actions.mode.enable("command")

    def dictation_mode():
        """Enter dictation mode"""
        actions.mode.disable("command")
        actions.mode.enable("dictation")

    def talon_sleep():
        """Put Talon to sleep"""
        actions.speech.disable()
        actions.user.mouse_sleep()
        app.notify("Talon sleeping")

    def talon_wake():
        """Wake Talon from sleep"""
        actions.speech.enable()
        app.notify("Talon awake")
