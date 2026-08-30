import time
import hid
from .gamepad_types import Button, Trigger, Stick, GamepadState


# ============================================================================
# Constants
# ============================================================================

NINTENDO_VENDOR_ID = 0x057E
JOYCON_L_PRODUCT_ID = 0x2006
JOYCON_R_PRODUCT_ID = 0x2007
JOYCON_PRODUCT_IDS = (JOYCON_L_PRODUCT_ID, JOYCON_R_PRODUCT_ID)

_STANDARD_REPORT_ID = 0x30
_STANDARD_REPORT_SIZE = 49
_SUBCOMMAND_REPLY_REPORT_ID = 0x21

# Rumble is required framing on every output report even when unused;
_NEUTRAL_RUMBLE_DATA = b"\x00\x01\x40\x40\x00\x01\x40\x40"

def find_joycon_ids(product_id=None):
    """Return a list of (vendor_id, product_id, serial) for connected
    Joy-Cons. Pass product_id=JOYCON_L_PRODUCT_ID or
    JOYCON_R_PRODUCT_ID to filter to one side."""

    wanted = (product_id,) if product_id is not None else JOYCON_PRODUCT_IDS

    return [
        (entry["vendor_id"], entry["product_id"], entry.get("serial_number"))
        for entry in hid.enumerate(NINTENDO_VENDOR_ID, 0)
        if entry["product_id"] in wanted
    ]


def _int16_le(low_byte, high_byte):
    value = (high_byte << 8) | low_byte
    return value if value < 0x8000 else value - 0x10000


class JoyCon:
    """A connected Joy-Con, Call poll() before reading any get_*() method to
    refresh cached state"""

    def __init__(self, vendor_id, product_id, serial=None):
        if vendor_id != NINTENDO_VENDOR_ID:
            raise ValueError(f"vendor_id is invalid: {vendor_id!r}")
        if product_id not in JOYCON_PRODUCT_IDS:
            raise ValueError(f"product_id is invalid: {product_id!r}")

        self.vendor_id = vendor_id
        self.product_id = product_id
        self.serial = serial

        self._report = bytes(_STANDARD_REPORT_SIZE)
        self._packet_number = 0

        self._accel_offset = (0, 0, 0)
        self._accel_coeff = (1.0, 1.0, 1.0)
        self._gyro_offset = (0, 0, 0)
        self._gyro_coeff = (1.0, 1.0, 1.0)

        self._device = hid.device()
        self._device.open(vendor_id, product_id, serial)

        self._read_calibration()
        self._enable_standard_reporting()

    def close(self):
        if getattr(self, "_device", None) is not None:
            self._device.close()
            self._device = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def is_left(self):
        return self.product_id == JOYCON_L_PRODUCT_ID

    def is_right(self):
        return self.product_id == JOYCON_R_PRODUCT_ID

    # ------------------------------------------------------------------
    # Low-level HID I/O
    # ------------------------------------------------------------------

    def _read_report(self, timeout_ms):
        data = self._device.read(_STANDARD_REPORT_SIZE, timeout_ms)
        return bytes(data) if data else None

    def _write_report(self, command, subcommand, argument):
        payload = b"".join([
            command,
            self._packet_number.to_bytes(1, "little"),
            _NEUTRAL_RUMBLE_DATA,
            subcommand,
            argument,
        ])
        self._device.write(payload)
        self._packet_number = (self._packet_number + 1) & 0xF

    def _send_subcommand(self, subcommand, argument, timeout_ms=100):
        """Send a subcommand and block briefly for its 0x21 reply. This
        is the one place we still wait synchronously -- it only happens
        during setup (calibration read, enabling standard reporting),
        never during regular polling."""

        self._write_report(b"\x01", subcommand, argument)

        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            report = self._read_report(timeout_ms=int((deadline - time.monotonic()) * 1000) or 1)
            if report and report[0] == _SUBCOMMAND_REPLY_REPORT_ID:
                ack = bool(report[13] & 0x80)
                return ack, report[13:]

        raise IOError(f"No reply to subcommand {subcommand!r} within {timeout_ms}ms")

    def _spi_flash_read(self, address, size):
        assert size <= 0x1D
        argument = address.to_bytes(4, "little") + size.to_bytes(1, "little")
        ack, data = self._send_subcommand(b"\x10", argument)

        if not ack:
            raise IOError(f"SPI read @ {address:#06x} was NACKed")
        if data[:2] != b"\x90\x10":
            raise IOError("Unexpected SPI read reply header")

        return data[7:7 + size]

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _read_calibration(self):
        color = self._spi_flash_read(0x6050, 6)
        self.color_body = tuple(color[:3])
        self.color_button = tuple(color[3:])

        has_user_calibration = self._spi_flash_read(0x8026, 2) == b"\xB2\xA1"
        imu_cal = self._spi_flash_read(0x8028 if has_user_calibration else 0x6020, 24)

        self._accel_offset = tuple(_int16_le(imu_cal[i], imu_cal[i + 1]) for i in (0, 2, 4))
        accel_raw_coeff = tuple(_int16_le(imu_cal[i], imu_cal[i + 1]) for i in (6, 8, 10))
        self._accel_coeff = tuple(0x4000 / c if c != 0x4000 else 1.0 for c in accel_raw_coeff)

        self._gyro_offset = tuple(_int16_le(imu_cal[i], imu_cal[i + 1]) for i in (12, 14, 16))
        gyro_raw_coeff = tuple(_int16_le(imu_cal[i], imu_cal[i + 1]) for i in (18, 20, 22))
        self._gyro_coeff = tuple(0x343B / c if c != 0x343B else 1.0 for c in gyro_raw_coeff)

    def _enable_standard_reporting(self):
        # Enable the 6-axis IMU.
        self._write_report(b"\x01", b"\x40", b"\x01")
        time.sleep(0.02)
        # Switch to standard full input reports (0x30: buttons, sticks, IMU).
        self._write_report(b"\x01", b"\x03", b"\x30")
        time.sleep(0.02)

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def poll(self, timeout_ms=0, max_drain=8):
        """Refresh cached state from the HID queue without blocking
        (beyond `timeout_ms`, which defaults to non-blocking).

        Drains up to `max_drain` pending reports so a poll after a gap
        (e.g. a slow cron tick) picks up the freshest data rather than
        the oldest queued one, and keeps only the last standard (0x30)
        report seen. Safe to call as often as you like -- if nothing is
        queued it returns False immediately.
        """

        updated = False

        for _ in range(max_drain):
            report = self._read_report(timeout_ms)
            if report is None:
                break
            if report[0] == _STANDARD_REPORT_ID and len(report) >= _STANDARD_REPORT_SIZE:
                self._report = report
                updated = True

        return updated

    # ------------------------------------------------------------------
    # Cached-state accessors (reflect whatever the last poll() saw)
    # ------------------------------------------------------------------

    def _bits(self, byte_offset, bit_offset, bit_count):
        return (self._report[byte_offset] >> bit_offset) & ((1 << bit_count) - 1)

    def get_battery_charging(self):
        return self._bits(2, 4, 1)

    def get_battery_level(self):
        return self._bits(2, 5, 3)

    # Right-side / shared buttons (byte 3: Y X B A SR SL R ZR)
    def get_button_y(self):
        return self._bits(3, 0, 1)

    def get_button_x(self):
        return self._bits(3, 1, 1)

    def get_button_b(self):
        return self._bits(3, 2, 1)

    def get_button_a(self):
        return self._bits(3, 3, 1)

    def get_button_right_sr(self):
        return self._bits(3, 4, 1)

    def get_button_right_sl(self):
        return self._bits(3, 5, 1)

    def get_button_r(self):
        return self._bits(3, 6, 1)

    def get_button_zr(self):
        return self._bits(3, 7, 1)

    # Shared buttons (byte 4: Minus Plus RStick LStick Home Capture - ChargingGrip)
    def get_button_minus(self):
        return self._bits(4, 0, 1)

    def get_button_plus(self):
        return self._bits(4, 1, 1)

    def get_button_right_stick(self):
        return self._bits(4, 2, 1)

    def get_button_left_stick(self):
        return self._bits(4, 3, 1)

    def get_button_home(self):
        return self._bits(4, 4, 1)

    def get_button_capture(self):
        return self._bits(4, 5, 1)

    def get_button_charging_grip(self):
        return self._bits(4, 7, 1)

    # Left-side buttons / d-pad (byte 5: Down Up Right Left SR SL L ZL)
    def get_button_down(self):
        return self._bits(5, 0, 1)

    def get_button_up(self):
        return self._bits(5, 1, 1)

    def get_button_right(self):
        return self._bits(5, 2, 1)

    def get_button_left(self):
        return self._bits(5, 3, 1)

    def get_button_left_sr(self):
        return self._bits(5, 4, 1)

    def get_button_left_sl(self):
        return self._bits(5, 5, 1)

    def get_button_l(self):
        return self._bits(5, 6, 1)

    def get_button_zl(self):
        return self._bits(5, 7, 1)

    # Analog sticks: 12-bit values packed across 3 bytes each.
    def get_stick_left_horizontal(self):
        return self._bits(6, 0, 8) | (self._bits(7, 0, 4) << 8)

    def get_stick_left_vertical(self):
        return self._bits(7, 4, 4) | (self._bits(8, 0, 8) << 4)

    def get_stick_right_horizontal(self):
        return self._bits(9, 0, 8) | (self._bits(10, 0, 4) << 8)

    def get_stick_right_vertical(self):
        return self._bits(10, 4, 4) | (self._bits(11, 0, 8) << 4)

    # IMU: 3 samples per report, 12 bytes each, starting at byte 13.
    def get_accel(self, sample_index=0):
        base = 13 + sample_index * 12
        x = _int16_le(self._report[base], self._report[base + 1])
        y = _int16_le(self._report[base + 2], self._report[base + 3])
        z = _int16_le(self._report[base + 4], self._report[base + 5])
        return (
            (x - self._accel_offset[0]) * self._accel_coeff[0],
            (y - self._accel_offset[1]) * self._accel_coeff[1],
            (z - self._accel_offset[2]) * self._accel_coeff[2],
        )

    def get_gyro(self, sample_index=0):
        base = 13 + sample_index * 12 + 6
        x = _int16_le(self._report[base], self._report[base + 1])
        y = _int16_le(self._report[base + 2], self._report[base + 3])
        z = _int16_le(self._report[base + 4], self._report[base + 5])
        return (
            (x - self._gyro_offset[0]) * self._gyro_coeff[0],
            (y - self._gyro_offset[1]) * self._gyro_coeff[1],
            (z - self._gyro_offset[2]) * self._gyro_coeff[2],
        )

    def get_status(self):
        status = {
            "battery": {
                "charging": self.get_battery_charging(),
                "level": self.get_battery_level(),
            },
            "buttons": {},
            "sticks": {},
            "accel": self.get_accel(),
            "gyro": self.get_gyro(),
        }

        if self.is_left():
            status["buttons"] = {
                "minus": self.get_button_minus(),
                "left_stick": self.get_button_left_stick(),
                "capture": self.get_button_capture(),
                "down": self.get_button_down(),
                "up": self.get_button_up(),
                "right": self.get_button_right(),
                "left": self.get_button_left(),
                "left_sr": self.get_button_left_sr(),
                "left_sl": self.get_button_left_sl(),
                "l": self.get_button_l(),
                "zl": self.get_button_zl(),
            }

            status["sticks"] = {
                "left": {
                    "horizontal": self.get_stick_left_horizontal(),
                    "vertical": self.get_stick_left_vertical(),
                },
            }

        elif self.is_right():
            status["buttons"] = {
                "y": self.get_button_y(),
                "x": self.get_button_x(),
                "b": self.get_button_b(),
                "a": self.get_button_a(),
                "right_sr": self.get_button_right_sr(),
                "right_sl": self.get_button_right_sl(),
                "r": self.get_button_r(),
                "zr": self.get_button_zr(),
                "plus": self.get_button_plus(),
                "right_stick": self.get_button_right_stick(),
                "home": self.get_button_home(),
                "charging_grip": self.get_button_charging_grip(),
            }

            status["sticks"] = {
                "right": {
                    "horizontal": self.get_stick_right_horizontal(),
                    "vertical": self.get_stick_right_vertical(),
                },
            }

        return status

    # ------------------------------------------------------------------
    # Translation to GamepadState
    # ------------------------------------------------------------------

    def _scale_stick(self, value):
        return round(Stick.min_value() + value * (Stick.max_value() - Stick.min_value()) / 4095)

    def get_gamepad_state(self):
        if self.is_left():
            return GamepadState(
                buttons={
                    Button.DPAD_UP: bool(self.get_button_up()),
                    Button.DPAD_DOWN: bool(self.get_button_down()),
                    Button.DPAD_LEFT: bool(self.get_button_left()),
                    Button.DPAD_RIGHT: bool(self.get_button_right()),
                    Button.L3: bool(self.get_button_left_stick()),
                    Button.LB: bool(self.get_button_l()),
                    Button.BACK: bool(self.get_button_minus()),
                },
                sticks={
                    Stick.LX: self._scale_stick(self.get_stick_left_horizontal()),
                    Stick.LY: self._scale_stick(self.get_stick_left_vertical()),
                },
                triggers={
                    Trigger.LEFT: Trigger.max_value() if self.get_button_zl() else Trigger.min_value(),
                }
            )

        if self.is_right():
            return GamepadState(
                buttons={
                    Button.A: bool(self.get_button_a()),
                    Button.B: bool(self.get_button_b()),
                    Button.X: bool(self.get_button_x()),
                    Button.Y: bool(self.get_button_y()),
                    Button.R3: bool(self.get_button_right_stick()),
                    Button.RB: bool(self.get_button_r()),
                    Button.START: bool(self.get_button_plus()),
                },
                sticks={
                    Stick.RX: self._scale_stick(self.get_stick_right_horizontal()),
                    Stick.RY: self._scale_stick(self.get_stick_right_vertical()),
                },
                triggers={
                    Trigger.RIGHT: Trigger.max_value() if self.get_button_zr() else Trigger.min_value(),
                }
            )

        return GamepadState()


    # ------------------------------------------------------------------
    # Output (player LED)
    # ------------------------------------------------------------------

    def set_player_lamp(self, pattern):
        self._write_report(b"\x01", b"\x30", pattern.to_bytes(1, "little"))

