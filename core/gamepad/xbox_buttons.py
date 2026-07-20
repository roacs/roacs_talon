from dataclasses import dataclass
from enum import Enum

@dataclass
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

@dataclass
class Trigger(Enum):
    LEFT = "LT"
    RIGHT = "RT"
