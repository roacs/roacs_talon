from talon import Module, app
import pygame
import threading
import time
import vgamepad as vg


mod = Module()

gamepad = vg.VX360Gamepad()
gamepad_lock = threading.Lock()

controller_active = False
x_requested = False

def controller_loop():
    try:
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("No Xbox controller found")
            return

        for i in range(pygame.joystick.get_count()):
            js = pygame.joystick.Joystick(i)
            js.init()
            print(
                i,
                js.get_name(),
                js.get_guid()
            )

        TARGET_CONTROLLER = "Xbox One".lower()
        controller = None

        for i in range(pygame.joystick.get_count()):
            js = pygame.joystick.Joystick(i)
            js.init()

            if TARGET_CONTROLLER in js.get_name().lower():
                controller = js
                break

        if controller is None:
            print("Physical controller not found")
            return
        controller.init()

        print("Using...")
        print("Controller:", controller.get_name())
        print("Axes:", controller.get_numaxes())
        print("Buttons:", controller.get_numbuttons())
        print("Hats:", controller.get_numhats())

        has_hat = controller.get_numhats() > 0

        button_map = {
            0: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            1: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            2: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            3: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            4: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            5: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            6: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            7: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            8: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            9: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
        }

        while True:
            pygame.event.pump()

            if controller_active:

                with gamepad_lock:

                    gamepad.left_joystick(
                        x_value=int(controller.get_axis(0) * 32767),
                        y_value=int(-controller.get_axis(1) * 32767),
                    )

                    gamepad.right_joystick(
                        x_value=int(controller.get_axis(2) * 32767),
                        y_value=int(-controller.get_axis(3) * 32767),
                    )

                    gamepad.left_trigger(
                        value=int((controller.get_axis(4) + 1) * 32767)
                    )

                    gamepad.right_trigger(
                        value=int((controller.get_axis(5) + 1) * 32767)
                    )

                    for index, button in button_map.items():
                        if controller.get_button(index):
                            gamepad.press_button(button=button)
                        else:
                            gamepad.release_button(button=button)

                    if has_hat:
                        hat = controller.get_hat(0)

                        gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                        gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                        gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                        gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)

                        if hat[1] > 0:
                            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)

                        elif hat[1] < 0:
                            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)

                        if hat[0] < 0:
                            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)

                        elif hat[0] > 0:
                            gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)

                    if x_requested:
                        gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
                    else:
                        gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)

                    gamepad.update()

            time.sleep(0.01)
            
    except Exception as e:
        print("Controller thread crashed:", e)
        import traceback
        traceback.print_exc()


# =====================================================
# Talon Actions
# =====================================================

@mod.action_class
class Actions:

    def toggle_controller():
        """Toggle virtual controller passthrough."""
        global controller_active

        controller_active = not controller_active

        if controller_active:
            print("virtual controller on")
            app.notify("Virtual controller ON")
        else:
            print("virtual controller off")
            app.notify("Virtual controller OFF")

    def x_button_down():
        """Request X held."""
        global x_requested
        with gamepad_lock:
            x_requested = True

    def x_button_up():
        """Release X."""
        global x_requested
        with gamepad_lock:
            x_requested = False

    def x_button_press():
        """Press X"""
        with gamepad_lock:
            gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            gamepad.update()
            time.sleep(0.05)
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
            gamepad.update()


# =====================================================
# Auto-start controller thread
# =====================================================

def start_thread():

    threading.Thread(
        target=controller_loop,
        daemon=True
    ).start()


start_thread()
