import ctypes
from ctypes import Structure, c_ubyte, c_ushort, c_short, c_ulong, POINTER
from dataclasses import dataclass
from typing import Protocol
from .xinput_buttons import Button


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

MIN_AXIS = -32768
MAX_AXIS = 32767

XINPUT_FLAG_GAMEPAD = 0x00000001

# ---------------------------------------------
# XInput Maps
# ---------------------------------------------

AXIS_FIELDS = {
    "LX": "sThumbLX",
    "LY": "sThumbLY",
    "RX": "sThumbRX",
    "RY": "sThumbRY",
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
# State
# ---------------------------------------------

@dataclass
class ControllerState:
    buttons: dict[Button, bool]
    LX: int = 0
    LY: int = 0
    RX: int = 0
    RY: int = 0
    LT: int = 0
    RT: int = 0

@dataclass
class AxisCalibration:
    center: int
    negative_scale: float
    positive_scale: float

# ---------------------------------------------
# Translator Interface
# ---------------------------------------------

class GamepadTranslator(Protocol):

    def translate(self, gamepad: XINPUT_GAMEPAD) -> ControllerState:
        ...

# ---------------------------------------------
# Standard Gamepad Translator
# ---------------------------------------------

class StandardGamepadTranslator:

    def __init__(self, centers=None, apply_calibration=False):
        if centers is None:
            centers = {
                "LX": 0,
                "LY": 0,
                "RX": 0,
                "RY": 0,
            }

        self.apply_calibration = apply_calibration

        self.calibrations = {
            axis: AxisCalibration(
                center=centers.get(axis, 0),
                negative_scale=MIN_AXIS / (MIN_AXIS - centers.get(axis, 0)),
                positive_scale=MAX_AXIS / (MAX_AXIS - centers.get(axis, 0)),
            )
            for axis in AXIS_FIELDS
        }

    def calibrate(self, value, calibration):
        if self.apply_calibration:
            offset = value - calibration.center

            if offset >= 0:
                value = int(offset * calibration.positive_scale)
            else:
                value = int(offset * calibration.negative_scale)

        return max(MIN_AXIS, min(MAX_AXIS, value))

    def translate(self, gamepad):
        buttons = {
            button: bool(gamepad.wButtons & mask) for button, mask in BUTTON_MASKS.items()
        }

        axes = {
            axis: self.calibrate(getattr(gamepad, field), self.calibrations[axis])
            for axis, field in AXIS_FIELDS.items()
        }

        return ControllerState(
            buttons=buttons,
            **axes,
            LT=gamepad.bLeftTrigger,
            RT=gamepad.bRightTrigger,
        )


# ---------------------------------------------
# Dpad As Analog Stick Translator (because fight stick joystick is a dpad)
# ---------------------------------------------

class DpadToStickTranslator(StandardGamepadTranslator):

    def translate(self, gamepad):
        state = super().translate(gamepad)

        if gamepad.wButtons & BUTTON_MASKS[Button.DPAD_LEFT]:
            state.LX = MIN_AXIS
        elif gamepad.wButtons & BUTTON_MASKS[Button.DPAD_RIGHT]:
            state.LX = MAX_AXIS

        if gamepad.wButtons & BUTTON_MASKS[Button.DPAD_UP]:
            state.LY = MAX_AXIS
        elif gamepad.wButtons & BUTTON_MASKS[Button.DPAD_DOWN]:
            state.LY = MIN_AXIS

        state.buttons[Button.DPAD_UP] = False
        state.buttons[Button.DPAD_DOWN] = False
        state.buttons[Button.DPAD_LEFT] = False
        state.buttons[Button.DPAD_RIGHT] = False

        return state

# ---------------------------------------------
# XInput Controller
# ---------------------------------------------

class XInputController:

    def __init__(self, translators):
        self.translators = dict(translators)
        self.indices = list(self.translators)
        self.states = {index: XINPUT_STATE() for index in self.indices}

    @staticmethod
    def merge_axis(values):
        """Return the value with the greatest magnitude."""
        return max(values, key=abs, default=0)

    @classmethod
    def merge_states(cls, states):
        if not states:
            return None

        buttons = {
            button: any(state.buttons[button] for state in states) for button in BUTTON_MASKS
        }

        axes = {
            axis: cls.merge_axis([getattr(state, axis) for state in states]) for axis in AXIS_FIELDS
        }

        LT = max(state.LT for state in states)
        RT = max(state.RT for state in states)

        return ControllerState(buttons=buttons, **axes, LT=LT, RT=RT)

    def read(self):
        translated_states = []

        for index in self.indices:
            state = self.states[index]
            result = XInputGetState(index, ctypes.byref(state))

            if result != ERROR_SUCCESS:
                continue

            gamepad = state.Gamepad
            translator = self.translators[index]

            translated_states.append(translator.translate(gamepad))

        return self.merge_states(translated_states)


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
