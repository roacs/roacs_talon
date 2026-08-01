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

@dataclass
class AxisCalibration:
    center: int
    negative_scale: float
    positive_scale: float

XInputGetState = xinput.XInputGetState
XInputGetState.argtypes = [
    ctypes.c_uint,
    POINTER(XINPUT_STATE)
]
XInputGetState.restype = ctypes.c_uint


class XInputController:

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

    def __init__(self, index=0, apply_calibration=True):
        self.index = index
        self.apply_calibration = apply_calibration
        self.state = XINPUT_STATE()

        # Joystick center positions.
        # Modify with care; use print_controller_state() to find them.
        centers = {
            "LX": -1351,
            "LY": 0,
            "RX": -2240,
            "RY": -512,
        }

        self.calibrations = {
            axis: AxisCalibration(
                center=center,
                negative_scale=self.MIN_AXIS / (self.MIN_AXIS - center),
                positive_scale=self.MAX_AXIS / (self.MAX_AXIS - center),
            )
            for axis, center in centers.items()
        }

    def calibrate(self, value, calibration):
        if self.apply_calibration:
            offset = value - calibration.center

            if offset >= 0:
                value = int(offset * calibration.positive_scale)
            else:
                value = int(offset * calibration.negative_scale)

        return max(self.MIN_AXIS, min(self.MAX_AXIS, value))

    def read(self):
        result = XInputGetState(self.index, ctypes.byref(self.state))
        if result != 0:
            return None

        gp = self.state.Gamepad

        axes = {
            axis: self.calibrate(getattr(gp, field), self.calibrations[axis])
            for axis, field in self.AXIS_FIELDS.items()
        }

        return ControllerState(
            buttons={
                button: bool(gp.wButtons & mask) for button, mask in self.BUTTON_MASKS.items()
            },
            **axes,
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
                "RX=", gp.sThumbRX,
                "RY=", gp.sThumbRY,
            )
        else:
            print(f"Controller {i}: not connected")
