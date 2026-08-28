# Week 3: GUI Design

## 1. Objectives
Design and implement an aesthetic, responsive Graphical User Interface (GUI) in Tkinter that serves as the command center for the Gesture-Based Presentation Control system.

---

## 2. Design Aesthetics & Visual Tokens

### 2.1 Color Palette
- **Background Dark**: `#181825` (Deep Slate Charcoal)
- **Card / Surface Background**: `#1e1e2e` (Dark Card Background)
- **Border / Divider**: `#313244` (Subtle dark separator)
- **Primary Accent**: `#89b4fa` (Soft Modern Blue)
- **Success / Active**: `#a6e3a1` (Vibrant Mint Green)
- **Warning / Accent 2**: `#f9e2af` (Warm Amber Yellow)
- **Danger / Stop**: `#f38ba8` (Coral Red)
- **Text Primary**: `#cdd6f4` (Crisp Off-White)
- **Text Secondary**: `#a6adc8` (Subtle Muted Gray)

### 2.2 Typography
- **Header Title**: Segoe UI / Helvetica, 18pt, Bold
- **Section Headings**: Segoe UI / Helvetica, 12pt, Bold
- **Body & Metrics**: Segoe UI / Consolas, 10pt, Regular / Medium

---

## 3. UI Layout Architecture

The GUI layout is organized into 3 main functional zones:
```
+-----------------------------------------------------------------------------------------+
| [LOGO / ICON]  GESTURE-BASED PRESENTATION CONTROLLER               [FPS: 30.0] [STATUS] |
+-------------------------------------------------------+---------------------------------+
|                                                       |  CONTROLS & SETTINGS            |
|                                                       |  - Camera Device: [ 0 | v ]     |
|                                                       |  - Resolution:    [ 720p | v ]  |
|               LIVE WEBCAM FEED DISPLAY                |  [ Start Camera ] [ Mirror: ON ]|
|                    (Canvas / Label)                   |  [ Snapshot ]     [ Fullscreen ]|
|                                                       +---------------------------------+
|                                                       |  GESTURE CHEAT SHEET            |
|                                                       |  👉 Point Right : Next Slide   |
|                                                       |  👈 Point Left  : Prev Slide   |
|                                                       |  ✋ Open Palm   : Laser Pointer |
|                                                       |  ✊ Fist        : Pause Control |
+-------------------------------------------------------+---------------------------------+
| SYSTEM LOGS / STATUS: [Ready] Camera initialized at 1280x720 (FPS: 30)                  |
+-----------------------------------------------------------------------------------------+
```

---

## 4. Key UI Components
1. **Header Banner**: Project title, team member credits, and live system status chips.
2. **Video Viewport**: High-performance canvas rendering real-time frames with aspect ratio preservation.
3. **Control Deck**: Toggle buttons with dynamic color transitions (e.g. Green "Start" -> Red "Stop"), dropdown selectors for camera index and resolution, and mirror toggle.
4. **Gesture Guide Panel**: Visual reference guide detailing upcoming gesture mappings and recognition states.
5. **Activity Log Viewer**: Real-time scrolling event log documenting camera lifecycle events and status updates.
