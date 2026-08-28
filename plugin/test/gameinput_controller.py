"""
gameinput_controller.py

Enumeration and polling logic on top of GameInput.py. GameInput.py only
defines the ctypes/enums/structures mirroring GameInput.h; this module
does the actual COM calls to enumerate devices and read their state.
"""

import ctypes
from ctypes import byref, c_void_p, c_uint32, c_uint64, c_long, c_bool

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
        GI.IUnknown.release(self.device)

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
            GI.IGameInput.setFocusPolicy(self._gameinput, GI.GameInputFocusPolicy.EnableBackgroundInput)

    # ------------------------------------------------------------------
    # Enumeration
    # ------------------------------------------------------------------

    def enumerate_devices(self, kind=GI.GameInputKind.Gamepad | GI.GameInputKind.RawDeviceReport):
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
            GI.IUnknown.addRef(handle)
            raw_devices.append(handle)

        callback_ref = GI.GameInputDeviceCallback(callback)
        token = c_uint64()

        hr = GI.IGameInput.registerDeviceCallback(
            self._gameinput,
            None,
            kind,
            GI.GameInputDeviceStatus.AnyStatus,
            GI.GameInputEnumerationKind.BlockingEnumeration,
            None,
            callback_ref,
            byref(token),
        )
        GI.check_hresult(hr, "RegisterDeviceCallback")

        if token.value:
            GI.IGameInput.unregisterCallback(self._gameinput, token.value)

        for handle in raw_devices:
            info = self._get_device_info(handle)
            if info is not None:
                self._devices.append(GamepadDevice(handle.value, info))
            else:
                GI.IUnknown.release(handle)

        return list(self._devices)

    def _get_device_info(self, device):
        info_ptr = c_void_p()
        hr = GI.IGameInputDevice.getDeviceInfo(device, byref(info_ptr))

        if hr != 0 or not info_ptr.value:
            return None

        return ctypes.cast(info_ptr, ctypes.POINTER(GI.GameInputDeviceInfo)).contents

    # ------------------------------------------------------------------
    # Reading current state
    # ------------------------------------------------------------------

    def get_current_reading(self, device=None, kind=GI.GameInputKind.Gamepad | GI.GameInputKind.RawDeviceReport):
        """Return a raw IGameInputReading* (c_void_p) for `device`, or
        None if unavailable. Caller must GI.IUnknown.release() it when done."""

        reading = c_void_p()
        device_ptr = device.device if isinstance(device, GamepadDevice) else device

        hr = GI.IGameInput.getCurrentReading(self._gameinput, kind, device_ptr, byref(reading))

        if hr != 0 or not reading.value:
            return None

        return reading

    def read_gamepad_state(self, device):
        """Return a dict of the current gamepad state for `device`, or
        None if no reading is currently available."""

        reading = self.get_current_reading(device, kind=GI.GameInputKind.Gamepad)

        if reading is None:
            return None

        self._print_reading(reading)

        try:
            state = GI.GameInputGamepadState()
            success = GI.IGameInputReading.getGamepadState(reading, byref(state))

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
            GI.IUnknown.release(reading)

    def _get_reading_device_info(self, reading):
        device = c_void_p()
        GI.IGameInputReading.getDevice(reading, byref(device))

        if not device.value:
            return None

        try:
            return self._get_device_info(device)
        finally:
            GI.release(device)

    def _print_reading(self, reading):
        info = self._get_reading_device_info(reading)
        input_kind = GI.IGameInputReading.getInputKind(reading)
        kind = GI.GameInputKind(input_kind)

        print(f"Input kind: {kind}  VID=0x{info.vendorId:04X}  PID=0x{info.productId:04x}")

        if kind & GI.GameInputKind.Gamepad:
            self._print_gamepad_reading(reading)
        else:
            print(f"No printer implemented for {kind}")

    def _print_gamepad_reading(self, reading):
        """Print the high-level gamepad state"""

        state = GI.GameInputGamepadState()
        success = GI.IGameInputReading.getGamepadState(reading, byref(state))

        if not success:
            return None

        if state is not None:
            buttons = GI.GameInputGamepadButtons(state.buttons)

            print("Gamepad state:")
            print(f"  Buttons:             {buttons}")
            print(f"  A:                   {bool(buttons & GI.GameInputGamepadButtons.A)}")
            print(f"  B:                   {bool(buttons & GI.GameInputGamepadButtons.B)}")
            print(f"  X:                   {bool(buttons & GI.GameInputGamepadButtons.X)}")
            print(f"  Y:                   {bool(buttons & GI.GameInputGamepadButtons.Y)}")
            print(f"  Menu:                {bool(buttons & GI.GameInputGamepadButtons.Menu)}")
            print(f"  View:                {bool(buttons & GI.GameInputGamepadButtons.View)}")
            print(f"  DPadUp:              {bool(buttons & GI.GameInputGamepadButtons.DPadUp)}")
            print(f"  DPadDown:            {bool(buttons & GI.GameInputGamepadButtons.DPadDown)}")
            print(f"  DPadLeft:            {bool(buttons & GI.GameInputGamepadButtons.DPadLeft)}")
            print(f"  DPadRight:           {bool(buttons & GI.GameInputGamepadButtons.DPadRight)}")
            print(f"  LeftShoulder:        {bool(buttons & GI.GameInputGamepadButtons.LeftShoulder)}")
            print(f"  RightShoulder:       {bool(buttons & GI.GameInputGamepadButtons.RightShoulder)}")
            print(f"  LeftThumbstick:      {bool(buttons & GI.GameInputGamepadButtons.LeftThumbstick)}")
            print(f"  RightThumbstick:     {bool(buttons & GI.GameInputGamepadButtons.RightThumbstick)}")
            print(f"  LeftTrigger:         {state.leftTrigger:+.4f}")
            print(f"  RightTrigger:        {state.rightTrigger:+.4f}")
            print(f"  LeftThumbstickX:     {state.leftThumbstickX:+.4f}")
            print(f"  LeftThumbstickY:     {state.leftThumbstickY:+.4f}")
            print(f"  RightThumbstickX:    {state.rightThumbstickX:+.4f}")
            print(f"  RightThumbstickY:    {state.rightThumbstickY:+.4f}")
            return


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
            GI.IUnknown.release(self._gameinput)
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
