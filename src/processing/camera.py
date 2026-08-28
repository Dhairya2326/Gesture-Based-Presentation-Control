"""
Webcam capture pipeline and CameraManager module using OpenCV.
Provides a thread-safe, non-blocking video capture feed for Tkinter GUI.
"""

import cv2
import numpy as np
import threading
import time
import os
from typing import Tuple, Optional, List


class CameraManager:
    """
    Manages OpenCV VideoCapture in a background thread to prevent GUI freezing.
    Provides thread-safe access to the latest video frame, FPS calculation,
    horizontal mirroring, resolution controls, and mock fallback support.
    """

    RESOLUTIONS = {
        "640x480 (SD)": (640, 480),
        "1280x720 (HD)": (1280, 720),
        "1920x1080 (FHD)": (1920, 1080),
    }

    def __init__(self, device_index: int = 0, resolution: Tuple[int, int] = (1280, 720)):
        self.device_index = device_index
        self.requested_width, self.requested_height = resolution
        self.mirror = True

        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.is_paused = False
        self.is_camera_connected = False

        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._current_frame: Optional[np.ndarray] = None

        # FPS calculation state
        self._fps: float = 0.0
        self._frame_count: int = 0
        self._fps_start_time: float = time.time()
        self._last_frame_time: float = time.time()

        # Fallback test pattern animation state
        self._pattern_angle = 0

    @staticmethod
    def detect_available_cameras(max_tested: int = 3) -> List[int]:
        """Detect available camera device indices."""
        available = []
        for index in range(max_tested):
            try:
                cap = cv2.VideoCapture(index)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        available.append(index)
                    cap.release()
            except Exception:
                pass
        return available if available else [0]

    def start(self) -> bool:
        """Start the background video capture thread."""
        if self.is_running:
            return True

        self._init_capture()
        self.is_running = True
        self.is_paused = False
        self._fps_start_time = time.time()
        self._frame_count = 0

        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return self.is_camera_connected

    def stop(self) -> None:
        """Stop the background capture thread and release hardware resources."""
        self.is_running = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._release_capture()

    def toggle_pause(self) -> bool:
        """Toggle video pause state."""
        self.is_paused = not self.is_paused
        return self.is_paused

    def set_mirror(self, mirror: bool) -> None:
        """Set horizontal mirror mode."""
        self.mirror = mirror

    def set_device(self, device_index: int) -> bool:
        """Switch camera device index."""
        if self.device_index == device_index and self.cap is not None:
            return True

        was_running = self.is_running
        if was_running:
            self.stop()

        self.device_index = device_index

        if was_running:
            return self.start()
        return True

    def set_resolution(self, width: int, height: int) -> bool:
        """Update capture resolution."""
        self.requested_width = width
        self.requested_height = height

        if self.cap is not None and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            return True
        return False

    def get_fps(self) -> float:
        """Return the current measured frames per second (FPS)."""
        return round(self._fps, 1)

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Thread-safe method to get the latest frame.
        Returns (success_flag, bgr_frame).
        If no physical camera is active, returns a generated test card frame.
        """
        with self._lock:
            if self._current_frame is not None:
                return True, self._current_frame.copy()

        if self.is_running:
            fallback = self._generate_fallback_frame()
            return False, fallback

        return False, None

    def capture_snapshot(self, output_dir: str = "assets") -> Optional[str]:
        """Save the current frame to disk as a snapshot image."""
        success, frame = self.get_frame()
        if frame is not None:
            os.makedirs(output_dir, exist_ok=True)
            filename = f"snapshot_{int(time.time())}.jpg"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, frame)
            return filepath
        return None

    def _init_capture(self) -> None:
        """Initialize OpenCV VideoCapture device."""
        try:
            self.cap = cv2.VideoCapture(self.device_index)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.requested_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.requested_height)
                ret, _ = self.cap.read()
                self.is_camera_connected = bool(ret)
            else:
                self.is_camera_connected = False
        except Exception:
            self.is_camera_connected = False

    def _release_capture(self) -> None:
        """Release the OpenCV capture handle."""
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        self.is_camera_connected = False

    def _capture_loop(self) -> None:
        """Background thread loop acquiring frames from the webcam."""
        while self.is_running:
            if self.is_paused:
                time.sleep(0.05)
                continue

            frame = None
            success = False

            if self.cap is not None and self.cap.isOpened():
                success, raw_frame = self.cap.read()
                if success and raw_frame is not None:
                    self.is_camera_connected = True
                    if self.mirror:
                        frame = cv2.flip(raw_frame, 1)
                    else:
                        frame = raw_frame
                else:
                    self.is_camera_connected = False

            if frame is None:
                # Generate synthetic test frame if camera read failed
                frame = self._generate_fallback_frame()

            # Update FPS calculation
            self._frame_count += 1
            now = time.time()
            elapsed = now - self._fps_start_time
            if elapsed >= 0.5:
                self._fps = self._frame_count / elapsed
                self._frame_count = 0
                self._fps_start_time = now

            with self._lock:
                self._current_frame = frame

            # Throttle loop to target ~30-60 FPS
            time.sleep(0.01)

    def _generate_fallback_frame(self) -> np.ndarray:
        """Generate an animated test pattern frame when physical camera is unavailable."""
        h, w = self.requested_height, self.requested_width
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Subtle dark gradient background
        frame[:] = (30, 24, 24)

        # Draw tech grid lines
        for x in range(0, w, 50):
            cv2.line(frame, (x, 0), (x, h), (45, 38, 38), 1)
        for y in range(0, h, 50):
            cv2.line(frame, (0, y), (w, y), (45, 38, 38), 1)

        # Animated radar / sweep circle
        self._pattern_angle = (self._pattern_angle + 4) % 360
        center = (w // 2, h // 2 - 20)
        radius = min(w, h) // 4
        cv2.circle(frame, center, radius, (70, 60, 60), 2)
        cv2.circle(frame, center, 8, (161, 227, 166), -1)

        rad = np.deg2rad(self._pattern_angle)
        end_pt = (int(center[0] + radius * np.cos(rad)), int(center[1] + radius * np.sin(rad)))
        cv2.line(frame, center, end_pt, (137, 180, 250), 2)

        # Informational Banner
        title = "WEBCAM TEST PATTERN / NO FEED"
        subtitle = f"Device Index: {self.device_index} | Resolution: {w}x{h}"
        hint = "Connect a webcam or select another device from the Controls."

        cv2.putText(frame, title, (w // 2 - 220, h // 2 + radius + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (243, 139, 168), 2)
        cv2.putText(frame, subtitle, (w // 2 - 200, h // 2 + radius + 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (205, 214, 244), 1)
        cv2.putText(frame, hint, (w // 2 - 240, h // 2 + radius + 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (166, 173, 200), 1)

        return frame
