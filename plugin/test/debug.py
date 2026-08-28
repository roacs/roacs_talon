from talon import Module, cron

from .gameinput_controller import get_controller

mod = Module()

_job = None
_device = None

def poll_controller():
    """Called on every cron.interval tick while polling is active."""

    global _device

    controller = get_controller()

    if _device is None:
        devices = controller.enumerate_devices()
        if not devices:
            print("gameinput: no gamepads found")
            return
        _device = devices[0]
        print(f"gameinput: polling {_device}")

    state = controller.read_gamepad_state(_device)

    if state is None:
        print("gameinput: no reading available")
        return

    pressed = [name for name in (
        "A", "B", "X", "Y", "Menu", "View",
        "DPadUp", "DPadDown", "DPadLeft", "DPadRight",
        "LeftShoulder", "RightShoulder",
        "LeftThumbstick", "RightThumbstick",
    ) if state[name]]

    print(
        f"gameinput: buttons=[{', '.join(pressed)}] "
        f"LT={state['LeftTrigger']:.2f} RT={state['RightTrigger']:.2f} "
        f"LX={state['LeftThumbstickX']:+.2f} LY={state['LeftThumbstickY']:+.2f} "
        f"RX={state['RightThumbstickX']:+.2f} RY={state['RightThumbstickY']:+.2f}"
    )

@mod.action_class
class Actions:

    def gameinput_poll_start():
        """Start polling the gamepad and printing its state."""

        global _job

        if _job is not None:
            print("gameinput: already polling")
            return

        _job = cron.interval("100ms", poll_controller)
        print("gameinput: started polling")

    def gameinput_poll_stop():
        """Stop polling the gamepad."""

        global _job, _device

        if _job is None:
            print("gameinput: not polling")
            return

        cron.cancel(_job)
        _job = None
        _device = None
        print("gameinput: stopped polling")

    def gameinput_devices():
        """Print connected GameInput devices."""
        get_controller().print_devices()
