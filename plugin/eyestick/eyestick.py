from talon import Module, actions, cron, ui
from talon.canvas import Canvas, MouseEvent
from skia import Canvas as SkiaCanvas
import math

mod = Module()
canvas: Canvas | None = None
position_job = None

def on_draw(c: SkiaCanvas):
    c.paint.color = "fffafa20"
    c.paint.style = c.paint.Style.STROKE
    c.paint.stroke_width = 2

    screen = ui.main_screen()
    x = screen.rect.center.x
    y = screen.rect.center.y
    c.draw_circle(x, y, 10)


def show():
    global canvas
    canvas = Canvas.from_rect(ui.main_screen().rect)
    canvas.draggable = False
    canvas.blocks_mouse = False
    canvas.focused = False
    canvas.cursor_visible = False
    canvas.register("draw", on_draw)


def hide():
    global canvas
    if canvas is not None:
        canvas.unregister("draw", on_draw)
        canvas.close()
        canvas = None


@mod.action_class
class Actions:
    def eyestick_debug_start():
        """ debug start """
        global position_job

        actions.tracking.control_toggle(True)

        if canvas is None:
            show()
            
        if position_job is None:
            position_job = cron.interval("100ms", update_eye_stick)

    def eyestick_debug_stop():
        """ debug stop """
        global position_job

        actions.tracking.control_toggle(False)
        actions.user.controller_left_stick_clear()

        if canvas is not None:
            hide()

        if position_job is not None:
            cron.cancel(position_job)
            position_job = None


MAX_STICK = 32767
DEADZONE = 20
STICK_RADIUS = 100

def update_eye_stick():
    stick_x, stick_y = cursor_to_stick()

    print(f"Left stick: X={stick_x}, Y={stick_y}")

    actions.user.controller_left_stick(stick_x, stick_y)

def cursor_to_stick():
    rect = ui.main_screen().rect

    center_x = rect.center.x
    center_y = rect.center.y - 50

    mouse_x = actions.mouse_x()
    mouse_y = actions.mouse_y()

    print(f"Mouse: X={mouse_x}, Y={mouse_y}")

    # Offset from screen center.
    dx = mouse_x - center_x
    dy = center_y - mouse_y

    distance = math.sqrt(dx * dx + dy * dy)

    # Inside deadzone
    if distance <= DEADZONE:
        return 0, 0

    # Direction from center
    direction_x = dx / distance
    direction_y = dy / distance

    # Rescale distance:
    # 20 px -> 0
    # 100 px -> 1
    magnitude = (distance - DEADZONE) / (STICK_RADIUS - DEADZONE)

    # Clamp at maximum
    magnitude = min(magnitude, 1.0)

    stick_x = round(direction_x * magnitude * MAX_STICK)
    stick_y = round(direction_y * magnitude * MAX_STICK)

    return stick_x, stick_y
