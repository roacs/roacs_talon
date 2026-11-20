from talon import Module, cron
import time

from .gameinput_test import GameInputController

mod = Module()

_job = None
#_gameinput_controller = GameInputController()

TARGET_VENDOR_ID = 0x1532
TARGET_PRODUCT_ID = 0x0A14

@mod.action_class
class Actions:

    def gameinput_devices():
        """Print connected GameInput devices."""
        #global _gameinput_controller
        _gameinput_controller = GameInputController()
        _gameinput_controller.print_devices()
