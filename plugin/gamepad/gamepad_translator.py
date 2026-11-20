from dataclasses import dataclass
from typing import Callable, Iterable, Mapping

from .gamepad_types import Button, Trigger, Stick, GamepadState

# -----------------------------------------------------------------------------
# A translator is anything that takes a GamepadState and returns a GamepadState.
# -----------------------------------------------------------------------------
GamepadStateTranslator = Callable[[GamepadState], GamepadState]


@dataclass(frozen=True)
class StickDir:
    """One direction of a stick, usable as a Remap target for a Button source."""
    stick: Stick
    positive: bool


# Convenience names so mappings read nicely: Button.DPAD_LEFT: LX_NEG
LX_NEG, LX_POS = StickDir(Stick.LX, False), StickDir(Stick.LX, True)
LY_NEG, LY_POS = StickDir(Stick.LY, False), StickDir(Stick.LY, True)
RX_NEG, RX_POS = StickDir(Stick.RX, False), StickDir(Stick.RX, True)
RY_NEG, RY_POS = StickDir(Stick.RY, False), StickDir(Stick.RY, True)


def _targets(value):
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(value)
    return (value,)


class Remap:
    """
    Declarative input remapping.

        Remap({Button.A: Button.B})                      # A reports as B
        Remap({Button.A: Button.B, Button.B: Button.A})  # swap
        Remap({Button.X: [Button.A, Button.B]})          # one source, many targets
        Remap({Trigger.LEFT: Button.LB})                 # trigger past threshold -> button
        Remap({Button.LB: Trigger.LEFT})                 # button -> full trigger
        Remap({Stick.LX: Stick.RX})                      # stick -> stick
        Remap({Button.DPAD_LEFT: LX_NEG})                # button -> stick direction
        Remap({...}, invert=[Stick.LY])                  # flip a stick axis

    Rules:
      * Every mapped source is cleared first, then written to its targets,
        so swaps work and a source no longer reports as itself.
      * Unmapped inputs pass through untouched.
      * When several inputs land on the same target: buttons OR, triggers take
        the max, sticks take the value with the largest magnitude.
    """

    def __init__(self, mapping: Mapping = None, invert: Iterable[Stick] = (), trigger_threshold: int = 128):
        self.mapping = {src: _targets(dst) for src, dst in (mapping or {}).items()}
        self.invert = frozenset(invert)
        self.trigger_threshold = trigger_threshold

        for src, dsts in self.mapping.items():
            for dst in dsts:
                self._validate(src, dst)

    @staticmethod
    def _validate(src, dst):
        ok = (
            (isinstance(src, Button) and isinstance(dst, (Button, Trigger, StickDir)))
            or (isinstance(src, Trigger) and isinstance(dst, (Button, Trigger)))
            or (isinstance(src, Stick) and isinstance(dst, Stick))
        )
        if not ok:
            raise ValueError(f"Unsupported mapping: {src!r} -> {dst!r}")

    def _is_pressed(self, state, src):
        if isinstance(src, Button):
            return bool(state.buttons.get(src, False))
        return state.triggers.get(src, 0) >= self.trigger_threshold

    def __call__(self, state: GamepadState) -> GamepadState:
        buttons = dict(state.buttons)
        sticks = dict(state.sticks)
        triggers = dict(state.triggers)

        # clear mapped sources
        for src in self.mapping:
            if isinstance(src, Button):
                buttons[src] = False
            elif isinstance(src, Trigger):
                triggers[src] = Trigger.min_value()
            else:
                sticks[src] = 0

        # write to targets 
        for src, dsts in self.mapping.items():
            for dst in dsts:
                if isinstance(dst, Button):
                    buttons[dst] = buttons.get(dst, False) or self._is_pressed(state, src)

                elif isinstance(dst, Trigger):
                    if isinstance(src, Trigger):
                        value = state.triggers.get(src, 0)
                    else:
                        value = Trigger.max_value() if self._is_pressed(state, src) else 0
                    triggers[dst] = max(triggers.get(dst, 0), value)

                elif isinstance(dst, StickDir):
                    if self._is_pressed(state, src):
                        value = Stick.max_value() if dst.positive else Stick.min_value()
                        current = sticks.get(dst.stick, 0)
                        if abs(value) > abs(current):
                            sticks[dst.stick] = value

                elif isinstance(dst, Stick):
                    value = state.sticks.get(src, 0)
                    current = sticks.get(dst, 0)
                    if abs(value) > abs(current):
                        sticks[dst] = value

        # inversions
        for stick in self.invert:
            if stick in sticks:
                sticks[stick] = max(Stick.min_value(), min(Stick.max_value(), -sticks[stick]))

        return GamepadState(buttons=buttons, sticks=sticks, triggers=triggers)

