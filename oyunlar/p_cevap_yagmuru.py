"""Üç şeritli, kimlik başına puanlanan ortak bilgi oyunu."""
import json
import math
import textwrap
from pathlib import Path
import cv2
import numpy as np
import cekirdek as ck
from cekirdek import G, Y, px, panel, yazi_koy, SARI, YESIL, KIRMIZI, BEYAZ, CAMGOBEGI, PEMBE
from oyun_akis import OyunAkisi, TutHedef
from gorsel import patlama
from cekirdek import yazi_sprite, bindir_merkez

VERI = Path(__file__).parent / 'veri'
_maskeci = None


def maske_ver(kare):
    global _maskeci
    if _maskeci is None:
        _maskeci = ck.Maskeci()
    return _maskeci.ver(kare)


def banka_dogrula(banka):
    ids = set()
    for s in banka:
        assert {'id', 'kategori', 'tip', 'soru', 'secenekler', 'dogru_indeks', 'zorluk', 'kaynak'} <= s.keys()
        assert s['id'] not in ids and s['tip'] in ('dy', 'coktan') and s['zorluk'] in (1, 2, 3)
        assert 2 <= len(s['secenekler']) <= 3 and 0 <= s['dogru_indeks'] < len(s['secenekler'])
        assert len(set(s['secenekler'])) == len(s['secenekler'])
        ids.add(s['id'])
    return banka


def matematik(rng, zorluk=1):
    a, b = int(rng.integers(2, 11+zorluk*5)), int(rng.integers(2, 11))
    op = ('+', '−', '×', 'kare')[int(rng.integers(4))]
    dogru = {'+': a+b, '−': a-b, '×': a*b, 'kare': a*a}[op]
    sec = [str(dogru), str(dogru+int(rng.integers(1, 6))), str(dogru-int(rng.integers(1, 6)))]
    rng.shuffle(sec)
    return dict(id=f'm-{a}-{b}-{op}', kategori='matematik', tip='coktan',
                soru=f'{a}² = ?' if op == 'kare' else f'{a} {op} {b} = ?', secenekler=sec,
                dogru_indeks=sec.index(str(dogru)), zorluk=zorluk, kaynak='Hesaplanan işlem', islem=(a, b, op))


class Prototip(OyunAkisi):
    AD, ACIKLAMA = 'Bilgi Yağmuru', 'Doğru cevabın şeridinde dur!'
    IHTIYAC, SIRA = {'poz', 'yuz', 'kalabalik'}, 32
    KAPI, TUR_SN = {'poz_omuz_min': .035, 'yuz_goz_min': .015}, 100.  # arkadaki küçük yüzler de sayılır
    KENDI_IMLECI = True  # parmak izi çizilmez: bu oyunda beden konumu oynar (Enes 2026-10-13)

    def __init__(self, ses):
        super().__init__(ses)
        self.banka = banka_dogrula(json.loads((VERI/'sorular.json').read_text(encoding='utf-8')))
        self.banka += banka_dogrula(json.loads((VERI/'ozel_sorular.json').read_text(encoding='utf-8')))
        self.rng = np.random.default_rng()
        self.mod, self.mod_hedef = 'Puan', TutHedef()
        self.oyuncular, self.pozlar, self.sira = {}, {}, []
        self.toplan_t = None
        self.soru, self.faz, self.soru_no = self.banka[0], 'soru', 0
        self.soru_t, self.kilit, self.puanlandi = 0., None, False
        self.sinir_kayma, self.kalibre = 0., False
        self.gosterilen, self.poplar, self.yazilar = {}, {}, {}
        self.kayip_t, self.son_sayim = None, None
        self.kisiler, self.kilit_dagilim = [], None
        try:
            self.sinir_kayma = float(json.loads((VERI/'serit_ayar.json').read_text())['kayma'])
        except (OSError, ValueError, KeyError):
            pass

    def tus(self, k):
        if k == 32 and self.durum == 'bekle':
            self.mod = 'Hayatta Kalma' if self.mod == 'Puan' else 'Puan'
        elif k in (ord('s'), ord('S')):
            self.kalibre = not self.kalibre
        elif self.kalibre and k in (81, 83, 2424832, 2555904):
            self.sinir_kayma = float(np.clip(self.sinir_kayma+(-.01 if k in (81, 2424832) else .01), -.1, .1))
            (VERI/'serit_ayar.json').write_text(json.dumps({'kayma': self.sinir_kayma}))

    def kisi_guncelle(self, algi):
        ids = getattr(algi, 'poz_id', []) or list(range(len(algi.pozlar)))
        self.pozlar = {}
        for kimlik, p in list(zip(ids, algi.pozlar))[:6]:
            if ('poz', kimlik) in getattr(algi, 'tahmini', []):
                continue
            ij = (23, 24) if min(getattr(p[i], 'visibility', 0) for i in (23, 24)) >= .6 else (11, 12)
            if min(getattr(p[i], 'visibility', 0) for i in ij) < .6:
                continue
            x = sum(p[i].x for i in ij)/2
            if .03 <= x <= .97:
                self.pozlar[kimlik] = p
                self.oyuncular.setdefault(kimlik, dict(x=x, puan=0, seri=0, tac=False, elendi=False, durum='bekle'))['x'] = x
        self.kalabalik_guncelle(algi)

    def kalabalik_guncelle(self, algi):
        """Pozlu oyuncular + pozu çıkmayan (arkada, kısmen kapalı) yüzler: şeritteki herkes sayılır."""
        kisiler = [dict(x=self.oyuncular[i]['x'], y=float(p[0].y), oyuncu=i) for i, p in self.pozlar.items()]
        for yuz in getattr(algi, 'yuzler', None) or []:
            try:
                fx, fy = float(yuz[33].x + yuz[263].x)/2, float(yuz[1].y)
            except (IndexError, AttributeError, TypeError):
                continue
            if not .03 <= fx <= .97 or any(abs(float(p[0].x)-fx) < .06 and abs(float(p[0].y)-fy) < .12 for p in self.pozlar.values()):
                continue
            kisiler.append(dict(x=fx, y=fy, oyuncu=None))
        self.kisiler = kisiler

    def serit_sayilari(self, n=None):
        n = n or len(self.soru['secenekler'])
        say = [0]*n
        for k in self.kisiler:
            say[min(n-1, self.serit(k['x']))] += 1
        return say

    def serit(self, x):
        n = len(self.soru['secenekler'])
        return max(0, min(n-1, int((x-self.sinir_kayma)*n)))

    def cizgide(self, x):
        n = len(self.soru['secenekler'])
        return any(abs(x-(j/n+self.sinir_kayma)) <= .03 for j in range(1, n))

    def baslat(self, algi, simdi):
        super().baslat(algi, simdi)
        self.oyuncular = {}
        self.kisi_guncelle(algi)
        self.soru_no = 0
        self.gosterilen, self.poplar = {}, {}
        self.kayip_t = None
        self.yeni_soru(simdi)

    def yeni_soru(self, simdi):
        self.soru_no += 1
        # Basit işlem soruları havuzdan çıkarıldı (Enes 2026-10-13); yalnız bilgi bankası
        self.soru = self.banka[int(self.rng.integers(len(self.banka)))]
        self.soru_t, self.kilit, self.puanlandi, self.faz = simdi, None, False, 'soru'
        self.kilit_dagilim = None
        self.yazilar, self.poplar = {}, {}

    def puanla(self, simdi):
        if self.puanlandi:
            return
        self.puanlandi = True
        for kimlik, serit in (self.kilit or {}).items():
            o = self.oyuncular[kimlik]
            if o['elendi'] or kimlik not in self.pozlar:
                continue
            dogru = serit == self.soru['dogru_indeks']
            o['durum'] = 'dogru' if dogru else 'yanlis'
            o['seri'] = o['seri']+1 if dogru else 0
            o['tac'] = o['seri'] >= 3
            if dogru:
                arti = 100 + (100 if o['seri'] >= 3 else 50 if o['seri'] == 2 else 0)
                o['puan'] += arti
                self.poplar[kimlik] = (simdi, arti)
            elif self.mod == 'Hayatta Kalma':
                o['elendi'] = True
            self.ses.cal('ding' if dogru else 'bonk', .5)
        self.skor = max((o['puan'] for o in self.oyuncular.values()), default=0)
        canli = [i for i,o in self.oyuncular.items() if not o['elendi']]
        if self.mod == 'Hayatta Kalma' and len(self.oyuncular) > 1 and len(canli) <= 1:
            self.podyum(simdi)

    def podyum(self, simdi):
        self.sira = sorted(self.oyuncular, key=lambda i: (not self.oyuncular[i]['elendi'], self.oyuncular[i]['puan']), reverse=True)
        self.bitir(simdi, 'Podyum')
        self.faz = 'podyum'

    def adim(self, algi, simdi):
        self.kisi_guncelle(algi)
        if self.durum == 'bekle':
            if not self.kisiler:
                self.toplan_t = None
            elif self.toplan_t is None:
                self.toplan_t = simdi
            elif simdi-self.toplan_t >= 1.5:
                self.durum, self.durum_t = 'hazir', simdi
        elif self.durum == 'hazir' and simdi-self.durum_t >= 3:
            self.baslat(algi, simdi)
        elif self.durum == 'sonuc' and simdi-self.durum_t >= 5:
            self.durum, self.toplan_t = 'bekle', None
        elif self.durum == 'oyun':
            zaman = simdi-self.soru_t
            dusun = 6. if len(self.oyuncular)>1 else max(3.5, 6.-.5*(self.soru_no-1))
            carpis = 2.5+dusun
            self.faz = 'soru' if zaman < 2.5 else 'yaklas' if zaman < carpis-.4 else 'kilit' if zaman < carpis else 'carpis' if zaman < carpis+1.5 else 'puan'
            if zaman >= carpis-.4 and self.kilit is None:
                self.kilit = {i: self.serit(self.oyuncular[i]['x']) for i in self.pozlar}
                self.kilit_dagilim = self.serit_sayilari()
            if zaman >= carpis:
                self.puanla(simdi)
            if self.durum == 'oyun' and zaman >= carpis+4.:  # 2.5 sn cevap analizi görünür
                if self.soru_no >= 6:
                    self.podyum(simdi)
                else:
                    self.yeni_soru(simdi)

    def seritleri_ciz(self, kare, n, renkler, etiket):
        """Tam boy renkli şeritler: nerede durulacağı uzaktan belli olsun. Altta cevap ve şeritteki kişi sayısı."""
        say = self.serit_sayilari(n)
        for j in range(n):
            x0 = int(np.clip((j/n+self.sinir_kayma)*G, 0, G))
            x1 = int(np.clip(((j+1)/n+self.sinir_kayma)*G, 0, G))
            panel(kare, x0, 225, x1, Y, renk=renkler[j], opak=.13 if say[j] else .07)
            if j:
                cv2.line(kare, (x0, 225), (x0, Y), renkler[j], 6, cv2.LINE_AA)
                cv2.line(kare, (x0, 225), (x0, Y), BEYAZ, 2, cv2.LINE_AA)
            if etiket:
                metin = self.soru['secenekler'][j]
                panel(kare, x0+8, 606, x1-8, Y-6, renk=renkler[j], opak=.6)
                yazi_koy(kare, f'{"ABC"[j]}  {metin}', (x0+x1)//2, 610, 36 if len(metin) <= 12 else 28, renk=BEYAZ, hiza='orta')
                yazi_koy(kare, f'{say[j]} kişi burada', (x0+x1)//2, 664, 26, renk=BEYAZ, hiza='orta')

    def rozetleri_ciz(self, kare, renkler, simdi):
        """Herkesin başının üstünde durduğu şeridin harfi: kim hangi cevapta, tek bakışta."""
        for k in self.kisiler:
            j = min(self.serit(k['x']), len(self.soru['secenekler'])-1)
            x, y = int(k['x']*G), max(getattr(self, 'soru_alt', 0)+30, int(k['y']*Y)-80)  # soru yazısını örtmesin
            sinirda = self.kilit is None and self.cizgide(k['x'])
            r = 24 + (int(4*math.sin(simdi*8)) if sinirda else 0)
            cv2.circle(kare, (x, y), r, renkler[j], -1, cv2.LINE_AA)
            cv2.circle(kare, (x, y), r+3, SARI if sinirda else BEYAZ, 3, cv2.LINE_AA)
            yazi_koy(kare, '?' if sinirda else 'ABC'[j], x, y-18, 30, renk=BEYAZ, hiza='orta')
        if any(self.kilit is None and self.cizgide(k['x']) for k in self.kisiler):
            yazi_koy(kare, 'Çizgide durma: bir şeridin içine geç!', G//2, 560, 28, renk=SARI, hiza='orta')

    def analiz_ciz(self, kare, renkler):
        """Cevap analizi: kilit anında hangi şıkta kaç kişi vardı."""
        d = self.kilit_dagilim or []
        top = sum(d)
        if not top:
            return
        dj, w = self.soru['dogru_indeks'], 680
        x0, y0 = G//2-w//2, 236
        panel(kare, x0, y0, x0+w, y0+58+len(d)*56, opak=.8, kenar=BEYAZ)
        yazi_koy(kare, f'Doğru cevapta {d[dj]} / {top} kişi', G//2, y0+8, 34, renk=YESIL if 2*d[dj] >= top else SARI, hiza='orta')
        for j, adet in enumerate(d):
            yy, oran = y0+58+j*56, adet/top
            cv2.rectangle(kare, (x0+16, yy), (x0+16+int((w-32)*oran), yy+46), YESIL if j == dj else renkler[j], -1)
            cv2.rectangle(kare, (x0+16, yy), (x0+w-16, yy+46), YESIL if j == dj else renkler[j], 2)
            isaret = 'DOĞRU: ' if j == dj else ''
            yazi_koy(kare, f'{isaret}{"ABC"[j]}  {self.soru["secenekler"][j]}: {adet} kişi (%{round(100*oran)})', x0+28, yy+6, 28, renk=BEYAZ)

    def isle(self, kare, algi, simdi):
        asil = kare.copy()
        kare[:] = cv2.convertScaleAbs(kare, alpha=.85)
        onceki, self.onceki_t = self.onceki_t, simdi
        dt = max(0., simdi-onceki) if onceki is not None else 0.
        self.kisi_guncelle(algi)
        if self.durum == 'oyun' and not self.kisiler:
            if self.kayip_t is None: self.kayip_t = simdi
            self.soru_t += dt; self.durum_t += dt
        else:
            self.kayip_t = None
            self.adim(algi, simdi)
        n = len(self.soru['secenekler'])
        renkler = (CAMGOBEGI, PEMBE, SARI)
        self.seritleri_ciz(kare, n, renkler, self.durum == 'oyun')
        yazi_koy(kare, self.AD, G//2, 8, 48, renk=SARI, hiza='orta')
        if self.durum == 'bekle':
            yazi_koy(kare, self.ACIKLAMA, G//2, 265, 42, hiza='orta')
            yazi_koy(kare, 'Kadraja gir; cevap için sağa / sola geç', G//2, 325, 30, hiza='orta')
            for j in range(3):
                x=int(G*(j+.5)/3)
                for d in (-18,18): cv2.ellipse(kare,(x+d,550+int(8*math.sin(simdi*2+j))),(12,25),d,0,360,renkler[j],3)
            yazi_koy(kare,'DOĞRU',G//4,430,42,renk=YESIL,hiza='orta')
            yazi_koy(kare,'YANLIŞ',3*G//4,430,42,renk=KIRMIZI,hiza='orta')
            panel(kare, 950, 70, 1260, 155, opak=.7)
            yazi_koy(kare, self.mod+' / değiştir', 1100, 90, 26, hiza='orta')
            h = any(950 <= px(e,9)[0] <= 1260 and 70 <= px(e,9)[1] <= 155 for e in algi.eller)
            if self.mod_hedef.sec('mod' if h else None, simdi): self.tus(32)
            ck.halka(kare, 1100, 138, self.mod_hedef.oran(simdi), r=15)
        elif self.durum == 'hazir':
            rakam=max(1,3-int(simdi-self.durum_t))
            yazi_koy(kare,'Hazır mısın?',G//2,250,36,hiza='orta')
            yazi_koy(kare,str(rakam),G//2,310,int(115+20*(1-(simdi-self.durum_t)%1)),hiza='orta')
            if self.son_sayim!=rakam: self.ses.cal('ding',.4);self.son_sayim=rakam
        elif self.durum == 'sonuc':
            panel(kare,250,245,G-250,590,opak=.75)
            yazi_koy(kare, 'PODYUM', G//2, 250, 54, renk=SARI, hiza='orta')
            for j,i in enumerate(self.sira[:3]):
                isim=list(self.oyuncular).index(i)+1
                yazi_koy(kare, f'{j+1}. P{isim}: {self.oyuncular[i]["puan"]}', G//2, 330+j*65, 38,renk=renkler[(isim-1)%3],hiza='orta')
            yazi_koy(kare,'Tekrar: kadraja gir',G//2,550,28,hiza='orta')
            for j in range(30): cv2.circle(kare,(int((j*173+simdi*20)%G),int((j*83+(simdi-self.durum_t)*95)%Y)),4,renkler[j%3],-1)
        else:
            satirlar=textwrap.wrap(self.soru['soru'],width=43)
            panel(kare,30,68,G-30,75+len(satirlar)*59,opak=.55)
            self.soru_alt=75+len(satirlar)*59
            for satir,metin in enumerate(satirlar): yazi_koy(kare,metin,G//2,70+satir*59,54,hiza='orta')
            zaman=simdi-self.soru_t
            dusun=6. if len(self.oyuncular)>1 else max(3.5,6.-.5*(self.soru_no-1))
            carpis=2.5+dusun
            ilerle=float(np.clip((zaman-2.5)/dusun,0,1))
            for j,sec in enumerate(self.soru['secenekler'] if self.faz!='puan' else []):  # analizde kartlar çekilir
                x=int(G/2+(G*(j+.5)/n-G/2)*(.4+.6*ilerle))
                yy=int(330+180*ilerle)
                if self.faz in ('carpis','puan'):
                    t=max(0.,zaman-carpis);dusme=.35*min(.3,t)+max(0.,t-.3)
                    yy+=int(min(1.4,dusme)*100)
                renk=YESIL if self.faz in ('carpis','puan') and j==self.soru['dogru_indeks'] else renkler[j]
                key=(sec,renk)
                if key not in self.yazilar:self.yazilar[key]=yazi_sprite(sec,60,renk)
                sprite=self.yazilar[key];boy=int(min(G/n-45,sprite.shape[1])*(.65+.35*ilerle))
                bindir_merkez(kare,sprite,x,yy,boyut=boy,aci=6*math.sin(simdi*2+j))
            panel(kare,30,210,G-30,218,renk=CAMGOBEGI,opak=.2)
            cv2.line(kare,(30,214),(int(30+(G-60)*ilerle),214),SARI,6)
            if self.faz in ('kilit','carpis'):
                yazi_koy(kare,'KİLİT' if self.faz=='kilit' else 'DOĞRU: '+self.soru['secenekler'][self.soru['dogru_indeks']],G//2,235,32,renk=YESIL,hiza='orta')
            maske=maske_ver(asil) if self.faz=='carpis' and self.pozlar else None
            if maske is not None:maske=(cv2.resize(maske,(G,Y),interpolation=cv2.INTER_NEAREST)>.45).astype(np.uint8)*255
            for i,p in self.pozlar.items():
                o=self.oyuncular[i];j=list(self.oyuncular).index(i);x,y=map(int,px(p,0))
                renk=YESIL if o['durum']=='dogru' else KIRMIZI if o['durum']=='yanlis' else renkler[j%3]
                if self.faz=='carpis':
                    xy=np.array([px([q],0) for q in p if getattr(q,'visibility',0)>.5],dtype=np.int32)
                    if len(xy):
                        a=np.clip(xy.min(axis=0)-40,(0,0),(G,Y)).astype(int);b=np.clip(xy.max(axis=0)+40,(0,0),(G,Y)).astype(int)
                        if np.all(b>a):
                            if maske is not None:
                                tone=cv2.add(cv2.convertScaleAbs(asil[a[1]:b[1],a[0]:b[0]],alpha=.7),tuple(float(c)*.3 for c in renk)+(0.,))
                                cv2.copyTo(tone,maske[a[1]:b[1],a[0]:b[0]],kare[a[1]:b[1],a[0]:b[0]])
                            else:cv2.rectangle(kare,tuple(a),tuple(b),renk,3)
                    patlama(kare,x,int(Y*.5),zaman-carpis,renk)
                    if o['durum']=='yanlis':
                        kelime=self.soru['secenekler'][(self.kilit or {}).get(i,self.serit(o['x']))]
                        omuz=max(230,int((p[11].y+p[12].y)*Y/2))
                        for h,harf in enumerate(kelime[:16]):
                            hx=int(x-45+(h*19)%90);hy=omuz+(h%3)*18+int(min(1.,max(0.,zaman-carpis))*65)
                            yazi_koy(kare,harf,hx,hy,30,renk=KIRMIZI,hiza='orta')
                yazi_koy(kare,f'P{j+1} {o["puan"]}',int(np.clip(o['x']*G+30,45,G-90)),max(self.soru_alt+30,y-80)-34,24,renk=renk)
                if o['tac']:
                    cv2.polylines(kare,[np.array([(x-25,y-15),(x-30,y-45),(x-10,y-30),(x,y-50),(x+10,y-30),(x+30,y-45),(x+25,y-15)],np.int32)],True,SARI,4)
                if i in self.poplar:
                    t0,arti=self.poplar[i];t=simdi-t0
                    if 0<=t<1:yazi_koy(kare,f'+{arti}',x,int(370-t*80),46,renk=YESIL,hiza='orta')
                if o['elendi']:yazi_koy(kare,'ELENDİ',int(np.clip(o['x']*G,80,G-80)),max(self.soru_alt+30,y-80)+28,22,renk=KIRMIZI,hiza='orta')
            self.rozetleri_ciz(kare, renkler, simdi)
            if self.faz == 'puan':
                self.analiz_ciz(kare, renkler)
        if self.kayip_t is not None and simdi-self.kayip_t>=.5:yazi_koy(kare,'Seni göremiyorum; kadraja dön',G//2,470,34,renk=SARI,hiza='orta')
        if self.kalibre:yazi_koy(kare,'S: bitir / oklar: şerit sınırları',G//2,Y-35,26,renk=SARI,hiza='orta')
        if self.durum=='oyun' and self.faz=='carpis' and 0<=simdi-self.soru_t-(2.5+dusun)<.12 and any(o['durum']=='yanlis' for o in self.oyuncular.values()):
            kare[:]=np.roll(kare,int(4*math.sin(simdi*100)),axis=1)
        return kare


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('--onizleme', type=Path)
    args = parser.parse_args()
    if args.onizleme:
        sys.path.insert(0, str(Path(__file__).parent.parent/'tests'))
        from test_cevap_yagmuru import oyun, a
        import p_cevap_yagmuru as onizleme_modulu
        from test_ozel import KARE
        args.onizleme.mkdir(parents=True, exist_ok=True)
        # Önizleme sentetik kişiler ve maske kullanır; kamera doğrulaması değildir.
        _maskeci = type('SentetikMaske', (), {'ver': lambda self,k: np.ones((Y//2,G//2),np.float32)})()
        onizleme_modulu._maskeci = _maskeci
        for ad,t,xs in [('soru',1.,(.2,.8)),('yaklasma',6.,(.2,.8)),('dogru',8.6,(.2,.2)),('yanlis',8.6,(.8,.8)),('podyum',12.,(.2,.8))]:
            p = oyun(*xs)
            if ad=='podyum':
                p.podyum(10.)
            cv2.imwrite(str(args.onizleme/f'{ad}.png'),p.isle(KARE(),a(*xs),t))
