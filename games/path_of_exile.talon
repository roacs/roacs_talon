app: PathOfExileSteam.exe
tag: user.game
-
# Vendor
vendor gem : user.insert_regex_name("gem")
vendor map : user.insert_regex_name("map")
vendor gear : user.insert_regex_name("vendor")
vendor rog : user.insert_regex_name("rog")
vendor clear : user.clear_filter()

# Craft
vendor craft physical : user.insert_regex_name("physical")
vendor craft sword : user.insert_regex_name("merc_sword")
vendor craft wand : user.insert_regex_name("merc_wand")
vendor craft dagger : user.insert_regex_name("merc_dagger")
vendor craft bow : user.insert_regex_name("merc_bow")

vendor boat : user.insert_regex_name("boat")
