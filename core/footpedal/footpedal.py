from talon import Module, actions, ui

mod = Module()

@mod.action_class
class Actions:

    def footpedal_ikkegol_dual_left_down():
        """pedal down"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_ikkegol_dual_left_up():
        """pedal up"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_ikkegol_dual_right_down():
        """pedal down"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_ikkegol_dual_right_up():
        """pedal up"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_olympus_left_down():
        """pedal down"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_olympus_left_up():
        """pedal up"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_olympus_center_down():
        """pedal down"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_olympus_center_up():
        """pedal up"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_olympus_right_down():
        """pedal down"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_olympus_right_up():
        """pedal up"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_olympus_top_down():
        """pedal down"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

    def footpedal_olympus_top_up():
        """pedal up"""
        print(f"footpedal called with no context override in {ui.active_app().name}")

