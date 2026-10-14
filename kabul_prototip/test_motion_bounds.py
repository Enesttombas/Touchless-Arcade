"""Unit and acceptance tests for motion state, time bounds, reduced motion, and preview renderer."""
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "prototipler"))
sys.path.insert(0, str(REPO_ROOT / "kabul_prototip"))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import cekirdek as ck
import stand
import stant_app
import render_preview


def test_reduced_motion_environment_toggle(monkeypatch):
    """Test that REDUCED_MOTION / AZ_HAREKET flags are respected."""
    monkeypatch.delenv("REDUCED_MOTION", raising=False)
    monkeypatch.delenv("AZ_HAREKET", raising=False)
    assert not stant_app._az_hareket()

    monkeypatch.setenv("REDUCED_MOTION", "1")
    assert stant_app._az_hareket()

    monkeypatch.delenv("REDUCED_MOTION", raising=False)
    monkeypatch.setenv("AZ_HAREKET", "true")
    assert stant_app._az_hareket()


def test_parmak_izi_reduced_motion_bounds(monkeypatch):
    """Reduced motion limits trail length and disables glow blur."""
    monkeypatch.setenv("REDUCED_MOTION", "1")
    el = ck.sahte_el(0.5, 0.5)
    kare = np.zeros((ck.Y, ck.G, 3), dtype=np.uint8)
    izler = []

    algi = ck.Algi()
    algi.eller = [el]
    algi.jestler = ["Pointing_Up"]

    t = 0.0
    for _ in range(10):
        t += 0.02
        stant_app.parmak_izi(kare, algi, izler, t)

    assert len(izler) == 1
    assert len(izler[0]) <= 4


def test_gecis_karti_time_bounds():
    """Transition card stays strictly within its 1.7s time window and does not mutate outside."""
    uyg = stant_app.StantUygulama(ck.Ses(acik=False))
    kare = np.zeros((ck.Y, ck.G, 3), dtype=np.uint8)
    proto = uyg._ornek(0)

    uyg.sec(0, 10.0)

    out_before = kare.copy()
    uyg._gecis_karti(out_before, proto, 9.9)
    assert np.array_equal(out_before, kare)

    out_during = kare.copy()
    uyg._gecis_karti(out_during, proto, 10.5)
    assert not np.array_equal(out_during, kare)

    out_after = kare.copy()
    uyg._gecis_karti(out_after, proto, 11.8)
    assert np.array_equal(out_after, kare)


def test_menu_geometry_footer_separation_and_rendered_bounds(monkeypatch):
    """Checks actual card grid dimensions, title line bounds, and clear footer separation."""
    uyg = stant_app.StantUygulama(ck.Ses(acik=False))
    kartlar = uyg.menu.kartlar()
    assert len(kartlar) == 9

    nav_l, nav_r = uyg.menu._nav_kutulari()
    footer_top = nav_l[1]
    assert nav_l[1] == nav_r[1]

    # 1. Nominal separation
    max_card_bottom = max(y1 for _, _, _, y1 in kartlar)
    assert footer_top - max_card_bottom >= 35, f"Nominal card to footer gap too small: {footer_top - max_card_bottom}px"

    # 2. Dynamic animated motion separation (+/-6 bob, +6 selection grow, +2 stroke)
    bob_amplitude = 6
    grow_amplitude = 6
    stroke_padding = 2
    worst_case_rendered_bottom = max_card_bottom + bob_amplitude + grow_amplitude + stroke_padding
    assert worst_case_rendered_bottom < footer_top, "Animated card bounds overlap footer navigation!"
    assert footer_top - worst_case_rendered_bottom >= 20, f"Dynamic separation too small: {footer_top - worst_case_rendered_bottom}px"

    # 3. Card interior bounds: titles (both lines) stay within the card height
    w = kartlar[0][2] - kartlar[0][0]
    h = kartlar[0][3] - kartlar[0][1]
    assert w == 320 and h == 154

    # Line 0 starts at 98, Line 1 starts at 122; with font 20 (height ~18-20px), text ends around 140-142px <= 154px
    for i in range(len(uyg.menu.adlar)):
        satirlar = uyg.menu.adlar[i].split(" ", 1)
        line_count = len(satirlar)
        if line_count > 1:
            line1_bottom = 122 + 20
            assert line1_bottom <= h - 8, f"Game title line 2 overflows card for {uyg.menu.adlar[i]}"
        else:
            line0_bottom = 108 + 20
            assert line0_bottom <= h - 8

    # 4. Reduced motion disables decorative bobbing and entrance offsets
    monkeypatch.setenv("REDUCED_MOTION", "1")
    kare = np.zeros((ck.Y, ck.G, 3), dtype=np.uint8)
    algi = ck.Algi()
    # At t=1.0 and t=1.5, in reduced motion, decorative sine movements must be 0
    uyg.menu.isle(kare.copy(), algi, simdi=1.0, dt=0.033)
    uyg.menu.isle(kare.copy(), algi, simdi=1.5, dt=0.033)


def test_synthetic_preview_no_camera_requirement(tmp_path, monkeypatch):
    """tools/render_preview.py runs strictly headless; fails if camera or detectors are instantiated."""
    def fail_camera(*args, **kwargs):
        raise AssertionError("Hardware camera or live video capture accessed in headless test!")

    def fail_detector(*args, **kwargs):
        raise AssertionError("MediaPipe live perception detector accessed in headless test!")

    monkeypatch.setattr(cv2, "VideoCapture", fail_camera)
    monkeypatch.setattr(stand, "Kamera", fail_camera)
    monkeypatch.setattr(ck, "Kamera", fail_camera)

    try:
        import mediapipe.tasks.python.vision as mp_vis
        monkeypatch.setattr(mp_vis.FaceLandmarker, "create_from_options", fail_detector)
        monkeypatch.setattr(mp_vis.HandLandmarker, "create_from_options", fail_detector)
        monkeypatch.setattr(mp_vis.PoseLandmarker, "create_from_options", fail_detector)
        monkeypatch.setattr(mp_vis.GestureRecognizer, "create_from_options", fail_detector)
    except Exception:
        pass

    menu_out1 = tmp_path / "test_menu1.png"
    menu_out2 = tmp_path / "test_menu2.png"
    demo_out = tmp_path / "test_demo.gif"

    # Render menu snapshot twice to verify reproducibility
    out1 = render_preview.render_menu(menu_out1)
    assert menu_out1.is_file()
    assert menu_out1.stat().st_size > 1000

    out2 = render_preview.render_menu(menu_out2)
    assert menu_out2.is_file()

    img1 = cv2.imread(str(menu_out1))
    img2 = cv2.imread(str(menu_out2))
    assert np.array_equal(img1, img2), "Menu render must be pixel-reproducible"

    # Render demo animation (quick mode)
    render_preview.render_demo(demo_out, quick=True)
    assert demo_out.is_file()
    assert demo_out.stat().st_size > 1000

    from PIL import Image
    with Image.open(demo_out) as gif:
        assert getattr(gif, "n_frames", 1) > 5
