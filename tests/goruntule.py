"""Sentetik durum galerisi ve fareyle kamerasız deneme; kamera kanıtı değildir."""
import argparse
import importlib
import os
from pathlib import Path
import sys
import time
import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'oyunlar'))
import cekirdek as C

OYUNLAR=['p_cevap_yagmuru','p_penalti','p_refleks','p_tas_kagit','p_parmak_kusu','p_ciz_tahmin']
DURUMLAR=['bekle','hazir','oyun','olay','sonuc']


def el(x=.3,y=.6,jest='Pointing_Up',olcek=1.):
    e=C.sahte_el(x,y)
    for q in e:q.x,q.y=x,y+.18*olcek
    acik={'Pointing_Up':(1,0,0,0),'Victory':(1,1,0,0),'Open_Palm':(1,1,1,1),'Closed_Fist':(0,0,0,0)}.get(jest,(0,0,0,0))
    for f,m in enumerate((5,9,13,17)):
        dx=(f-1.5)*.025*olcek
        for j,dy in zip(range(m,m+4),(.1,.065,.03,0.) if acik[f] else (.1,.065,.105,.14)):
            e[j].x,e[j].y=x+dx,y+dy*olcek
    for j in (1,2,3,4):e[j].x,e[j].y=x-.08*olcek,y+.12*olcek
    for q in e:q.x,q.y=np.float64(q.x),np.float64(q.y)
    return e


def algi(n=2,x=.3,y=.6,jest='Pointing_Up'):
    v=C.Algi()
    for i in range(n):
        cx=x if i==0 else .7 if i==1 else .1+i*.15
        e=el(cx,y,jest);p=C.sahte_poz()
        for q in p:q.x,q.y,q.visibility=cx,.55,.95
        for j in (11,23,15,27):p[j].x=cx-.035
        for j in (12,24,16,28):p[j].x=cx+.035
        for j in (11,12):p[j].y=.35
        for j in (27,28):p[j].y=.92
        p[0].y=.23
        for q in e+p:q.x,q.y=np.float64(q.x),np.float64(q.y)
        v.eller.append(e);v.pozlar.append(p)
        v.el_id.append(10+i);v.poz_id.append(10+i)
        v.jestler.append(jest);v.jest_skor.append(.9)
        v.yuzler.append(C.sahte_yuz(cx,.23,.08));v.yuz_id.append(10+i)
    return v


def kamera(a):
    k=np.full((C.Y,C.G,3),(75,90,100),np.uint8)
    for x in range(0,C.G,80):cv2.line(k,(x,0),(x,C.Y),(100,110,115),3)
    for i,p in enumerate(a.pozlar):
        cx=int(p[0].x*C.G)
        cv2.circle(k,(cx,180),38,(160,180,210),-1)
        cv2.rectangle(k,(cx-45,220),(cx+45,500),(130+30*(i%2),90,60),-1)
        cv2.line(k,(cx-25,500),(cx-30,665),(160,150,130),22)
        cv2.line(k,(cx+25,500),(cx+30,665),(160,150,130),22)
    return k


def modele_girme():
    # Görsel/gürültü testinde segmentasyon değil oyun katmanı ölçülür.
    import p_cevap_yagmuru as m
    m._maskeci=type('Maske',(),{'ver':lambda s,k:None})()
    import p_penalti as p
    p.maske_ver=lambda k:None


def sahne(ad,durum):
    p=importlib.import_module(ad).Prototip(C.Ses(acik=False));a=algi();p.baslat(a,0.)
    t=.6
    if durum=='bekle':p.durum='bekle'
    elif durum=='hazir':p.durum,p.durum_t='hazir',0.
    elif durum=='sonuc':
        if ad=='p_cevap_yagmuru':p.podyum(0.)
        else:p.bitir(0.,'SOL KAZANDI / 120 PUAN')
    elif ad=='p_cevap_yagmuru':
        p.soru=dict(soru='Güneş sisteminin en büyük gezegeni hangisidir?',secenekler=['Jüpiter','Mars','Dünya'],dogru_indeks=0)
        t=8.7 if durum=='olay' else 6.
    elif ad=='p_penalti':
        p.sut(0.,dict(guc=.6,yatay=0.,dikey=7.,falso=.4))
        if durum=='olay':p.atis_sonuc('GOL',.5)
    elif ad=='p_refleks':
        a=algi(y=.75);a.eller=[];a.el_id=[]
        p.baslat(a,0.);p.bekleme=1.5 if durum=='olay' else 4.
        p.adim(a,0.);p.adim(a,.6);t=.7
        if durum=='olay':p.adim(a,2.11);t=2.12
        if durum=='bekle':p.durum='bekle'
        elif durum=='hazir':p.durum,p.durum_t='hazir',0.
        elif durum=='sonuc':p.bitir(0.,'SOL KAZANDI')
    elif ad=='p_tas_kagit':
        a=algi(jest='Closed_Fist');a.eller[1]=el(.7,.6,'Victory');a.jestler=['Closed_Fist','Victory'];t=3.7 if durum=='olay' else 1.2
        if durum=='olay':p.adim(a,3.2)
    elif ad=='p_parmak_kusu':
        p.sutunlar[0]['x']=700
        if durum=='olay':
            p.skor=8;p.olum_t=.5
            next(iter(p.kuslar.values()))['canli']=False
            p.bitir(.5,'ÇARPIŞMA / 8 PUAN')
    elif ad=='p_ciz_tahmin':
        p.mod='Düello';p.baslat(a,0.)
        for i in p.ids:
            p.cizimler[i]=[[(100,250),(160,210),(220,250),(220,340),(100,340),(100,250)]]
            cv2.polylines(p.tuvaller[i],[np.array(p.cizimler[i][0],np.int32)+(640 if i==11 else 0,0)],False,C.CAMGOBEGI,5)
            p.tahminler[i]=[('ev',.73),('gitar',.15),('anahtar',.08)]
        p.tahmin_t=t
        if durum=='olay':p.bildi(10,.5)
    return p,a,t


def galeri(ad,out):
    modele_girme();out.mkdir(parents=True,exist_ok=True);mini=[]
    for durum in DURUMLAR:
        p,a,t=sahne(ad,durum)
        for j in range(3):
            k=p.isle(kamera(a),a,t+j/60)
            cv2.imwrite(str(out/f'{ad}_{durum}_{j}.png'),k)
            if j==2:
                cv2.imwrite(str(out/f'{ad}_{durum}.png'),k)
                b=cv2.resize(k,(640,360));cv2.putText(b,durum,(12,345),cv2.FONT_HERSHEY_SIMPLEX,.7,(255,255,255),2);mini.append(b)
    grid=np.zeros((1080,1280,3),np.uint8)
    for i,b in enumerate(mini):grid[(i//2)*360:(i//2+1)*360,(i%2)*640:(i%2+1)*640]=b
    path=out/f'{ad}_galeri.png';cv2.imwrite(str(path),grid);print(path,flush=True)


def fare(ad):
    """Fare: parmak; sol tuş çiz/çek, sağ tuş avuç, V makas; P iki kişi."""
    modele_girme();p=importlib.import_module(ad).Prototip(C.Ses(acik=True));pos=[640,350];dur=['Closed_Fist' if ad=='p_ciz_tahmin' else 'Pointing_Up'];n=[1]
    def hareket(ev,x,y,flags,param):
        pos[:]=[x,y]
        dur[0]='Open_Palm' if flags&cv2.EVENT_FLAG_RBUTTON else 'Pointing_Up' if ad!='p_ciz_tahmin' or flags&cv2.EVENT_FLAG_LBUTTON else 'Closed_Fist'
    w='Fare - '+p.AD;cv2.namedWindow(w,cv2.WINDOW_NORMAL);cv2.setMouseCallback(w,hareket)
    try:
        while True:
            a=algi(n[0],pos[0]/C.G+.0375,pos[1]/C.Y,dur[0]);t=time.monotonic()
            k=p.isle(kamera(a),a,t)
            C.yazi_koy(k,'Fare: parmak / V: makas / F: taş / A: avuç / P: iki kişi / Q: çık',C.G//2,690,26,hiza='orta')
            cv2.imshow(w,k);key=cv2.waitKey(16)&255
            if key in (27,ord('q')) or cv2.getWindowProperty(w,cv2.WND_PROP_VISIBLE)<1:break
            if key==ord('v'):dur[0]='Victory'
            elif key==ord('f'):dur[0]='Closed_Fist'
            elif key==ord('a'):dur[0]='Open_Palm'
            elif key==ord('p'):n[0]=3-n[0]
            elif key!=255:p.tus(key)
    finally:cv2.destroyAllWindows()


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('oyun',choices=OYUNLAR);ap.add_argument('--fare',action='store_true')
    ap.add_argument('--cikti',type=Path,default=Path(os.environ['TEMP'])/'cila_kareler')
    args=ap.parse_args()
    if args.fare or os.environ.get('FARE_EL')=='1':fare(args.oyun)
    else:galeri(args.oyun,args.cikti)
