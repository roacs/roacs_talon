from talon import Module

mod = Module()

tagList = [
    "tabs",
]
for entry in tagList:
    mod.tag(entry, f"tag to load {entry} and/or related plugins ")
