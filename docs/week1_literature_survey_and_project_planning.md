# Week 1: Literature Survey and Project Planning

## 1. Project Title
**Gesture-Based Presentation Control using Computer Vision**

## 2. Project Team Members
1. Dhruv Pankhania (ID: 24001158)
2. Krish Jadav (ID: 24000638)
3. Dhairya Patel (ID: 24001142)

---

## 3. Literature Survey

### 3.1 Background & Motivation
Traditional presentation controllers rely on handheld hardware remotes, mice, keyboards, or touchpads. These devices can disrupt the natural flow of a presenter, require constant physical tethering or battery management, and limit physical expression. Vision-based Human-Computer Interaction (HCI) offers a contactless, intuitive alternative by recognizing natural hand gestures using standard consumer webcams without specialized hardware or wearable sensors.

### 3.2 Existing Approaches & Related Work
1. **Color-based Skin Detection and Contour Analysis**:
   - *Technique*: HSV color thresholding followed by convex hull and convexity defects.
   - *Limitations*: Highly sensitive to lighting changes, skin tone variations, and background clutter.
2. **Wearable Sensor-based Gloves (Data Gloves)**:
   - *Technique*: Flex sensors and IMUs (accelerometers/gyroscopes) transmitting over RF/Bluetooth.
   - *Limitations*: Expensive, uncomfortable, intrusive, and requires dedicated hardware maintenance.
3. **Deep Learning Landmark Detection (MediaPipe Hands / OpenPose)**:
   - *Technique*: Two-stage pipeline: a Palm Detector (BlazePalm) operating on full images, followed by a Hand Landmark Model predicting 21 3D coordinates on the detected hand bounding box.
   - *Advantages*: Real-time inference on CPU (30+ FPS), robust against varying lighting conditions, invariant to skin tone, and provides precise 3D spatial coordinate tracking.

### 3.3 Technology Stack Selection
| Component | Selected Tool | Rationale |
| :--- | :--- | :--- |
| **Programming Language** | Python 3.11 | High productivity, extensive scientific and vision ecosystem, rapid prototyping |
| **Computer Vision** | OpenCV | Industry-standard real-time image and video processing library |
| **Hand Tracking** | MediaPipe Hands | High-accuracy 21-landmark tracking with sub-millisecond per-frame CPU latency |
| **GUI Framework** | Tkinter | Native cross-platform GUI toolkit included with Python, lightweight and responsive |
| **Automation** | PyAutoGUI | Cross-platform simulation of keyboard shortcuts and mouse events |
| **IDE** | Visual Studio Code | Rich Python development, linting, and debugging environment |
| **Version Control** | GitHub | Distributed version control and collaborative workflow tracking |

---

## 4. Project Planning & Work Schedule

| Week | Milestone / Activity | Deliverables |
| :---: | :--- | :--- |
| **1** | Literature Survey and Project Planning | Research review, state-of-the-art comparison, methodology selection, and roadmap |
| **2** | Requirement Analysis and Software Setup | Functional/non-functional requirements specification, environment configuration, dependency validation |
| **3** | GUI Design | Intuitive, modern Tkinter GUI layout, real-time visual feedback containers, status monitors |
| **4** | Webcam Integration using OpenCV | Thread-safe video capture pipeline, frame rendering into GUI, FPS counter, camera device management |
| **5** | Hand Detection using MediaPipe | 21-landmark extraction, bounding box computation, hand skeleton visualizer |
| **6** | Gesture Recognition Development | Rule-based & geometric gesture classification (Next, Prev, Pointer, Play/Pause, Volume, Pen) |
| **7** | Presentation Controller Integration | PyAutoGUI mapping to PowerPoint / PDF viewer shortcuts, debounce & cooldown engine |
| **8** | Virtual Laser Pointer & Drawing Mode | Real-time on-screen cursor tracking, slide annotation canvas |
| **9** | Testing, Optimization & Benchmarking | Latency profiling, false-positive filtering, CPU/memory optimization |
| **10** | Final Documentation & Presentation | User manual, demonstration video, technical project report, presentation slides |

---

## 5. Objectives
- Develop an end-to-end contactless presentation control system using standard RGB webcams.
- Provide real-time responsiveness (<50ms latency) with high gesture classification accuracy (>95%).
- Create an intuitive graphical interface displaying live feeds, status indicators, and control toggles.
