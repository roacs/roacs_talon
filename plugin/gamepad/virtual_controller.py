from talon import Module, cron
import vgamepad as vg

from .gamepad_types import Button, Trigger, Stick, GamepadState, ExternalInput
from .gamepad_translator import GamepadTranslator, CalibrateSticks, Remap, LX_NEG, LX_POS, LY_NEG, LY_POS
from .gameinput_controller import GameInputController
from .xinput_controller import XInputController
from .joycon_hid_controller import JoyCon, get_device_ids


mod = Module()

# -----------------------------------------------------------------------------
# Controller(s)
# -----------------------------------------------------------------------------

_controllers = []

def add_controller(device, calibration=None, remap=None):
    translator = None
    if calibration is not None or remap is not None:
        translator = GamepadTranslator(calibration=calibration, remap=remap)
    _controllers.append((device, translator))

KNOWN_DEVICES = {
    "razer_wolverine_ultimate": (0x1532, 0x0a14),
    "mad_catz_sfiv_fightstick": (0x0738, 0x4718),
    "navigation_controller_dshidmini": (0x045e, 0x02ff),
}

razer_stick_calibration = CalibrateSticks({
    Stick.LX: -1351, Stick.LY: 0, Stick.RX: -2240, Stick.RY: -512,
})

dpad_to_left_stick = Remap({
    Button.DPAD_LEFT: LX_NEG, Button.DPAD_RIGHT: LX_POS,
    Button.DPAD_UP: LY_POS,   Button.DPAD_DOWN: LY_NEG,
})

add_controller(GameInputController(KNOWN_DEVICES["razer_wolverine_ultimate"]),
    calibration=razer_stick_calibration,
)
add_controller(GameInputController(KNOWN_DEVICES["navigation_controller_dshidmini"]),
    remap=Remap({Button.A: Button.BACK}),
)

#add_controller(XInputController(1),
#    calibration=razer_stick_calibration,
#)
#add_controller(XInputController(2),
#    remap=dpad_to_left_stick,
#)

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
# Inputs external to the physical controllers
# -----------------------------------------------------------------------------

external_input = ExternalInput()

# -----------------------------------------------------------------------------
# Poll Controllers and update ViGEm 
# -----------------------------------------------------------------------------

last_state = None

def merge_states(physical_states, external):
    """
    Combine physical controller states with the external state into one full GamepadState.
    """
    states = [state for state in physical_states if state is not None]

    buttons = {
        button: any(state.buttons.get(button, False) for state in states)
                or external.buttons.get(button, False)
        for button in Button
    }

    sticks = {}
    for stick in Stick:
        external_value = external.sticks.get(stick, 0)
        if external_value != 0:
            sticks[stick] = external_value
        else:
            sticks[stick] = max(
                (state.sticks.get(stick, 0) for state in states), key=abs, default=0
            )

    triggers = {
        trigger: max(
            [external.triggers.get(trigger, 0)]
            + [state.triggers.get(trigger, 0) for state in states]
        )
        for trigger in Trigger
    }

    return GamepadState(buttons=buttons, sticks=sticks, triggers=triggers)

def poll_controller():
    """
    Poll physical controllers and merge with external input.  Update virtual controller.
    """
    global last_state
    global _controllers, _joycons

    physical_states = []

    for device, translator in _controllers:
        state = device.get_gamepad_state()
        if state is not None and translator is not None:
            state = translator(state)
        physical_states.append(state)

    for serial, joycon in list(_joycons.items()):
        physical_states.append(joycon.get_gamepad_state())

    merged_state = merge_states(physical_states, external_input.to_gamepad_state())

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
        external_input.press([button])

    def controller_button_up(button: Button | Trigger):
        """Release virtual controller button."""
        external_input.release([button])

    def controller_button_press(buttons: list[Button | Trigger]):
        """Press virtual controller buttons."""
        if buttons is None:
            return
        if not isinstance(buttons, list):
            buttons = [buttons]

        if buttons:
            external_input.press(buttons)
            cron.after("30ms", lambda: external_input.release(buttons))

    def controller_left_stick(x: int, y: int):
        """Move the left analog stick. Physical input disabled until controller_left_stick_clear called."""
        external_input.set_stick(Stick.LX, Stick.LY, x, y)

    def controller_left_stick_clear():
        """Return left stick control to the physical controller."""
        external_input.clear_stick(Stick.LX, Stick.LY)
