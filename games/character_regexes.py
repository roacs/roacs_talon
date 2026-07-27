from enum import Enum


class Character(str, Enum):
    LUMINARY_MERC_SUPPORT_329 = "luminary_merc_support_329"
    SLAYER_CYCLONE_329 = "slayer_cyclone_329"

class Category(str, Enum):
    GEM = "gem"
    VENDOR = "vendor"
    MAP = "map"
    CRAFT = "craft"


# SELECTED CHARACTER
selected_character = Character.SLAYER_CYCLONE_329


REGEXES = {
    Character.LUMINARY_MERC_SUPPORT_329: {
        Category.GEM:
            r'"Spec.*throw|d sand$|steelsk|tblink$|p slam$|^prec|^clari|sunder$|poac|ood ra|d stone$|^prid|ty of ele|^general|autoe|^autom|^cyclone$|crate$|^faster a|lifeta|cruel|melee ph.*sup|shoc.*wa.*rt|volat.*s|pulv|infused c|^inc.*crit|arrog|^assa|mark on"',

        Category.VENDOR:
            r'"([rgb]-){2}[rgb]|-\w-|Runn|rint|me Sh"',

        Category.MAP:
            r'"!gy|efl|eec|o al|non"',

        Category.CRAFT:
            r'"flaring|tempered|razor|dictator|emperor|conquer|merciless|tyrannical|cruel|infamy|celebration"'
    },

    Character.SLAYER_CYCLONE_329: {
        Category.GEM:
            r'"righteous f|tal focus|effica|ing damage s|scorching r|ed chan|surge s|flame link|bleed su|shield ch|arrog|haste|urity of elem|vitality|mom|sniper|skitter"',

        Category.VENDOR:
            r'"([rgb]-){2}[rgb]|-\w-|Runn|rint|me Sh"',

        Category.MAP:
            r'"!gy|efl|eec|o al|non"',

        Category.CRAFT:
            r'"flaring|tempered|razor|dictator|emperor|conquer|merciless|tyrannical|cruel|infamy|celebration"'
    },
}


def get_regex(category: str) -> str | None:
    cat = Category._value2member_map_.get(category)
    if cat is None:
        return None

    return REGEXES[selected_character].get(cat)
