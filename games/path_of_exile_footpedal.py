from talon import Context, actions, cron
from ..gamepad.xbox_buttons import Button, Trigger
from functools import partial
import random

ctx = Context()
ctx.matches = r"""
app: PathOfExileSteam.exe
app: Google Chrome
"""

# Pressing buttons in a list in a cycle while job is running

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

def start_button_cycle(pedal_id, buttons, delay_range=(120, 160)):
    if pedal_jobs.get(pedal_id) is None:
        button_list_cycle_step(pedal_id, buttons, delay_range, index=0)

def stop_button_cycle(pedal_id):
    job = pedal_jobs.get(pedal_id)
    if job is not None:
        cron.cancel(job)
        pedal_jobs[pedal_id] = None


# Actions

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
        start_button_cycle("olympus_left", [Button.X, Button.DPAD_UP])

    def footpedal_olympus_left_up():
        """pedal up"""
        stop_button_cycle("olympus_left")

    def footpedal_olympus_center_down():
        """pedal down"""
        pass

    def footpedal_olympus_center_up():
        """pedal up"""
        pass

    def footpedal_olympus_right_down():
        """pedal down"""
        start_button_cycle("olympus_right", [Button.X, Button.DPAD_DOWN])

    def footpedal_olympus_right_up():
        """pedal up"""
        stop_button_cycle("olympus_right")

    def footpedal_olympus_top_down():
        """pedal down"""
        pass

    def footpedal_olympus_top_up():
        """pedal up"""
        pass
