# Contributing Guidelines / Katkı Rehberi

Welcome! This repository hosts interactive camera-based arcade games built for public booth and exhibition environments.

---

## Architecture Principles / Mimari İlkeler

1. **Camera Privacy First**: Live video feeds are processed entirely in memory as numpy frames. Visitor images, audio recordings, or personal telemetry are **never** uploaded to cloud services or saved to disk without explicit administrative debugging configuration.
2. **Deterministic & Frame-Time Based**: All particle systems, transitions, and hover rings use delta-time calculations. No thread sleeps or blocking calls in the render loop.
3. **Interruption-Safe**: Players leaving the frame, hand tracking dropouts, or sudden key presses do not cause exceptions.
4. **Reduced-Motion Support**: Respect accessibility needs. The shared menu, transitions and fingertip trail honor `REDUCED_MOTION=1` or `AZ_HAREKET=1`; individual game effects may still animate. New decorative effects should honor these flags.

---

## Development Setup / Geliştirme Ortamı

1. **Prerequisites**: Python 3.11 on Windows (64-bit).
2. **Environment Setup**: `BASLAT.bat` creates `app\.venv` automatically on first run. Or manually:
   ```cmd
   py -3.11 -m venv app\.venv
   app\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. **Launch**:
   ```cmd
   BASLAT.bat
   ```
4. **Run Acceptance & Unit Tests**:
   ```cmd
   app\.venv\Scripts\python.exe -m pytest -q tests -p no:cacheprovider
   ```
5. **Generate Synthetic Preview**:
   ```cmd
   app\.venv\Scripts\python.exe tools/render_preview.py --quick
   ```

---

## Submitting Pull Requests / Katkıda Bulunma

- Never commit binary `.venv`, `.onnx` cache files, machine-specific absolute paths, or visitor recordings.
- Maintain test integrity: do not relax assertions or skip tests to mask regressions.
- Ensure `compileall` clean checks:
  ```cmd
  app\.venv\Scripts\python.exe -m compileall -q oyunlar stand tools
  ```
