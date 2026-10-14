# Third-Party Notices and Model Provenance

This document outlines the intellectual property, model assets, open-source libraries, and licenses utilized in **Stant Kamera Oyunları**.

The root [MIT License](LICENSE) applies to the original project source code only. Third-party bundled models, training datasets, and runtime packages are governed separately by their respective licenses as detailed below.

---

## 1. Bundled MediaPipe Perception Task Models

The application bundles three binary perception task models under `app/modeller/`:

| Bundled Artifact Name | SHA256 Checksum | Purpose |
|---|---|---|
| `app/modeller/face_landmarker.task` | `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff` | 478 3D face landmarks & blendshapes |
| `app/modeller/gesture_recognizer.task` | `97952348cf6a6a4915c2ea1496b4b37ebabc50cbbf80571435643c455f2b0482` | 21 hand landmarks & gesture recognition |
| `app/modeller/pose_landmarker_lite.task` | `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a` | 33 full-body pose landmarks (lite model) |

### Licensing & Provenance Status:
- **MediaPipe Software Runtime**: Apache License 2.0 (verified via [github.com/google-ai-edge/mediapipe/blob/master/LICENSE](https://github.com/google-ai-edge/mediapipe/blob/master/LICENSE)). Copyright (c) Google LLC.
- **Artifact-Specific Weight Verification**: *Pending Verification*.
  > [!IMPORTANT]
  > The Apache 2.0 license of the MediaPipe source code repository does not automatically certify the standalone redistribution license or training dataset terms of the compiled binary `.task` neural network weights. Because exact artifact-specific licensing records and dataset provenance are not documented locally within this checkout, artifact verification remains **pending** prior to any future public open-source redistribution.

---

## 2. Quick, Draw! Dataset & Sketch ONNX Model

The application bundles a local sketch recognition neural network under `prototipler/modeller/`:

| Bundled Artifact Name | SHA256 Checksum | Purpose |
|---|---|---|
| `prototipler/modeller/ciz_tanima.onnx` | `e56db75539bd4a5a638f841cb298d0548f7ff9745d846a368f3de5116a738574` | 25-category air-drawing sketch classification |

### Dataset Attribution:
- **Upstream Source**: The Quick, Draw! Dataset by Google Creative Lab ([github.com/googlecreativelab/quickdraw-dataset](https://github.com/googlecreativelab/quickdraw-dataset)).
- **License**: Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).

### Local Provenance Evidence:
- **Download Specification**: Documented in [`prototipler/modeller/ciz_indirme.json`](prototipler/modeller/ciz_indirme.json) (25 category bitmap arrays fetched from Google Cloud Storage `storage.googleapis.com/quickdraw_dataset/full/numpy_bitmap/`).
- **Training Artifact**: Documented in [`prototipler/modeller/ciz_egitim.json`](prototipler/modeller/ciz_egitim.json):
  - Categories: 25 classes (`ciz_kelimeler.json`)
  - Dataset sample size: 20,000 samples per category
  - Model architecture: 166,169 parameters
  - Recorded metrics: validation accuracy `0.91896`, test accuracy `0.92` across 14 training epochs (138.4s training time).

---

## 3. Python Runtime Dependencies

The application relies on the following open-source packages:

| Package | Purpose | License |
|---|---|---|
| `opencv-contrib-python` | Camera I/O, canvas rendering, computer vision algorithms | Apache 2.0 / BSD 3-Clause |
| `mediapipe` | Python bindings for vision perception tasks | Apache 2.0 |
| `numpy` | Matrix transformations and geometry calculations | BSD 3-Clause |
| `pillow` | Typography rendering, image encoding, animated preview export | HPND License |
| `onnxruntime` | CPU inference engine for sketch classification | MIT License |
| `pygame-ce` | Real-time audio engine and frequency synthesizer | LGPL v2.1+ |
| `sounddevice` | Cross-platform audio streaming wrapper | MIT License |
| `pytest` | Acceptance and unit testing framework | MIT License |
