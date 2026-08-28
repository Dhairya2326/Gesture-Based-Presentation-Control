"""
Unit tests for Tkinter GUI setup and lifecycle.
"""

import unittest
import tkinter as tk
from src.gui.app import PresentationControllerApp


class TestGUIApp(unittest.TestCase):
    """Test GUI instantiation, widget existence, and clean destruction."""

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during automated test
        self.app = PresentationControllerApp(self.root, camera_index=0)

    def tearDown(self):
        self.app.on_close()

    def test_gui_components_exist(self):
        """Verify essential GUI components are initialized."""
        self.assertIsNotNone(self.app.video_canvas)
        self.assertIsNotNone(self.app.btn_toggle_camera)
        self.assertIsNotNone(self.app.fps_badge)
        self.assertIsNotNone(self.app.status_badge)
        self.assertIsNotNone(self.app.log_text)

    def test_log_message(self):
        """Verify logging writes to log text area without exception."""
        self.app.log_message("Test diagnostic log entry")
        content = self.app.log_text.get("1.0", tk.END)
        self.assertIn("Test diagnostic log entry", content)


if __name__ == "__main__":
    unittest.main()
