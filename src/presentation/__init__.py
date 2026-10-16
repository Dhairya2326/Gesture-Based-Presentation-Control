"""
Presentation control and annotation package.
"""

from src.presentation.controller import (
    PresentationController,
    TargetProfile,
    ControllerMode,
    PROFILE_KEYMAPS,
)
from src.presentation.laser_pointer import LaserPointer
from src.presentation.annotator import SlideAnnotator, AnnotationStroke
from src.presentation.slides import SlideDeck

__all__ = [
    "PresentationController",
    "TargetProfile",
    "ControllerMode",
    "PROFILE_KEYMAPS",
    "LaserPointer",
    "SlideAnnotator",
    "AnnotationStroke",
    "SlideDeck",
]
