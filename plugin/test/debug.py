from talon import Module, cron
import time

from .joycon_hid_controller import JoyCon, get_device_ids
from .gamepad_types import print_gamepad_state

mod = Module()

_connection_job = None
_poll_job = None
_joycons = {}

def poll_controller():
    global _poll_job
    global _joycons

    disconnected = []

    for serial, joycon in list(_joycons.items()):
        if joycon.is_disconnected():
            disconnected.append(serial)
        else:
            print_gamepad_state(joycon.get_gamepad_state())

    for serial in disconnected:
        joycon = _joycons.pop(serial, None)

        if joycon is not None:
            try:
                joycon.close()
            except Exception:
                pass

    # Stop polling when there are no connected Joy-Cons.
    if not _joycons and _poll_job is not None:
        cron.cancel(_poll_job)
        _poll_job = None
        print("joycon: stopped polling")

def check_connection():
    global _poll_job
    global _joycons

    joycon_id_list = get_device_ids()

    for joycon_id in joycon_id_list:
        if joycon_id[0] is not None:
            serial = joycon_id[2]

            if serial not in _joycons:
                joycon = JoyCon(*joycon_id)
                _joycons[serial] = joycon
                print(f"joycon [{serial}]: connected")

    # Start polling when the first Joy-Con connects.
    if _joycons and _poll_job is None:
        _poll_job = cron.interval("100ms", poll_controller)
        print("joycon: started polling")


@mod.action_class
class Actions:

    def joycon_poll_start():
        """Start Joy-Con connection monitoring."""

        global _connection_job

        if _connection_job is not None:
            print("joycon: already monitoring")
            return

        check_connection()

        _connection_job = cron.interval("2s", check_connection)

        print("joycon: started connection monitoring")

    def joycon_poll_stop():
        """Stop Joy-Con connection monitoring and polling."""

        global _connection_job
        global _poll_job
        global _joycons

        if _connection_job is not None:
            cron.cancel(_connection_job)
            _connection_job = None

        if _poll_job is not None:
            cron.cancel(_poll_job)
            _poll_job = None

        for joycon in _joycons.values():
            try:
                joycon.close()
            except Exception:
                pass

        _joycons.clear()

        print("joycon: stopped")
