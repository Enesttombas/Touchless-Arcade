# Troubleshooting Guide / Sorun Giderme Kılavuzu

Common deployment, hardware, and operational questions for **Stant Kamera Oyunları**.

---

## 1. Camera & Video Input Issues

### Black Screen or "Kamera bulunamadı" (Camera Not Found)
- **Check Device Index**: By default the app opens camera index `0`. If using an external USB webcam, specify the index via environment variable:
  ```cmd
  set KAMERA=1
  BASLAT.bat
  ```
- **Check Windows Privacy Settings**: Ensure camera access is allowed for desktop applications under **Windows Settings -> Privacy & Security -> Camera**.
- **Close Competing Applications**: Windows webcams cannot be shared concurrently across multiple processes (Teams, Zoom, Camera app, browser).

### Using the Optional LAN Camera Bridge
- If using an operator-configured secondary machine running `kamera_kopru.py`:
  ```cmd
  set KAMERA=tcp://<BOOTH_HOST_IP>:8090
  BASLAT.bat
  ```
- Ensure both machines are on the same local network subnet and firewall port 8090 is open.

---

## 2. Performance & Responsiveness

### Lower Frame Rate or High CPU Load
- **Lighting**: Vision tracking algorithms require clear silhouettes and minimal motion blur. Ensure the booth area has adequate front lighting.
- **Enable Reduced Motion**:
  ```cmd
  set REDUCED_MOTION=1
  BASLAT.bat
  ```
  *(or `set AZ_HAREKET=1`)*. This disables decorative particles and animations in the shared shell.
- **Background Processes**: Close background browsers, heavy IDEs, or indexing services.

---

## 3. Controls & Navigation

### How to Return to the Menu
- **Touch-Free (Recommended)**: Raise an open palm to the bottom-left corner of the screen for 3 seconds. A yellow circular countdown will fill and return to the main menu.
- **Keyboard Shortcut**: Press `M` to immediately return to the main menu.
- **Idle Timeout**: If no person is detected in the frame for 40 seconds (and no active game is in progress), the app automatically returns to the menu.

### Navigation Keys Summary
| Context | Key | Action |
|---|---|---|
| **Anywhere** | `Q` or `Esc` | Exit application |
| **Anywhere** | `F` | Toggle Fullscreen |
| **Main Menu** | `1`–`9` | Select card on the **current** page |
| **Main Menu** | `N` / `B` | Next / Previous menu page |
| **In-Game** | `M` | Return to main menu |
| **In-Game** | `N` / `B` | Switch to Next / Previous game |
| **In-Game** | `1`–`9` | Jump directly to game index |
| **Sequence Games** | `3`, `4`, `5`, Space | Switch player count or game mode |

---

## 4. Setup & Model Errors

### Missing `.venv` or Import Errors
- Re-run the clean installation script from the project root:
  ```cmd
  KUR.bat
  ```
- Verify that Python **3.11** is installed and accessible in `PATH`.
- Verify that bundled task models exist under `app/modeller/`:
  - `face_landmarker.task`
  - `gesture_recognizer.task`
  - `pose_landmarker_lite.task`
  and sketch ONNX classifier under `prototipler/modeller/ciz_tanima.onnx`.
