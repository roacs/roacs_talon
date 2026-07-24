from talon import Module, actions
from ..gamepad.xbox_buttons import Button, Trigger

mod = Module()

#regex_names = {
#    "gem": 
#          r"Spec.*throw|d sand$|steelsk|tblink$|p slam$|^prec|^clari|sunder$|poac|ood ra|d stone$|^prid|ty of ele|^general|autoe|^autom|^cyclone$|crate$|^faster a|lifeta|cruel|melee ph.*sup|shoc.*wa.*rt|volat.*s|pulv|infused c|^inc.*crit|arrog|^assa|mark on",
#          
#    "vendor": 
#          r"r-r-|-r-r|r-.-r|g-g-r|g-r-g|r-g-g|Runn|rint|Glint|Heav" "mac|ax|stave|armour|boot|glove",
#
#    "map": 
#          r"!gy|efl|eec|o al|non",
#}

regex_names = {
    "gem": 
          r'"righteous f|tal focus|effica|ing damage s|scorching r|ed chan|surge s|flame link|bleed su|shield ch|arrog|haste|urity of elem|vitality|mom|sniper|skitter"',
          
    "vendor": 
          r'"([rgb]-){2}[rgb]|-\w-|Runn|rint|me Sh"',

    "map": 
          r'"!gy|efl|eec|o al|non"',
}


@mod.action_class
class Actions:
    def insert_regex_name(name: str):
        """Insert a regex name"""
        actions.user.controller_button_press([Button.L3, Button.DPAD_LEFT])
        actions.sleep("50ms")
        actions.clip.set_text(regex_names[name])
        actions.edit.paste()

    def clear_filter():
        """Send vendor clear"""
        actions.user.controller_button_press([Button.L3, Button.DPAD_RIGHT])
