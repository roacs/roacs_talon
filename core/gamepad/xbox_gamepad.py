from talon import Module, app
import threading
import time
import vgamepad as vg
from inputs import get_gamepad
from .xbox_buttons import Button, Trigger

mod = Module()

gamepad = vg.VX360Gamepad()
gamepad.reset()
gamepad.update()

controller_state_lock = threading.Lock()
gamepad_lock = threading.Lock()

physical_button_state = {
    button.value: False for button in Button
}

physical_axes_state = {
    "LX": 0,
    "LY": 0,
    "RX": 0,
    "RY": 0,
    "LT": 0,
    "RT": 0,
}

external_state = {
    item.value: False for item in list(Button) + list(Trigger)
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

def normalize_axis(value):
    return max(-32768, min(32767, value))

def input_thread():
    while True:
        events = get_gamepad()

        with controller_state_lock:
            for event in events:
                if event.code in button_map:
                    physical_button_state[button_map[event.code]] = bool(event.state)
                elif event.code == "ABS_HAT0X":
                    physical_button_state[Button.DPAD_LEFT.value] = event.state < 0
                    physical_button_state[Button.DPAD_RIGHT.value] = event.state > 0
                elif event.code == "ABS_HAT0Y":
                    physical_button_state[Button.DPAD_UP.value] = event.state < 0
                    physical_button_state[Button.DPAD_DOWN.value] = event.state > 0
                elif event.code == "ABS_X":
                    physical_axes_state["LX"] = normalize_axis(event.state)
                elif event.code == "ABS_Y":
                    physical_axes_state["LY"] = normalize_axis(event.state)
                elif event.code == "ABS_RX":
                    physical_axes_state["RX"] = normalize_axis(event.state)
                elif event.code == "ABS_RY":
                    physical_axes_state["RY"] = normalize_axis(event.state)
                elif event.code == "ABS_Z":
                    physical_axes_state["LT"] = event.state
                elif event.code == "ABS_RZ":
                    physical_axes_state["RT"] = event.state


def output_thread():
    while True:
        with controller_state_lock:
            physical = physical_button_state.copy()
            external = external_state.copy()
            axes = physical_axes_state.copy()

        with gamepad_lock:
            for name, button in virtual_button_map.items():
                if physical[name] or external[name]:
                    gamepad.press_button(button)
                else:
                    gamepad.release_button(button)

            gamepad.left_joystick(axes["LX"], axes["LY"])
            gamepad.right_joystick(axes["RX"], axes["RY"])

            gamepad.left_trigger(255 if external[Trigger.LEFT.value] else axes["LT"])
            gamepad.right_trigger(255 if external[Trigger.RIGHT.value] else axes["RT"])

            gamepad.update()

    time.sleep(0.01)


@mod.action_class
class Actions:

    def controller_button_down(button: Button | Trigger):
        """Press virtual controller button."""
        external_state[button.value] = True

    def controller_button_up(button: Button | Trigger):
        """Release virtual controller button."""
        external_state[button.value] = False

    def controller_button_press(press_button: Button):
        """Press virtual controller button."""
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
