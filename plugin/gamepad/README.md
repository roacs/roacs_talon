### Dependencies:
* Install packages in Talon's python
    * C:\Program Files\Talon\python.exe -m pip install vgamepad

* Install HidHide to hide the physical controller(s)
    * Add Talon's python.exe, pythonw.exe, talon.exe, talon_console.exe to whitelist
    * Devices -> Enable device hiding, select to hide the physical controller

* Install Microsoft.GameInput v3 for gameinput_controller
    * https://www.nuget.org/packages/Microsoft.GameInput
    * winget install --id Microsoft.GameInput --exact

### xinput_controller.py, xinput_information.py/.talon
Wrapper around Windows XInput DLL for reading from an xinput controller.
Exposes state of the physical controller through a dataclass GamepadState.
Translators are specified for each XInput index that maps XInput gamepad state into desired controller state.
This way, custom translators can be used to map things like a fight stick joystick (which is normally 
a dpad) into an approximation of an analog joystick.
xinput_information useful for identifying which xinput indices have been assigned to physical devices.
Open Talon Log and say 'print controller start'.  Press buttons on the controller and see which
state changes.
NOTE: XInput not recommended as their indices can move around

### gameinput_controller.py, GameInput.py
Uses Microsoft GameInput API and background service to read from devices.
Exposes state of the physical controller through a dataclass GamepadState.
Allows selecting the device by VID/PID. Currently only works with Gamepad type.

### joycon_hid_controller.py
Wrapper around joycon, mostly taken from tocoteron/joycon-python.
Exposes state of the physical controller through a dataclass GamepadState.
NOTE: The joycon implementation uses a background thread to keep the state up-to-date.
NOTE: It sucks and it is laggy.

### virtual_controller.py
Holds the instance of a virtual gamepad from vgamepad.  Polls the physical
controller(s) and keeps the state of the virtual controller in sync.
Multiple physical devices can be polled and their outputs merged into one returned state.
Adds Talon user actions that allow external actors (footpedal, noise, voice commands)
to influence the state of the virtual controller.
Translations and Stick calibrations can be applied to each physical device before being
merged into the virtual state.

### voice_buttons.py/.talon
Using voice phrases to push buttons on the virtual controller.

### TODO
* Need the ability to add physical devices to be used by the virtual controller automatically
  Perhaps with a GUI where you press buttons on the device to help select it
* Add an auto-calibration to find joystick centers
* Use packetNumber to determine if physical state has not changed instead of comparing objects
* Fix Joy-Con's, or maybe get rid of them and rely on something like DS4Windows to turn them
  into something easier.
* goal: 
  - May need to abstract the controller buttons to east/west/north/south to use nintendo/playstation
