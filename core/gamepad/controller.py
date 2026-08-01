import ctypes
from ctypes import Structure, c_ubyte, c_ushort, c_short, c_ulong, POINTER


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


XInputGetState = xinput.XInputGetState
XInputGetState.argtypes = [
    ctypes.c_uint,
    POINTER(XINPUT_STATE)
]
XInputGetState.restype = ctypes.c_uint


BUTTONS = {
    "DPAD_UP": 0x0001,
    "DPAD_DOWN": 0x0002,
    "DPAD_LEFT": 0x0004,
    "DPAD_RIGHT": 0x0008,
    "START": 0x0010,
    "BACK": 0x0020,
    "L3": 0x0040,
    "R3": 0x0080,
    "LB": 0x0100,
    "RB": 0x0200,
    "A": 0x1000,
    "B": 0x2000,
    "X": 0x4000,
    "Y": 0x8000,
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

        return {
            **{
                name: bool(gp.wButtons & mask) for name, mask in BUTTONS.items()
            },
            "LX": gp.sThumbLX,
            "LY": gp.sThumbLY,
            "RX": gp.sThumbRX,
            "RY": gp.sThumbRY,
            "LT": gp.bLeftTrigger,
            "RT": gp.bRightTrigger,
        }


# This is for finding which controller is active.
# TODO

def test_xinput():
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
