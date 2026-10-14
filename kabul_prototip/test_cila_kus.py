import numpy as np
from cila_destek import *
from p_parmak_kusu import Prototip


def oyun():
    p=Prototip(C.Ses(acik=False));p.baslat(algi(1,x=.3,y=.5),0.);return p


def test_kus_hiz_monoton_tavan_aralik_adil():
    p=oyun();hiz=[];bos=[]
    for skor in range(100):p.skor=skor;hiz.append(p.hiz);bos.append(p.aralik)
    assert all(a<=b for a,b in zip(hiz,hiz[1:])) and hiz[-1]<=hiz[0]*2.2
    assert np.isclose(hiz[1]/hiz[0],1.04) and min(bos)>=bos[0]*.75


def test_kus_boru_15_60fps_ayni_yol():
    xs=[]
    for fps in (60,15):
        p=oyun();p.sutunlar=[dict(x=1200.,y=360.,gecen=set())];a=algi(1,x=.3,y=.5)
        for j in range(fps):p.adim(a,(j+1)/fps,1/fps)
        xs.append(p.sutunlar[0]['x'])
    assert abs(xs[0]-xs[1])<5


def test_kus_el_kaybi_olum_degil_ve_borular_durur():
    p=oyun();x=p.sutunlar[0]['x'];y=p.kuslar[10]['y']
    for t in np.arange(.1,1.5,.1):p.adim(algi(0),float(t),.1)
    assert p.durum=='oyun' and p.kuslar[10]['canli'] and p.sutunlar[0]['x']==x and p.kuslar[10]['y']==y


def test_kus_kontrol_hizdan_bagimsiz():
    ys=[]
    for skor in (0,30):
        p=oyun();p.skor=skor;p.sutunlar=[]
        p.adim(algi(1,y=.4),.1,.1);ys.append(p.kuslar[10]['y'])
    assert ys[0]==ys[1]


def test_kus_2005_gurultulu_kare():
    gurultu('p_parmak_kusu')
