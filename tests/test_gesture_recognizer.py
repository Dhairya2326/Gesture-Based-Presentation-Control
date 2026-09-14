"""
Unit tests for GestureRecognizer engine.
Tests geometric heuristic classification across synthetic 3D hand landmark postures,
scale normalization, temporal voting buffers, and HUD overlay rendering.
"""

import unittest
import numpy as np
import cv2
from src.processing.gesture_recognizer import (
    GestureRecognizer,
    GestureType,
    GestureState,
    GESTURE_METADATA,
)


class TestGestureRecognizer(unittest.TestCase):
    """Test suite for GestureRecognizer rules, geometry calculations, and stability filtering."""

    def setUp(self):
        self.recognizer = GestureRecognizer(smoothing_window=5, min_confidence=0.6)

    def _create_base_landmarks(self, wrist_pos=(200, 300, 0.0)) -> list:
        """Create a default synthetic hand with neutral MCP base joints."""
        # 21 landmarks initialized to wrist base
        landmarks = [list(wrist_pos) for _ in range(21)]

        # MCP Joints (Knuckles) relative to wrist
        landmarks[GestureRecognizer.INDEX_MCP] = [180, 220, 0.0]
        landmarks[GestureRecognizer.MIDDLE_MCP] = [200, 210, 0.0]
        landmarks[GestureRecognizer.RING_MCP] = [220, 220, 0.0]
        landmarks[GestureRecognizer.PINKY_MCP] = [240, 230, 0.0]
        landmarks[GestureRecognizer.THUMB_CMC] = [160, 270, 0.0]
        landmarks[GestureRecognizer.THUMB_MCP] = [150, 240, 0.0]

        # By default, curl all fingers down (PIP and TIP lower/below MCPs in Y)
        for tip_idx, dip_idx, pip_idx, mcp_idx in [
            (GestureRecognizer.INDEX_TIP, GestureRecognizer.INDEX_DIP, GestureRecognizer.INDEX_PIP, GestureRecognizer.INDEX_MCP),
            (GestureRecognizer.MIDDLE_TIP, GestureRecognizer.MIDDLE_DIP, GestureRecognizer.MIDDLE_PIP, GestureRecognizer.MIDDLE_MCP),
            (GestureRecognizer.RING_TIP, GestureRecognizer.RING_DIP, GestureRecognizer.RING_PIP, GestureRecognizer.RING_MCP),
            (GestureRecognizer.PINKY_TIP, GestureRecognizer.PINKY_DIP, GestureRecognizer.PINKY_PIP, GestureRecognizer.PINKY_MCP),
        ]:
            mcp_y = landmarks[mcp_idx][1]
            landmarks[pip_idx] = [landmarks[mcp_idx][0], mcp_y + 20, 0.0]
            landmarks[dip_idx] = [landmarks[mcp_idx][0], mcp_y + 35, 0.0]
            landmarks[tip_idx] = [landmarks[mcp_idx][0], mcp_y + 50, 0.0]

        # Fold thumb
        landmarks[GestureRecognizer.THUMB_IP] = [170, 230, 0.0]
        landmarks[GestureRecognizer.THUMB_TIP] = [180, 230, 0.0]

        return [tuple(pt) for pt in landmarks]

    def test_recognizer_initialization(self):
        """Verify recognizer attributes and defaults."""
        self.assertEqual(self.recognizer.smoothing_window, 5)
        self.assertEqual(self.recognizer.min_confidence, 0.6)
        self.assertEqual(self.recognizer._last_stable_gesture, GestureType.NONE)

    def test_invalid_or_empty_hand(self):
        """Verify invalid or empty landmarks return GestureType.NONE gracefully."""
        res_empty = self.recognizer.classify_raw({})
        self.assertEqual(res_empty.gesture, GestureType.NONE)

        res_short = self.recognizer.classify_raw({"landmarks": [(0, 0, 0.0)] * 10})
        self.assertEqual(res_short.gesture, GestureType.NONE)

    def test_palm_scale_calculation(self):
        """Verify scale normalization factor is calculated reliably."""
        landmarks = self._create_base_landmarks()
        scale = self.recognizer.get_palm_scale(landmarks)
        self.assertGreater(scale, 10.0)

    def test_fist_gesture(self):
        """Verify all curled fingers classify as FIST."""
        landmarks = self._create_base_landmarks()
        hand_data = {"landmarks": landmarks, "label": "Right", "bbox": (100, 100, 300, 300)}

        state = self.recognizer.classify_raw(hand_data)
        self.assertEqual(state.gesture, GestureType.FIST)
        self.assertEqual(state.emoji, "✊")

    def test_open_palm_gesture(self):
        """Verify all extended fingers classify as OPEN_PALM."""
        landmarks = self._create_base_landmarks()

        # Extend 4 fingers upwards (Tip Y < DIP Y < PIP Y < MCP Y)
        for tip_idx, dip_idx, pip_idx, mcp_idx in [
            (GestureRecognizer.INDEX_TIP, GestureRecognizer.INDEX_DIP, GestureRecognizer.INDEX_PIP, GestureRecognizer.INDEX_MCP),
            (GestureRecognizer.MIDDLE_TIP, GestureRecognizer.MIDDLE_DIP, GestureRecognizer.MIDDLE_PIP, GestureRecognizer.MIDDLE_MCP),
            (GestureRecognizer.RING_TIP, GestureRecognizer.RING_DIP, GestureRecognizer.RING_PIP, GestureRecognizer.RING_MCP),
            (GestureRecognizer.PINKY_TIP, GestureRecognizer.PINKY_DIP, GestureRecognizer.PINKY_PIP, GestureRecognizer.PINKY_MCP),
        ]:
            mcp_y = landmarks[mcp_idx][1]
            landmarks[pip_idx] = (landmarks[mcp_idx][0], mcp_y - 30, 0.0)
            landmarks[dip_idx] = (landmarks[mcp_idx][0], mcp_y - 60, 0.0)
            landmarks[tip_idx] = (landmarks[mcp_idx][0], mcp_y - 90, 0.0)

        # Extend thumb outward to the left (Right hand: Thumb Tip X < Thumb IP X)
        landmarks[GestureRecognizer.THUMB_IP] = (130, 220, 0.0)
        landmarks[GestureRecognizer.THUMB_TIP] = (100, 200, 0.0)

        hand_data = {"landmarks": landmarks, "label": "Right", "bbox": (100, 100, 300, 300)}
        state = self.recognizer.classify_raw(hand_data)
        self.assertEqual(state.gesture, GestureType.OPEN_PALM)
        self.assertEqual(state.emoji, "✋")

    def test_laser_pointer_gesture(self):
        """Verify only index finger extended vertically upwards classifies as INDEX_POINTER."""
        landmarks = self._create_base_landmarks()

        # Extend Index finger vertically up
        mcp_y = landmarks[GestureRecognizer.INDEX_MCP][1]
        mcp_x = landmarks[GestureRecognizer.INDEX_MCP][0]
        landmarks[GestureRecognizer.INDEX_PIP] = (mcp_x, mcp_y - 30, 0.0)
        landmarks[GestureRecognizer.INDEX_DIP] = (mcp_x, mcp_y - 60, 0.0)
        landmarks[GestureRecognizer.INDEX_TIP] = (mcp_x, mcp_y - 90, 0.0)

        hand_data = {"landmarks": landmarks, "label": "Right", "bbox": (100, 100, 300, 300)}
        state = self.recognizer.classify_raw(hand_data)
        self.assertEqual(state.gesture, GestureType.INDEX_POINTER)
        self.assertEqual(state.emoji, "👆")

    def test_point_right_gesture(self):
        """Verify index finger extended horizontally to the right classifies as POINT_RIGHT."""
        landmarks = self._create_base_landmarks()

        # Extend Index finger pointing rightwards (dx > 0)
        mcp_x = landmarks[GestureRecognizer.INDEX_MCP][0]
        mcp_y = landmarks[GestureRecognizer.INDEX_MCP][1]
        landmarks[GestureRecognizer.INDEX_PIP] = (mcp_x + 30, mcp_y, 0.0)
        landmarks[GestureRecognizer.INDEX_DIP] = (mcp_x + 60, mcp_y, 0.0)
        landmarks[GestureRecognizer.INDEX_TIP] = (mcp_x + 90, mcp_y, 0.0)

        hand_data = {"landmarks": landmarks, "label": "Right", "bbox": (100, 100, 300, 300)}
        state = self.recognizer.classify_raw(hand_data)
        self.assertEqual(state.gesture, GestureType.POINT_RIGHT)
        self.assertEqual(state.emoji, "👉")

    def test_point_left_gesture(self):
        """Verify index finger extended horizontally to the left classifies as POINT_LEFT."""
        landmarks = self._create_base_landmarks()

        # Extend Index finger pointing leftwards (dx < 0)
        mcp_x = landmarks[GestureRecognizer.INDEX_MCP][0]
        mcp_y = landmarks[GestureRecognizer.INDEX_MCP][1]
        landmarks[GestureRecognizer.INDEX_PIP] = (mcp_x - 30, mcp_y, 0.0)
        landmarks[GestureRecognizer.INDEX_DIP] = (mcp_x - 60, mcp_y, 0.0)
        landmarks[GestureRecognizer.INDEX_TIP] = (mcp_x - 90, mcp_y, 0.0)

        hand_data = {"landmarks": landmarks, "label": "Right", "bbox": (100, 100, 300, 300)}
        state = self.recognizer.classify_raw(hand_data)
        self.assertEqual(state.gesture, GestureType.POINT_LEFT)
        self.assertEqual(state.emoji, "👈")

    def test_pinch_gesture(self):
        """Verify thumb tip and index tip touching classifies as PINCH."""
        landmarks = self._create_base_landmarks()

        # Position Thumb Tip and Index Tip directly on top of each other
        landmarks[GestureRecognizer.THUMB_TIP] = (175, 180, 0.0)
        landmarks[GestureRecognizer.INDEX_TIP] = (176, 180, 0.0)

        hand_data = {"landmarks": landmarks, "label": "Right", "bbox": (100, 100, 300, 300)}
        state = self.recognizer.classify_raw(hand_data)
        self.assertEqual(state.gesture, GestureType.PINCH)
        self.assertEqual(state.emoji, "🤏")

    def test_peace_gesture(self):
        """Verify index & middle extended classifies as PEACE."""
        landmarks = self._create_base_landmarks()

        # Extend Index & Middle
        for mcp_idx, pip_idx, dip_idx, tip_idx in [
            (GestureRecognizer.INDEX_MCP, GestureRecognizer.INDEX_PIP, GestureRecognizer.INDEX_DIP, GestureRecognizer.INDEX_TIP),
            (GestureRecognizer.MIDDLE_MCP, GestureRecognizer.MIDDLE_PIP, GestureRecognizer.MIDDLE_DIP, GestureRecognizer.MIDDLE_TIP),
        ]:
            mcp_x = landmarks[mcp_idx][0]
            mcp_y = landmarks[mcp_idx][1]
            landmarks[pip_idx] = (mcp_x, mcp_y - 30, 0.0)
            landmarks[dip_idx] = (mcp_x, mcp_y - 60, 0.0)
            landmarks[tip_idx] = (mcp_x, mcp_y - 90, 0.0)

        hand_data = {"landmarks": landmarks, "label": "Right", "bbox": (100, 100, 300, 300)}
        state = self.recognizer.classify_raw(hand_data)
        self.assertEqual(state.gesture, GestureType.PEACE)
        self.assertEqual(state.emoji, "✌️")

    def test_ok_sign_gesture(self):
        """Verify pinch + 3 extended fingers classifies as OK_SIGN."""
        landmarks = self._create_base_landmarks()

        # Pinch Thumb & Index
        landmarks[GestureRecognizer.THUMB_TIP] = (175, 180, 0.0)
        landmarks[GestureRecognizer.INDEX_TIP] = (176, 180, 0.0)

        # Extend Middle, Ring, Pinky
        for mcp_idx, pip_idx, dip_idx, tip_idx in [
            (GestureRecognizer.MIDDLE_MCP, GestureRecognizer.MIDDLE_PIP, GestureRecognizer.MIDDLE_DIP, GestureRecognizer.MIDDLE_TIP),
            (GestureRecognizer.RING_MCP, GestureRecognizer.RING_PIP, GestureRecognizer.RING_DIP, GestureRecognizer.RING_TIP),
            (GestureRecognizer.PINKY_MCP, GestureRecognizer.PINKY_PIP, GestureRecognizer.PINKY_DIP, GestureRecognizer.PINKY_TIP),
        ]:
            mcp_x = landmarks[mcp_idx][0]
            mcp_y = landmarks[mcp_idx][1]
            landmarks[pip_idx] = (mcp_x, mcp_y - 30, 0.0)
            landmarks[dip_idx] = (mcp_x, mcp_y - 60, 0.0)
            landmarks[tip_idx] = (mcp_x, mcp_y - 90, 0.0)

        hand_data = {"landmarks": landmarks, "label": "Right", "bbox": (100, 100, 300, 300)}
        state = self.recognizer.classify_raw(hand_data)
        self.assertEqual(state.gesture, GestureType.OK_SIGN)
        self.assertEqual(state.emoji, "👌")

    def test_temporal_smoothing(self):
        """Verify majority voting across consecutive frames."""
        recognizer = GestureRecognizer(smoothing_window=5, min_confidence=0.6)

        landmarks_fist = self._create_base_landmarks()
        hand_fist = {"landmarks": landmarks_fist, "label": "Right", "bbox": (100, 100, 300, 300)}

        # Push 3 Fist frames
        for _ in range(3):
            st = recognizer.recognize(hand_fist, use_smoothing=True)

        self.assertEqual(st.gesture, GestureType.FIST)

        # 1 single glitch frame should not immediately overturn stable gesture
        empty_hand = {"landmarks": [], "label": "Right"}
        st_glitch = recognizer.recognize(empty_hand, use_smoothing=True)
        self.assertEqual(st_glitch.gesture, GestureType.FIST)

    def test_draw_gesture_hud(self):
        """Verify HUD overlay drawing executes without raising exceptions."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        landmarks = self._create_base_landmarks()
        hand_data = {"landmarks": landmarks, "label": "Right", "bbox": (50, 50, 200, 200)}

        state = self.recognizer.classify_raw(hand_data)
        annotated = self.recognizer.draw_gesture_hud(frame, state, landmarks=landmarks)
        self.assertEqual(annotated.shape, frame.shape)


if __name__ == "__main__":
    unittest.main()
