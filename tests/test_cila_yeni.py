from cila_destek import *

def kovboy():
    from p_refleks import Prototip
    p=Prototip(C.Ses(acik=False));p.baslat(algi(y=.75),0.);p.bekleme=5
    for t in (0.,.25,.61):p.adim(algi(y=.75),t)
    return p


def test_kovboy_titreme_ve_tek_sicrama_erken_degil():
    p=kovboy()
    for j,y in enumerate([.71,.79,.72,.4,.75]):p.adim(algi(y=y),.6+j*.05)
    assert p.ara_t is None and p.puanlar==[0,0]


def test_kovboy_kayip_ve_geri_gelme_erken_degil():
    p=kovboy();p.adim(algi(0),.7);p.adim(algi(y=.8),.7);p.adim(algi(y=.8),.8)
    assert p.ara_t is None


def test_kovboy_iki_kare_gercek_erken():
    p=kovboy();p.adim(algi(y=.15),.7);assert p.ara_t is None
    p.adim(algi(y=.15),.8);assert p.ara_t==.8 and 'ERKEN' in p.mesaj


def test_kovboy_herkes_hazir_olmadan_sinyal_yok():
    from p_refleks import Prototip
    a=algi(y=.75)
    for q in a.eller[1]:q.y=np.float64(.15)
    p=Prototip(C.Ses(acik=False));p.baslat(a,0.);p.bekleme=.1
    for t in (0.,1.,2.,3.):p.adim(a,t)
    assert p.k0 is None


def test_kovboy_raunt_otomatik_yenilenmez():
    p=kovboy();p.raunt_bitir(None,1.)
    p.isle(kamera(algi(y=.15)),algi(y=.15),3.4)
    assert p.raunt==1
    p.isle(kamera(algi(y=.75)),algi(y=.75),3.6)
    assert p.raunt==2


def test_kovboy_2005_gurultulu_kare():
    gurultu('p_refleks')


def test_kovboy_hazir_olmayan_8sn_sonra_seyirci():
    from p_refleks import Prototip
    a=algi(y=.75)
    for q in a.eller[1]:q.y=np.float64(.15)
    p=Prototip(C.Ses(acik=False));p.baslat(a,0.);p.bekleme=.2
    for t in (0.,.61,1.,7.99):p.adim(a,t)
    assert p.k0 is None
    p.adim(a,8.1)
    assert p.aktif=={0} and p.k0 is None
    p.adim(a,8.4)
    assert p.k0 is not None and p.aktif=={0} and p.puanlar==[0,0]


def test_kovboy_kadrajdan_cikan_8sn_sonra_kilitlenmez():
    from p_refleks import Prototip
    p=Prototip(C.Ses(acik=False));p.baslat(algi(y=.75),0.);p.bekleme=.2
    a=algi(1,y=.75)
    for t in (0.,.61,1.,8.1,8.4):p.adim(a,t)
    assert p.k0 is not None and p.aktif=={0} and p.ara_t is None


def test_kovboy_sag_tek_kalinca_cekis_sag_oyuncuya_yazilir():
    from p_refleks import Prototip
    a=algi(y=.75)
    for q in a.eller[0]:q.y=np.float64(.15)
    p=Prototip(C.Ses(acik=False));p.baslat(a,0.);p.bekleme=.2
    for t in (0.,.61,1.,8.1,8.4):p.adim(a,t)
    assert p.aktif=={1} and p.k0 is not None
    for q in a.eller[1]:q.y=np.float64(.15)
    p.adim(a,8.5)
    assert p.puanlar==[0,1] and 'SAĞ' in p.mesaj
