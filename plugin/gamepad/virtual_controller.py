from talon import Module, cron
import threading
import vgamepad as vg

from .xinput_buttons import Button, Trigger, Axis
from .xinput_controller import XInputController, ControllerState


mod = Module()

# -----------------------------
# Physical controller(s)
# -----------------------------

controller = XInputController(indices=[1,3])

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
# Counters are used for buttons/triggers and values for sticks
# -----------------------------

external_state = {
    **{item: 0 for item in list(Button) + list(Trigger)},
    Axis.LX: None,
    Axis.LY: None
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

    if physical is None:
        return

    with external_state_lock:
        external = external_state.copy()

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


    lx = physical.LX if external[Axis.LX] is None else external[Axis.LX]
    ly = physical.LY if external[Axis.LY] is None else external[Axis.LY]
    gamepad.left_joystick(lx, ly)
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

    def controller_left_stick(x: int, y: int):
        """Move the left analog stick. Physical input disabled until controller_left_stick_clear called."""
        x = max(-32768, min(32767, x))
        y = max(-32768, min(32767, y))

        with external_state_lock:
            external_state[Axis.LX] = x
            external_state[Axis.LY] = y

    def controller_left_stick_clear():
        """Return left stick control to the physical controller."""
        with external_state_lock:
            external_state[Axis.LX] = None
            external_state[Axis.LY] = None


def increment_external_state(buttons):
    with external_state_lock:
        for button in buttons:
            external_state[button] += 1

def decrement_external_state(buttons):
    with external_state_lock:
        for button in buttons:
            external_state[button] = max(0, external_state[button] - 1)

