import cv2
import numpy as np
from test_penalti import M,C,oyun,el,param,KARE


def test_tanitim_topa_dokunup_tek_parmakla_yol_cizer(monkeypatch):
    p=oyun();p.durum='bekle';calls=[];eller=[];tops=[]
    poly=cv2.polylines
    def yakala(k,pts,*args,**kwargs):
        calls.append(np.array(pts[0]).copy());return poly(k,pts,*args,**kwargs)
    monkeypatch.setattr(M.cv2,'polylines',yakala)
    monkeypatch.setattr(M,'el_ikonu',lambda k,x,y,sekil,*args:eller.append((x,y,sekil)))
    monkeypatch.setattr(p,'top_ciz',lambda k,pos,t:tops.append(pos.copy()))
    for t in (0.,.8,1.6):p.isle(KARE(),el(),t)
    assert len(calls)==3 and len(tops)==3
    assert all(np.array_equal(q[0],M.TOP.astype(int)) for q in calls)
    assert all(e[2]=='taş' for e in eller) and eller[-1][1]<eller[0][1]-150
    assert np.linalg.norm(calls[0][-1]-M.TOP)<2


def test_ucusta_fizik_yolunun_parlayan_izi_topa_kadar_surer(monkeypatch):
    p=oyun();p.sut(0.,param(falso=.8));calls=[];poly=cv2.polylines
    def yakala(k,pts,closed,color,width,*args,**kwargs):
        if tuple(color)==M.SARI:calls.append((np.array(pts[0]).copy(),width))
        return poly(k,pts,closed,color,width,*args,**kwargs)
    monkeypatch.setattr(M.cv2,'polylines',yakala)
    p.isle(KARE(),el(),.7)
    assert len(calls)>=2 and max(w for _,w in calls)>min(w for _,w in calls)
    for pts,_ in calls:
        assert len(pts)>12
        assert np.array_equal(pts[0],M.izdusus(p.fizik[0])[:2])
        assert np.linalg.norm(pts[-1]-np.asarray(M.izdusus(p.top_p)[:2]))<2
