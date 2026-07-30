from talon import Module, Context, actions, cron
from ..core.gamepad.xbox_buttons import Button, Trigger
from .character_regexes import get_regex
from functools import partial
import random

ctx = Context()
ctx.matches = r"""
app: PathOfExileSteam.exe
"""
ctx.tags = ["user.game"]

# Helper functions to press buttons in a list in sequence with a small delay between them
# TODO just make this simple and actions.sleep between buttons

DELAY_TIME_MIN=120
DELAY_TIME_MAX=150

pedal_jobs = {}

def button_list_cycle_step(pedal_id, buttons, delay_range, index):
    global pedal_jobs

    actions.user.controller_button_press(buttons[index])

    next_index = (index + 1) % len(buttons)
    delay_ms = random.randint(*delay_range)

    pedal_jobs[pedal_id] = cron.after(
        f"{delay_ms}ms",
        partial(button_list_cycle_step, pedal_id, buttons, delay_range, next_index)
    )

def start_button_cycle(pedal_id, buttons, delay_range=(DELAY_TIME_MIN, DELAY_TIME_MAX)):
    if pedal_jobs.get(pedal_id) is None:
        button_list_cycle_step(pedal_id, buttons, delay_range, index=0)

def stop_button_cycle(pedal_id):
    job = pedal_jobs.get(pedal_id)
    if job is not None:
        cron.cancel(job)
        pedal_jobs[pedal_id] = None

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

# Overriden Contextualized Actions

@ctx.action_class("user")
class Actions:

    def noise_talon_pop():
        """Talon pop noise"""
        actions.user.controller_button_press(Button.Y)
    
    def noise_talon_hiss():
        """Talon hiss noise"""
        pass

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
