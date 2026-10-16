"""
Virtual Laser Pointer engine for gesture-driven screen tracking and crosshair rendering.
Provides exponential moving average coordinate smoothing, active bounding-zone normalization,
and PyAutoGUI OS cursor automation.
"""

from collections import deque
from typing import Tuple, Optional, List, Dict
import cv2
import numpy as np

try:
    import pyautogui
    HAS_PYAUTOGUI = True
    SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
except Exception:
    HAS_PYAUTOGUI = False
    SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080


class LaserPointer:
    """
    Tracks hand index fingertip, applies low-pass temporal smoothing, maps camera coordinates
    to full-screen presentation display, and renders high-visibility virtual laser optics.
    """

    # Color tokens in BGR
    COLOR_LASER_CORE = (255, 255, 255)       # Pure white hot center
    COLOR_RED_GLOW = (40, 50, 245)           # Neon Red / Coral
    COLOR_GREEN_GLOW = (80, 235, 120)        # Laser Green
    COLOR_CYAN_GLOW = (245, 220, 70)         # Electric Cyan
    COLOR_GOLD_GLOW = (60, 215, 255)         # Golden Amber

    COLOR_PRESETS: Dict[str, Tuple[int, int, int]] = {
        "Red": COLOR_RED_GLOW,
        "Green": COLOR_GREEN_GLOW,
        "Cyan": COLOR_CYAN_GLOW,
        "Gold": COLOR_GOLD_GLOW,
    }

    def __init__(
        self,
        smoothing_factor: float = 0.45,
        trail_length: int = 8,
        active_margin: float = 0.12,
        move_os_cursor: bool = False,
    ):
        """
        Initialize the Laser Pointer.

        :param smoothing_factor: Exponential moving average alpha (0.1 = heavy smooth, 0.9 = raw).
        :param trail_length: Number of past trail points to render for laser beam effect.
        :param active_margin: Fractional margin inside camera frame mapped to full screen (0.0 to 0.25).
        :param move_os_cursor: Whether to automatically move OS mouse cursor using PyAutoGUI.
        """
        self.is_enabled = True
        self.smoothing_factor = max(0.05, min(0.95, smoothing_factor))
        self.trail_length = max(0, trail_length)
        self.active_margin = max(0.0, min(0.35, active_margin))
        self.move_os_cursor = move_os_cursor
        self.laser_color_name = "Red"
        self.laser_color = self.COLOR_RED_GLOW

        # Coordinates tracking
        self._current_pos: Optional[Tuple[int, int]] = None
        self._screen_pos: Optional[Tuple[int, int]] = None
        self._trail: deque = deque(maxlen=self.trail_length)

    def enable(self) -> None:
        """Enable virtual laser pointer."""
        self.is_enabled = True

    def disable(self) -> None:
        """Disable virtual laser pointer."""
        self.is_enabled = False
        self.reset()

    def toggle(self) -> bool:
        """Toggle active state."""
        self.is_enabled = not self.is_enabled
        if not self.is_enabled:
            self.reset()
        return self.is_enabled

    def set_color(self, color_name: str) -> None:
        """Select laser glow color preset."""
        if color_name in self.COLOR_PRESETS:
            self.laser_color_name = color_name
            self.laser_color = self.COLOR_PRESETS[color_name]

    def set_smoothing(self, factor: float) -> None:
        """Update smoothing factor."""
        self.smoothing_factor = max(0.05, min(0.95, factor))

    def reset(self) -> None:
        """Reset internal positions and clear trail."""
        self._current_pos = None
        self._screen_pos = None
        self._trail.clear()

    def update_position(
        self,
        raw_x: int,
        raw_y: int,
        frame_width: int,
        frame_height: int,
    ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Apply EMA smoothing and compute both frame coordinates and mapped screen coordinates.

        :param raw_x: Raw pixel X coordinate in frame.
        :param raw_y: Raw pixel Y coordinate in frame.
        :param frame_width: Current frame width.
        :param frame_height: Current frame height.
        :return: (smoothed_frame_pos, mapped_screen_pos)
        """
        # 1. Apply Exponential Moving Average (EMA) to frame coordinates
        if self._current_pos is None:
            smooth_x, smooth_y = float(raw_x), float(raw_y)
        else:
            prev_x, prev_y = self._current_pos
            smooth_x = self.smoothing_factor * raw_x + (1.0 - self.smoothing_factor) * prev_x
            smooth_y = self.smoothing_factor * raw_y + (1.0 - self.smoothing_factor) * prev_y

        frame_pos = (int(smooth_x), int(smooth_y))
        self._current_pos = frame_pos
        self._trail.append(frame_pos)

        # 2. Map frame coordinates to screen coordinates via active tracking margin
        # Clamps edges so presenter does not need to reach camera extremes
        margin_x = int(frame_width * self.active_margin)
        margin_y = int(frame_height * self.active_margin)

        clamped_x = max(margin_x, min(frame_width - margin_x, smooth_x))
        clamped_y = max(margin_y, min(frame_height - margin_y, smooth_y))

        effective_w = max(1, frame_width - 2 * margin_x)
        effective_h = max(1, frame_height - 2 * margin_y)

        norm_x = (clamped_x - margin_x) / effective_w
        norm_y = (clamped_y - margin_y) / effective_h

        # Screen coordinates
        screen_x = int(norm_x * SCREEN_WIDTH)
        screen_y = int(norm_y * SCREEN_HEIGHT)
        screen_pos = (screen_x, screen_y)
        self._screen_pos = screen_pos

        # 3. Optional PyAutoGUI OS mouse cursor automation
        if self.move_os_cursor and self.is_enabled and HAS_PYAUTOGUI:
            try:
                pyautogui.moveTo(screen_x, screen_y, _pause=False)
            except Exception:
                pass

        return frame_pos, screen_pos

    def render_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Render dynamic glowing laser pointer optics with trailing decay onto frame.

        :param frame: BGR input image frame.
        :return: Annotated frame with laser pointer optics.
        """
        if not self.is_enabled or self._current_pos is None or frame is None:
            return frame

        # Render trailing motion beam
        if len(self._trail) > 1:
            points = list(self._trail)
            for i in range(1, len(points)):
                # Decaying alpha and thickness for trail
                progress = i / len(points)
                alpha_thickness = max(1, int(progress * 4))
                # Fade color towards black
                trail_color = tuple(int(c * progress * 0.7) for c in self.laser_color)
                cv2.line(frame, points[i - 1], points[i], trail_color, alpha_thickness, cv2.LINE_AA)

        px, py = self._current_pos

        # Multi-layer optical glow
        # Layer 1: Outermost translucent atmospheric halo
        overlay = frame.copy()
        cv2.circle(overlay, (px, py), 22, self.laser_color, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.22, frame, 0.78, 0, frame)

        # Layer 2: Medium glow ring
        cv2.circle(frame, (px, py), 12, self.laser_color, 2, cv2.LINE_AA)

        # Layer 3: Solid intense inner dot
        cv2.circle(frame, (px, py), 6, self.laser_color, -1, cv2.LINE_AA)

        # Layer 4: Hot white core
        cv2.circle(frame, (px, py), 3, self.COLOR_LASER_CORE, -1, cv2.LINE_AA)

        return frame
