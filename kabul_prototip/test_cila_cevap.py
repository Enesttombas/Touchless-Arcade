from cila_destek import *

def test_cevap_yagmuru_2005_gurultulu_kare():
    gurultu('p_cevap_yagmuru')


def test_cevap_kadraj_disinda_maske_roi_bos_olabilir(monkeypatch):
    import p_cevap_yagmuru as M
    monkeypatch.setattr(M,'maske_ver',lambda k:np.ones((C.Y,C.G),np.float32))
    a=algi(1)
    for q in a.pozlar[0]:q.y=np.float64(1.3)
    p=M.Prototip(C.Ses(acik=False));p.baslat(a,0.)
    assert p.isle(kamera(a),a,8.6).shape==(C.Y,C.G,3)


def test_cevap_kayipta_sure_ve_puan_donuyor():
    import p_cevap_yagmuru as M
    p=M.Prototip(C.Ses(acik=False));p.baslat(algi(1),0.)
    p.isle(kamera(algi(1)),algi(1),1.)
    for t in np.arange(1.1,3.,.1):p.isle(kamera(algi(0)),algi(0),float(t))
    assert p.soru_t>1. and p.skor==0 and p.durum=='oyun'


def test_kaybolan_oyuncu_kilitten_sonra_ceza_almaz():
    import p_cevap_yagmuru as M
    p=M.Prototip(C.Ses(acik=False));p.baslat(algi(2),0.)
    p.mod='Hayatta Kalma';p.kilit={10:1,11:1}
    p.soru['dogru_indeks']=0;p.kisi_guncelle(algi(1));p.puanla(9.)
    assert not p.oyuncular[11]['elendi']


def test_kamera_tam_ekran_zemin_olarak_aydinlik_kalir():
    import p_cevap_yagmuru as M
    a=algi(0);k=np.full((C.Y,C.G,3),160,np.uint8)
    out=M.Prototip(C.Ses(acik=False)).isle(k,a,0.)
    assert out[330:450,40:180].mean()>=160*.65
