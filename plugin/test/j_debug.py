from talon import Module, cron

from .Joycon import JoyCon, find_joycon_ids
from .gamepad_types import print_gamepad_state

mod = Module()

_connection_job = None
_poll_job = None
_joycons = {}


def poll_controller():
    """Called every 100ms while Joy-Cons are connected."""

    global _poll_job

    disconnected = []

    for serial, joycon in list(_joycons.items()):
        try:
            if joycon.poll():
                print(f"joycon [{serial}]: ", end="")
                print_gamepad_state(joycon.get_gamepad_state())

        except Exception as e:
            print(f"joycon [{serial}]: disconnected: {e}")
            disconnected.append(serial)

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
    """Look for new Joy-Cons and connect them."""

    global _poll_job

    for vendor_id, product_id, serial in find_joycon_ids():

        if serial in _joycons:
            continue

        print(
            f"joycon: found new Joy-Con "
            f"vid:0x{vendor_id:04x} "
            f"pid:0x{product_id:04x} "
            f"serial:{serial}"
        )

        try:
            joycon = JoyCon(vendor_id, product_id, serial)
            _joycons[serial] = joycon

            print(f"joycon [{serial}]: connected")

        except Exception as e:
            print(f"joycon [{serial}]: failed to connect: {e}")

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
