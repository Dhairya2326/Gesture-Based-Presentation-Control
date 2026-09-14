"""
Presentation controller interface and keyboard automation mappings.
Simulates slide navigation keystrokes, laser pointer toggling, and presentation actions.
"""

import time
from typing import Optional, Callable, Dict, List, Any
from src.processing.gesture_recognizer import GestureType, GestureState


class PresentationController:
    """
    Manages presentation state, gesture action dispatching, debounce cooldowns,
    and simulated navigation events.
    """

    def __init__(self, cooldown_seconds: float = 1.0):
        self.is_enabled = True
        self.cooldown_seconds = max(0.2, cooldown_seconds)
        self.last_action_time = 0.0
        self.last_action_name = "None"
        self.action_history: List[Dict[str, Any]] = []
        self._on_action_callback: Optional[Callable[[str, GestureState], None]] = None

    def enable(self) -> None:
        """Enable gesture-driven presentation control actions."""
        self.is_enabled = True

    def disable(self) -> None:
        """Disable presentation control actions."""
        self.is_enabled = False

    def toggle(self) -> bool:
        """Toggle active state."""
        self.is_enabled = not self.is_enabled
        return self.is_enabled

    def set_cooldown(self, seconds: float) -> None:
        """Update cooldown debounce threshold."""
        self.cooldown_seconds = max(0.2, seconds)

    def set_action_callback(self, callback: Callable[[str, GestureState], None]) -> None:
        """Register listener callback invoked when a presentation action executes."""
        self._on_action_callback = callback

    def can_trigger(self) -> bool:
        """Check if gesture debounce cooldown has elapsed."""
        return (time.time() - self.last_action_time) >= self.cooldown_seconds

    def handle_gesture(self, gesture_state: GestureState) -> Optional[str]:
        """
        Evaluate recognized gesture and execute associated presentation action if cooldown permits.

        :param gesture_state: Current classified GestureState.
        :return: Action name if triggered, else None.
        """
        if not self.is_enabled:
            return None

        gesture = gesture_state.gesture

        # Continuous gestures (Pointer, Pinch) do not require discrete cooldown blocking
        if gesture == GestureType.INDEX_POINTER:
            return "LASER_POINTER"
        if gesture == GestureType.PINCH:
            return "DRAWING_PEN"

        # Discrete trigger gestures require cooldown check
        if not self.can_trigger():
            return None

        action_triggered: Optional[str] = None

        if gesture == GestureType.POINT_RIGHT:
            action_triggered = "NEXT_SLIDE"
        elif gesture == GestureType.POINT_LEFT:
            action_triggered = "PREV_SLIDE"
        elif gesture == GestureType.OK_SIGN:
            action_triggered = "FULLSCREEN_TOGGLE"
        elif gesture == GestureType.THUMBS_UP:
            action_triggered = "VOLUME_UP"
        elif gesture == GestureType.THUMBS_DOWN:
            action_triggered = "VOLUME_DOWN"
        elif gesture == GestureType.FIST:
            action_triggered = "PAUSE_NAVIGATION"

        if action_triggered:
            self.last_action_time = time.time()
            self.last_action_name = action_triggered
            self.action_history.append({
                "action": action_triggered,
                "gesture": gesture.value,
                "time": self.last_action_time,
            })
            if self._on_action_callback:
                self._on_action_callback(action_triggered, gesture_state)

        return action_triggered

    def next_slide(self) -> bool:
        """Trigger next slide navigation."""
        if not self.is_enabled or not self.can_trigger():
            return False
        self.last_action_time = time.time()
        self.last_action_name = "NEXT_SLIDE"
        return True

    def prev_slide(self) -> bool:
        """Trigger previous slide navigation."""
        if not self.is_enabled or not self.can_trigger():
            return False
        self.last_action_time = time.time()
        self.last_action_name = "PREV_SLIDE"
        return True

