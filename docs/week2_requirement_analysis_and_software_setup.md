# Week 2: Requirement Analysis and Software Setup

## 1. System Requirements Analysis

### 1.1 Functional Requirements (FR)
- **FR-1: Real-time Video Stream Capture**: The system must capture video frames from an integrated or USB webcam at a minimum of 30 FPS.
- **FR-2: Dynamic Device & Resolution Selection**: The system must allow users to choose available webcam device indices (0, 1, etc.) and resolution modes (640x480, 1280x720).
- **FR-3: Stream Control & Mirroring**: The user must be able to start, pause, resume, stop the video stream, and toggle horizontal mirroring.
- **FR-4: Graphical User Interface (GUI)**: The application must provide a responsive Tkinter GUI displaying the live video feed, real-time FPS metric, system logs, and quick control buttons.
- **FR-5: Hand Landmark Extraction (Future Integration)**: The processing module must extract 21 distinct 3D landmarks for detected hands.
- **FR-6: Presentation Command Dispatching (Future Integration)**: The system must map recognized gestures to keyboard keystrokes (e.g., `Right Arrow` for Next Slide, `Left Arrow` for Previous Slide, `F5` / `Esc` for Fullscreen).

### 1.2 Non-Functional Requirements (NFR)
- **NFR-1: Performance & Latency**: Frame capture and UI rendering pipeline must maintain < 35ms per-frame total processing time.
- **NFR-2: Reliability & Error Handling**: If the webcam is disconnected or unavailable, the application must display a descriptive error/placeholder without crashing.
- **NFR-3: Thread Safety**: Heavy video capture operations must run asynchronously in background worker threads to prevent GUI freezing.
- **NFR-4: Usability & Aesthetics**: The UI must use a clean, modern dark theme with high-contrast status feedback and clear visual cues.

---

## 2. Hardware and Software Specifications

### 2.1 Hardware Requirements
- **Processor**: Intel Core i3 / AMD Ryzen 3 or higher.
- **RAM**: Minimum 4 GB (8 GB recommended).
- **Camera**: Built-in HD webcam or USB camera supporting 720p at 30 FPS.
- **Display**: Minimum screen resolution 1280 x 720.

### 2.2 Software Environment
- **Operating System**: Windows 10 / 11, Linux, or macOS.
- **Python Version**: Python 3.11+
- **Key Dependencies**:
  - `opencv-python` (v4.8+)
  - `mediapipe` (v0.10+)
  - `numpy` (v1.24+)
  - `pyautogui` (v0.9.54+)
  - `pillow` (PIL v10.0+)

---

## 3. Software Environment Setup Verification

The environment is set up and verified with the following package checklist:
```text
Python 3.11.9
├── opencv-python / opencv-contrib-python (Computer Vision & Video Capture)
├── mediapipe (Hand landmark ML models)
├── numpy (Matrix and tensor operations)
├── pyautogui (Keystroke & mouse automation)
└── pillow (Image format conversion for Tkinter display)
```

---

## 4. Directory & Modular Architecture
```
Gesture-Based-Presentation-Control/
├── assets/                  # Icons, graphic assets, demo media
├── docs/                    # Weekly milestones & project documentation
│   ├── week1_literature_survey_and_project_planning.md
│   ├── week2_requirement_analysis_and_software_setup.md
│   ├── week3_gui_design.md
│   └── week4_webcam_integration.md
├── src/
│   ├── gui/                 # Tkinter User Interface components
│   │   ├── __init__.py
│   │   ├── app.py           # Main window application
│   │   └── styles.py        # Color palette, font definitions, and widgets
│   ├── processing/          # Computer Vision & Video pipelines
│   │   ├── __init__.py
│   │   └── camera.py        # OpenCV VideoCapture wrapper & thread manager
│   ├── presentation/        # Keystroke automation & slide controllers
│   │   ├── __init__.py
│   │   └── controller.py    # Slide controller stub
│   ├── __init__.py
│   └── main.py              # Application entrypoint
├── tests/                   # Automated unit & integration tests
│   ├── test_camera.py
│   └── test_gui.py
├── requirements.txt         # Project package requirements
└── README.md                # Project documentation overview
```
