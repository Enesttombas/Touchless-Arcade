import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import cv2
import pytest

PROTOTIP_YOLU = Path.cwd() / "oyunlar"
if str(PROTOTIP_YOLU) not in sys.path:
    sys.path.insert(0, str(PROTOTIP_YOLU))


def test_govde_disindaki_arkaplan_imzaya_karismaz():
    from kimlik_imza import cikar, uzaklik
    poz = _sahte_poz()
    poz.landmarks[0].visibility = 0.0  # Bu kontrol govdeye ait; sac orneklenmez.
    ilk = _sentetik_kare()
    ikinci = ilk.copy()
    ikinci[np.all(ilk == 0, axis=2)] = (0, 0, 255)
    assert uzaklik(cikar(ilk, poz), cikar(ikinci, poz)) < 0.02


@pytest.mark.parametrize("deger", [float("inf"), float("nan")])
def test_gecersiz_omuz_koordinati_imza_uretmez(deger):
    from kimlik_imza import cikar
    poz = _sahte_poz()
    poz.landmarks[11].x = deger
    assert cikar(_sentetik_kare(), poz) is None


def test_cok_koyu_doygun_kumas_kendi_imzasiyla_eslesir():
    from kimlik_imza import cikar, uzaklik
    poz = _sahte_poz()
    kare = _sentetik_kare(torso_bgr=(25, 4, 4))
    assert uzaklik(cikar(kare, poz), cikar(kare, poz)) < 0.02


def _sahte_poz(modifications=None):
    pts = [SimpleNamespace(x=0.5, y=0.5, visibility=0.95) for _ in range(33)]
    pts[0] = SimpleNamespace(x=0.5, y=0.16, visibility=0.95)
    pts[2] = SimpleNamespace(x=0.475, y=0.15, visibility=0.95)
    pts[5] = SimpleNamespace(x=0.525, y=0.15, visibility=0.95)
    pts[11] = SimpleNamespace(x=0.35, y=0.30, visibility=0.95)
    pts[12] = SimpleNamespace(x=0.65, y=0.30, visibility=0.95)
    pts[23] = SimpleNamespace(x=0.38, y=0.75, visibility=0.95)
    pts[24] = SimpleNamespace(x=0.62, y=0.75, visibility=0.95)

    if modifications:
        for idx, val in modifications.items():
            pts[idx] = val

    poz = SimpleNamespace(landmarks=pts, noktalar=pts)
    return poz


def _sentetik_kare(torso_bgr=(0, 255, 0), sac_bgr=None, h=720, w=1280):
    kare = np.zeros((h, w, 3), dtype=np.uint8)

    torso_pts = np.array([
        [int(0.35 * w), int(0.30 * h)],
        [int(0.65 * w), int(0.30 * h)],
        [int(0.62 * w), int(0.75 * h)],
        [int(0.38 * w), int(0.75 * h)],
    ], dtype=np.int32)
    cv2.fillPoly(kare, [torso_pts], torso_bgr)

    if sac_bgr is not None:
        sac_pts = np.array([
            [int(0.45 * w), int(0.05 * h)],
            [int(0.55 * w), int(0.05 * h)],
            [int(0.55 * w), int(0.15 * h)],
            [int(0.45 * w), int(0.15 * h)],
        ], dtype=np.int32)
        cv2.fillPoly(kare, [sac_pts], sac_bgr)

    return kare


def test_ayni_renk_yakin():
    from kimlik_imza import cikar, uzaklik

    poz = _sahte_poz()
    kare1 = _sentetik_kare(torso_bgr=(20, 200, 40), sac_bgr=(30, 30, 30))
    kare2 = _sentetik_kare(torso_bgr=(20, 200, 40), sac_bgr=(30, 30, 30))

    imza1 = cikar(kare1, poz)
    imza2 = cikar(kare2, poz)

    assert imza1 is not None
    assert imza2 is not None
    fark = uzaklik(imza1, imza2)
    assert fark < 0.15


def test_kirmizi_mavi_farkli():
    from kimlik_imza import cikar, uzaklik

    poz = _sahte_poz()
    kare_kirmizi = _sentetik_kare(torso_bgr=(0, 0, 240))
    kare_mavi = _sentetik_kare(torso_bgr=(240, 0, 0))

    imza_k = cikar(kare_kirmizi, poz)
    imza_m = cikar(kare_mavi, poz)

    assert imza_k is not None
    assert imza_m is not None
    fark = uzaklik(imza_k, imza_m)
    assert fark > 0.6


def test_siyah_lacivert_ayrimi():
    from kimlik_imza import cikar, uzaklik

    poz = _sahte_poz()
    kare_siyah = _sentetik_kare(torso_bgr=(0, 0, 0))
    kare_lacivert = _sentetik_kare(torso_bgr=(70, 15, 10))

    imza_s = cikar(kare_siyah, poz)
    imza_l = cikar(kare_lacivert, poz)

    assert imza_s is not None
    assert imza_l is not None
    fark = uzaklik(imza_s, imza_l)
    assert fark > 0.25


def test_sac_farki_etkisi():
    from kimlik_imza import cikar, uzaklik

    poz = _sahte_poz()
    kare_govde_ayni_sac1 = _sentetik_kare(torso_bgr=(0, 180, 180), sac_bgr=(10, 10, 10))
    kare_govde_ayni_sac2 = _sentetik_kare(torso_bgr=(0, 180, 180), sac_bgr=(40, 220, 240))
    kare_govde_ayni_sac1_kopya = _sentetik_kare(torso_bgr=(0, 180, 180), sac_bgr=(10, 10, 10))

    imza_sac1 = cikar(kare_govde_ayni_sac1, poz)
    imza_sac2 = cikar(kare_govde_ayni_sac2, poz)
    imza_sac1_kopya = cikar(kare_govde_ayni_sac1_kopya, poz)

    assert imza_sac1 is not None
    assert imza_sac2 is not None
    assert imza_sac1_kopya is not None

    ayni_uzaklik = uzaklik(imza_sac1, imza_sac1_kopya)
    sac_farkli_uzaklik = uzaklik(imza_sac1, imza_sac2)

    assert sac_farkli_uzaklik > ayni_uzaklik
    assert sac_farkli_uzaklik > 0.05


def test_alan_kucuk_veya_disarida_none():
    from kimlik_imza import cikar

    kare = np.zeros((720, 1280, 3), dtype=np.uint8)

    poz_kucuk = _sahte_poz({
        11: SimpleNamespace(x=0.500, y=0.500, visibility=0.95),
        12: SimpleNamespace(x=0.505, y=0.500, visibility=0.95),
        23: SimpleNamespace(x=0.500, y=0.505, visibility=0.95),
        24: SimpleNamespace(x=0.505, y=0.505, visibility=0.95),
    })
    imza_kucuk = cikar(kare, poz_kucuk)
    assert imza_kucuk is None

    poz_disarida = _sahte_poz({
        11: SimpleNamespace(x=1.35, y=1.30, visibility=0.95),
        12: SimpleNamespace(x=1.65, y=1.30, visibility=0.95),
        23: SimpleNamespace(x=1.38, y=1.75, visibility=0.95),
        24: SimpleNamespace(x=1.62, y=1.75, visibility=0.95),
    })
    imza_disarida = cikar(kare, poz_disarida)
    assert imza_disarida is None


def test_yalniz_olmayan_ogrenmez():
    from kimlik_imza import cikar, uzaklik, Imza

    depo = Imza()
    poz = _sahte_poz()
    kare1 = _sentetik_kare(torso_bgr=(0, 200, 0))
    kare2 = _sentetik_kare(torso_bgr=(200, 0, 0))

    imza1 = cikar(kare1, poz)
    imza2 = cikar(kare2, poz)
    assert imza1 is not None
    assert imza2 is not None

    depo.guncelle(kimlik=1, vektor=imza1, simdi=0.0, yalniz=True)
    ilk_kayitli = depo.al(1)
    assert ilk_kayitli is not None

    depo.guncelle(kimlik=1, vektor=imza2, simdi=1.0, yalniz=False)
    son_kayitli = depo.al(1)

    assert uzaklik(ilk_kayitli, son_kayitli) == pytest.approx(0.0, abs=1e-5)


def test_olgunluk_ve_guvenli_ornek_sayisi():
    from kimlik_imza import cikar, Imza

    depo = Imza()
    poz = _sahte_poz()
    kare = _sentetik_kare(torso_bgr=(100, 150, 50))
    imza = cikar(kare, poz)
    assert imza is not None

    for i in range(9):
        simdi = i * 0.15
        depo.guncelle(kimlik=7, vektor=imza, simdi=simdi, yalniz=True)
        assert depo.olgun(7) is False

    depo.guncelle(kimlik=7, vektor=imza, simdi=9 * 0.15, yalniz=True)
    assert depo.olgun(7) is True


def test_oran_siniri_saniyede_10():
    from kimlik_imza import cikar, uzaklik, Imza

    depo = Imza()
    poz = _sahte_poz()
    kare_yesil = _sentetik_kare(torso_bgr=(0, 255, 0))
    kare_kirmizi = _sentetik_kare(torso_bgr=(0, 0, 255))

    imza_yesil = cikar(kare_yesil, poz)
    imza_kirmizi = cikar(kare_kirmizi, poz)

    depo.guncelle(kimlik=2, vektor=imza_yesil, simdi=0.0, yalniz=True)

    # 10 ornek 0.1 araliklarla (1 sn icinde limit dolmali)
    for i in range(1, 10):
        depo.guncelle(kimlik=2, vektor=imza_yesil, simdi=i * 0.05, yalniz=True)

    durum_oncesi = depo.al(2)

    # Ayni saniye dilimi icinde 11. ve sonrasi hizli guncellemeler reddedilmeli
    for i in range(10, 20):
        depo.guncelle(kimlik=2, vektor=imza_kirmizi, simdi=0.5 + (i * 0.001), yalniz=True)

    durum_sonrasi = depo.al(2)
    assert uzaklik(durum_oncesi, durum_sonrasi) == pytest.approx(0.0, abs=1e-4)


def test_sil_ve_sifirla():
    from kimlik_imza import cikar, Imza

    depo = Imza()
    poz = _sahte_poz()
    kare = _sentetik_kare(torso_bgr=(120, 80, 200))
    imza = cikar(kare, poz)

    depo.guncelle(kimlik=10, vektor=imza, simdi=1.0, yalniz=True)
    depo.guncelle(kimlik=20, vektor=imza, simdi=1.0, yalniz=True)

    assert depo.al(10) is not None
    assert depo.al(20) is not None

    depo.sil(10)
    assert depo.al(10) is None
    assert depo.al(20) is not None

    depo.sifirla()
    assert depo.al(20) is None


def test_parlaklik_dususu_dayanimi():
    from kimlik_imza import cikar, uzaklik

    poz = _sahte_poz()
    kare = _sentetik_kare(torso_bgr=(100, 180, 220), sac_bgr=(50, 40, 30))

    kare_soluk = (kare.astype(np.float32) * 0.7).astype(np.uint8)

    imza_normal = cikar(kare, poz)
    imza_soluk = cikar(kare_soluk, poz)

    assert imza_normal is not None
    assert imza_soluk is not None
    fark = uzaklik(imza_normal, imza_soluk)
    assert fark < 0.3
