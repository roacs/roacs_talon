"""
gameinput_controller.py

Enumeration and polling logic on top of GameInput.py. GameInput.py only
defines the ctypes/enums/structures mirroring GameInput.h; this module
does the actual COM calls to enumerate devices and read their state.
"""

import ctypes
from ctypes import byref, c_void_p, c_uint32, c_uint64, c_long, c_bool
import time

from . import GameInput as GI


class GamepadDevice:
    """A connected gamepad: the raw IGameInputDevice* plus its decoded
    GameInputDeviceInfo. Holds one AddRef'd reference to the device for
    its lifetime -- call .release() (or use GameInputController.close())
    when done with it."""

    def __init__(self, device_ptr, info):
        self.device = c_void_p(device_ptr)
        self.info = info

    @property
    def vendor_id(self):
        return self.info.vendorId

    @property
    def product_id(self):
        return self.info.productId

    @property
    def display_name(self):
        return self.info.displayName.decode("utf-8", errors="replace") if self.info.displayName else None

    def release(self):
        GI.release(self.device)

    def __repr__(self):
        name = self.display_name or "<unnamed>"
        return f"GamepadDevice(VID=0x{self.vendor_id:04X}, PID=0x{self.product_id:04X}, name={name!r})"


class GameInputController:
    """Owns one IGameInput instance: enumerates gamepads and polls state."""

    def __init__(self, dll_path=GI.GAMEINPUT_REDIST_PATH, allow_background_input=True):
        self._dll = GI.load_dll(dll_path)
        self._gameinput = GI.create_gameinput(self._dll)
        self._devices = []

        if allow_background_input:
            # By default GameInput only delivers live input state to the
            # foreground application (so a background process can't
            # silently read input meant for whatever has focus).
            # Enumeration and device info still work without this, but
            # every GetXState() call will report success with all-zero
            # data unless we opt in here. Talon is a background process,
            # so this is required for real state to ever show up.
            self.set_focus_policy(GI.GameInputFocusPolicy.EnableBackgroundInput)

    def set_focus_policy(self, policy):
        method = GI.get_method(self._gameinput, GI.IGameInputIdx.SET_FOCUS_POLICY, None, [c_uint32])
        method(self._gameinput, int(policy))

    # ------------------------------------------------------------------
    # Enumeration
    #
    # Devices handed to the callback are only valid for the duration of
    # the callback unless AddRef'd (Microsoft's own samples, e.g.
    # DirectXTK's GamePad.cpp, do this explicitly). We AddRef here and
    # keep the reference for the lifetime of the GamepadDevice object.
    # ------------------------------------------------------------------

    def enumerate_devices(self, kind=GI.GameInputKind.Gamepad, timeout=0.5, poll_interval=0.01):
        """Enumerate connected devices matching `kind`. Returns a list of
        GamepadDevice. Replaces any previously enumerated devices (the
        old ones are released)."""

        for device in self._devices:
            device.release()
        self._devices = []

        raw_devices = []
        seen = set()

        def callback(callback_token, context, device_ptr, timestamp, current_status, previous_status):
            if not device_ptr or device_ptr in seen:
                return
            seen.add(device_ptr)
            handle = c_void_p(device_ptr)
            GI.addref(handle)
            raw_devices.append(handle)

        callback_ref = GI.GameInputDeviceCallback(callback)
        token = c_uint64()

        method = GI.get_method(
            self._gameinput,
            GI.IGameInputIdx.REGISTER_DEVICE_CALLBACK,
            c_long,
            [c_void_p, c_uint32, c_uint32, c_uint32, c_void_p, GI.GameInputDeviceCallback, ctypes.POINTER(c_uint64)],
        )

        hr = method(
            self._gameinput,
            None,
            int(kind),
            int(GI.GameInputDeviceStatus.AnyStatus),
            GI.GameInputEnumerationKind.BlockingEnumeration,
            None,
            callback_ref,
            byref(token),
        )
        GI.check_hresult(hr, "RegisterDeviceCallback")

        # Settle-poll: blocking enumeration has been observed on some
        # GameInput versions to not fully synchronize before returning.
        # Stop early once the device count is stable for a few polls.
        deadline = time.monotonic() + timeout
        stable_polls = 0
        last_count = -1

        while time.monotonic() < deadline:
            if len(raw_devices) == last_count:
                stable_polls += 1
                if stable_polls >= 3 and len(raw_devices) > 0:
                    break
            else:
                stable_polls = 0
            last_count = len(raw_devices)
            time.sleep(poll_interval)

        if token.value:
            unregister = GI.get_method(self._gameinput, GI.IGameInputIdx.UNREGISTER_CALLBACK, c_bool, [c_uint64])
            unregister(self._gameinput, token.value)

        for handle in raw_devices:
            info = self._get_device_info(handle)
            if info is not None:
                self._devices.append(GamepadDevice(handle.value, info))
            else:
                GI.release(handle)

        return list(self._devices)

    def _get_device_info(self, device):
        method = GI.get_method(device, GI.IGameInputDeviceIdx.GET_DEVICE_INFO, c_long, [ctypes.POINTER(c_void_p)])

        info_ptr = c_void_p()
        hr = method(device, byref(info_ptr))

        if hr != 0 or not info_ptr.value:
            return None

        return ctypes.cast(info_ptr, ctypes.POINTER(GI.GameInputDeviceInfo)).contents

    # ------------------------------------------------------------------
    # Reading current state
    # ------------------------------------------------------------------

    def get_current_reading(self, device, kind=GI.GameInputKind.Gamepad):
        """Return a raw IGameInputReading* (c_void_p) for `device`, or
        None if unavailable. Caller must GI.release() it when done."""

        method = GI.get_method(
            self._gameinput,
            GI.IGameInputIdx.GET_CURRENT_READING,
            c_long,
            [c_uint32, c_void_p, ctypes.POINTER(c_void_p)],
        )

        reading = c_void_p()
        device_ptr = device.device if isinstance(device, GamepadDevice) else device
        hr = method(self._gameinput, int(kind), device_ptr, byref(reading))

        if hr != 0 or not reading.value:
            return None

        return reading

    def read_gamepad_state(self, device):
        """Return a dict of the current gamepad state for `device`, or
        None if no reading is currently available."""

        reading = self.get_current_reading(device, kind=GI.GameInputKind.Gamepad)

        if reading is None:
            return None

        try:
            method = GI.get_method(
                reading,
                GI.IGameInputReadingIdx.GET_GAMEPAD_STATE,
                c_bool,
                [ctypes.POINTER(GI.GameInputGamepadState)],
            )

            state = GI.GameInputGamepadState()
            success = method(reading, byref(state))

            if not success:
                return None

            buttons = GI.GameInputGamepadButtons(state.buttons)

            return {
                "buttons": buttons,
                "A": bool(buttons & GI.GameInputGamepadButtons.A),
                "B": bool(buttons & GI.GameInputGamepadButtons.B),
                "X": bool(buttons & GI.GameInputGamepadButtons.X),
                "Y": bool(buttons & GI.GameInputGamepadButtons.Y),
                "Menu": bool(buttons & GI.GameInputGamepadButtons.Menu),
                "View": bool(buttons & GI.GameInputGamepadButtons.View),
                "DPadUp": bool(buttons & GI.GameInputGamepadButtons.DPadUp),
                "DPadDown": bool(buttons & GI.GameInputGamepadButtons.DPadDown),
                "DPadLeft": bool(buttons & GI.GameInputGamepadButtons.DPadLeft),
                "DPadRight": bool(buttons & GI.GameInputGamepadButtons.DPadRight),
                "LeftShoulder": bool(buttons & GI.GameInputGamepadButtons.LeftShoulder),
                "RightShoulder": bool(buttons & GI.GameInputGamepadButtons.RightShoulder),
                "LeftThumbstick": bool(buttons & GI.GameInputGamepadButtons.LeftThumbstick),
                "RightThumbstick": bool(buttons & GI.GameInputGamepadButtons.RightThumbstick),
                "LeftTrigger": state.leftTrigger,
                "RightTrigger": state.rightTrigger,
                "LeftThumbstickX": state.leftThumbstickX,
                "LeftThumbstickY": state.leftThumbstickY,
                "RightThumbstickX": state.rightThumbstickX,
                "RightThumbstickY": state.rightThumbstickY,
            }
        finally:
            GI.release(reading)

    # ------------------------------------------------------------------
    # Lookup / diagnostics
    # ------------------------------------------------------------------

    def get_device(self, vendor_id, product_id):
        for device in self._devices:
            if device.vendor_id == vendor_id and device.product_id == product_id:
                return device
        return None

    def print_devices(self):
        devices = self.enumerate_devices()
        print(f"Devices: {len(devices)}")
        for index, device in enumerate(devices):
            print(f"[{index}] {device}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self):
        for device in self._devices:
            device.release()
        self._devices = []

        if self._gameinput is not None:
            GI.release(self._gameinput)
            self._gameinput = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


# ============================================================================
# Shared instance
# ============================================================================

_controller = None


def get_controller():
    global _controller
    if _controller is None:
        _controller = GameInputController()
    return _controller
