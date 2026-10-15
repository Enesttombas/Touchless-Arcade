import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "oyunlar"))
import cekirdek as C
from filtre import OneEuro, Ongorucu, NoktaTakip
from oyuncu import OyuncuKapisi
from olcum import Profil


def el(x=.5, y=.4):
    return C.sahte_el(x, y, "avuc")


def test_profil_yuzdelikler():
    p = Profil()
    for n in range(1, 101):
        p.ekle("x", n)
    assert p.ozet()["x"] == pytest.approx((50.5, 95.05))


def test_profil_son_300_ve_asama():
    p = Profil()
    for n in range(400):
        p.ekle("x", n)
    with p.asama("y"):
        pass
    assert len(p.sureler["x"]) == 300 and p.ozet()["y"][0] >= 0


def test_filtre_gurultu():
    f = OneEuro()
    rng = np.random.default_rng(1)
    sonuc = [float(f(500 + rng.uniform(-4, 4), i / 60)) for i in range(600)]
    assert np.percentile(np.abs(np.array(sonuc[100:]) - 500), 95) <= 1.5


def test_filtre_hiz_ve_ongoru():
    f, o = OneEuro(), Ongorucu()
    hatalar, tahmin = [], []
    for i in range(120):
        ham = np.array([i / 60 * 1000, 0])
        suz = f(ham, i / 60)
        if i > 30:
            hatalar.append(ham[0] - suz[0])
            tahmin.append(abs(ham[0] - o.ongor(suz, f.hiz)[0]))
    assert max(hatalar) < 40 and max(tahmin) < 15


def test_ongoru_tavan_ve_durgun():
    o = Ongorucu(50, 35)
    assert np.linalg.norm(o.ongor([0, 0], [30000, 30000])) <= 35.001
    assert np.array_equal(o.ongor([1, 2], [0, 0]), [1, 2])


def test_filtre_degisken_dt_ve_dizi():
    f = OneEuro()
    t = 0
    for i in range(60):
        t += .02 if i % 2 else .06
        a = f(np.full((478, 3), i), t)
        assert np.isfinite(a).all() and a.shape == (478, 3)
    onceki = a.copy()
    assert np.array_equal(f(np.ones((478, 3)), t), onceki)


def test_filtre_gecersiz_girdi():
    with pytest.raises(ValueError):
        OneEuro()([float("nan")], 0)


def test_nokta_kimlige_bagli_ve_temizlik():
    f = NoktaTakip()
    f.suz(1, [0, 0], 0)
    assert np.array_equal(f.suz(2, [100, 100], 1), [100, 100])
    f.temizle({2})
    assert set(f.filtreler) == {2}


def test_kapi_parmak_ucu_ve_kucuk_el():
    for pts in (el(1.1), C.sahte_el(olcek=.01)):
        k = OyuncuKapisi()
        for i in range(31):
            assert not k.suz(C.Algi(eller=[pts]), i / 10).eller


def test_kapi_aday_ve_histerezis():
    k = OyuncuKapisi()
    a = C.Algi(eller=[el()])
    assert not k.suz(a, 0).eller
    assert k.suz(a, .2).adaylar
    out = k.suz(a, .4)
    assert out.el_id and len(out.eller) == 1
    assert k.suz(C.Algi(), .8).tahmini == [("el", out.el_id[0])]
    assert not k.suz(C.Algi(), 1.2).eller


def test_kapi_guven_ve_yan_listeler():
    k = OyuncuKapisi()
    a = C.Algi(eller=[el(.3), el(.7)], jestler=["Open_Palm", "Victory"], el_taraf=["Left", "Right"], el_skor=[.1, .9])
    k.suz(a, 0)
    out = k.suz(a, .4)
    assert len(out.eller) == 1 and out.jestler == ["Victory"] and out.el_taraf == ["Right"]


def test_kapi_yuz_tek_kare():
    k = OyuncuKapisi()
    assert not k.suz(C.Algi(yuzler=[C.sahte_yuz()]), 0).yuzler
    assert not k.suz(C.Algi(), 1.1).yuzler


def test_kapi_durgun_yuz():
    k = OyuncuKapisi()
    a = C.Algi(yuzler=[C.sahte_yuz()], blend=[{}])
    for i in range(101):
        out = k.suz(a, i / 10)
    assert not out.yuzler and ("yuz", "durgun") in out.redler


def test_kapi_hareketli_yuz():
    k = OyuncuKapisi()
    for i in range(101):
        out = k.suz(C.Algi(yuzler=[C.sahte_yuz(.5 + .01 * np.sin(i), .4)]), i / 10)
    assert out.yuzler


def test_kimlik_siralama_ve_kayip():
    k = OyuncuKapisi()
    a = C.Algi(yuzler=[C.sahte_yuz(.3), C.sahte_yuz(.7)])
    k.suz(a, 0)
    ids = k.suz(a, .4).yuz_id
    a.yuzler.reverse()
    assert k.suz(a, .5).yuz_id == ids
    assert k.suz(C.Algi(), .9).yuz_id == ids
    assert not k.suz(C.Algi(), 2).yuz_id
    k.suz(a, 2.1)
    assert not set(k.suz(a, 2.5).yuz_id) & set(ids)


def test_kapi_el_sahibi():
    k = OyuncuKapisi()
    a = C.Algi(yuzler=[C.sahte_yuz(.3, .3, .08)], eller=[el(.3, .3), el(.85, .3)])
    for i in range(10):
        out = k.suz(a, i / 10)
    assert len(out.eller) == 1
    assert out.kisi_id[("el", out.el_id[0])] == out.yuz_id[0]


def test_kapi_aday_kesintisi():
    k = OyuncuKapisi()
    k.suz(C.Algi(eller=[el()]), 0)
    k.suz(C.Algi(eller=[el(1.1)]), .2)
    assert not k.suz(C.Algi(eller=[el()]), .3).eller
