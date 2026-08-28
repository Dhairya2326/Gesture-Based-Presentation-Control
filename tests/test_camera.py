"""
Unit tests for CameraManager and video capture pipeline.
"""

import unittest
import time
import numpy as np
from src.processing.camera import CameraManager


class TestCameraManager(unittest.TestCase):
    """Test CameraManager thread lifecycle, resolution changes, and frame generation."""

    def setUp(self):
        self.camera = CameraManager(device_index=0, resolution=(640, 480))

    def tearDown(self):
        if self.camera.is_running:
            self.camera.stop()

    def test_camera_start_and_stop(self):
        """Test starting and stopping background capture thread."""
        self.assertFalse(self.camera.is_running)
        self.camera.start()
        self.assertTrue(self.camera.is_running)

        # Allow brief time for thread loop
        time.sleep(0.1)

        self.camera.stop()
        self.assertFalse(self.camera.is_running)

    def test_get_frame_returns_valid_image(self):
        """Test that get_frame returns a valid numpy image array."""
        self.camera.start()
        time.sleep(0.1)

        success, frame = self.camera.get_frame()
        self.assertIsNotNone(frame)
        self.assertIsInstance(frame, np.ndarray)
        self.assertEqual(len(frame.shape), 3)  # Height, Width, 3 channels
        self.assertEqual(frame.shape[2], 3)

    def test_resolution_switching(self):
        """Test resolution configuration."""
        self.camera.set_resolution(1280, 720)
        self.assertEqual(self.camera.requested_width, 1280)
        self.assertEqual(self.camera.requested_height, 720)

    def test_mirror_toggle(self):
        """Test horizontal mirroring flag."""
        self.camera.set_mirror(False)
        self.assertFalse(self.camera.mirror)
        self.camera.set_mirror(True)
        self.assertTrue(self.camera.mirror)

    def test_pause_resume(self):
        """Test pausing and resuming stream."""
        self.camera.start()
        self.assertFalse(self.camera.is_paused)

        paused = self.camera.toggle_pause()
        self.assertTrue(paused)
        self.assertTrue(self.camera.is_paused)

        resumed = self.camera.toggle_pause()
        self.assertFalse(resumed)
        self.assertFalse(self.camera.is_paused)


if __name__ == "__main__":
    unittest.main()
