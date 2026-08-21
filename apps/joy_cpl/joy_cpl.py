from talon import Context, Module, actions, app

ctx = Context()
mod = Module()

mod.apps.joy_cpl = "app.name: joy cpl"
mod.apps.joy_cpl = r"""
os: windows
and win.title: /Controller.*/
"""

ctx.matches = r"""
app: joy_cpl
"""
ctx.tags = ["user.game"]
ctx.tags = ["user.voice_buttons"]
