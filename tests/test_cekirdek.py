"""Kör kabul: oyunlar/cekirdek.py ve gezgin.py sözleşmesi. Koşum: <app venv python> -m pytest -q <bu dosya>"""
import importlib
import os
import sys
from pathlib import Path

import numpy as np
import pytest

PROTO = Path(os.environ.get("PROTO_DIZIN") or Path(__file__).resolve().parent.parent / "oyunlar")
sys.path.insert(0, str(PROTO))
C = importlib.import_module("cekirdek")


@pytest.mark.parametrize("ad", ["kick", "snare", "hihat", "clap", "pop", "ding", "bonk", "woosh", "basari", "zap",
                                "nota60", "nota72", "bilinmeyen"])
def test_sentez_sesleri_sonlu_ve_sinirli(ad):
    d = C.sentez(ad, 44100)
    assert d.ndim == 1 and 400 < len(d) < 44100 * 2
    assert np.isfinite(d).all() and np.abs(d).max() <= 1.0 + 1e-6 and np.abs(d).max() > 0.01


def test_ses_kapaliyken_sessiz_gecer():
    s = C.Ses(acik=False)
    s.cal("kick")
    s.cal("yok_boyle_ses")


def test_sahte_el_durumlari_stand_el_durumu_ile_uyumlu():
    assert C.el_durumu(C.sahte_el(0.5, 0.5, "isaret")) == "ciz"
    assert C.el_durumu(C.sahte_el(0.5, 0.5, "avuc")) == "sil"
    assert C.el_durumu(C.sahte_el(0.5, 0.5, "v")) == "kalk"
    assert C.el_durumu(C.sahte_el(0.5, 0.5, "yumruk")) == "yok"
    el = C.sahte_el(0.3, 0.4, "isaret")
    assert len(el) == 21 and abs(el[8].x - 0.3) < 0.05 and abs(el[8].y - 0.4) < 0.05


def test_sahte_yuz_ve_poz_boyutlari():
    assert len(C.sahte_yuz()) == 478
    p = C.sahte_poz(0.5, 0.3)
    assert len(p) == 33 and p[0].visibility > 0.5 and p[15].visibility > 0.5


def test_gorsel_yardimcilar_kenarda_cokmez():
    img = np.zeros((C.Y, C.G, 3), np.uint8)
    C.panel(img, -50, -50, 200, 100, kenar=C.SARI)
    C.panel(img, C.G - 10, C.Y - 10, C.G + 300, C.Y + 300)
    C.halka(img, 5, 5, 0.7)
    C.baslik(img, "Başlık ğüşİ", "alt satır")
    k = np.zeros_like(img)
    k[300:310, 300:600] = 255
    C.parilti(img, k)
    assert img.any() and img.dtype == np.uint8 and img.shape == (C.Y, C.G, 3)


def test_algi_varsayilan_bos():
    a = C.Algi()
    assert a.yuzler == [] and a.blend == [] and a.eller == [] and a.el_taraf == [] and a.jestler == [] \
        and a.pozlar == []


def test_algilayici_gercek_modelle_bos_karede_calisir():
    alg = C.Algilayici()
    kare = np.full((C.Y, C.G, 3), 90, np.uint8)
    a = alg.algila(kare, {"yuz", "blend", "el", "poz"})
    assert isinstance(a, C.Algi) and a.yuzler == [] and a.eller == []
    a = alg.algila(kare, set())
    assert a.yuzler == [] and a.pozlar == []


def test_gezgin_prototipleri_kesfeder_ve_arayuz_tam():
    g = importlib.import_module("gezgin")
    liste = g.kesfet()
    adlar = [m.__name__ for m in liste]
    assert "p_penalti" in adlar and "p_ciz_tahmin" in adlar
    for m in liste:
        P = m.Prototip
        assert isinstance(P.AD, str) and P.AD and isinstance(P.ACIKLAMA, str)
        assert isinstance(P.IHTIYAC, set) and P.IHTIYAC <= {"yuz", "yuz2", "blend", "el", "poz", "poz?", "kalabalik"}


def test_gezgin_onizleme_kontakt_uretir(tmp_path):
    import cv2
    g = importlib.import_module("gezgin")
    foto = tmp_path / "foto.jpg"
    cv2.imwrite(str(foto), np.full((720, 1280, 3), 100, np.uint8))
    g.onizleme(str(foto), str(tmp_path / "cikti"), kare_sayisi=8)
    pngler = {p.name for p in (tmp_path / "cikti").glob("*.png")}
    assert "kontakt.png" in pngler and "p_penalti.png" in pngler
