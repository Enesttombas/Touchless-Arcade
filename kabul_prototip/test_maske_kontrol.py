import math
import pytest
from test_altyapi import C, OyuncuKapisi
from test_ozel import KARE
from p_maske import Prototip


def yeni():
    return Prototip(C.Ses(acik=False))


def a(bl=None, el=None):
    return C.Algi(yuzler=[C.sahte_yuz()], blend=[bl or {}], eller=[el] if el else [])


def sur(p, algi, bas, sure, adim=.1):
    for i in range(round(sure / adim) + 1):
        p.isle(KARE(), algi, bas + i * adim)


@pytest.mark.parametrize("bl", [{"eyeBlinkLeft": .9, "eyeBlinkRight": .9}, {}])
def test_dogal_ifadeler_degistirmez(bl):
    p = yeni()
    p.isle(KARE(), a(), 0)
    idx = p.takipler[0].maske_idx
    sur(p, a(bl), .1, 1)
    assert p.takipler[0].maske_idx == idx
    if "eyeBlinkLeft" in bl:
        assert p.takipler[0].goz_efekti


def egik(aci):
    algi = a()
    for n in algi.yuzler[0]:
        dx, dy = (n.x - .5) * C.G, (n.y - .5) * C.Y
        n.x, n.y = .5 + (dx * math.cos(aci) - dy * math.sin(aci)) / C.G, .5 + (dx * math.sin(aci) + dy * math.cos(aci)) / C.Y
    return algi


def test_bas_egimi_degistirir_iki_yonlu():
    # Enes 2026-10-12 "akıcı ve kolay": başı sağa yatır sonraki, sola önceki; eğik tutmak tekrarlamaz
    p = yeni()
    p.isle(KARE(), a(), 0)
    sur(p, a(), .05, .3)
    sur(p, egik(.5), .4, 1)
    assert p.takipler[0].maske_idx == 1
    sur(p, a(), 1.5, .5)
    sur(p, egik(-.5), 2.1, 1)
    assert p.takipler[0].maske_idx == 0


@pytest.mark.parametrize("aci, sure", [(.2, 1.5), (.5, .1)])  # gülerken ~11°; çok kısa eğme
def test_hafif_ya_da_kisa_egim_degistirmez(aci, sure):
    p = yeni()
    p.isle(KARE(), a(), 0)
    sur(p, a(), .05, .3)
    sur(p, egik(aci), .4, sure, adim=.05)
    sur(p, a(), .5 + sure, .5)
    assert p.takipler[0].maske_idx == 0


def test_yuz_varken_otomatik_yok_vitrin_var():
    p = yeni()
    p.isle(KARE(), a(), 0)
    sur(p, a(), .1, 30, .5)
    assert p.takipler[0].maske_idx == 0
    p.isle(KARE(), C.Algi(), 32)
    assert p.tur == 1


@pytest.mark.parametrize("yon", [-1, 1])
def test_ok_tutma_kilit_ve_tekrar(yon):
    p = yeni()
    p.isle(KARE(), a(), 0)
    x, y = p._dugme_merkez(yon)
    algi = a(el=C.sahte_el(x / C.G, y / C.Y - .1, "avuc"))
    sur(p, algi, .1, .4)
    assert p.takipler[0].maske_idx == 0
    sur(p, algi, .6, 3)
    assert p.takipler[0].maske_idx == yon % len(p.MASKELER)
    p.isle(KARE(), a(), 3.8)
    sur(p, algi, 3.9, .8)
    assert p.takipler[0].maske_idx == (2 * yon) % len(p.MASKELER)


def test_el_sallama_degistirmez():
    p = yeni()
    p.isle(KARE(), a(), 0)
    for i in range(12):
        algi = a(el=C.sahte_el(.3 + (i % 6) * .08, .5, "avuc"))
        algi.jestler = [None]
        p.isle(KARE(), algi, (i + 1) * .05)
    assert p.takipler[0].maske_idx == 0


def avuc_sira(p, jestler, bas=.1, adim=.066):
    for i, jest in enumerate(jestler):
        algi = a(el=C.sahte_el(.5, .6, "avuc"))
        algi.jestler = [jest]
        p.isle(KARE(), algi, bas + i * adim)
    return bas + len(jestler) * adim


def test_kas_kaldirma_degistirmez_efekt_oynar():
    # kaş yalnız efekt (şaşırınca kaş kalkar); KAS_TETIK açılırsa değiştirir
    p = yeni()
    p.isle(KARE(), a(), 0)
    sur(p, a({"browInnerUp": .8}), .1, 1)
    assert p.takipler[0].maske_idx == 0
    q = yeni()
    q.KAS_TETIK = True
    q.isle(KARE(), a(), 0)
    sur(q, a({"browInnerUp": .8}), .1, 1)
    assert q.takipler[0].maske_idx == 1


def test_kisa_kas_seyirmesi_degistirmez():
    p = yeni()
    p.isle(KARE(), a(), 0)
    sur(p, a({"browInnerUp": .8}), .05, .1, adim=.05)  # ~0.15 sn seyirme
    sur(p, a({"browInnerUp": .05}), .3, .5)
    assert p.takipler[0].maske_idx == 0


def test_avuc_varsayilan_kapali():
    p = yeni()
    p.isle(KARE(), a(), 0)
    avuc_sira(p, ["Open_Palm"] * 3 + ["Closed_Fist"] * 3)
    assert p.takipler[0].maske_idx == 0


def test_avuc_ac_kapa_degistirir_tek_adim():
    p = yeni()
    p.AVUC_TETIK = True
    p.isle(KARE(), a(), 0)
    avuc_sira(p, ["Open_Palm"] * 3 + ["Closed_Fist"] * 10)
    assert p.takipler[0].maske_idx == 1


def test_avuc_tekrar_ac_kapa_bir_daha_degistirir():
    p = yeni()
    p.AVUC_TETIK = True
    p.isle(KARE(), a(), 0)
    t = avuc_sira(p, ["Open_Palm"] * 3 + ["Closed_Fist"] * 3)
    avuc_sira(p, ["Open_Palm"] * 3 + ["Closed_Fist"] * 3, bas=t)
    assert p.takipler[0].maske_idx == 2


@pytest.mark.parametrize("jestler", [
    ["Open_Palm"] + ["Closed_Fist"] * 3,          # tek karelik yanlış avuç
    ["Closed_Fist"] * 6,                          # avuç açılmadan yumruk
    ["Open_Palm"] * 3 + [None] * 20 + ["Closed_Fist"] * 3,  # 1.2 sn'den geç kapanış
])
def test_avuc_yanlis_tetik_yok(jestler):
    p = yeni()
    p.AVUC_TETIK = True
    p.isle(KARE(), a(), 0)
    avuc_sira(p, jestler)
    assert p.takipler[0].maske_idx == 0


def test_avuc_tetik_kapatilabilir():
    p = yeni()
    p.AVUC_TETIK = False
    p.isle(KARE(), a(), 0)
    avuc_sira(p, ["Open_Palm"] * 3 + ["Closed_Fist"] * 3)
    assert p.takipler[0].maske_idx == 0


def test_eski_tetik_geri_donusu():
    p = yeni()
    p.ESKI_TETIKLER = True
    p.isle(KARE(), a(), 0)
    sur(p, a({"eyeBlinkLeft": .9, "eyeBlinkRight": .9}), .1, .7)
    assert p.takipler[0].maske_idx == 1


def test_etiket_bir_saniye():
    p = yeni()
    p.isle(KARE(), a(), 0)
    p._degistir(p.takipler[0], 1, .2)
    p.isle(KARE(), a(), .3)
    assert p.takipler[0].etiket.startswith("→")
    p.isle(KARE(), a(), 1.3)
    assert not p.takipler[0].etiket


def test_kapi_yarim_el_degistiremez():
    p, k = yeni(), OyuncuKapisi()
    algi = a(el=C.sahte_el(1.1, .42))
    for i in range(22):
        p.isle(KARE(), k.suz(algi, i * .1), i * .1)
    assert p.takipler[0].maske_idx == 0 and not p.hedef_yuz


def test_kalabalik_el_sahibi_hedeflenir():
    p = yeni()
    algi = C.Algi(yuzler=[C.sahte_yuz(.3), C.sahte_yuz(.7)], blend=[{}, {}], yuz_id=[11, 22])
    p.isle(KARE(), algi, 0)
    x, y = p._dugme_merkez(-1)
    algi.eller = [C.sahte_el(x / C.G, y / C.Y - .1, "avuc")]
    algi.el_id = [33]
    algi.kisi_id = {("el", 33): 22}
    p.isle(KARE(), algi, .1)
    assert p.hedef_yuz.kimlik == 22
    sur(p, algi, .2, .7)
    assert p.takipler[0].maske_idx == 0 and p.takipler[1].maske_idx == 0


def test_titrek_egim_hizli_hizli_degistirmez():
    # Enes 2026-10-13: maske "ışık hızıyla" değişiyordu; düz-eğik-düz-eğik sallanma 1 sn'de en çok bir değişim yapar
    p = yeni()
    p.isle(KARE(), a(), 0)
    sur(p, a(), .05, .3)
    t = .4
    for _ in range(4):
        sur(p, egik(.5), t, .5, adim=.05)
        sur(p, a(), t + .55, .1, adim=.05)
        t += .7
    assert p.takipler[0].maske_idx in (1, 2)  # 2,8 sn'de en çok 2 değişim (eskiden her sallanmada)


def test_cok_kisa_egim_tutmasi_degistirmez():
    p = yeni()
    p.isle(KARE(), a(), 0)
    sur(p, a(), .05, .3)
    sur(p, egik(.5), .4, .3, adim=.05)  # 0,3 sn eşik üstü: eskiden (0,2 sn) değiştiriyordu
    sur(p, a(), .75, .5)
    assert p.takipler[0].maske_idx == 0
