import cv2
import numpy as np
from cekirdek import G,Y,px,yazi_koy,YESIL,SARI,KIRMIZI
from oyun_akis import OyunAkisi
from rekabet import Rekabet,erken_kare
from gorsel import el_ikonu


class Prototip(Rekabet):
    AD,ACIKLAMA='Silahşor Düellosu','Eller aşağı. ATEŞ yazınca elini kaldır!'
    IHTIYAC,SIRA={'el','yuz'},33

    def __init__(self,ses):
        super().__init__(ses)
        self.aktif=set();self.yuzler={};self.hazir={};self.tetik={}
        self.k0,self.ates_t,self.tepki,self.en_iyi=None,None,None,None
        self.bekleme,self.beklenen=2.,0.
        self.adim_t=None;self.kilif_t,self.kalkis,self.silah,self.yok_t={},{},{},{}

    def yuzleri(self,algi):
        sonuc={};ids=getattr(algi,'yuz_id',[]) or list(range(len(algi.yuzler)))
        for i,yuz in zip(ids,algi.yuzler):
            if ('yuz',i) in getattr(algi,'tahmini',[]):continue
            xy=np.asarray([(q.x,q.y) for q in yuz],dtype=float)
            if not len(xy) or not np.isfinite(xy).all():continue
            lo,hi=xy.min(0),xy.max(0);merkez=(lo+hi)/2
            if not (0<=merkez[0]<=1 and 0<=merkez[1]<=1):continue
            slot=int(merkez[0]>=.5);alan=float(np.prod(hi-lo))
            if slot not in sonuc or alan>sonuc[slot]['alan']:
                sonuc[slot]=dict(x=int(merkez[0]*G),y=int(merkez[1]*Y),r=max(25,int((hi[1]-lo[1])*Y*.65)),
                                 omuz=float((hi[1]+.5*(hi[1]-lo[1]))*Y),alan=alan,ust=int(lo[1]*Y))
        return sonuc

    def yukarida(self,algi):
        ids=getattr(algi,'el_id',[]) or list(range(len(algi.eller)))
        yukari=set()
        for i,e in zip(ids,algi.eller):
            if ('el',i) in getattr(algi,'tahmini',[]):continue
            x,y=px(e,9);j=int(x>=G/2)
            if 0<=x<=G and 0<=y<=Y and j in self.yuzler and y<self.yuzler[j]['omuz']:yukari.add(j)
        return yukari

    def baslat(self,algi,simdi):
        OyunAkisi.baslat(self,algi,simdi)
        self.yuzler=self.yuzleri(algi);self.yuvalar=sorted(self.yuzler)
        self.puanlar,self.kazanan,self.raunt=[0,0],None,0
        self.yeni_raunt(simdi)

    def yeni_raunt(self,simdi):
        super().yeni_raunt(simdi)
        self.aktif=set(self.yuzler);self.bekleme=float(self.rng.uniform(1.5,4.))
        self.k0,self.ates_t,self.tepki=None,None,None
        self.hazir,self.tetik,self.kilif_t,self.kalkis,self.silah,self.yok_t={},{},{},{},{},{}
        self.beklenen,self.adim_t=0.,simdi
        self.yz_sure=max(.35,.6-.05*(self.raunt-1));self.yz_kare=None
        self.son_kazanan=None

    def raunt_bitir(self,kazanan,simdi,mesaj=''):
        self.son_kazanan=kazanan
        super().raunt_bitir(kazanan,simdi,mesaj)

    def raunt_hazir(self,algi,simdi):
        return simdi-self.ara_t>=2.5

    def yonerge(self,simdi):
        if self.k0 is not None:return 'ATEŞ!'
        return 'HAZIR…' if self.aktif and all(self.hazir.get(j) for j in self.aktif) else 'ELLERİ İNDİR' if simdi-self.raunt_t>=4 else 'ELLER AŞAĞI'

    def adim(self,algi,simdi):
        if self.ara_t is not None:return
        dt=max(0.,simdi-self.adim_t) if self.adim_t is not None else 0.;self.adim_t=simdi
        self.yuzler=self.yuzleri(algi);yukari=self.yukarida(algi);erken=[]
        for j in sorted(self.aktif):
            var=j in self.yuzler
            if var and j not in yukari:
                self.kilif_t.setdefault(j,simdi);self.hazir[j]=simdi-self.kilif_t[j]>=.6-1e-9
                if self.hazir[j]:self.silah[j]=True
                self.kalkis[j]=0
            else:
                self.kilif_t.pop(j,None);self.hazir[j]=False
                if not var:self.silah[j]=False;self.kalkis[j]=0
                elif self.k0 is not None:self.tetik.setdefault(j,self.kare_no)
                elif self.silah.get(j):
                    self.kalkis[j]=self.kalkis.get(j,0)+1
                    if self.kalkis[j]>=2:erken.append(j)
            if self.hazir[j]:self.yok_t.pop(j,None)
            else:self.yok_t.setdefault(j,simdi)
        if erken:
            self.raunt_bitir(1-erken[0] if len(erken)==1 else None,simdi,'ERKEN!' if len(erken)==1 else 'ERKEN! / EŞİTLİK')
            return
        if self.k0 is None:
            seyirci={j for j in self.aktif if not self.hazir.get(j) and simdi-self.yok_t.get(j,simdi)>=8}
            if seyirci:self.aktif-=seyirci;self.beklenen=0.
            if not self.aktif:self.durum='bekle';return
            if all(self.hazir.get(j) for j in self.aktif):
                self.beklenen+=0. if seyirci else min(dt,max(0.,simdi-max(self.kilif_t[j]+.6 for j in self.aktif)))
                if self.beklenen>=self.bekleme:
                    self.k0,self.ates_t=self.kare_no,simdi
                    self.yz_kare=self.k0+int(np.ceil(self.yz_sure/max(.001,np.median(self.dtler) if self.dtler else 1/60)))
                    self.ses.cal('zap',.8)
            else:self.beklenen=0.
        else:
            if not self.aktif.issubset(self.yuzler):
                self.yz_kare+=1;return
            if len(self.aktif)==1 and self.kare_no>=self.yz_kare:self.tetik.setdefault(1-next(iter(self.aktif)),self.yz_kare)
            if self.tetik:
                k=erken_kare(self.tetik)
                self.tepki=(self.tetik[k]-self.k0)*float(np.median(self.dtler) if self.dtler else 1/30) if k is not None else None
                if self.tepki is not None:self.en_iyi=self.tepki if self.en_iyi is None else min(self.en_iyi,self.tepki)
                ad='YZ' if k not in self.aktif else ('SOL','SAĞ')[k] if k is not None else ''
                self.raunt_bitir(k,simdi,'Aynı kare / tekrar' if k is None else f'{ad} KAZANDI • {self.tepki:.3f} sn')

    def isle(self,kare,algi,simdi):
        dt=1/30 if self.onceki_t is None else max(0.,min(.125,simdi-self.onceki_t));self.onceki_t=simdi
        if dt:self.dtler.append(dt)
        self.kare_no+=1;self.yuzler=self.yuzleri(algi)
        kare[:]=cv2.convertScaleAbs(kare,alpha=.85)
        if not self.yuzler:
            self.durum='bekle';self.donmus=None;self.tekrar.kareler.clear()
        elif self.durum=='bekle':self.durum,self.durum_t='hazir',simdi
        elif self.durum=='hazir' and simdi-self.durum_t>=2:self.baslat(algi,simdi)
        elif self.durum=='sonuc' and simdi-self.durum_t>=5:self.durum='bekle'
        if self.durum=='oyun':
            if self.ara_t is None:self.adim(algi,simdi)
            elif self.raunt_hazir(algi,simdi):self.yeni_raunt(simdi)
        if self.ates_t is not None and 0<=simdi-self.ates_t<.12:
            cv2.addWeighted(kare,.65,np.full_like(kare,255),.35,0,dst=kare)
        for x in (12,G-12):cv2.line(kare,(x,12),(x,Y-12),(80,150,200),2)
        if self.durum=='hazir':
            el_ikonu(kare,G//2,440,'kağıt',SARI,.8)
            cv2.arrowedLine(kare,(G//2,405),(G//2,340),SARI,4,tipLength=.3)
            metin=self.ACIKLAMA;boy=38
        elif self.ara_t is not None or self.durum=='sonuc':metin=self.mesaj or self.sonuc;boy=54
        else:metin=self.yonerge(simdi) if self.yuzler else 'ELLER AŞAĞI';boy=90 if metin=='ATEŞ!' else int(62+4*np.sin(simdi*3))
        renk=KIRMIZI if 'ERKEN' in metin else YESIL if metin=='HAZIR…' else SARI
        yazi_koy(kare,metin,G//2,300,boy,renk=renk,hiza='orta')
        # İki oyuncu etiketi tek üst satırdır; toplam iki metin bloğu.
        adlar=['SOL' if j==0 else 'SAĞ' for j in sorted(self.yuzler)]
        if len(adlar)==1:adlar.append('YZ')
        isimler='     |     '.join(adlar)
        if self.yuzler:yazi_koy(kare,isimler,G//2,max(12,min(v['ust'] for v in self.yuzler.values())-45),32,renk=YESIL if self.hazir and all(self.hazir.values()) else SARI,hiza='orta')
        for j,v in self.yuzler.items():
            if self.hazir.get(j) and self.ara_t is None:
                cv2.polylines(kare,[np.array([(v['x']-12,v['ust']-15),(v['x']-3,v['ust']-6),(v['x']+15,v['ust']-27)],np.int32)],False,YESIL,4,cv2.LINE_AA)
            if self.ara_t is not None and self.son_kazanan==j:cv2.circle(kare,(v['x'],v['y']),v['r'],YESIL,5,cv2.LINE_AA)
        return kare
