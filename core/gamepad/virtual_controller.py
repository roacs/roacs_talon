from talon import Module, cron
import threading
import vgamepad as vg

from .xinput_buttons import Button, Trigger
from .xinput_controller import XInputController, ControllerState, print_controller_state


mod = Module()

# -----------------------------
# Physical controller
# -----------------------------

controller = XInputController(index=1)

# uncomment this and view the log while pressing things on controller to find index
#cron_job = cron.interval("100ms", print_controller_state)

# -----------------------------
# Virtual controller
# -----------------------------

gamepad = vg.VX360Gamepad()
gamepad.reset()
gamepad.update()

virtual_button_map = {
    Button.A: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    Button.B: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    Button.X: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    Button.Y: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    Button.LB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    Button.RB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    Button.BACK: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    Button.START: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    Button.L3: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    Button.R3: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    Button.DPAD_UP: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    Button.DPAD_DOWN: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    Button.DPAD_LEFT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    Button.DPAD_RIGHT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}

# -----------------------------
# Inputs External from the physical controller
# -----------------------------

external_state_counters = {
    item: 0 for item in list(Button) + list(Trigger)
}

external_state_lock = threading.Lock()


# -----------------------------
# Poll XInput and update ViGEm
# -----------------------------

last_physical_state = None
last_external_state = None

# TODO revisit this logic and see if there are any bugs
#      do we need to abort if the state is the same? is writing to virtual at 4ms costly?
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

    for button, virtual_button in virtual_button_map.items():
        pressed = (physical.buttons[button] or external[button] > 0)

        if pressed:
            gamepad.press_button(virtual_button)
        else:
            gamepad.release_button(virtual_button)


    gamepad.left_joystick(physical.LX, physical.LY)
    gamepad.right_joystick(physical.RX, physical.RY)

    gamepad.left_trigger(255 if external[Trigger.LEFT] > 0 else physical.LT)
    gamepad.right_trigger(255 if external[Trigger.RIGHT] > 0 else physical.RT)

    gamepad.update()


cron_job = cron.interval("4ms", poll_controller)

# -----------------------------
# Talon actions
# -----------------------------

@mod.action_class
class Actions:

    def controller_button_down(button: Button | Trigger):
        """Press virtual controller button."""
        increment_external_state([button])

    def controller_button_up(button: Button | Trigger):
        """Release virtual controller button."""
        decrement_external_state([button])

    def controller_button_press(buttons: list[Button | Trigger]):
        """Press virtual controller buttons."""
        if buttons is None:
            return
        if not isinstance(buttons, list):
            buttons = [buttons]

        if buttons:
            increment_external_state(buttons)
            cron.after("30ms", lambda: decrement_external_state(buttons))


def increment_external_state(buttons):
    with external_state_lock:
        for button in buttons:
            external_state_counters[button] += 1

def decrement_external_state(buttons):
    with external_state_lock:
        for button in buttons:
            external_state_counters[button] = max(0, external_state_counters[button] - 1)

