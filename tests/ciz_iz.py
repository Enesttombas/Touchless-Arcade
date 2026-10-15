import math
from types import SimpleNamespace
import cv2
import numpy as np
from cila_destek import C
from goruntule import algi
import p_ciz_tahmin as M


def yol(ad,n=121):
    if ad=='daire':
        q=np.linspace(0,2*math.pi,n);return np.column_stack([640+130*np.cos(q),410+130*np.sin(q)])
    if ad=='yildiz':
        q=np.linspace(-math.pi/2,3*math.pi/2,11);r=np.array([160,70]*5+[160]);v=np.column_stack([640+r*np.cos(q),410+r*np.sin(q)])
    else:v=np.array([(490,550),(490,370),(640,270),(790,370),(790,550),(490,550)])
    uzun=np.r_[0,np.cumsum(np.linalg.norm(np.diff(v,axis=0),axis=1))];t=np.linspace(0,uzun[-1],n)
    return np.column_stack([np.interp(t,uzun,v[:,k]) for k in range(2)])


def oturum(ad,dt=1/15):
    rng=np.random.default_rng(77);son=[]
    for j,xy in enumerate(yol(ad)):
        a=algi(0) if j%10==6 else algi(1,x=(xy[0]+48)/C.G,y=xy[1]/C.Y,jest='Victory' if j%3 else 'Pointing_Up')
        for e in a.eller:
            for q in e:q.x+=rng.uniform(-6,6)/C.G;q.y+=rng.uniform(-6,6)/C.Y
        son.append((j*dt,a))
    return son


def oyun():
    p=M.Prototip(C.Ses(acik=False));p.mod='Seyirci';p.baslat(algi(1,y=.4),0.);return p


def kapsam(p,ad):
    dist=cv2.distanceTransform((~p.tuvaller[10].any(axis=2)).astype(np.uint8),cv2.DIST_L2,5)
    pts=yol(ad,2000).round().astype(int)
    return float(np.mean(dist[pts[:,1],pts[:,0]]<=12))


def tekrar(rows):
    p=oyun()
    for row in rows:
        a=C.Algi();a.eller=[[SimpleNamespace(x=x,y=y,z=z) for x,y,z in e] for e in row['eller']]
        a.el_id=row['el_id'];a.tahmini=[tuple(x) for x in row['tahmini']];p.ciz(a,row['t'])
    return p
