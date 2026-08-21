### Dependencies:
* Install packages in Talon's python
    * C:\Program Files\Talon\python.exe -m pip install vgamepad

* Install HidHide to hide the physical controller
    * Add Talon's python.exe, pythonw.exe, talon.exe, talon_console.exe to whitelist
    * Devices -> Enable device hiding, select to hide the physical controller

### xinput_controller.py
Wrapper around Windows XInput DLL for reading from a physical controller.
Exposes state of the physical controller through a dataclass ControllerState.
Multiple indices can be polled and their outputs merged into one returned state.

### virtual_controller.py
Holds the instance of a virtual gamepad from vgamepad.  Polls the physical
controller and keeps the state of the virtual controller in sync.
Adds Talon user actions that allow external actors (footpedal, noise, voice commands)
to influence the state of the virtual controller.

### xinput_information.py/.talon
Useful for identifying which xinput indices to pick.
Open Talon Log and say 'print controller start'.  Press buttons on the controller and see which
state changes.

### voice_buttons.py/.talon
Using voice phrases to push buttons on the virtual controller.

### TODO
* Add ability to display what controllers are which and select which ones to use for the
  virtual controller
* Add an auto-calibration to find joystick centers and also to select the physical controller
* Use packetNumber to determine if physical state has not changed instead of comparing objects
