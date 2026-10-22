<p align="center"><img src="docs/media/banner.png" width="100%" alt="Touchless Arcade: nine camera games you play with one finger, no controller or touch screen"></p>
<p align="center"><b>English</b> · <a href="README.tr.md">Türkçe</a></p>

<p align="center">
<a href="https://github.com/Enesttombas/Touchless-Arcade/actions/workflows/ci.yml"><img src="https://github.com/Enesttombas/Touchless-Arcade/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<img src="https://img.shields.io/badge/Python-3.11-blue.svg" alt="Python 3.11">
<img src="https://img.shields.io/badge/Platform-Windows-lightgrey.svg" alt="Platform: Windows">
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"></a>
</p>

Touchless Arcade is a set of nine camera games you play with your finger, face or body in front of a mirrored live camera. I built it for the R&D Club booth at Nişantaşı University's club week, to stop people walking past and give them a few minutes of fun.

<p align="center"><a href="https://github.com/Enesttombas/Touchless-Arcade/releases/latest/download/Touchless-Arcade-Windows.zip"><img src="docs/media/indir-dugmesi.png" alt="Download: Windows ZIP" width="420"></a></p>
<p align="center">Download · right-click the ZIP, <b>Extract All</b> · double-click <code>BASLAT.bat</code></p>

<p align="center"><a href="docs/media/canli/neon-kilic.mp4"><img src="docs/media/canli/neon-kilic.gif" width="720" alt="Two players slicing in Neon Kılıç at the university booth"></a></p>
<p align="center"><sub>Recorded with real players at the booth. Click for the full video.</sub></p>

## What it does

**Play with one finger.** Raise your index finger and the game follows it. Hold it over a menu card for one second to start a game, so a booth needs no keyboard or mouse.

<p align="center"><a href="docs/media/canli/kanat-rotasi.mp4"><img src="docs/media/canli/kanat-rotasi.gif" height="420" alt="Kanat Rotası: a player steers the bird with a fingertip"></a></p>

**Two players at once.** Duels track two people in the same frame: in Gülme Düellosu the first to laugh loses, and in Neon Kılıç two blades slice together. AR Maskeler gives everyone in the frame their own mask.

<p align="center"><a href="docs/media/canli/gulme-duellosu.mp4"><img src="docs/media/canli/gulme-duellosu.gif" width="600" alt="Gülme Düellosu: two players face off, first to laugh loses"></a></p>

**Nine games, one menu.** Every game shares the same camera and perception thread, so switching games is instant.

| | Game | How you play |
|---|---|---|
| 1 | **Neon Kılıç** | Your index finger is a blade. Slice in **Fruit** or **Meme** mode. |
| 2 | **Gülme Düellosu** | Two players face to face: the first to laugh or blink loses. |
| 3 | **AR Maskeler** | Real-time 3D masks and filters on every face. |
| 4 | **Kanat Rotası** | The height of your finger flies the bird between the pipes. |
| 5 | **Bilgi Yağmuru** | Run with your body under the falling correct answer. |
| 6 | **Silahşor Düellosu** | When "ATEŞ!" appears, the fastest raised hand wins. |
| 7 | **Hayalet Klonlar** | Time clones and an invisibility cloak. |
| 8 | **Altın Vuruş** | Put your finger on the ball and draw the shot. The neon keeper fakes a dive. |
| 9 | **Çizim Kâhini** | Draw in the air; a small neural net guesses what it is. |

*Taş Kağıt Makas* stays in the menu as a faded, disabled card.

<p align="center"><img src="docs/media/oyun-turu.gif" width="600" alt="A short tour of the nine games rendered with synthetic input"></p>
<p align="center"><sub>Rendered by the game's own engine from synthetic input, not a live camera recording.</sub></p>

## How it works

<p align="center"><img src="docs/media/architecture.svg" width="860" alt="Architecture: camera to AlgiIscisi thread to Algilayici (MediaPipe), then OyuncuKapisi, StantUygulama and the nine p_*.py games, drawn to a 1280x720 window"></p>

- `cekirdek.Kamera()` opens a USB camera, or a `tcp://` stream from `kamera_kopru.py` when the camera sits on a second laptop.
- `AlgiIscisi` in `stant_app.py` runs `Algilayici` from `cekirdek.py` on its own thread: MediaPipe face, gesture and pose models (`app/modeller/*.task`).
- `OyuncuKapisi` (`oyuncu.py`) decides who is playing. `StantUygulama` and `AnaMenu` own the menu, dwell selection and crash isolation: a game that crashes three times sends you back to the menu.
- Each game in `oyunlar/p_*.py` exposes `Prototip.isle(kare, algi, t)` and draws with the shared `stand/stand.py`. Çizim Kâhini adds `ciz_tanima.onnx`, a sketch classifier trained on Quick, Draw! data.

More detail: [architecture](docs/architecture.md) · [troubleshooting](docs/troubleshooting.md).

## Numbers

<p align="center"><img src="docs/media/numbers.svg" width="860" alt="261 tests pass with 29 skipped, 9 playable games, 185.2 MB Windows ZIP, 18.6 MB of local models"></p>

Measured on 2026-10-22 (Windows 11, Python 3.11): `python -m pytest -q tests` exited 0 with 261 passed and 29 skipped in 478 s. The package size is the GitHub release asset; model sizes are the files in `app/modeller/` and `oyunlar/modeller/`. Raw data: [`docs/media/data/`](docs/media/data/).

## Quick start

1. **[Download the ZIP](https://github.com/Enesttombas/Touchless-Arcade/releases/latest/download/Touchless-Arcade-Windows.zip)** (185 MB).
2. Right-click it and choose **Extract All**.
3. Double-click **`BASLAT.bat`** in the extracted folder.

The package carries its own portable Python and every library, so nothing is installed and nothing is downloaded on first launch. You need Windows 10 or 11 (64-bit) and a USB or built-in camera.

If you downloaded the source instead (**Code → Download ZIP**), `BASLAT.bat` installs what it needs on first launch (internet required, 3 to 5 minutes).

> If Windows shows an "unknown publisher" warning, choose **More info → Run anyway**. If the camera does not open: Settings → Privacy → Camera → **Let desktop apps access your camera**.

## Usage

Raise your index finger with your **palm facing the camera** and the other fingers closed. Pointing the fingertip straight at the lens makes the finger look short and tracking can drop.

<p align="center"><img src="docs/media/parmak-durusu.gif" width="600" alt="Correct finger pose: index finger up, palm facing the camera"></p>

Hold your hand over a card for 1 s to pick a game. Hold an open palm in the bottom-left corner for 3 s to go back to the menu. Keyboard: `1` to `9` select, `M` menu, `F` full screen, `Q` quit; the shortcuts are always shown at the bottom left.

Development:

```cmd
app\.venv\Scripts\python.exe -m pytest -q tests
app\.venv\Scripts\python.exe tools\render_preview.py --quick
```

Code layout: `oyunlar/` (games and menu), `stand/` (shared drawing and effects), `app/modeller/` (MediaPipe models), `tests/`.

## Limits

- Windows only. The ZIP and `BASLAT.bat` are built and tested for Windows 10/11 64-bit.
- The release is unsigned, so Windows SmartScreen warns on first launch.
- Tracking depends on light and camera angle. Back light and a fingertip pointed at the lens are the usual failures; see [troubleshooting](docs/troubleshooting.md).
- The in-game text is Turkish.

## License

[MIT](LICENSE). Third-party model licenses: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Changes: [CHANGELOG.md](CHANGELOG.md).

The previous README is kept in [docs/NOTES.md](docs/NOTES.md).
