### Dependencies:
* Install packages in Talon's python
    * C:\Program Files\Talon\python.exe -m pip install vgamepad

* Install HidHide to hide the physical controller
    * Add Talon's python.exe, pythonw.exe, talon.exe, talon_console.exe to whitelist
    * Devices -> Enable device hiding, select to hide the physical controller

### xinput_controller.py
Wrapper around Windows XInput DLL for reading from a physical controller.
Exposes state of the physical controller(s) through a dataclass ControllerState.
Multiple XInput indices can be polled and their outputs merged into one returned state.
Translators are specified for each XInput index that maps XInput gamepad state into desired controller state.
This way, custom translators can be used to map things like a fight stick joystick (which is normally 
a dpad) into an approximation of an analog joystick.

### virtual_controller.py
Holds the instance of a virtual gamepad from vgamepad.  Polls the physical
controller(s) and keeps the state of the virtual controller in sync.
Adds Talon user actions that allow external actors (footpedal, noise, voice commands)
to influence the state of the virtual controller.

### xinput_information.py/.talon
Useful for identifying which xinput indices have been assigned to physical devices.
Open Talon Log and say 'print controller start'.  Press buttons on the controller and see which
state changes.

### voice_buttons.py/.talon
Using voice phrases to push buttons on the virtual controller.

### TODO
* Need to add the ability to assign an index to a physical controller automatically (perhaps
  with some kind of "press button on controller to use dialog")
* Add an auto-calibration to find joystick centers
* Use packetNumber to determine if physical state has not changed instead of comparing objects
