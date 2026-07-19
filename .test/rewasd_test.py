from talon import noise, actions
import sys
import time

def on_pop(active):
    print("pop sending f13")
    actions.key("f13:down")
    time.sleep(0.05)
    actions.key("f13:up")

noise.register("pop", on_pop)

