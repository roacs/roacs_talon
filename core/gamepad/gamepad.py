from talon import Module, app
import threading
import time
import vgamepad as vg
from inputs import get_gamepad

mod = Module()

gamepad = vg.VX360Gamepad()
gamepad.reset()
gamepad.update()

controller_state_lock = threading.Lock()
gamepad_lock = threading.Lock()

controller_active = False

controller_state = {
    "A": False,
    "B": False,
    "X": False,
    "Y": False,
    "LB": False,
    "RB": False,
    "BACK": False,
    "START": False,
    "L3": False,
    "R3": False,
    "DPAD_UP": False,
    "DPAD_DOWN": False,
    "DPAD_LEFT": False,
    "DPAD_RIGHT": False,
    "LX": 0,
    "LY": 0,
    "RX": 0,
    "RY": 0,
    "LT": 0,
    "RT": 0,
}

external_request_state = {
    "A": False,
    "B": False,
    "X": False,
    "Y": False,
    "LB": False,
    "RB": False,
    "BACK": False,
    "START": False,
    "L3": False,
    "R3": False,
    "DPAD_UP": False,
    "DPAD_DOWN": False,
    "DPAD_LEFT": False,
    "DPAD_RIGHT": False,
}

button_map = {
    "BTN_SOUTH": "A",
    "BTN_EAST": "B",
    "BTN_NORTH": "Y",
    "BTN_WEST": "X",
    "BTN_TL": "LB",
    "BTN_TR": "RB",
    "BTN_SELECT": "BACK",
    "BTN_START": "START",
    "BTN_THUMBL": "L3",
    "BTN_THUMBR": "R3",
}

virtual_button_map = {
    "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "L3": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "R3": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "DPAD_UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "DPAD_DOWN": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "DPAD_LEFT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "DPAD_RIGHT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}

def normalize_axis(value):
    return max(-32768, min(32767, value))

def update_controller_state():
    global controller_state

    try:
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
                        controller_state["DPAD_LEFT"] = event.state < 0
                        controller_state["DPAD_RIGHT"] = event.state > 0

                    elif event.code == "ABS_HAT0Y":
                        controller_state["DPAD_UP"] = event.state < 0
                        controller_state["DPAD_DOWN"] = event.state > 0

    except Exception as e:
        print("Input reader crashed:", e)
        import traceback
        traceback.print_exc()

def output_controller_state_to_virtual():
    try:
        while True:
            if controller_active:
                with controller_state_lock:
                    state = controller_state.copy()

                with gamepad_lock:
                    for name, button in virtual_button_map.items():
                        if state[name] or external_request_state[name]:
                            gamepad.press_button(button=button)
                        else:
                            gamepad.release_button(button=button)

                    gamepad.left_joystick(x_value=state["LX"], y_value=state["LY"])
                    gamepad.right_joystick(x_value=state["RX"], y_value=state["RY"])
                    gamepad.left_trigger(value=state["LT"])
                    gamepad.right_trigger(value=state["RT"])

                    gamepad.update()

            time.sleep(0.01)

    except Exception as e:
        print("Controller output crashed:", e)
        import traceback
        traceback.print_exc()

@mod.action_class
class Actions:

    def toggle_controller():
        """Toggle virtual controller passthrough."""
        global controller_active

        controller_active = not controller_active

        if controller_active:
            print("virtual controller ON")
            app.notify("Virtual controller ON")
        else:
            print("virtual controller OFF")
            app.notify("Virtual controller OFF")

    def x_button_down():
        """Hold X."""
        global external_request_state
        external_request_state["X"] = True

    def x_button_up():
        """Release X."""
        global external_request_state
        external_request_state["X"] = False
    
    def x_button_press():
        """Press X"""
        with gamepad_lock:
            gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            gamepad.update()
            time.sleep(0.05)
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            gamepad.update()

def start_threads():

    threading.Thread(
        target=update_controller_state,
        daemon=True
    ).start()

    threading.Thread(
        target=output_controller_state_to_virtual,
        daemon=True
    ).start()

start_threads()
