"""Kimlikli iki yuva, 3'te 2 raunt ve yalnız RAM'de kısa tekrar."""
from collections import deque
import cv2
import numpy as np
from cekirdek import G,Y,SARI,BEYAZ,CAMGOBEGI,PEMBE,px,yazi_koy
from oyun_akis import OyunAkisi


def erken_kare(kareler):
    if not kareler:
        return None
    en = min(kareler.values())
    aday = [i for i,k in kareler.items() if k==en]
    return aday[0] if len(aday)==1 else None


class Tekrar:
    def __init__(self, fps=60):
        self.kareler = deque(maxlen=max(1,int(1.5*fps)))

    def ekle(self,kare,simdi):
        self.kareler.append((simdi, cv2.resize(kare,(320,180))))
        while self.kareler and simdi-self.kareler[0][0] > 1.5:
            self.kareler.popleft()

    def goruntu(self,gecen):
        if not self.kareler:
            return None
        i=min(len(self.kareler)-1,int(gecen*len(self.kareler)/3))
        return self.kareler[i][1]


class Rekabet(OyunAkisi):
    TUR_SN = 180.

    def __init__(self,ses):
        super().__init__(ses)
        self.yuvalar, self.puanlar = [], [0,0]
        self.raunt, self.raunt_t = 0, 0.
        self.mesaj, self.ara_t = '', None
        self.kare_no, self.dtler = 0, deque(maxlen=60)
        self.tekrar, self.donmus = Tekrar(), None
        self.kazanan = None
        self.rng = np.random.default_rng()

    def baslat(self,algi,simdi):
        super().baslat(algi,simdi)
        ids=getattr(algi,'el_id',[]) or list(range(len(algi.eller)))
        self.yuvalar=[i for i,e in sorted(zip(ids,algi.eller),key=lambda z:px(z[1],9)[0])][:2]
        self.puanlar, self.kazanan = [0,0], None
        self.raunt=0
        self.yeni_raunt(simdi)

    def yeni_raunt(self,simdi):
        self.raunt+=1
        self.raunt_t,self.ara_t,self.mesaj=simdi,None,''
        self.tekrar=Tekrar()
        self.donmus=None

    def eller(self,algi):
        ids=getattr(algi,'el_id',[]) or list(range(len(algi.eller)))
        return {self.yuvalar.index(i):(e,j) for j,(i,e) in enumerate(zip(ids,algi.eller))
                if i in self.yuvalar and ('el',i) not in getattr(algi,'tahmini',[])}

    def raunt_bitir(self,kazanan,simdi,mesaj=''):
        if self.ara_t is not None:
            return
        self.ara_t=simdi
        self.donmus=self.tekrar
        if kazanan is None:
            self.mesaj=mesaj or 'Eşitlik / tekrar'
        else:
            self.puanlar[kazanan]+=1
            self.mesaj=mesaj or ('YZ kazandı' if kazanan==1 and len(self.yuvalar)==1 else f'Oyuncu {kazanan+1} kazandı')
            self.ses.cal('ding',.5)
        if max(self.puanlar)>=2:
            self.kazanan=self.puanlar.index(max(self.puanlar))
            self.skor=max(self.puanlar)
            self.bitir(simdi,self.mesaj)

    def raunt_hazir(self,algi,simdi):
        return simdi-self.ara_t>=2

    def isle(self,kare,algi,simdi):
        dt=self.akis(kare,algi,simdi)
        if self.durum=='bekle':
            self.donmus=None
            self.tekrar.kareler.clear()
        self.kare_no+=1
        if dt>0:
            self.dtler.append(dt)
        if self.durum=='oyun':
            if self.ara_t is None:
                self.tekrar.ekle(kare,simdi)
                self.adim(algi,simdi)
            elif self.raunt_hazir(algi,simdi):
                self.yeni_raunt(simdi)
            yazi_koy(kare,f'{self.puanlar[0]}   VS   {self.puanlar[1]}',G//2,85,40,renk=SARI,hiza='orta')
            yazi_koy(kare,self.mesaj or self.yonerge(simdi),G//2,185,40 if self.mesaj else getattr(self,'YONERGE_BOY',40),hiza='orta')
            for j,(e,_) in self.eller(algi).items():
                x,y=map(int,px(e,9))
                cv2.circle(kare,(x,y),40,(CAMGOBEGI,PEMBE)[j],3)
                yazi_koy(kare,str(j+1),x,y-20,28,hiza='orta')
        if self.donmus and (self.ara_t is not None or self.durum=='sonuc'):
            tekrar=self.donmus.goruntu(simdi-(self.ara_t or self.durum_t))
            if tekrar is not None:
                kare[470:650,480:800]=tekrar
                yazi_koy(kare,'Ağır çekim',G//2,650,22,hiza='orta')
        return kare
