"""Hayalet Klonlar: eski iki ayna deneyimi tek kartta (Enes 2026-10-13, Taş Kağıt Makas'ın yerine).

Zaman Klonları (Loop/Neon/Klon/Gökkuşağı) ile Görünmezlik Pelerini (Pelerin/Hayalet/Uçan Kafa) sırayla gelir;
her biri kendi içinde modlarını zaten kendisi döndürür. V tuşu deneyimi elle değiştirir, diğer tuşlar etkin
deneyime gider. İkinci deneyim ilk geçişte kurulur (açılışta iki segmentasyon modeli yüklenmesin).
"""
import p_gorunmez
import p_zaman_klonu


class Prototip:
    AD = 'Hayalet Klonlar'
    ACIKLAMA = 'Kendi klonlarını yarat, sonra görünmez ol!'
    IHTIYAC = set(p_zaman_klonu.Prototip.IHTIYAC) | set(p_gorunmez.Prototip.IHTIYAC)
    KENDI_IMLECI = True  # parmak noktası pelerinin altından görünüp efekti bozmasın
    PARCA_SN = 45.0
    SINIFLAR = (p_zaman_klonu.Prototip, p_gorunmez.Prototip)

    def __init__(self, ses):
        self.ses = ses
        self.parcalar = [self.SINIFLAR[0](ses), None]
        self.i, self.bas = 0, None

    @property
    def etkin(self):
        if self.parcalar[self.i] is None:
            self.parcalar[self.i] = self.SINIFLAR[self.i](self.ses)
        return self.parcalar[self.i]

    @property
    def durum(self):
        return getattr(self.etkin, 'durum', '')

    def degistir(self, simdi=None):
        self.i, self.bas = 1 - self.i, simdi

    def tus(self, k):
        if k in (ord('v'), ord('V')):
            self.degistir()
        else:
            self.etkin.tus(k)

    def isle(self, kare, algi, simdi):
        if self.bas is None:
            self.bas = simdi
        elif simdi - self.bas >= self.PARCA_SN:
            self.degistir(simdi)
        return self.etkin.isle(kare, algi, simdi)
