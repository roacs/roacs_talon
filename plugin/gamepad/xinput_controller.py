import ctypes
from ctypes import Structure, c_ubyte, c_ushort, c_short, c_ulong, POINTER
from dataclasses import dataclass
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
# Maps and Constants
# ---------------------------------------------

ERROR_SUCCESS = 0

MIN_AXIS = -32768
MAX_AXIS = 32767

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

XINPUT_FLAG_GAMEPAD = 0x00000001
XINPUT_DEVTYPE_GAMEPAD = 0x01

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
# XInput Controller
# ---------------------------------------------

class XInputController:

    def __init__(self, indices=(0,), centers=None, apply_calibration=False):
        self.indices = list(indices)
        self.apply_calibration = apply_calibration
        self.states = {index: XINPUT_STATE() for index in self.indices}

        if centers is None:
            centers = {
                index: {"LX": 0, "LY": 0, "RX": 0, "RY": 0}
                for index in self.indices
            }

        # TODO need to have a way of calibrating the stick and saving that calibration
        # somewhere
        ## Joystick center positions.
        ## Modify with care; use print_xinput_controllers() to find them.
        #centers = {
        #    "LX": -1351,
        #    "LY": 0,
        #    "RX": -2240,
        #    "RY": -512,
        #}

        self.calibrations = {}

        for index in self.indices:
            index_centers = centers.get(index, {})

            self.calibrations[index] = {
                axis: AxisCalibration(
                    center=index_centers.get(axis, 0),
                    negative_scale=MIN_AXIS / (MIN_AXIS - index_centers.get(axis, 0)),
                    positive_scale=MAX_AXIS / (MAX_AXIS - index_centers.get(axis, 0)),
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

    @staticmethod
    def merge_axis(values):
        """Return the value with the greatest magnitude."""
        return max(values, key=abs, default=0)

    def read(self):
        gamepads = []

        for index in self.indices:
            state = self.states[index]
            result = XInputGetState(index, ctypes.byref(state))

            if result != ERROR_SUCCESS:
                continue

            gp = state.Gamepad

            axes = {
                axis: self.calibrate(getattr(gp, field), self.calibrations[index][axis])
                for axis, field in AXIS_FIELDS.items()
            }

            gamepads.append({"gamepad": gp, "axes": axes})

        if not gamepads:
            return None

        buttons = {
            button: any(item["gamepad"].wButtons & mask for item in gamepads)
            for button, mask in BUTTON_MASKS.items()
        }

        axes = {
            axis: self.merge_axis([item["axes"][axis] for item in gamepads])
            for axis in AXIS_FIELDS
        }

        LT = max(item["gamepad"].bLeftTrigger for item in gamepads)
        RT = max(item["gamepad"].bRightTrigger for item in gamepads)

        return ControllerState(buttons=buttons, **axes, LT=LT, RT=RT)


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
