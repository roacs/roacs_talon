from talon import Module, app
import threading
import time
import vgamepad as vg
from inputs import get_gamepad
from .xbox_buttons import Button
from .game_layouts import layouts

mod = Module()

gamepad = vg.VX360Gamepad()
gamepad.reset()
gamepad.update()

controller_state_lock = threading.Lock()
gamepad_lock = threading.Lock()

current_layout = "default"

controller_state = {
    Button.A.value: False,
    Button.B.value: False,
    Button.X.value: False,
    Button.Y.value: False,
    Button.LB.value: False,
    Button.RB.value: False,
    Button.BACK.value: False,
    Button.START.value: False,
    Button.L3.value: False,
    Button.R3.value: False,
    Button.DPAD_UP.value: False,
    Button.DPAD_DOWN.value: False,
    Button.DPAD_LEFT.value: False,
    Button.DPAD_RIGHT.value: False,
    "LX": 0,
    "LY": 0,
    "RX": 0,
    "RY": 0,
    "LT": 0,
    "RT": 0,
}

external_request_state = {
    button.value: False
    for button in Button
}

button_map = {
    "BTN_SOUTH": Button.A.value,
    "BTN_EAST": Button.B.value,
    "BTN_WEST": Button.X.value,
    "BTN_NORTH": Button.Y.value,
    "BTN_TL": Button.LB.value,
    "BTN_TR": Button.RB.value,
    "BTN_SELECT": Button.BACK.value,
    "BTN_START": Button.START.value,
    "BTN_THUMBL": Button.L3.value,
    "BTN_THUMBR": Button.R3.value,
}

virtual_button_map = {
    Button.A.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    Button.B.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    Button.X.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    Button.Y.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    Button.LB.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    Button.RB.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    Button.BACK.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    Button.START.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    Button.L3.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    Button.R3.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    Button.DPAD_UP.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    Button.DPAD_DOWN.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    Button.DPAD_LEFT.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    Button.DPAD_RIGHT.value: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}

def normalize_axis(value):
    return max(-32768, min(32767, value))

def input_thread():

    while True:
        events = get_gamepad()

        with controller_state_lock:

            for event in events:

                if event.code in button_map:
                    controller_state[button_map[event.code]] = bool(event.state)
                elif event.code == "ABS_X":
                    controller_state["LX"] = normalize_axis(event.state)
                elif event.code == "ABS_Y":
                    controller_state["LY"] = normalize_axis(event.state)
                elif event.code == "ABS_RX":
                    controller_state["RX"] = normalize_axis(event.state)
                elif event.code == "ABS_RY":
                    controller_state["RY"] = normalize_axis(event.state)
                elif event.code == "ABS_Z":
                    controller_state["LT"] = event.state
                elif event.code == "ABS_RZ":
                    controller_state["RT"] = event.state
                elif event.code == "ABS_HAT0X":
                    controller_state[Button.DPAD_LEFT.value] = event.state < 0
                    controller_state[Button.DPAD_RIGHT.value] = event.state > 0
                elif event.code == "ABS_HAT0Y":
                    controller_state[Button.DPAD_UP.value] = event.state < 0
                    controller_state[Button.DPAD_DOWN.value] = event.state > 0

def output_thread():

    while True:
        with controller_state_lock:
            state = controller_state.copy()

        with gamepad_lock:

            for name, button in virtual_button_map.items():

                if state[name] or external_request_state[name]:
                    gamepad.press_button(button)
                else:
                    gamepad.release_button(button)

            gamepad.left_joystick(
                x_value=state["LX"],
                y_value=state["LY"],
            )

            gamepad.right_joystick(
                x_value=state["RX"],
                y_value=state["RY"],
            )

            gamepad.left_trigger(state["LT"])
            gamepad.right_trigger(state["RT"])

            gamepad.update()

        time.sleep(0.01)

@mod.action_class
class Actions:

    def controller_input_down(name: str):
        """Press mapped virtual button."""
        button = layouts[current_layout].get(name)

        if button:
            external_request_state[button.value] = True

    def controller_input_up(name: str):
        """Release mapped virtual button."""
        button = layouts[current_layout].get(name)

        if button:
            external_request_state[button.value] = False

    def controller_set_layout(name: str):
        """Change controller layout."""
        global current_layout

        if name in layouts:
            current_layout = name
            app.notify("Layout: " + name)

    def controller_press_button(press_button: Button):
        """Press Button"""
        with gamepad_lock:
            gamepad.press_button(button=virtual_button_map.get(press_button.value))
            gamepad.update()
            time.sleep(0.05)
            gamepad.release_button(button=virtual_button_map.get(press_button.value))
            gamepad.update()

threading.Thread(
    target=input_thread,
    daemon=True
).start()

threading.Thread(
    target=output_thread,
    daemon=True
).start()
