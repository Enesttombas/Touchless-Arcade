"""Yalnız yeni altı oyunda kullanılan küçük prosedürel görseller."""
import cv2
import numpy as np
from cekirdek import G,Y,SARI,BEYAZ,yazi_koy


def el_ikonu(kare,x,y,sekil,renk,olcek=1.):
    x,y,r=int(x),int(y),int(30*olcek)
    cv2.ellipse(kare,(x,y),(r,int(r*.9)),0,0,360,renk,-1,cv2.LINE_AA)
    n=4 if sekil=='kağıt' else 2 if sekil=='makas' else 0
    for i in range(4):
        dx=int((i-1.5)*r*.52);uzun=int(r*(2.2 if i<n else .6))
        a=(x+dx,y-int(r*.3));b=(x+dx,y-uzun)
        cv2.line(kare,a,b,renk,max(4,int(r*.4)),cv2.LINE_AA)
        cv2.circle(kare,b,max(2,int(r*.2)),renk,-1,cv2.LINE_AA)
    cv2.line(kare,(x-r,y),(x-int(1.35*r),y-r),renk,max(4,int(r*.5)),cv2.LINE_AA)
    cv2.line(kare,(x-r//2,y+r//2),(x+r//2,y+r//2),(40,50,70),2,cv2.LINE_AA)


def patlama(kare,x,y,t,renk=SARI):
    if not 0<=t<.7:return
    for i in range(18):
        a=i*2*np.pi/18;r=30+150*t
        p=(int(x+np.cos(a)*r),int(y+np.sin(a)*r+t*t*100))
        cv2.circle(kare,p,max(1,int(6*(1-t/.7))),renk,-1,cv2.LINE_AA)


def rozet(kare,x,y,skor):
    renk=(70,155,215) if skor<10 else (205,210,215) if skor<25 else SARI
    cv2.circle(kare,(int(x),int(y)),55,renk,-1,cv2.LINE_AA)
    cv2.circle(kare,(int(x),int(y)),45,BEYAZ,3,cv2.LINE_AA)
    yazi_koy(kare,'BRONZ' if skor<10 else 'GÜMÜŞ' if skor<25 else 'ALTIN',x,y-15,22,hiza='orta')
