"""
Main Tkinter Graphical User Interface for Gesture-Based Presentation Control.
Integrates OpenCV camera feed, MediaPipe 21 3D hand tracking, geometric gesture recognition,
PyAutoGUI presentation automation, virtual laser pointer, drawing canvas, and real-time benchmarking.
Milestone: Week 10 (Full System Complete - End Sem Final Implementation).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import time
import os
import threading
from typing import Optional, List, Dict, Any, Tuple

from src.gui import styles
from src.processing.camera import CameraManager
from src.processing.hand_detector import HandDetector
from src.processing.gesture_recognizer import (
    GestureRecognizer,
    GestureType,
    GestureState,
    GESTURE_METADATA,
)
from src.processing.benchmarking import PipelineLatencyTracker, BenchmarkSuite
from src.presentation.controller import (
    PresentationController,
    TargetProfile,
    ControllerMode,
)
from src.presentation.laser_pointer import LaserPointer
from src.presentation.annotator import SlideAnnotator
from src.presentation.slides import SlideDeck


class PresentationControllerApp:
    """
    Complete Desktop Command Center embedding:
    - Multi-threaded OpenCV video pipeline
    - MediaPipe 21 3D hand landmarks skeleton & bounding box tracking
    - Real-time geometric gesture classifier with temporal voting
    - PyAutoGUI OS slide navigation (PowerPoint, Google Slides, PDF, Media)
    - Virtual Laser Pointer with optical glow & screen coordinate mapping
    - Slide Annotation & Drawing Canvas with custom palettes & undo
    - In-App Interactive Presentation Slide Deck Viewer with Camera PiP
    - Real-time pipeline latency profiler and automated benchmark runner
    """

    def __init__(self, root: tk.Tk, camera_index: int = 0):
        self.root = root
        self.root.title("Gesture-Based Presentation Controller (End Sem Project)")
        self.root.geometry("1340x880")
        self.root.minsize(1120, 740)
        self.root.configure(bg=styles.BG_DARK)

        # Initialize Hardware & Processing Engines
        self.camera = CameraManager(device_index=camera_index, resolution=(1280, 720))
        self.hand_detector = HandDetector(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )
        self.gesture_recognizer = GestureRecognizer(
            smoothing_window=5,
            min_confidence=0.6,
        )
        self.controller = PresentationController(
            cooldown_seconds=1.0,
            mode=ControllerMode.LIVE_OS,
            profile=TargetProfile.POWERPOINT,
            total_slides=SlideDeck.get_slide_count(),
        )
        self.controller.set_action_callback(self._on_presentation_action_triggered)

        self.laser_pointer = LaserPointer(smoothing_factor=0.45, trail_length=8)
        self.annotator = SlideAnnotator()
        self.latency_tracker = PipelineLatencyTracker(history_size=60)

        # Feature Toggles & View Modes
        self.enable_hand_tracking = True
        self.enable_bounding_box = True
        self.enable_gesture_recognition = True
        self.enable_gesture_hud = True
        self.enable_laser_pointer = True
        self.enable_annotation = True
        self.view_mode = "CAMERA"  # "CAMERA" or "SLIDES"
        self.show_camera_pip = True

        # State tracking
        self._last_hand_count = 0
        self._last_recognized_gesture: GestureType = GestureType.NONE
        self._current_photo_image: Optional[ImageTk.PhotoImage] = None
        self._is_closing = False
        self._benchmarking_active = False

        # Build UI layout
        self._setup_styles()
        self._build_header()
        self._build_main_content()
        self._build_footer()
        self._bind_shortcuts()

        # Handle graceful window exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start camera stream on startup
        self.log_message("System initialized. Starting Camera, MediaPipe & Presentation Engines...")
        self.camera.start()
        self._update_ui_state()

        # Start frame refresh loop
        self._refresh_frame_loop()

    def _setup_styles(self) -> None:
        """Configure ttk styles for uniform dark theme widgets and tabs."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Combobox style
        self.style.configure(
            "TCombobox",
            fieldbackground=styles.BG_INPUT,
            background=styles.BG_CARD,
            foreground=styles.TEXT_PRIMARY,
            arrowcolor=styles.TEXT_PRIMARY,
            bordercolor=styles.BORDER_COLOR,
            darkcolor=styles.BG_INPUT,
            lightcolor=styles.BG_INPUT,
        )

        # Notebook tabs style
        self.style.configure(
            "TNotebook",
            background=styles.BG_DARK,
            borderwidth=0,
        )
        self.style.configure(
            "TNotebook.Tab",
            background=styles.BG_PANEL,
            foreground=styles.TEXT_SECONDARY,
            font=styles.FONT_BODY_BOLD,
            padding=[10, 6],
            borderwidth=0,
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", styles.BG_CARD)],
            foreground=[("selected", styles.ACCENT_CYAN)],
        )

    def _build_header(self) -> None:
        """Build top header banner with project identity and live telemetry badges."""
        header_frame = tk.Frame(self.root, bg=styles.BG_PANEL, height=75, padx=20, pady=8)
        header_frame.pack(side=tk.TOP, fill=tk.X)

        # Title & Subtitle container
        title_box = tk.Frame(header_frame, bg=styles.BG_PANEL)
        title_box.pack(side=tk.LEFT, fill=tk.Y)

        title_lbl = tk.Label(
            title_box,
            text="✨ Gesture-Based Presentation Control",
            font=styles.FONT_TITLE,
            fg=styles.ACCENT_CYAN,
            bg=styles.BG_PANEL,
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            title_box,
            text="NUV CGIP End Sem Project | Dhruv Pankhania • Krish Jadav • Dhairya Patel",
            font=styles.FONT_SMALL,
            fg=styles.TEXT_SECONDARY,
            bg=styles.BG_PANEL,
        )
        subtitle_lbl.pack(anchor="w")

        # Telemetry & Status Badges
        badge_box = tk.Frame(header_frame, bg=styles.BG_PANEL)
        badge_box.pack(side=tk.RIGHT, fill=tk.Y)

        # Active Gesture badge
        self.gesture_badge = tk.Label(
            badge_box,
            text="🎯 GESTURE: NONE",
            font=styles.FONT_BADGE,
            fg=styles.ACCENT_YELLOW,
            bg=styles.BG_CARD,
            padx=10,
            pady=4,
            relief=tk.FLAT,
        )
        self.gesture_badge.pack(side=tk.LEFT, padx=4)

        # Controller Mode badge (Live OS vs Sim)
        self.mode_badge = tk.Label(
            badge_box,
            text="💻 LIVE OS",
            font=styles.FONT_SUBTITLE,
            fg=styles.ACCENT_GREEN,
            bg=styles.BG_CARD,
            padx=9,
            pady=4,
            relief=tk.FLAT,
        )
        self.mode_badge.pack(side=tk.LEFT, padx=4)

        # Latency badge (Week 9)
        self.latency_badge = tk.Label(
            badge_box,
            text="⚡ 0.0 ms",
            font=styles.FONT_FPS,
            fg=styles.ACCENT_CYAN,
            bg=styles.BG_CARD,
            padx=9,
            pady=4,
            relief=tk.FLAT,
        )
        self.latency_badge.pack(side=tk.LEFT, padx=4)

        # FPS badge
        self.fps_badge = tk.Label(
            badge_box,
            text="FPS: 0.0",
            font=styles.FONT_FPS,
            fg=styles.ACCENT_GREEN,
            bg=styles.BG_CARD,
            padx=9,
            pady=4,
            relief=tk.FLAT,
        )
        self.fps_badge.pack(side=tk.LEFT, padx=4)

        # Status badge
        self.status_badge = tk.Label(
            badge_box,
            text="● INITIALIZING",
            font=styles.FONT_SUBTITLE,
            fg=styles.ACCENT_YELLOW,
            bg=styles.BG_CARD,
            padx=9,
            pady=4,
            relief=tk.FLAT,
        )
        self.status_badge.pack(side=tk.LEFT, padx=4)

    def _build_main_content(self) -> None:
        """Build central viewport split into video/presentation canvas and controls notebook."""
        main_frame = tk.Frame(self.root, bg=styles.BG_DARK, padx=12, pady=8)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Column: Video & Presentation Viewport Container
        viewport_container = tk.Frame(
            main_frame,
            bg=styles.BG_PANEL,
            highlightbackground=styles.BORDER_COLOR,
            highlightthickness=1,
            padx=10,
            pady=8,
        )
        viewport_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Viewport Header with View Mode Switcher
        viewport_hdr = tk.Frame(viewport_container, bg=styles.BG_PANEL)
        viewport_hdr.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))

        self.viewport_title = tk.Label(
            viewport_hdr,
            text="📹 Live Camera & Gesture Recognition Viewport",
            font=styles.FONT_SECTION,
            fg=styles.TEXT_PRIMARY,
            bg=styles.BG_PANEL,
        )
        self.viewport_title.pack(side=tk.LEFT)

        # View mode toggle button
        self.btn_view_mode = tk.Button(
            viewport_hdr,
            text="🖥️ Switch to Slide Deck View",
            font=styles.FONT_SMALL,
            bg=styles.ACCENT_PURPLE,
            fg=styles.BTN_START_FG,
            relief=tk.FLAT,
            padx=8,
            pady=2,
            command=self._toggle_view_mode,
            cursor="hand2",
        )
        self.btn_view_mode.pack(side=tk.RIGHT, padx=(8, 0))

        self.resolution_lbl = tk.Label(
            viewport_hdr,
            text="1280x720 (HD)",
            font=styles.FONT_SMALL,
            fg=styles.TEXT_MUTED,
            bg=styles.BG_PANEL,
        )
        self.resolution_lbl.pack(side=tk.RIGHT)

        # Canvas for Video & Slide rendering
        self.video_canvas = tk.Canvas(
            viewport_container,
            bg="#0f0f17",
            highlightthickness=0,
        )
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # Right Column: Tabbed Control Deck & Activity Log
        sidebar = tk.Frame(main_frame, bg=styles.BG_DARK, width=440)
        sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        sidebar.pack_propagate(False)

        # Tabbed Notebook for organized, clean UI controls
        self.notebook = ttk.Notebook(sidebar)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Tab 1: Presentation & Gestures (Week 6 & Week 7)
        tab_pres = tk.Frame(self.notebook, bg=styles.BG_PANEL, padx=10, pady=8)
        self.notebook.add(tab_pres, text="🎮 Presentation")
        self._build_presentation_tab(tab_pres)

        # Tab 2: Laser & Annotation Canvas (Week 8)
        tab_laser = tk.Frame(self.notebook, bg=styles.BG_PANEL, padx=10, pady=8)
        self.notebook.add(tab_laser, text="👆 Laser & Draw")
        self._build_laser_annotation_tab(tab_laser)

        # Tab 3: Hardware & Diagnostics (Week 4, 5, 9)
        tab_diag = tk.Frame(self.notebook, bg=styles.BG_PANEL, padx=10, pady=8)
        self.notebook.add(tab_diag, text="⚙️ Hardware & Tests")
        self._build_hardware_diagnostics_tab(tab_diag)

        # Bottom: Activity Log Viewer (Fixed height)
        self._build_logs_card(sidebar)

    def _build_presentation_tab(self, parent: tk.Frame) -> None:
        """Tab 1: Presentation automation, profiles, slide deck controls, and cheat sheet."""
        # Section 1: Presentation Navigation Deck
        deck_box = tk.Frame(parent, bg=styles.BG_CARD, padx=8, pady=6, highlightbackground=styles.BORDER_COLOR, highlightthickness=1)
        deck_box.pack(fill=tk.X, pady=(0, 6))

        tk.Label(deck_box, text="📑 Presentation Navigation Deck", font=styles.FONT_SECTION, fg=styles.ACCENT_CYAN, bg=styles.BG_CARD).pack(anchor="w", pady=(0, 4))

        # Slide counter display
        slide_row = tk.Frame(deck_box, bg=styles.BG_CARD)
        slide_row.pack(fill=tk.X, pady=2)

        self.slide_lbl = tk.Label(
            slide_row,
            text=f"Slide 1 / {self.controller.total_slides}",
            font=styles.FONT_TITLE,
            fg=styles.ACCENT_YELLOW,
            bg=styles.BG_CARD,
        )
        self.slide_lbl.pack(side=tk.LEFT)

        # Quick Slide Action Buttons
        btn_box = tk.Frame(slide_row, bg=styles.BG_CARD)
        btn_box.pack(side=tk.RIGHT)

        btn_prev = tk.Button(btn_box, text="◀ Prev", font=styles.FONT_SMALL, bg=styles.BTN_SECONDARY_BG, fg=styles.TEXT_PRIMARY, relief=tk.FLAT, padx=6, pady=2, command=self._on_prev_slide, cursor="hand2")
        btn_prev.pack(side=tk.LEFT, padx=2)

        btn_next = tk.Button(btn_box, text="Next ▶", font=styles.FONT_SMALL, bg=styles.BTN_ACTION_BG, fg=styles.BTN_ACTION_FG, relief=tk.FLAT, padx=6, pady=2, command=self._on_next_slide, cursor="hand2")
        btn_next.pack(side=tk.LEFT, padx=2)

        # Section 2: Automation Controls & Target Profile
        cfg_box = tk.Frame(parent, bg=styles.BG_CARD, padx=8, pady=6, highlightbackground=styles.BORDER_COLOR, highlightthickness=1)
        cfg_box.pack(fill=tk.X, pady=(0, 6))

        tk.Label(cfg_box, text="⚡ PyAutoGUI OS Automation (Week 7)", font=styles.FONT_SECTION, fg=styles.ACCENT_GREEN, bg=styles.BG_CARD).pack(anchor="w", pady=(0, 4))

        # Profile selection
        row_prof = tk.Frame(cfg_box, bg=styles.BG_CARD)
        row_prof.pack(fill=tk.X, pady=2)
        tk.Label(row_prof, text="Target Software:", font=styles.FONT_BODY_BOLD, fg=styles.TEXT_SECONDARY, bg=styles.BG_CARD).pack(side=tk.LEFT)

        self.profile_var = tk.StringVar(value="PowerPoint")
        self.profile_combo = ttk.Combobox(
            row_prof,
            textvariable=self.profile_var,
            values=["PowerPoint", "Google Slides", "PDF Viewer", "Media Player", "General"],
            state="readonly",
            width=14,
        )
        self.profile_combo.pack(side=tk.RIGHT)
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_changed)

        # Mode & Cooldown Row
        row_mode = tk.Frame(cfg_box, bg=styles.BG_CARD)
        row_mode.pack(fill=tk.X, pady=3)

        self.btn_mode = tk.Button(
            row_mode,
            text="💻 Mode: Live OS (Keys ON)",
            font=styles.FONT_SMALL,
            bg=styles.ACCENT_GREEN,
            fg=styles.BTN_START_FG,
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=self._toggle_automation_mode,
            cursor="hand2",
        )
        self.btn_mode.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.cooldown_var = tk.StringVar(value="1.0s (Standard)")
        self.cooldown_combo = ttk.Combobox(
            row_mode,
            textvariable=self.cooldown_var,
            values=["0.5s (Fast)", "1.0s (Standard)", "1.5s (Deliberate)", "2.0s (Safe)"],
            state="readonly",
            width=14,
        )
        self.cooldown_combo.pack(side=tk.RIGHT, padx=(2, 0))
        self.cooldown_combo.bind("<<ComboboxSelected>>", self._on_cooldown_changed)

        # Section 3: Gesture Cheat Sheet reference
        guide_box = tk.Frame(parent, bg=styles.BG_CARD, padx=8, pady=6, highlightbackground=styles.BORDER_COLOR, highlightthickness=1)
        guide_box.pack(fill=tk.BOTH, expand=True)

        tk.Label(guide_box, text="💡 Supported Gesture Actions", font=styles.FONT_SECTION, fg=styles.ACCENT_YELLOW, bg=styles.BG_CARD).pack(anchor="w", pady=(0, 3))

        gestures = [
            ("👉 Point Right", "Next Slide (Right Arrow)"),
            ("👈 Point Left", "Previous Slide (Left Arrow)"),
            ("👆 Laser Pointer", "Screen Laser Tracking"),
            ("🤏 Pinch / Pen", "Draw Slide Annotation"),
            ("✋ Open Palm", "Attention / Free State"),
            ("✊ Fist", "Pause / Lock Navigation"),
            ("👌 OK Sign", "Fullscreen Toggle (F5 / F)"),
            ("👍 / 👎 Thumbs", "Volume Up / Down"),
        ]

        for gesture, action in gestures:
            r = tk.Frame(guide_box, bg=styles.BG_CARD)
            r.pack(fill=tk.X, pady=1)
            tk.Label(r, text=gesture, font=styles.FONT_BODY_BOLD, fg=styles.ACCENT_YELLOW, bg=styles.BG_CARD).pack(side=tk.LEFT)
            tk.Label(r, text=f": {action}", font=styles.FONT_SMALL, fg=styles.TEXT_SECONDARY, bg=styles.BG_CARD).pack(side=tk.LEFT)

    def _build_laser_annotation_tab(self, parent: tk.Frame) -> None:
        """Tab 2: Virtual Laser Pointer and Slide Annotation controls (Week 8)."""
        # Section 1: Virtual Laser Pointer
        laser_box = tk.Frame(parent, bg=styles.BG_CARD, padx=8, pady=6, highlightbackground=styles.BORDER_COLOR, highlightthickness=1)
        laser_box.pack(fill=tk.X, pady=(0, 6))

        tk.Label(laser_box, text="👆 Virtual Laser Pointer (Week 8)", font=styles.FONT_SECTION, fg=styles.ACCENT_RED, bg=styles.BG_CARD).pack(anchor="w", pady=(0, 4))

        row_l_btns = tk.Frame(laser_box, bg=styles.BG_CARD)
        row_l_btns.pack(fill=tk.X, pady=2)

        self.btn_toggle_laser = tk.Button(
            row_l_btns,
            text="👆 Laser Pointer: ON",
            font=styles.FONT_SMALL,
            bg=styles.ACCENT_RED,
            fg=styles.BTN_START_FG,
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=self._toggle_laser_pointer,
            cursor="hand2",
        )
        self.btn_toggle_laser.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_toggle_mouse = tk.Button(
            row_l_btns,
            text="🖱️ OS Mouse: OFF",
            font=styles.FONT_SMALL,
            bg=styles.BTN_SECONDARY_BG,
            fg=styles.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=self._toggle_os_mouse,
            cursor="hand2",
        )
        self.btn_toggle_mouse.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # Laser color palette
        col_row = tk.Frame(laser_box, bg=styles.BG_CARD)
        col_row.pack(fill=tk.X, pady=3)
        tk.Label(col_row, text="Laser Glow Color:", font=styles.FONT_BODY_BOLD, fg=styles.TEXT_SECONDARY, bg=styles.BG_CARD).pack(side=tk.LEFT)

        for col_name in ["Red", "Green", "Cyan", "Gold"]:
            b = tk.Button(
                col_row,
                text=col_name,
                font=styles.FONT_SMALL,
                bg=styles.BTN_SECONDARY_BG,
                fg=styles.TEXT_PRIMARY,
                relief=tk.FLAT,
                padx=5,
                pady=1,
                command=lambda c=col_name: self._set_laser_color(c),
                cursor="hand2",
            )
            b.pack(side=tk.LEFT, padx=2)

        # Section 2: Slide Annotation & Freehand Drawing
        draw_box = tk.Frame(parent, bg=styles.BG_CARD, padx=8, pady=6, highlightbackground=styles.BORDER_COLOR, highlightthickness=1)
        draw_box.pack(fill=tk.X, pady=(0, 6))

        tk.Label(draw_box, text="🤏 Slide Drawing Canvas (Week 8)", font=styles.FONT_SECTION, fg=styles.ACCENT_PURPLE, bg=styles.BG_CARD).pack(anchor="w", pady=(0, 4))

        row_d_btns = tk.Frame(draw_box, bg=styles.BG_CARD)
        row_d_btns.pack(fill=tk.X, pady=2)

        self.btn_toggle_annot = tk.Button(
            row_d_btns,
            text="✏️ Drawing Canvas: ON",
            font=styles.FONT_SMALL,
            bg=styles.ACCENT_PURPLE,
            fg=styles.BTN_START_FG,
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=self._toggle_annotation,
            cursor="hand2",
        )
        self.btn_toggle_annot.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        btn_undo = tk.Button(
            row_d_btns,
            text="↩ Undo Stroke",
            font=styles.FONT_SMALL,
            bg=styles.BTN_SECONDARY_BG,
            fg=styles.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=self._undo_annotation,
            cursor="hand2",
        )
        btn_undo.pack(side=tk.LEFT, padx=2)

        btn_clear = tk.Button(
            row_d_btns,
            text="🗑️ Clear All",
            font=styles.FONT_SMALL,
            bg=styles.BTN_STOP_BG,
            fg=styles.BTN_STOP_FG,
            relief=tk.FLAT,
            padx=6,
            pady=2,
            command=self._clear_annotation,
            cursor="hand2",
        )
        btn_clear.pack(side=tk.RIGHT, padx=(2, 0))

        # Pen Color buttons
        pen_col_row = tk.Frame(draw_box, bg=styles.BG_CARD)
        pen_col_row.pack(fill=tk.X, pady=3)
        tk.Label(pen_col_row, text="Pen Color:", font=styles.FONT_BODY_BOLD, fg=styles.TEXT_SECONDARY, bg=styles.BG_CARD).pack(side=tk.LEFT)

        for col_name in ["Red", "Cyan", "Green", "Yellow", "Purple", "Eraser"]:
            b = tk.Button(
                pen_col_row,
                text=col_name,
                font=styles.FONT_SMALL,
                bg=styles.BTN_SECONDARY_BG,
                fg=styles.TEXT_PRIMARY,
                relief=tk.FLAT,
                padx=4,
                pady=1,
                command=lambda c=col_name: self._set_pen_color(c),
                cursor="hand2",
            )
            b.pack(side=tk.LEFT, padx=1)

        # Pen thickness dropdown
        thick_row = tk.Frame(draw_box, bg=styles.BG_CARD)
        thick_row.pack(fill=tk.X, pady=2)
        tk.Label(thick_row, text="Brush Size:", font=styles.FONT_BODY_BOLD, fg=styles.TEXT_SECONDARY, bg=styles.BG_CARD).pack(side=tk.LEFT)

        self.thick_var = tk.StringVar(value="Medium (4px)")
        self.thick_combo = ttk.Combobox(
            thick_row,
            textvariable=self.thick_var,
            values=["Fine (2px)", "Medium (4px)", "Thick (8px)", "Bold (12px)"],
            state="readonly",
            width=14,
        )
        self.thick_combo.pack(side=tk.RIGHT)
        self.thick_combo.bind("<<ComboboxSelected>>", self._on_thickness_changed)

    def _build_hardware_diagnostics_tab(self, parent: tk.Frame) -> None:
        """Tab 3: Hardware camera controls, MediaPipe settings, and benchmark test suite (Week 9)."""
        # Section 1: Camera Hardware Controls
        cam_box = tk.Frame(parent, bg=styles.BG_CARD, padx=8, pady=6, highlightbackground=styles.BORDER_COLOR, highlightthickness=1)
        cam_box.pack(fill=tk.X, pady=(0, 6))

        tk.Label(cam_box, text="⚙️ Camera Hardware (Week 4)", font=styles.FONT_SECTION, fg=styles.ACCENT_BLUE, bg=styles.BG_CARD).pack(anchor="w", pady=(0, 4))

        # Device & Resolution Rows
        row1 = tk.Frame(cam_box, bg=styles.BG_CARD)
        row1.pack(fill=tk.X, pady=1)
        tk.Label(row1, text="Device:", font=styles.FONT_BODY_BOLD, fg=styles.TEXT_SECONDARY, bg=styles.BG_CARD).pack(side=tk.LEFT)

        available_devs = self.camera.detect_available_cameras()
        self.device_var = tk.StringVar(value=f"Camera {self.camera.device_index}")
        self.device_combo = ttk.Combobox(
            row1,
            textvariable=self.device_var,
            values=[f"Camera {i}" for i in available_devs],
            state="readonly",
            width=14,
        )
        self.device_combo.pack(side=tk.RIGHT)
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_changed)

        row2 = tk.Frame(cam_box, bg=styles.BG_CARD)
        row2.pack(fill=tk.X, pady=1)
        tk.Label(row2, text="Resolution:", font=styles.FONT_BODY_BOLD, fg=styles.TEXT_SECONDARY, bg=styles.BG_CARD).pack(side=tk.LEFT)

        self.res_var = tk.StringVar(value="1280x720 (HD)")
        self.res_combo = ttk.Combobox(
            row2,
            textvariable=self.res_var,
            values=list(self.camera.RESOLUTIONS.keys()),
            state="readonly",
            width=14,
        )
        self.res_combo.pack(side=tk.RIGHT)
        self.res_combo.bind("<<ComboboxSelected>>", self._on_resolution_changed)

        # Camera action buttons
        btn_grid = tk.Frame(cam_box, bg=styles.BG_CARD)
        btn_grid.pack(fill=tk.X, pady=(4, 0))

        self.btn_toggle_camera = tk.Button(
            btn_grid,
            text="⏹ Stop Camera",
            font=styles.FONT_BODY_BOLD,
            bg=styles.BTN_STOP_BG,
            fg=styles.BTN_STOP_FG,
            relief=tk.FLAT,
            padx=8,
            pady=3,
            command=self._toggle_camera_stream,
            cursor="hand2",
        )
        self.btn_toggle_camera.pack(fill=tk.X, pady=1)

        btn_sub = tk.Frame(btn_grid, bg=styles.BG_CARD)
        btn_sub.pack(fill=tk.X, pady=1)

        self.btn_mirror = tk.Button(btn_sub, text="🪞 Mirror: ON", font=styles.FONT_SMALL, bg=styles.BTN_SECONDARY_BG, fg=styles.TEXT_PRIMARY, relief=tk.FLAT, padx=4, pady=2, command=self._toggle_mirror, cursor="hand2")
        self.btn_mirror.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_pause = tk.Button(btn_sub, text="⏸ Pause", font=styles.FONT_SMALL, bg=styles.BTN_SECONDARY_BG, fg=styles.TEXT_PRIMARY, relief=tk.FLAT, padx=4, pady=2, command=self._toggle_pause, cursor="hand2")
        self.btn_pause.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.btn_snapshot = tk.Button(btn_sub, text="📸 Snapshot", font=styles.FONT_SMALL, bg=styles.BTN_ACTION_BG, fg=styles.BTN_ACTION_FG, relief=tk.FLAT, padx=4, pady=2, command=self._take_snapshot, cursor="hand2")
        self.btn_snapshot.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # Section 2: MediaPipe Skeleton & Gesture Engine Overlays
        mp_box = tk.Frame(parent, bg=styles.BG_CARD, padx=8, pady=6, highlightbackground=styles.BORDER_COLOR, highlightthickness=1)
        mp_box.pack(fill=tk.X, pady=(0, 6))

        tk.Label(mp_box, text="🖐️ MediaPipe & Vision HUD (Week 5 & 6)", font=styles.FONT_SECTION, fg=styles.ACCENT_CYAN, bg=styles.BG_CARD).pack(anchor="w", pady=(0, 4))

        mp_btn_row = tk.Frame(mp_box, bg=styles.BG_CARD)
        mp_btn_row.pack(fill=tk.X, pady=2)

        self.btn_toggle_skeleton = tk.Button(mp_btn_row, text="🦴 Skeleton: ON", font=styles.FONT_SMALL, bg=styles.ACCENT_CYAN, fg=styles.BTN_START_FG, relief=tk.FLAT, padx=6, pady=2, command=self._toggle_skeleton, cursor="hand2")
        self.btn_toggle_skeleton.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_toggle_bbox = tk.Button(mp_btn_row, text="📦 Box: ON", font=styles.FONT_SMALL, bg=styles.ACCENT_BLUE, fg=styles.BTN_START_FG, relief=tk.FLAT, padx=6, pady=2, command=self._toggle_bounding_box, cursor="hand2")
        self.btn_toggle_bbox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.btn_toggle_hud = tk.Button(mp_btn_row, text="🏷️ HUD: ON", font=styles.FONT_SMALL, bg=styles.ACCENT_PINK, fg=styles.BTN_START_FG, relief=tk.FLAT, padx=6, pady=2, command=self._toggle_gesture_hud, cursor="hand2")
        self.btn_toggle_hud.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

        # Section 3: Performance Benchmarking Suite (Week 9)
        bench_box = tk.Frame(parent, bg=styles.BG_CARD, padx=8, pady=6, highlightbackground=styles.BORDER_COLOR, highlightthickness=1)
        bench_box.pack(fill=tk.X)

        tk.Label(bench_box, text="📊 System Benchmarking & Latency (Week 9)", font=styles.FONT_SECTION, fg=styles.ACCENT_ORANGE, bg=styles.BG_CARD).pack(anchor="w", pady=(0, 4))

        self.btn_run_bench = tk.Button(
            bench_box,
            text="🚀 Run Performance Benchmark (30 Frames)",
            font=styles.FONT_BODY_BOLD,
            bg=styles.ACCENT_ORANGE,
            fg=styles.BTN_START_FG,
            relief=tk.FLAT,
            padx=8,
            pady=4,
            command=self._run_benchmark_async,
            cursor="hand2",
        )
        self.btn_run_bench.pack(fill=tk.X, pady=2)

    def _build_logs_card(self, parent: tk.Frame) -> None:
        """Real-time scrolling system activity log viewer."""
        card = tk.Frame(
            parent,
            bg=styles.BG_PANEL,
            highlightbackground=styles.BORDER_COLOR,
            highlightthickness=1,
            padx=10,
            pady=6,
            height=180,
        )
        card.pack(fill=tk.X, side=tk.BOTTOM)
        card.pack_propagate(False)

        lbl = tk.Label(
            card,
            text="📋 System Activity & Dispatch Log",
            font=styles.FONT_SECTION,
            fg=styles.TEXT_PRIMARY,
            bg=styles.BG_PANEL,
        )
        lbl.pack(anchor="w", pady=(0, 2))

        self.log_text = tk.Text(
            card,
            bg=styles.BG_INPUT,
            fg=styles.TEXT_PRIMARY,
            insertbackground=styles.ACCENT_CYAN,
            font=styles.FONT_MONO,
            relief=tk.FLAT,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)

    def _build_footer(self) -> None:
        """Bottom status bar with system information and shortcuts."""
        footer_frame = tk.Frame(self.root, bg=styles.BG_PANEL, height=26, padx=15, pady=2)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = tk.Label(
            footer_frame,
            text="Ready. Space: Camera | G: Gesture | L: Laser | C: Clear Draw | O: OS Mode | V: Slides View",
            font=styles.FONT_SMALL,
            fg=styles.TEXT_MUTED,
            bg=styles.BG_PANEL,
        )
        self.status_label.pack(side=tk.LEFT)

        version_lbl = tk.Label(
            footer_frame,
            text="Milestone: Final Week 10 (End Sem Project Complete)",
            font=styles.FONT_SMALL,
            fg=styles.TEXT_MUTED,
            bg=styles.BG_PANEL,
        )
        version_lbl.pack(side=tk.RIGHT)

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts for quick presentation control."""
        self.root.bind("<space>", lambda e: self._toggle_camera_stream())
        self.root.bind("<g>", lambda e: self._toggle_gesture_recognition())
        self.root.bind("<G>", lambda e: self._toggle_gesture_recognition())
        self.root.bind("<d>", lambda e: self._toggle_gesture_hud())
        self.root.bind("<D>", lambda e: self._toggle_gesture_hud())
        self.root.bind("<m>", lambda e: self._toggle_mirror())
        self.root.bind("<M>", lambda e: self._toggle_mirror())
        self.root.bind("<s>", lambda e: self._take_snapshot())
        self.root.bind("<S>", lambda e: self._take_snapshot())
        self.root.bind("<p>", lambda e: self._toggle_pause())
        self.root.bind("<P>", lambda e: self._toggle_pause())
        self.root.bind("<h>", lambda e: self._toggle_skeleton())
        self.root.bind("<H>", lambda e: self._toggle_skeleton())
        self.root.bind("<b>", lambda e: self._toggle_bounding_box())
        self.root.bind("<B>", lambda e: self._toggle_bounding_box())
        self.root.bind("<l>", lambda e: self._toggle_laser_pointer())
        self.root.bind("<L>", lambda e: self._toggle_laser_pointer())
        self.root.bind("<c>", lambda e: self._clear_annotation())
        self.root.bind("<C>", lambda e: self._clear_annotation())
        self.root.bind("<u>", lambda e: self._undo_annotation())
        self.root.bind("<U>", lambda e: self._undo_annotation())
        self.root.bind("<o>", lambda e: self._toggle_automation_mode())
        self.root.bind("<O>", lambda e: self._toggle_automation_mode())
        self.root.bind("<v>", lambda e: self._toggle_view_mode())
        self.root.bind("<V>", lambda e: self._toggle_view_mode())
        self.root.bind("<Left>", lambda e: self._on_prev_slide())
        self.root.bind("<Right>", lambda e: self._on_next_slide())

    def log_message(self, message: str) -> None:
        """Append a timestamped log line to the activity log."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # ==================== Handlers & Callbacks ====================

    def _on_presentation_action_triggered(self, action: str, gesture_state: GestureState) -> None:
        """Callback invoked when PresentationController triggers an action."""
        self.slide_lbl.configure(text=f"Slide {self.controller.current_slide} / {self.controller.total_slides}")
        self.log_message(f"⚡ ACTION DISPATCHED: {action} via {gesture_state.emoji} {gesture_state.label} (Slide {self.controller.current_slide})")
        self.status_label.configure(text=f"Action Triggered: {action} ({gesture_state.label})")

    def _on_next_slide(self) -> None:
        """Manual next slide action."""
        self.controller.next_slide()
        self.slide_lbl.configure(text=f"Slide {self.controller.current_slide} / {self.controller.total_slides}")
        self.log_message(f"Manual Slide Navigation: Next -> Slide {self.controller.current_slide}")

    def _on_prev_slide(self) -> None:
        """Manual previous slide action."""
        self.controller.prev_slide()
        self.slide_lbl.configure(text=f"Slide {self.controller.current_slide} / {self.controller.total_slides}")
        self.log_message(f"Manual Slide Navigation: Prev -> Slide {self.controller.current_slide}")

    def _toggle_automation_mode(self) -> None:
        """Toggle between Live OS keystrokes and Simulation mode."""
        mode = self.controller.toggle_mode()
        if mode == ControllerMode.LIVE_OS:
            self.btn_mode.configure(text="💻 Mode: Live OS (Keys ON)", bg=styles.ACCENT_GREEN, fg=styles.BTN_START_FG)
            self.mode_badge.configure(text="💻 LIVE OS", fg=styles.ACCENT_GREEN)
            self.log_message("Switched to LIVE OS Mode: Gestures will dispatch actual OS keystrokes to active presentation.")
        else:
            self.btn_mode.configure(text="🧪 Mode: Simulation (Keys OFF)", bg=styles.ACCENT_YELLOW, fg=styles.BTN_START_FG)
            self.mode_badge.configure(text="🧪 SIMULATION", fg=styles.ACCENT_YELLOW)
            self.log_message("Switched to SIMULATION Mode: Gestures are tested safely within the application.")

    def _on_profile_changed(self, event=None) -> None:
        """Handle target software profile switch."""
        name = self.profile_var.get()
        mapping = {
            "PowerPoint": TargetProfile.POWERPOINT,
            "Google Slides": TargetProfile.GOOGLE_SLIDES,
            "PDF Viewer": TargetProfile.PDF_VIEWER,
            "Media Player": TargetProfile.MEDIA_PLAYER,
            "General": TargetProfile.GENERAL,
        }
        if name in mapping:
            self.controller.set_profile(mapping[name])
            self.log_message(f"Active presentation profile set to {name}.")

    def _toggle_view_mode(self) -> None:
        """Toggle between live camera viewport and slide deck preview mode."""
        if self.view_mode == "CAMERA":
            self.view_mode = "SLIDES"
            self.btn_view_mode.configure(text="📹 Switch to Camera View", bg=styles.ACCENT_CYAN)
            self.viewport_title.configure(text="🖥️ Slide Deck Presentation View (with PiP Camera)")
            self.log_message("Viewport switched to Slide Deck Presentation View.")
        else:
            self.view_mode = "CAMERA"
            self.btn_view_mode.configure(text="🖥️ Switch to Slide Deck View", bg=styles.ACCENT_PURPLE)
            self.viewport_title.configure(text="📹 Live Camera & Gesture Recognition Viewport")
            self.log_message("Viewport switched to Live Camera View.")

    def _toggle_laser_pointer(self) -> None:
        """Toggle virtual laser pointer on/off."""
        enabled = self.laser_pointer.toggle()
        state = "ON" if enabled else "OFF"
        bg_col = styles.ACCENT_RED if enabled else styles.BTN_SECONDARY_BG
        fg_col = styles.BTN_START_FG if enabled else styles.TEXT_PRIMARY
        self.btn_toggle_laser.configure(text=f"👆 Laser Pointer: {state}", bg=bg_col, fg=fg_col)
        self.log_message(f"Virtual laser pointer turned {state}.")

    def _toggle_os_mouse(self) -> None:
        """Toggle PyAutoGUI OS mouse cursor movement."""
        self.laser_pointer.move_os_cursor = not self.laser_pointer.move_os_cursor
        state = "ON" if self.laser_pointer.move_os_cursor else "OFF"
        bg_col = styles.ACCENT_GREEN if self.laser_pointer.move_os_cursor else styles.BTN_SECONDARY_BG
        fg_col = styles.BTN_START_FG if self.laser_pointer.move_os_cursor else styles.TEXT_PRIMARY
        self.btn_toggle_mouse.configure(text=f"🖱️ OS Mouse: {state}", bg=bg_col, fg=fg_col)
        self.log_message(f"OS Mouse cursor automation turned {state}.")

    def _set_laser_color(self, color_name: str) -> None:
        """Set laser pointer glow color preset."""
        self.laser_pointer.set_color(color_name)
        self.log_message(f"Laser pointer color set to {color_name}.")

    def _toggle_annotation(self) -> None:
        """Toggle slide drawing canvas on/off."""
        enabled = self.annotator.toggle()
        state = "ON" if enabled else "OFF"
        bg_col = styles.ACCENT_PURPLE if enabled else styles.BTN_SECONDARY_BG
        fg_col = styles.BTN_START_FG if enabled else styles.TEXT_PRIMARY
        self.btn_toggle_annot.configure(text=f"✏️ Drawing Canvas: {state}", bg=bg_col, fg=fg_col)
        self.log_message(f"Drawing canvas turned {state}.")

    def _undo_annotation(self) -> None:
        """Undo last drawing stroke."""
        if self.annotator.undo():
            self.log_message(f"Annotation stroke undone. Remaining strokes: {self.annotator.stroke_count}")

    def _clear_annotation(self) -> None:
        """Clear all annotation strokes."""
        self.annotator.clear()
        self.log_message("All canvas drawing annotations cleared.")

    def _set_pen_color(self, color_name: str) -> None:
        """Select annotation brush color."""
        self.annotator.set_color(color_name)
        self.log_message(f"Drawing brush set to {color_name}.")

    def _on_thickness_changed(self, event=None) -> None:
        """Update annotation stroke width."""
        val = self.thick_var.get()
        sizes = {"Fine (2px)": 2, "Medium (4px)": 4, "Thick (8px)": 8, "Bold (12px)": 12}
        if val in sizes:
            self.annotator.set_thickness(sizes[val])
            self.log_message(f"Drawing brush thickness set to {sizes[val]}px.")

    def _on_cooldown_changed(self, event=None) -> None:
        """Update action cooldown threshold."""
        selected = self.cooldown_var.get()
        try:
            sec = float(selected.split("s")[0])
            self.controller.set_cooldown(sec)
            self.log_message(f"Action debounce cooldown set to {sec}s.")
        except Exception as err:
            self.log_message(f"Cooldown parse error: {err}")

    def _on_device_changed(self, event=None) -> None:
        """Handle camera device switch."""
        selected_text = self.device_var.get()
        try:
            device_idx = int(selected_text.split()[-1])
            self.log_message(f"Switching to Camera index {device_idx}...")
            self.camera.set_device(device_idx)
            self.log_message(f"Active camera device set to {device_idx}.")
        except Exception as err:
            self.log_message(f"Error switching camera device: {err}")

    def _on_resolution_changed(self, event=None) -> None:
        """Handle resolution change."""
        selected_res = self.res_var.get()
        if selected_res in self.camera.RESOLUTIONS:
            w, h = self.camera.RESOLUTIONS[selected_res]
            self.camera.set_resolution(w, h)
            self.resolution_lbl.configure(text=selected_res)
            self.log_message(f"Resolution set to {w}x{h}.")

    def _toggle_gesture_recognition(self) -> None:
        """Toggle gesture classification engine on/off."""
        self.enable_gesture_recognition = not self.enable_gesture_recognition
        state = "ON" if self.enable_gesture_recognition else "OFF"
        self.log_message(f"Gesture recognition engine turned {state}.")
        if not self.enable_gesture_recognition:
            self.gesture_badge.configure(text="🎯 GESTURE: OFF", fg=styles.TEXT_MUTED)

    def _toggle_gesture_hud(self) -> None:
        """Toggle visual HUD overlays on/off."""
        self.enable_gesture_hud = not self.enable_gesture_hud
        state = "ON" if self.enable_gesture_hud else "OFF"
        bg_col = styles.ACCENT_PINK if self.enable_gesture_hud else styles.BTN_SECONDARY_BG
        fg_col = styles.BTN_START_FG if self.enable_gesture_hud else styles.TEXT_PRIMARY
        self.btn_toggle_hud.configure(text=f"🏷️ HUD: {state}", bg=bg_col, fg=fg_col)
        self.log_message(f"Gesture HUD overlay turned {state}.")

    def _toggle_skeleton(self) -> None:
        """Toggle landmark skeleton visual overlay."""
        self.enable_hand_tracking = not self.enable_hand_tracking
        state = "ON" if self.enable_hand_tracking else "OFF"
        bg_col = styles.ACCENT_CYAN if self.enable_hand_tracking else styles.BTN_SECONDARY_BG
        fg_col = styles.BTN_START_FG if self.enable_hand_tracking else styles.TEXT_PRIMARY
        self.btn_toggle_skeleton.configure(text=f"🦴 Skeleton: {state}", bg=bg_col, fg=fg_col)
        self.log_message(f"Hand landmark skeleton overlay turned {state}.")

    def _toggle_bounding_box(self) -> None:
        """Toggle bounding box and handedness badge overlay."""
        self.enable_bounding_box = not self.enable_bounding_box
        state = "ON" if self.enable_bounding_box else "OFF"
        bg_col = styles.ACCENT_BLUE if self.enable_bounding_box else styles.BTN_SECONDARY_BG
        fg_col = styles.BTN_START_FG if self.enable_bounding_box else styles.TEXT_PRIMARY
        self.btn_toggle_bbox.configure(text=f"📦 Box: {state}", bg=bg_col, fg=fg_col)
        self.log_message(f"Hand bounding box overlay turned {state}.")

    def _toggle_camera_stream(self) -> None:
        """Start or stop the camera video capture stream."""
        if self.camera.is_running:
            self.camera.stop()
            self.log_message("Camera stream stopped.")
            self.btn_toggle_camera.configure(text="▶ Start Camera", bg=styles.BTN_START_BG, fg=styles.BTN_START_FG)
            self.status_badge.configure(text="● STOPPED", fg=styles.ACCENT_RED)
            self.fps_badge.configure(text="FPS: 0.0")
            self.latency_badge.configure(text="⚡ 0.0 ms")
            self.gesture_badge.configure(text="🎯 GESTURE: STOPPED", fg=styles.TEXT_MUTED)
            self.video_canvas.delete("all")
        else:
            self.camera.start()
            self.log_message("Camera stream started.")
            self.btn_toggle_camera.configure(text="⏹ Stop Camera", bg=styles.BTN_STOP_BG, fg=styles.BTN_STOP_FG)
            self._update_ui_state()

    def _toggle_mirror(self) -> None:
        """Toggle frame horizontal mirroring."""
        self.camera.mirror = not self.camera.mirror
        state_text = "ON" if self.camera.mirror else "OFF"
        self.btn_mirror.configure(text=f"🪞 Mirror: {state_text}")
        self.log_message(f"Mirror mode turned {state_text}.")

    def _toggle_pause(self) -> None:
        """Toggle frame pause state."""
        paused = self.camera.toggle_pause()
        if paused:
            self.btn_pause.configure(text="▶ Resume", bg=styles.ACCENT_YELLOW, fg=styles.BTN_START_FG)
            self.status_badge.configure(text="● PAUSED", fg=styles.ACCENT_YELLOW)
            self.log_message("Stream paused.")
        else:
            self.btn_pause.configure(text="⏸ Pause", bg=styles.BTN_SECONDARY_BG, fg=styles.TEXT_PRIMARY)
            self._update_ui_state()
            self.log_message("Stream resumed.")

    def _take_snapshot(self) -> None:
        """Capture and save snapshot frame to disk."""
        filepath = self.camera.capture_snapshot(output_dir="assets")
        if filepath:
            self.log_message(f"Snapshot saved: {filepath}")
            self.status_label.configure(text=f"Snapshot saved to {filepath}")
        else:
            self.log_message("Failed to capture snapshot (no active frame).")

    def _update_ui_state(self) -> None:
        """Update status badges based on camera state."""
        if self.camera.is_running:
            if self.camera.is_camera_connected:
                self.status_badge.configure(text="● CAMERA LIVE", fg=styles.ACCENT_GREEN)
            else:
                self.status_badge.configure(text="● TEST PATTERN", fg=styles.ACCENT_YELLOW)

    def _run_benchmark_async(self) -> None:
        """Launch system benchmark suite in background thread."""
        if self._benchmarking_active:
            return

        def _bench_worker():
            self._benchmarking_active = True
            self.log_message("--- Starting Automated System Benchmark (30 frames) ---")
            try:
                results = BenchmarkSuite.run_benchmark(iterations=30)
                report_str = BenchmarkSuite.format_report(results)
                for line in report_str.split("\n"):
                    self.log_message(line)
            except Exception as err:
                self.log_message(f"Benchmark error: {err}")
            finally:
                self._benchmarking_active = False

        threading.Thread(target=_bench_worker, daemon=True).start()

    # ==================== Core Processing Loop ====================

    def _refresh_frame_loop(self) -> None:
        """Periodic rendering loop integrating vision pipeline, gestures, laser, annotations, and UI."""
        if self._is_closing:
            return

        if self.camera.is_running:
            self.latency_tracker.start_frame()

            success, raw_frame = self.camera.get_frame()

            if raw_frame is not None:
                fps = self.camera.get_fps()
                self.fps_badge.configure(text=f"FPS: {fps:0.1f}")
                self._update_ui_state()

                cam_frame = raw_frame.copy()
                hand_count = 0

                # 1. Hand Detection
                if self.enable_hand_tracking:
                    cam_frame, detected_hands = self.hand_detector.find_hands(
                        cam_frame,
                        draw=self.enable_hand_tracking,
                        draw_box=self.enable_bounding_box,
                    )
                    hand_count = len(detected_hands)
                    self.latency_tracker.mark_stage("detection")

                    if hand_count > 0:
                        primary_hand = detected_hands[0]
                        landmarks = primary_hand.get("landmarks", [])

                        # Gesture Recognition Engine (Week 6)
                        if self.enable_gesture_recognition:
                            gesture_state = self.gesture_recognizer.recognize(
                                primary_hand, use_smoothing=True
                            )
                            self.latency_tracker.mark_stage("gesture")

                            # Visual HUD Overlay
                            if self.enable_gesture_hud:
                                cam_frame = self.gesture_recognizer.draw_gesture_hud(
                                    cam_frame,
                                    gesture_state,
                                    landmarks=landmarks,
                                )

                            # Track Laser Pointer if in Pointer Mode
                            if gesture_state.gesture in (
                                GestureType.INDEX_POINTER,
                                GestureType.POINT_RIGHT,
                                GestureType.POINT_LEFT,
                            ):
                                if gesture_state.pointer_pos is not None:
                                    px, py = gesture_state.pointer_pos
                                    h, w, _ = cam_frame.shape
                                    self.laser_pointer.update_position(px, py, w, h)
                            else:
                                if gesture_state.gesture not in (GestureType.INDEX_POINTER,):
                                    self.laser_pointer.reset()

                            # Track Annotation Drawing if in Pinch Mode
                            if gesture_state.gesture in (GestureType.PINCH, GestureType.OK_SIGN):
                                if len(landmarks) >= 21:
                                    t_pt = landmarks[self.gesture_recognizer.THUMB_TIP]
                                    i_pt = landmarks[self.gesture_recognizer.INDEX_TIP]
                                    mid_x = (t_pt[0] + i_pt[0]) // 2
                                    mid_y = (t_pt[1] + i_pt[1]) // 2
                                    self.annotator.continue_drawing(mid_x, mid_y)
                            else:
                                self.annotator.stop_drawing()

                            # Evaluate Presentation Controller Action
                            self.controller.handle_gesture(gesture_state)

                            # Update Gesture Badge in Header
                            if gesture_state.gesture != GestureType.NONE:
                                g_conf = int(gesture_state.confidence * 100)
                                self.gesture_badge.configure(
                                    text=f"{gesture_state.emoji} {gesture_state.label.upper()} ({g_conf}%)",
                                    fg=styles.ACCENT_ORANGE if gesture_state.gesture != GestureType.OPEN_PALM else styles.ACCENT_GREEN,
                                )
                            else:
                                self.gesture_badge.configure(
                                    text="🎯 GESTURE: NONE",
                                    fg=styles.TEXT_MUTED,
                                )

                            # Log Gesture Transition
                            if gesture_state.gesture != self._last_recognized_gesture:
                                if gesture_state.gesture != GestureType.NONE:
                                    self.log_message(
                                        f"Gesture recognized: {gesture_state.emoji} {gesture_state.label} -> {gesture_state.action}"
                                    )
                                self._last_recognized_gesture = gesture_state.gesture

                    else:
                        self.gesture_recognizer.reset()
                        self.laser_pointer.reset()
                        self.annotator.stop_drawing()
                        self._last_recognized_gesture = GestureType.NONE
                        if self.enable_gesture_recognition:
                            self.gesture_badge.configure(text="🎯 GESTURE: NONE", fg=styles.TEXT_MUTED)

                    # Log Detection acquisition/loss
                    if hand_count != self._last_hand_count:
                        if hand_count > 0:
                            self.log_message(f"Tracking acquired: Hand detected ({hand_count}).")
                        else:
                            self.log_message("Tracking lost: Hand exited frame.")
                        self._last_hand_count = hand_count

                # 2. View Mode Rendering (Camera View vs Slide Deck View)
                h, w, _ = cam_frame.shape

                if self.view_mode == "SLIDES":
                    # Render slide canvas
                    display_frame = SlideDeck.render_slide(
                        self.controller.current_slide,
                        width=w,
                        height=h,
                    )
                    # Render annotations and laser pointer on slide
                    if self.enable_annotation:
                        display_frame = self.annotator.render(display_frame)
                    if self.enable_laser_pointer:
                        display_frame = self.laser_pointer.render_overlay(display_frame)

                    # Picture-in-Picture (PiP) Camera Feed in bottom right corner
                    if self.show_camera_pip:
                        pip_w, pip_h = 240, 135
                        pip_x = w - pip_w - 20
                        pip_y = h - pip_h - 20
                        small_cam = cv2.resize(cam_frame, (pip_w, pip_h), interpolation=cv2.INTER_AREA)

                        # Draw subtle neon border around PiP box
                        cv2.rectangle(display_frame, (pip_x - 2, pip_y - 2), (pip_x + pip_w + 2, pip_y + pip_h + 2), (200, 140, 245), 2)
                        display_frame[pip_y:pip_y + pip_h, pip_x:pip_x + pip_w] = small_cam
                else:
                    # Camera view: render annotations and laser pointer directly onto camera frame
                    display_frame = cam_frame
                    if self.enable_annotation:
                        display_frame = self.annotator.render(display_frame)
                    if self.enable_laser_pointer:
                        display_frame = self.laser_pointer.render_overlay(display_frame)

                self.latency_tracker.mark_stage("render")
                total_latency_ms = self.latency_tracker.end_frame()

                # Update live latency badge
                self.latency_badge.configure(text=f"⚡ {total_latency_ms:0.1f} ms")

                # 3. Canvas Geometry & Drawing
                canvas_width = max(self.video_canvas.winfo_width(), 100)
                canvas_height = max(self.video_canvas.winfo_height(), 100)

                rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                dh, dw, _ = rgb_frame.shape

                scale = min(canvas_width / dw, canvas_height / dh)
                nw, nh = max(int(dw * scale), 1), max(int(dh * scale), 1)

                resized_frame = cv2.resize(rgb_frame, (nw, nh), interpolation=cv2.INTER_AREA)

                img = Image.fromarray(resized_frame)
                self._current_photo_image = ImageTk.PhotoImage(image=img)

                self.video_canvas.delete("all")
                cx = canvas_width // 2
                cy = canvas_height // 2
                self.video_canvas.create_image(cx, cy, anchor=tk.CENTER, image=self._current_photo_image)

        # Re-schedule frame loop (~30ms = ~33 FPS)
        self.root.after(30, self._refresh_frame_loop)

    def on_close(self) -> None:
        """Gracefully terminate background threads, engines, and close window."""
        self._is_closing = True
        try:
            self.camera.stop()
        except Exception:
            pass
        try:
            self.hand_detector.close()
        except Exception:
            pass
        self.root.destroy()
