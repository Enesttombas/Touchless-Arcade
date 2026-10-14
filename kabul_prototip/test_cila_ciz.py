import numpy as np
from cila_destek import *
from p_ciz_tahmin import Prototip


def ciz(p,a,t):
    p.onceki_t=t;p.ciz(a)


def oyun():
    p=Prototip(C.Ses(acik=False));p.mod='Seyirci';p.baslat(algi(1,y=.4),0.);return p


def test_ciz_15fps_yol_birlesir():
    p=oyun()
    for j in range(20):ciz(p,algi(1,x=.2+j*.008,y=.4),j/15)
    assert len(p.cizimler[10])==1 and len(p.cizimler[10][0])>=20 and p.tuvaller[10].any()


def test_ciz_kayip_sonrasi_yeni_cizgi():
    p=oyun();ciz(p,algi(1,x=.3,y=.4),0.);ciz(p,algi(1,x=.32,y=.4),.1)
    ciz(p,algi(0),.51);ciz(p,algi(1,x=.34,y=.4),.6);ciz(p,algi(1,x=.35,y=.4),.7)
    assert len(p.cizimler[10])==2


def test_ciz_tek_kare_kapanma_histerezis():
    p=oyun();ciz(p,algi(1,y=.4),0.);ciz(p,algi(1,y=.4),.1)
    for t in (.2,.3,.4):
        ciz(p,algi(1,y=.4,jest='Closed_Fist'),t);assert 10 in p.kalem
    ciz(p,algi(1,y=.4,jest='Closed_Fist'),.5);assert 10 not in p.kalem


def test_ciz_noktalar_etiketten_oncelikli_orta_acikken_de_cizer():
    p=oyun();a=algi(1,y=.4,jest='Victory');a.jestler=['Closed_Fist']
    ciz(p,a,0.);ciz(p,a,.1)
    assert p.cizimler[10] and p.tuvaller[10].any()


def test_ciz_sicrama_uzun_segment_olmaz():
    p=oyun();ciz(p,algi(1,x=.2,y=.4),0.);ciz(p,algi(1,x=.21,y=.4),.05)
    ciz(p,algi(1,x=.8,y=.4),.1);ciz(p,algi(1,x=.81,y=.4),.15)
    assert len(p.cizimler[10])==2 and not p.tuvaller[10][:,500:700].any()


def test_ciz_sil_bir_saniye_geri_al_son_cizgi():
    p=oyun();ciz(p,algi(1,x=.3,y=.4),0.);ciz(p,algi(1,x=.33,y=.4),.1)
    ciz(p,algi(1,y=.4,jest='Open_Palm'),.2);assert p.cizimler[10]
    ciz(p,algi(1,y=.4,jest='Open_Palm'),1.21);assert not p.cizimler[10]
    ciz(p,algi(1,x=.3,y=.4),1.3);ciz(p,algi(1,x=.33,y=.4),1.4)
    p.geri_al(10);assert not p.cizimler[10]


def test_ciz_2005_gurultulu_kare():
    gurultu('p_ciz_tahmin')


def test_ciz_kamera_tuvalde_de_gorunur_kalir():
    import p_ciz_tahmin as M
    a=algi(1);p=M.Prototip(C.Ses(acik=False));p.baslat(a,0.)
    k=np.full((C.Y,C.G,3),160,np.uint8)
    out=p.isle(k,a,.1)
    assert out[380:430,60:160].mean()>=160*.65
