from talon import Module, cron
import threading
import vgamepad as vg

from .gamepad_types import Button, Trigger, Stick, GamepadState
from .xinput_controller import XInputController, StandardGamepadTranslator, DpadToStickTranslator


mod = Module()

# -----------------------------------------------------------------------------
# Physical controller(s)
# -----------------------------------------------------------------------------

# TODO need to have a way of calibrating the stick and saving that calibration somewhere
#      having to change them here manually is no bueno
standard_xbox_translator = StandardGamepadTranslator(
    centers={
        Stick.LX: -1351,
        Stick.LY: 0,
        Stick.RX: -2240,
        Stick.RY: -512,
    },
    apply_calibration=True,
)

xinput_xbox_controller = XInputController(0, standard_xbox_translator)
xinput_fight_stick = XInputController(2, DpadToStickTranslator())

# -----------------------------------------------------------------------------
# Virtual controller
# -----------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
# Inputs External from the physical controller
# Counters are used for buttons/triggers and values for sticks
# -----------------------------------------------------------------------------

external_state = GamepadState(
    buttons={button: 0 for button in Button},
    sticks={stick: 0 for stick in Stick},
    triggers={trigger: 0 for trigger in Trigger},
)

external_state_lock = threading.Lock()


# -----------------------------------------------------------------------------
# Poll Physical Controllers and XInput and update ViGEm 
# -----------------------------------------------------------------------------

last_state = None

def merge_states(states, external):
    if not states:
        return external

    buttons = {
        button: any(state.buttons[button] for state in states) or external.buttons[button] > 0
        for button in Button
    }

    sticks = {
        stick: (
            external.sticks[stick]
            if external.sticks[stick] != 0
            else max((state.sticks[stick] for state in states), key=abs, default=0)
        )
        for stick in Stick
    }

    triggers = {
        trigger: (
            external.triggers[trigger]
            if external.triggers[trigger] > 0
            else max(state.triggers[trigger] for state in states)
        )
        for trigger in Trigger
    }

    return GamepadState(
        buttons=buttons,
        sticks=sticks,
        triggers=triggers,
    )

def poll_controller():

    global last_state

    physical_states = []
    physical_states.append(xinput_xbox_controller.read())
    physical_states.append(xinput_fight_stick.read())

    with external_state_lock:
        external = GamepadState(
            buttons=external_state.buttons.copy(),
            sticks=external_state.sticks.copy(),
            triggers=external_state.triggers.copy(),
        )

    merged_state = merge_states(physical_states, external)

    if merged_state == last_state:
        return

    last_state = merged_state

    for button, virtual_button in virtual_button_map.items():
        if merged_state.buttons[button]:
            gamepad.press_button(virtual_button)
        else:
            gamepad.release_button(virtual_button)

    gamepad.left_joystick(merged_state.sticks[Stick.LX], merged_state.sticks[Stick.LY])
    gamepad.right_joystick(merged_state.sticks[Stick.RX], merged_state.sticks[Stick.RY])

    gamepad.left_trigger(merged_state.triggers[Trigger.LEFT])
    gamepad.right_trigger(merged_state.triggers[Trigger.RIGHT])

    gamepad.update()


cron_job = cron.interval("5ms", poll_controller)

# -----------------------------------------------------------------------------
# Talon actions
# -----------------------------------------------------------------------------

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
        x = max(Stick.min_value(), min(Stick.max_value(), x))
        y = max(Stick.min_value(), min(Stick.max_value(), y))

        with external_state_lock:
            external_state.sticks[Stick.LX] = x
            external_state.sticks[Stick.LY] = y

    def controller_left_stick_clear():
        """Return left stick control to the physical controller."""
        with external_state_lock:
            external_state.sticks[Stick.LX] = 0
            external_state.sticks[Stick.LY] = 0

def increment_external_state(buttons):
    with external_state_lock:
        for button in buttons:
            external_state.buttons[button] += 1

def decrement_external_state(buttons):
    with external_state_lock:
        for button in buttons:
            external_state.buttons[button] = max(0, external_state.buttons[button] - 1)
