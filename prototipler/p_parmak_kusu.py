"""Kimlikli iki eli yayla izleyen kuşlar."""
import math
import cv2
import numpy as np
from cekirdek import G, Y, CAMGOBEGI, PEMBE, SARI, BEYAZ, px, panel, halka, yazi_koy
from filtre import OneEuro
from cekirdek import bindir_merkez,KIRMIZI
from gorsel import patlama,rozet
from oyun_akis import OyunAkisi, TutHedef, sutun_carpisti


class Prototip(OyunAkisi):
    AD, ACIKLAMA = 'Kanat Rotası', 'Parmağınla kuşu boşluklardan geçir!'
    IHTIYAC, SIRA = {'el'}, 31
    KUS_X, BOY, R = .3*G, 64, 22.4
    TIRMANMA_HIZI=460.
    KAMERA_PARLAKLIK=1.

    def __init__(self, ses):
        super().__init__(ses)
        self.mod, self.kuslar, self.sutunlar = 'Süzül', {}, []
        self.mod_hedef, self.rng = TutHedef(), np.random.default_rng(31)
        self.kazanan = None
        self.mesafe,self.pop_t,self.hiz_t,self.olum_t=0.,-10.,-10.,None
        self.goster_skor=0.;self.cizim_aralik=self.aralik
        self.kayip_t=None
        a=np.linspace((175,90,35),(205,165,95),Y).astype(np.uint8)
        self.gok=np.repeat(a[:,None,:],G,axis=1)
        self.spriteler={}


    def baslat(self, algi, simdi):
        super().baslat(algi, simdi)
        ids = getattr(algi, 'el_id', []) or list(range(len(algi.eller)))
        self.kuslar = {i: dict(y=Y/2, v=0., filtre=OneEuro(), son=simdi,
                              py=px(e, 8)[1], skor=0, canli=True, fiske=-10.)
                       for i, e in list(zip(ids, algi.eller))[:2]}
        self.sutunlar = [self.yeni_boru(G+100+j*430) for j in range(4)]
        self.kazanan = None
        self.mesafe,self.pop_t,self.hiz_t,self.olum_t=0.,-10.,-10.,None
        self.goster_skor=0.;self.kayip_t=None;self.cizim_aralik=self.aralik

    def tus(self, k, simdi=None):
        if k == 32 and self.durum == 'bekle':
            self.mod = 'Flappy' if self.mod == 'Süzül' else 'Süzül'

    @property
    def hiz(self):
        return 240*min(2.2,1.04**min(100,max(0,self.skor)))

    @property
    def aralik(self):
        oran=1-.25*(self.hiz/240-1)/1.2
        return 3.4*self.BOY*max(.75,oran)*(1.2 if self.mod=='Flappy' else 1.)

    def yeni_boru(self,x):
        return dict(x=x,y=float(self.rng.uniform(210,510)),gecen=set(),
                    faz=float(self.rng.uniform(0,2*math.pi)),frekans=float(self.rng.uniform(.85,1.15)),genlik=35.)

    def bosluk_y(self,p,dt=0.):
        p.setdefault('faz',0.);p.setdefault('frekans',1.);p.setdefault('genlik',35.)
        alt,ust=self.aralik/2+40,Y-self.aralik/2-40
        if 'cy' not in p:p['cy']=float(np.clip(p['y']+p['genlik']*math.sin(p['faz']),alt,ust))
        if dt>0:
            # Fazı entegre etmek skor değişiminde boşluğun sıçramasını önler.
            omega=float(np.clip((.6+.035*self.skor)*p['frekans'],.6,1.3))
            p['faz']=(p['faz']+omega*dt)%(2*math.pi)
            p['genlik']+=float(np.clip(min(35+7*self.skor,120)-p['genlik'],-42*dt,42*dt))
            hedef=float(np.clip(p['y']+p['genlik']*math.sin(p['faz']),alt,ust))
            p['cy']+=float(np.clip(hedef-p['cy'],-.6*self.TIRMANMA_HIZI*dt,.6*self.TIRMANMA_HIZI*dt))
            p['cy']=float(np.clip(p['cy'],alt,ust))
        return p['cy']

    def _yeniden_bagla(self, eller, tahmini):
        """El 0,6 sn'den uzun kaybolunca yeni kimlikle döner; kayıp kuşu sahipsiz en yakın ele bağla."""
        kayip = [i for i, b in self.kuslar.items() if b['canli'] and i not in eller]
        bos = [i for i in eller if i not in self.kuslar and ('el', i) not in tahmini]
        esle = {}
        for k in sorted(kayip, key=lambda k: min((abs(px(eller[j], 8)[1]-self.kuslar[k]['py']) for j in bos), default=0)):
            if not bos:
                break
            j = min(bos, key=lambda j: abs(px(eller[j], 8)[1]-self.kuslar[k]['py']))
            esle[k] = j
            bos.remove(j)
        if esle:  # sıra korunur: kuşun yeri ve rengi listedeki indeksinden gelir
            self.kuslar = {esle.get(i, i): b for i, b in self.kuslar.items()}

    def adim(self, algi, simdi, dt):
        ids = getattr(algi, 'el_id', []) or list(range(len(algi.eller)))
        eller = dict(zip(ids, algi.eller))
        tahmini = getattr(algi, 'tahmini', set())
        self._yeniden_bagla(eller, tahmini)
        # Eli görünmeyen kuş yerinde bekler ve çarpmaz; öteki oyuncu oynamaya devam eder.
        # Hepsi kayıpsa oyun durur. 5 sn dönmeyen elenir (sonsuza dek donma yok).
        canli = [i for i, b in self.kuslar.items() if b['canli']]
        kayip = [i for i in canli if i not in eller or ('el', i) in tahmini]
        for i in canli:
            b = self.kuslar[i]
            if i in kayip:
                if b.get('kayip') is None:
                    b['kayip'] = simdi
                    print(f"[kus] el kayboldu {i}; redler={getattr(algi, 'redler', [])[-6:]}", flush=True)
                elif simdi - b['kayip'] >= 5:
                    b['canli'] = False
            elif b.get('kayip') is not None:
                b['kayip'], b['py'], b['filtre'] = None, px(eller[i], 8)[1], OneEuro()
        self.kayip_t = min((self.kuslar[i]['kayip'] for i in kayip if self.kuslar[i]['canli']), default=None)
        if self.kayip_t is not None and all(i in kayip for i, b in self.kuslar.items() if b['canli']):
            self.durum_t += dt
            return
        self.cizim_aralik=self.aralik
        self.mesafe+=self.hiz*dt
        for kimlik, b in self.kuslar.items():
            if not b['canli']:
                continue
            el = eller.get(kimlik)
            if el is not None and ('el', kimlik) not in tahmini:
                py = px(el, 8)[1]
                hiz = (py-b['py'])/max(dt, .001)
                b['py'], b['son'] = py, simdi
                hedef = float(b['filtre'](np.clip((py-.15*Y)/.714, self.R, Y-self.R), simdi))
                if self.mod == 'Flappy' and hiz < -650 and simdi-b['fiske'] >= .12:
                    b['v'], b['fiske'] = -self.TIRMANMA_HIZI, simdi
            else:
                continue
            if self.mod == 'Süzül':
                w, fark = 18., b['y']-hedef
                c, s = b['v']+w*fark, math.exp(-w*dt)
                b['y'], b['v'] = hedef+(fark+c*dt)*s, (b['v']-w*c*dt)*s
            else:
                b['y'] += b['v']*dt+500*dt*dt
                b['v'] += 1000*dt
                if b['y'] < self.R or b['y'] > Y-self.R:
                    b['canli'] = False
        for p in self.sutunlar:
            p['x'] -= self.hiz*dt
            cy = self.bosluk_y(p,dt)
            for kimlik, b in self.kuslar.items():
                if not b['canli'] or b.get('kayip') is not None:
                    continue
                if sutun_carpisti(self.KUS_X-80*list(self.kuslar).index(kimlik), b['y'], self.R, p['x'], 86, cy, self.cizim_aralik):
                    b['canli'] = False
                elif p['x']+86 < self.KUS_X-80*list(self.kuslar).index(kimlik) and kimlik not in p['gecen']:
                    p['gecen'].add(kimlik)
                    b['skor'] += 1
                    self.pop_t=simdi
                    if b['skor']%5==0:self.hiz_t=simdi
                    self.ses.cal('ding', .4)
            if p['x'] < -86:
                x=max(q['x'] for q in self.sutunlar)+430
                p.clear();p.update(self.yeni_boru(x))
                self.bosluk_y(p)
        self.skor = max((b['skor'] for b in self.kuslar.values()), default=0)
        canli = [i for i, b in self.kuslar.items() if b['canli']]
        if not canli or len(self.kuslar) == 2 and len(canli) == 1:
            self.kazanan = canli[0] if len(canli) == 1 else None
            self.olum_t=simdi
            self.ses.cal('bonk',.6)
            self.bitir(simdi, f'Oyuncu {list(self.kuslar).index(self.kazanan)+1} kazandı!' if self.kazanan is not None else 'Tur bitti')

    def kuş(self,kare,x,y,v,j,simdi):
        wing=int(simdi*12)%3;angle=int(np.clip(v/20,-25,25)//5)*5
        key=(wing,angle,j)
        if key not in self.spriteler:
            s=np.zeros((100,100,4),np.uint8);renk=(20,205,255,255) if j==0 else (185,85,255,255)
            cv2.fillPoly(s,[np.array([(26,46),(8,33),(12,56),(28,61)],np.int32)],renk)
            cv2.ellipse(s,(50,50),(32,25),0,0,360,(30,70,100,255),-1,cv2.LINE_AA)
            cv2.ellipse(s,(50,48),(30,23),0,0,360,renk,-1,cv2.LINE_AA)
            cv2.ellipse(s,(53,59),(20,12),0,0,360,(150,230,255,255),-1,cv2.LINE_AA)
            cv2.fillPoly(s,[np.array([(76,45),(94,51),(77,57)],np.int32)],(40,110,245,255))
            cv2.circle(s,(65,39),10,(255,255,255,255),-1,cv2.LINE_AA)
            cv2.circle(s,(68,39),5,(25,35,50,255),-1,cv2.LINE_AA)
            cv2.circle(s,(70,36),2,(255,255,255,255),-1)
            cv2.ellipse(s,(37,52+(wing-1)*6),(17,(7,14,20)[wing]),-25,0,360,(25,145,215,255),-1,cv2.LINE_AA)
            self.spriteler[key]=cv2.warpAffine(s,cv2.getRotationMatrix2D((50,50),-angle,1),(100,100),flags=cv2.INTER_LINEAR)
        bindir_merkez(kare,self.spriteler[key],int(x),int(y))

    def dekor(self,kare,simdi):
        cv2.addWeighted(kare,.42,self.gok,.58,0,dst=kare)
        d=self.mesafe if self.durum=='oyun' else simdi*60
        cv2.circle(kare,(1080,175),70,(140,215,255),-1,cv2.LINE_AA)
        for j in range(7):
            x=int((j*250-d*.15)%(G+250)-125);y=160+(j%3)*70
            for dx,dy,r in ((-30,0,28),(0,-10,40),(35,0,30)):
                cv2.circle(kare,(x+dx,y+dy),r,(220,225,235),-1,cv2.LINE_AA)
        for j in range(11):
            x=int((j*145-d*.3)%(G+160)-80)
            cv2.rectangle(kare,(x,470-j%3*35),(x+95,650),(140,115,80),-1)
            for yy in range(490-j%3*35,620,30):cv2.line(kare,(x+12,yy),(x+80,yy),(170,150,105),3)
        for j in range(6):
            x=int((j*320-d*.55)%(G+400)-200)
            cv2.ellipse(kare,(x,720),(260,90+j%2*35),0,180,360,(80,135,75),-1,cv2.LINE_AA)
        cv2.rectangle(kare,(0,700),(G,Y),(55,115,55),-1)
        for x in range(0,G,32):
            xx=int((x-d*.8)%G);cv2.line(kare,(xx,718),(xx+7,703),(115,200,105),2)

    def boru(self,kare,x,cy):
        ust,alt=int(cy-self.cizim_aralik/2),int(cy+self.cizim_aralik/2);x=int(x)
        for y0,y1,end in ((65,ust,ust-24),(alt,Y,alt)):
            if y1<=y0:continue
            cv2.rectangle(kare,(x+5,y0),(x+92,y1),(25,55,30),-1)
            cv2.rectangle(kare,(x,y0),(x+86,y1),(65,145,55),-1)
            cv2.rectangle(kare,(x+9,y0),(x+25,y1),(140,225,105),-1)
            cv2.rectangle(kare,(x+70,y0),(x+86,y1),(35,95,35),-1)
            cv2.rectangle(kare,(x-7,end),(x+93,end+24),(75,175,65),-1)
            cv2.rectangle(kare,(x-7,end),(x+93,end+24),(165,235,125),3)
            cv2.line(kare,(x+3,end+5),(x+83,end+5),(205,255,165),3)
        for yy,d in ((ust-14,-1),(alt+14,1)):
            cv2.arrowedLine(kare,(x+43,yy-d*5),(x+43,yy+d*5),(220,255,170),2,cv2.LINE_AA,tipLength=.6)

    def isle(self,kare,algi,simdi):
        dt=.033 if self.onceki_t is None else max(0.,min(.125,simdi-self.onceki_t))
        if self.durum=='oyun':self.adim(algi,simdi,dt)
        if self.durum=='bekle':self.cizim_aralik=self.aralik
        self.dekor(kare,simdi)
        offset=0.
        if self.olum_t is not None:offset=min(.3,max(0.,simdi-self.olum_t))*self.hiz*.25
        if self.durum in ('oyun','sonuc'):
            for p in self.sutunlar:
                cy=self.bosluk_y(p)
                self.boru(kare,p['x']-offset,cy)
            for j,b in enumerate(self.kuslar.values()):
                x=self.KUS_X-j*80;y=b['y']
                self.kuş(kare,x,y,b['v'],j,simdi)
                yazi_koy(kare,('SOL','SAĞ')[j],int(x),int(y)-65,26,renk=(SARI,PEMBE)[j],hiza='orta')
                if b['canli'] and self.durum=='oyun':
                    cv2.line(kare,(int(x),int(y)),(int(x+70),int(b['py'])),(SARI,PEMBE)[j],1)
                if self.olum_t is not None and not b['canli']:
                    t=simdi-self.olum_t;patlama(kare,x,y,t,(SARI,PEMBE)[j])
                    if 0<=t<.12:
                        kare[:]=np.roll(kare,int(5*math.sin(t*120)),axis=1)
                        panel(kare,0,0,G,Y,renk=KIRMIZI,opak=.15)
        elif self.durum=='bekle':
            self.boru(kare,(1100-simdi*80)%G,370)
            self.kuş(kare,180,340+60*math.sin(simdi*1.5),0,0,simdi)
        self.akis(kare,algi,simdi)
        self.goster_skor+=(self.skor-self.goster_skor)*min(1.,dt*12)
        if self.durum=='oyun':
            yazi_koy(kare,str(int(round(self.goster_skor))),G//2,85,72,renk=SARI,hiza='orta')
            yazi_koy(kare,f'Rekor: {max(self.rekorlar+[self.skor])}',G//2,165,28,hiza='orta')
            if self.kayip_t is not None and simdi-self.kayip_t>=.5:yazi_koy(kare,'Seni göremiyorum / elini göster',G//2,270,36,hiza='orta')
            if 0<=simdi-self.pop_t<.7:
                patlama(kare,self.KUS_X,300,simdi-self.pop_t)
                yazi_koy(kare,'+1',int(self.KUS_X),int(250-70*(simdi-self.pop_t)),40,renk=SARI,hiza='orta')
            if 0<=simdi-self.hiz_t<1.2:yazi_koy(kare,'HIZLANIYOR!',G//2,225,42,renk=SARI,hiza='orta')
        if self.durum=='sonuc':rozet(kare,G//2,530,self.skor)
        if self.durum=='bekle':
            panel(kare,960,80,1240,160,opak=.8)
            yazi_koy(kare,self.mod+' / değiştir',1100,100,28,hiza='orta')
            # Elle mod değiştirme kapalı: iki kişide kalkık el kazara Flappy'ye geçirip kuşu
            # düşürüyordu (Enes 2026-10-13). Mod yalnız operatör tuşuyla (boşluk) değişir.
        return kare
