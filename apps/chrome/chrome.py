from talon import Context, Module, actions, app

ctx = Context()
mod = Module()

mod.apps.chrome = "app.name: Google Chrome"
mod.apps.chrome = r"""
os: windows
and app.exe: /^chrome\.exe$/i
"""
mod.apps.chrome = """
os: mac
app.bundle: com.google.Chrome
app.bundle: com.google.Chrome.canary
app.bundle: org.chromium.Chromium
"""
mod.apps.chrome = """
os: linux
app.exe: chrome
app.exe: chromium-browser
app.exe: chromium
"""
mod.apps.chrome = """
os: linux
and app.name: Google-chrome
"""

ctx.matches = r"""
app: chrome
"""


@mod.action_class
class Actions:
    def chrome_mod(key: str):
        """Press the specified key with the correct modifier key for the OS"""
        if app.platform == "mac":
            actions.key(f"cmd-{key}")
        else:
            actions.key(f"ctrl-{key}")


@ctx.action_class("user")
class UserActions:
    def tab_close_wrapper():
        actions.sleep("180ms")
        actions.app.tab_close()


@ctx.action_class("browser")
class BrowserActions:
    def show_extensions():
        actions.app.tab_open()
        actions.browser.go("chrome://extensions")


@ctx.action_class("user")
class Actions:

    def footpedal_ikkegol_dual_left_down():
        """pedal down"""
        actions.skip()

    def footpedal_ikkegol_dual_left_up():
        """pedal up"""
        actions.skip()

    def footpedal_ikkegol_dual_right_down():
        """pedal down"""
        actions.skip()

    def footpedal_ikkegol_dual_right_up():
        """pedal up"""
        actions.skip()

    def footpedal_ikkegol_single_down():
        """pedal down"""
        actions.skip()

    def footpedal_ikkegol_single_up():
        """pedal up"""
        actions.skip()

    def footpedal_olympus_left_down():
        """pedal down"""
        actions.user.mouse_scroll_up()
        actions.user.mouse_scroll_up_continuous()

    def footpedal_olympus_left_up():
        """pedal up"""
        actions.user.mouse_scroll_stop()

    def footpedal_olympus_center_down():
        """pedal down"""
        actions.skip()

    def footpedal_olympus_center_up():
        """pedal up"""
        actions.skip()

    def footpedal_olympus_right_down():
        """pedal down"""
        actions.user.mouse_scroll_down()
        actions.user.mouse_scroll_down_continuous()

    def footpedal_olympus_right_up():
        """pedal up"""
        actions.user.mouse_scroll_stop()

    def footpedal_olympus_top_down():
        """pedal down"""
        actions.skip()

    def footpedal_olympus_top_up():
        """pedal up"""
        actions.skip()
