"""
Unit tests for HandDetector module using MediaPipe Hands.
"""

import unittest
import numpy as np
import math
from src.processing.hand_detector import HandDetector


class TestHandDetector(unittest.TestCase):
    """Test HandDetector initialization, inference on blank frames, geometry utilities, and teardown."""

    def setUp(self):
        self.detector = HandDetector(
            static_image_mode=True,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def tearDown(self):
        self.detector.close()

    def test_detector_initialization(self):
        """Verify detector hyperparameter assignment."""
        self.assertEqual(self.detector.max_num_hands, 2)
        self.assertEqual(self.detector.min_detection_confidence, 0.5)
        self.assertEqual(self.detector.min_tracking_confidence, 0.5)
        self.assertIsNotNone(self.detector.hands)

    def test_find_hands_on_blank_frame(self):
        """Verify processing on a blank/solid black frame returns no hands gracefully."""
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        annotated_frame, hands_data = self.detector.find_hands(blank_frame, draw=True, draw_box=True)

        self.assertIsNotNone(annotated_frame)
        self.assertEqual(annotated_frame.shape, blank_frame.shape)
        self.assertIsInstance(hands_data, list)
        self.assertEqual(len(hands_data), 0)

    def test_find_hands_empty_input(self):
        """Verify handling of None or empty ndarray input."""
        frame, hands = self.detector.find_hands(None)
        self.assertIsNone(frame)
        self.assertEqual(hands, [])

        empty_frame = np.array([])
        frame, hands = self.detector.find_hands(empty_frame)
        self.assertEqual(len(hands), 0)

    def test_calculate_distance(self):
        """Test Euclidean distance calculation between two landmark points."""
        p1 = (0, 0, 0.0)
        p2 = (30, 40, 0.0)
        dist = HandDetector.calculate_distance(p1, p2)
        self.assertAlmostEqual(dist, 50.0, places=2)

    def test_finger_states_logic(self):
        """Test finger extension detection logic with synthetic mock landmarks."""
        # Construct synthetic hand landmarks with Index finger extended upwards (Tip Y < PIP Y)
        # Note: In screen pixel coordinates, Y=0 is at the top of the screen.
        mock_landmarks = [(100, 100, 0.0) for _ in range(21)]

        # Set Index TIP (idx 8) higher than Index PIP (idx 6) -> Extended
        mock_landmarks[HandDetector.INDEX_TIP] = (100, 50, 0.0)
        mock_landmarks[HandDetector.INDEX_PIP] = (100, 80, 0.0)

        # Set Middle TIP (idx 12) lower than Middle PIP (idx 10) -> Folded
        mock_landmarks[HandDetector.MIDDLE_TIP] = (120, 120, 0.0)
        mock_landmarks[HandDetector.MIDDLE_PIP] = (120, 90, 0.0)

        # Set Ring TIP lower than Ring PIP -> Folded
        mock_landmarks[HandDetector.RING_TIP] = (140, 120, 0.0)
        mock_landmarks[HandDetector.RING_PIP] = (140, 90, 0.0)

        # Set Pinky TIP lower than Pinky PIP -> Folded
        mock_landmarks[HandDetector.PINKY_TIP] = (160, 120, 0.0)
        mock_landmarks[HandDetector.PINKY_PIP] = (160, 90, 0.0)

        mock_hand_data = {
            "label": "Right",
            "landmarks": mock_landmarks,
        }

        states = self.detector.get_finger_states(mock_hand_data)
        self.assertTrue(states["index"])
        self.assertFalse(states["middle"])
        self.assertFalse(states["ring"])
        self.assertFalse(states["pinky"])


if __name__ == "__main__":
    unittest.main()
