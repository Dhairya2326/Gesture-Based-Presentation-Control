"""
Presentation controller interface and keyboard automation mappings.
Prepared for integration with PyAutoGUI in Weeks 6-7.
"""

import time
from typing import Optional, Callable


class PresentationController:
    """
    Simulates slide navigation keystrokes and maintains presentation state.
    """

    def __init__(self):
        self.is_enabled = False
        self.last_action_time = 0.0
        self.cooldown_seconds = 1.0  # Gesture debounce cooldown

    def enable(self) -> None:
        self.is_enabled = True

    def disable(self) -> None:
        self.is_enabled = False

    def can_trigger(self) -> bool:
        """Check if gesture debounce cooldown has elapsed."""
        return (time.time() - self.last_action_time) >= self.cooldown_seconds

    def next_slide(self) -> bool:
        """Trigger next slide action."""
        if not self.is_enabled or not self.can_trigger():
            return False
        self.last_action_time = time.time()
        # In future weeks: pyautogui.press('right')
        return True

    def prev_slide(self) -> bool:
        """Trigger previous slide action."""
        if not self.is_enabled or not self.can_trigger():
            return False
        self.last_action_time = time.time()
        # In future weeks: pyautogui.press('left')
        return True
