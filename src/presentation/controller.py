"""
Presentation controller interface and keyboard automation mappings.
Simulates slide navigation keystrokes, laser pointer toggling, and presentation actions
via PyAutoGUI across multiple target software profiles (PowerPoint, Google Slides, PDF, Media).
"""

import time
from enum import Enum
from typing import Optional, Callable, Dict, List, Any, Tuple
from src.processing.gesture_recognizer import GestureType, GestureState

try:
    import pyautogui
    # Configure PyAutoGUI safe defaults
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    HAS_PYAUTOGUI = True
except Exception:
    HAS_PYAUTOGUI = False


class TargetProfile(Enum):
    """Supported target presentation software profiles."""
    POWERPOINT = "PowerPoint"
    GOOGLE_SLIDES = "Google Slides"
    PDF_VIEWER = "PDF Viewer"
    MEDIA_PLAYER = "Media Player"
    GENERAL = "General"


class ControllerMode(Enum):
    """Operation mode: Live OS keystroke execution vs safe simulation."""
    LIVE_OS = "Live OS"
    SIMULATION = "Simulation"


# Keystroke mappings per profile for various presentation actions
PROFILE_KEYMAPS: Dict[TargetProfile, Dict[str, List[str]]] = {
    TargetProfile.POWERPOINT: {
        "NEXT_SLIDE": ["right"],
        "PREV_SLIDE": ["left"],
        "FIRST_SLIDE": ["home"],
        "LAST_SLIDE": ["end"],
        "FULLSCREEN_TOGGLE": ["f5"],
        "EXIT_SLIDESHOW": ["esc"],
        "PAUSE_NAVIGATION": ["b"],        # 'b' turns screen black in PowerPoint
        "VOLUME_UP": ["volumeup"],
        "VOLUME_DOWN": ["volumedown"],
        "LASER_POINTER": ["ctrl", "l"],   # PowerPoint native laser shortcut
        "DRAWING_PEN": ["ctrl", "p"],     # PowerPoint native pen shortcut
    },
    TargetProfile.GOOGLE_SLIDES: {
        "NEXT_SLIDE": ["right"],
        "PREV_SLIDE": ["left"],
        "FIRST_SLIDE": ["home"],
        "LAST_SLIDE": ["end"],
        "FULLSCREEN_TOGGLE": ["f"],       # 'f' enters presenter view in Google Slides
        "EXIT_SLIDESHOW": ["esc"],
        "PAUSE_NAVIGATION": ["b"],
        "VOLUME_UP": ["volumeup"],
        "VOLUME_DOWN": ["volumedown"],
        "LASER_POINTER": ["l"],           # Google Slides laser pointer toggle
        "DRAWING_PEN": ["p"],
    },
    TargetProfile.PDF_VIEWER: {
        "NEXT_SLIDE": ["right"],
        "PREV_SLIDE": ["left"],
        "FIRST_SLIDE": ["home"],
        "LAST_SLIDE": ["end"],
        "FULLSCREEN_TOGGLE": ["ctrl", "l"], # Adobe Acrobat / Foxit fullscreen
        "EXIT_SLIDESHOW": ["esc"],
        "PAUSE_NAVIGATION": ["space"],
        "VOLUME_UP": ["volumeup"],
        "VOLUME_DOWN": ["volumedown"],
        "LASER_POINTER": ["ctrl", "l"],
        "DRAWING_PEN": ["ctrl", "d"],
    },
    TargetProfile.MEDIA_PLAYER: {
        "NEXT_SLIDE": ["right"],          # Seek forward
        "PREV_SLIDE": ["left"],           # Seek backward
        "FIRST_SLIDE": ["home"],
        "LAST_SLIDE": ["end"],
        "FULLSCREEN_TOGGLE": ["f"],
        "EXIT_SLIDESHOW": ["esc"],
        "PAUSE_NAVIGATION": ["space"],    # Play / Pause
        "VOLUME_UP": ["volumeup"],
        "VOLUME_DOWN": ["volumedown"],
        "LASER_POINTER": ["l"],
        "DRAWING_PEN": ["d"],
    },
    TargetProfile.GENERAL: {
        "NEXT_SLIDE": ["right"],
        "PREV_SLIDE": ["left"],
        "FIRST_SLIDE": ["home"],
        "LAST_SLIDE": ["end"],
        "FULLSCREEN_TOGGLE": ["f11"],
        "EXIT_SLIDESHOW": ["esc"],
        "PAUSE_NAVIGATION": ["space"],
        "VOLUME_UP": ["volumeup"],
        "VOLUME_DOWN": ["volumedown"],
        "LASER_POINTER": ["ctrl", "l"],
        "DRAWING_PEN": ["ctrl", "p"],
    },
}


class PresentationController:
    """
    Manages presentation state, gesture action dispatching, debounce cooldowns,
    slide indexing, and PyAutoGUI OS-level presentation automation.
    """

    def __init__(
        self,
        cooldown_seconds: float = 1.0,
        mode: ControllerMode = ControllerMode.LIVE_OS,
        profile: TargetProfile = TargetProfile.POWERPOINT,
        total_slides: int = 15,
    ):
        self.is_enabled = True
        self.cooldown_seconds = max(0.2, cooldown_seconds)
        self.mode = mode
        self.profile = profile
        self.last_action_time = 0.0
        self.last_action_name = "None"
        self.action_history: List[Dict[str, Any]] = []
        self._on_action_callback: Optional[Callable[[str, GestureState], None]] = None

        # Virtual Slide Deck state (for in-app presentation preview & tracking)
        self.total_slides = max(1, total_slides)
        self.current_slide = 1
        self.is_fullscreen = False
        self.is_paused = False

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

    def set_mode(self, mode: ControllerMode) -> None:
        """Switch between Live OS keystrokes and Simulation mode."""
        self.mode = mode

    def toggle_mode(self) -> ControllerMode:
        """Toggle between Live OS and Simulation mode."""
        if self.mode == ControllerMode.LIVE_OS:
            self.mode = ControllerMode.SIMULATION
        else:
            self.mode = ControllerMode.LIVE_OS
        return self.mode

    def set_profile(self, profile: TargetProfile) -> None:
        """Set the active presentation software target profile."""
        self.profile = profile

    def set_cooldown(self, seconds: float) -> None:
        """Update cooldown debounce threshold."""
        self.cooldown_seconds = max(0.2, seconds)

    def set_total_slides(self, count: int) -> None:
        """Update total slide count."""
        self.total_slides = max(1, count)
        if self.current_slide > self.total_slides:
            self.current_slide = self.total_slides

    def set_action_callback(self, callback: Callable[[str, GestureState], None]) -> None:
        """Register listener callback invoked when a presentation action executes."""
        self._on_action_callback = callback

    def can_trigger(self) -> bool:
        """Check if gesture debounce cooldown has elapsed."""
        return (time.time() - self.last_action_time) >= self.cooldown_seconds

    def execute_action(self, action_name: str) -> bool:
        """
        Execute OS keystroke mapped to action_name using active profile if in Live OS mode.
        """
        keymap = PROFILE_KEYMAPS.get(self.profile, PROFILE_KEYMAPS[TargetProfile.GENERAL])
        keys = keymap.get(action_name)

        if not keys:
            return False

        # Update internal slide deck state
        if action_name == "NEXT_SLIDE":
            if self.current_slide < self.total_slides:
                self.current_slide += 1
        elif action_name == "PREV_SLIDE":
            if self.current_slide > 1:
                self.current_slide -= 1
        elif action_name == "FIRST_SLIDE":
            self.current_slide = 1
        elif action_name == "LAST_SLIDE":
            self.current_slide = self.total_slides
        elif action_name == "FULLSCREEN_TOGGLE":
            self.is_fullscreen = not self.is_fullscreen
        elif action_name == "PAUSE_NAVIGATION":
            self.is_paused = not self.is_paused

        # Dispatch keystrokes to OS if in Live OS mode
        if self.mode == ControllerMode.LIVE_OS and HAS_PYAUTOGUI:
            try:
                if len(keys) == 1:
                    pyautogui.press(keys[0])
                else:
                    pyautogui.hotkey(*keys)
            except Exception:
                # Catch any OS permissions or screen lock exceptions safely
                return False

        return True

    def handle_gesture(self, gesture_state: GestureState) -> Optional[str]:
        """
        Evaluate recognized gesture and execute associated presentation action if cooldown permits.

        :param gesture_state: Current classified GestureState.
        :return: Action name if triggered, else None.
        """
        if not self.is_enabled:
            return None

        gesture = gesture_state.gesture

        # Continuous gestures (Pointer, Pinch) do not trigger discrete keystroke cooldowns
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

            success = self.execute_action(action_triggered)

            self.action_history.append({
                "action": action_triggered,
                "gesture": gesture.value,
                "time": self.last_action_time,
                "profile": self.profile.value,
                "mode": self.mode.value,
                "success": success,
                "slide": self.current_slide,
            })

            if self._on_action_callback:
                self._on_action_callback(action_triggered, gesture_state)

        return action_triggered

    def next_slide(self) -> bool:
        """Trigger next slide navigation programmatically."""
        if not self.is_enabled or not self.can_trigger():
            return False
        self.last_action_time = time.time()
        self.last_action_name = "NEXT_SLIDE"
        return self.execute_action("NEXT_SLIDE")

    def prev_slide(self) -> bool:
        """Trigger previous slide navigation programmatically."""
        if not self.is_enabled or not self.can_trigger():
            return False
        self.last_action_time = time.time()
        self.last_action_name = "PREV_SLIDE"
        return self.execute_action("PREV_SLIDE")

    def goto_slide(self, slide_num: int) -> bool:
        """Jump to a specific slide index."""
        if 1 <= slide_num <= self.total_slides:
            self.current_slide = slide_num
            return True
        return False
