import numpy as np
import pytest
from cila_destek import C,kamera
import p_refleks as M
from goruntule import algi,el


def yuzler(n=2,eller=()):
    a=algi(0)
    a.yuzler=[C.sahte_yuz(.25+.5*j,.23,.08) for j in range(n)]
    a.yuz_id=list(range(n));a.eller=list(eller);a.el_id=list(range(len(eller)))
    return a


def oyun(n=2):
    p=M.Prototip(C.Ses(acik=False));p.baslat(yuzler(n),0.);p.bekleme=1.5
    return p


def kare(p,a,t,k):
    p.kare_no=k;p.adim(a,t)


def test_yalniz_yuzler_eller_yokken_hazir_ve_ates():
    p=oyun();a=yuzler()
    for t,k in [(0.,0),(.6,18),(2.11,63)]:kare(p,a,t,k)
    assert p.hazir=={0:True,1:True} and p.k0==63


def test_ates_sonrasi_ilk_kare_kazanir():
    p=oyun();a=yuzler()
    for t,k in [(0.,0),(.6,18),(2.11,63)]:kare(p,a,t,k)
    kare(p,yuzler(eller=[el(.75,.15)]),2.15,64)
    assert p.puanlar==[0,1] and p.tepki>0


def test_tek_sicrama_erken_degil_iki_kare_erken():
    p=oyun();kare(p,yuzler(),0.,0);kare(p,yuzler(),.6,18)
    a=yuzler(eller=[el(.25,.15)])
    kare(p,a,.7,21);assert p.ara_t is None
    kare(p,a,.74,22);assert p.puanlar==[0,1] and 'ERKEN' in p.mesaj


def test_beldeki_el_hazirligi_bozmaz():
    p=oyun();a=yuzler(eller=[el(.25,.8),el(.75,.9)])
    kare(p,a,0.,0);kare(p,a,.61,18)
    assert all(p.hazir.values())


def test_sekiz_sn_hazir_olmayan_seyirci():
    p=oyun();a=yuzler(eller=[el(.75,.15)])
    for t,k in [(0.,0),(.61,18),(4.,120),(8.01,240),(9.6,288)]:kare(p,a,t,k)
    assert p.aktif=={0} and p.k0 is not None and p.ara_t is None


def test_tek_yuz_yz_ile_oynar():
    p=oyun(1);a=yuzler(1)
    for t,k in [(0.,0),(.6,18),(2.11,63)]:kare(p,a,t,k)
    assert p.aktif=={0} and p.yz_kare>p.k0
    kare(p,a,3.,p.yz_kare)
    assert p.puanlar==[0,1]


@pytest.mark.parametrize('durum',['bekle','hazir','oyun','sonuc'])
def test_yazi_cagrisi_en_fazla_iki(monkeypatch,durum):
    p=oyun();p.durum=durum;p.durum_t=0.
    say=[];monkeypatch.setattr(M,'yazi_koy',lambda *a,**k:say.append(a[1]))
    p.isle(np.full((C.Y,C.G,3),160,np.uint8),yuzler(),.2)
    assert 1<=len(say)<=2 and all('KILIF' not in s for s in say)


def test_yuz_yokken_vitrin_ve_kamera_korunur():
    p=oyun();k=np.full((C.Y,C.G,3),160,np.uint8)
    p.isle(k,yuzler(0),4.)
    assert p.durum=='bekle' and k[500,200,0]>=120
