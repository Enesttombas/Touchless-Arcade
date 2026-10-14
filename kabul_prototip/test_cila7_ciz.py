import json
import pytest
from ciz_iz import *
from oyuncu import OyuncuKapisi


@pytest.mark.parametrize('ad',['daire','yildiz','ev'])
def test_gurultulu_iz_yuzde92_ve_tani_tekrar(ad,tmp_path,monkeypatch):
    monkeypatch.setenv('CIZ_TANI','1');monkeypatch.setattr(M,'TANI_YOL',tmp_path/(ad+'.jsonl'))
    p=oyun()
    for t,a in oturum(ad):p.ciz(a,t)
    assert kapsam(p,ad)>=.92
    assert len(p.cizimler[10])-1<=1
    rows=[json.loads(x) for x in M.TANI_YOL.read_text(encoding='utf-8').splitlines()]
    p2=tekrar(rows)
    assert p.cizimler==p2.cizimler and np.array_equal(p.tuvaller[10],p2.tuvaller[10])
    assert len(rows)==121 and not any('goruntu' in x for x in rows)


def test_iki_kare_inis_ilk_murekkep_150ms():
    p=oyun();p.ciz(algi(1,y=.4),0.);assert 10 not in p.kalem
    p.ciz(algi(1,y=.4),.125)
    assert 10 in p.kalem and p.tuvaller[10].any()


def test_kalkis_dort_kare_orta_parmak_serbest():
    p=oyun()
    for t in (0.,.05):p.ciz(algi(1,y=.4,jest='Victory'),t)
    assert 10 in p.kalem
    for t in (.1,.15,.2):p.ciz(algi(1,y=.4,jest='Closed_Fist'),t);assert 10 in p.kalem
    p.ciz(algi(1,y=.4,jest='Closed_Fist'),.25);assert 10 not in p.kalem


def test_kisa_kayip_ara_noktalari_doldurur():
    p=oyun()
    for t,x in ((0.,.3),(.1,.31)):p.ciz(algi(1,x=x,y=.4),t)
    p.ciz(algi(0),.3);p.ciz(algi(1,x=.34,y=.4),.4)
    assert len(p.cizimler[10])==1 and len(p.cizimler[10][0])>10


@pytest.mark.parametrize('dt,dx',[(1/15,170),(1/8,220)])
def test_dusuk_fps_kopma_esigi_olceklenir(dt,dx):
    p=oyun()
    for j in range(12):p.ciz(algi(1,x=(300+(j%2)*dx+48)/C.G,y=.5),j*dt)
    assert len(p.cizimler[10])==1 and p.tuvaller[10].any()


def test_avuc_bir_sn_son_cizgi_iki_sn_tumunu_siler():
    p=oyun()
    for t in (0.,.05):p.ciz(algi(1,x=.3,y=.4),t)
    for t in (.1,.15,.2,.25):p.ciz(algi(1,y=.4,jest='Closed_Fist'),t)
    for t in (.3,.35):p.ciz(algi(1,x=.5,y=.4),t)
    assert len(p.cizimler[10])==2
    for t in (.4,1.41):p.ciz(algi(1,y=.4,jest='Open_Palm'),t)
    assert len(p.cizimler[10])==1 and p.tuvaller[10].any()
    p.ciz(algi(1,y=.4,jest='Open_Palm'),2.41)
    assert not p.cizimler[10] and not p.tuvaller[10].any()


def test_tani_gercek_kapi_kucuk_el_reddini_kaydeder(tmp_path,monkeypatch):
    monkeypatch.setenv('CIZ_TANI','1');monkeypatch.setattr(M,'TANI_YOL',tmp_path/'tani.jsonl')
    p=oyun();k=OyuncuKapisi();a=algi(1,x=.5,y=.4);a.yuzler=[];a.pozlar=[]
    for e in a.eller:
        for q in e:q.x=.5+(q.x-.5)*.1;q.y=.4+(q.y-.4)*.1
    p.ciz(k.suz(a,0.),0.)
    r=json.loads(M.TANI_YOL.read_text(encoding='utf-8'))
    assert r['ham_el']==1 and not r['kapidan_gecti'] and r['kapi_redleri']==['küçük']


def test_ilk_iki_nokta_sicrarsa_araya_murekkep_cekilmez():
    p=oyun();p.ciz(algi(1,x=.2,y=.4),0.);p.ciz(algi(1,x=.8,y=.4),.1)
    assert not p.tuvaller[10].any()
    p.ciz(algi(1,x=.81,y=.4),.2)
    assert not p.tuvaller[10][:,500:700].any()


@pytest.mark.parametrize('ad',['daire','yildiz','ev'])
def test_fare_el_yolu_uc_sekil(ad,tmp_path,monkeypatch):
    import goruntule as F
    p=oyun();monkeypatch.setenv('FARE_EL','1');monkeypatch.setattr(M,'Prototip',lambda ses:p)
    sessiz=C.Ses(acik=False);monkeypatch.setattr(C,'Ses',lambda **kwargs:sessiz)
    callback=[];sayac=[0];cikti=[];pts=yol(ad).round().astype(int)
    monkeypatch.setattr(F.cv2,'namedWindow',lambda *args:None)
    monkeypatch.setattr(F.cv2,'setMouseCallback',lambda w,fn:callback.append(fn))
    monkeypatch.setattr(F.cv2,'getWindowProperty',lambda *args:1)
    monkeypatch.setattr(F.cv2,'destroyAllWindows',lambda:None)
    monkeypatch.setattr(F.cv2,'imshow',lambda w,k:cikti.append(k.copy()))
    monkeypatch.setattr(F.time,'monotonic',lambda:sayac[0]/15)
    def tus(ms):
        j=sayac[0];sayac[0]+=1
        if j>=len(pts):return ord('q')
        callback[0](F.cv2.EVENT_MOUSEMOVE,int(pts[j,0]),int(pts[j,1]),F.cv2.EVENT_FLAG_LBUTTON,None)
        return 255
    monkeypatch.setattr(F.cv2,'waitKey',tus)
    F.fare('p_ciz_tahmin')
    assert kapsam(p,ad)>=.92 and len(p.cizimler[10])==1
    assert F.cv2.imwrite(str(tmp_path/(ad+'_fare.png')),cikti[-1])
