from talon import Module, cron
import time

from .gameinput_controller import GameInputController, GamepadNotFoundError

mod = Module()

_job = None
_gameinput_controller = None

TARGET_VENDOR_ID = 0x1532
TARGET_PRODUCT_ID = 0x0A14

def poll_controller():
    """Called on every cron.interval tick while polling is active."""

    global _gameinput_controller

    try:
        state = _gameinput_controller.get_gamepad_state()

        if state is None:
            print("gameinput: no reading available")
            return

        print(state)
    except GamepadNotFoundError as e:
        print(e)

@mod.action_class
class Actions:

    def gameinput_poll_start():
        """Start polling the gamepad and printing its state."""

        global _job, _gameinput_controller

        if _job is not None:
            print("gameinput: already polling")
            return

        _gameinput_controller = GameInputController(TARGET_VENDOR_ID, TARGET_PRODUCT_ID)

        _job = cron.interval("100ms", poll_controller)
        print("gameinput: started polling")

    def gameinput_poll_stop():
        """Stop polling the gamepad."""

        global _job, _gameinput_controller

        if _job is None:
            print("gameinput: not polling")
            return

        cron.cancel(_job)
        _job = None
        _gameinput_controller.close()
        _gameinput_controller = None
        print("gameinput: stopped polling")

    def gameinput_devices():
        """Print connected GameInput devices."""
        global _controller
        _controller.print_devices()
