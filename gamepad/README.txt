For outputting to a virtual gamepad and reading from a physical controller
  Install packages in Talon's python
   - C:\Program Files\Talon\python.exe -m pip install vgamepad
   - C:\Program Files\Talon\python.exe -m pip install inputs

  Install HidHide to hide the physical controller
   - Add Talon's python.exe, pythonw.exe, talon.exe, talon_console.exe to whitelist
   - Devices -> Enable device hiding, select to hide the physical controller


Foot switches are set to use hidden function keys (F13-F24).  This maps those function
keys to named actions for ease of use:
  F13 - ikkegol dual twin foot switch left pedal
  F14 - ikkegol dual twin foot switch right pedal
  F15 - olympus rs31h/31n foot switch left pedal
  F16 - olympus rs31h/31n foot switch center pedal
  F17 - olympus rs31h/31n foot switch right pedal
  F18 - olympus rs31h/31n foot switch top pedal

There is an included olympus_rs31h.xml containing a template that can be loaded in 
Olympus' FTSW tool to set the pedals to the right keys.  Can't be done through their
tool GUI.

Footpedal actions and noise actions are defined in Module user actions.  For specific
behavior, override those actions in a Context in a different file.

TODO description of how the gamepad works with external + physical

TODO need a way to only enable the voice buttons when in game mode, tag?
