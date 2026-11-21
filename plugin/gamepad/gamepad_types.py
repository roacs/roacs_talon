import threading
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

    @classmethod
    def neutral(cls):
        """A state with nothing pressed and every stick centered."""
        return cls()

    def __repr__(self):
        buttons = [b.value for b, v in self.buttons.items() if v]
        sticks = [f"{s.value}={self.sticks[s]}" for s in self.sticks]
        triggers = [f"{t.value}={self.triggers[t]}" for t in self.triggers]
        return f"GamepadState(Buttons=[{','.join(buttons)}] Sticks=[{','.join(sticks)}] Triggers=[{','.join(triggers)}])"

@dataclass
class StickCalibration:
    center: int
    negative_scale: float
    positive_scale: float

class ExternalInput:
    """
    External inputs (voice, pedals, scripts, etc.)

    Buttons and triggers are reference counters.
    Sticks hold a value directly. Thread-safe.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._buttons = {button: 0 for button in Button}
        self._triggers = {trigger: 0 for trigger in Trigger}
        self._sticks = {stick: 0 for stick in Stick}

    def _counters_for(self, item):
        return self._triggers if isinstance(item, Trigger) else self._buttons

    def press(self, items):
        """Increment the press counter for each Button/Trigger."""
        with self._lock:
            for item in items:
                self._counters_for(item)[item] += 1

    def release(self, items):
        """Decrement the press counter for each Button/Trigger (min 0)."""
        with self._lock:
            for item in items:
                counters = self._counters_for(item)
                counters[item] = max(0, counters[item] - 1)

    def set_stick(self, x_stick, y_stick, x, y):
        """Hold a stick (two axes) at the given values, clamped to the valid range."""
        x = max(Stick.min_value(), min(Stick.max_value(), x))
        y = max(Stick.min_value(), min(Stick.max_value(), y))
        with self._lock:
            self._sticks[x_stick] = x
            self._sticks[y_stick] = y

    def clear_stick(self, x_stick, y_stick):
        """Release a stick back to the physical controllers."""
        with self._lock:
            self._sticks[x_stick] = 0
            self._sticks[y_stick] = 0

    def to_gamepad_state(self) -> GamepadState:
        """Convert to GamepadState"""
        with self._lock:
            return GamepadState(
                buttons={button: count > 0 for button, count in self._buttons.items()},
                sticks=dict(self._sticks),
                triggers={
                    trigger: Trigger.max_value() if count > 0 else Trigger.min_value()
                    for trigger, count in self._triggers.items()
                },
            )
