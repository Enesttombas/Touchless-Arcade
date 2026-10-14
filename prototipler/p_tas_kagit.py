from collections import Counter,deque
import cv2
import numpy as np
from cekirdek import G,Y,px,panel,yazi_koy,CAMGOBEGI,PEMBE,SARI
from el_kontrol import sekil
from gorsel import el_ikonu,patlama
from rekabet import Rekabet

JEST={'Closed_Fist':'taş','Open_Palm':'kağıt','Victory':'makas'}
YENER={'taş':'makas','makas':'kağıt','kağıt':'taş'}


def kazanan(a,b):
    return None if a==b else 0 if YENER[a]==b else 1


class Prototip(Rekabet):
    AD,ACIKLAMA='Taş Kağıt Makas','ŞİMDİ yazınca işaretini göster!'
    IHTIYAC,SIRA={'el'},34

    def __init__(self,ses):
        super().__init__(ses)
        self.gecmis,self.secimler=deque(maxlen=5),{}
        self.yz_oran=0.
        self.yz_secim='taş'
        self.uyari,self.kural,self.son_ritim='', '',None
        self.adim_t=0.
        self.kayip_t=None

    def yz_sec(self):
        if len(self.gecmis)>=5:
            tahmin,n=Counter(self.gecmis).most_common(1)[0]
            self.yz_oran=n/5
            if self.rng.random()<.8:
                return next(k for k,v in YENER.items() if v==tahmin)
        return str(self.rng.choice(list(YENER)))

    def yeni_raunt(self,simdi):
        super().yeni_raunt(simdi)
        self.secimler={}
        self.adim_t=simdi
        self.kayip_t=None
        self.uyari,self.kural,self.son_ritim='', '',None
        self.yz_secim=self.yz_sec()

    def yonerge(self,simdi):
        if self.uyari:return self.uyari
        t=max(0.,simdi-self.raunt_t)
        return ('TAŞ...', 'KAĞIT...', 'MAKAS...', 'ŞİMDİ!')[min(3,int(t))]

    def adim(self,algi,simdi):
        dt=max(0.,simdi-self.adim_t);self.adim_t=simdi
        eller=self.eller(algi)
        kucuk=any(np.linalg.norm(np.array(px(e,9))-px(e,0))<45 for e,_ in eller.values())
        if kucuk or len(eller)!=len(self.yuvalar) or not eller:
            if self.kayip_t is None:self.kayip_t=simdi
            self.uyari='YAKLAŞ / elini büyük göster' if kucuk else ('Seni göremiyorum' if simdi-self.kayip_t>=.5 else 'Elini göster')
            self.raunt_t+=dt;self.durum_t+=dt
            return
        self.uyari=''
        self.kayip_t=None
        t=simdi-self.raunt_t;ritim=min(3,int(max(0,t)))
        if ritim!=self.son_ritim:self.ses.cal('ding',.45);self.son_ritim=ritim
        if 3<=t<=3.6:
            for j,(e,ix) in eller.items():
                s=sekil(e)
                if s is not None:
                    skorlar=getattr(algi,'jest_skor',[])
                    skor=max(.6,float(skorlar[ix] or 0.)) if ix<len(skorlar) else .6
                    if skor>=self.secimler.get(j,('',-1))[1]:self.secimler[j]=(s,skor)
        if t>3.6:
            if len(self.yuvalar)==1:self.secimler[1]=(self.yz_secim,1.)
            if len(self.secimler)!=2:
                self.raunt_bitir(None,simdi,'Elini net göster / tekrar')
            else:
                a,b=self.secimler[0][0],self.secimler[1][0]
                if len(self.yuvalar)==1:self.gecmis.append(a)
                k=kazanan(a,b)
                self.kural='Aynı şekil / eşitlik' if k is None else {'taş':'TAŞ makası kırar','makas':'MAKAS kağıdı keser','kağıt':'KAĞIT taşı sarar'}[(a,b)[k]]
                self.raunt_bitir(k,simdi,'EŞİTLİK' if k is None else ('SOL','SAĞ' if len(self.yuvalar)>1 else 'YZ')[k]+' KAZANDI!')

    def isle(self,kare,algi,simdi):
        self.YONERGE_BOY=int(64+16*(1-max(0.,simdi-self.raunt_t)%1))
        super().isle(kare,algi,simdi)
        if self.durum in ('bekle','hazir'):
            for j,s in enumerate(('taş','kağıt','makas')):
                x=320+j*320
                panel(kare,x-120,525,x+120,640,opak=.75,kenar=(CAMGOBEGI,PEMBE,SARI)[j])
                el_ikonu(kare,x,585,s,(CAMGOBEGI,PEMBE,SARI)[j],.7)
                yazi_koy(kare,s.upper(),x,605,28,hiza='orta')
            yazi_koy(kare,'TAŞ makası, MAKAS kağıdı, KAĞIT taşı yener',G//2,665,28,hiza='orta')
        elif self.durum=='oyun' and self.ara_t is None:
            t=max(0.,simdi-self.raunt_t)
            if not self.uyari:
                el_ikonu(kare,G//2,int(350+12*np.sin(t*12)),'taş',SARI,1.5)
                yazi_koy(kare,'Ritmi izle, ŞİMDİ deyince şeklini göster',G//2,440,28,hiza='orta')
        if self.ara_t is not None:
            t=simdi-self.ara_t
            for j,(s,_) in self.secimler.items():
                x=320+j*640
                k=kazanan(*[self.secimler[i][0] for i in (0,1)]) if len(self.secimler)==2 else None
                scale=1.5+.25*np.sin(min(1.,t/.3)*np.pi) if k==j else 1.5-min(.6,t*.5) if k is not None else 1.5
                el_ikonu(kare,x,320,s,(CAMGOBEGI,PEMBE)[j],scale)
                yazi_koy(kare,s.upper(),x,360,32,hiza='orta')
                if k==j:patlama(kare,x,300,t,(CAMGOBEGI,PEMBE)[j])
            yazi_koy(kare,self.kural,G//2,415,34,renk=SARI,hiza='orta')
        return kare
