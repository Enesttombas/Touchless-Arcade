import numpy as np
import pytest
from test_ozel import C,KARE,algi
from test_cevap_yagmuru import a as beden
import p_penalti as M


def el(x=M.TOP[0],y=M.TOP[1],id=10):
    from goruntule import el as el_nokta
    a=algi([el_nokta(x/C.G+.0375,y/C.Y,'Pointing_Up')])
    a.el_id=[] if id is None else [id]
    return a


def oyun():
    p=M.Prototip(C.Ses(acik=False));p.baslat(el(),0.);return p


def param(guc=.6,falso=0.):
    return dict(guc=guc,yatay=0.,dikey=M.merkez_acisi(guc),falso=falso)


def test_kilit_sure_ve_kimlik_sarti():
    p=oyun();p.kontrol(el(),0.,.03);p.kontrol(el(),.1,.03)
    assert p.faz=='bekle'
    p.kontrol(el(),.16,.03);assert p.faz=='ciz'
    q=oyun();q.kontrol(el(id=None),0.,.03);q.kontrol(el(id=None),1.,.03)
    assert q.faz=='bekle'


def test_cizilen_yon_sapan_gibi_tersine_donmez():
    a=M.ciz_sut([(M.TOP,0.),(M.TOP+[0,-200],.6)],200)
    assert abs(a['yatay'])<2 and a['falso']==0
    b=M.ciz_sut([(M.TOP,0.),(M.TOP+[-70,-200],.6)],200)
    assert b['yatay']<0


def test_kavis_isareti_ve_alti_ornek():
    yol=[M.TOP+[30*np.sin(np.pi*t),100*t] for t in np.linspace(0,1,9)]
    assert M.falso(yol)<0
    assert M.falso([M.TOP,M.TOP+[0,100]])==0
    assert M.falso([p*np.array([-1,1]) for p in yol])>0


def test_guc_hiz_ve_sinirlar():
    a=M.ciz_sut([(M.TOP,0.),(M.TOP+[0,-200],2.)],200)
    b=M.ciz_sut([(M.TOP,0.),(M.TOP+[0,-200],.2)],200)
    assert M.ucus(a)[1]<M.ucus(b)[1]
    assert .25<=a['guc']<b['guc']<=1.


def test_yol_bitince_durmak_sut_atarken_cizimde_atmaz():
    p=oyun();p.kontrol(el(),0.,.03);p.kontrol(el(),.31,.03)
    for j in range(1,10):p.kontrol(el(y=M.TOP[1]-j*28),.31+j/15,1/15)
    assert p.faz=='ciz'
    for j in range(5):p.kontrol(el(y=M.TOP[1]-252),1.0+j*.1,.1)
    assert p.faz=='ucus' and p.param['dikey']>=0


def test_fizik_merkez_falso_ve_sabit_adim():
    yol,_=M.ucus(param())
    assert abs(yol[-1,0])<.01 and abs(yol[-1,1]-1.22)<.1 and yol[-1,2]==pytest.approx(11)
    sag,_=M.ucus(param(falso=.8));sol,_=M.ucus(param(falso=-.8))
    assert sag[-1,0]>0 and sol[-1,0]<0
    assert abs(sag[-1,0]+sol[-1,0])<.01


def test_30_60_kare_ayni_inis():
    sonlar=[]
    for fps in (30,60):
        p=oyun();p.ucus_sn=1.3;p.sut(0.,param())
        for i in range(int(1.3*fps)+2):p.isle(KARE(),el(),i/fps)
        sonlar.append(p.top_p)
    assert np.linalg.norm(sonlar[0]-sonlar[1])<.05


def test_gecikme_dort_kati_ve_yavas_ucus():
    p=oyun();p.gecikme=.3;p.ucus_sn=max(1.3,4*p.gecikme)
    p.sut(0.,param());p.isle(KARE(),el(),1.19)
    assert p.faz=='ucus' and p.ucus_sn>=1.2


def test_kaleci_tutus_govde_gol_direk():
    assert M.kale_karari([0,1.2,11],[(0,1.2)])=='Tutuş'
    assert M.kale_karari([0,1.2,11],govde=lambda x,y: True)=='Sektirme'
    assert M.kale_karari([2,1.2,11])=='GOL'
    assert M.kale_karari([3.66,1.2,11])=='Direk'
    assert M.kale_karari([0,3,11])=='Dışarı'


def test_duello_bes_atis_rol_degisim_ve_seri():
    p=oyun();p.ids=[1,2];p.fizik=M.ucus(param())[0]
    for i in range(10):
        rol=p.rol;p.atis_sonuc('GOL',i*3.)
        assert p.atilan[rol]==i//2+1
        p.isle(KARE(),algi(),i*3.+2.1)
        assert p.rol!=rol
    assert p.durum=='oyun' and p.atilan==[5,5] and p.goller==[5,5]
    p.atis_sonuc('GOL',31.);p.isle(KARE(),algi(),33.1)
    p.atis_sonuc('Dışarı',34.)
    assert p.durum=='sonuc' and p.goller==[6,5]


def test_yz_sag_ogrenmesi():
    p=oyun();p.rng=np.random.default_rng(4);p.gecmis.extend([1]*5)
    assert sum(p.yz_sec()==1 for _ in range(1000))/1000>=.6


def test_frikik_baraj_falso_gecer():
    p=oyun();p.mod='Frikik'
    p.fizik=M.ucus(param())[0]
    assert p.karar(algi(),KARE(),1.)=='Baraj'
    p.fizik=M.ucus(param(guc=.6,falso=.9))[0]
    assert p.karar(algi(),KARE(),1.)!='Baraj'


def test_el_kaybi_ve_durgun_iptal_hak_yakmaz():
    p=oyun();p.kontrol(el(),0.,.03);p.kontrol(el(),.31,.03)
    p.kontrol(algi(),.4,.03);assert p.faz=='ciz'  # tek kare kayıp tolere edilir
    p.kontrol(algi(),.75,.03)
    assert p.faz=='bekle' and p.atilan==[0,0]
    p.kontrol(el(),1.,.03);p.kontrol(el(),1.31,.03);p.kontrol(el(),3.5,.03)
    assert p.faz=='bekle' and p.atilan==[0,0]


def test_kaleci_kayip_04sn_ve_boy_normalizasyon():
    p=oyun();p.ids=[1,2]
    a=beden(.2,.8);q=p.kaleci(a,1.)
    assert q is not None and p.kaleci(algi(),1.39) is q
    assert p.kaleci(algi(),1.41) is None
    _,konum=p.kaleci_noktalar(q)
    assert konum(0)[1]==pytest.approx(1.9)


def test_ag_titresimi_ve_menu_karti():
    ag=M.Ag();ag.vur(0,1.2);before=ag.z.copy();ag.adim(.1)
    assert not np.array_equal(before,ag.z) and np.isfinite(ag.z).all()
    assert not ag.z[[0,-1]].any()
    import stant_app as S
    u=S.StantUygulama(C.Ses(acik=False));u.tus(ord('8'),0.)
    assert u._ornek(7).AD=='Altın Vuruş'


def test_kaleci_challenge_on_atis_skoru():
    p=oyun();p.baslat(beden(.5),0.)
    assert p.challenge
    p.fizik=M.ucus(param())[0]
    for i in range(10):p.atis_sonuc('Tutuş',i)
    assert p.durum=='sonuc' and p.skor==10


def test_tek_hareket_tek_sut_parmak_topta_kalsa_da():
    # Enes 2026-10-13/15: "topu atıyorum 2 kez gidiyor". Dokun, çiz, dur, parmak topta 3 sn kalsın.
    p=oyun();sayac=[];asil=p.sut
    p.sut=lambda simdi,param=None:(sayac.append(simdi),asil(simdi,param))
    p.kontrol(el(),0.,.03);p.kontrol(el(),.16,.03)
    for j in range(1,8):p.kontrol(el(y=M.TOP[1]-j*35),.16+j/15,1/15)
    for j in range(4):p.kontrol(el(y=M.TOP[1]-245),.7+j*.1,.1)
    assert len(sayac)==1
    p.atis_sonuc('GOL',2.);p.isle(KARE(),el(),4.1)
    t=4.2
    while t<7.2:p.kontrol(el(),t,1/15);t+=1/15
    assert len(sayac)==1 and p.atilan[0]==1 and p.faz=='bekle'
    p.kontrol(el(y=M.TOP[1]-200),7.3,.1)
    p.kontrol(el(),7.4,.1);p.kontrol(el(),7.6,.1)
    assert p.faz=='ciz'


def test_hizli_fiske_ve_el_kaybi_sut_sayilir_rastgele_sallama_saymaz():
    rng=np.random.default_rng(3);tamam=0
    for n in range(20):
        p=oyun();t=0.
        p.kontrol(el(),t,1/15);t+=.16;p.kontrol(el(),t,1/15)
        dx=rng.uniform(-150,150)
        for j in range(1,4):
            t+=1/15
            if rng.random()<.1:p.kontrol(algi(),t,1/15);continue
            p.kontrol(el(x=M.TOP[0]+dx*j/3+rng.uniform(-6,6),y=M.TOP[1]-j*60+rng.uniform(-6,6)),t,1/15)
        p.kontrol(algi(),t+1/15,1/15)  # fiske sonunda el bulanıp kaybolur
        tamam+=p.faz=='ucus' and p.atilan==[0,0]
    assert tamam>=19
    p=oyun()
    for j in range(60):p.kontrol(el(x=200+rng.uniform(-80,80),y=250+rng.uniform(-80,80)),j/15,1/15)
    assert p.faz=='bekle' and p.fizik is None


def test_cizilen_nokta_nisan_noktasidir():
    sag=M.ciz_sut([(M.TOP,0.),(M.TOP+[260,-330],.5)],200)
    yol,_=M.ucus(sag)
    assert 2.6<yol[-1,0]<3.66 and yol[-1,1]>1.
    alt=M.ciz_sut([(M.TOP,0.),(M.TOP+[0,-100],.15)],200)
    assert 0<M.ucus(alt)[0][-1,1]<2.44


def test_sanal_kaleci_adil_ve_cizimle_tutarli():
    rng=np.random.default_rng(11);kurtaris=0;n=200
    for _ in range(n):
        p=oyun();p.rng=rng;p.sanal.rng=rng;p.yz_yon=p.yz_sec()
        hx=rng.uniform(-3.4,3.4);hy=rng.uniform(.3,2.2)
        p.sut(0.,M.ciz_sut([(M.TOP,0.),(M.TOP+[hx*M.EKRAN_OLCEK,-(240+(hy-.6)*M.EKRAN_OLCEK)],.45)],200))
        karar=p.karar(algi(),KARE(),1.5)
        eld=p.sanal.eldivenler()
        degdi=any(np.linalg.norm(p.fizik[-1,:2]-g)<=.18+M.R for g in eld)
        assert (karar=='Tutuş')==(degdi and karar not in ('Direk','Dışarı'))
        kurtaris+=karar=='Tutuş'
    assert .2<=kurtaris/n<=.4, kurtaris/n


def test_sanal_kaleci_aldatir_atlar_ve_yere_duser():
    k=M.SanalKaleci(np.random.default_rng(0))
    fizik,_=M.ucus(dict(guc=.7,yatay=12.,dikey=M.hedef_acisi(.7,1.),falso=0.))
    k.planla(fizik,1)
    bas=k.poz(10.,10.,1.3)[0]
    aldat=k.poz(10.9,10.,1.3)[0]
    atla=k.poz(11.3,10.,1.3)
    yer=k.poz(11.8,10.,1.3)
    assert aldat[0]<bas[0]-.1  # önce ters tarafa
    assert atla[0][0]>.8 and abs(atla[1][0])>.5  # sonra uzanarak köşeye
    assert yer[3]>.9 and yer[0][1]<atla[0][1]
    kare=KARE();k.ciz(kare,11.3,10.,1.3);assert kare.any()
