import ctypes
from ctypes import byref, c_void_p, c_uint64

from . import GameInput as GI
from .gamepad_types import Button, Trigger, Stick, GamepadState


class GamepadNotFoundError(RuntimeError):
    """Raised when no connected device matches the requested VID/PID."""
    pass


class GameInputController:
    """A single Gamepad device, located by VID/PID at construction time."""

    def __init__(self, vid_pid_tuple, allow_background_input=True):
        self.vendor_id, self.product_id = vid_pid_tuple
        self._gameinput = GI.create_gameinput()
        self._device = None

        try:
            self._device = self._find_device()
            if allow_background_input:
                GI.IGameInput.setFocusPolicy(self._gameinput, GI.GameInputFocusPolicy.EnableBackgroundInput)
        except Exception:
            self.close()
            raise

    def _find_device(self):
        found = c_void_p()

        def callback(callback_token, context, device_ptr, timestamp, current_status, previous_status):
            if found.value is not None or not device_ptr:
                return
            info = self._get_device_info(c_void_p(device_ptr))
            if info is not None and info.vendorId == self.vendor_id and info.productId == self.product_id:
                handle = c_void_p(device_ptr)
                GI.IUnknown.addRef(handle)
                found.value = handle.value

        callback_ref = GI.GameInputDeviceCallback(callback)
        token = c_uint64()

        hr = GI.IGameInput.registerDeviceCallback(
            self._gameinput,
            None,
            GI.GameInputKind.Gamepad,
            GI.GameInputDeviceStatus.AnyStatus,
            GI.GameInputEnumerationKind.BlockingEnumeration,
            None,
            callback_ref,
            byref(token),
        )
        GI.check_hresult(hr, "RegisterDeviceCallback")

        if token.value:
            GI.IGameInput.unregisterCallback(self._gameinput, token.value)

        if found.value is None:
            raise GamepadNotFoundError(
                f"No connected gamepad found with VID=0x{self.vendor_id:04X} PID=0x{self.product_id:04X}"
            )

        return c_void_p(found.value)

    def _get_device_info(self, device):
        info_ptr = c_void_p()
        hr = GI.IGameInputDevice.getDeviceInfo(device, byref(info_ptr))

        if hr != 0 or not info_ptr.value:
            return None

        return ctypes.cast(info_ptr, ctypes.POINTER(GI.GameInputDeviceInfo)).contents

    # ------------------------------------------------------------------
    # Reading current state
    # ------------------------------------------------------------------

    def get_gamepad_state(self):

        if self._device is None:
            return None

        reading = c_void_p()
        hr = GI.IGameInput.getCurrentReading(
            self._gameinput, GI.GameInputKind.Gamepad, self._device, byref(reading)
        )

        if hr != 0 or not reading.value:
            return None

        try:
            raw_state = GI.GameInputGamepadState()
            success = GI.IGameInputReading.getGamepadState(reading, byref(raw_state))

            if not success:
                return None

            return self._to_gamepad_state(raw_state)
        finally:
            GI.IUnknown.release(reading)

    # ------------------------------------------------------------------
    # Conversion: GameInputGamepadState -> GamepadState
    # ------------------------------------------------------------------

    _BUTTON_MAP = {
        Button.A: GI.GameInputGamepadButtons.A,
        Button.B: GI.GameInputGamepadButtons.B,
        Button.X: GI.GameInputGamepadButtons.X,
        Button.Y: GI.GameInputGamepadButtons.Y,
        Button.LB: GI.GameInputGamepadButtons.LeftShoulder,
        Button.RB: GI.GameInputGamepadButtons.RightShoulder,
        Button.BACK: GI.GameInputGamepadButtons.View,
        Button.START: GI.GameInputGamepadButtons.Menu,
        Button.L3: GI.GameInputGamepadButtons.LeftThumbstick,
        Button.R3: GI.GameInputGamepadButtons.RightThumbstick,
        Button.DPAD_UP: GI.GameInputGamepadButtons.DPadUp,
        Button.DPAD_DOWN: GI.GameInputGamepadButtons.DPadDown,
        Button.DPAD_LEFT: GI.GameInputGamepadButtons.DPadLeft,
        Button.DPAD_RIGHT: GI.GameInputGamepadButtons.DPadRight,
    }

    @classmethod
    def _to_gamepad_state(cls, raw_state):
        buttons_raw = GI.GameInputGamepadButtons(raw_state.buttons)

        buttons = {
            button: bool(buttons_raw & flag)
            for button, flag in cls._BUTTON_MAP.items()
        }

        sticks = {
            Stick.LX: cls._float_to_stick(raw_state.leftThumbstickX),
            Stick.LY: cls._float_to_stick(raw_state.leftThumbstickY),
            Stick.RX: cls._float_to_stick(raw_state.rightThumbstickX),
            Stick.RY: cls._float_to_stick(raw_state.rightThumbstickY),
        }

        triggers = {
            Trigger.LEFT: cls._float_to_trigger(raw_state.leftTrigger),
            Trigger.RIGHT: cls._float_to_trigger(raw_state.rightTrigger),
        }

        return GamepadState(buttons=buttons, sticks=sticks, triggers=triggers)

    @staticmethod
    def _float_to_stick(value):
        value = max(-1.0, min(1.0, value))
        scale = Stick.max_value() if value >= 0 else -Stick.min_value()
        return int(round(value * scale))

    @staticmethod
    def _float_to_trigger(value):
        value = max(0.0, min(1.0, value))
        return int(round(value * Trigger.max_value()))

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self):
        if self._device is not None:
            GI.IUnknown.release(self._device)
            self._device = None

        if self._gameinput is not None:
            GI.IUnknown.release(self._gameinput)
            self._gameinput = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
