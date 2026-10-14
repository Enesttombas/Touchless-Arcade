from types import SimpleNamespace as N

import numpy as np

import stand as S


def _el(acik):
    """Bilek (0.5,0.9), orta taban (0.5,0.8); açık parmak ucu bileğe 0.2, kıvrık 0.1 uzak (el boyu 0.1)."""
    lm = [N(x=0.5, y=0.9) for _ in range(21)]
    lm[9] = N(x=0.5, y=0.8)
    for uc, a in zip((8, 12, 16, 20), acik):
        lm[uc] = N(x=0.5, y=0.9 - (0.2 if a else 0.1))
    return lm


def test_el_durumu():
    assert S.el_durumu(_el([1, 0, 0, 0])) == "ciz"
    assert S.el_durumu(_el([1, 1, 0, 0])) == "kalk"
    assert S.el_durumu(_el([1, 1, 1, 1])) == "sil"
    assert S.el_durumu(_el([0, 0, 0, 0])) == "yok"


def test_sisir_merkezi_buyutur_disari_dokunmaz():
    img = np.zeros((200, 200, 3), np.uint8)
    img[95:105, 95:105] = 255           # ortada küçük beyaz kare
    once = img.copy()
    S.sisir(img, 100, 100, 50, 0.7)
    assert (img[:, :, 0] > 128).sum() > (once[:, :, 0] > 128).sum()   # büyüdü
    assert (img[:40] == once[:40]).all()                             # yarıçap dışı aynı


def test_sisir_kenarda_cokmez():
    img = np.random.randint(0, 255, (100, 100, 3), np.uint8)
    S.sisir(img, 2, 2, 60, 0.6)
    S.sisir(img, 99, 50, 3, 0.6)


# ---------------------------------------------------------------- sahne (sahte noktalarla, kamera/model yok)
import pytest


def _isaret_eli(x, y):
    """Yalnız işaret parmağı açık el; işaret ucu (x, y)."""
    lm = [N(x=x, y=y + 0.2) for _ in range(21)]
    lm[9] = N(x=x, y=y + 0.1)
    lm[8] = N(x=x, y=y)
    for uc in (12, 16, 20):
        lm[uc] = N(x=x, y=y + 0.1)
    return lm


def _yuz(cx=0.5, cy=0.4, r=0.1):
    """478 noktalı sahte yüz: noktalar daire üstünde, göz/ağız/alın/çene noktaları anlamlı yerde."""
    a = np.linspace(0, 2 * np.pi, 478, endpoint=False)
    lm = [N(x=cx + r * np.cos(t) * 0.6, y=cy + r * np.sin(t)) for t in a]
    for i, (dx, dy) in {33: (-0.03, -0.02), 263: (0.03, -0.02), 468: (-0.03, -0.02), 473: (0.03, -0.02),
                        13: (0, 0.04), 14: (0, 0.05), 10: (0, -0.09), 152: (0, 0.1)}.items():
        lm[i] = N(x=cx + dx, y=cy + dy)
    return lm


def _poz(cx=0.5, cy=0.3, gor=0.9):
    lm = [N(x=cx, y=cy + 0.3, visibility=0.1) for _ in range(33)]
    lm[0] = N(x=cx, y=cy, visibility=gor)
    lm[7] = N(x=cx - 0.03, y=cy - 0.01, visibility=gor)
    lm[8] = N(x=cx + 0.03, y=cy - 0.01, visibility=gor)
    return lm


@pytest.fixture
def stant(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "DUVAR", tmp_path / "duvar")
    return S.Stant()


def _kare():
    return np.full((S.Y, S.G, 3), 120, np.uint8)


def test_bos_durumda_tanitim_ekrani(stant):
    out = stant.isle(_kare(), [], [], [], [], 100.0)
    assert stant.durum == "bos"
    assert out.shape == (S.Y, S.G, 3)
    assert out.mean() < 120          # kamera karartıldı


def test_vucut_var_yuz_yok_emoji_kafa(stant):
    kare = _kare()
    out = stant.isle(kare.copy(), [], [], [], [_poz()], 100.0)
    assert stant.durum == "uzak"
    cx, cy = int(0.5 * S.G), int(0.3 * S.Y)
    assert (out[cy - 20:cy + 20, cx - 20:cx + 20] != 120).any()   # kafa bölgesine emoji bindi


def test_poz_kafa_gorunmezse_none():
    assert S.poz_kafa(_poz(gor=0.1)) is None
    cx, cy, boy, aci = S.poz_kafa(_poz())
    assert boy > 0 and abs(aci) < 1


def test_yuz_varsa_yakin_ve_her_efekt_calisir(stant):
    for ef in range(len(S.EFEKTLER)):
        stant.efekt, stant.t_efekt = ef, 100.0
        out = stant.isle(_kare(), [_yuz()], [], [], [], 100.1)
        assert stant.durum == "yakin"
        assert out.shape == (S.Y, S.G, 3)


def test_kisi_kaybolunca_hemen_degil_sonra_bos(stant):
    stant.isle(_kare(), [_yuz()], [], [], [], 100.0)
    stant.isle(_kare(), [], [], [], [], 100.5)
    assert stant.durum == "yakin"                 # kısa kayıpta titreme yok
    stant.isle(_kare(), [], [], [], [], 100.0 + S.BOS_SN + 0.1)
    assert stant.durum == "bos"


def test_isaret_tut_cizime_gec_ciz_basparmakla_kaydet(stant):
    t = 100.0
    for _ in range(25):
        stant.isle(_kare(), [], [_isaret_eli(0.5, 0.5)], [None], [], t)
        t += 0.033
    assert stant.mod == "cizim"
    for i in range(30):
        stant.isle(_kare(), [], [_isaret_eli(0.3 + i * 0.01, 0.5)], [None], [], t)
        t += 0.033
    assert stant.tuval.any()
    for _ in range(20):
        stant.isle(_kare(), [], [_isaret_eli(0.5, 0.5)], ["Thumb_Up"], [], t)
        t += 0.033
    assert stant.mod == "filtre"
    assert len(list(S.DUVAR.glob("*.png"))) == 1
    assert len(stant.kucukler) == 1


def test_el_kaybolunca_cizim_kaydedilir(stant):
    t = 100.0
    for i in range(40):
        stant.isle(_kare(), [], [_isaret_eli(0.3 + i * 0.005, 0.5)], [None], [], t)
        t += 0.033
    stant.isle(_kare(), [], [], [], [], t + S.EL_KAYIP_SN + 0.1)
    assert stant.mod == "filtre"
    assert len(list(S.DUVAR.glob("*.png"))) == 1


def test_bos_cizim_kaydedilmez(stant):
    assert not stant.duvara_kaydet(100.0)
    assert not S.DUVAR.exists() or not list(S.DUVAR.glob("*.png"))


def test_parcaciklar_tavan_ve_sonme():
    p = S.Parcaciklar(tavan=50)
    p.yay(10, 10, 80)
    assert len(p.p) == 50
    img = np.zeros((100, 100, 3), np.uint8)
    p.ciz(img)
    assert img.any()
    for _ in range(30):
        p.guncelle(0.1)
    assert len(p.p) == 0


def test_bindir_kenarda_ve_disarida_cokmez():
    img = np.zeros((100, 100, 3), np.uint8)
    e = S.emoji_sprite("😎")
    S.bindir_merkez(img, e, 0, 0, 80, 30)
    S.bindir_merkez(img, e, 500, 500, 80)
    S.bindir_merkez(img, e, 99, 50, 3)
    assert img.any()


def test_kirp_sigdir_cizimi_buyutur():
    img = np.zeros((360, 640, 3), np.uint8)
    img[170:180, 310:330] = 255
    k = S.kirp_sigdir(img, 160, 90)
    assert k.shape == (90, 160, 3)
    assert (k > 0).mean() > 0.2
