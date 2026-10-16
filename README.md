# Gesture-Based Presentation Control using Computer Vision

A contactless, intuitive Human-Computer Interaction (HCI) desktop system that enables presenters to navigate slides, control multimedia presentations, highlight points with a virtual laser pointer, and annotate slide graphics using real-time hand gestures captured via a standard webcam.

---

## 👥 Project Team Members
- **Dhruv Pankhania** (ID: `24001158`)
- **Krish Jadav** (ID: `24000638`)
- **Dhairya Patel** (ID: `24001142`)

*Navrachana University — School of Engineering & Technology (NUV SE&T)*  
*Course: Computer Graphics & Image Processing (CGIP) — End Semester Project*

---

## 📅 Project Progress (All 10 Milestones Complete ✅)

| Milestone | Status | Description |
| :--- | :---: | :--- |
| **Week 1: Literature Survey & Project Planning** | ✅ Completed | Comprehensive survey of vision-based HCI, comparison with sensor gloves, tech stack selection, and weekly roadmap. |
| **Week 2: Requirement Analysis & Software Setup** | ✅ Completed | Specification of functional & non-functional requirements, setup of Python 3.11 environment with OpenCV, MediaPipe, NumPy, PyAutoGUI, Pillow. |
| **Week 3: GUI Design** | ✅ Completed | Modern dark-themed Tkinter command center with live video viewport, telemetry badges, gesture reference guide, and real-time activity log. |
| **Week 4: Webcam Integration using OpenCV** | ✅ Completed | Multi-threaded `CameraManager` pipeline with asynchronous frame capture, real-time FPS calculation, dynamic device switching, mirror mode, and graceful fallback. |
| **Week 5: Hand Detection using MediaPipe** | ✅ Completed | Real-time 21 3D hand landmarks tracking, custom neon skeleton overlay, handedness classification, dynamic bounding boxes, and geometric telemetry. |
| **Week 6: Gesture Recognition Development** | ✅ Completed | Rule-based & geometric gesture classification engine, scale normalization, temporal smoothing, HUD overlays, and presentation dispatching. |
| **Week 7: Presentation Controller Integration** | ✅ Completed | Full PyAutoGUI OS-level slide automation for PowerPoint, Google Slides, PDF, and Media Players with debounce cooldown engine. |
| **Week 8: Virtual Laser Pointer & Drawing Mode** | ✅ Completed | Real-time index finger laser tracking with optical glow, EMA coordinate smoothing, and Pinch-driven slide annotation canvas. |
| **Week 9: Testing, Optimization & Benchmarking** | ✅ Completed | Latency profiling framework, automated benchmark suite, CPU/memory profiling, and unit test expansion (44 tests). |
| **Week 10: Final Documentation & Presentation** | ✅ Completed | Executive summary, completed milestone matrix, system architecture, user manual, and performance evaluation. |

---

## 🛠️ Technology Stack
- **Language**: Python 3.11
- **Computer Vision**: OpenCV (`cv2`)
- **Hand Landmark Tracking**: MediaPipe Hands (21 3D Keypoints & BlazePalm)
- **Gesture Classification**: Rule-based geometric heuristics & spatial scale normalization
- **GUI Framework**: Tkinter (Native cross-platform UI with Modern Dark Slate theme & Notebook tabs)
- **Image Processing**: Pillow (PIL) & NumPy
- **Automation**: PyAutoGUI (Cross-platform keyboard and mouse automation)
- **Benchmarking**: High-resolution OS perf counters & `tracemalloc`

---

## 📂 Project Structure
```
Gesture-Based-Presentation-Control/
├── assets/                  # Captured snapshots and visual assets
├── docs/                    # Weekly project milestone documentation (Weeks 1 to 10)
│   ├── week1_literature_survey_and_project_planning.md
│   ├── week2_requirement_analysis_and_software_setup.md
│   ├── week3_gui_design.md
│   ├── week4_webcam_integration.md
│   ├── week5_hand_detection_mediapipe.md
│   ├── week6_gesture_recognition_development.md
│   ├── week7_presentation_controller_integration.md
│   ├── week8_virtual_laser_pointer_and_drawing_mode.md
│   ├── week9_testing_optimization_and_benchmarking.md
│   ├── week10_final_documentation_and_project_summary.md
│   └── README.md
├── src/
│   ├── gui/                 # User Interface components
│   │   ├── __init__.py
│   │   ├── app.py           # PresentationControllerApp (Tkinter window & Tabbed deck)
│   │   └── styles.py        # Modern dark theme tokens & colors
│   ├── processing/          # Computer Vision & Video pipelines
│   │   ├── __init__.py
│   │   ├── camera.py        # Multi-threaded OpenCV CameraManager
│   │   ├── hand_detector.py # MediaPipe Hands 21-landmark tracking module
│   │   ├── gesture_recognizer.py # 21-landmark Gesture Recognition engine
│   │   └── benchmarking.py  # Latency profiler & automated benchmark runner
│   ├── presentation/        # Automation & Controller engine
│   │   ├── __init__.py
│   │   ├── controller.py    # PyAutoGUI presentation controller with profiles
│   │   ├── laser_pointer.py # Virtual laser pointer with optical glow & smoothing
│   │   ├── annotator.py     # Slide annotation & freehand drawing canvas
│   │   └── slides.py        # Built-in slide deck generator & renderer
│   ├── __init__.py
│   └── main.py              # Application main launcher
├── tests/                   # Automated unit tests (44 tests, 100% pass)
│   ├── test_camera.py
│   ├── test_gui.py
│   ├── test_hand_detector.py
│   ├── test_gesture_recognizer.py
│   ├── test_presentation_controller.py
│   ├── test_laser_and_annotator.py
│   └── test_benchmarking_and_slides.py
├── build_exe.bat            # Automated PyInstaller .exe compilation script
├── run.bat                  # One-click Windows batch launcher
├── requirements.txt         # Project Python dependencies
└── README.md                # Project documentation overview
```

---

## 🚀 Getting Started

### ⚡ Quick Start (One-Click)
Simply **double-click [`run.bat`](file:///c:/NUV/CGIP/Presentation%20Controller%20End%20Sem/Gesture-Based-Presentation-Control/run.bat)** in the root directory. It will automatically verify your Python environment, install any missing dependencies, and launch the presentation controller GUI.

### 💻 Manual Command Line
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the application:
   ```bash
   python -m src.main
   ```
3. (Optional) Custom camera index:
   ```bash
   python -m src.main --camera-index 1
   ```

### 📦 Standalone Executable (.exe)
To compile a standalone Windows desktop executable:
```bash
build_exe.bat
```
The compiled application will be generated in `dist\GesturePresentationController\GesturePresentationController.exe`.

---

## 🎮 Controls & Shortcuts

| Action | Shortcut / Control | Description |
| :--- | :---: | :--- |
| **Start / Stop Stream** | `Space` / Button | Toggles webcam video capture stream on/off. |
| **Gesture Recognition** | `G` / Button | Toggles real-time gesture recognition engine on/off. |
| **Gesture Visual HUD**  | `D` / Button | Toggles gesture badge, pinch gauge, and laser reticle overlays. |
| **Toggle Hand Skeleton**| `H` / Button | Toggles 21-landmark joint and bone visual overlay. |
| **Toggle Bounding Box** | `B` / Button | Toggles hand bounding box, handedness label, and confidence badge. |
| **Virtual Laser Pointer** | `L` / Button | Toggles glowing virtual laser pointer crosshair and beam trail. |
| **Clear Drawing Canvas** | `C` / Button | Wipes all freehand annotations from the screen/presentation. |
| **Undo Stroke** | `U` / Button | Undoes the most recent drawn annotation stroke. |
| **Toggle OS Mode** | `O` / Button | Toggles between **Live OS mode** (keys sent) and **Simulation mode**. |
| **Toggle View Mode** | `V` / Button | Switches between **Camera View** and **Interactive Slide Deck View**. |
| **Manual Slide Next/Prev** | `Left` / `Right` | Navigates previous or next presentation slide. |
| **Mirror Mode** | `M` / Button | Toggles horizontal frame flip for natural presenter view. |
| **Pause / Resume** | `P` / Button | Freezes current video stream frame. |
| **Capture Snapshot** | `S` / Button | Saves the current camera frame to `assets/`. |
| **Target Profile** | Dropdown | Select between PowerPoint, Google Slides, PDF Viewer, Media Player. |
| **Action Cooldown** | Dropdown | Adjust presentation trigger debounce delay (0.5s to 2.0s). |
| **Smoothing Buffer** | Dropdown | Switch gesture temporal voting buffer (1 to 12 frames). |
| **Device Selection** | Dropdown | Dynamically switch between connected camera devices. |
| **Resolution Selection**| Dropdown | Switch between 640x480 (SD), 1280x720 (HD), and 1920x1080 (FHD). |

---

## 📊 Performance Benchmarks (Week 9 Evaluation)

| Metric | Specification | Measured Value |
| :--- | :---: | :---: |
| **Throughput (FPS)** | $\ge 30\text{ FPS}$ | **$43.0\text{ FPS}$** |
| **Mean End-to-End Latency** | $< 50.0\text{ ms}$ | **$23.13\text{ ms}$** |
| **95th Percentile Latency (P95)** | $< 60.0\text{ ms}$ | **$24.58\text{ ms}$** |
| **Hand Landmark Tracking** | $< 35.0\text{ ms}$ | **$19.49\text{ ms}$** |
| **Gesture Classification** | $< 2.0\text{ ms}$ | **$0.19\text{ ms}$** |
| **Laser & Annotation Rendering** | $< 8.0\text{ ms}$ | **$3.46\text{ ms}$** |
| **Peak Memory Allocation** | $< 50.0\text{ MB}$ | **$10.71\text{ MB}$** |

---

## 🧪 Running Unit Tests
Run the complete automated test suite (44 tests):
```bash
python -m unittest discover -s tests
```
