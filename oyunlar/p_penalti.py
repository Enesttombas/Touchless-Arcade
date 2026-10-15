"""Parmakla çizilen yön/falso, hız ve ivmeden güç; bedenle kalecilik."""
import math
from collections import Counter,deque
from pathlib import Path
import json
import cv2
import numpy as np
from cekirdek import G,Y,px,yazi_koy,panel,halka,bindir,parilti,SARI,YESIL,BEYAZ,CAMGOBEGI,KIRMIZI
from oyun_akis import OyunAkisi,TutHedef
from el_kontrol import parmaklar
from filtre import OneEuro
from gorsel import patlama,el_ikonu
from p_cevap_yagmuru import maske_ver

TOP=np.array([G/2,Y-130.])
R=.11
YAKALA_R,KILIT_SN,SERBEST_R=95.,.15,140.  # topu yakalama yarıçapı, kilit süresi, yeni atış için uzaklaşma
EKRAN_OLCEK=1000/13  # izdusus'te kale düzleminin (z=11) piksel/metre ölçeği


def falso(yol):
    if len(yol)<6:
        return 0.
    a,b=np.asarray(yol[0]),np.asarray(yol[-1]);d=b-a;l=np.linalg.norm(d)
    if l<1:
        return 0.
    v=np.asarray(yol)-a
    uzak=(d[0]*v[:,1]-d[1]*v[:,0])/l
    return float(np.clip(uzak[np.argmax(abs(uzak))]/l,-1,1))


def ciz_sut(ornekler,boy):
    yol=np.array([p for p,t in ornekler],dtype=float)
    zaman=np.array([t for p,t in ornekler],dtype=float)
    boy=max(60.,boy)
    dt=np.maximum(.015,np.diff(zaman))
    hiz=np.linalg.norm(np.diff(yol,axis=0),axis=1)/dt/boy if len(yol)>1 else np.array([0.])
    ivme=np.maximum(0.,np.diff(hiz)/np.maximum(.015,dt[1:])) if len(hiz)>1 else np.array([0.])
    guc=float(np.clip(.25+.18*np.percentile(hiz,75)+.025*min(5.,float(np.percentile(ivme,75))),.25,1.))
    d=yol[-1]-yol[0]
    # Yol nereye çizildiyse top oraya gider: yolun ucu kale düzlemindeki nişan noktasıdır.
    # Kısa fiske kalenin altında biterse aynı yönde kale ortasına uzatılır.
    uc_y=yol[0,1]+d[1]
    if d[1]<-1 and uc_y>360:
        d=d*(yol[0,1]-290)/max(1.,-d[1])
        uc_y=yol[0,1]+d[1]
    hx=float(d[0])/EKRAN_OLCEK
    yatay=float(np.clip(math.degrees(math.atan2(hx,11.)),-25,25))
    hy=float(np.clip(.6-(uc_y-330)/EKRAN_OLCEK,.3,3.))
    dikey=float(np.clip(hedef_acisi(guc,hy),0,18))
    return dict(guc=guc,yatay=yatay,dikey=dikey,falso=falso(yol))


def ucus(param):
    v0=18+12*float(np.clip(param['guc'],.25,1))
    az,el=map(math.radians,(param['yatay'],param['dikey']))
    v=np.array([math.sin(az)*math.cos(el),math.sin(el),math.cos(az)*math.cos(el)])*v0
    p=np.array([0.,R,0.]);w=np.array([0.,40*param['falso'],0.]);yol=[p.copy()]
    for _ in range(480):
        eski=p.copy()
        a=np.array([0.,-9.81,0.])+.025*np.cross(w,v)-.002*np.linalg.norm(v)*v
        v+=a/120;p+=v/120
        if p[1]<R:
            p[1]=R
            v[1]=abs(v[1])*.3
        if p[2]>=11:
            p=eski+(p-eski)*(11-eski[2])/(p[2]-eski[2])
            yol.append(p.copy());break
        yol.append(p.copy())
    return np.asarray(yol),v0


_acilar={}
def hedef_acisi(guc,yukseklik):
    """Topun kale çizgisinde verilen yüksekliğe varması için gereken dikey açı (önbellekli)."""
    key=(round(float(guc),2),round(float(yukseklik),1))
    if key not in _acilar:
        lo,hi=0.,18.
        for _ in range(12):
            mid=(lo+hi)/2
            yol,_=ucus(dict(guc=key[0],yatay=0,dikey=mid,falso=0))
            if yol[-1,1]<key[1]: lo=mid
            else: hi=mid
        _acilar[key]=(lo+hi)/2
    return _acilar[key]


def merkez_acisi(guc):
    return hedef_acisi(guc,1.22)


def _yumusak(t):
    t=min(1.,max(0.,t));return t*t*(3-2*t)


class SanalKaleci:
    """Tek oyunculu modda çizilmiş neon kaleci: bekler, yalandan bir yana yatar, seçtiği köşeye uçar.
    Kurtarış kararı çizilen eldivenlerle aynı noktalardan verilir (kol topa değmeden Tutuş yok)."""
    Z=10.9

    def __init__(self,rng):
        self.rng=rng;self.plan=None;self.hedef=np.array([0.,1.1])

    def planla(self,fizik,yon):
        q=fizik[-1];taraf=-1 if q[0]<-.8 else 1 if q[0]>.8 else 0
        menzil_x,menzil_y=float(self.rng.uniform(2.,3.)),float(self.rng.uniform(1.9,2.35))
        if yon==taraf:  # doğru köşe: uzanabildiği yere kadar
            self.hedef=np.array([np.clip(q[0],-menzil_x,menzil_x),np.clip(q[1],.3,menzil_y)])
        elif yon==0:
            self.hedef=np.array([float(self.rng.uniform(-.3,.3)),1.95])
        else:
            self.hedef=np.array([yon*float(self.rng.uniform(1.8,2.6)),float(self.rng.uniform(.5,1.6))])
        self.plan=yon if yon else (1 if self.hedef[0]>=0 else -1)
        return self.hedef

    def eldivenler(self,fizik=None,yon=0):
        if self.plan is None and fizik is not None:self.planla(fizik,yon)
        h=self.hedef;return [h+np.array([0.,.11]),h-np.array([0.,.11])]

    def sifirla(self):
        self.plan=None

    def poz(self,simdi,ucus_t=None,ucus_sn=1.3):
        """Kalça, gövde yönü (birim), eldivenler ve yerdelik oranı."""
        bekle_x=.22*math.sin(simdi*1.7);zip_=.07*abs(math.sin(simdi*3.4))
        kalca=np.array([bekle_x,.95+zip_]);yukari=np.array([0.,1.])
        el=[kalca+np.array([-.5,.15]),kalca+np.array([.5,.15])]
        if ucus_t is None or self.plan is None:
            return kalca,yukari,el,0.
        t=simdi-ucus_t;atla_bas=max(.2,ucus_sn-.45)
        if t<atla_bas:  # yalancıktan ters tarafa yatma (aldatma)
            a=_yumusak((t-(atla_bas-.25))/.15)
            kalca=kalca+np.array([-self.plan*.35*a,-.08*a])
            return kalca,yukari,el,0.
        e=_yumusak((t-atla_bas)/.4)
        bas_k=kalca-np.array([self.plan*.35,.08])
        hedef_k=self.hedef-(self.hedef-np.array([0.,.95]))/max(.01,np.linalg.norm(self.hedef-np.array([0.,.95])))*1.05
        kalca=bas_k+(hedef_k-bas_k)*e
        yon=self.hedef-kalca;yon=yon/max(.01,np.linalg.norm(yon))
        govde=yukari+(yon-yukari)*e;govde=govde/max(.01,np.linalg.norm(govde))
        el=[a+(b-a)*e for a,b in zip(el,self.eldivenler())]
        dus=_yumusak((t-ucus_sn)/.35)
        if dus>0:
            alt=min(kalca[1],min(g[1] for g in el))
            kay=np.array([0.,-max(0.,min(alt,kalca[1]-.25))*dus])
            kalca=kalca+kay;el=[g+kay for g in el]
        return kalca,govde,el,dus

    def ciz(self,kare,simdi,ucus_t=None,ucus_sn=1.3,kurtardi=False):
        kalca,govde,el,_=self.poz(simdi,ucus_t,ucus_sn)
        dik=np.array([govde[1],-govde[0]])
        boyun=kalca+govde*.62;kafa=boyun+govde*.24
        ayak=[kalca-govde*.85+dik*.22,kalca-govde*.85-dik*.22]
        if ucus_t is None:ayak=[np.array([kalca[0]-.28,0.]),np.array([kalca[0]+.28,0.])]
        def e(q):return izdusus((float(q[0]),float(q[1]),self.Z))[:2]
        isik=np.zeros_like(kare);renk=CAMGOBEGI
        olcek=1000/(self.Z+2)
        for a,b in ((kalca,boyun),(boyun,el[0]),(boyun,el[1]),(kalca,ayak[0]),(kalca,ayak[1])):
            cv2.line(isik,e(a),e(b),renk,9,cv2.LINE_AA)
        cv2.circle(isik,e(kafa),int(.15*olcek),renk,6,cv2.LINE_AA)
        cv2.ellipse(isik,e(kalca+govde*.3),(int(.2*olcek),int(.34*olcek)),
                    -math.degrees(math.atan2(govde[0],govde[1])),0,360,renk,5,cv2.LINE_AA)
        parlak=SARI if not kurtardi else YESIL
        for g in el:cv2.circle(isik,e(g),int(.13*olcek)+(6 if kurtardi else 0),parlak,-1,cv2.LINE_AA)
        golge=np.array([kalca[0],0.]);gx,gy=e(golge)
        cv2.ellipse(kare,(gx,gy),(int(.5*olcek),int(.07*olcek)),0,0,360,(25,40,30),-1,cv2.LINE_AA)
        parilti(kare,isik,guc=1.4,sigma=4.0)


def izdusus(p):
    x,y,z=p
    olcek=1000/(z+2)
    return int(G/2+x*olcek),int(330+(.6-y)*olcek),max(4,int(R*olcek))


def kale_karari(p,eller=(),govde=None):
    x,y=p[:2]
    if (abs(abs(x)-3.66)<=R and 0<=y<=2.44+R) or (abs(y-2.44)<=R and abs(x)<=3.66+R):
        return 'Direk'
    if abs(x)>3.66-R or y>2.44-R or y<R:
        return 'Dışarı'
    if any(np.linalg.norm(np.asarray((x,y))-e)<=.18+R for e in eller):
        return 'Tutuş'
    if govde and (govde(x,y) or any(govde(x+R*math.cos(t),y+R*math.sin(t)) for t in np.linspace(0,2*math.pi,8,endpoint=False))):
        return 'Sektirme'
    return 'GOL'


class Ag:
    def __init__(self):
        self.z=np.zeros((8,16));self.eski=self.z.copy();self.birik=0.

    def vur(self,x,y):
        ix=int(np.clip((x+3.66)/7.32*15,1,14));iy=int(np.clip((2.44-y)/2.44*7,1,6))
        self.z[iy,ix]=.6

    def adim(self,dt):
        self.birik+=min(.1,dt)
        while self.birik>=1/120:
            z=self.z;v=(z-self.eski)*.97
            lap=(z[1:-1,:-2]+z[1:-1,2:]+z[:-2,1:-1]+z[2:,1:-1]-4*z[1:-1,1:-1])*.08
            self.eski=z.copy();self.z=z+v;self.z[1:-1,1:-1]+=lap
            self.z[[0,-1]]=0;self.z[:,[0,-1]]=0;self.birik-=1/120


class Prototip(OyunAkisi):
    AD,ACIKLAMA='Altın Vuruş','Topu tut, yol çiz, dur!'
    IHTIYAC,SIRA={'el','poz'},35
    KAPI={'el_sahip_sart':False}  # şut eli bedenden uzakta da kabul (Enes 2026-10-15: oynaması çok zor)
    TUR_SN=240.
    KAMERA_PARLAKLIK=.85

    def __init__(self,ses):
        super().__init__(ses)
        self.faz,self.kilit_t='bekle',None
        self.yol,self.fizik=[],None
        self.param=dict(guc=.6,yatay=0,dikey=merkez_acisi(.6),falso=0)
        self.onceki_p,self.hareket_t=None,0.
        self.hizlar=deque(maxlen=2)
        self.el_id,self.ids=None,[]
        self.rol,self.atilan,self.goller=0,[0,0],[0,0]
        self.gecmis,self.rng=deque(maxlen=5),np.random.default_rng()
        self.mod,self.mod_hedef='Penaltı',TutHedef()
        self.challenge=False
        self.yz_oran,self.yz_yon=0.,0
        self.ag=Ag()
        self.sanal=SanalKaleci(self.rng);self.serbest=True
        self.el_kayip_t=None
        self.ucus_sn,self.gecikme=1.3,0.
        self.son_kaleci,self.kaleci_t=None,-10.
        self.ucus_t,self.atis_t=0.,None
        self.en_hizli=0.
        self.tam_beden_t=None
        self.top_p=np.array([0.,R,0.])
        self.render_mask=None
        self.ornekler=[];self.kapali=0;self.parmak_filtre=OneEuro(2.5,.025)
        self.ham_p=None;self.kayip_t=None;self.onizleme_key=None;self.onizleme_yol=None
        try:
            ayar=json.loads((Path(__file__).parent/'veri/filtre_ayar.json').read_text())
            self.gecikme=max(0,float(ayar.get('gecikme_ms',0))/1000)
        except (OSError,ValueError,TypeError):
            pass
        self.ucus_sn=max(1.3,4*self.gecikme)

    def baslat(self,algi,simdi):
        super().baslat(algi,simdi)
        pi=getattr(algi,'poz_id',[]) or list(range(len(algi.pozlar)))
        self.ids=[i for i,p in sorted(zip(pi,algi.pozlar),key=lambda z:z[1][23].x)][:2]
        self.challenge=bool(self.ids and not algi.eller)
        self.rol,self.atilan,self.goller=0,[0,0],[0,0]
        self.son_kaleci,self.kaleci_t=None,-10.
        self.yeni_atis(simdi)
        self.serbest=True  # ilk atışta kilit yok; yalnız şuttan sonra parmak toptan çekilmeli

    def tus(self,k):
        if k==32 and self.durum=='bekle':
            self.mod='Frikik' if self.mod=='Penaltı' else 'Penaltı'

    def yeni_atis(self,simdi):
        self.faz,self.kilit_t,self.el_id,self.atis_t='bekle',None,None,None
        self.yol,self.hizlar=[],deque(maxlen=2)
        self.ornekler=[];self.kapali=0;self.ham_p=None
        self.parmak_filtre=OneEuro(2.5,.025);self.kayip_t=None
        self.hareket_t=simdi
        self.yz_yon=self.yz_sec()
        self.sanal.sifirla();self.serbest=False  # parmak toptan uzaklaşmadan yeni atış kilitlenmez (çift şut)
        self.challenge_t=simdi

    def yz_sec(self):
        if len(self.gecmis)>=5:
            yon,n=Counter(self.gecmis).most_common(1)[0];self.yz_oran=n/5
            if self.rng.random()<.8: return yon
        return int(self.rng.choice([-1,0,1]))

    def sutcu(self,algi):
        ids=getattr(algi,'el_id',[])
        eller=[(i,e) for i,e in zip(ids,algi.eller) if ('el',i) not in getattr(algi,'tahmini',[])]
        if len(self.ids)>=2:
            sahip=self.ids[self.rol]
            pi=getattr(algi,'poz_id',[])
            poz=next((p for i,p in zip(pi,algi.pozlar) if i==sahip),None)
            if poz is not None:
                eller=[(i,e) for i,e in eller if min(np.linalg.norm(np.array(px(e,0))-px(poz,j)) for j in (15,16))<.18*G]
        if self.el_id is not None:
            return next((e for i,e in eller if i==self.el_id),None)
        if eller:
            self.el_id=eller[0][0];return eller[0][1]
        return None

    def boy(self,algi):
        if algi.pozlar:
            return max(60,float(np.linalg.norm(np.array(px(algi.pozlar[0],11))-px(algi.pozlar[0],12))))
        if algi.yuzler:
            return max(60,float(np.linalg.norm(np.array(px(algi.yuzler[0],33))-px(algi.yuzler[0],263)))*4)
        return 200.

    def kontrol(self,algi,simdi,dt):
        el=self.sutcu(algi)
        if el is None:
            # Hızlı fiskede el bulanıp kaybolur: yeterince çizildiyse şut sayılır.
            if self.faz=='ciz' and len(self.yol)>=3 and np.linalg.norm(self.yol[-1]-TOP)>=60:
                self.sut(simdi);return
            if self.faz=='ciz':  # tek kare kayıp çizimi bozmasın; 0,3 sn sürerse bırak
                if self.el_kayip_t is None:self.el_kayip_t=simdi
                if simdi-self.el_kayip_t<.3:return
            self.el_kayip_t=None
            self.faz,self.kilit_t,self.el_id='bekle',None,None
            self.yol=[];self.ornekler=[];self.ham_p=None;self.serbest=True
            self.parmak_filtre=OneEuro(2.5,.025);return
        self.el_kayip_t=None
        ham=np.asarray(px(el,8),dtype=float)
        p=self.parmak_filtre.suz(ham,simdi)
        if self.faz=='bekle':
            uzak=np.linalg.norm(TOP-ham)
            if uzak>SERBEST_R:self.serbest=True
            # Kalem şartı yok: parmak ucu topun üstünde kısa süre durunca yakalanır.
            if self.serbest and uzak<=YAKALA_R:
                if self.kilit_t is None:self.kilit_t=simdi
                if simdi-self.kilit_t>=KILIT_SN:
                    self.faz,self.yol,self.onceki_p,self.hareket_t='ciz',[TOP.copy()],p.copy(),simdi
                    self.ornekler=[(TOP.copy(),simdi)];self.ham_p=ham.copy();self.kapali=0
            else:self.kilit_t=None
            return
        if self.faz=='ciz':
            hareket=np.linalg.norm(ham-self.ham_p) if self.ham_p is not None else 0.
            self.ham_p=ham.copy()
            if hareket>4:
                self.hareket_t=simdi
                self.yol.append(p.copy() if hareket<.18*G else ham.copy());self.yol=self.yol[-120:]
                self.ornekler.append((self.yol[-1].copy(),simdi));self.ornekler=self.ornekler[-120:]
                self.param=ciz_sut(self.ornekler,self.boy(algi))
            uzaklik=np.linalg.norm(self.yol[-1]-TOP)
            if (uzaklik>=80 and simdi-self.hareket_t>=.22) or (len(self.yol)>=3 and self.yol[-1][1]<150):
                self.sut(simdi);return
            if simdi-self.hareket_t>=2:
                self.faz,self.kilit_t,self.el_id='bekle',None,None;self.yol=[];return
            self.onceki_p=p.copy()

    def sut(self,simdi,param=None):
        if param is not None: self.param=param
        self.fizik,v0=ucus(self.param)
        self.en_hizli=max(self.en_hizli,v0*3.6)
        self.ucus_t,self.faz=simdi,'ucus';self.serbest=False
        self.sanal.planla(self.fizik,self.yz_yon)
        self.gecmis.append(-1 if self.fizik[-1,0]<-.7 else 1 if self.fizik[-1,0]>.7 else 0)

    def kaleci(self,algi,simdi):
        if self.challenge: kid=self.ids[0] if self.ids else None
        elif len(self.ids)>=2: kid=self.ids[1-self.rol]
        else: return None
        pi=getattr(algi,'poz_id',[])
        p=next((p for i,p in zip(pi,algi.pozlar) if i==kid and ('poz',i) not in getattr(algi,'tahmini',[])),None)
        if p is not None and min(getattr(p[j],'visibility',0) for j in (11,12,23,24))<.5:p=None
        if p is not None:
            self.son_kaleci,self.kaleci_t=p,simdi
        elif simdi-self.kaleci_t<=.4:
            p=self.son_kaleci
        return p

    @staticmethod
    def kaleci_noktalar(p):
        ayak=(p[27].y+p[28].y)/2;bas=p[0].y
        s=1.9/max(.15,ayak-bas)
        cx=(p[23].x+p[24].x)/2
        def konum(j): return np.array([(cx-.5)*7.32+(p[j].x-cx)*s*G/Y, (ayak-p[j].y)*s])
        return [konum(j) for j in (15,16)],konum

    def karar(self,algi,kare,simdi):
        q=self.fizik[-1]
        if self.mod=='Frikik':
            baraj=self.fizik[np.argmin(abs(self.fizik[:,2]-9.15))]
            if abs(baraj[0])<1.3 and baraj[1]<2:
                return 'Baraj'
        p=self.kaleci(algi,simdi)
        if p is None and not self.challenge and len(self.ids)<2:
            return kale_karari(q,self.sanal.eldivenler(self.fizik,self.yz_yon))
        if p is None: return kale_karari(q)
        eller,konum=self.kaleci_noktalar(p)
        m=self.render_mask if self.render_mask is not None else maske_ver(kare)
        govde=None
        if m is not None:
            cx=(p[23].x+p[24].x)/2;ayak=(p[27].y+p[28].y)/2;s=1.9/max(.15,ayak-p[0].y)
            def govde(x,y):
                nx=cx+(x-(cx-.5)*7.32)/(s*G/Y);ny=ayak-y/s
                x0,x1=min(v.x for v in p)-.03,max(v.x for v in p)+.03
                return x0<=nx<=x1 and 0<=nx<1 and 0<=ny<1 and m[int(ny*m.shape[0]),int(nx*m.shape[1])]>.45
        return kale_karari(q,eller,govde)

    def atis_sonuc(self,karar,simdi):
        self.faz,self.atis_t,self.sonuc='atis_sonuc',simdi,karar
        self.atilan[self.rol]+=1
        if karar=='GOL':
            self.goller[self.rol]+=1;self.ag.vur(*self.fizik[-1,:2])
        if self.challenge:
            self.skor+=int(karar in ('Tutuş','Sektirme'))
        else:
            self.skor=max(self.goller)
        self.ses.cal('basari' if karar=='GOL' else 'bonk',.7)
        bitti=self.atilan[0]>=10 if self.challenge else self.atilan[0]>=5 if len(self.ids)<2 else min(self.atilan)>=5 and self.atilan[0]==self.atilan[1] and self.goller[0]!=self.goller[1]
        if bitti:
            self.bitir(simdi,f'{self.goller[0]} - {self.goller[1]} / {self.skor} kurtarış' if self.challenge else f'{self.goller[0]} - {self.goller[1]} / {self.en_hizli:.0f} km/sa')

    @staticmethod
    def top_ciz(kare,p,t):
        x,y,r=izdusus(p)
        gx,gy,_=izdusus((p[0],0,p[2]))
        cv2.ellipse(kare,(gx,gy),(max(6,r),max(3,r//4)),0,0,360,(25,50,30),-1,cv2.LINE_AA)
        cv2.circle(kare,(x,y),r,BEYAZ,-1,cv2.LINE_AA)
        cv2.circle(kare,(x,y),r,(75,80,90),2,cv2.LINE_AA)
        cv2.ellipse(kare,(x,y),(max(2,r//2),r),t*190,0,360,(65,70,80),2,cv2.LINE_AA)
        cv2.ellipse(kare,(x,y),(r,max(2,r//3)),t*120,0,360,(65,70,80),2,cv2.LINE_AA)

    def isle(self,kare,algi,simdi):
        asil=kare.copy();onceki=self.onceki_t
        dt=self.akis(kare,algi,simdi)
        gercek_dt=max(0.,simdi-onceki) if onceki is not None else 0.
        # Çim ve ışık yalnız alt zemin/çerçeveye biner; insanlar kamerada kalır.
        for j in range(14):
            yy=550+j*12
            cv2.line(kare,(0,yy),(G,yy),(65,100+(j%2)*15,60),1)
        for j in range(30):
            x=(j*149)%G;y=560+(j*37)%150
            cv2.line(kare,(x,y),(x+3,y-5),(65,115,65),1)
        for x in (45,G-45):
            cv2.line(kare,(x,100),(x,230),BEYAZ,3)
            for j in range(5):cv2.circle(kare,(x-18+j*9,98),5,SARI,-1,cv2.LINE_AA)
        if self.durum=='oyun':
            self.ag.adim(dt)
            for row in range(8):
                pts=np.array([izdusus((x,2.44-row*2.44/7,11+self.ag.z[row,j]*2))[:2] for j,x in enumerate(np.linspace(-3.66,3.66,16))],np.int32)
                cv2.polylines(kare,[pts],False,(190,205,210),2,cv2.LINE_AA)
            for col in range(16):
                pts=np.array([izdusus((-3.66+col*7.32/15,2.44-y*2.44/7,11+self.ag.z[y,col]*2))[:2] for y in range(8)],np.int32)
                cv2.polylines(kare,[pts],False,(190,205,210),2,cv2.LINE_AA)
            goal=np.array([izdusus((-3.66,0,11))[:2],izdusus((-3.66,2.44,11))[:2],izdusus((3.66,2.44,11))[:2],izdusus((3.66,0,11))[:2]],np.int32)
            cv2.polylines(kare,[goal],False,(70,80,90),12,cv2.LINE_AA)
            cv2.polylines(kare,[goal],False,BEYAZ,7,cv2.LINE_AA)
        if self.durum=='bekle':
            if algi.pozlar and not algi.eller:
                if self.tam_beden_t is None:self.tam_beden_t=simdi
                elif simdi-self.tam_beden_t>=1.5:self.durum,self.durum_t='hazir',simdi
            else:self.tam_beden_t=None
            panel(kare,950,75,1260,155,opak=.7)
            yazi_koy(kare,self.mod+' / değiştir',1100,95,26,hiza='orta')
            hedef=any(950<=px(e,9)[0]<=1260 and 75<=px(e,9)[1]<=155 for e in algi.eller)
            if self.mod_hedef.sec('mod' if hedef else None,simdi):self.tus(32)
            halka(kare,1100,140,self.mod_hedef.oran(simdi),r=14)
            u=min(1.,(simdi%3)/2.3)
            iz=np.array([(TOP[0]+190*v+40*math.sin(math.pi*v),TOP[1]-280*v) for v in np.linspace(0,u,25)],np.int32)
            self.top_ciz(kare,np.array([0.,R,0.]),simdi)
            cv2.polylines(kare,[iz],False,CAMGOBEGI,4,cv2.LINE_AA)
            x,y=map(int,iz[-1]);el_ikonu(kare,x,y+42,'taş',SARI,.6)
            cv2.line(kare,(x,y+42),(x,y),SARI,8,cv2.LINE_AA)
            cv2.circle(kare,(x,y),5,BEYAZ,-1,cv2.LINE_AA)
            yazi_koy(kare,'Topa dokun, kaleye yol çiz, dur!',G//2,650,28,hiza='orta')
            return kare
        if self.durum!='oyun':return kare
        kp=self.kaleci(algi,simdi)
        self.render_mask=maske_ver(asil) if kp is not None else None
        if (self.challenge or len(self.ids)>=2) and kp is None and self.faz=='ucus':
            if self.kayip_t is None:self.kayip_t=simdi
            self.ucus_t+=gercek_dt;self.durum_t+=gercek_dt
        else:self.kayip_t=None
        pi=getattr(algi,'poz_id',[])
        for kid,p in zip(pi,algi.pozlar):
            if kid not in self.ids:continue
            j=self.ids.index(kid);x,y=map(int,px(p,0));renk=YESIL if j==self.rol and not self.challenge else CAMGOBEGI
            yazi_koy(kare,('SOL' if j==0 else 'SAĞ')+' / '+('ŞUTÇU' if j==self.rol and not self.challenge else 'KALECİ'),int(np.clip(x,160,G-160)),max(130,y-70),28,renk=renk,hiza='orta')
        if kp is not None:
            # Gerçek kalecinin ellerini işaretle; çizilmiş insan/avatar yok.
            for j in (15,16):
                if getattr(kp[j],'visibility',0)>.5:cv2.circle(kare,tuple(map(int,px(kp,j))),24,CAMGOBEGI,3,cv2.LINE_AA)
        elif len(self.ids)<2 and not self.challenge:
            ucusta=self.faz in ('ucus','atis_sonuc') and self.sanal.plan is not None
            self.sanal.ciz(kare,simdi,self.ucus_t if ucusta else None,self.ucus_sn,
                           kurtardi=self.faz=='atis_sonuc' and self.sonuc=='Tutuş')
        if self.mod=='Frikik':
            for x in (-1.,-.33,.33,1.):
                a=izdusus((x,0,9.15));b=izdusus((x,2,9.15))
                cv2.line(kare,a[:2],b[:2],SARI,15,cv2.LINE_AA)
        if self.faz in ('bekle','ciz'):
            if self.challenge:
                if simdi-self.challenge_t>=2 and kp is not None:
                    power=min(1,.4+self.atilan[0]*.06)
                    self.sut(simdi,dict(guc=power,yatay=float(self.rng.uniform(-12,12)),dikey=merkez_acisi(power),falso=float(self.rng.uniform(-.6,.6))))
            else:self.kontrol(algi,simdi,dt)
            self.top_ciz(kare,np.array([0.,R,0.]),simdi)
            if self.kilit_t is not None:halka(kare,*TOP,min(1.,(simdi-self.kilit_t)/KILIT_SN),r=55,renk=YESIL)
            elif self.faz=='bekle' and self.serbest:
                halka(kare,*TOP,.5+.5*math.sin(simdi*4),r=int(YAKALA_R*.7),renk=SARI)
            if self.faz=='ciz':
                key=tuple(round(self.param[k],2) for k in ('guc','yatay','dikey','falso'))
                if key!=self.onizleme_key:self.onizleme_yol,_=ucus(self.param);self.onizleme_key=key
                for q in self.onizleme_yol[::3]:
                    x,y,_=izdusus(q);cv2.circle(kare,(x,y),4,SARI,-1,cv2.LINE_AA)
                if len(self.yol)>1:cv2.polylines(kare,[np.array(self.yol,np.int32)],False,CAMGOBEGI,4,cv2.LINE_AA)
                yazi_koy(kare,f'GÜÇ %{self.param["guc"]*100:.0f} / FALSO {self.param["falso"]:+.1f}',G//2,510,30,renk=SARI,hiza='orta')
        if self.faz=='ucus':
            sure=simdi-self.ucus_t
            ilerle=.85*sure/max(.1,self.ucus_sn-.35) if sure<self.ucus_sn-.35 else .85+.15*(sure-self.ucus_sn+.35)/.35
            ix=min(len(self.fizik)-1,int(max(0,ilerle)*(len(self.fizik)-1)))
            self.top_p=self.fizik[ix]
            iz=np.array([izdusus(self.fizik[j])[:2] for j in sorted(set(range(0,ix+1,3))|{ix})],np.int32)
            if len(iz)>1:
                isik=np.zeros_like(kare)
                cv2.polylines(isik,[iz],False,SARI,14,cv2.LINE_AA)
                cv2.addWeighted(kare,1.,isik,.28,0,dst=kare)
                cv2.polylines(kare,[iz],False,SARI,3,cv2.LINE_AA)
            self.top_ciz(kare,self.top_p,simdi)
            if sure>=self.ucus_sn and self.kayip_t is None:self.atis_sonuc(self.karar(algi,asil,simdi),simdi)
        elif self.faz=='atis_sonuc':
            t=simdi-self.atis_t;gol=self.sonuc=='GOL';renk=YESIL if gol else KIRMIZI
            sonuc='KURTARDI!' if self.sonuc in ('Tutuş','Sektirme') else 'GOL!' if gol else self.sonuc.upper()
            yazi_koy(kare,sonuc,G//4,420,int(72+16*max(0,1-t/.3)),renk=renk,hiza='orta')
            patlama(kare,G//2,450,t,renk)
            if 0<=t<.12:cv2.addWeighted(kare,.85,np.full_like(kare,renk),.15,0,dst=kare)
            if gol and self.fizik is not None:
                ix=min(len(self.fizik)-1,int(min(1.,t/2)*(len(self.fizik)-1)))
                self.top_ciz(kare,self.fizik[ix],t)
                yazi_koy(kare,'AĞIR ÇEKİM TEKRAR',G//2,560,28,hiza='orta')
            if t>=2:
                if len(self.ids)>=2 and not self.challenge:self.rol=1-self.rol
                self.yeni_atis(simdi)
        yazi_koy(kare,f'{self.goller[0]} : {self.goller[1]} / Şutçu {self.rol+1} / {self.en_hizli:.0f} km/sa',G//2,75,32,hiza='orta')
        ipucu='Nişan aldığın yere çiz ve dur' if self.faz=='ciz' else ('Parmağını topun üstüne getir' if self.serbest else 'Parmağını toptan çek') if self.faz=='bekle' else '' if len(self.ids)<2 and not self.challenge else 'Kaleci: bedeninle topu karşıla' if self.faz=='ucus' else 'Roller değişiyor...'
        if ipucu:yazi_koy(kare,ipucu,G//2,650,30,hiza='orta')
        if self.kayip_t is not None and simdi-self.kayip_t>=.5:yazi_koy(kare,'Kaleciyi göremiyorum; kadraja dön',G//2,475,32,renk=SARI,hiza='orta')
        return kare
