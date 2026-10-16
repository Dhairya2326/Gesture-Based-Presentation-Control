"""
Unit tests for the PresentationController class (Week 7).
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from src.presentation.controller import (
    PresentationController,
    TargetProfile,
    ControllerMode,
    PROFILE_KEYMAPS,
)
from src.processing.gesture_recognizer import GestureType, GestureState


class TestPresentationController(unittest.TestCase):
    """Test suite for presentation action dispatching and OS keystroke mapping."""

    def setUp(self):
        self.controller = PresentationController(
            cooldown_seconds=0.5,
            mode=ControllerMode.SIMULATION,
            profile=TargetProfile.POWERPOINT,
            total_slides=10,
        )

    def test_initial_state(self):
        """Test default controller state."""
        self.assertTrue(self.controller.is_enabled)
        self.assertEqual(self.controller.cooldown_seconds, 0.5)
        self.assertEqual(self.controller.mode, ControllerMode.SIMULATION)
        self.assertEqual(self.controller.profile, TargetProfile.POWERPOINT)
        self.assertEqual(self.controller.current_slide, 1)
        self.assertEqual(self.controller.total_slides, 10)

    def test_enable_disable_toggle(self):
        """Test active state toggling."""
        self.controller.disable()
        self.assertFalse(self.controller.is_enabled)
        self.controller.enable()
        self.assertTrue(self.controller.is_enabled)
        result = self.controller.toggle()
        self.assertFalse(result)
        self.assertFalse(self.controller.is_enabled)

    def test_set_profile(self):
        """Test switching presentation profiles."""
        self.controller.set_profile(TargetProfile.GOOGLE_SLIDES)
        self.assertEqual(self.controller.profile, TargetProfile.GOOGLE_SLIDES)
        self.controller.set_profile(TargetProfile.PDF_VIEWER)
        self.assertEqual(self.controller.profile, TargetProfile.PDF_VIEWER)

    def test_toggle_mode(self):
        """Test switching between Simulation and Live OS modes."""
        self.assertEqual(self.controller.mode, ControllerMode.SIMULATION)
        new_mode = self.controller.toggle_mode()
        self.assertEqual(new_mode, ControllerMode.LIVE_OS)
        self.assertEqual(self.controller.mode, ControllerMode.LIVE_OS)
        new_mode = self.controller.toggle_mode()
        self.assertEqual(new_mode, ControllerMode.SIMULATION)

    def test_slide_navigation(self):
        """Test internal slide navigation counters."""
        self.assertEqual(self.controller.current_slide, 1)

        self.assertTrue(self.controller.next_slide())
        self.assertEqual(self.controller.current_slide, 2)

        # Immediate trigger blocked by cooldown
        self.assertFalse(self.controller.next_slide())

        # Advance past cooldown
        self.controller.last_action_time = 0.0
        self.assertTrue(self.controller.prev_slide())
        self.assertEqual(self.controller.current_slide, 1)

        # Cannot navigate before slide 1
        self.controller.last_action_time = 0.0
        self.controller.prev_slide()
        self.assertEqual(self.controller.current_slide, 1)

        # Goto slide
        self.assertTrue(self.controller.goto_slide(5))
        self.assertEqual(self.controller.current_slide, 5)
        self.assertFalse(self.controller.goto_slide(999))
        self.assertEqual(self.controller.current_slide, 5)

    def test_handle_gesture_discrete(self):
        """Test gesture evaluation and action triggering."""
        callback_mock = MagicMock()
        self.controller.set_action_callback(callback_mock)

        state = GestureState(
            gesture=GestureType.POINT_RIGHT,
            label="Point Right",
            emoji="👉",
            action="Next Slide",
            confidence=0.9,
            finger_states={},
            pinch_distance_norm=1.0,
            raw_pinch_distance=100.0,
        )

        action = self.controller.handle_gesture(state)
        self.assertEqual(action, "NEXT_SLIDE")
        self.assertEqual(self.controller.current_slide, 2)
        callback_mock.assert_called_once_with("NEXT_SLIDE", state)

        # Second trigger should be blocked by cooldown
        action_blocked = self.controller.handle_gesture(state)
        self.assertIsNone(action_blocked)

    def test_handle_gesture_continuous(self):
        """Test continuous gestures (Laser Pointer, Pinch) bypass cooldown."""
        state_pointer = GestureState(
            gesture=GestureType.INDEX_POINTER,
            label="Laser Pointer",
            emoji="👆",
            action="Point",
            confidence=0.9,
            finger_states={},
            pinch_distance_norm=1.0,
            raw_pinch_distance=100.0,
        )

        res1 = self.controller.handle_gesture(state_pointer)
        self.assertEqual(res1, "LASER_POINTER")
        res2 = self.controller.handle_gesture(state_pointer)
        self.assertEqual(res2, "LASER_POINTER")

    def test_profile_keymaps_completeness(self):
        """Verify that all target profiles have valid key combinations."""
        for profile in TargetProfile:
            self.assertIn(profile, PROFILE_KEYMAPS)
            keymap = PROFILE_KEYMAPS[profile]
            self.assertIn("NEXT_SLIDE", keymap)
            self.assertIn("PREV_SLIDE", keymap)
            self.assertIn("FULLSCREEN_TOGGLE", keymap)
            self.assertIsInstance(keymap["NEXT_SLIDE"], list)
            self.assertGreater(len(keymap["NEXT_SLIDE"]), 0)


if __name__ == "__main__":
    unittest.main()
