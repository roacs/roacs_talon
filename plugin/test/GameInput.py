"""
GameInput.py

A ctypes wrapper around Microsoft's GameInput.h (API version 3 / the
GameInputRedist.dll redistributable). This module only defines the
constants, enums, structures, GUIDs, callback types, and COM plumbing
that mirror the header -- it has no enumeration or polling logic of its
own. See gameinput_controller.py for that.

Enums are real Python enum.IntEnum / enum.IntFlag classes so they can be
used like:

    GameInput.GameInputKind.Gamepad
    GameInput.GameInputDeviceStatus.Connected

rather than bare integer constants.
"""

import ctypes
from ctypes import (
    POINTER,
    Structure,
    Union,
    c_bool,
    c_char_p,
    c_float,
    c_int32,
    c_uint8,
    c_uint16,
    c_uint32,
    c_uint64,
    c_void_p,
    c_wchar,
    c_long,
    c_size_t,
)
from enum import IntEnum, IntFlag


# ============================================================================
# DLL location
#
# The in-box System32\GameInput.dll is a frozen, very old (v0) build and
# cannot be updated. The redistributable installs its own, differently
# named DLL alongside it -- load that one explicitly.
# ============================================================================

GAMEINPUT_REDIST_PATH = r"C:\Program Files\Microsoft GameInput\x64\GameInputRedist.dll"


# ============================================================================
# GUID / APP_LOCAL_DEVICE_ID
# ============================================================================

class GUID(Structure):
    _fields_ = [
        ("Data1", c_uint32),
        ("Data2", c_uint16),
        ("Data3", c_uint16),
        ("Data4", c_uint8 * 8),
    ]

    def __repr__(self):
        d4 = "".join(f"{b:02X}" for b in self.Data4)
        return f"{{{self.Data1:08X}-{self.Data2:04X}-{self.Data3:04X}-{d4[:4]}-{d4[4:]}}}"


def _guid(data1, data2, data3, *data4_bytes):
    return GUID(data1, data2, data3, (c_uint8 * 8)(*data4_bytes))


class APP_LOCAL_DEVICE_ID(Structure):
    _fields_ = [("value", c_uint8 * 32)]


# ============================================================================
# Interface IIDs
# ============================================================================

IID_IGameInput = _guid(0x20EFC1C7, 0x5D9A, 0x43BA, 0xB2, 0x6F, 0xB8, 0x07, 0xFA, 0x48, 0x60, 0x9C)
IID_IGameInputRawDeviceReport = _guid(0x05A42D89, 0x2CB6, 0x45A3, 0x87, 0x4D, 0xE6, 0x35, 0x72, 0x35, 0x87, 0xAB)
IID_IGameInputReading = _guid(0xC81C4CDE, 0xED1A, 0x4631, 0xA3, 0x0F, 0xC5, 0x56, 0xA6, 0x24, 0x1A, 0x1F)
IID_IGameInputDevice = _guid(0x63E2F38B, 0xA399, 0x4275, 0x8A, 0xE7, 0xD4, 0xC6, 0xE5, 0x24, 0xD1, 0x2A)
IID_IGameInputDispatcher = _guid(0x415EED2E, 0x98CB, 0x42C2, 0x8F, 0x28, 0xB9, 0x46, 0x01, 0x07, 0x4E, 0x31)
IID_IGameInputForceFeedbackEffect = _guid(0xFF61096A, 0x3373, 0x4093, 0xA1, 0xDF, 0x6D, 0x31, 0x84, 0x6B, 0x35, 0x11)
IID_IGameInputMapper = _guid(0x3C600700, 0xF16C, 0x49CE, 0x9B, 0xE6, 0x6A, 0x2E, 0xF7, 0x52, 0xED, 0x5E)


# ============================================================================
# Enums
#
# IntFlag is used for every enum the header marks with
# DEFINE_ENUM_FLAG_OPERATORS (bitwise-combinable); plain IntEnum otherwise.
# ============================================================================

class GameInputKind(IntFlag):
    Unknown = 0x00000000
    RawDeviceReport = 0x00000001
    ControllerAxis = 0x00000002
    ControllerButton = 0x00000004
    ControllerSwitch = 0x00000008
    Controller = 0x0000000E
    Keyboard = 0x00000010
    Mouse = 0x00000020
    Sensors = 0x00000040
    ArcadeStick = 0x00010000
    FlightStick = 0x00020000
    Gamepad = 0x00040000
    RacingWheel = 0x00080000


class GameInputEnumerationKind(IntEnum):
    NoEnumeration = 0
    AsyncEnumeration = 1
    BlockingEnumeration = 2


class GameInputFocusPolicy(IntFlag):
    Default = 0x00000000
    ExclusiveForegroundInput = 0x00000002
    ExclusiveForegroundGuideButton = 0x00000008
    ExclusiveForegroundShareButton = 0x00000020
    EnableBackgroundInput = 0x00000040
    EnableBackgroundGuideButton = 0x00000080
    EnableBackgroundShareButton = 0x00000100


class GameInputSwitchKind(IntEnum):
    Unknown = -1
    TwoWay = 0
    FourWay = 1
    EightWay = 2


class GameInputSwitchPosition(IntEnum):
    Center = 0
    Up = 1
    UpRight = 2
    Right = 3
    DownRight = 4
    Down = 5
    DownLeft = 6
    Left = 7
    UpLeft = 8


class GameInputKeyboardKind(IntEnum):
    Unknown = -1
    Ansi = 0
    Iso = 1
    Ks = 2
    Abnt = 3
    Jis = 4


class GameInputMouseButtons(IntFlag):
    NoneFlag = 0x00000000
    LeftButton = 0x00000001
    RightButton = 0x00000002
    MiddleButton = 0x00000004
    Button4 = 0x00000008
    Button5 = 0x00000010
    WheelTiltLeft = 0x00000020
    WheelTiltRight = 0x00000040


class GameInputMousePositions(IntFlag):
    NoPosition = 0x00000000
    AbsolutePosition = 0x00000001
    RelativePosition = 0x00000002


class GameInputSensorsKind(IntFlag):
    NoneFlag = 0x00000000
    Accelerometer = 0x00000001
    Gyrometer = 0x00000002
    Compass = 0x00000004
    Orientation = 0x00000008


class GameInputSensorAccuracy(IntEnum):
    Unknown = 0x00000000
    Unreliable = 0x00000001
    Approximate = 0x00000002
    High = 0x00000003


class GameInputArcadeStickButtons(IntFlag):
    NoneFlag = 0x00000000
    Menu = 0x00000001
    View = 0x00000002
    Up = 0x00000004
    Down = 0x00000008
    Left = 0x00000010
    Right = 0x00000020
    Action1 = 0x00000040
    Action2 = 0x00000080
    Action3 = 0x00000100
    Action4 = 0x00000200
    Action5 = 0x00000400
    Action6 = 0x00000800
    Special1 = 0x00001000
    Special2 = 0x00002000


class GameInputFlightStickButtons(IntFlag):
    NoneFlag = 0x00000000
    Menu = 0x00000001
    View = 0x00000002
    FirePrimary = 0x00000004
    FireSecondary = 0x00000008
    HatSwitchUp = 0x00000010
    HatSwitchDown = 0x00000020
    HatSwitchLeft = 0x00000040
    HatSwitchRight = 0x00000080
    A = 0x00000100
    B = 0x00000200
    X = 0x00000400
    Y = 0x00000800
    LeftShoulder = 0x00001000
    RightShoulder = 0x00002000


class GameInputGamepadButtons(IntFlag):
    NoneFlag = 0x00000000
    Menu = 0x00000001
    View = 0x00000002
    A = 0x00000004
    B = 0x00000008
    C = 0x00004000
    X = 0x00000010
    Y = 0x00000020
    Z = 0x00008000
    DPadUp = 0x00000040
    DPadDown = 0x00000080
    DPadLeft = 0x00000100
    DPadRight = 0x00000200
    LeftShoulder = 0x00000400
    RightShoulder = 0x00000800
    LeftTriggerButton = 0x00010000
    RightTriggerButton = 0x00020000
    LeftThumbstick = 0x00001000
    LeftThumbstickUp = 0x00040000
    LeftThumbstickDown = 0x00080000
    LeftThumbstickLeft = 0x00100000
    LeftThumbstickRight = 0x00200000
    RightThumbstick = 0x00002000
    RightThumbstickUp = 0x00400000
    RightThumbstickDown = 0x00800000
    RightThumbstickLeft = 0x01000000
    RightThumbstickRight = 0x02000000
    PaddleLeft1 = 0x04000000
    PaddleLeft2 = 0x08000000
    PaddleRight1 = 0x10000000
    PaddleRight2 = 0x20000000


class GameInputRawDeviceReportKind(IntEnum):
    Input = 0
    Output = 1


class GameInputRacingWheelButtons(IntFlag):
    NoneFlag = 0x00000000
    Menu = 0x00000001
    View = 0x00000002
    PreviousGear = 0x00000004
    NextGear = 0x00000008
    A = 0x00000100
    B = 0x00000200
    X = 0x00000400
    Y = 0x00000800
    DpadUp = 0x00000010
    DpadDown = 0x00000020
    DpadLeft = 0x00000040
    DpadRight = 0x00000080
    LeftThumbstick = 0x00001000
    RightThumbstick = 0x00002000


class GameInputSystemButtons(IntFlag):
    NoneFlag = 0x00000000
    Guide = 0x00000001
    Share = 0x00000002


class GameInputFlightStickAxes(IntFlag):
    NoneFlag = 0x00000000
    Roll = 0x00000010
    Pitch = 0x00000020
    Yaw = 0x00000040
    Throttle = 0x00000080


class GameInputGamepadAxes(IntFlag):
    NoneFlag = 0x00000000
    LeftTrigger = 0x00000001
    RightTrigger = 0x00000002
    LeftThumbstickX = 0x00000004
    LeftThumbstickY = 0x00000008
    RightThumbstickX = 0x00000010
    RightThumbstickY = 0x00000020


class GameInputRacingWheelAxes(IntFlag):
    NoneFlag = 0x00000000
    Steering = 0x00000100
    Throttle = 0x00000200
    Brake = 0x00000400
    Clutch = 0x00000800
    Handbrake = 0x00001000
    PatternShifter = 0x00002000


class GameInputDeviceStatus(IntFlag):
    NoStatus = 0x00000000
    Connected = 0x00000001
    HapticInfoReady = 0x00200000
    AnyStatus = 0xFFFFFFFF


class GameInputDeviceFamily(IntEnum):
    Virtual = -1
    Unknown = 0
    XboxOne = 1
    Xbox360 = 2
    Hid = 3
    I8042 = 4
    Aggregate = 5


class GameInputLabel(IntEnum):
    Unknown = -1
    NoneLabel = 0
    XboxGuide = 1
    XboxBack = 2
    XboxStart = 3
    XboxMenu = 4
    XboxView = 5
    XboxA = 7
    XboxB = 8
    XboxX = 9
    XboxY = 10
    XboxDPadUp = 11
    XboxDPadDown = 12
    XboxDPadLeft = 13
    XboxDPadRight = 14
    XboxLeftShoulder = 15
    XboxLeftTrigger = 16
    XboxLeftStickButton = 17
    XboxRightShoulder = 18
    XboxRightTrigger = 19
    XboxRightStickButton = 20
    XboxPaddle1 = 21
    XboxPaddle2 = 22
    XboxPaddle3 = 23
    XboxPaddle4 = 24
    LetterA = 25
    LetterB = 26
    LetterC = 27
    LetterD = 28
    LetterE = 29
    LetterF = 30
    LetterG = 31
    LetterH = 32
    LetterI = 33
    LetterJ = 34
    LetterK = 35
    LetterL = 36
    LetterM = 37
    LetterN = 38
    LetterO = 39
    LetterP = 40
    LetterQ = 41
    LetterR = 42
    LetterS = 43
    LetterT = 44
    LetterU = 45
    LetterV = 46
    LetterW = 47
    LetterX = 48
    LetterY = 49
    LetterZ = 50
    Number0 = 51
    Number1 = 52
    Number2 = 53
    Number3 = 54
    Number4 = 55
    Number5 = 56
    Number6 = 57
    Number7 = 58
    Number8 = 59
    Number9 = 60
    ArrowUp = 61
    ArrowUpRight = 62
    ArrowRight = 63
    ArrowDownRight = 64
    ArrowDown = 65
    ArrowDownLeft = 66
    ArrowLeft = 67
    ArrowUpLeft = 68
    ArrowUpDown = 69
    ArrowLeftRight = 70
    ArrowUpDownLeftRight = 71
    ArrowClockwise = 72
    ArrowCounterClockwise = 73
    ArrowReturn = 74
    IconBranding = 75
    IconHome = 76
    IconMenu = 77
    IconCross = 78
    IconCircle = 79
    IconSquare = 80
    IconTriangle = 81
    IconStar = 82
    IconDPadUp = 83
    IconDPadDown = 84
    IconDPadLeft = 85
    IconDPadRight = 86
    IconDialClockwise = 87
    IconDialCounterClockwise = 88
    IconSliderLeftRight = 89
    IconSliderUpDown = 90
    IconWheelUpDown = 91
    IconPlus = 92
    IconMinus = 93
    IconSuspension = 94
    Home = 95
    Guide = 96
    Mode = 97
    Select = 98
    Menu = 99
    View = 100
    Back = 101
    Start = 102
    Options = 103
    Share = 104
    Up = 105
    Down = 106
    Left = 107
    Right = 108
    LB = 109
    LT = 110
    LSB = 111
    L1 = 112
    L2 = 113
    L3 = 114
    RB = 115
    RT = 116
    RSB = 117
    R1 = 118
    R2 = 119
    R3 = 120
    PaddleLeft1 = 121
    PaddleLeft2 = 122
    PaddleRight1 = 123
    PaddleRight2 = 124


class GameInputFeedbackAxes(IntFlag):
    NoneFlag = 0x00000000
    LinearX = 0x00000001
    LinearY = 0x00000002
    LinearZ = 0x00000004
    AngularX = 0x00000008
    AngularY = 0x00000010
    AngularZ = 0x00000020
    Normal = 0x00000040


class GameInputFeedbackEffectState(IntEnum):
    Stopped = 0
    Running = 1
    Paused = 2


class GameInputForceFeedbackEffectKind(IntEnum):
    Constant = 0
    Ramp = 1
    SineWave = 2
    SquareWave = 3
    TriangleWave = 4
    SawtoothUpWave = 5
    SawtoothDownWave = 6
    Spring = 7
    Friction = 8
    Damper = 9
    Inertia = 10


class GameInputRumbleMotors(IntFlag):
    NoneFlag = 0x00000000
    LowFrequency = 0x00000001
    HighFrequency = 0x00000002
    LeftTrigger = 0x00000004
    RightTrigger = 0x00000008


class GameInputElementKind(IntEnum):
    NoneKind = 0
    Axis = 1
    Button = 2
    Switch = 3


# ============================================================================
# Haptic locations / limits
# ============================================================================

GAMEINPUT_HAPTIC_LOCATION_NONE = _guid(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
GAMEINPUT_HAPTIC_LOCATION_GRIP_LEFT = _guid(0x08C707C2, 0x66BB, 0x406C, 0xA8, 0x4A, 0xDF, 0xE0, 0x85, 0x12, 0x0A, 0x92)
GAMEINPUT_HAPTIC_LOCATION_GRIP_RIGHT = _guid(0x155A0B77, 0x8BB2, 0x40DB, 0x86, 0x90, 0xB6, 0xD4, 0x11, 0x26, 0xDF, 0xC1)
GAMEINPUT_HAPTIC_LOCATION_TRIGGER_LEFT = _guid(0x8DE4D896, 0x5559, 0x4081, 0x86, 0xE5, 0x17, 0x24, 0xCC, 0x07, 0xC6, 0xBC)
GAMEINPUT_HAPTIC_LOCATION_TRIGGER_RIGHT = _guid(0xFF0CB557, 0x3AF5, 0x406B, 0x8B, 0x0F, 0x55, 0x5A, 0x2D, 0x92, 0xA2, 0x20)

GAMEINPUT_HAPTIC_MAX_LOCATIONS = 8
GAMEINPUT_HAPTIC_MAX_AUDIO_ENDPOINT_ID_SIZE = 256


# ============================================================================
# Callback types
# ============================================================================

GameInputCallbackToken = c_uint64

GameInputReadingCallback = ctypes.WINFUNCTYPE(
    None,
    c_uint64,   # callbackToken
    c_void_p,   # context
    c_void_p,   # reading (IGameInputReading*)
)

GameInputDeviceCallback = ctypes.WINFUNCTYPE(
    None,
    c_uint64,   # callbackToken
    c_void_p,   # context
    c_void_p,   # device (IGameInputDevice*)
    c_uint64,   # timestamp
    c_uint32,   # currentStatus (GameInputDeviceStatus)
    c_uint32,   # previousStatus (GameInputDeviceStatus)
)

GameInputSystemButtonCallback = ctypes.WINFUNCTYPE(
    None,
    c_uint64,
    c_void_p,
    c_void_p,   # device
    c_uint64,
    c_uint32,   # currentButtons
    c_uint32,   # previousButtons
)

GameInputKeyboardLayoutCallback = ctypes.WINFUNCTYPE(
    None,
    c_uint64,
    c_void_p,
    c_void_p,   # device
    c_uint64,
    c_uint32,   # currentLayout
    c_uint32,   # previousLayout
)


# ============================================================================
# Plain structures
# ============================================================================

class GameInputKeyState(Structure):
    _fields_ = [
        ("scanCode", c_uint32),
        ("codePoint", c_uint32),
        ("virtualKey", c_uint8),
        ("isDeadKey", c_bool),
    ]


class GameInputMouseState(Structure):
    _fields_ = [
        ("buttons", c_uint32),
        ("positions", c_uint32),
        ("positionX", ctypes.c_int64),
        ("positionY", ctypes.c_int64),
        ("absolutePositionX", ctypes.c_int64),
        ("absolutePositionY", ctypes.c_int64),
        ("wheelX", ctypes.c_int64),
        ("wheelY", ctypes.c_int64),
    ]


class GameInputVersion(Structure):
    _fields_ = [
        ("major", c_uint16),
        ("minor", c_uint16),
        ("build", c_uint16),
        ("revision", c_uint16),
    ]


class GameInputSensorsState(Structure):
    _fields_ = [
        ("accelerationInGX", c_float),
        ("accelerationInGY", c_float),
        ("accelerationInGZ", c_float),
        ("angularVelocityInRadPerSecX", c_float),
        ("angularVelocityInRadPerSecY", c_float),
        ("angularVelocityInRadPerSecZ", c_float),
        ("headingInDegreesFromMagneticNorth", c_float),
        ("headingAccuracy", c_uint32),
        ("orientationW", c_float),
        ("orientationX", c_float),
        ("orientationY", c_float),
        ("orientationZ", c_float),
    ]


class GameInputArcadeStickState(Structure):
    _fields_ = [("buttons", c_uint32)]


class GameInputFlightStickState(Structure):
    _fields_ = [
        ("buttons", c_uint32),
        ("hatSwitch", c_int32),
        ("roll", c_float),
        ("pitch", c_float),
        ("yaw", c_float),
        ("throttle", c_float),
    ]


class GameInputGamepadState(Structure):
    _fields_ = [
        ("buttons", c_uint32),
        ("leftTrigger", c_float),
        ("rightTrigger", c_float),
        ("leftThumbstickX", c_float),
        ("leftThumbstickY", c_float),
        ("rightThumbstickX", c_float),
        ("rightThumbstickY", c_float),
    ]


class GameInputRacingWheelState(Structure):
    _fields_ = [
        ("buttons", c_uint32),
        ("patternShifterGear", c_int32),
        ("wheel", c_float),
        ("throttle", c_float),
        ("brake", c_float),
        ("clutch", c_float),
        ("handbrake", c_float),
    ]


class GameInputUsage(Structure):
    _fields_ = [
        ("page", c_uint16),
        ("id", c_uint16),
    ]


GAMEINPUT_MAX_SWITCH_STATES = 8


class GameInputControllerSwitchInfo(Structure):
    _fields_ = [
        ("labels", c_int32 * GAMEINPUT_MAX_SWITCH_STATES),
        ("kind", c_int32),
    ]


class GameInputControllerInfo(Structure):
    _fields_ = [
        ("controllerAxisCount", c_uint32),
        ("controllerAxisLabels", POINTER(c_int32)),
        ("controllerButtonCount", c_uint32),
        ("controllerButtonLabels", POINTER(c_int32)),
        ("controllerSwitchCount", c_uint32),
        ("controllerSwitchInfo", POINTER(GameInputControllerSwitchInfo)),
    ]


class GameInputKeyboardInfo(Structure):
    _fields_ = [
        ("kind", c_int32),
        ("layout", c_uint32),
        ("keyCount", c_uint32),
        ("functionKeyCount", c_uint32),
        ("maxSimultaneousKeys", c_uint32),
        ("platformType", c_uint32),
        ("platformSubtype", c_uint32),
    ]


class GameInputMouseInfo(Structure):
    _fields_ = [
        ("supportedButtons", c_uint32),
        ("sampleRate", c_uint32),
        ("hasWheelX", c_bool),
        ("hasWheelY", c_bool),
    ]


class GameInputSensorsInfo(Structure):
    _fields_ = [("supportedSensors", c_uint32)]


class GameInputArcadeStickInfo(Structure):
    _fields_ = [
        ("menuButtonLabel", c_int32),
        ("viewButtonLabel", c_int32),
        ("stickUpLabel", c_int32),
        ("stickDownLabel", c_int32),
        ("stickLeftLabel", c_int32),
        ("stickRightLabel", c_int32),
        ("actionButton1Label", c_int32),
        ("actionButton2Label", c_int32),
        ("actionButton3Label", c_int32),
        ("actionButton4Label", c_int32),
        ("actionButton5Label", c_int32),
        ("actionButton6Label", c_int32),
        ("specialButton1Label", c_int32),
        ("specialButton2Label", c_int32),
        ("extraButtonCount", c_uint32),
        ("extraAxisCount", c_uint32),
    ]


class GameInputFlightStickInfo(Structure):
    _fields_ = [
        ("menuButtonLabel", c_int32),
        ("viewButtonLabel", c_int32),
        ("firePrimaryButtonLabel", c_int32),
        ("fireSecondaryButtonLabel", c_int32),
        ("hatSwitchUpLabel", c_int32),
        ("hatSwitchDownLabel", c_int32),
        ("hatSwitchLeftLabel", c_int32),
        ("hatSwitchRightLabel", c_int32),
        ("aButtonLabel", c_int32),
        ("bButtonLabel", c_int32),
        ("xButtonLabel", c_int32),
        ("yButtonLabel", c_int32),
        ("leftShoulderButtonLabel", c_int32),
        ("rightShoulderButtonLabel", c_int32),
        ("extraButtonCount", c_uint32),
        ("extraAxisCount", c_uint32),
    ]


class GameInputGamepadInfo(Structure):
    _fields_ = [
        ("supportedLayout", c_uint32),
        ("menuButtonLabel", c_int32),
        ("viewButtonLabel", c_int32),
        ("aButtonLabel", c_int32),
        ("bButtonLabel", c_int32),
        ("cButtonLabel", c_int32),
        ("xButtonLabel", c_int32),
        ("yButtonLabel", c_int32),
        ("zButtonLabel", c_int32),
        ("dpadUpLabel", c_int32),
        ("dpadDownLabel", c_int32),
        ("dpadLeftLabel", c_int32),
        ("dpadRightLabel", c_int32),
        ("leftShoulderButtonLabel", c_int32),
        ("rightShoulderButtonLabel", c_int32),
        ("leftThumbstickButtonLabel", c_int32),
        ("rightThumbstickButtonLabel", c_int32),
        ("extraButtonCount", c_uint32),
        ("extraAxisCount", c_uint32),
    ]


class GameInputRacingWheelInfo(Structure):
    _fields_ = [
        ("menuButtonLabel", c_int32),
        ("viewButtonLabel", c_int32),
        ("previousGearButtonLabel", c_int32),
        ("nextGearButtonLabel", c_int32),
        ("dpadUpLabel", c_int32),
        ("dpadDownLabel", c_int32),
        ("dpadLeftLabel", c_int32),
        ("dpadRightLabel", c_int32),
        ("aButtonLabel", c_int32),
        ("bButtonLabel", c_int32),
        ("xButtonLabel", c_int32),
        ("yButtonLabel", c_int32),
        ("leftThumbstickButtonLabel", c_int32),
        ("rightThumbstickButtonLabel", c_int32),
        ("hasClutch", c_bool),
        ("hasHandbrake", c_bool),
        ("hasPatternShifter", c_bool),
        ("minPatternShifterGear", c_int32),
        ("maxPatternShifterGear", c_int32),
        ("maxWheelAngle", c_float),
        ("extraButtonCount", c_uint32),
        ("extraAxisCount", c_uint32),
    ]


class GameInputForceFeedbackMotorInfo(Structure):
    _fields_ = [
        ("supportedAxes", c_uint32),
        ("isConstantEffectSupported", c_bool),
        ("isRampEffectSupported", c_bool),
        ("isSineWaveEffectSupported", c_bool),
        ("isSquareWaveEffectSupported", c_bool),
        ("isTriangleWaveEffectSupported", c_bool),
        ("isSawtoothUpWaveEffectSupported", c_bool),
        ("isSawtoothDownWaveEffectSupported", c_bool),
        ("isSpringEffectSupported", c_bool),
        ("isFrictionEffectSupported", c_bool),
        ("isDamperEffectSupported", c_bool),
        ("isInertiaEffectSupported", c_bool),
    ]


class GameInputRawDeviceReportInfo(Structure):
    _fields_ = [
        ("kind", c_int32),
        ("id", c_uint32),
        ("size", c_uint32),
    ]


class GameInputDeviceInfo(Structure):
    _fields_ = [
        ("vendorId", c_uint16),
        ("productId", c_uint16),
        ("revisionNumber", c_uint16),
        ("usage", GameInputUsage),
        ("hardwareVersion", GameInputVersion),
        ("firmwareVersion", GameInputVersion),
        ("deviceId", APP_LOCAL_DEVICE_ID),
        ("deviceRootId", APP_LOCAL_DEVICE_ID),
        ("deviceFamily", c_int32),
        ("supportedInput", c_uint32),
        ("supportedRumbleMotors", c_uint32),
        ("supportedSystemButtons", c_uint32),
        ("containerId", GUID),
        ("displayName", c_char_p),
        ("pnpPath", c_char_p),
        ("keyboardInfo", POINTER(GameInputKeyboardInfo)),
        ("mouseInfo", POINTER(GameInputMouseInfo)),
        ("sensorsInfo", POINTER(GameInputSensorsInfo)),
        ("controllerInfo", POINTER(GameInputControllerInfo)),
        ("arcadeStickInfo", POINTER(GameInputArcadeStickInfo)),
        ("flightStickInfo", POINTER(GameInputFlightStickInfo)),
        ("gamepadInfo", POINTER(GameInputGamepadInfo)),
        ("racingWheelInfo", POINTER(GameInputRacingWheelInfo)),
        ("forceFeedbackMotorCount", c_uint32),
        ("forceFeedbackMotorInfo", POINTER(GameInputForceFeedbackMotorInfo)),
        ("inputReportCount", c_uint32),
        ("inputReportInfo", POINTER(GameInputRawDeviceReportInfo)),
        ("outputReportCount", c_uint32),
        ("outputReportInfo", POINTER(GameInputRawDeviceReportInfo)),
    ]


class GameInputHapticInfo(Structure):
    _fields_ = [
        ("audioEndpointId", c_wchar * GAMEINPUT_HAPTIC_MAX_AUDIO_ENDPOINT_ID_SIZE),
        ("locationCount", c_uint32),
        ("locations", GUID * GAMEINPUT_HAPTIC_MAX_LOCATIONS),
    ]


class GameInputRumbleParams(Structure):
    _fields_ = [
        ("lowFrequency", c_float),
        ("highFrequency", c_float),
        ("leftTrigger", c_float),
        ("rightTrigger", c_float),
    ]


# --- Force feedback params (used by CreateForceFeedbackEffect) -----------

class GameInputForceFeedbackEnvelope(Structure):
    _fields_ = [
        ("attackDuration", c_uint64),
        ("sustainDuration", c_uint64),
        ("releaseDuration", c_uint64),
        ("attackGain", c_float),
        ("sustainGain", c_float),
        ("releaseGain", c_float),
        ("playCount", c_uint32),
        ("repeatDelay", c_uint64),
    ]


class GameInputForceFeedbackMagnitude(Structure):
    _fields_ = [
        ("linearX", c_float),
        ("linearY", c_float),
        ("linearZ", c_float),
        ("angularX", c_float),
        ("angularY", c_float),
        ("angularZ", c_float),
        ("normal", c_float),
    ]


class GameInputForceFeedbackConditionParams(Structure):
    _fields_ = [
        ("magnitude", GameInputForceFeedbackMagnitude),
        ("positiveCoefficient", c_float),
        ("negativeCoefficient", c_float),
        ("maxPositiveMagnitude", c_float),
        ("maxNegativeMagnitude", c_float),
        ("deadZone", c_float),
        ("bias", c_float),
    ]


class GameInputForceFeedbackConstantParams(Structure):
    _fields_ = [
        ("envelope", GameInputForceFeedbackEnvelope),
        ("magnitude", GameInputForceFeedbackMagnitude),
    ]


class GameInputForceFeedbackPeriodicParams(Structure):
    _fields_ = [
        ("envelope", GameInputForceFeedbackEnvelope),
        ("magnitude", GameInputForceFeedbackMagnitude),
        ("frequency", c_float),
        ("phase", c_float),
        ("bias", c_float),
    ]


class GameInputForceFeedbackRampParams(Structure):
    _fields_ = [
        ("envelope", GameInputForceFeedbackEnvelope),
        ("startMagnitude", GameInputForceFeedbackMagnitude),
        ("endMagnitude", GameInputForceFeedbackMagnitude),
    ]


class _GameInputForceFeedbackParamsData(Union):
    _fields_ = [
        ("constant", GameInputForceFeedbackConstantParams),
        ("ramp", GameInputForceFeedbackRampParams),
        ("sineWave", GameInputForceFeedbackPeriodicParams),
        ("squareWave", GameInputForceFeedbackPeriodicParams),
        ("triangleWave", GameInputForceFeedbackPeriodicParams),
        ("sawtoothUpWave", GameInputForceFeedbackPeriodicParams),
        ("sawtoothDownWave", GameInputForceFeedbackPeriodicParams),
        ("spring", GameInputForceFeedbackConditionParams),
        ("friction", GameInputForceFeedbackConditionParams),
        ("damper", GameInputForceFeedbackConditionParams),
        ("inertia", GameInputForceFeedbackConditionParams),
    ]


class GameInputForceFeedbackParams(Structure):
    _fields_ = [
        ("kind", c_int32),
        ("data", _GameInputForceFeedbackParamsData),
    ]


# --- Mapping structs (used by IGameInputMapper) ---------------------------

class GameInputAxisMapping(Structure):
    _fields_ = [
        ("controllerElementKind", c_int32),
        ("controllerIndex", c_uint32),
        ("isInverted", c_bool),
        ("fromTwoButtons", c_bool),
        ("buttonMinIndexValue", c_uint32),
        ("referenceDirection", c_int32),
    ]


class GameInputButtonMapping(Structure):
    _fields_ = [
        ("controllerElementKind", c_int32),
        ("controllerIndex", c_uint32),
        ("isInverted", c_bool),
        ("switchPosition", c_int32),
    ]


# ============================================================================
# COM vtable index namespaces
#
# Every COM interface starts with IUnknown (QueryInterface=0, AddRef=1,
# Release=2); interface-specific methods start at index 3. These indices
# are v3-specific -- earlier GameInput API versions had different methods
# (e.g. GetTemporalReading, FindDeviceFromObject) that shift everything.
# ============================================================================

class IUnknownIdx:
    QUERY_INTERFACE = 0
    ADD_REF = 1
    RELEASE = 2


class IGameInputIdx:
    GET_CURRENT_TIMESTAMP = 3
    GET_CURRENT_READING = 4
    GET_NEXT_READING = 5
    GET_PREVIOUS_READING = 6
    REGISTER_READING_CALLBACK = 7
    REGISTER_DEVICE_CALLBACK = 8
    REGISTER_SYSTEM_BUTTON_CALLBACK = 9
    REGISTER_KEYBOARD_LAYOUT_CALLBACK = 10
    STOP_CALLBACK = 11
    UNREGISTER_CALLBACK = 12
    CREATE_DISPATCHER = 13
    FIND_DEVICE_FROM_ID = 14
    FIND_DEVICE_FROM_PLATFORM_STRING = 15
    SET_FOCUS_POLICY = 16
    CREATE_AGGREGATE_DEVICE = 17
    DISABLE_AGGREGATE_DEVICE = 18


class IGameInputReadingIdx:
    GET_INPUT_KIND = 3
    GET_TIMESTAMP = 4
    GET_DEVICE = 5
    GET_CONTROLLER_AXIS_COUNT = 6
    GET_CONTROLLER_AXIS_STATE = 7
    GET_CONTROLLER_BUTTON_COUNT = 8
    GET_CONTROLLER_BUTTON_STATE = 9
    GET_CONTROLLER_SWITCH_COUNT = 10
    GET_CONTROLLER_SWITCH_STATE = 11
    GET_KEY_COUNT = 12
    GET_KEY_STATE = 13
    GET_MOUSE_STATE = 14
    GET_SENSORS_STATE = 15
    GET_ARCADE_STICK_STATE = 16
    GET_FLIGHT_STICK_STATE = 17
    GET_GAMEPAD_STATE = 18
    GET_RACING_WHEEL_STATE = 19
    GET_RAW_REPORT = 20


class IGameInputDeviceIdx:
    GET_DEVICE_INFO = 3
    GET_HAPTIC_INFO = 4
    GET_DEVICE_STATUS = 5
    CREATE_FORCE_FEEDBACK_EFFECT = 6
    IS_FORCE_FEEDBACK_MOTOR_POWERED_ON = 7
    SET_FORCE_FEEDBACK_MOTOR_GAIN = 8
    SET_RUMBLE_STATE = 9
    DIRECT_INPUT_ESCAPE = 10
    CREATE_INPUT_MAPPER = 11
    GET_EXTRA_AXIS_COUNT = 12
    GET_EXTRA_BUTTON_COUNT = 13
    GET_EXTRA_AXIS_INDEXES = 14
    GET_EXTRA_BUTTON_INDEXES = 15
    CREATE_RAW_DEVICE_REPORT = 16
    SEND_RAW_DEVICE_OUTPUT = 17


class IGameInputDispatcherIdx:
    DISPATCH = 3
    OPEN_WAIT_HANDLE = 4


class IGameInputForceFeedbackEffectIdx:
    GET_DEVICE = 3
    GET_MOTOR_INDEX = 4
    GET_GAIN = 5
    SET_GAIN = 6
    GET_PARAMS = 7
    SET_PARAMS = 8
    GET_STATE = 9
    SET_STATE = 10


class IGameInputMapperIdx:
    GET_ARCADE_STICK_BUTTON_MAPPING_INFO = 3
    GET_FLIGHT_STICK_AXIS_MAPPING_INFO = 4
    GET_FLIGHT_STICK_BUTTON_MAPPING_INFO = 5
    GET_GAMEPAD_AXIS_MAPPING_INFO = 6
    GET_GAMEPAD_BUTTON_MAPPING_INFO = 7
    GET_RACING_WHEEL_AXIS_MAPPING_INFO = 8
    GET_RACING_WHEEL_BUTTON_MAPPING_INFO = 9


# ============================================================================
# COM helpers
# ============================================================================

def get_vtable(interface):
    """Return the COM vtable for a COM interface pointer."""

    if not interface:
        raise RuntimeError("Null COM interface")

    interface_pointer = ctypes.cast(interface, POINTER(c_void_p))
    vtable_address = interface_pointer[0]

    if not vtable_address:
        raise RuntimeError("Null COM vtable")

    return ctypes.cast(vtable_address, POINTER(c_void_p))


def get_method(interface, index, restype, argtypes):
    """Look up and bind a single COM vtable method by index."""

    vtable = get_vtable(interface)
    address = vtable[index]

    if not address:
        raise RuntimeError(f"Null COM method at vtable[{index}]")

    return ctypes.WINFUNCTYPE(restype, c_void_p, *argtypes)(address)


def addref(interface):
    """AddRef a COM interface. Returns the new refcount."""

    if not interface:
        return 0
    return get_method(interface, IUnknownIdx.ADD_REF, c_uint32, [])(interface)


def release(interface):
    """Release a COM interface. Returns the new refcount."""

    if not interface:
        return 0
    return get_method(interface, IUnknownIdx.RELEASE, c_uint32, [])(interface)


def check_hresult(hr, operation):
    """Raise OSError if an HRESULT indicates failure."""

    if hr < 0:
        raise OSError(f"{operation} failed: HRESULT=0x{hr & 0xFFFFFFFF:08X}")


# ============================================================================
# DLL loading / interface creation
# ============================================================================

def load_dll(path=GAMEINPUT_REDIST_PATH):
    """Load the GameInput redistributable DLL."""

    return ctypes.WinDLL(path)


def create_gameinput(dll):
    """Call GameInputInitialize(IID_IGameInput, ...) and return the raw
    IGameInput interface pointer (c_void_p).

    Note: GameInputCreate() in the header is only an inline C++ helper --
    it is not a DLL export. GameInputInitialize is the real export.
    """

    initialize = dll.GameInputInitialize
    initialize.argtypes = [POINTER(GUID), POINTER(c_void_p)]
    initialize.restype = c_long

    gameinput = c_void_p()
    hr = initialize(ctypes.byref(IID_IGameInput), ctypes.byref(gameinput))
    check_hresult(hr, "GameInputInitialize")

    return gameinput
