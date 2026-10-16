"""
Unit tests for LaserPointer and SlideAnnotator (Week 8).
"""

import unittest
import numpy as np

from src.presentation.laser_pointer import LaserPointer
from src.presentation.annotator import SlideAnnotator, AnnotationStroke


class TestLaserPointer(unittest.TestCase):
    """Test suite for virtual laser pointer optics and coordinate mapping."""

    def setUp(self):
        self.laser = LaserPointer(smoothing_factor=0.5, trail_length=5, active_margin=0.1)

    def test_initial_state(self):
        """Test default laser pointer state."""
        self.assertTrue(self.laser.is_enabled)
        self.assertEqual(self.laser.laser_color_name, "Red")
        self.assertEqual(self.laser.smoothing_factor, 0.5)

    def test_set_color(self):
        """Test changing laser glow color presets."""
        self.laser.set_color("Green")
        self.assertEqual(self.laser.laser_color_name, "Green")
        self.assertEqual(self.laser.laser_color, LaserPointer.COLOR_GREEN_GLOW)
        self.laser.set_color("Cyan")
        self.assertEqual(self.laser.laser_color_name, "Cyan")

    def test_update_position_smoothing(self):
        """Test exponential moving average smoothing."""
        # Initial point
        frame_pos1, screen_pos1 = self.laser.update_position(100, 100, 1000, 1000)
        self.assertEqual(frame_pos1, (100, 100))

        # Second point (0.5 * 200 + 0.5 * 100 = 150)
        frame_pos2, screen_pos2 = self.laser.update_position(200, 200, 1000, 1000)
        self.assertEqual(frame_pos2, (150, 150))
        self.assertIsInstance(screen_pos2[0], int)
        self.assertIsInstance(screen_pos2[1], int)

    def test_render_overlay(self):
        """Test optical glow overlay rendering onto frame."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.laser.update_position(320, 240, 640, 480)
        rendered = self.laser.render_overlay(frame.copy())
        self.assertEqual(rendered.shape, (480, 640, 3))
        # Point at (320, 240) should be brightened
        self.assertTrue(np.any(rendered[240, 320] > 0))


class TestSlideAnnotator(unittest.TestCase):
    """Test suite for slide annotation canvas and stroke management."""

    def setUp(self):
        self.annotator = SlideAnnotator()

    def test_initial_state(self):
        """Test default annotator configuration."""
        self.assertTrue(self.annotator.is_enabled)
        self.assertEqual(self.annotator.active_color_name, "Red")
        self.assertEqual(self.annotator.active_thickness, 4)
        self.assertEqual(self.annotator.stroke_count, 0)

    def test_drawing_lifecycle(self):
        """Test starting, continuing, and finishing a stroke."""
        self.annotator.start_drawing(50, 50)
        self.annotator.continue_drawing(55, 55)
        self.annotator.continue_drawing(60, 60)
        self.assertEqual(self.annotator.stroke_count, 1)
        self.assertEqual(len(self.annotator.strokes[0].points), 3)

        self.annotator.stop_drawing()
        self.assertFalse(self.annotator._is_drawing)

    def test_undo_and_clear(self):
        """Test undoing strokes and clearing canvas."""
        self.annotator.start_drawing(10, 10)
        self.annotator.continue_drawing(20, 20)
        self.annotator.stop_drawing()

        self.annotator.start_drawing(30, 30)
        self.annotator.continue_drawing(40, 40)
        self.annotator.stop_drawing()

        self.assertEqual(self.annotator.stroke_count, 2)

        # Undo 1
        self.assertTrue(self.annotator.undo())
        self.assertEqual(self.annotator.stroke_count, 1)

        # Clear
        self.annotator.clear()
        self.assertEqual(self.annotator.stroke_count, 0)

    def test_render_annotations(self):
        """Test rendering strokes onto a frame."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.annotator.start_drawing(100, 100)
        self.annotator.continue_drawing(200, 200)
        self.annotator.stop_drawing()

        rendered = self.annotator.render(frame.copy())
        self.assertEqual(rendered.shape, (480, 640, 3))
        # Center of line between (100,100) and (200,200) is (150,150)
        self.assertTrue(np.any(rendered[150, 150] > 0))


if __name__ == "__main__":
    unittest.main()
