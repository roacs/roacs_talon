import ctypes
from ctypes import Structure, c_ubyte, c_ushort, c_short, c_ulong, POINTER
from dataclasses import dataclass
from .xinput_buttons import Button


for dll in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
    try:
        xinput = ctypes.WinDLL(dll)
        break
    except OSError:
        continue
else:
    raise RuntimeError("Could not load XInput")


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


@dataclass
class ControllerState:
    buttons: dict[Button, bool]
    LX: int = 0
    LY: int = 0
    RX: int = 0
    RY: int = 0
    LT: int = 0
    RT: int = 0

XInputGetState = xinput.XInputGetState
XInputGetState.argtypes = [
    ctypes.c_uint,
    POINTER(XINPUT_STATE)
]
XInputGetState.restype = ctypes.c_uint

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

class XInputController:

    def __init__(self, index=0):
        self.index = index
        self.state = XINPUT_STATE()

    def read(self):
        result = XInputGetState(self.index, ctypes.byref(self.state))
        if result != 0:
            return None

        gp = self.state.Gamepad

        return ControllerState(
            buttons={
                button: bool(gp.wButtons & mask) for button, mask in BUTTON_MASKS.items()
            },
            LX=gp.sThumbLX,
            LY=gp.sThumbLY,
            RX=gp.sThumbRX,
            RY=gp.sThumbRY,
            LT=gp.bLeftTrigger,
            RT=gp.bRightTrigger,
        )


# This is for finding which controller is active.
def print_controller_state():
    for i in range(4):
        state = XINPUT_STATE()
        result = XInputGetState(i, ctypes.byref(state))

        if result == 0:
            gp = state.Gamepad
            print(
                f"Controller {i}:",
                "buttons=", hex(gp.wButtons),
                "LT=", gp.bLeftTrigger,
                "RT=", gp.bRightTrigger,
                "LX=", gp.sThumbLX,
                "LY=", gp.sThumbLY,
            )
        else:
            print(f"Controller {i}: not connected")
