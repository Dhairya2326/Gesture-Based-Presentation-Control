"""
Gesture Recognition Engine using MediaPipe 21 Hand Landmarks.
Classifies discrete and continuous gestures (Next, Prev, Pointer, Open Palm, Fist, Pinch,
Peace, Thumbs Up/Down, OK Sign) with scale normalization and temporal smoothing.
"""

import math
from collections import deque, Counter
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Dict, Optional, Any
import cv2
import numpy as np


class GestureType(Enum):
    """Enumeration of all supported presentation control gestures."""
    NONE = "NONE"
    OPEN_PALM = "OPEN_PALM"
    FIST = "FIST"
    POINT_RIGHT = "POINT_RIGHT"
    POINT_LEFT = "POINT_LEFT"
    INDEX_POINTER = "INDEX_POINTER"
    PINCH = "PINCH"
    PEACE = "PEACE"
    THUMBS_UP = "THUMBS_UP"
    THUMBS_DOWN = "THUMBS_DOWN"
    OK_SIGN = "OK_SIGN"


# Mapping from GestureType to Human-Readable Label and Emoji
GESTURE_METADATA: Dict[GestureType, Dict[str, str]] = {
    GestureType.NONE: {"label": "No Gesture", "emoji": "⏳", "action": "Idle"},
    GestureType.OPEN_PALM: {"label": "Open Palm", "emoji": "✋", "action": "Attention / Free"},
    GestureType.FIST: {"label": "Fist", "emoji": "✊", "action": "Pause / Neutral"},
    GestureType.POINT_RIGHT: {"label": "Point Right", "emoji": "👉", "action": "Next Slide"},
    GestureType.POINT_LEFT: {"label": "Point Left", "emoji": "👈", "action": "Previous Slide"},
    GestureType.INDEX_POINTER: {"label": "Laser Pointer", "emoji": "👆", "action": "Point / Track"},
    GestureType.PINCH: {"label": "Pinch", "emoji": "🤏", "action": "Pen / Annotate"},
    GestureType.PEACE: {"label": "Peace / Victory", "emoji": "✌️", "action": "Highlight / Zoom"},
    GestureType.THUMBS_UP: {"label": "Thumbs Up", "emoji": "👍", "action": "Confirm / Volume Up"},
    GestureType.THUMBS_DOWN: {"label": "Thumbs Down", "emoji": "👎", "action": "Exit / Volume Down"},
    GestureType.OK_SIGN: {"label": "OK Sign", "emoji": "👌", "action": "Fullscreen / Start"},
}


@dataclass
class GestureState:
    """Encapsulates the result of gesture classification for a detected hand."""
    gesture: GestureType
    label: str
    emoji: str
    action: str
    confidence: float
    finger_states: Dict[str, bool]
    pinch_distance_norm: float
    raw_pinch_distance: float
    pointer_pos: Optional[Tuple[int, int]] = None
    hand_label: str = "Right"
    bbox: Optional[Tuple[int, int, int, int]] = None


class GestureRecognizer:
    """
    Robust, rule-based and geometric hand gesture classifier.
    Incorporates hand-scale invariant landmark normalization and temporal voting smoothing.
    """

    # Landmark Constants (Standard MediaPipe 21 Hand Landmarks)
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

    # Pinch threshold (normalized by palm scale)
    PINCH_THRESHOLD_NORM = 0.38

    # Visual Theme Colors (BGR)
    COLOR_HUD_BG = (26, 21, 35)        # Deep Obsidian Purple
    COLOR_HUD_BORDER = (245, 140, 198)  # Electric Violet
    COLOR_PINCH_LINE = (166, 227, 161)  # Soft Lime Green
    COLOR_POINTER_DOT = (110, 115, 243) # Coral Red / Orange
    COLOR_ACCENT_TEXT = (255, 255, 255) # Pure White
    COLOR_ACTION_TEXT = (230, 214, 137) # Cyan

    def __init__(self, smoothing_window: int = 5, min_confidence: float = 0.6):
        """
        Initialize the GestureRecognizer.

        :param smoothing_window: Number of consecutive frames used for temporal voting filter.
        :param min_confidence: Minimum voting ratio required to confirm a smoothed gesture.
        """
        self.smoothing_window = max(1, smoothing_window)
        self.min_confidence = min_confidence
        self._history: deque = deque(maxlen=self.smoothing_window)
        self._last_stable_gesture: GestureType = GestureType.NONE

    def reset(self) -> None:
        """Clear temporal history buffer."""
        self._history.clear()
        self._last_stable_gesture = GestureType.NONE

    @staticmethod
    def calculate_distance(pt1: Tuple[float, float, Any], pt2: Tuple[float, float, Any]) -> float:
        """Euclidean distance between 2D or 3D points."""
        return math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1])

    def get_palm_scale(self, landmarks: List[Tuple[int, int, float]]) -> float:
        """
        Calculate a robust reference scale for the hand (wrist to middle MCP distance).
        Ensures landmark distances are invariant to hand-to-camera distance.
        """
        if len(landmarks) < 21:
            return 100.0
        dist_wrist_middle_mcp = self.calculate_distance(landmarks[self.WRIST], landmarks[self.MIDDLE_MCP])
        dist_index_pinky_mcp = self.calculate_distance(landmarks[self.INDEX_MCP], landmarks[self.PINKY_MCP])
        # Return average or primary vertical span (fallback to 1.0 to avoid division by zero)
        scale = max(dist_wrist_middle_mcp, dist_index_pinky_mcp, 10.0)
        return scale

    def get_finger_states(
        self,
        landmarks: List[Tuple[int, int, float]],
        hand_label: str = "Right",
    ) -> Dict[str, bool]:
        """
        Determine boolean extension state for all 5 digits using 3D spatial geometry.
        """
        if len(landmarks) < 21:
            return {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}

        is_right = (hand_label == "Right")
        states = {}

        # 1. Thumb Extension
        # For thumb, check horizontal separation from MCP/IP joint and angle with wrist
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        thumb_mcp = landmarks[self.THUMB_MCP]

        # Horizontal distance check adjusted for handedness
        if is_right:
            thumb_extended = (thumb_tip[0] < thumb_ip[0]) and (thumb_tip[0] < thumb_mcp[0])
        else:
            thumb_extended = (thumb_tip[0] > thumb_ip[0]) and (thumb_tip[0] > thumb_mcp[0])

        # Also thumb can be extended upwards in Thumbs Up
        thumb_dist_wrist = self.calculate_distance(thumb_tip, landmarks[self.WRIST])
        thumb_mcp_dist_wrist = self.calculate_distance(thumb_mcp, landmarks[self.WRIST])
        if thumb_dist_wrist > thumb_mcp_dist_wrist * 1.35:
            thumb_extended = True

        states["thumb"] = thumb_extended

        # 2. 4 Fingers (Index, Middle, Ring, Pinky)
        # Finger is extended if TIP is above PIP and DIP in the vertical direction (Y decreases upwards)
        # AND TIP distance from wrist is substantially greater than PIP distance from wrist
        wrist = landmarks[self.WRIST]
        digits = [
            ("index", self.INDEX_TIP, self.INDEX_DIP, self.INDEX_PIP, self.INDEX_MCP),
            ("middle", self.MIDDLE_TIP, self.MIDDLE_DIP, self.MIDDLE_PIP, self.MIDDLE_MCP),
            ("ring", self.RING_TIP, self.RING_DIP, self.RING_PIP, self.RING_MCP),
            ("pinky", self.PINKY_TIP, self.PINKY_DIP, self.PINKY_PIP, self.PINKY_MCP),
        ]

        for name, tip_idx, dip_idx, pip_idx, mcp_idx in digits:
            tip = landmarks[tip_idx]
            pip = landmarks[pip_idx]
            mcp = landmarks[mcp_idx]

            # Primary vertical check (Screen coordinates: Y=0 at top)
            y_extended = (tip[1] < pip[1]) and (tip[1] < mcp[1])

            # Radial distance check from wrist (robust when hand is tilted sideways)
            dist_tip_wrist = self.calculate_distance(tip, wrist)
            dist_pip_wrist = self.calculate_distance(pip, wrist)
            radial_extended = dist_tip_wrist > dist_pip_wrist * 1.15

            # Lateral check for pointing left/right
            dx_tip_mcp = abs(tip[0] - mcp[0])
            dy_tip_mcp = abs(tip[1] - mcp[1])
            lateral_extended = (dx_tip_mcp > 1.4 * dy_tip_mcp) and (dist_tip_wrist > dist_pip_wrist)

            states[name] = bool(y_extended or radial_extended or lateral_extended)

        return states

    def classify_raw(
        self,
        hand_data: Dict[str, Any],
    ) -> GestureState:
        """
        Classify raw gesture for a single frame hand detection dictionary.

        :param hand_data: Dict containing 'landmarks', 'label', 'bbox', 'confidence'.
        :return: GestureState dataclass instance.
        """
        landmarks = hand_data.get("landmarks", [])
        hand_label = hand_data.get("label", "Right")
        bbox = hand_data.get("bbox", None)

        if len(landmarks) < 21:
            return GestureState(
                gesture=GestureType.NONE,
                label=GESTURE_METADATA[GestureType.NONE]["label"],
                emoji=GESTURE_METADATA[GestureType.NONE]["emoji"],
                action=GESTURE_METADATA[GestureType.NONE]["action"],
                confidence=0.0,
                finger_states={"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False},
                pinch_distance_norm=999.0,
                raw_pinch_distance=999.0,
                pointer_pos=None,
                hand_label=hand_label,
                bbox=bbox,
            )

        palm_scale = self.get_palm_scale(landmarks)
        finger_states = self.get_finger_states(landmarks, hand_label=hand_label)

        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]
        index_mcp = landmarks[self.INDEX_MCP]
        wrist = landmarks[self.WRIST]

        # Calculate normalized pinch distance (Thumb TIP to Index TIP)
        raw_pinch_dist = self.calculate_distance(thumb_tip, index_tip)
        pinch_dist_norm = raw_pinch_dist / palm_scale

        is_pinching = pinch_dist_norm < self.PINCH_THRESHOLD_NORM

        # Pointer position (Index fingertip coordinates)
        pointer_pos = (index_tip[0], index_tip[1])

        # Finger count
        num_extended = sum(1 for f in ["index", "middle", "ring", "pinky"] if finger_states[f])
        total_extended = num_extended + (1 if finger_states["thumb"] else 0)

        classified = GestureType.NONE
        conf = 0.85

        # ----------------------------------------------------
        # Rule-Based Decision Tree & Geometric Heuristics
        # ----------------------------------------------------

        # 1. OK SIGN: Pinching (Thumb+Index) + Middle, Ring, Pinky are extended
        if is_pinching and finger_states["middle"] and finger_states["ring"] and finger_states["pinky"]:
            classified = GestureType.OK_SIGN
            conf = 0.95

        # 2. PINCH: Thumb & Index tips touching/close, other fingers closed or relaxed
        elif is_pinching and not (finger_states["middle"] and finger_states["ring"] and finger_states["pinky"]):
            classified = GestureType.PINCH
            conf = min(0.98, max(0.70, 1.0 - pinch_dist_norm))

        # 3. OPEN PALM: All 5 fingers (or all 4 main fingers + thumb) extended
        elif total_extended >= 5 or (num_extended == 4 and finger_states["thumb"]):
            classified = GestureType.OPEN_PALM
            conf = 0.96

        # 4. FIST: 0 fingers extended
        elif total_extended == 0 or (num_extended == 0 and not finger_states["thumb"]):
            # Confirm all fingertips are curled close to palm
            classified = GestureType.FIST
            conf = 0.94

        # 5. PEACE / VICTORY: Index & Middle extended, Ring & Pinky curled
        elif finger_states["index"] and finger_states["middle"] and not finger_states["ring"] and not finger_states["pinky"]:
            classified = GestureType.PEACE
            conf = 0.95

        # 6. THUMBS UP / THUMBS DOWN: Thumb extended, 4 main fingers curled
        elif num_extended == 0 and finger_states["thumb"]:
            thumb_mcp = landmarks[self.THUMB_MCP]
            # If thumb tip is significantly higher than thumb MCP -> Thumbs Up
            if thumb_tip[1] < thumb_mcp[1] - (palm_scale * 0.25):
                classified = GestureType.THUMBS_UP
                conf = 0.95
            elif thumb_tip[1] > thumb_mcp[1] + (palm_scale * 0.25):
                classified = GestureType.THUMBS_DOWN
                conf = 0.95
            else:
                classified = GestureType.THUMBS_UP
                conf = 0.80

        # 7. DIRECTIONAL POINTING / LASER POINTER: Only Index finger extended
        elif finger_states["index"] and not finger_states["middle"] and not finger_states["ring"] and not finger_states["pinky"]:
            # Analyze pointing vector (Index MCP -> Index TIP)
            dx = index_tip[0] - index_mcp[0]
            dy = index_tip[1] - index_mcp[1]
            angle_deg = math.degrees(math.atan2(dy, dx))  # 0 = Right, 180/-180 = Left, -90 = Up, 90 = Down

            # Point Right (Vector angle roughly -45 to +45 deg)
            if -45 <= angle_deg <= 45 and abs(dx) > palm_scale * 0.35:
                classified = GestureType.POINT_RIGHT
                conf = 0.92
            # Point Left (Vector angle roughly 135 to 180 or -180 to -135 deg)
            elif (angle_deg >= 135 or angle_deg <= -135) and abs(dx) > palm_scale * 0.35:
                classified = GestureType.POINT_LEFT
                conf = 0.92
            # Pointing Upwards -> Laser Pointer mode
            elif -135 < angle_deg < -45:
                classified = GestureType.INDEX_POINTER
                conf = 0.96
            else:
                classified = GestureType.INDEX_POINTER
                conf = 0.85

        meta = GESTURE_METADATA.get(classified, GESTURE_METADATA[GestureType.NONE])

        return GestureState(
            gesture=classified,
            label=meta["label"],
            emoji=meta["emoji"],
            action=meta["action"],
            confidence=conf,
            finger_states=finger_states,
            pinch_distance_norm=pinch_dist_norm,
            raw_pinch_distance=raw_pinch_dist,
            pointer_pos=pointer_pos,
            hand_label=hand_label,
            bbox=bbox,
        )

    def recognize(
        self,
        hand_data: Dict[str, Any],
        use_smoothing: bool = True,
    ) -> GestureState:
        """
        Classify gesture with optional temporal voting filter.

        :param hand_data: Hand detection dictionary.
        :param use_smoothing: If True, applies rolling window majority vote.
        :return: Smoothed or raw GestureState.
        """
        raw_state = self.classify_raw(hand_data)

        if not use_smoothing or self.smoothing_window <= 1:
            return raw_state

        self._history.append(raw_state.gesture)

        # Compute majority vote in buffer
        counts = Counter(self._history)
        most_common_gesture, freq = counts.most_common(1)[0]
        vote_ratio = freq / len(self._history)

        if vote_ratio >= self.min_confidence:
            stable_gesture = most_common_gesture
            self._last_stable_gesture = stable_gesture
        else:
            stable_gesture = self._last_stable_gesture

        meta = GESTURE_METADATA.get(stable_gesture, GESTURE_METADATA[GestureType.NONE])

        return GestureState(
            gesture=stable_gesture,
            label=meta["label"],
            emoji=meta["emoji"],
            action=meta["action"],
            confidence=vote_ratio if stable_gesture == most_common_gesture else raw_state.confidence,
            finger_states=raw_state.finger_states,
            pinch_distance_norm=raw_state.pinch_distance_norm,
            raw_pinch_distance=raw_state.raw_pinch_distance,
            pointer_pos=raw_state.pointer_pos,
            hand_label=raw_state.hand_label,
            bbox=raw_state.bbox,
        )

    def draw_gesture_hud(
        self,
        frame: np.ndarray,
        gesture_state: GestureState,
        landmarks: Optional[List[Tuple[int, int, float]]] = None,
    ) -> np.ndarray:
        """
        Render real-time gesture badges, pinch vectors, and pointer reticles onto the frame.

        :param frame: BGR input image frame.
        :param gesture_state: Classified GestureState.
        :param landmarks: 21 landmark coordinate list if available.
        :return: Annotated frame.
        """
        if frame is None or frame.size == 0 or gesture_state.gesture == GestureType.NONE:
            return frame

        # 1. Draw Pointer Crosshair if in Pointer Mode
        if gesture_state.gesture in (GestureType.INDEX_POINTER, GestureType.POINT_RIGHT, GestureType.POINT_LEFT):
            if gesture_state.pointer_pos is not None:
                px, py = gesture_state.pointer_pos
                # Glowing outer circle + crosshair
                cv2.circle(frame, (px, py), 12, self.COLOR_POINTER_DOT, 2, cv2.LINE_AA)
                cv2.circle(frame, (px, py), 4, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.line(frame, (px - 16, py), (px + 16, py), self.COLOR_POINTER_DOT, 1, cv2.LINE_AA)
                cv2.line(frame, (px, py - 16), (px, py + 16), self.COLOR_POINTER_DOT, 1, cv2.LINE_AA)

        # 2. Draw Pinch Connecting Line
        if landmarks and len(landmarks) >= 21:
            thumb_pt = (landmarks[self.THUMB_TIP][0], landmarks[self.THUMB_TIP][1])
            index_pt = (landmarks[self.INDEX_TIP][0], landmarks[self.INDEX_TIP][1])

            is_pinch_active = gesture_state.gesture in (GestureType.PINCH, GestureType.OK_SIGN)
            line_color = self.COLOR_PINCH_LINE if is_pinch_active else (180, 180, 180)
            thickness = 3 if is_pinch_active else 1

            cv2.line(frame, thumb_pt, index_pt, line_color, thickness, cv2.LINE_AA)
            mid_x = (thumb_pt[0] + index_pt[0]) // 2
            mid_y = (thumb_pt[1] + index_pt[1]) // 2
            cv2.circle(frame, (mid_x, mid_y), 4, line_color, -1, cv2.LINE_AA)

        # 3. Draw Gesture HUD Pill Badge above Hand Bounding Box
        if gesture_state.bbox is not None:
            x_min, y_min, x_max, y_max = gesture_state.bbox
            hud_text = f"{gesture_state.emoji} {gesture_state.label} -> {gesture_state.action}"

            (tw, th), baseline = cv2.getTextSize(hud_text, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)

            pill_w = tw + 18
            pill_h = th + 14
            pill_x = max(10, x_min)
            pill_y = max(10, y_min - pill_h - 10)

            # Draw background pill with subtle border
            cv2.rectangle(
                frame,
                (pill_x, pill_y),
                (pill_x + pill_w, pill_y + pill_h),
                self.COLOR_HUD_BG,
                -1,
            )
            cv2.rectangle(
                frame,
                (pill_x, pill_y),
                (pill_x + pill_w, pill_y + pill_h),
                self.COLOR_HUD_BORDER,
                1,
                cv2.LINE_AA,
            )

            # Draw text
            cv2.putText(
                frame,
                hud_text,
                (pill_x + 8, pill_y + th + 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                self.COLOR_ACTION_TEXT,
                1,
                cv2.LINE_AA,
            )

        return frame
