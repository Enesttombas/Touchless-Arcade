import json
import numpy as np
import pytest
from test_ozel import C, KARE, algi
import p_cevap_yagmuru as M


def poz(x):
    p = C.sahte_poz()
    for v in p:
        v.x, v.y, v.visibility = x, .55, .95
    for j in (11,23,15,27):
        p[j].x = x-.035
    for j in (12,24,16,28):
        p[j].x = x+.035
    for j in (11,12):
        p[j].y = .35
    for j in (27,28):
        p[j].y = .92
    p[0].y = .23
    return p


def a(*xs):
    v = algi()
    v.pozlar, v.poz_id = [poz(x) for x in xs], list(range(1,len(xs)+1))
    return v


def oyun(*xs):
    p = M.Prototip(C.Ses(acik=False))
    p.baslat(a(*xs), 0.)
    p.soru = dict(secenekler=['A','B','C'], dogru_indeks=0, soru='Soru')
    return p


def test_toplan_geri_sayim_oyun():
    p = M.Prototip(C.Ses(acik=False))
    p.adim(a(), 0.)
    assert p.durum == 'bekle'
    p.adim(a(.2), 1.)
    p.adim(a(.2), 2.4)
    assert p.durum == 'bekle'
    p.adim(a(.2), 2.6)
    assert p.durum == 'hazir'
    p.adim(a(.2), 5.7)
    assert p.durum == 'oyun'


def test_500_soru_benzersiz_ve_hesapla_dogru():
    rng = np.random.default_rng(5)
    for _ in range(500):
        s = M.matematik(rng)
        x,y,op = s['islem']
        cevap = x+y if op=='+' else x-y if op=='−' else x*y if op=='×' else x**2
        assert int(s['secenekler'][s['dogru_indeks']]) == cevap
        assert len(set(s['secenekler'])) == 3


def test_dogru_skor_tek_kez():
    p = oyun(.2,.8)
    p.adim(a(.2,.8), 8.6)
    p.adim(a(.2,.8), 9.)
    assert p.oyuncular[1]['puan']==100 and p.oyuncular[1]['durum']=='dogru'
    assert p.oyuncular[2]['puan']==0 and p.oyuncular[2]['durum']=='yanlis'


def test_yanlis_siluet_kirmizi_ton(monkeypatch):
    p = oyun(.8,.2)
    monkeypatch.setattr(M,'maske_ver', lambda k: np.ones((C.Y//2,C.G//2), np.float32))
    out = p.isle(KARE(), a(.8,.2), 8.6)
    roi = out[300:380,1000:1050]
    assert roi[:,:,2].mean() > roi[:,:,1].mean()+25


def test_kilit_sonrasi_hareket_degerlendirmeyi_degistirmez():
    p = oyun(.2,.8)
    p.adim(a(.2,.8),8.2)
    p.adim(a(.8,.2),8.6)
    assert p.oyuncular[1]['puan']==100 and p.oyuncular[2]['puan']==0


def test_cizgi_uyarisi_ve_en_yakin_merkez():
    p = oyun(.335,.8)
    assert p.cizgide(.335) and p.serit(.335)==1
    assert p.serit(.331)==0


def test_kimlik_sira_degisimi():
    p = oyun(.2,.8)
    p.oyuncular[1]['puan']=500
    z = a(.2,.8)
    z.poz_id = [2,1]
    p.kisi_guncelle(z)
    assert p.oyuncular[1]['puan']==500 and p.oyuncular[1]['x']==.8


def test_uc_seri_tac_ve_bonus():
    p = oyun(.2,.8)
    for _ in range(3):
        p.kilit, p.puanlandi = {1:0,2:1}, False
        p.puanla(1.)
    assert p.oyuncular[1]['tac'] and p.oyuncular[1]['puan']==450


def test_elendi_tekrar_puan_alamaz_son_kalan_kazanir():
    p = oyun(.2,.8)
    p.mod = 'Hayatta Kalma'
    p.kilit = {1:0,2:1}
    p.puanla(9.)
    assert p.durum=='sonuc' and p.sira[0]==1
    p.kilit, p.puanlandi = {2:0}, False
    p.puanla(10.)
    assert p.oyuncular[2]['elendi'] and p.oyuncular[2]['puan']==0


def test_alti_soru_ve_podyum_bekleme():
    p = oyun(.2,.8)
    for i in range(6):
        p.adim(a(.2,.8), (i+1)*12.6)
    assert p.durum=='sonuc' and p.faz=='podyum'
    assert len(p.sira)==2
    p.adim(a(),82.)
    assert p.durum=='bekle'


def test_60_soru_semasi_ve_hatalinin_reddi():
    p = M.Prototip(C.Ses(acik=False))
    assert len(p.banka)>=60 and M.banka_dogrula(p.banka)
    with pytest.raises(AssertionError):
        M.banka_dogrula([dict(p.banka[0],dogru_indeks=9)])


def test_uzak_kisi_oyuncu_kapisindan_gecer():
    from oyuncu import OyuncuKapisi
    gate = OyuncuKapisi()
    v = a(.3)
    v.pozlar[0][11].x, v.pozlar[0][12].x = .28,.32
    assert not gate.suz(v,0.,M.Prototip.KAPI).pozlar
    assert gate.suz(v,.5,M.Prototip.KAPI).pozlar


def test_menu_karti_ve_alti_kisi_cizim(monkeypatch):
    import stant_app as S
    u = S.StantUygulama(C.Ses(acik=False))
    u.tus(ord('5'),0.)
    assert u._ornek(4).AD=='Bilgi Yağmuru'
    monkeypatch.setattr(M,'maske_ver',lambda k: None)
    p=oyun(.1,.25,.4,.6,.75,.9)
    assert p.isle(KARE(),a(.1,.25,.4,.6,.75,.9),8.6).shape == (C.Y,C.G,3)
