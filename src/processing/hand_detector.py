"""
Hand Detection and Landmark Tracking pipeline using MediaPipe Hands.
Extracts 21 3D landmarks, calculates bounding boxes, determines handedness,
and renders high-visibility overlays for gesture presentation control.
"""

import cv2
import numpy as np
import mediapipe as mp
import math
from typing import List, Tuple, Dict, Optional, Any


class HandDetector:
    """
    Encapsulates MediaPipe Hands solution with custom visual rendering,
    coordinate transformation, handedness tracking, and gesture geometry utilities.
    """

    # MediaPipe Hand Landmark Indices Constants
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    FINGER_TIPS = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
    FINGER_PIPS = [THUMB_IP, INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]
    FINGER_MCPS = [THUMB_CMC, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP]

    # Visual Theme Palette (BGR for OpenCV)
    COLOR_JOINT = (230, 214, 137)       # Neon Cyan
    COLOR_CONNECTION = (245, 140, 198)  # Electric Violet / Magenta
    COLOR_TIP = (166, 227, 161)         # Soft Green
    COLOR_BOX = (242, 180, 137)         # Sky Blue
    COLOR_BOX_BG = (35, 27, 30)         # Dark background tag
    COLOR_TEXT = (255, 255, 255)        # Crisp White

    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.5,
    ):
        """
        Initialize the MediaPipe Hands detector.

        :param static_image_mode: If False, treats input images as a continuous video stream.
        :param max_num_hands: Maximum number of hands to detect concurrently (1 or 2).
        :param min_detection_confidence: Minimum confidence threshold [0.0, 1.0] for detection.
        :param min_tracking_confidence: Minimum confidence threshold [0.0, 1.0] for tracking.
        """
        self.static_image_mode = static_image_mode
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.static_image_mode,
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
        )

        self.mp_draw = mp.solutions.drawing_utils
        self.mp_draw_styles = mp.solutions.drawing_styles

        self.results: Optional[Any] = None

    def find_hands(
        self,
        frame: np.ndarray,
        draw: bool = True,
        draw_box: bool = True,
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Process a BGR video frame to detect hands, extract landmark coordinates,
        and optionally render custom skeleton overlays and bounding boxes.

        :param frame: BGR input image frame from OpenCV.
        :param draw: Whether to draw skeleton connections and landmarks.
        :param draw_box: Whether to draw bounding box and handedness badge.
        :return: (annotated_frame, list_of_detected_hands_dict)
        """
        if frame is None or frame.size == 0:
            return frame, []

        h, w, c = frame.shape
        annotated_frame = frame.copy()

        # Convert BGR to RGB for MediaPipe inference
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        self.results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        detected_hands: List[Dict[str, Any]] = []

        if not self.results.multi_hand_landmarks:
            return annotated_frame, detected_hands

        # Extract handedness if available
        handedness_list = []
        if self.results.multi_handedness:
            for classification in self.results.multi_handedness:
                label = classification.classification[0].label
                score = classification.classification[0].score
                handedness_list.append({"label": label, "confidence": score})

        # Process each detected hand
        for i, hand_landmarks in enumerate(self.results.multi_hand_landmarks):
            handedness_info = (
                handedness_list[i] if i < len(handedness_list) else {"label": "Hand", "confidence": 1.0}
            )

            # Extract 21 landmark coordinate points
            landmarks_px: List[Tuple[int, int, float]] = []
            landmarks_norm: List[Tuple[float, float, float]] = []
            x_coords: List[int] = []
            y_coords: List[int] = []

            for lm in hand_landmarks.landmark:
                px_x = int(lm.x * w)
                px_y = int(lm.y * h)
                px_z = lm.z
                landmarks_px.append((px_x, px_y, px_z))
                landmarks_norm.append((lm.x, lm.y, lm.z))
                x_coords.append(px_x)
                y_coords.append(px_y)

            # Compute bounding box with padding
            pad = 20
            bbox_x_min = max(0, min(x_coords) - pad)
            bbox_y_min = max(0, min(y_coords) - pad)
            bbox_x_max = min(w, max(x_coords) + pad)
            bbox_y_max = min(h, max(y_coords) + pad)
            bbox = (bbox_x_min, bbox_y_min, bbox_x_max, bbox_y_max)

            hand_dict: Dict[str, Any] = {
                "index": i,
                "label": handedness_info["label"],
                "confidence": handedness_info["confidence"],
                "landmarks": landmarks_px,
                "landmarks_norm": landmarks_norm,
                "bbox": bbox,
            }
            detected_hands.append(hand_dict)

            # Render custom visualization overlay
            if draw:
                self._draw_hand_skeleton(annotated_frame, hand_landmarks, landmarks_px)

            if draw_box:
                self._draw_bounding_box(annotated_frame, hand_dict)

        return annotated_frame, detected_hands

    def _draw_hand_skeleton(
        self,
        frame: np.ndarray,
        hand_landmarks: Any,
        landmarks_px: List[Tuple[int, int, float]],
    ) -> None:
        """Render high-contrast, aesthetic skeleton connections and joint keypoints."""
        # Draw connections
        for conn in self.mp_hands.HAND_CONNECTIONS:
            pt1_idx, pt2_idx = conn
            pt1 = (landmarks_px[pt1_idx][0], landmarks_px[pt1_idx][1])
            pt2 = (landmarks_px[pt2_idx][0], landmarks_px[pt2_idx][1])
            cv2.line(frame, pt1, pt2, self.COLOR_CONNECTION, 2, cv2.LINE_AA)

        # Draw joints
        for idx, pt in enumerate(landmarks_px):
            pos = (pt[0], pt[1])
            if idx in self.FINGER_TIPS:
                # Finger tips have distinct green accent
                cv2.circle(frame, pos, 6, self.COLOR_TIP, -1, cv2.LINE_AA)
                cv2.circle(frame, pos, 8, (255, 255, 255), 1, cv2.LINE_AA)
            elif idx == self.WRIST:
                # Wrist root joint
                cv2.circle(frame, pos, 7, (137, 180, 250), -1, cv2.LINE_AA)
                cv2.circle(frame, pos, 9, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                # Normal bone joints
                cv2.circle(frame, pos, 4, self.COLOR_JOINT, -1, cv2.LINE_AA)

    def _draw_bounding_box(self, frame: np.ndarray, hand_data: Dict[str, Any]) -> None:
        """Draw an elegant bounding box with corner accents and a header badge."""
        x_min, y_min, x_max, y_max = hand_data["bbox"]
        label = hand_data["label"]
        conf = hand_data["confidence"]

        # Outer subtle box
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), self.COLOR_BOX, 1, cv2.LINE_AA)

        # Corner bracket highlights
        corner_len = 16
        thick = 2
        # Top-Left
        cv2.line(frame, (x_min, y_min), (x_min + corner_len, y_min), self.COLOR_BOX, thick, cv2.LINE_AA)
        cv2.line(frame, (x_min, y_min), (x_min, y_min + corner_len), self.COLOR_BOX, thick, cv2.LINE_AA)
        # Top-Right
        cv2.line(frame, (x_max, y_min), (x_max - corner_len, y_min), self.COLOR_BOX, thick, cv2.LINE_AA)
        cv2.line(frame, (x_max, y_min), (x_max, y_min + corner_len), self.COLOR_BOX, thick, cv2.LINE_AA)
        # Bottom-Left
        cv2.line(frame, (x_min, y_max), (x_min + corner_len, y_max), self.COLOR_BOX, thick, cv2.LINE_AA)
        cv2.line(frame, (x_min, y_max), (x_min, y_max - corner_len), self.COLOR_BOX, thick, cv2.LINE_AA)
        # Bottom-Right
        cv2.line(frame, (x_max, y_max), (x_max - corner_len, y_max), self.COLOR_BOX, thick, cv2.LINE_AA)
        cv2.line(frame, (x_max, y_max), (x_max, y_max - corner_len), self.COLOR_BOX, thick, cv2.LINE_AA)

        # Header Badge
        badge_text = f"{label} Hand ({int(conf * 100)}%)"
        (txt_w, txt_h), baseline = cv2.getTextSize(
            badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1
        )
        badge_y_min = max(0, y_min - txt_h - 10)
        badge_y_max = y_min

        # Background rounded badge
        cv2.rectangle(
            frame,
            (x_min, badge_y_min),
            (x_min + txt_w + 12, badge_y_max),
            self.COLOR_BOX_BG,
            -1,
        )
        cv2.rectangle(
            frame,
            (x_min, badge_y_min),
            (x_min + txt_w + 12, badge_y_max),
            self.COLOR_BOX,
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            badge_text,
            (x_min + 6, badge_y_max - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            self.COLOR_TEXT,
            1,
            cv2.LINE_AA,
        )

    def get_finger_states(self, hand_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Determine which fingers are extended (open/up) vs curled (closed).
        Useful as the fundamental primitive for Week 6 Gesture Recognition.

        :param hand_data: Hand dictionary containing 'landmarks' (pixel coordinates) and 'label'.
        :return: Dict mapping finger names ('thumb', 'index', 'middle', 'ring', 'pinky') to bool.
        """
        landmarks = hand_data.get("landmarks", [])
        if len(landmarks) < 21:
            return {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}

        is_right_hand = hand_data.get("label") == "Right"
        states: Dict[str, bool] = {}

        # Thumb: Horizontal extension check (depending on whether hand is Left or Right)
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]

        if is_right_hand:
            states["thumb"] = thumb_tip[0] < thumb_ip[0]
        else:
            states["thumb"] = thumb_tip[0] > thumb_ip[0]

        # 4 Fingers: Vertical extension check (Tip Y < PIP Y because Y increases downwards in screen space)
        finger_names = ["index", "middle", "ring", "pinky"]
        tip_indices = [self.INDEX_TIP, self.MIDDLE_TIP, self.RING_TIP, self.PINKY_TIP]
        pip_indices = [self.INDEX_PIP, self.MIDDLE_PIP, self.RING_PIP, self.PINKY_PIP]

        for name, tip_idx, pip_idx in zip(finger_names, tip_indices, pip_indices):
            states[name] = landmarks[tip_idx][1] < landmarks[pip_idx][1]

        return states

    @staticmethod
    def calculate_distance(
        pt1: Tuple[int, int, Any], pt2: Tuple[int, int, Any]
    ) -> float:
        """Calculate Euclidean distance between two landmark coordinate points."""
        return math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1])

    def close(self) -> None:
        """Release underlying MediaPipe resource handles."""
        if self.hands is not None:
            self.hands.close()
