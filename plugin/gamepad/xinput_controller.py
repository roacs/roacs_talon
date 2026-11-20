import ctypes
from ctypes import Structure, c_ubyte, c_ushort, c_short, c_ulong, POINTER
from .gamepad_types import Button, Stick, Trigger, GamepadState


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
# XInput Controller
# ---------------------------------------------

class XInputController:

    def __init__(self, index):
        self.index = index
        self.state = XINPUT_STATE()

    def get_gamepad_state(self):
        """Return the current GamepadState, or None if the controller is not connected."""
        result = XInputGetState(self.index, ctypes.byref(self.state))

        if result != ERROR_SUCCESS:
            return None

        gamepad = self.state.Gamepad

        return GamepadState(
            buttons={
                button: bool(gamepad.wButtons & mask)
                for button, mask in BUTTON_MASKS.items()
            },
            sticks={
                axis: getattr(gamepad, field)
                for axis, field in STICK_AXES.items()
            },
            triggers={
                Trigger.LEFT: gamepad.bLeftTrigger,
                Trigger.RIGHT: gamepad.bRightTrigger,
            },
        )


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
