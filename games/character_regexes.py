from enum import Enum


class Character(str, Enum):
    LUMINARY_MERC_SUPPORT_329 = "luminary_merc_support_329"
    SLAYER_CYCLONE_329 = "slayer_cyclone_329"

class Category(str, Enum):
    GEM = "gem"
    VENDOR = "vendor"
    MAP = "map"

# SELECTED CHARACTER
selected_character = Character.SLAYER_CYCLONE_329

# non-character specific regexes

REGEXES = {
    "physical":
        r'"flaring|tempered|dictator|emperor|conquer|merciless|tyrannical|cruel|celebration"',
    "rog":
        r'"of all|suppress|chaos res|profane|spine bow|ivory bow|bone bow|thicket bow|grove bow|short bow|l arrow|% increased maximum life|bone ring|293|173|throwing"',
    "sword":
        r'"incision|celebration|infamy|vapouri|electrocuting|discharging|shocking|arcing|sparking|crackling|snapping"',
    #"sword":
    #    r'"incision|celebration|infamy|crystalising|entombing|polar|glaciated|frozen|freezing|frigid|icy"',
    "wand":
        r'"incision|penetrat|acclaim|renown|crystali|entomb|polar|vapour|electrocuting|discharg|flaring|tempered|razor"',
}


# character specific regexes

CHARACTER_REGEXES = {
    Character.LUMINARY_MERC_SUPPORT_329: {
        Category.GEM:
            r'"Spec.*throw|d sand$|steelsk|tblink$|p slam$|^prec|^clari|sunder$|poac|ood ra|d stone$|^prid|ty of ele|^general|autoe|^autom|^cyclone$|crate$|^faster a|lifeta|cruel|melee ph.*sup|shoc.*wa.*rt|volat.*s|pulv|infused c|^inc.*crit|arrog|^assa|mark on"',

        Category.VENDOR:
            r'"([rgb]-){2}[rgb]|-\w-|Runn|rint|me Sh"',

        Category.MAP:
            r'"!ur$|kes$|t reg" "y: r"',
    },

    Character.SLAYER_CYCLONE_329: {
        Category.GEM:
            r'"righteous f|tal focus|effica|ing damage s|scorching r|ed chan|surge s|flame link|bleed su|shield ch|arrog|haste|urity of elem|vitality|mom|sniper|skitter"',

        Category.VENDOR:
            r'"([rgb]-){2}[rgb]|-\w-|Runn|rint|me Sh"',

        Category.MAP:
            r'"!nerg|ve p|eec|a d|o bl"',
    },
}


def get_regex(category: str) -> str | None:
    cat = Category._value2member_map_.get(category)
    if cat is None:
        return REGEXES.get(category)

    return CHARACTER_REGEXES[selected_character].get(cat)
