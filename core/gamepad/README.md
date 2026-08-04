### Dependencies:
* Install packages in Talon's python
    * C:\Program Files\Talon\python.exe -m pip install vgamepad

* Install HidHide to hide the physical controller
    * Add Talon's python.exe, pythonw.exe, talon.exe, talon_console.exe to whitelist
    * Devices -> Enable device hiding, select to hide the physical controller

### xinput_controller.py
Wrapper around Windows XInput DLL for reading from a physical controller.
Exposes state of the physical controller through a dataclass ControllerState.

### virtual_controller.py
Holds the instance of a virtual gamepad from vgamepad.  Polls the physical
controller and keeps the state of the virtual controller in sync.
Adds Talon user actions that allow external actors (footpedal, noise, voice commands)
to influence the state of the virtual controller.


### TODO
* Add an auto-calibration to find joystick centers and also to select the physical controller
* Should voice buttons only be available with tag user.game?
* Use packetNumber to determine if physical state has not changed instead of comparing objects
