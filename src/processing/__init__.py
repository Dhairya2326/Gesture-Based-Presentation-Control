"""
Video capture and computer vision processing package.
"""

from src.processing.camera import CameraManager
from src.processing.hand_detector import HandDetector
from src.processing.gesture_recognizer import GestureRecognizer, GestureType, GestureState, GESTURE_METADATA

__all__ = ["CameraManager", "HandDetector", "GestureRecognizer", "GestureType", "GestureState", "GESTURE_METADATA"]

