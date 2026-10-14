import numpy as np
import pytest
from test_ozel import C,KARE,algi
from rekabet import Rekabet,Tekrar,erken_kare
from p_refleks import Prototip as Kovboy
from p_tas_kagit import Prototip as TKM,kazanan


def a(n=2,y=.7,jest='Closed_Fist',skor=.9):
    from goruntule import el
    v=algi([el(.25+j*.5,y,jest) for j in range(n)],[jest]*n)
    v.el_id=list(range(10,10+n))
    v.jest_skor=[skor]*n
    v.yuzler=[C.sahte_yuz(.25+j*.5,.23,.08) for j in range(n)]
    return v


def oyun(cls,n=2):
    p=cls(C.Ses(acik=False));p.baslat(a(n),0.);return p


def adim(p,v,t,k):
    p.kare_no=k;p.adim(v,t)


def test_kovboy_erken_ceken_kaybeder():
    p=oyun(Kovboy);p.bekleme=5
    adim(p,a(),0.,0);adim(p,a(),.61,31)
    v=a();v.eller[0]=C.sahte_el(.25,.2)
    adim(p,v,.6,36);adim(p,v,.7,42)
    assert p.puanlar==[0,1] and 'ERKEN' in p.mesaj


def test_kovboy_ayni_kare_esitlik():
    p=oyun(Kovboy);p.bekleme=2
    adim(p,a(),0.,0);adim(p,a(),.61,31)
    adim(p,a(),2.61,120)
    adim(p,a(y=.2),2.7,132)
    assert p.k0==120 and p.puanlar==[0,0] and 'Aynı kare' in p.mesaj


def test_farkli_karede_erken_olan():
    assert erken_kare({0:121,1:122})==0
    assert erken_kare({0:124,1:122})==1
    assert erken_kare({0:121,1:121}) is None
    p=oyun(Kovboy);p.bekleme=2
    adim(p,a(),0.,0);adim(p,a(),.61,31);adim(p,a(),2.61,120)
    v=a();v.eller[1]=C.sahte_el(.75,.2)
    adim(p,v,2.7,132)
    assert p.puanlar==[0,1] and p.tepki>0


def test_tohumlu_sinyal_1_5_4():
    p=oyun(Kovboy);q=oyun(Kovboy)
    p.rng=np.random.default_rng(5);q.rng=np.random.default_rng(5)
    for i in range(50):
        p.yeni_raunt(i);q.yeni_raunt(i)
        assert 1.5<=p.bekleme<=4 and p.bekleme==q.bekleme


def test_kovboy_tek_kisi_yz_kareyle_oynar():
    p=oyun(Kovboy,1);p.bekleme=2
    adim(p,a(1),0.,0);adim(p,a(1),.61,31);adim(p,a(1),2.61,120)
    assert p.yz_kare==156
    adim(p,a(1),3.21,156)
    assert p.puanlar==[0,1]


def test_tkm_onceki_jest_sayilmaz_ve_yuksek_guven_kazanir():
    p=oyun(TKM)
    adim(p,a(jest='Victory'),2.9,174)
    assert not p.secimler
    adim(p,a(jest='Closed_Fist',skor=.7),3.05,183)
    adim(p,a(jest='Victory',skor=.95),3.2,192)
    adim(p,a(jest='Open_Palm',skor=.8),3.3,198)
    assert p.secimler[0]==('makas',.95)
    adim(p,a(),3.61,217)
    assert p.puanlar==[0,0]


@pytest.mark.parametrize('x,y,k',[('taş','makas',0),('makas','kağıt',0),('kağıt','taş',0),('makas','taş',1),('taş','taş',None)])
def test_tkm_kural(x,y,k):
    assert kazanan(x,y)==k


def test_tkm_dusuk_guven_tekrar():
    p=oyun(TKM)
    adim(p,a(jest='Pointing_Up',skor=.59),3.1,186)
    adim(p,a(jest='Pointing_Up',skor=.59),3.61,217)
    assert p.puanlar==[0,0] and 'net göster' in p.mesaj


def test_tkm_yz_bes_tasi_ogrendi():
    p=oyun(TKM,1);p.rng=np.random.default_rng(9)
    p.gecmis.extend(['taş']*5)
    assert sum(p.yz_sec()=='kağıt' for _ in range(1000))/1000>=.6
    assert p.yz_oran==1


def test_3te2_kazanan_ve_puan_id_korunur():
    p=oyun(TKM)
    p.raunt_bitir(1,1.);p.yeni_raunt(3.)
    v=a();v.el_id.reverse()
    assert set(p.eller(v))=={0,1}
    assert p.eller(v)[0][1]==1
    p.raunt_bitir(1,4.)
    assert p.durum=='sonuc' and p.kazanan==1 and p.puanlar==[0,2]


def test_tekrar_tamponu_ram_sure_ve_kare_siniri():
    t=Tekrar(30)
    for i in range(300):
        t.ekle(KARE(),i/30)
    assert len(t.kareler)<=45
    assert t.kareler[-1][0]-t.kareler[0][0]<=1.5
    assert t.goruntu(1).shape==(180,320,3)


def test_menu_iki_kart_ve_cizim():
    import stant_app as S
    u=S.StantUygulama(C.Ses(acik=False))
    assert 'p_tas_kagit' not in S.DENEYIMLER  # TKM menüden çıktı (Enes 2026-10-13); oyun dosyası yine çalışmalı
    u.tus(ord('6'),0.)
    assert isinstance(u._ornek(5),Kovboy)
    for cls in (Kovboy,TKM):
        p=oyun(cls)
        assert p.isle(KARE(),a(),.1).shape==(C.Y,C.G,3)


def test_sonuc_sonrasi_kamera_tamponu_silinir():
    p=oyun(Kovboy);p.tekrar.ekle(KARE(),0.)
    p.donmus=p.tekrar;p.bitir(0.)
    p.isle(KARE(),algi(),5.1)
    assert p.durum=='bekle' and p.donmus is None and not p.tekrar.kareler
