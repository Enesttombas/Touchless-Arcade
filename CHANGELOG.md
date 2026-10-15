# Changelog

All notable changes to the **Stant Kamera Oyunları** project are documented here.

## [v0.2.1] - 2026-10-15

### Fixed
- **Drawing Oracle (`p_ciz_tahmin`) — drawing did not work on the live camera**:
  - When a hand was lost for more than 0.6 s the tracker issued a new hand ID, but the game only accepted the ID captured at round start, so ink never came back and the round froze on "Seni göremiyorum". Player slots now rebind to the returning hand.
  - Pen-down used a 2D finger-length test, so an index finger pointed toward the camera looked "curled". It now measures 3D length (MediaPipe `z`).
  - The hand gate no longer rejects a drawing hand held away from the face (`el_sahip_sart` off for this game).
- **Golden Strike (`p_penalti`) — hard controls, double shots, no goalkeeper**:
  - Ball pickup: any fingertip within 95 px for 0.15 s (was index-only pose, 60 px, 0.3 s).
  - A fast flick or a hand that blurs out mid-flick now counts as a shot; one dropped frame no longer cancels the drawing.
  - The fingertip must leave the ball (140 px) before the next shot can lock, so one gesture fires exactly one shot.
  - The end of the drawn path is now the aim point on the goal plane.
  - New animated neon virtual goalkeeper for solo play: idle sway/hop, a feint to the wrong side, a full-stretch dive and a landing. Saves are decided from the same glove positions that are drawn; measured save rate on 200 random shots is 20–40 %.

### Changed
- Rock Paper Scissors is back in the menu as a dimmed, disabled card (greyed icon + "KAPALI" badge).

## [v0.2.0] - 2026-10-15

### Fixed & Refined
- **Menu Geometry & Footer Clearance**:
  - Recomputed menu card boundaries: cards now occupy `y = 134` to `y = 628` (nominal height 154px, vertical gap 16px).
  - Reserved a clear `>30px` separation between row 3 cards and footer navigation (`y = 672..708`), fully accommodating animated +/-6px vertical bob, +6px hover expansion, and border strokes.
  - Formatted multi-line card titles so both lines strictly fit inside the card container with bottom padding.
  - Added comprehensive geometry unit tests verifying nominal bounds, dynamic animated separation, and interior text constraints (`kabul_prototip/test_motion_bounds.py`).
- **Refined Motion System**:
  - Implemented smooth time-bounded entrance stagger and easing for menu cards.
  - Enhanced touch-free dwell progress with a radial progress ring around the card icon and a bottom progress bar.
  - Added subtle hover feedback pulse and disabled all decorative bobbing when `REDUCED_MOTION=1` or `AZ_HAREKET=1` is set.
- **Headless Synthetic Preview Engine (`tools/render_preview.py`)**:
  - Corrected synthetic hand landmark 9 positioning for menu hover detection, properly triggering hover states and dwell progress in generated snapshots (`docs/media/menu.png`).
  - Resolved the 1.7s transition banner occlusion bug by advancing synthetic time past entrance banners before capturing gameplay visuals.
  - Expanded `demo.gif` to showcase all 9 core experiences + 2 multiplayer sequence games (11 total) with clear caption badges and lightweight palette optimization (<2MB).
  - Added headless verification tests monkeypatching camera and detector instantiation to guarantee offline safety, along with pixel-reproducible menu snapshots.
- **Launch & Setup Scripts**:
  - Updated `BASLAT.bat` to preserve nonzero Python exit codes after user pause.
  - Clarified prerequisite and failure messaging in `KUR.bat`.
  - Updated `.gitignore` to explicitly exclude `.env`, `.env.*` (while allowing `.env.example`), and local capture/runtime recordings.
- **Documentation & Legal Notices**:
  - Corrected GitHub Actions CI badge URL and repository owner to `Enesttombas`.
  - Explicitly labeled `menu.png` and `demo.gif` as synthetic offline renders, not live camera recordings.
  - Clarified controls: `N`/`B` changes menu pages when in menu, but switches games inside active gameplay; `1`-`9` selects current page cards.
  - Documented LAN camera bridge transmission scope and dependency installation behavior in privacy notice.
  - Updated `THIRD_PARTY_NOTICES.md` with SHA256 hashes of all bundled models, MediaPipe Apache 2.0 runtime details, QuickDraw CC BY 4.0 attribution, and clear license scopes.
  - Replaced personal pairing PINs and host-specific IPs in `kurulum/README.md` with neutral operator placeholders.

## [v0.1.0] - 2026-10-13

### Added
- Turnkey arcade suite of 11 standalone camera-based experiences (9 core games + 2 multiplayer sequence games).
- Unified single-window manager with touch-free hover dwell selection, automatic idle recovery, and crash isolation.
- Acceptance test suite.
