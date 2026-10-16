"""
Built-in Presentation Slide Deck Renderer.
Generates styled, high-resolution presentation slides dynamically for in-app presentation mode,
allowing seamless demonstration of slide navigation, laser pointer, and annotation drawing.
"""

from typing import List, Dict, Any, Tuple
import cv2
import numpy as np


class SlideDeck:
    """
    Manages slide content and generates slide frames at arbitrary resolutions.
    """

    SLIDES: List[Dict[str, Any]] = [
        {
            "slide_num": 1,
            "category": "PROJECT OVERVIEW",
            "title": "Gesture-Based Presentation Control",
            "subtitle": "Human-Computer Interaction using Computer Vision & Hand Landmark Tracking",
            "points": [
                "Contactless, natural presentation navigation using standard consumer webcams",
                "Eliminates dependency on handheld remotes, hardware clickers, and tethered devices",
                "Real-time 21 3D hand landmark tracking powered by MediaPipe Hands",
                "End Semester Project - Computer Graphics & Image Processing (CGIP)",
            ],
            "footer": "Team: Dhairya Patel (24001142) • Dhruv Pankhania (24001158) • Krish Jadav (24000638)",
            "accent": (235, 140, 198),  # Lavender
        },
        {
            "slide_num": 2,
            "category": "PROBLEM STATEMENT & MOTIVATION",
            "title": "Motivation & Key Objectives",
            "subtitle": "Addressing the limitations of conventional presentation controllers",
            "points": [
                "Hardware Clickers: Frequent battery failures, loss of remotes, and presenter tethering",
                "Color/Skin Segmentation: Fails under dynamic lighting, shadows, and varying skin tones",
                "Wearable Sensor Gloves: Prohibitively expensive, bulky, and intrusive to wear",
                "Our Solution: Robust, vision-only geometric gesture classifier running at 40+ FPS on CPU",
                "Goal: Sub-50ms latency with >95% classification accuracy across lighting environments",
            ],
            "footer": "Navrachana University - School of Engineering & Technology",
            "accent": (137, 214, 230),  # Cyan
        },
        {
            "slide_num": 3,
            "category": "SYSTEM ARCHITECTURE",
            "title": "Multi-Stage Computer Vision Pipeline",
            "subtitle": "From raw webcam capture to OS-level presentation automation",
            "points": [
                "Stage 1: Multi-threaded OpenCV frame acquisition with real-time FPS counter",
                "Stage 2: MediaPipe BlazePalm detector + 21 3D hand landmark regressor",
                "Stage 3: Hand scale normalization using wrist-to-MCP Euclidean baseline",
                "Stage 4: Geometric finger extension state analysis and pinch distance vector",
                "Stage 5: Temporal majority-voting filter to eliminate single-frame jitter",
                "Stage 6: PyAutoGUI OS automation & active presentation profile dispatch",
            ],
            "footer": "Pipeline Latency: ~23ms End-to-End | Throughput: 43 FPS",
            "accent": (161, 227, 166),  # Soft Green
        },
        {
            "slide_num": 4,
            "category": "GESTURE RECOGNITION MATRIX",
            "title": "Natural Hand Gesture Mappings",
            "subtitle": "Ergonomic, intuitive gestures mapped to presentation controls",
            "points": [
                "👉 Point Right: Navigate to Next Slide (Right Arrow key)",
                "👈 Point Left: Navigate to Previous Slide (Left Arrow key)",
                "👆 Index Finger: Virtual Laser Pointer with optical glow & screen tracking",
                "🤏 Pinch (Thumb + Index): Slide Annotation & Freehand Pen Drawing",
                "👌 OK Sign: Toggle Fullscreen Presentation Mode (F5 / F)",
                "✊ Closed Fist: Pause / Neutral Lock to prevent unintended triggers",
                "👍 / 👎 Thumbs Up / Down: Volume Control & Confirmation",
            ],
            "footer": "Configurable Action Debounce Cooldown: 0.5s - 2.0s",
            "accent": (175, 226, 249),  # Golden Yellow
        },
        {
            "slide_num": 5,
            "category": "EXPERIMENTAL RESULTS & BENCHMARKS",
            "title": "Performance Evaluation & Profiling",
            "subtitle": "Rigorous latency profiling across resolutions and hardware loads",
            "points": [
                "End-to-End Processing Latency: 23.1 ms mean (Target: < 50 ms)",
                "95th Percentile Latency (P95): 24.6 ms under standard 720p stream",
                "Hand Detection Inference: ~19.5 ms on standard Intel/AMD CPU",
                "Gesture Classification: 0.19 ms (ultra-fast geometric heuristics)",
                "Laser & Drawing Render: ~3.4 ms with multi-layer glowing optics",
                "Peak Memory Footprint: ~10.7 MB dynamic allocation overhead",
            ],
            "footer": "Verified with automated benchmark suite (tests/benchmark.py)",
            "accent": (250, 179, 135),  # Orange
        },
        {
            "slide_num": 6,
            "category": "CONCLUSION & FUTURE ENHANCEMENTS",
            "title": "Summary & Future Roadmap",
            "subtitle": "Complete contactless presentation controller milestone achieved",
            "points": [
                "Successfully implemented full 10-week development curriculum",
                "Cross-platform support: PowerPoint, Google Slides, Adobe PDF, Media Player",
                "Features interactive virtual laser pointer, drawing pen, and telemetry",
                "Future Scope: Multi-presenter hand arbitration & dynamic hand-over detection",
                "Future Scope: Voice command fusion for multimodal presentation interaction",
            ],
            "footer": "Gesture-Based Presentation Control - Milestone Week 10 Completed",
            "accent": (203, 166, 247),  # Mauve
        },
    ]

    @classmethod
    def get_slide_count(cls) -> int:
        """Total number of slides."""
        return len(cls.SLIDES)

    @classmethod
    def render_slide(
        cls,
        slide_index: int,
        width: int = 1280,
        height: int = 720,
    ) -> np.ndarray:
        """
        Render a presentation slide at specified dimensions as a BGR numpy array.

        :param slide_index: 1-indexed slide number.
        :param width: Target width in pixels.
        :param height: Target height in pixels.
        :return: Rendered slide frame.
        """
        idx = max(0, min(len(cls.SLIDES) - 1, slide_index - 1))
        data = cls.SLIDES[idx]

        # Background gradient: Deep obsidian navy (#0f111a to #1a1b26)
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (26, 17, 15)  # Dark background

        # Subtle top accent bar
        accent_color = data["accent"]
        cv2.rectangle(frame, (0, 0), (width, 8), accent_color, -1)

        # Slide Number Badge (Top Right)
        badge_text = f"SLIDE {data['slide_num']} / {len(cls.SLIDES)}"
        cv2.putText(
            frame,
            badge_text,
            (width - 180, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            accent_color,
            2,
            cv2.LINE_AA,
        )

        # Category pill (Top Left)
        cat_text = data["category"]
        cv2.putText(
            frame,
            cat_text,
            (60, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (150, 155, 175),
            1,
            cv2.LINE_AA,
        )

        # Title
        title_text = data["title"]
        cv2.putText(
            frame,
            title_text,
            (60, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.15,
            (240, 245, 255),
            2,
            cv2.LINE_AA,
        )

        # Subtitle
        sub_text = data["subtitle"]
        cv2.putText(
            frame,
            sub_text,
            (60, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            accent_color,
            1,
            cv2.LINE_AA,
        )

        # Divider line
        cv2.line(frame, (60, 175), (width - 60, 175), (60, 65, 85), 1, cv2.LINE_AA)

        # Bullet Points
        start_y = 240
        line_spacing = 65

        for i, pt in enumerate(data["points"]):
            y_pos = start_y + i * line_spacing
            if y_pos > height - 100:
                break

            # Bullet dot
            cv2.circle(frame, (75, y_pos - 6), 6, accent_color, -1, cv2.LINE_AA)
            cv2.circle(frame, (75, y_pos - 6), 9, accent_color, 1, cv2.LINE_AA)

            # Bullet text
            cv2.putText(
                frame,
                pt,
                (105, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.68,
                (220, 225, 240),
                1,
                cv2.LINE_AA,
            )

        # Footer divider and text
        cv2.line(frame, (60, height - 60), (width - 60, height - 60), (45, 50, 70), 1, cv2.LINE_AA)
        cv2.putText(
            frame,
            data["footer"],
            (60, height - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (120, 125, 150),
            1,
            cv2.LINE_AA,
        )

        return frame
