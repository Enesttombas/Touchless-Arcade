"""Kör kabul (genel): her prototip için arayüz, dayanıklılık, hız, diske yazmama.

Koşum: PROTOTIP=p_neon_kilic PROTO_DIZIN=... STAND_DIZIN=... <app venv python> -m pytest -q test_prototip.py 
"""
import importlib
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import pytest

PROTO = Path(os.environ.get("PROTO_DIZIN") or Path(__file__).resolve().parent.parent / "oyunlar")
sys.path.insert(0, str(PROTO))
C = importlib.import_module("cekirdek")
AD = os.environ.get("PROTOTIP", "p_neon_kilic")


def yeni():
    return importlib.import_module(AD).Prototip(C.Ses(acik=False))


def kamera(i):
    """Gürültülü, zamanla değişen sahte kamera karesi."""
    k = np.full((C.Y, C.G, 3), 70, np.uint8)
    x = int(200 + 800 * (0.5 + 0.5 * math.sin(i * 0.07)))
    k[200:500, x:x + 160] = (40, 160, 230)
    return k


def senaryo(ad, i):
    t = i * 0.033
    a = C.Algi()
    if ad in ("yuz", "hepsi"):
        a.yuzler = [C.sahte_yuz(0.5 + 0.1 * math.sin(t), 0.4)]
        acik = 0.8 if (i // 15) % 2 else 0.05
        a.blend = [{"jawOpen": acik, "mouthSmileLeft": 0.7 - acik / 2, "mouthSmileRight": 0.7 - acik / 2,
                    "browInnerUp": 0.6, "eyeBlinkLeft": 0.7, "eyeBlinkRight": 0.1, "mouthPucker": 0.2}]
    if ad in ("el", "hepsi"):
        durum = ["isaret", "avuc", "yumruk", "v"][(i // 20) % 4]
        a.eller = [C.sahte_el(0.15 + 0.7 * (0.5 + 0.5 * math.sin(t * 1.7)), 0.3 + 0.3 * abs(math.sin(t)), durum),
                   C.sahte_el(0.5 + 0.3 * math.cos(t), 0.5, "avuc")]
        a.el_taraf = ["Right", "Left"]
        a.jestler = [None, "Open_Palm"]
    if ad in ("poz", "hepsi"):
        a.pozlar = [C.sahte_poz(0.5 + 0.2 * math.sin(t), 0.25)]
    return a


def test_arayuz():
    P = importlib.import_module(AD).Prototip
    assert isinstance(P.AD, str) and P.AD and isinstance(P.ACIKLAMA, str) and P.ACIKLAMA
    assert isinstance(P.IHTIYAC, set) and P.IHTIYAC <= {"yuz", "blend", "el", "poz", "poz?", "yuz2"}  # yuz2: 2 yüz yoksa yarılarda ara
    assert isinstance(getattr(P, "SIRA", 99), int)


@pytest.mark.parametrize("ad", ["bos", "yuz", "el", "poz", "hepsi"])
def test_senaryo_cokmez_bicim_dogru_ve_hizli(ad):
    p, sureler, farkli = yeni(), [], 0
    for i in range(150):
        k = kamera(i)
        giris = k.copy()
        t0 = time.perf_counter()
        out = p.isle(k, senaryo(ad, i), 1000.0 + i * 0.033)
        sureler.append(time.perf_counter() - t0)
        assert isinstance(out, np.ndarray) and out.shape == (C.Y, C.G, 3) and out.dtype == np.uint8
        farkli += int(not np.array_equal(out, giris))
    assert farkli > 0, "prototip hiçbir karede görüntüyü değiştirmedi"
    assert np.median(sureler) * 1000 < 30, f"çizim çok yavaş: {np.median(sureler) * 1000:.1f} ms"


def test_uzun_oturum_zamanlayicilar_cokmez():
    """Tur/sonuç/bekleme döngüleri: 90 sn sahte zaman, kişi gelip gider."""
    p = yeni()
    for i in range(900):
        ad = ["hepsi", "bos", "el", "yuz"][(i // 120) % 4]
        out = p.isle(kamera(i), senaryo(ad, i), 2000.0 + i * 0.1)
        assert out.shape == (C.Y, C.G, 3)


def test_tuslar_cokmez():
    p = yeni()
    p.isle(kamera(0), senaryo("hepsi", 0), 1000.0)
    if hasattr(p, "tus"):
        for k in (ord("e"), ord("c"), ord("r"), 32, 255):
            p.tus(k)
    p.isle(kamera(1), senaryo("hepsi", 1), 1000.1)


def test_diske_yazmaz():
    def tara():  # paralel işçiler başka .py yazabilir; yalnız veri dosyalarına bak
        return {f for f in PROTO.rglob("*") if "__pycache__" not in f.parts and f.suffix != ".py"}
    once = tara()
    p = yeni()
    for i in range(60):
        p.isle(kamera(i), senaryo("hepsi", i), 1000.0 + i * 0.05)
    sonra = tara()
    assert sonra - once <= {PROTO / "hata.txt"}, f"yeni dosya yazıldı: {sonra - once}"
