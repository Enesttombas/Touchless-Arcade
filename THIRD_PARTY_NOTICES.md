# Third-Party Notices and Model Provenance

This document outlines the intellectual property, model assets, open-source libraries, and licenses utilized in **Stant Kamera Oyunları**.

The root [MIT License](LICENSE) applies to the original project source code and the locally trained sketch ONNX artifact. Third-party bundled models, training datasets, and runtime packages are governed separately by their respective licenses as detailed below.

---

## 1. Bundled MediaPipe Perception Task Models

The application bundles three binary perception task models under `app/modeller/`:

| Bundled Artifact Name | SHA256 Checksum | Purpose |
|---|---|---|
| `app/modeller/face_landmarker.task` | `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff` | 478 3D face landmarks & blendshapes |
| `app/modeller/gesture_recognizer.task` | `97952348cf6a6a4915c2ea1496b4b37ebabc50cbbf80571435643c455f2b0482` | 21 hand landmarks & gesture recognition |
| `app/modeller/pose_landmarker_lite.task` | `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a` | 33 full-body pose landmarks (lite model) |

### Licensing & Provenance Status (verified 2026-10-15)
- **Runtime and bundled task models**: Apache License 2.0; Copyright Google LLC. Full license: [`licenses/Apache-2.0.txt`](licenses/Apache-2.0.txt). The original project MIT license does not replace these terms.
- **Publisher statement**: [MediaPipe maintainer response, 2026-10-05](https://github.com/google-ai-edge/mediapipe/issues/6355) confirms the source and models are Apache 2.0 unless otherwise noted. Official [Face Mesh V2 model card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Face%20Mesh%20V2.pdf) and [BlazePose GHUM 3D model card](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf) also identify Apache 2.0.
- **Versioned publisher artifacts**: Each local file's MD5 matches the ETag supplied by the following official Google Cloud Storage object; local SHA256 pins are listed above. These are version `1`, not moving `latest` links.

| Artifact | Official versioned download | Matching MD5 |
|---|---|---|
| Face Landmarker | [float16/1](https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task) | `b0e7274907a1644404fef66b28dd6d85` |
| Gesture Recognizer | [float16/1](https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task) | `4dbf485c473207651100a1895343f35a` |
| Pose Landmarker Lite | [float16/1](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task) | `04a75ddf7c811ac7a1a4523266dd7d88` |

The bundled task files are unmodified. Retain these attribution and license notices when redistributing them. Publisher training data and build attestations are separate from this license verification; this record does not claim a signed model SBOM.

---

## 2. Quick, Draw! Dataset & Sketch ONNX Model

The application bundles a local sketch recognition neural network under `prototipler/modeller/`:

| Bundled Artifact Name | SHA256 Checksum | Purpose |
|---|---|---|
| `prototipler/modeller/ciz_tanima.onnx` | `e56db75539bd4a5a638f841cb298d0548f7ff9745d846a368f3de5116a738574` | 25-category air-drawing sketch classification |

The locally trained `ciz_tanima.onnx` artifact is released under the project MIT license, with the following training-data attribution retained.

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
