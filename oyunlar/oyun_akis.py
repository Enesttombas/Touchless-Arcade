"""Görünür başlangıç hedefi, geri sayım ve kısa sonuç ekranı."""
import cv2
from cekirdek import G, Y, SARI, BEYAZ, YESIL, panel, halka, px, yazi_koy


class TutHedef:
    def __init__(self):
        self.hedef, self.bas, self.kilit = None, 0., False

    def sec(self, hedef, simdi, sure=1.):
        if hedef != self.hedef:
            self.hedef, self.bas, self.kilit = hedef, simdi, False
        if hedef is not None and not self.kilit and simdi - self.bas >= sure:
            self.kilit = True
            return True
        return False

    def oran(self, simdi, sure=1.):
        return min(1., (simdi - self.bas) / sure) if self.hedef is not None else 0.


class OyunAkisi:
    TUR_SN = 60.

    def __init__(self, ses):
        self.ses = ses
        self.durum, self.durum_t = 'bekle', 0.
        self.onceki_t = None
        self.skor, self.rekorlar, self.sonuc = 0, [], ''
        self.secici = TutHedef()

    def baslat(self, algi, simdi):
        self.durum, self.durum_t, self.skor = 'oyun', simdi, 0

    def bitir(self, simdi, sonuc='Tur bitti'):
        if self.durum == 'oyun':
            self.durum, self.durum_t, self.sonuc = 'sonuc', simdi, sonuc
            self.rekorlar = sorted(self.rekorlar + [self.skor], reverse=True)[:5]
            self.ses.cal('basari', .5)

    def akis(self, kare, algi, simdi):
        dt = .033 if self.onceki_t is None else max(0., min(.1, simdi - self.onceki_t))
        self.onceki_t = simdi
        kare[:] = cv2.convertScaleAbs(kare, alpha=getattr(self,'KAMERA_PARLAKLIK',.85))
        yazi_koy(kare, self.AD, G//2, 18, 48, renk=SARI, hiza='orta')
        if self.durum == 'bekle':
            panel(kare, G//2-160, 260, G//2+160, 410, opak=.8)
            yazi_koy(kare, 'BAŞLA', G//2, 280, 40, renk=YESIL, hiza='orta')
            yazi_koy(kare, self.ACIKLAMA, G//2, 430, 28, renk=BEYAZ, hiza='orta')
            hedef = any(G//2-160 <= px(e, 9)[0] <= G//2+160 and 260 <= px(e, 9)[1] <= 410 for e in algi.eller)
            if self.secici.sec('basla' if hedef else None, simdi):
                self.durum, self.durum_t = 'hazir', simdi
            halka(kare, G//2, 355, self.secici.oran(simdi), r=34, renk=YESIL)
            yazi_koy(kare, 'Elini bu hedefte tut', G//2, 495, 28, hiza='orta')
            if self.rekorlar:
                yazi_koy(kare, 'En iyi: ' + ' / '.join(map(str, self.rekorlar)), G//2, 550, 22, hiza='orta')
        elif self.durum == 'hazir':
            if simdi-self.durum_t >= 3:
                if self.IHTIYAC == {'el'} and not algi.eller:
                    self.durum, self.secici = 'bekle', TutHedef()
                else:
                    self.baslat(algi, simdi)
            else:
                rakam=3-int(simdi-self.durum_t)
                yazi_koy(kare, 'Hazır mısın?', G//2, 210, 32, hiza='orta')
                yazi_koy(kare, str(rakam), G//2, 270, int(100+22*(1-(simdi-self.durum_t)%1)), hiza='orta')
                if getattr(self,'son_sayim',None)!=rakam:
                    self.ses.cal('ding',.35);self.son_sayim=rakam
        elif self.durum == 'sonuc':
            panel(kare,170,220,G-170,440,opak=.8)
            yazi_koy(kare, self.sonuc, G//2, 265, 48, hiza='orta')
            yazi_koy(kare, 'Tekrar: elini kaldır', G//2, 405, 28, hiza='orta')
            for i in range(36):
                x=int((i*173+simdi*20)%G);y=int((i*79+(simdi-self.durum_t)*100)%Y)
                cv2.circle(kare,(x,y),4,(SARI,YESIL,BEYAZ)[i%3],-1)
            yazi_koy(kare, f'Skor: {self.skor}', G//2, 330, 35, hiza='orta')
            if simdi-self.durum_t >= 5:
                self.durum, self.secici = 'bekle', TutHedef()
        elif simdi-self.durum_t >= self.TUR_SN:
            self.bitir(simdi)
        return dt


def sutun_carpisti(x, y, r, sx, genislik, merkez, aralik):
    """Daire ile sütunun iki dikdörtgeninin gerçek kesişimi."""
    dx = x - max(sx, min(x, sx + genislik))
    if abs(dx) >= r:
        return False
    ust, alt = merkez-aralik/2, merkez+aralik/2
    dy = min(y-ust, alt-y) if ust < y < alt else 0
    return dx*dx + dy*dy < r*r
