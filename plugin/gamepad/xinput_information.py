from talon import Module, cron
from .xinput_controller import print_xinput_controllers

mod = Module()

job = None

@mod.action_class
class Actions:

    def start_print_controller_info():
        """Starts printing controller information."""
        global job
        if job is None:
            job = cron.interval("100ms", print_xinput_controllers)

    def stop_print_controller_info():
        """Stops printing controller information."""
        global job
        if job is not None:
            cron.cancel(job)
            job = None
