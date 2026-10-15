"""Kör kabul (oyuna özel): PROTOTIP ortam değişkenine göre ilgili sözleşme koşulur, diğerleri atlanır."""
import importlib
import os
import sys
from pathlib import Path

import numpy as np
import pytest

PROTO = Path(os.environ.get("PROTO_DIZIN") or Path(__file__).resolve().parent.parent / "oyunlar")
sys.path.insert(0, str(PROTO))
C = importlib.import_module("cekirdek")
AD = os.environ.get("PROTOTIP", "p_stant")
KARE = lambda: np.full((C.Y, C.G, 3), 80, np.uint8)  # noqa: E731


def sadece(ad):
    return pytest.mark.skipif(AD != ad, reason=f"yalnız {ad}")


def yeni():
    return importlib.import_module(AD).Prototip(C.Ses(acik=False))


def algi(eller=(), jestler=None, yuz=False, blend=None, poz=False):
    a = C.Algi()
    a.eller = list(eller)
    a.el_taraf = ["Right", "Left"][:len(a.eller)]
    a.jestler = list(jestler) if jestler is not None else [None] * len(a.eller)
    if yuz:
        a.yuzler = [C.sahte_yuz(0.5, 0.45)]
        a.blend = [dict(blend or {})]
    if poz:
        a.pozlar = [C.sahte_poz(0.5, 0.25)]
    return a


def baslat_avuc(p, t):
    """Açık avuç 1.5 sn tutulunca oyun başlar."""
    for i in range(50):
        p.isle(KARE(), algi([C.sahte_el(0.5, 0.5, "avuc")], ["Open_Palm"]), t + i * 0.033)
    return t + 50 * 0.033


@sadece("p_neon_kilic")
def test_kilic_hizli_kesis_skor_verir_tur_biter():
    p = yeni()
    assert p.durum == "bekle" and p.skor == 0
    t = baslat_avuc(p, 1000.0)
    assert p.durum == "oyun"
    hedef = None
    for i in range(120):  # ilk nesne gelene kadar bekle
        t += 0.033
        p.isle(KARE(), algi(), t)
        normal = [m for m in p.meyveler if not getattr(m, "bomba", False) and 100 < m.x < C.G - 100]
        if normal:
            hedef = normal[0]
            break
    assert hedef is not None, "4 sn içinde kesilecek nesne çıkmadı"
    for dx in (-160, 160):  # parmak ucu nesnenin üstünden hızla geçer (piksel koordinat)
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el((hedef.x + dx) / C.G, hedef.y / C.Y, "isaret")]), t)
    assert p.skor > 0
    for _ in range(40 * 31):  # 30 sn tur biter
        t += 0.033
        p.isle(KARE(), algi(), t)
        if p.durum == "sonuc":
            break
    assert p.durum == "sonuc"


@sadece("p_kafa_topu")
def test_kafa_topu_alinda_seker_kafa_gidince_biter():
    p = yeni()
    assert p.durum == "bekle" and p.skor == 0
    t = 1000.0
    for _ in range(200):  # yüz sabit: top alına düşer, seker
        t += 0.033
        p.isle(KARE(), algi(yuz=True), t)
        if p.skor > 0:
            break
    assert p.durum == "oyun" and p.skor > 0
    assert hasattr(p.top, "x") and hasattr(p.top, "y")
    for _ in range(400):  # kafa kaybolur: top yere düşer, oyun biter
        t += 0.033
        p.isle(KARE(), algi(), t)
        if p.durum == "sonuc":
            break
    assert p.durum == "sonuc"


@sadece("p_gulmeme")
def test_gulmeme_ilk_gulen_kaybeder():
    p = yeni()
    assert p.durum == "bekle"

    def iki(gulen=None):
        a = C.Algi()
        a.yuzler = [C.sahte_yuz(0.7, 0.45, 0.12), C.sahte_yuz(0.3, 0.45, 0.12)]  # sıra karışık verilir
        a.blend = [{"mouthSmileLeft": 0.05, "mouthSmileRight": 0.05}, {"mouthSmileLeft": 0.05, "mouthSmileRight": 0.05}]
        if gulen is not None:
            a.blend[gulen] = {"mouthSmileLeft": 0.9, "mouthSmileRight": 0.9}
        return a
    t = 1000.0
    for _ in range(200):  # iki kişi gelir, geri sayım, oyun
        t += 0.033
        p.isle(KARE(), iki(), t)
        if p.durum == "oyun":
            break
    assert p.durum == "oyun"
    for _ in range(30):  # ekranın solundaki kişi (x=0.3, listede 2.) güler
        t += 0.033
        p.isle(KARE(), iki(gulen=1), t)
        if p.durum == "sonuc":
            break
    assert p.durum == "sonuc" and p.kaybeden == "sol"


@sadece("p_ucan_kafa")
def test_ucan_kafa_agiz_acinca_ziplar_ve_yanar():
    p = yeni()
    assert p.durum == "bekle"
    t = 1000.0
    for i in range(30):
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={"jawOpen": 0.6}), t)
    assert p.durum == "oyun"
    y0 = p.kus_y
    for i in range(6):
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={"jawOpen": 0.0 if i % 3 else 0.7}), t)
    for _ in range(3):  # ağız kapalı: düşer
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={"jawOpen": 0.0}), t)
    assert p.kus_y != y0
    for _ in range(600):  # hiç zıplamazsa yere düşüp oyun biter
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={"jawOpen": 0.0}), t)
        if p.durum == "sonuc":
            break
    assert p.durum == "sonuc"


@sadece("p_buyu")
def test_enerji_iki_elle_dolar_ve_atis_yapar():
    p = yeni()
    assert p.enerji == 0 and p.atis == 0
    t = 1000.0
    for i in range(60):  # iki el yakın, karşılıklı: dolum
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(0.44, 0.5, "avuc"), C.sahte_el(0.56, 0.5, "avuc")]), t)
    assert p.enerji > 0.5
    for i in range(10):  # eller hızla açılır: atış
        t += 0.033
        d = 0.06 + 0.04 * i
        p.isle(KARE(), algi([C.sahte_el(0.5 - d, 0.5, "avuc"), C.sahte_el(0.5 + d, 0.5, "avuc")]), t)
    assert p.atis >= 1


@sadece("p_hava_davulu")
def test_davul_asagi_vurus_sayilir():
    p = yeni()
    assert p.vurus == 0 and len(p.pedler) >= 4
    ped = p.pedler[0]  # .x .y piksel merkez, .r yarıçap
    t = 1000.0
    for i in range(8):  # parmak ucu yukarıdan pede hızla iner
        t += 0.033
        y = (ped.y - 160 + i * 40) / C.Y
        p.isle(KARE(), algi([C.sahte_el(ped.x / C.G, min(y, 0.98), "isaret")]), t)
    assert p.vurus >= 1
    v = p.vurus
    for i in range(30):  # pedde dururken tekrar tekrar çalmaz
        t += 0.033
        p.isle(KARE(), algi([C.sahte_el(ped.x / C.G, ped.y / C.Y, "isaret")]), t)
    assert p.vurus == v


@sadece("p_ifade_oyunu")
def test_ifade_taklidi_puan_verir():
    p = yeni()
    t = 1000.0
    for i in range(20):  # yüz gelince oyun başlar
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={}), t)
    assert p.durum == "oyun" and p.hedef in p.IFADELER
    s0 = p.skor
    for i in range(45):  # hedef ifadenin blendshape'leri tam yapılır
        t += 0.033
        p.isle(KARE(), algi(yuz=True, blend={k: 0.95 for k in p.IFADELER[p.hedef]} if p.durum == "oyun" else {}), t)
        if p.skor > s0:
            break
    assert p.skor > s0
