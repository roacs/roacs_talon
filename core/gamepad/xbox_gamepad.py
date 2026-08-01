from talon import Module, cron
import threading
import vgamepad as vg

from .xbox_buttons import Button, Trigger
from .controller import XInputController, test_xinput


mod = Module()


# -----------------------------
# Virtual controller
# -----------------------------

gamepad = vg.VX360Gamepad()
gamepad.reset()
gamepad.update()


virtual_button_map = {
    Button.A.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    Button.B.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    Button.X.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    Button.Y.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    Button.LB.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    Button.RB.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    Button.BACK.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    Button.START.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    Button.L3.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    Button.R3.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    Button.DPAD_UP.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    Button.DPAD_DOWN.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    Button.DPAD_LEFT.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    Button.DPAD_RIGHT.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}


# -----------------------------
# Physical controller
# -----------------------------

controller = XInputController(index=1)

# -----------------------------
# External Inputs to controller
# -----------------------------

external_state_counters = {
    item.value: 0 for item in list(Button) + list(Trigger)
}

external_state_lock = threading.Lock()


# -----------------------------
# Poll XInput and update ViGEm
# -----------------------------

last_physical_state = None
last_external_state = None

# TODO revisit this logic and see if there are any bugs
def poll_controller():

    global last_physical_state
    global last_external_state

    physical = controller.read()

    with external_state_lock:
        external = external_state_counters.copy()

    if (physical == last_physical_state and external == last_external_state):
        return

    last_physical_state = physical
    last_external_state = external

    for name, button in virtual_button_map.items():
        pressed = (physical[name] or external[name] > 0)

        if pressed:
            gamepad.press_button(button)
        else:
            gamepad.release_button(button)


    gamepad.left_joystick(physical["LX"], physical["LY"])
    gamepad.right_joystick(physical["RX"], physical["RY"])

    gamepad.left_trigger(255 if external[Trigger.LEFT.value] > 0 else physical["LT"])
    gamepad.right_trigger(255 if external[Trigger.RIGHT.value] > 0 else physical["RT"])

    gamepad.update()


cron_job = cron.interval("4ms", poll_controller)
#cron_job = cron.interval("100ms", test_xinput)


# -----------------------------
# Talon actions
# -----------------------------

@mod.action_class
class Actions:

    def controller_button_down(button: Button | Trigger):
        """Press virtual controller button."""
        increment_external_state([button.value])

    def controller_button_up(button: Button | Trigger):
        """Release virtual controller button."""
        decrement_external_state([button.value])

    def controller_button_press(buttons: list[Button | Trigger]):
        """Press virtual controller buttons."""
        if buttons is None:
            return
        if not isinstance(buttons, list):
            buttons = [buttons]

        if buttons:
            values = [button.value for button in buttons]
            increment_external_state(values)
            cron.after("30ms", lambda: decrement_external_state(values))


def increment_external_state(names):
    with external_state_lock:
        for name in names:
            external_state_counters[name] += 1

def decrement_external_state(names):
    with external_state_lock:
        for name in names:
            external_state_counters[name] = max(0, external_state_counters[name] - 1)

