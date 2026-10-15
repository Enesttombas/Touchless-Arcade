import numpy as np
from test_ozel import C, KARE, algi
from p_parmak_kusu import Prototip
from oyun_akis import sutun_carpisti


def oyun(n=1, mod='Süzül'):
    p = Prototip(C.Ses(acik=False))
    a = algi([C.sahte_el(.5, .5) for _ in range(n)])
    a.el_id = list(range(10, 10+n))
    p.mod = mod
    p.baslat(a, 0.)
    p.sutunlar = []
    return p, a


def test_sabit_parmak_ve_gurultu():
    p, a = oyun()
    hedef = (.5*C.Y-.15*C.Y)/.714
    for i in range(1, 121):
        a.eller[0][8].y = .5 + (4 if i%2 else -4)/C.Y
        p.adim(a, i/60, 1/60)
        if i > 60:
            assert abs(p.kuslar[10]['y']-hedef) < 1.5


def test_sicrama_isinlanmaz():
    p, a = oyun()
    a.eller[0][8].y = .1
    p.adim(a, 1/60, 1/60)
    assert 0 < 360-p.kuslar[10]['y'] < 40


def test_gecis_tek_skor_ve_carpisma():
    p, a = oyun()
    p.sutunlar = [dict(x=p.KUS_X-90, y=360., gecen=set())]
    p.adim(a, .01, .01)
    p.adim(a, .02, .01)
    assert p.skor == 1
    p.sutunlar[0].update(x=p.KUS_X, y=130., cy=130.)
    p.adim(a, .03, .01)
    assert p.durum == 'sonuc'


def test_sprite_kenarina_siyirmak_affedilir():
    assert not sutun_carpisti(300, 360, 22.4, 329, 86, 120, 200)
    assert sutun_carpisti(300, 360, 22.4, 320, 86, 120, 200)


def test_fiske_hizli_yukari_ve_yavas():
    p, a = oyun(mod='Flappy')
    a.eller[0][8].y -= .003
    p.adim(a, .02, .02)
    assert p.kuslar[10]['v'] > 0
    a.eller[0][8].y -= .1
    p.adim(a, .04, .02)
    assert p.kuslar[10]['v'] < -400


def test_iki_el_kimlik_ve_kazanan():
    p, a = oyun(2)
    p.kuslar[10]['canli'] = False
    a.eller.reverse()
    a.el_id.reverse()
    p.adim(a, .02, .02)
    assert p.kazanan == 11 and p.durum == 'sonuc'


def test_el_kaybi_tahmin_de_canlandirmaz():
    p, a = oyun()
    a.tahmini = [('el', 10)]
    p.adim(a, .8, .1)
    assert p.kuslar[10]['canli']
    p.adim(a, 1.5, .1)
    assert p.kuslar[10]['canli'] and p.durum == 'oyun'


def test_gorunur_baslangic_tur_sonucu_ve_menu():
    p = Prototip(C.Ses(acik=False))
    a = algi([C.sahte_el(.5, .37)])
    p.isle(KARE(), a, 0.)
    p.isle(KARE(), a, 1.1)
    assert p.durum == 'hazir'
    p.isle(KARE(), a, 4.2)
    assert p.durum == 'oyun'
    p.isle(KARE(), a, 65.)
    assert p.durum == 'sonuc'
    p.isle(KARE(), a, 71.)
    assert p.durum == 'bekle'


def test_menu_karti_ve_kamerali_cizim():
    import stant_app as S
    u = S.StantUygulama(C.Ses(acik=False))
    u.tus(ord('4'), 0.)
    assert u._ornek(3).AD == 'Kanat Rotası'
    p, a = oyun()
    assert p.isle(KARE(), a, .1).shape == (C.Y, C.G, 3)


def test_el_yeni_kimlikle_donunce_oyun_devam_eder():
    # iki oyuncu; 11 numaralı el kaybolup 0,6 sn sonra 99 kimliğiyle döner
    p, a = oyun(2)
    p.adim(a, .02, .02)
    sira = list(p.kuslar)
    a.el_id = [10, 99]
    p.adim(a, .1, .02)
    assert p.kayip_t is None and p.durum == 'oyun'
    assert list(p.kuslar) == [10, 99] and len(sira) == 2  # sıra (yer/renk) korunur


def test_oyuncu_gidince_sonsuza_dek_donmaz():
    p, a = oyun(2)
    a.eller, a.el_id = a.eller[:1], [10]
    p.adim(a, .1, .02)
    assert p.kayip_t is not None and p.durum == 'oyun'
    p.adim(a, 5.2, .02)
    assert p.durum == 'sonuc'


def test_bir_oyuncu_kaybolunca_oteki_oynamaya_devam_eder():
    p, a = oyun(2)
    a.eller, a.el_id = a.eller[:1], [10]
    p.adim(a, .1, .02)
    m0 = p.mesafe
    a.eller[0][8].y = .2
    y0 = p.kuslar[10]['y']
    for i in range(2, 30):
        p.adim(a, .1 + i/60, 1/60)
    assert p.mesafe > m0 and p.kuslar[10]['y'] < y0  # oyun akıyor, duran oyuncunun kuşu eli izliyor
    assert p.kuslar[11]['canli'] and p.durum == 'oyun'  # kayıp kuş çarpmaz, 5 sn bekler


def test_bekleme_ekraninda_el_modu_degistirmez():
    p = Prototip(C.Ses(acik=False))
    a = algi([C.sahte_el(1100/C.G, 48/C.Y)])  # 9. nokta eski mod panelinin (960-1240, 80-160) içinde
    for i in range(120):
        p.isle(KARE(), a, i/30)
    assert p.mod == 'Süzül'
