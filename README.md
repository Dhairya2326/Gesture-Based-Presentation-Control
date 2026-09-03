# Gesture-Based Presentation Control using Computer Vision

A contactless, intuitive Human-Computer Interaction (HCI) system that enables presenters to navigate slides and control multimedia presentations using real-time hand gestures captured via a standard webcam.

---

## 👥 Project Team Members
- **Dhruv Pankhania** (ID: `24001158`)
- **Krish Jadav** (ID: `24000638`)
- **Dhairya Patel** (ID: `24001142`)

---

## 📅 Project Progress (Milestone: Week 5)

| Milestone | Status | Description |
| :--- | :---: | :--- |
| **Week 1: Literature Survey & Project Planning** | ✅ Completed | Comprehensive survey of vision-based HCI, comparison with sensor gloves, tech stack selection, and weekly roadmap. |
| **Week 2: Requirement Analysis & Software Setup** | ✅ Completed | Specification of functional & non-functional requirements, setup of Python 3.11 environment with OpenCV, MediaPipe, NumPy, PyAutoGUI, Pillow. |
| **Week 3: GUI Design** | ✅ Completed | Modern dark-themed Tkinter command center with live video viewport, telemetry badges, gesture reference guide, and real-time activity log. |
| **Week 4: Webcam Integration using OpenCV** | ✅ Completed | Multi-threaded `CameraManager` pipeline with asynchronous frame capture, real-time FPS calculation, dynamic device switching, mirror mode, and graceful fallback. |
| **Week 5: Hand Detection using MediaPipe** | ✅ Completed | Real-time 21 3D hand landmarks tracking, custom neon skeleton overlay, handedness classification, dynamic bounding boxes, and geometric telemetry. |
| **Week 6: Gesture Recognition Development** | 🔜 Upcoming | Heuristic and geometric gesture classification algorithms. |
| **Week 7: Presentation Controller Integration** | 🔜 Upcoming | Keystroke simulation for slide navigation with debounce cooldown. |

---

## 🛠️ Technology Stack
- **Language**: Python 3.11
- **Computer Vision**: OpenCV (`cv2`)
- **Hand Landmark Tracking**: MediaPipe Hands (21 3D Keypoints & BlazePalm)
- **GUI Framework**: Tkinter (Native cross-platform UI with Dark Slate theme)
- **Image Processing**: Pillow (PIL) & NumPy
- **Automation**: PyAutoGUI

---

## 📂 Project Structure
```
Gesture-Based-Presentation-Control/
├── assets/                  # Captured snapshots and visual assets
├── docs/                    # Weekly project milestone documentation
│   ├── week1_literature_survey_and_project_planning.md
│   ├── week2_requirement_analysis_and_software_setup.md
│   ├── week3_gui_design.md
│   ├── week4_webcam_integration.md
│   ├── week5_hand_detection_mediapipe.md
│   └── README.md
├── src/
│   ├── gui/                 # User Interface components
│   │   ├── __init__.py
│   │   ├── app.py           # PresentationControllerApp (Tkinter window)
│   │   └── styles.py        # Modern dark theme tokens & colors
│   ├── processing/          # Computer Vision & Video pipelines
│   │   ├── __init__.py
│   │   ├── camera.py        # Multi-threaded OpenCV CameraManager
│   │   └── hand_detector.py # MediaPipe Hands 21-landmark tracking module
│   ├── presentation/        # Automation & Controller stubs
│   │   ├── __init__.py
│   │   └── controller.py    # Presentation navigation controller
│   ├── __init__.py
│   └── main.py              # Application main launcher
├── tests/                   # Automated unit tests
│   ├── test_camera.py
│   ├── test_gui.py
│   └── test_hand_detector.py
├── requirements.txt         # Project Python dependencies
└── README.md                # Project documentation overview
```

---

## 🚀 Getting Started

### 1. Prerequisites & Installation
Ensure you have Python 3.11+ installed. Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Running the Application
Launch the main presentation controller application:
```bash
python -m src.main
```
Or directly:
```bash
python src/main.py
```

Optional command-line arguments:
- Specify a custom camera device index:
  ```bash
  python src/main.py --camera-index 1
  ```

---

## 🎮 Controls & Shortcuts

| Action | Shortcut / Control | Description |
| :--- | :---: | :--- |
| **Start / Stop Stream** | `Space` / Button | Toggles webcam video capture stream on/off. |
| **Toggle Hand Skeleton**| `H` / Button | Toggles 21-landmark joint and bone visual overlay. |
| **Toggle Bounding Box** | `B` / Button | Toggles hand bounding box, handedness label, and confidence badge. |
| **Mirror Mode** | `M` / Button | Toggles horizontal frame flip for natural presenter view. |
| **Pause / Resume** | `P` / Button | Freezes current video stream frame. |
| **Capture Snapshot** | `S` / Button | Saves the current camera frame to `assets/`. |
| **Max Hands Selection** | Dropdown | Switch between single hand (1 Hand) or dual hand (2 Hands) tracking. |
| **Device Selection** | Dropdown | Dynamically switch between connected camera devices. |
| **Resolution Selection**| Dropdown | Switch between 640x480 (SD), 1280x720 (HD), and 1920x1080 (FHD). |

---

## 🧪 Running Unit Tests
Run the automated test suite:
```bash
python -m unittest discover -s tests
```
