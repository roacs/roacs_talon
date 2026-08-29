from enum import Enum
from dataclasses import dataclass, field

class Button(Enum):
    A = "A"
    B = "B"
    X = "X"
    Y = "Y"
    LB = "LB"
    RB = "RB"
    BACK = "BACK"
    START = "START"
    L3 = "L3"
    R3 = "R3"
    DPAD_UP = "DPAD_UP"
    DPAD_DOWN = "DPAD_DOWN"
    DPAD_LEFT = "DPAD_LEFT"
    DPAD_RIGHT = "DPAD_RIGHT"

class Trigger(Enum):
    LEFT = "LT"
    RIGHT = "RT"

    @classmethod
    def min_value(cls):
        return 0

    @classmethod
    def max_value(cls):
        return 255

class Stick(Enum):
    LX = "LX"
    LY = "LY"
    RX = "RX"
    RY = "RY"

    @classmethod
    def min_value(cls):
        return -32768

    @classmethod
    def max_value(cls):
        return 32767

@dataclass
class GamepadState:
    buttons: dict[Button, bool] = field(default_factory=dict)
    sticks: dict[Stick, int] = field(default_factory=lambda: {stick: 0 for stick in Stick})
    triggers: dict[Trigger, int] = field(default_factory=lambda: {trigger: 0 for trigger in Trigger})

@dataclass
class StickCalibration:
    center: int
    negative_scale: float
    positive_scale: float



def print_gamepad_state(state: GamepadState):
    buttons = [b.value for b, v in state.buttons.items() if v]
    sticks = [f"{s.value}={state.sticks[s]}" for s in state.sticks]
    triggers = [f"{t.value}={state.triggers[t]}" for t in state.triggers]

    print(f"Buttons=[{','.join(buttons)}] Sticks=[{','.join(sticks)}] Triggers=[{','.join(triggers)}]")
