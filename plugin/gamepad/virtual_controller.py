from talon import Module, cron
import threading
import vgamepad as vg

from .gamepad_types import Button, Trigger, Stick, GamepadState
from .gameinput_controller import GameInputController
from .xinput_controller import XInputController, StandardGamepadTranslator, DpadToStickTranslator
from .joycon_hid_controller import JoyCon, get_device_ids


mod = Module()

# -----------------------------------------------------------------------------
# GameInput controller(s)
# -----------------------------------------------------------------------------

_gameinputs = []

KNOWN_DEVICES = {
    "razer_wolverine_ultimate": (0x1532, 0x0a14),
    "mad_catz_sfiv_fightstick": (0x0738, 0x4718),
}

_gameinputs.append(GameInputController(KNOWN_DEVICES["razer_wolverine_ultimate"]))

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# XInput controller(s)
# -----------------------------------------------------------------------------

_xinputs = []

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

#_xinputs.append(XInputController(1, standard_xbox_translator))
#_xinputs.append(XInputController(2, DpadToStickTranslator()))

# -----------------------------------------------------------------------------
# Joy-Con controller(s)
# -----------------------------------------------------------------------------

_joycons = {}

def check_connection():
    """Look for new Joy-Cons and connect them."""
    for vendor_id, product_id, serial in get_device_ids():
        if vendor_id is not None and serial not in _joycons:
            try:
                joycon = JoyCon(vendor_id, product_id, serial)
                _joycons[serial] = joycon
                print(f"joycon [{serial}]: connected")

            except Exception as e:
                print(f"joycon [{serial}]: failed to connect: {e}")

# TODO uncomment to use joycon
#connection_job = cron.interval("2s", check_connection)

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
# Poll Controllers and update ViGEm 
# -----------------------------------------------------------------------------

last_state = None

def merge_states(states, external):
    states = [state for state in states if state is not None]
    if not states:
        return external

    buttons = {
        button: any(state.buttons.get(button, False) for state in states) or external.buttons[button] > 0
        for button in Button
    }

    sticks = {
        stick: (
            external.sticks[stick]
            if external.sticks[stick] != 0
            else max((state.sticks.get(stick, 0) for state in states), key=abs, default=0)
        )
        for stick in Stick
    }

    triggers = {
        trigger: (
            external.triggers[trigger]
            if external.triggers[trigger] > 0
            else max((state.triggers.get(trigger, 0) for state in states), default=0)
        )
        for trigger in Trigger
    }

    return GamepadState(buttons=buttons, sticks=sticks, triggers=triggers)

def poll_controller():

    global last_state
    global _gameinputs, _xinputs, _joycons

    physical_states = []
    disconnected = []

    for gameinput in _gameinputs:
        physical_states.append(gameinput.get_gamepad_state())
    for xinput in _xinputs:
        physical_states.append(xinput.read())
    for serial, joycon in list(_joycons.items()):
        physical_states.append(joycon.get_gamepad_state())

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


poll_job = cron.interval("4ms", poll_controller)

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
