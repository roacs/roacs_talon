For outputting to a virtual gamepad and reading from a physical controller
  Install packages in Talon's python
   - C:\Program Files\Talon\python.exe -m pip install vgamepad
   - C:\Program Files\Talon\python.exe -m pip install inputs

  Install HidHide to hide the physical controller
   - Add Talon's python.exe, pythonw.exe, talon.exe, talon_console.exe to whitelist
   - Devices -> Enable device hiding, select to hide the physical controller


TODO description of footpedal setup and noise setup
external + physical gamepad into virtual gamepad
abstraction layer to map actions to enumerated externals (foot, noise_pop, etc.)


create a loadout class where we can define action(s) for an enumerated list of things
  FootPedal.F13 down -> actions.user.controller_button_down(Button.X),
  FootPedal.F13 up   -> actions.user.controller_button_up(Button.X),
  Noise.Pop -> actions.user.controller_press_button(Button.X),
  Noise.Hiss -> mouse click
  Noise.Click -> {multiple actions... hold LT and press X}
  etc.
}
noise.py and footpedal.py would import the loadout and perform the action(s) of the current loadout
noise.py would define an enum of the available noises
footpedal.py would define an enum of the available footpedal actions
this is so we can define actions other than gamepad, like mouse/keyboard actions on a pop
