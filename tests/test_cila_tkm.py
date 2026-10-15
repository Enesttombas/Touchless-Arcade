import numpy as np
from cila_destek import *
from goruntule import el
from p_tas_kagit import Prototip


def oyun():
    p=Prototip(C.Ses(acik=False));p.baslat(algi(jest='Closed_Fist'),0.);return p


def test_tkm_noktalar_yanlis_etiketi_yener():
    p=oyun();a=algi(jest='Open_Palm');a.jestler=['Closed_Fist']*2
    p.adim(a,3.2)
    assert p.secimler[0][0]=='kağıt'


def test_tkm_yarim_saniye_sonra_hala_okur():
    p=oyun();p.adim(algi(jest='Victory'),3.5)
    assert p.secimler[0][0]=='makas' and p.ara_t is None
    p.adim(algi(jest='Victory'),3.61);assert p.ara_t==3.61


def test_tkm_kucuk_elde_sayac_durur():
    p=oyun();a=algi();a.eller=[el(.3,.6,'Closed_Fist',.2),el(.7,.6,'Closed_Fist',.2)]
    p.adim(a,2.)
    assert p.raunt_t>0 and 'YAKLAŞ' in p.yonerge(2.)


def test_tkm_okunmayan_el_cezasiz_tekrar():
    p=oyun();a=algi(jest='Pointing_Up');p.adim(a,3.1);p.adim(a,3.61)
    assert p.puanlar==[0,0] and 'net' in p.mesaj.lower()


def test_tkm_sonucta_uygulanan_kural():
    p=oyun();a=algi(jest='Closed_Fist');a.eller[1]=el(.7,.6,'Victory')
    p.adim(a,3.2);p.adim(a,3.61)
    assert p.puanlar==[1,0] and 'makası' in p.kural


def test_tkm_kayip_uyarisi_yarim_saniye_bekler():
    p=oyun();bos=algi(n=0)
    p.adim(bos,.1)
    assert 'göremiyorum' not in p.uyari
    p.adim(bos,.61)
    assert 'göremiyorum' in p.uyari and p.puanlar==[0,0]
    p.adim(algi(jest='Closed_Fist'),.7)
    assert p.uyari==''


def test_tkm_2005_gurultulu_kare():
    gurultu('p_tas_kagit')
