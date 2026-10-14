"""Gerçek algı tipleri/kaybı ve oyun sınırlarında regresyon kontrolleri."""
import importlib
import numpy as np
from goruntule import algi,kamera,modele_girme
from test_ozel import C


def gurultu(ad):
    modele_girme();p=importlib.import_module(ad).Prototip(C.Ses(acik=False))
    rng=np.random.default_rng(49);t=0.
    for j in range(2005):
        t+=float(rng.uniform(1/60,1/8));n=0 if j%5 in (0,1) or 400<=j%500<420 else int(rng.integers(1,7))
        jest=('Pointing_Up','Open_Palm','Victory','Closed_Fist')[(j//20)%4]
        x=.3+.08*np.sin(j/15) if j%80<25 else float(rng.uniform(-.2,1.2))
        y=.6+.05*np.cos(j/15) if j%80<25 else float(rng.uniform(-.2,1.2))
        a=algi(n,x=x,y=y,jest=jest)
        for e in a.eller:
            for q in e:q.x=np.float64(q.x+rng.normal(0,.003));q.y=np.float64(q.y+rng.normal(0,.003))
        a.jestler=[rng.choice([None,'Victory','Pointing_Up','Open_Palm','Closed_Fist']) for _ in a.eller]
        for pz in a.pozlar:
            for q in pz:
                q.x=np.float64(q.x+rng.normal(0,.018));q.y=np.float64(q.y+rng.normal(0,.018))
        if j%300==0:p.baslat(algi(),t)
        out=p.isle(kamera(a),a,t)
        assert out.shape==(C.Y,C.G,3) and out.dtype==np.uint8
    return p


