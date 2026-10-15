import numpy as np
from cila_destek import C, kamera
from test_parmak_kusu import oyun
import p_parmak_kusu as M


def test_ilk_boru_sifir_skorda_da_salinir():
    p,a=oyun();b=p.yeni_boru(1000);b.update(y=360.,faz=0.)
    ilk=p.bosluk_y(b)
    for _ in range(10):son=p.bosluk_y(b,1/30)
    assert son>ilk+5


def test_her_borunun_fazi_ve_frekansi_ayri():
    p,a=oyun();borular=[p.yeni_boru(1000) for _ in range(4)]
    for b in borular:b['y']=360.
    assert len({b['faz'] for b in borular})==4
    assert len({b['frekans'] for b in borular})==4
    assert len({round(p.bosluk_y(b),3) for b in borular})==4


def test_genlik_skorda_buyur_120de_durur():
    p,a=oyun();b=p.yeni_boru(1000);p.skor=100
    for _ in range(300):p.bosluk_y(b,1/30)
    assert b['genlik']==120
    p.skor=0;p.bosluk_y(b,1/30)
    assert 35<=b['genlik']<120


def test_merkez_ekran_icinde():
    p,a=oyun();p.skor=100
    for y in (0,360,C.Y):
        b=p.yeni_boru(1000);b['y']=y
        for _ in range(200):
            cy=p.bosluk_y(b,1/8)
            assert p.aralik/2+40<=cy<=C.Y-p.aralik/2-40


def test_skor_artisi_dahil_dikey_hiz_adil():
    p,a=oyun();b=p.yeni_boru(1000);once=p.bosluk_y(b)
    for j in range(800):
        p.skor=j//8;dt=(1/60,1/15,1/8)[j%3];cy=p.bosluk_y(b,dt)
        assert abs(cy-once)/dt<=.6*p.TIRMANMA_HIZI+1e-6
        once=cy


def test_cizim_ve_carpisma_ayni_bosluk_skor_degisiminde(monkeypatch):
    p,a=oyun();p.sutunlar=[p.yeni_boru(p.KUS_X-100)]
    carp,ciz=[],[]
    monkeypatch.setattr(M,'sutun_carpisti',lambda *args:carp.append(args[-2:]) or False)
    monkeypatch.setattr(p,'boru',lambda k,x,cy:ciz.append((cy,p.cizim_aralik)))
    p.isle(kamera(a),a,.1)
    assert p.skor==1 and carp==ciz


def test_kayip_el_salinimi_de_durdurur():
    p,a=oyun();b=p.yeni_boru(1000);p.sutunlar=[b]
    p.adim(a,.1,.1);cy=b['cy'];faz=b['faz'];a.eller=[];a.el_id=[]
    p.adim(a,.3,.1)
    assert b['cy']==cy and b['faz']==faz
