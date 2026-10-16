"""
Slide Annotation and Drawing Canvas Engine.
Provides real-time freehand drawing on presentation slides or video frames using Pinch gestures,
with stroke smoothing, custom color palettes, undo operations, and alpha-blending.
"""

from typing import List, Tuple, Dict, Optional, Any
import cv2
import numpy as np


class AnnotationStroke:
    """Represents a continuous drawn stroke."""

    def __init__(self, color: Tuple[int, int, int], thickness: int):
        self.color = color
        self.thickness = thickness
        self.points: List[Tuple[int, int]] = []

    def add_point(self, x: int, y: int) -> None:
        """Append a point to the stroke."""
        self.points.append((x, y))

    def is_empty(self) -> bool:
        """Check if stroke contains points."""
        return len(self.points) == 0


class SlideAnnotator:
    """
    Manages annotation strokes, real-time pen tracking, brush settings,
    and rendering onto display frames or slide decks.
    """

    # BGR Color Tokens
    PALETTE: Dict[str, Tuple[int, int, int]] = {
        "Red": (50, 50, 240),
        "Cyan": (245, 220, 70),
        "Green": (70, 230, 110),
        "Yellow": (50, 220, 255),
        "Purple": (235, 130, 195),
        "White": (250, 250, 250),
        "Eraser": (0, 0, 0),
    }

    BRUSH_SIZES: Dict[str, int] = {
        "Fine (2px)": 2,
        "Medium (4px)": 4,
        "Thick (8px)": 8,
        "Bold (12px)": 12,
    }

    def __init__(self):
        self.is_enabled = True
        self.active_color_name = "Red"
        self.active_color = self.PALETTE["Red"]
        self.active_thickness = 4
        self.is_eraser_mode = False

        self.strokes: List[AnnotationStroke] = []
        self._current_stroke: Optional[AnnotationStroke] = None
        self._is_drawing = False

    def enable(self) -> None:
        """Enable drawing canvas."""
        self.is_enabled = True

    def disable(self) -> None:
        """Disable drawing canvas."""
        self.is_enabled = False
        self.stop_drawing()

    def toggle(self) -> bool:
        """Toggle active state."""
        self.is_enabled = not self.is_enabled
        if not self.is_enabled:
            self.stop_drawing()
        return self.is_enabled

    def set_color(self, color_name: str) -> None:
        """Set active drawing stroke color."""
        if color_name in self.PALETTE:
            self.active_color_name = color_name
            self.active_color = self.PALETTE[color_name]
            self.is_eraser_mode = (color_name == "Eraser")

    def set_thickness(self, thickness: int) -> None:
        """Set stroke line thickness."""
        self.active_thickness = max(1, thickness)

    def start_drawing(self, x: int, y: int) -> None:
        """Begin a new stroke at coordinates (x, y)."""
        if not self.is_enabled:
            return
        self._is_drawing = True
        self._current_stroke = AnnotationStroke(self.active_color, self.active_thickness)
        self._current_stroke.add_point(x, y)
        self.strokes.append(self._current_stroke)

    def continue_drawing(self, x: int, y: int) -> None:
        """Add consecutive point to current drawing stroke."""
        if not self.is_enabled:
            return
        if not self._is_drawing or self._current_stroke is None:
            self.start_drawing(x, y)
            return

        # Avoid redundant duplicate points if finger hasn't moved
        if self._current_stroke.points:
            last_x, last_y = self._current_stroke.points[-1]
            if abs(last_x - x) < 2 and abs(last_y - y) < 2:
                return

        self._current_stroke.add_point(x, y)

    def stop_drawing(self) -> None:
        """Conclude active drawing stroke."""
        self._is_drawing = False
        self._current_stroke = None

    def undo(self) -> bool:
        """Remove most recent stroke."""
        if self.strokes:
            self.strokes.pop()
            return True
        return False

    def clear(self) -> None:
        """Clear all annotation strokes from the canvas."""
        self.strokes.clear()
        self._current_stroke = None
        self._is_drawing = False

    @property
    def stroke_count(self) -> int:
        """Total number of completed strokes."""
        return len(self.strokes)

    def render(self, frame: np.ndarray) -> np.ndarray:
        """
        Render all drawn strokes onto the frame.

        :param frame: BGR input image frame.
        :return: Frame with rendered annotation strokes.
        """
        if not self.is_enabled or not self.strokes or frame is None:
            return frame

        for stroke in self.strokes:
            if len(stroke.points) < 2:
                if len(stroke.points) == 1:
                    cv2.circle(frame, stroke.points[0], stroke.thickness, stroke.color, -1, cv2.LINE_AA)
                continue

            for i in range(1, len(stroke.points)):
                cv2.line(
                    frame,
                    stroke.points[i - 1],
                    stroke.points[i],
                    stroke.color,
                    stroke.thickness,
                    cv2.LINE_AA,
                )

        return frame
