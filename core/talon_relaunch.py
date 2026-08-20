from talon import Module, ui, app
import os


mod = Module()

@mod.action_class
class ModeActions:
     def talon_relaunch():
        """Quit and relaunch the Talon app"""
        talon_app = ui.apps(pid=os.getpid())[0]
        if app.platform == "windows":
            os.startfile(talon_app.exe)
            talon_app.quit()
