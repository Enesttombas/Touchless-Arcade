import json
import numpy as np
import pytest
from test_ozel import C,KARE,algi
import p_ciz_tahmin as M


def a(n=1,jest='Pointing_Up',x=.3,y=.4):
    from goruntule import el
    v=algi([el(x+i*.5,y,jest) for i in range(n)],[jest]*n)
    v.el_id=list(range(10,10+n));return v


def oyun(mod='YZ Tahmin',n=1):
    p=M.Prototip(C.Ses(acik=False));p.mod=mod;p.baslat(a(n),0.);return p


def kare():return [[(0,0),(100,0),(100,100),(0,100),(0,0)]]


def test_onisleme_28_ortalanmis_aspect_ve_kalinlik():
    x=M.onisle(kare())[0,0]
    assert x.shape==(28,28) and x.max()<=1
    ys,xs=np.where(x>.4)
    assert abs((xs.min()+xs.max())/2-13.5)<1
    assert xs.max()-xs.min()==ys.max()-ys.min()
    assert not x[0].any() and not x[-1].any()
    with pytest.raises(ValueError):M.onisle([[(float('nan'),0),(10,10)]])


def test_bos_cizim_modele_gonderilmez():
    p=oyun();calls=[]
    p.model=type('Model',(),{'tahmin':lambda s,x:calls.append(x) or []})()
    p.adim(algi(),.3)
    assert calls==[] and p.tahminler[10]==[] and M.onisle([]) is None


def test_ayrilmis_200_ornek_onnx_dogruluk():
    yol=M.KOK/'modeller/ciz_tanima.onnx';test=M.KOK/'modeller/ciz_test200.npz'
    if not yol.exists() or not test.exists():pytest.skip('Eğitilmiş yerel model/kabul verisi henüz yok')
    model=M.CizModel(yol);d=np.load(test);n=0
    for x,y in zip(d['x'],d['y']):
        tahmin=model.tahmin(x[None].astype(np.float32)/255)
        n+=tahmin[0][0]==M.KELIMELER[int(y)]['tr']
    assert len(d['x'])==200 and n/200>=.85,f'{n}/200'


def test_sahte_dogru_tahmin_ve_sure_puani():
    p=oyun();p.cizimler[10]=kare()
    p.model=type('Model',(),{'tahmin':lambda s,x:[(p.hedef['tr'],.7)]})()
    p.adim(algi(),5.)
    assert p.faz=='bildim' and p.kazanan==10 and p.skor==150


def test_20sn_bilinemedi_uc_kelime_sonuc():
    p=oyun();p.model=None
    for i in range(3):
        bitis=p.kelime_t+20.01
        p.adim(algi(),bitis)
        assert p.faz=='bilinemedi'
        p.adim(algi(),bitis+2.01)
    assert p.durum=='sonuc' and p.skor==0


def test_bukme_kalemi_kaldirir_avuc_geri_al_ve_siler():
    p=oyun()
    p.ciz(a(x=.3));p.ciz(a(x=.32))
    assert sum(map(len,p.cizimler[10]))>=2
    no=sum(map(len,p.cizimler[10]))
    for _ in range(4):p.ciz(a(jest='Closed_Fist',x=.35))
    assert sum(map(len,p.cizimler[10]))==no and 10 not in p.kalem
    p.ciz(a(jest='Victory',x=.37));p.ciz(a(jest='Victory',x=.38))
    assert len(p.cizimler[10])==2
    p.ciz(a(jest='Open_Palm'),1.);p.ciz(a(jest='Open_Palm'),2.01)
    assert len(p.cizimler[10])==1
    p.ciz(a(jest='Open_Palm'),3.01)
    assert p.cizimler[10]==[] and not p.tuvaller[10].any()


def test_duello_ayri_tuval_kimlik_ve_ilk_bilen():
    p=oyun('Düello',2)
    p.ciz(a(2,x=.2));p.ciz(a(2,x=.22))
    assert len(p.cizimler[10][0])>=2 and len(p.cizimler[11][0])>=2
    assert not np.array_equal(p.tuvaller[10],p.tuvaller[11])
    p.model=type('Model',(),{'tahmin':lambda s,x:[(p.hedef['tr'],.7)]})()
    p.cizimler[10]=[]
    p.adim(algi(),1.)
    assert p.kazanan==11 and p.puanlar[11]>0 and p.puanlar[10]==0


def test_seyirci_d_kelimeyi_acar():
    p=oyun('Seyirci');p.onceki_t=4.
    p.tus(ord('D'))
    assert p.faz=='bildim' and p.kazanan==10 and p.skor==160


def test_model_yokken_yz_gizlenir(monkeypatch):
    monkeypatch.setattr(M.Path,'exists',lambda p:False)
    p=M.Prototip(C.Ses(acik=False))
    assert p.modlar==['Seyirci'] and p.mod=='Seyirci'


def test_model_guven_esigi_ve_dort_hz():
    p=oyun();p.cizimler[10]=kare();calls=[]
    p.model=type('Model',(),{'tahmin':lambda s,x:calls.append(x) or [(p.hedef['tr'],.59)]})()
    for t in (.01,.1,.2,.26,.3):p.adim(algi(),t)
    assert len(calls)==2 and p.faz=='ciz'


def test_menu_karti_ve_neon_cizim():
    import stant_app as S
    u=S.StantUygulama(C.Ses(acik=False));u.tus(ord('9'),0.)
    assert u._ornek(8).AD=='Çizim Kâhini'
    p=oyun('Seyirci');p.ciz(a(x=.3));p.ciz(a(x=.35))
    assert p.isle(KARE(),a(x=.37),.1).shape==(C.Y,C.G,3)


def test_geri_sayimda_el_kaybolursa_bos_oyun_baslamaz():
    p=M.Prototip(C.Ses(acik=False));p.durum,p.durum_t='hazir',0.
    p.isle(KARE(),algi(),3.1)
    assert p.durum=='bekle'


def test_canli_kabul_on_kelimeyi_sayip_tamamlar():
    p=M.Prototip(C.Ses(acik=False));p.KELIME_SAYISI=10;p.TUR_SN=240.
    p.baslat(a(),0.);p.model=None
    for n in range(10):
        bitis=p.kelime_t+20.01
        if n<7:p.bildi(10,p.kelime_t+5.)
        else:p.adim(algi(),bitis)
        p.adim(algi(),(p.faz_t)+2.01)
    assert p.durum=='sonuc' and len(p.canli_sonuclar)==10
    assert sum(s['bildi'] for s in p.canli_sonuclar)==7
