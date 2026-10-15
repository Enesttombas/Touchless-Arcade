# System Architecture / Sistem Mimarisi

Technical architecture overview of the Standalone Camera Arcade (**Stant Kamera Oyunları**).

---

## 1. High-Level Architecture

The project is structured into three primary layers:
1. **Perception Pipeline (`cekirdek.py`, `oyuncu.py`)**: Real-time vision analysis using Google MediaPipe Tasks (Face, Gesture, Pose) and ONNX Runtime running 100% locally on CPU.
2. **Game Core & State Machines (`oyunlar/p_*.py`)**: 9 self-contained arcade games adhering to the common prototype interface (`Prototip.isle`, `Prototip.tus`, `Prototip.baslat`).
3. **Application Shell (`oyunlar/stant_app.py`)**: Unified single-window manager with touch-free menu navigation, idle detection, crash recovery, and seamless scene transitions.

```
+-------------------------------------------------------------------+
|               Camera Stream (Local USB / Optional TCP LAN)        |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                   Perception Engine (MediaPipe / ONNX)            |
|   - Face Landmarker & Blendshapes                                 |
|   - Hand Landmarker & Gesture Recognizer                          |
|   - Pose Landmarker Lite                                          |
|   - QuickDraw ONNX Sketch Classifier                              |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|               Multi-Player Gate & Tracker (`oyuncu.py`)           |
|   - Spatial tracking, entry confidence, lost player timeout       |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|               Unified Shell (`oyunlar/stant_app.py`)              |
|   - Main Menu (single screen, touch-free hover dwell)             |
|   - Active Game Runner (9 games)                                   |
|   - Transition Banners & Crash Isolation (3 crash -> safe retreat)|
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|               Render Canvas (1280x720 BGR)                        |
|   - Procedural Neon & Particle Glow                               |
|   - PIL Turkish TTF Typography & Segoe UI Emoji Support           |
+-------------------------------------------------------------------+
```

---

## 2. Component Roles

### 2.1 Unified Shell (`stant_app.py`)
- **Main Menu (`AnaMenu`)**: Shows every game on one screen (3x3 grid, or 5 columns when there are more than 9 cards) with procedural icons and Turkish titles. Dwell selection completes in 1.0s (`SECIM_SN`).
- **Safety Margin Geometry**: Cards start at `y = 134` and always keep a clear margin above the bottom edge, even during vertical oscillation (+/-6px) and hover expansion (+6px).
- **Reduced Motion Support (`REDUCED_MOTION=1` / `AZ_HAREKET=1`)**: Disables card bobbing, entrance translation, pulse glows, and truncates fingertip particle trails to preserve comfort and performance.

### 2.2 Optional LAN Camera Bridge (`kamera_kopru.py`)
- Designed for booth configurations where the camera is physically connected to a secondary machine (e.g. a second laptop) and relayed to the main display workstation over a dedicated local Ethernet TCP socket (`tcp://<IP>:<PORT>`).
- Operates single-frame low-latency buffering with zero disk writes.

### 2.3 Headless Preview Engine (`tools/render_preview.py`)
- Enables synthetic offline rendering of `docs/media/menu.png` and `docs/media/demo.gif` (README uses `docs/media/oyun-turu.gif`, made with `tools/oyun_turu.py`) without requiring a physical camera or MediaPipe initialization.
- The menu snapshot is pixel-reproducible. The demo uses fixed synthetic times and inputs, while game randomness can vary. Acceptance tests guard against camera and detector initialization.
