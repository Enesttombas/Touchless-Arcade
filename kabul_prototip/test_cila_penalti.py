from cila_destek import *


def test_penalti_2005_gurultulu_kare():
    gurultu('p_penalti')


def test_kaleci_noktalari_gorunmezse_cokmez(monkeypatch):
    import p_penalti as M
    a=algi(2)
    for q in a.pozlar[1]:q.visibility=0.
    monkeypatch.setattr(M,'maske_ver',lambda k:np.ones((C.Y,C.G),np.float32))
    p=M.Prototip(C.Ses(acik=False));p.baslat(a,0.)
    assert p.isle(kamera(a),a,.1).shape==(C.Y,C.G,3)


def test_ivme_artinca_guc_artar():
    import p_penalti as M
    sabit=[(M.TOP+[0,-j*30],j*.1) for j in range(8)]
    ivmeli=[(M.TOP+[0,-j*30],j*.1 if j<4 else .3+(j-3)*.045) for j in range(8)]
    assert M.ciz_sut(ivmeli,200)['guc']>M.ciz_sut(sabit,200)['guc']


def test_kaleci_kayipta_ucus_cezasiz_bekler():
    import p_penalti as M
    a=algi(2);p=M.Prototip(C.Ses(acik=False));p.baslat(a,0.)
    p.sut(0.,dict(guc=.6,yatay=0.,dikey=M.merkez_acisi(.6),falso=0.))
    p.isle(kamera(a),a,.1)
    for t in np.arange(.2,2.,.1):p.isle(kamera(algi(0)),algi(0),float(t))
    assert p.faz=='ucus' and p.atilan==[0,0] and p.ucus_t>1.
