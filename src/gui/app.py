"""
Main Tkinter Graphical User Interface for Gesture-Based Presentation Control.
Integrates OpenCV camera feed with real-time MediaPipe 21-hand-landmark detection.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import time
import os
from typing import Optional, List, Dict, Any

from src.gui import styles
from src.processing.camera import CameraManager
from src.processing.hand_detector import HandDetector


class PresentationControllerApp:
    """
    Tkinter Application embedding OpenCV webcam stream with MediaPipe Hand Detection,
    21 3D landmarks skeleton overlay, real-time telemetry, and modern dark theme UI.
    """

    def __init__(self, root: tk.Tk, camera_index: int = 0):
        self.root = root
        self.root.title("Gesture-Based Presentation Controller")
        self.root.geometry("1240x800")
        self.root.minsize(1020, 680)
        self.root.configure(bg=styles.BG_DARK)

        # Initialize Camera Manager and Hand Detector
        self.camera = CameraManager(device_index=camera_index, resolution=(1280, 720))
        self.hand_detector = HandDetector(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )

        # Hand detection feature toggles
        self.enable_hand_tracking = True
        self.enable_bounding_box = True
        self._last_hand_count = 0

        # Tkinter image reference to avoid garbage collection
        self._current_photo_image: Optional[ImageTk.PhotoImage] = None
        self._is_closing = False

        # Build UI layout
        self._setup_styles()
        self._build_header()
        self._build_main_content()
        self._build_footer()
        self._bind_shortcuts()

        # Handle graceful window exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start camera stream on startup
        self.log_message("System initialized. Starting camera and MediaPipe pipeline...")
        self.camera.start()
        self._update_ui_state()

        # Start frame refresh loop
        self._refresh_frame_loop()

    def _setup_styles(self) -> None:
        """Configure ttk styles for uniform dark theme widgets."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

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

    def _build_header(self) -> None:
        """Build the top header banner with title and live telemetry badges."""
        header_frame = tk.Frame(self.root, bg=styles.BG_PANEL, height=70, padx=20, pady=10)
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
            text="NUV CGIP Project | Dhruv Pankhania • Krish Jadav • Dhairya Patel",
            font=styles.FONT_SMALL,
            fg=styles.TEXT_SECONDARY,
            bg=styles.BG_PANEL,
        )
        subtitle_lbl.pack(anchor="w")

        # Telemetry & Status Badges
        badge_box = tk.Frame(header_frame, bg=styles.BG_PANEL)
        badge_box.pack(side=tk.RIGHT, fill=tk.Y)

        # Hands Detected badge
        self.hands_badge = tk.Label(
            badge_box,
            text="✋ 0 HANDS",
            font=styles.FONT_SUBTITLE,
            fg=styles.ACCENT_PURPLE,
            bg=styles.BG_CARD,
            padx=12,
            pady=4,
            relief=tk.FLAT,
        )
        self.hands_badge.pack(side=tk.LEFT, padx=5)

        # FPS badge
        self.fps_badge = tk.Label(
            badge_box,
            text="FPS: 0.0",
            font=styles.FONT_FPS,
            fg=styles.ACCENT_GREEN,
            bg=styles.BG_CARD,
            padx=12,
            pady=4,
            relief=tk.FLAT,
        )
        self.fps_badge.pack(side=tk.LEFT, padx=5)

        # Status badge
        self.status_badge = tk.Label(
            badge_box,
            text="● INITIALIZING",
            font=styles.FONT_SUBTITLE,
            fg=styles.ACCENT_YELLOW,
            bg=styles.BG_CARD,
            padx=12,
            pady=4,
            relief=tk.FLAT,
        )
        self.status_badge.pack(side=tk.LEFT, padx=5)

    def _build_main_content(self) -> None:
        """Build the central viewport split into video feed and controls."""
        main_frame = tk.Frame(self.root, bg=styles.BG_DARK, padx=15, pady=15)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Column: Video Viewport Container
        video_container = tk.Frame(
            main_frame,
            bg=styles.BG_PANEL,
            highlightbackground=styles.BORDER_COLOR,
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        video_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Viewport Header
        viewport_hdr = tk.Frame(video_container, bg=styles.BG_PANEL)
        viewport_hdr.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))

        vtitle = tk.Label(
            viewport_hdr,
            text="📹 Live Camera & Landmark Viewport",
            font=styles.FONT_SECTION,
            fg=styles.TEXT_PRIMARY,
            bg=styles.BG_PANEL,
        )
        vtitle.pack(side=tk.LEFT)

        self.resolution_lbl = tk.Label(
            viewport_hdr,
            text="1280x720 (HD)",
            font=styles.FONT_SMALL,
            fg=styles.TEXT_MUTED,
            bg=styles.BG_PANEL,
        )
        self.resolution_lbl.pack(side=tk.RIGHT)

        # Video Canvas / Display Label
        self.video_canvas = tk.Canvas(
            video_container,
            bg="#0f0f17",
            highlightthickness=0,
        )
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # Right Column: Control Deck & Cheat Sheet
        sidebar = tk.Frame(main_frame, bg=styles.BG_DARK, width=400)
        sidebar.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        sidebar.pack_propagate(False)

        # Card 1: Camera Controls
        self._build_camera_controls_card(sidebar)

        # Card 2: Hand Tracking Controls (Week 5)
        self._build_hand_controls_card(sidebar)

        # Card 3: Gesture Cheat Sheet
        self._build_gestures_card(sidebar)

        # Card 4: Activity Log Viewer
        self._build_logs_card(sidebar)

    def _build_camera_controls_card(self, parent: tk.Frame) -> None:
        """Card containing webcam device selection, toggle, and settings."""
        card = tk.Frame(
            parent,
            bg=styles.BG_PANEL,
            highlightbackground=styles.BORDER_COLOR,
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        card.pack(fill=tk.X, pady=(0, 8))

        lbl = tk.Label(
            card,
            text="⚙️ Camera Hardware Controls",
            font=styles.FONT_SECTION,
            fg=styles.ACCENT_BLUE,
            bg=styles.BG_PANEL,
        )
        lbl.pack(anchor="w", pady=(0, 6))

        # Device & Resolution Rows
        row1 = tk.Frame(card, bg=styles.BG_PANEL)
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Device:", font=styles.FONT_BODY_BOLD, fg=styles.TEXT_SECONDARY, bg=styles.BG_PANEL).pack(side=tk.LEFT)

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

        row2 = tk.Frame(card, bg=styles.BG_PANEL)
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Resolution:", font=styles.FONT_BODY_BOLD, fg=styles.TEXT_SECONDARY, bg=styles.BG_PANEL).pack(side=tk.LEFT)

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

        # Buttons Grid
        btn_grid = tk.Frame(card, bg=styles.BG_PANEL)
        btn_grid.pack(fill=tk.X, pady=(6, 0))

        self.btn_toggle_camera = tk.Button(
            btn_grid,
            text="⏹ Stop Camera",
            font=styles.FONT_BODY_BOLD,
            bg=styles.BTN_STOP_BG,
            fg=styles.BTN_STOP_FG,
            activebackground=styles.ACCENT_RED,
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self._toggle_camera_stream,
            cursor="hand2",
        )
        self.btn_toggle_camera.pack(fill=tk.X, pady=2)

        btn_sub_row = tk.Frame(btn_grid, bg=styles.BG_PANEL)
        btn_sub_row.pack(fill=tk.X, pady=2)

        self.btn_mirror = tk.Button(
            btn_sub_row,
            text="🪞 Mirror: ON",
            font=styles.FONT_SMALL,
            bg=styles.BTN_SECONDARY_BG,
            fg=styles.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=6,
            pady=3,
            command=self._toggle_mirror,
            cursor="hand2",
        )
        self.btn_mirror.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_pause = tk.Button(
            btn_sub_row,
            text="⏸ Pause",
            font=styles.FONT_SMALL,
            bg=styles.BTN_SECONDARY_BG,
            fg=styles.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=6,
            pady=3,
            command=self._toggle_pause,
            cursor="hand2",
        )
        self.btn_pause.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.btn_snapshot = tk.Button(
            btn_sub_row,
            text="📸 Snapshot",
            font=styles.FONT_SMALL,
            bg=styles.BTN_ACTION_BG,
            fg=styles.BTN_ACTION_FG,
            relief=tk.FLAT,
            padx=6,
            pady=3,
            command=self._take_snapshot,
            cursor="hand2",
        )
        self.btn_snapshot.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

    def _build_hand_controls_card(self, parent: tk.Frame) -> None:
        """Card containing MediaPipe Hand Detection controls and configuration."""
        card = tk.Frame(
            parent,
            bg=styles.BG_PANEL,
            highlightbackground=styles.BORDER_COLOR,
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        card.pack(fill=tk.X, pady=(0, 8))

        lbl = tk.Label(
            card,
            text="🖐️ MediaPipe Hand Tracking (Week 5)",
            font=styles.FONT_SECTION,
            fg=styles.ACCENT_PURPLE,
            bg=styles.BG_PANEL,
        )
        lbl.pack(anchor="w", pady=(0, 6))

        # Max Hands selector
        row_hands = tk.Frame(card, bg=styles.BG_PANEL)
        row_hands.pack(fill=tk.X, pady=2)
        tk.Label(
            row_hands, text="Max Hands:", font=styles.FONT_BODY_BOLD, fg=styles.TEXT_SECONDARY, bg=styles.BG_PANEL
        ).pack(side=tk.LEFT)

        self.max_hands_var = tk.StringVar(value="2 Hands")
        self.max_hands_combo = ttk.Combobox(
            row_hands,
            textvariable=self.max_hands_var,
            values=["1 Hand", "2 Hands"],
            state="readonly",
            width=14,
        )
        self.max_hands_combo.pack(side=tk.RIGHT)
        self.max_hands_combo.bind("<<ComboboxSelected>>", self._on_max_hands_changed)

        # Overlay Toggle Buttons Row
        btn_row = tk.Frame(card, bg=styles.BG_PANEL)
        btn_row.pack(fill=tk.X, pady=(6, 0))

        self.btn_toggle_skeleton = tk.Button(
            btn_row,
            text="🦴 Skeleton: ON",
            font=styles.FONT_SMALL,
            bg=styles.ACCENT_CYAN,
            fg=styles.BTN_START_FG,
            relief=tk.FLAT,
            padx=8,
            pady=4,
            command=self._toggle_skeleton,
            cursor="hand2",
        )
        self.btn_toggle_skeleton.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.btn_toggle_bbox = tk.Button(
            btn_row,
            text="📦 Bounding Box: ON",
            font=styles.FONT_SMALL,
            bg=styles.ACCENT_BLUE,
            fg=styles.BTN_START_FG,
            relief=tk.FLAT,
            padx=8,
            pady=4,
            command=self._toggle_bounding_box,
            cursor="hand2",
        )
        self.btn_toggle_bbox.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(2, 0))

    def _build_gestures_card(self, parent: tk.Frame) -> None:
        """Gesture Cheat Sheet reference card (Weeks 5-6 Preview)."""
        card = tk.Frame(
            parent,
            bg=styles.BG_PANEL,
            highlightbackground=styles.BORDER_COLOR,
            highlightthickness=1,
            padx=14,
            pady=8,
        )
        card.pack(fill=tk.X, pady=(0, 8))

        lbl = tk.Label(
            card,
            text="💡 Gesture Guide & Hand Geometry",
            font=styles.FONT_SECTION,
            fg=styles.ACCENT_YELLOW,
            bg=styles.BG_PANEL,
        )
        lbl.pack(anchor="w", pady=(0, 4))

        gestures = [
            ("👉 Point Right", "Next Slide (Index Extended)"),
            ("👈 Point Left", "Previous Slide (Thumb/Index Left)"),
            ("✋ Open Palm", "Pointer Mode (5 Fingers Extended)"),
            ("✊ Fist", "Pause Navigation (0 Fingers)"),
            ("🤏 Pinch Index", "Annotation Pen (Thumb-Index Distance)"),
        ]

        for gesture, action in gestures:
            row = tk.Frame(card, bg=styles.BG_PANEL)
            row.pack(fill=tk.X, pady=1)

            tk.Label(
                row,
                text=gesture,
                font=styles.FONT_BODY_BOLD,
                fg=styles.ACCENT_YELLOW,
                bg=styles.BG_PANEL,
            ).pack(side=tk.LEFT)

            tk.Label(
                row,
                text=f": {action}",
                font=styles.FONT_SMALL,
                fg=styles.TEXT_SECONDARY,
                bg=styles.BG_PANEL,
            ).pack(side=tk.LEFT)

    def _build_logs_card(self, parent: tk.Frame) -> None:
        """Real-time scrolling system activity log viewer."""
        card = tk.Frame(
            parent,
            bg=styles.BG_PANEL,
            highlightbackground=styles.BORDER_COLOR,
            highlightthickness=1,
            padx=14,
            pady=8,
        )
        card.pack(fill=tk.BOTH, expand=True)

        lbl = tk.Label(
            card,
            text="📋 Activity & Telemetry Log",
            font=styles.FONT_SECTION,
            fg=styles.TEXT_PRIMARY,
            bg=styles.BG_PANEL,
        )
        lbl.pack(anchor="w", pady=(0, 3))

        self.log_text = tk.Text(
            card,
            bg=styles.BG_INPUT,
            fg=styles.TEXT_PRIMARY,
            insertbackground=styles.ACCENT_CYAN,
            font=styles.FONT_MONO,
            relief=tk.FLAT,
            height=5,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)

    def _build_footer(self) -> None:
        """Bottom status bar with system information and shortcuts."""
        footer_frame = tk.Frame(self.root, bg=styles.BG_PANEL, height=30, padx=15, pady=4)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = tk.Label(
            footer_frame,
            text="Ready. Space: Start/Stop | H: Skeleton | B: Bounding Box | M: Mirror | S: Snapshot",
            font=styles.FONT_SMALL,
            fg=styles.TEXT_MUTED,
            bg=styles.BG_PANEL,
        )
        self.status_label.pack(side=tk.LEFT)

        version_lbl = tk.Label(
            footer_frame,
            text="Version: Milestone Week 5 (MediaPipe 21-Landmark Tracking)",
            font=styles.FONT_SMALL,
            fg=styles.TEXT_MUTED,
            bg=styles.BG_PANEL,
        )
        version_lbl.pack(side=tk.RIGHT)

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts for quick control."""
        self.root.bind("<space>", lambda e: self._toggle_camera_stream())
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

    def log_message(self, message: str) -> None:
        """Append a timestamped log line to the activity log."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_device_changed(self, event=None) -> None:
        """Handle camera index switch from dropdown."""
        selected_text = self.device_var.get()
        try:
            device_idx = int(selected_text.split()[-1])
            self.log_message(f"Switching to Camera index {device_idx}...")
            self.camera.set_device(device_idx)
            self.log_message(f"Active camera device set to {device_idx}.")
        except Exception as err:
            self.log_message(f"Error switching camera device: {err}")

    def _on_resolution_changed(self, event=None) -> None:
        """Handle resolution change from dropdown."""
        selected_res = self.res_var.get()
        if selected_res in self.camera.RESOLUTIONS:
            w, h = self.camera.RESOLUTIONS[selected_res]
            self.camera.set_resolution(w, h)
            self.resolution_lbl.configure(text=selected_res)
            self.log_message(f"Resolution set to {w}x{h}.")

    def _on_max_hands_changed(self, event=None) -> None:
        """Update maximum number of hands tracked simultaneously."""
        selected = self.max_hands_var.get()
        num_hands = 1 if "1" in selected else 2
        self.hand_detector.close()
        self.hand_detector = HandDetector(
            max_num_hands=num_hands,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
        )
        self.log_message(f"Max hands tracking set to {num_hands}.")

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
        self.btn_toggle_bbox.configure(text=f"📦 Bounding Box: {state}", bg=bg_col, fg=fg_col)
        self.log_message(f"Hand bounding box overlay turned {state}.")

    def _toggle_camera_stream(self) -> None:
        """Start or stop the camera video capture stream."""
        if self.camera.is_running:
            self.camera.stop()
            self.log_message("Camera stream stopped.")
            self.btn_toggle_camera.configure(
                text="▶ Start Camera",
                bg=styles.BTN_START_BG,
                fg=styles.BTN_START_FG,
                activebackground=styles.ACCENT_GREEN,
            )
            self.status_badge.configure(text="● STOPPED", fg=styles.ACCENT_RED)
            self.fps_badge.configure(text="FPS: 0.0")
            self.hands_badge.configure(text="✋ STOPPED", fg=styles.TEXT_MUTED)
            self.video_canvas.delete("all")
        else:
            self.camera.start()
            self.log_message("Camera stream started.")
            self.btn_toggle_camera.configure(
                text="⏹ Stop Camera",
                bg=styles.BTN_STOP_BG,
                fg=styles.BTN_STOP_FG,
                activebackground=styles.ACCENT_RED,
            )
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
        """Update badges based on camera connection."""
        if self.camera.is_running:
            if self.camera.is_camera_connected:
                self.status_badge.configure(text="● CAMERA LIVE", fg=styles.ACCENT_GREEN)
            else:
                self.status_badge.configure(text="● TEST PATTERN", fg=styles.ACCENT_YELLOW)

    def _refresh_frame_loop(self) -> None:
        """Periodic rendering loop to process MediaPipe landmarks and update canvas."""
        if self._is_closing:
            return

        if self.camera.is_running:
            success, raw_frame = self.camera.get_frame()

            if raw_frame is not None:
                # Update FPS badge
                fps = self.camera.get_fps()
                self.fps_badge.configure(text=f"FPS: {fps:0.1f}")
                self._update_ui_state()

                display_frame = raw_frame
                hand_count = 0

                # Process hand landmark detection
                if self.enable_hand_tracking:
                    display_frame, detected_hands = self.hand_detector.find_hands(
                        raw_frame,
                        draw=self.enable_hand_tracking,
                        draw_box=self.enable_bounding_box,
                    )
                    hand_count = len(detected_hands)

                    if hand_count > 0:
                        primary_hand = detected_hands[0]
                        label = primary_hand["label"]
                        conf = int(primary_hand["confidence"] * 100)
                        if hand_count == 1:
                            self.hands_badge.configure(
                                text=f"✋ 1 HAND ({label}: {conf}%)",
                                fg=styles.ACCENT_GREEN,
                            )
                        else:
                            self.hands_badge.configure(
                                text=f"✋ 2 HANDS DETECTED",
                                fg=styles.ACCENT_GREEN,
                            )
                    else:
                        self.hands_badge.configure(
                            text="✋ 0 HANDS",
                            fg=styles.ACCENT_PURPLE,
                        )

                    # Log detection transitions
                    if hand_count != self._last_hand_count:
                        if hand_count > 0:
                            labels_str = ", ".join([f"{h['label']} ({int(h['confidence']*100)}%)" for h in detected_hands])
                            self.log_message(f"Tracking acquired: {labels_str}")
                        else:
                            self.log_message("Tracking lost: Hand exited frame.")
                        self._last_hand_count = hand_count
                else:
                    self.hands_badge.configure(text="✋ SKELETON OFF", fg=styles.TEXT_MUTED)

                # Get canvas size
                canvas_width = max(self.video_canvas.winfo_width(), 100)
                canvas_height = max(self.video_canvas.winfo_height(), 100)

                # Convert BGR (OpenCV) to RGB (PIL)
                rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                h, w, _ = rgb_frame.shape

                # Scale to fit canvas maintaining aspect ratio
                scale = min(canvas_width / w, canvas_height / h)
                nw, nh = max(int(w * scale), 1), max(int(h * scale), 1)

                resized_frame = cv2.resize(rgb_frame, (nw, nh), interpolation=cv2.INTER_AREA)

                # Convert to PIL Image & ImageTk
                img = Image.fromarray(resized_frame)
                self._current_photo_image = ImageTk.PhotoImage(image=img)

                # Draw centered on canvas
                self.video_canvas.delete("all")
                cx = canvas_width // 2
                cy = canvas_height // 2
                self.video_canvas.create_image(cx, cy, anchor=tk.CENTER, image=self._current_photo_image)

        # Re-schedule after ~30ms (~33 FPS refresh)
        self.root.after(30, self._refresh_frame_loop)

    def on_close(self) -> None:
        """Gracefully terminate background threads and close window."""
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
