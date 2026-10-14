"""Kalabalık stant: arkadan geçenler efekti bozmasın, öndeki her oyuncu ayrı işlensin (kamerasız)."""
import importlib

import numpy as np

from test_ozel import C, algi

H, W = C.Y // 2, C.G // 2


def _maske(*kutular):
    m = np.zeros((H, W), np.float32)
    for x0, y0, x1, y1 in kutular:
        m[y0:y1, x0:x1] = 1.0
    return m


def test_on_plan_arkadan_geceni_atar_oyuncuyu_tutar():
    m = _maske((100, 60, 220, 350), (500, 40, 515, 80))  # öndeki oyuncu + uzaktaki küçük yaya
    s = C.on_plan(m)
    assert s[200, 160] == 1.0 and s[60, 507] == 0.0
    tek = _maske((100, 60, 220, 350))
    assert np.array_equal(C.on_plan(tek), tek)
    iki = _maske((100, 60, 220, 350), (400, 120, 500, 350))  # iki oyuncu yan yana: ikisi de kalır
    assert C.on_plan(iki)[200, 450] == 1.0


def test_zaman_klonu_arkadaki_yayayi_yanki_yapmaz():
    p = importlib.import_module("p_zaman_klonu").Prototip(C.Ses(acik=False))
    m = _maske((100, 60, 220, 350), (500, 40, 515, 80))
    p.maskeci.ver = lambda kare: m
    kare = np.full((C.Y, C.G, 3), 80, np.uint8)
    yumusak, hazir = p._maske_cikar(kare, kare[::2, ::2], 1000.0)
    assert hazir and yumusak[200, 160] > 0.9 and yumusak[60, 507] < 0.05


def test_gorunmez_ucan_kafa_her_kisinin_kafasi_ayri_kalir():
    p = importlib.import_module("p_gorunmez").Prototip(C.Ses(acik=False))
    bos = np.zeros((H, W), np.float32)
    kisiler = _maske((100, 60, 200, 340), (400, 150, 480, 340))  # uzun ve kısa iki oyuncu
    durum = {"m": bos}
    p.maskeci.ver = lambda kare: durum["m"]
    oda = np.full((C.Y, C.G, 3), 80, np.uint8)
    t = 1000.0
    for _ in range(35):  # oda ezberlenir
        t += 0.033
        p.isle(oda.copy(), algi(), t)
    assert p.plaka_hazir
    p.mod = "Uçan Kafa"
    durum["m"] = kisiler
    sahne = oda.copy()
    sahne[np.repeat(np.repeat(kisiler > 0, 2, 0), 2, 1)] = 200
    for _ in range(100):  # pelerin açılır, giriş yazıları söner
        t += 0.033
        cikti = p.isle(sahne.copy(), algi(), t)
    kisa_kafa = cikti[2 * 165, 2 * 440].astype(int)
    kisa_govde = cikti[2 * 300, 2 * 440].astype(int)
    uzun_kafa = cikti[2 * 75, 2 * 150].astype(int)
    assert kisa_kafa.mean() > 170, kisa_kafa  # kısa oyuncunun kafası da görünür
    assert uzun_kafa.mean() > 170, uzun_kafa
    assert kisa_govde.mean() < 150, kisa_govde  # gövde görünmez
