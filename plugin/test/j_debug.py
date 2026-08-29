from talon import Module, cron

from .Joycon import JoyCon, find_joycon_ids

mod = Module()

_job = None
_joycon = None

def poll_controller():
    """Called on every cron.interval tick while polling is active."""

    if _joycon is None:
        return

    if _joycon.poll():
        print(_joycon.get_status())


@mod.action_class
class Actions:

    def joycon_poll_start():
        """Start polling the gamepad and printing its state."""
        global _job
        global _joycon

        if _joycon is None:
            ids = find_joycon_ids()
            print(ids)
            if not ids:
                print("No Joy-Cons found.")
                return

            vendor_id, product_id, serial = ids[0]
            print(f"vid:0x{vendor_id:04x} pid:0x{product_id:04x} serial:{serial}")
            _joycon = JoyCon(vendor_id, product_id, serial)

        if _joycon is None:
            print("No joy-con")
            return

        if _job is not None:
            print("joycon: already polling")
            return

        _job = cron.interval("100ms", poll_controller)
        print("joycon: started polling")

    def joycon_poll_stop():
        """Stop polling the gamepad."""

        global _job
        global _joycon

        if _joycon is not None:
            _joycon.close()
            _joycon = None

        if _job is None:
            print("joycon: not polling")
            return

        cron.cancel(_job)
        _job = None
        print("joycon: stopped polling")
