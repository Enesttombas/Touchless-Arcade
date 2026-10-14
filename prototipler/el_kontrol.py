"""Yeni oyunlar için dönmeye dayanıklı, nokta tabanlı parmak açıklığı."""
import numpy as np
from cekirdek import px


def parmaklar(el):
    p=np.array([px(el,j) for j in range(21)],dtype=float)
    if not np.isfinite(p).all() or np.linalg.norm(p[9]-p[0])<8:
        return None
    acik=[]
    for m in (5,9,13,17):
        a,b=p[m]-p[m+1],p[m+3]-p[m+1]
        norm=np.linalg.norm(a)*np.linalg.norm(b)
        acik.append(bool(norm>1 and np.dot(a,b)/norm<-.5 and np.linalg.norm(p[m+3]-p[0])>1.12*np.linalg.norm(p[m+1]-p[0])))
    return tuple(acik)


def sekil(el):
    acik=parmaklar(el)
    if acik is None:return None
    if not any(acik):return 'taş'
    if all(acik):return 'kağıt'
    if acik==(True,True,False,False):return 'makas'
    return None
