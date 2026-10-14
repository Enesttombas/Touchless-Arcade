"""Havada neon çizim, 4 Hz yerel CNN ve kartlı seyirci yedeği."""
import json
import os
import tempfile
from pathlib import Path
from time import perf_counter
import cv2
import numpy as np
import cekirdek as ck
from cekirdek import G,Y,px,panel,yazi_koy,SARI,YESIL,CAMGOBEGI,PEMBE,BEYAZ
from oyun_akis import OyunAkisi,TutHedef
from filtre import OneEuro
from el_kontrol import parmaklar
from gorsel import patlama

TANI_YOL=Path(tempfile.gettempdir())/"ciz_tani.jsonl"
KOK=Path(__file__).parent
KELIMELER=json.loads((KOK/'veri/ciz_kelimeler.json').read_text(encoding='utf-8'))


def onisle(cizgiler):
    pts=[p for c in cizgiler for p in c]
    if not pts:
        return None
    a=np.asarray(pts,dtype=float)
    if a.ndim!=2 or a.shape[1]!=2 or not np.isfinite(a).all():
        raise ValueError('Çizim noktaları sonlu x/y olmalı')
    lo,hi=a.min(0),a.max(0);boy=hi-lo
    if max(boy)<2:
        return None
    scale=23/max(boy);bas=(27-boy*scale)/2
    tuval=np.zeros((28,28),np.uint8)
    for c in cizgiler:
        if len(c)>=2:
            xy=np.rint((np.asarray(c)-lo)*scale+bas).astype(np.int32)
            cv2.polylines(tuval,[xy],False,255,1,cv2.LINE_AA)
    return tuval.astype(np.float32)[None,None]/255 if tuval.any() else None


class CizModel:
    def __init__(self,yol):
        import onnxruntime as ort
        ayar=ort.SessionOptions();ayar.intra_op_num_threads=1;ayar.inter_op_num_threads=1
        self.oturum=ort.InferenceSession(str(yol),sess_options=ayar,providers=['CPUExecutionProvider'])
        self.girdi=self.oturum.get_inputs()[0].name
        if self.oturum.get_inputs()[0].shape[1:]!=[1,28,28]:
            raise ValueError('Model girdi şekli uyumsuz')
        self.ms=0.

    def tahmin(self,x):
        if x is None:return []
        t=perf_counter();logits=self.oturum.run(None,{self.girdi:x})[0][0]
        self.ms=(perf_counter()-t)*1000
        if len(logits)!=len(KELIMELER):raise ValueError('Model kategori sayısı uyumsuz')
        p=np.exp(logits-logits.max());p/=p.sum()
        return [(KELIMELER[i]['tr'],float(p[i])) for i in np.argsort(p)[-3:][::-1]]


class Prototip(OyunAkisi):
    AD,ACIKLAMA='Çizim Kâhini','İşaretini uzat ve çiz; bükerek kalemi kaldır.'
    IHTIYAC,SIRA={'el'},36
    TUR_SN=90.
    KELIME_SAYISI=3

    def __init__(self,ses):
        super().__init__(ses)
        self.model,self.model_hata=None,None
        yol=KOK/'modeller/ciz_tanima.onnx'
        if yol.exists():
            try:self.model=CizModel(yol)
            except Exception as e:self.model_hata=str(e)
        self.modlar=['YZ Tahmin','Düello','Seyirci'] if self.model else ['Seyirci']
        self.mod=self.modlar[0]
        self.mod_hedef=TutHedef()
        self.bilim=False
        self.rng=np.random.default_rng()
        self.ids,self.cizimler,self.tuvaller=[],{},{}
        self.kalem,self.tahminler,self.girdiler={},{},{}
        self.puanlar={};self.kelime_no=0
        self.hedef=KELIMELER[0]
        self.faz,self.kelime_t,self.faz_t='ciz',0.,0.
        self.tahmin_t=-10.;self.kazanan=None
        self.parametre=0
        self.neon_cache=np.zeros((Y,G,3),np.uint8)
        self.neon_dirty=True
        self.neden={};self.tani_t=None;self.tani_hata=None
        try:self.parametre=json.loads((KOK/'modeller/ciz_egitim.json').read_text())['parametre']
        except (OSError,ValueError,KeyError):pass

    def baslat(self,algi,simdi):
        super().baslat(algi,simdi)
        self.jeu_t,self.kayip_t=simdi,None
        ids=getattr(algi,'el_id',[]) or list(range(len(algi.eller)))
        sirali=[i for i,e in sorted(zip(ids,algi.eller),key=lambda z:px(z[1],8)[0])]
        self.ids=sirali[:2] if self.mod=='Düello' else sirali[:1]
        self.puanlar={i:0 for i in self.ids}
        self.canli_sonuclar=[]
        self.kelime_no=0;self.kelimeler=self.rng.choice(len(KELIMELER),self.KELIME_SAYISI,replace=False)
        self.yeni_kelime(simdi)

    def yeni_kelime(self,simdi):
        self.hedef=KELIMELER[int(self.kelimeler[self.kelime_no])]
        self.kelime_no+=1;self.kelime_t,self.faz,self.kazanan=simdi,'ciz',None
        self.cizimler={i:[] for i in self.ids};self.tuvaller={i:np.zeros((Y,G,3),np.uint8) for i in self.ids}
        self.kalem,self.tahminler,self.girdiler={},{},{}
        self.neden={}
        self.filtreler,self.ham,self.goruldu,self.kapali={},{},{},{}
        self.inik,self.bekleyen,self.yazildi={},{},{};self.silindi=set()
        self.siliciler={i:TutHedef() for i in self.ids};self.gericiler={i:TutHedef() for i in self.ids}
        self.uc,self.ciz_t={},simdi
        self.tahmin_t=simdi-.25
        self.neon_dirty=True

    def tus(self,k):
        if k==32 and self.durum=='bekle':
            self.mod=self.modlar[(self.modlar.index(self.mod)+1)%len(self.modlar)]
        elif k in (ord('d'),ord('D')) and self.mod=='Seyirci' and self.durum=='oyun' and self.faz=='ciz':
            self.bildi(self.ids[0] if self.ids else None,self.onceki_t or self.kelime_t)
        elif k in (ord('i'),ord('I')):self.bilim=not self.bilim

    def bildi(self,kimlik,simdi):
        if self.faz!='ciz':return
        self.faz,self.faz_t,self.kazanan='bildim',simdi,kimlik
        self.canli_sonuclar.append({'kelime':self.hedef['tr'],'bildi':kimlik is not None,'sn':simdi-self.kelime_t})
        if kimlik is not None:self.puanlar[kimlik]+=max(0,int((20-simdi+self.kelime_t)*10))
        self.skor=max(self.puanlar.values(),default=0)
        self.ses.cal('basari',.6)

    def geri_al(self,i):
        if self.cizimler[i]:self.cizimler[i].pop()
        self.tuvaller[i].fill(0)
        for c in self.cizimler[i]:
            if c:cv2.circle(self.tuvaller[i],c[0],5,(CAMGOBEGI,PEMBE)[self.ids.index(i)],-1,cv2.LINE_AA)
            for a,b in zip(c,c[1:]):
                cv2.line(self.tuvaller[i],a,b,(CAMGOBEGI,PEMBE)[self.ids.index(i)],10,cv2.LINE_AA)
                cv2.circle(self.tuvaller[i],b,5,(CAMGOBEGI,PEMBE)[self.ids.index(i)],-1,cv2.LINE_AA)
        self.kalemi_kaldir(i)
        self.neon_dirty=True

    def kalemi_kaldir(self,i):
        for d in (self.kalem,self.ham,self.filtreler,self.bekleyen,self.yazildi):d.pop(i,None)
        self.inik[i]=0

    def tani_yaz(self,algi,simdi,kare=None):
        if os.environ.get('CIZ_TANI')!='1':return kare
        ids=getattr(algi,'el_id',[]) or list(range(len(algi.eller)))
        tahmini=getattr(algi,'tahmini',[])
        canli=[i for i in ids if ('el',i) not in tahmini]
        red=[n for tur,n in getattr(algi,'redler',[]) if tur=='el']
        aday=sum(tur=='el' for tur,*_ in getattr(algi,'adaylar',[]))
        veri=dict(t=float(simdi),ham_el=len(canli)+len(red)+aday,kapidan_gecti=bool(canli),
                  kapi_redleri=red,kapi_aday=aday,el_id=list(ids),tahmini=list(tahmini),
                  eller=[[[float(q.x),float(q.y),float(getattr(q,'z',0))] for q in e] for e in algi.eller],
                  kalem={str(i):i in self.kalem for i in self.ids},neden=self.neden.copy(),
                  nokta=sum(len(c) for cs in self.cizimler.values() for c in cs))
        if self.tani_t!=simdi:
            try:
                with TANI_YOL.open('a',encoding='utf-8') as f:f.write(json.dumps(veri,ensure_ascii=False)+'\n')
                self.tani_t=simdi
            except OSError as e:self.tani_hata=str(e)
        if kare is not None:
            durum=' / '.join(('iner' if i in self.kalem else 'kalkar')+': '+self.neden.get(i,'bekleme') for i in self.ids)
            metin=f"El {veri['ham_el']} / kapı {'geçti' if canli else 'bekle'} {','.join(red)} / {durum} / {veri['nokta']} nokta"
            if self.tani_hata:metin='Tanı kaydı yazılamadı: '+self.tani_hata
            panel(kare,0,0,G,48,opak=.9);yazi_koy(kare,metin,G//2,8,22,hiza='orta')
        return kare

    def ciz(self,algi,simdi=None):
        simdi=(self.onceki_t if self.onceki_t is not None else self.ciz_t+1/30) if simdi is None else simdi
        self.ciz_t=simdi
        ids=getattr(algi,'el_id',[]) or list(range(len(algi.eller)))
        gorulen=set()
        for i,e in zip(ids,algi.eller):
            if i not in self.ids or ('el',i) in getattr(algi,'tahmini',[]):continue
            gorulen.add(i);slot=self.ids.index(i);acik=parmaklar(e)
            raw=np.array(px(e,8),dtype=float);p=tuple(map(int,raw));self.uc[i]=p;self.neden[i]="çiziyor"
            x0,x1=(20,G-20) if len(self.ids)==1 else (20+slot*G//2,(slot+1)*G//2-20)
            geride=x0<=p[0]<=x0+170 and 175<=p[1]<=230
            if self.gericiler[i].sec('geri' if geride else None,simdi):self.geri_al(i)
            sil=acik is not None and all(acik)
            if self.siliciler[i].sec('sil' if sil else None,simdi):
                self.geri_al(i);self.neden[i]='avuç: geri al'
            if sil and simdi-self.siliciler[i].bas>=2 and i not in self.silindi:
                self.cizimler[i]=[];self.geri_al(i);self.tahminler[i]=[];self.girdiler.pop(i,None)
                self.silindi.add(i);self.neden[i]='avuç: tümünü sil'
            if not sil:self.silindi.discard(i)
            kok=np.array(px(e,5));bilek=np.array(px(e,0))
            isaret=np.linalg.norm(raw-kok)>max(12.,.75*np.linalg.norm(kok-bilek))
            icerde=x0<=p[0]<=x1 and 170<=p[1]<=630
            ciziyor=isaret and not sil and not geride and icerde
            son_t=self.goruldu.get(i,simdi);self.goruldu[i]=simdi
            if not ciziyor:
                self.inik[i]=0;self.bekleyen.pop(i,None)
                self.kapali[i]=self.kapali.get(i,0)+1
                self.neden[i]='avuç bekle' if sil else 'geri al hedefi' if geride else 'tuval dışında' if not icerde else 'işaret bükülü'
                if self.kapali[i]>=4:self.kalemi_kaldir(i)
                continue
            self.kapali[i]=0
            ilk=self.bekleyen.get(i,(None,simdi-1/30))
            dt=max(1/120,simdi-self.yazildi.get(i,ilk[1]))
            referans=self.ham.get(i,ilk[0])
            uzak=referans is not None and np.linalg.norm(raw-np.asarray(referans))>max(80.,min(.35*G,.12*G*dt*30))
            if simdi-son_t>=.4 or uzak:
                self.kalemi_kaldir(i);self.neden[i]='sıçrama' if uzak else f'el kayıp {simdi-son_t:.2f} sn'
            self.inik[i]=self.inik.get(i,0)+1
            if i not in self.kalem and self.inik[i]<2:
                self.bekleyen[i]=(p,simdi);self.neden[i]='kalem inişi 1/2'
                continue
            f=self.filtreler.setdefault(i,OneEuro(min_cutoff=6.,beta=.025))
            son=self.kalem.get(i)
            if son is None:
                son,ilk_t=self.bekleyen.pop(i,(p,simdi));f.suz(np.array(son,dtype=float),ilk_t)
                self.cizimler[i].append([son])
            p=tuple(map(int,np.rint(f.suz(raw,simdi))))
            renk=(CAMGOBEGI,PEMBE)[slot]
            if p!=son and sum(map(len,self.cizimler[i]))<5000:
                mesafe=np.linalg.norm(np.array(p)-son);n=max(1,int(np.ceil(mesafe/4)))
                self.cizimler[i][-1].extend([tuple(map(int,np.rint(np.array(son)+(np.array(p)-son)*k/n))) for k in range(1,n+1)])
                kalin=int(np.clip(14-mesafe/dt/150,6,14))
                cv2.line(self.tuvaller[i],son,p,renk,kalin,cv2.LINE_AA)
                cv2.circle(self.tuvaller[i],son,kalin//2,renk,-1,cv2.LINE_AA)
            cv2.circle(self.tuvaller[i],p,5,renk,-1,cv2.LINE_AA)
            self.neon_dirty=True
            self.kalem[i]=p;self.ham[i]=raw;self.yazildi[i]=simdi

        for i in self.ids:
            if i not in gorulen:
                kayip=simdi-self.goruldu.get(i,simdi)
                self.neden[i]=f'el kayıp {kayip:.2f} sn'
                self.siliciler[i].sec(None,simdi);self.gericiler[i].sec(None,simdi);self.silindi.discard(i)
                if kayip>=.4:self.kalemi_kaldir(i);self.uc.pop(i,None)
        self.tani_yaz(algi,simdi)

    def adim(self,algi,simdi):
        if self.faz=='ciz':
            self.ciz(algi,simdi)
            if simdi-self.kelime_t>=20:
                self.faz,self.faz_t='bilinemedi',simdi
                self.canli_sonuclar.append({'kelime':self.hedef['tr'],'bildi':False,'sn':20.})
            elif self.model and simdi-self.tahmin_t>=.25:
                self.tahmin_t=simdi;bildi=[]
                for i in self.ids:
                    x=onisle(self.cizimler[i]);self.girdiler[i]=x
                    tahmin=self.model.tahmin(x) if x is not None else []
                    self.tahminler[i]=tahmin
                    if tahmin and tahmin[0][0]==self.hedef['tr'] and tahmin[0][1]>=.6:bildi.append(i)
                if self.mod!='Seyirci' and bildi:
                    self.bildi(bildi[0] if len(bildi)==1 else None,simdi)
        elif simdi-self.faz_t>=2:
            if self.kelime_no>=self.KELIME_SAYISI:self.bitir(simdi,f'{self.KELIME_SAYISI} kelime tamamlandı!')
            else:self.yeni_kelime(simdi)

    def isle(self,kare,algi,simdi):
        self.akis(kare,algi,simdi)
        if self.durum=='bekle':
            panel(kare,930,70,1260,160,opak=.8)
            yazi_koy(kare,self.mod+' / değiştir',1100,95,26,hiza='orta')
            h=any(930<=px(e,9)[0]<=1260 and 70<=px(e,9)[1]<=160 for e in algi.eller)
            if self.mod_hedef.sec('mod' if h else None,simdi):self.tus(32)
            if self.mod=='Seyirci':yazi_koy(kare,'Fiziksel kelime kartını çiz / operatör D: doğru',G//2,600,22,hiza='orta')
        if self.durum!='oyun':return self.tani_yaz(algi,simdi,kare)
        ids=getattr(algi,'el_id',[]) or list(range(len(algi.eller)))
        presents=set(ids)-{i for typ,i in getattr(algi,'tahmini',[]) if typ=='el'}
        if not set(self.ids).issubset(presents):
            self.kelime_t+=max(0.,simdi-getattr(self,'jeu_t',simdi));self.durum_t+=max(0.,simdi-getattr(self,'jeu_t',simdi))
            if getattr(self,'kayip_t',None) is None:self.kayip_t=simdi
            if simdi-self.kayip_t>=.5:yazi_koy(kare,'Seni göremiyorum / elini göster',G//2,110,30,hiza='orta')
        else:self.kayip_t=None
        self.jeu_t=simdi
        self.adim(algi,simdi)
        if self.durum!='oyun':return self.tani_yaz(algi,simdi,kare)
        hedef='?' if self.mod=='Seyirci' and self.faz=='ciz' else self.hedef['tr'].upper()
        yazi_koy(kare,hedef,G//2,75,45,renk=SARI,hiza='orta')
        for j,i in enumerate(self.ids):
            x0,x1=(20,G-20) if len(self.ids)==1 else (20+j*G//2,(j+1)*G//2-20)
            roi=kare[170:630,x0:x1]
            roi[:]=cv2.convertScaleAbs(roi,alpha=.9)
            cv2.rectangle(kare,(x0,170),(x1,630),(CAMGOBEGI,PEMBE)[j],2)
            panel(kare,x0,175,x0+170,230,opak=.75)
            yazi_koy(kare,'GERİ AL',x0+85,185,28,hiza='orta')
            ck.halka(kare,x0+145,215,self.gericiler[i].oran(simdi),r=14)
            tahmin=self.tahminler.get(i,[])
            for n,(kelime,oran) in enumerate(tahmin):
                yy=245+n*38
                yazi_koy(kare,f'{kelime} %{int(oran*100)}',x1-160,yy,28,hiza='orta')
                cv2.rectangle(kare,(x1-310,yy+25),(x1-310+int(oran*140),yy+30),YESIL,-1)
            yazi_koy(kare,f'{j+1}: {self.puanlar[i]}',x0+90,640,28)
            if self.bilim and self.girdiler.get(i) is not None:
                k=(self.girdiler[i][0,0]*255).astype(np.uint8)
                k=cv2.cvtColor(cv2.resize(k,(112,112),interpolation=cv2.INTER_NEAREST),cv2.COLOR_GRAY2BGR)
                kare[500:612,x1-125:x1-13]=k
        if self.neon_dirty:
            # Işık yalnız tuval çevresinde; boş kamera alanını her karede süzme.
            birlesik=np.zeros((480,G,3),np.uint8)
            for t in self.tuvaller.values():cv2.add(birlesik,t[160:640],dst=birlesik)
            blur=cv2.GaussianBlur(cv2.resize(birlesik,(G//4,120)),(5,5),0)
            self.neon_cache[160:640]=cv2.add(birlesik,cv2.resize(blur,(G,480)))
            self.neon_dirty=False
        cv2.add(kare[160:640],self.neon_cache[160:640],dst=kare[160:640])
        for i,p in self.uc.items():
            cv2.circle(kare,tuple(map(int,p)),12,(CAMGOBEGI,PEMBE)[self.ids.index(i)],-1 if i in self.kalem else 3,cv2.LINE_AA)
            if self.siliciler[i].hedef:ck.halka(kare,*p,self.siliciler[i].oran(simdi,2.),r=30)
        yazi_koy(kare,'İşaret: çiz / bük: kaldır / avuç 1 sn: geri, 2 sn: sil',G//2,685,26,hiza='orta')
        kalan=max(0,int(20-simdi+self.kelime_t))
        yazi_koy(kare,f'{self.kelime_no}/{self.KELIME_SAYISI} / {kalan} sn',G//2,130,26,hiza='orta')
        if self.faz!='ciz':
            if self.faz=='bildim':patlama(kare,G//2,350,simdi-self.faz_t,YESIL)
            yazi_koy(kare,'BİLDİM!' if self.kazanan is not None else 'EŞİTLİK' if self.faz=='bildim' else 'BİLİNEMEDİ',G//2,350,62,renk=YESIL,hiza='orta')
        if self.bilim and self.model:
            yazi_koy(kare,f'28×28 / {self.parametre} parametre / {self.model.ms:.2f} ms',G//2,680,20,hiza='orta')
        return self.tani_yaz(algi,simdi,kare)


def canli_test():
    """İnsan 10 kelime çizer; yalnız tamamlanan denemenin anonim sonuçları saklanır."""
    import os,time
    from oyuncu import OyuncuKapisi
    p=Prototip(ck.Ses(acik=True))
    if p.model is None:raise RuntimeError('Canlı kabul için eğitimli ONNX modeli gerekli')
    p.KELIME_SAYISI,p.TUR_SN=10,240.
    kam=ck.Kamera(int(os.environ.get('KAMERA','0')));alg=ck.Algilayici();kapi=OyuncuKapisi()
    pencere='Ciz Tahmin - 10 kelime canli test'
    kam.start();cv2.namedWindow(pencere,cv2.WINDOW_NORMAL)
    try:
        while True:
            if kam.kare is not None:
                t=time.time();k=kam.kare.copy();a=kapi.suz(alg.algila(k,p.IHTIYAC),t)
                cv2.imshow(pencere,p.isle(k,a,t))
                if p.durum=='sonuc':
                    sonuc={'tarih':time.strftime('%Y-%m-%d %H:%M:%S'),'tamamlanan':len(p.canli_sonuclar),
                           'dogru':sum(s['bildi'] for s in p.canli_sonuclar),'kelimeler':p.canli_sonuclar}
                    out=KOK/'modeller/ciz_canli_test.json';out.parent.mkdir(parents=True,exist_ok=True)
                    out.write_text(json.dumps(sonuc,ensure_ascii=False,indent=2),encoding='utf-8')
                    print(json.dumps(sonuc,ensure_ascii=False),flush=True);break
            tus=cv2.waitKey(10)&255
            if tus in (27,ord('q'),ord('Q')) or cv2.getWindowProperty(pencere,cv2.WND_PROP_VISIBLE)<1:break
            if tus in (ord('i'),ord('I')):p.tus(tus)
    finally:
        kam.kapat();cv2.destroyAllWindows()


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--canli-test',action='store_true')
    if ap.parse_args().canli_test:canli_test()
