import ctypes
from ctypes import Structure, c_ubyte, c_ushort, c_short, c_ulong, POINTER
from typing import Protocol
from .gamepad_types import Button, Stick, Trigger, GamepadState, StickCalibration


# ---------------------------------------------
# Load XInput
# ---------------------------------------------

for dll in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
    try:
        xinput = ctypes.WinDLL(dll)
        break
    except OSError:
        continue
else:
    raise RuntimeError("Could not load XInput")

# ---------------------------------------------
# XInput Structures
# ---------------------------------------------

class XINPUT_GAMEPAD(Structure):
    _fields_ = [
        ("wButtons", c_ushort),
        ("bLeftTrigger", c_ubyte),
        ("bRightTrigger", c_ubyte),
        ("sThumbLX", c_short),
        ("sThumbLY", c_short),
        ("sThumbRX", c_short),
        ("sThumbRY", c_short),
    ]

class XINPUT_STATE(Structure):
    _fields_ = [
        ("dwPacketNumber", c_ulong),
        ("Gamepad", XINPUT_GAMEPAD),
    ]

class XINPUT_VIBRATION(Structure):
    _fields_ = [
        ("wLeftMotorSpeed", c_ushort),
        ("wRightMotorSpeed", c_ushort),
    ]

class XINPUT_CAPABILITIES(Structure):
    _fields_ = [
        ("Type", c_ubyte),
        ("SubType", c_ubyte),
        ("Flags", c_ushort),
        ("Gamepad", XINPUT_GAMEPAD),
        ("Vibration", XINPUT_VIBRATION),
    ]

XInputGetState = xinput.XInputGetState
XInputGetState.argtypes = [
    ctypes.c_uint,
    POINTER(XINPUT_STATE)
]
XInputGetState.restype = ctypes.c_uint

XInputGetCapabilities = xinput.XInputGetCapabilities
XInputGetCapabilities.argtypes = [
    ctypes.c_uint,
    ctypes.c_uint,
    POINTER(XINPUT_CAPABILITIES),
]

XInputGetCapabilities.restype = ctypes.c_uint

# ---------------------------------------------
# XInput Constants
# ---------------------------------------------

ERROR_SUCCESS = 0

XINPUT_FLAG_GAMEPAD = 0x00000001

# ---------------------------------------------
# XInput Maps
# ---------------------------------------------

STICK_AXES = {
    Stick.LX: "sThumbLX",
    Stick.LY: "sThumbLY",
    Stick.RX: "sThumbRX",
    Stick.RY: "sThumbRY",
}

BUTTON_MASKS = {
    Button.DPAD_UP: 0x0001,
    Button.DPAD_DOWN: 0x0002,
    Button.DPAD_LEFT: 0x0004,
    Button.DPAD_RIGHT: 0x0008,
    Button.START: 0x0010,
    Button.BACK: 0x0020,
    Button.L3: 0x0040,
    Button.R3: 0x0080,
    Button.LB: 0x0100,
    Button.RB: 0x0200,
    Button.A: 0x1000,
    Button.B: 0x2000,
    Button.X: 0x4000,
    Button.Y: 0x8000,
}


SUBTYPE_NAMES = {
    0x00: "Unknown",
    0x01: "Gamepad",
    0x02: "Wheel",
    0x03: "Arcade Stick",
    0x04: "Flight Stick",
    0x05: "Dance Pad",
    0x06: "Guitar",
    0x07: "Guitar Alternate",
    0x08: "Drum Kit",
    0x0B: "Guitar Bass",
}

# ---------------------------------------------
# Translator Interface
# ---------------------------------------------

class GamepadTranslator(Protocol):

    def translate(self, gamepad: XINPUT_GAMEPAD) -> GamepadState:
        ...

# ---------------------------------------------
# Standard Gamepad Translator
# ---------------------------------------------

class StandardGamepadTranslator:

    def __init__(self, centers=None, apply_calibration=False):
        if centers is None:
            centers = {
                Stick.LX: 0,
                Stick.LY: 0,
                Stick.RX: 0,
                Stick.RY: 0,
            }

        self.apply_calibration = apply_calibration

        self.calibrations = {
            axis: StickCalibration(
                center=centers.get(axis, 0),
                negative_scale=Stick.min_value() / (Stick.min_value() - centers.get(axis, 0)),
                positive_scale=Stick.max_value() / (Stick.max_value() - centers.get(axis, 0)),
            )
            for axis in STICK_AXES
        }

    def calibrate(self, value, calibration):
        if self.apply_calibration:
            offset = value - calibration.center

            if offset >= 0:
                value = int(offset * calibration.positive_scale)
            else:
                value = int(offset * calibration.negative_scale)

        return max(Stick.min_value(), min(Stick.max_value(), value))

    def translate(self, gamepad):
        buttons = {
            button: bool(gamepad.wButtons & mask) for button, mask in BUTTON_MASKS.items()
        }

        sticks = {
            axis: self.calibrate(getattr(gamepad, field), self.calibrations[axis])
            for axis, field in STICK_AXES.items()
        }

        triggers = {
            Trigger.LEFT: gamepad.bLeftTrigger,
            Trigger.RIGHT: gamepad.bRightTrigger,
        }

        return GamepadState(
            buttons=buttons,
            sticks=sticks,
            triggers=triggers,
        )


# ---------------------------------------------
# Dpad As Analog Stick Translator (because fight stick joystick is a dpad)
# ---------------------------------------------

class DpadToStickTranslator(StandardGamepadTranslator):

    def translate(self, gamepad):
        state = super().translate(gamepad)

        if gamepad.wButtons & BUTTON_MASKS[Button.DPAD_LEFT]:
            state.sticks[Stick.LX] = Stick.min_value()
        elif gamepad.wButtons & BUTTON_MASKS[Button.DPAD_RIGHT]:
            state.sticks[Stick.LX] = Stick.max_value()

        if gamepad.wButtons & BUTTON_MASKS[Button.DPAD_UP]:
            state.sticks[Stick.LY] = Stick.max_value()
        elif gamepad.wButtons & BUTTON_MASKS[Button.DPAD_DOWN]:
            state.sticks[Stick.LY] = Stick.min_value()

        state.buttons[Button.DPAD_UP] = False
        state.buttons[Button.DPAD_DOWN] = False
        state.buttons[Button.DPAD_LEFT] = False
        state.buttons[Button.DPAD_RIGHT] = False

        return state

# ---------------------------------------------
# XInput Controller
# ---------------------------------------------

class XInputController:

    def __init__(self, index, translator):
        self.index = index
        self.translator = translator
        self.state = XINPUT_STATE()

    def read(self):
        result = XInputGetState(self.index, ctypes.byref(self.state))

        if result != ERROR_SUCCESS:
            return None

        return self.translator.translate(self.state.Gamepad)


# ---------------------------------------------
# Support/Debug Functions
# ---------------------------------------------

def print_xinput_controllers():
    """Print capabilities and current state for all XInput controllers."""
    for i in range(4):
        capabilities = XINPUT_CAPABILITIES()
        capabilities_result = XInputGetCapabilities(i, XINPUT_FLAG_GAMEPAD, ctypes.byref(capabilities))

        state = XINPUT_STATE()
        state_result = XInputGetState(i, ctypes.byref(state))

        if (capabilities_result != ERROR_SUCCESS and state_result != ERROR_SUCCESS):
            print(f"Controller {i}: not connected")
            print()
            continue

        print(f"Controller {i}:")
        if capabilities_result == ERROR_SUCCESS:
            subtype = SUBTYPE_NAMES.get(capabilities.SubType, f"Unknown (0x{capabilities.SubType:02X})")

            print(f"  Type:       0x{capabilities.Type:02X}")
            print(f"  SubType:    0x{capabilities.SubType:02X} ({subtype})")
            print(f"  Flags:      0x{capabilities.Flags:04X}")
        else:
            print("  Capabilities: unavailable")

        if state_result == ERROR_SUCCESS:
            gp = state.Gamepad

            print("  Current State:")
            print(f"    Buttons:  0x{gp.wButtons:04X}")
            print(f"    LT:       {gp.bLeftTrigger}")
            print(f"    RT:       {gp.bRightTrigger}")
            print(f"    LX:       {gp.sThumbLX}")
            print(f"    LY:       {gp.sThumbLY}")
            print(f"    RX:       {gp.sThumbRX}")
            print(f"    RY:       {gp.sThumbRY}")
        else:
            print("  Current State: unavailable")

        print()
