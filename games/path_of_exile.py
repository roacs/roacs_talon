from talon import Module, Context, actions, cron
from ..core.gamepad.xinput_buttons import Button, Trigger
from .character_regexes import get_regex
import random

ctx = Context()
ctx.matches = r"""
app: PathOfExileSteam.exe
"""
ctx.tags = ["user.game"]

# Methods to press buttons in a list in sequence with a small delay between them

DELAY_TIME_MIN = 80
DELAY_TIME_MAX = 100

pedal_jobs = {}
pedal_indices = {}

def button_cycle(pedal_id, buttons):
    index = pedal_indices.get(pedal_id, 0)
    actions.user.controller_button_press(buttons[index])
    pedal_indices[pedal_id] = (index + 1) % len(buttons)

def start_button_cycle(pedal_id, buttons):
    if pedal_id in pedal_jobs:
        return

    index = 0
    actions.user.controller_button_press(buttons[index])
    pedal_indices[pedal_id] = (index + 1) % len(buttons)

    delay = random.randint(DELAY_TIME_MIN, DELAY_TIME_MAX)
    pedal_jobs[pedal_id] = cron.interval(
        f"{delay}ms",
        lambda: button_cycle(pedal_id, buttons),
    )

def stop_button_cycle(pedal_id):
    job = pedal_jobs.pop(pedal_id, None)
    if job:
        cron.cancel(job)

    pedal_indices.pop(pedal_id, None)


# Game specific actions

mod = Module()

@mod.action_class
class Actions:
    def insert_regex_name(name: str):
        """Insert a regex name"""
        actions.user.controller_button_press([Button.L3, Button.DPAD_LEFT])
        actions.sleep("50ms")
        actions.clip.set_text(get_regex(name))
        actions.edit.paste()

    def clear_filter():
        """Send vendor clear"""
        actions.user.controller_button_press([Button.L3, Button.DPAD_RIGHT])

    def special_menu_y():
        """Controller special menu"""
        actions.user.controller_button_press([Trigger.LEFT, Trigger.RIGHT, Button.Y])

    def special_menu_a():
        """Controller special menu"""
        actions.user.controller_button_press([Trigger.LEFT, Trigger.RIGHT, Button.A])

# Overriden Contextualized Actions

@ctx.action_class("user")
class Actions:

    def talon_noise_pop():
        """Talon pop noise"""
        actions.user.controller_button_press(Button.Y)
    
    def talon_noise_hiss(active: bool):
        """Talon hiss noise"""
        print(f"poe hiss {active}")
        #pass

    def parrot_noise_cluck():
        """Parrot cluck"""
        skip()

    def parrot_noise_hiss():
        """Parrot hiss"""
        skip()

    def parrot_noise_horse_click():
        """Parrot horse_click"""
        actions.user.controller_button_press(Button.Y)

    def parrot_noise_lateral_click():
        """Parrot lateral_click"""
        actions.user.controller_button_press(Button.Y)

    def parrot_noise_whistle():
        """Parrot whistle"""
        actions.user.controller_button_press(Button.A)

@ctx.action_class("user")
class Actions:

    def footpedal_ikkegol_dual_left_down():
        """pedal down"""
        actions.user.controller_button_down(Button.X)

    def footpedal_ikkegol_dual_left_up():
        """pedal up"""
        actions.user.controller_button_up(Button.X)

    def footpedal_ikkegol_dual_right_down():
        """pedal down"""
        pass

    def footpedal_ikkegol_dual_right_up():
        """pedal up"""
        pass

    def footpedal_ikkegol_single_down():
        """pedal down"""
        pass

    def footpedal_ikkegol_single_up():
        """pedal up"""
        pass

    def footpedal_olympus_left_down():
        """pedal down"""
        start_button_cycle("olympus_left", [Button.X, Button.DPAD_LEFT])

    def footpedal_olympus_left_up():
        """pedal up"""
        stop_button_cycle("olympus_left")

    def footpedal_olympus_center_down():
        """pedal down"""
        actions.key("alt:down")

    def footpedal_olympus_center_up():
        """pedal up"""
        actions.key("alt:up")

    def footpedal_olympus_right_down():
        """pedal down"""
        start_button_cycle("olympus_right", [Button.X, Button.DPAD_RIGHT])

    def footpedal_olympus_right_up():
        """pedal up"""
        stop_button_cycle("olympus_right")

    def footpedal_olympus_top_down():
        """pedal down"""
        pass

    def footpedal_olympus_top_up():
        """pedal up"""
        pass
