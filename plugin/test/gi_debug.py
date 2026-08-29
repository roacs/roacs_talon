from talon import Module, cron
import time

from .gameinput_controller import get_controller

mod = Module()

_job = None
_device = None
_controller = get_controller(ignored_devices=[(0x045E, 0x028E)])


#TARGET_VENDOR_ID = None
#TARGET_PRODUCT_ID = None
#TARGET_VENDOR_ID = 0x1532
#TARGET_PRODUCT_ID = 0x0A14
TARGET_VENDOR_ID = 0x057E
TARGET_PRODUCT_ID = 0x2006

def poll_controller():
    """Called on every cron.interval tick while polling is active."""

    global _device
    global _controller

    if TARGET_VENDOR_ID is not None and TARGET_PRODUCT_ID is not None:
        if _device is None:
            _device = _controller.get_device(TARGET_VENDOR_ID, TARGET_PRODUCT_ID)
            if _device is None:
                print(f"gameinput: target device VID=0x{TARGET_VENDOR_ID:04X} PID=0x{TARGET_PRODUCT_ID:04X} not found")
                return
            print(f"gameinput: polling {_device}")
            _controller.enable_joycon_standard_reporting(_device)
            time.sleep(0.1)


    state = _controller.read_gamepad_state(_device)

    if state is None:
        print("gameinput: no reading available")
        return

    #pressed = [name for name in (
    #    "A", "B", "X", "Y", "Menu", "View",
    #    "DPadUp", "DPadDown", "DPadLeft", "DPadRight",
    #    "LeftShoulder", "RightShoulder",
    #    "LeftThumbstick", "RightThumbstick",
    #) if state[name]]

    #print(
    #    f"gameinput: buttons=[{', '.join(pressed)}] "
    #    f"LT={state['LeftTrigger']:.2f} RT={state['RightTrigger']:.2f} "
    #    f"LX={state['LeftThumbstickX']:+.2f} LY={state['LeftThumbstickY']:+.2f} "
    #    f"RX={state['RightThumbstickX']:+.2f} RY={state['RightThumbstickY']:+.2f}"
    #)

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
        global _controller
        _controller.print_devices()
