"""Zaman Yarığı (Time Warp Scan) prototipi.

Kamera karşısında durulduğunda geri sayımla başlayan ve ekran boyunca
ilerleyen neon tarama çizgisiyle dondurulmuş eğlenceli şekiller üretir.
"""
from __future__ import annotations

import math
from typing import Any, Optional

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    PEMBE,
    SARI,
    Y,
    halka,
    panel,
    parilti,
    yazi_koy,
)


class Prototip:
    AD = "Zaman Yarığı"
    ACIKLAMA = "Tarama çizgisi geçerken don ve garip şekiller oluştur!"
    IHTIYAC = {"yuz"}
    SIRA = 2

    def __init__(self, ses: Any):
        self.ses = ses
        self.durum = "bekle"
        self.tur = 1

        self.onceki_simdi: Optional[float] = None
        self.yuz_gorulme_suresi = 0.0
        self.hemen_baslat = False

        self.gs_baslangic = 0.0
        self.son_calinan_sayi = -1

        self.tarama_baslangic = 0.0
        self.tarama_sure = 6.0
        self.son_pos = 0
        self.donmus: Optional[np.ndarray] = None

        self.flas_baslangic = 0.0
        self.sonuc_baslangic = 0.0

        self.katman = np.zeros((Y, G, 3), dtype=np.uint8)

    def tus(self, k: int) -> None:
        if k == 32:  # Boşluk tuşu
            self.hemen_baslat = True

    def isle(self, kare: np.ndarray, algi: Any, simdi: float) -> np.ndarray:
        if self.onceki_simdi is None:
            dt = 0.033
        else:
            dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        yuz_var = bool(algi.yuzler and len(algi.yuzler) > 0)

        # Durum: BEKLE
        if self.durum == "bekle":
            baslat = False
            if self.hemen_baslat:
                self.hemen_baslat = False
                baslat = True
            elif yuz_var:
                self.yuz_gorulme_suresi += dt
                if self.yuz_gorulme_suresi >= 1.0:
                    baslat = True
            else:
                self.yuz_gorulme_suresi = max(0.0, self.yuz_gorulme_suresi - dt * 2.0)

            if baslat:
                self.durum = "geri_sayim"
                self.gs_baslangic = simdi
                self.son_calinan_sayi = -1
                self.yuz_gorulme_suresi = 0.0
            else:
                # Çekim / Bekleme Ekranı
                panel(kare, 0, 0, G, Y, (12, 12, 20), opak=0.45)
                nabiz = 1.0 + 0.04 * math.sin(simdi * 4.0)

                panel(kare, G // 2 - 360, Y // 2 - 130, G // 2 + 360, Y // 2 + 110, (18, 18, 28), opak=0.75, kenar=CAMGOBEGI)
                yazi_koy(kare, "ZAMAN YARIĞI", G // 2, Y // 2 - 105, int(60 * nabiz), CAMGOBEGI, hiza="orta")
                yazi_koy(kare, "Yaklaş, tarama başlasın!", G // 2, Y // 2 - 20, 36, BEYAZ, hiza="orta")

                if yuz_var:
                    oran = min(1.0, self.yuz_gorulme_suresi / 1.0)
                    halka(kare, G // 2, Y // 2 + 50, oran, r=26, renk=SARI, kalinlik=5)
                else:
                    yazi_koy(kare, "Kamera karşısına geç...", G // 2, Y // 2 + 45, 24, SARI, hiza="orta")

                panel(kare, G // 2 - 220, Y - 65, G // 2 + 220, Y - 25, (15, 15, 22), opak=0.6)
                yazi_koy(kare, "[ Boşluk ] ile hemen başlat", G // 2, Y - 56, 22, (200, 200, 210), hiza="orta")

        # Durum: GERİ SAYIM
        elif self.durum == "geri_sayim":
            gecen = simdi - self.gs_baslangic
            adim_sure = 0.7
            adim_idx = int(gecen / adim_sure)

            if adim_idx >= 3:
                # Taramaya geçiş
                self.durum = "tarama"
                self.tarama_baslangic = simdi
                self.donmus = kare.copy()
                self.son_pos = 0
                self.ses.cal("woosh", 0.8)
            else:
                kalan_sayi = 3 - adim_idx
                if self.son_calinan_sayi != kalan_sayi:
                    self.ses.cal("ding", 0.85)
                    self.son_calinan_sayi = kalan_sayi

                adim_t = (gecen - adim_idx * adim_sure) / adim_sure
                # 1.4 -> 1.0 ease-out ölçek
                olcek = 1.0 + 0.4 * (1.0 - math.sin(adim_t * math.pi * 0.5))
                boyut = int(220 * olcek)

                panel(kare, G // 2 - 180, Y // 2 - 160, G // 2 + 180, Y // 2 + 150, (16, 16, 26), opak=0.55, kenar=SARI)
                yazi_koy(kare, str(kalan_sayi), G // 2, Y // 2 - boyut // 2 - 10, boyut, SARI, hiza="orta")
                yazi_koy(kare, "HAZIR OL!", G // 2, Y // 2 + 95, 30, BEYAZ, hiza="orta")

        # Durum: TARAMA
        elif self.durum == "tarama":
            gecen = simdi - self.tarama_baslangic
            oran = min(1.0, gecen / self.tarama_sure)

            dikey_mi = (self.tur % 2 != 0)  # Tek turlar dikey (üstten alta), çift turlar yatay (soldan sağa)
            max_sinir = Y if dikey_mi else G
            yeni_pos = int(oran * max_sinir)
            yeni_pos = max(0, min(max_sinir, yeni_pos))

            if self.donmus is None:
                self.donmus = kare.copy()

            # Yeni geçilen aralığı donmuş tampona mühürle
            if yeni_pos > self.son_pos:
                if dikey_mi:
                    self.donmus[self.son_pos:yeni_pos, :] = kare[self.son_pos:yeni_pos, :]
                else:
                    self.donmus[:, self.son_pos:yeni_pos] = kare[:, self.son_pos:yeni_pos]
                self.son_pos = yeni_pos

            # Geçilmiş bölge donmuş tampondan, geri kalanı canlı kameradan
            if dikey_mi:
                if yeni_pos > 0:
                    kare[:yeni_pos, :] = self.donmus[:yeni_pos, :]
            else:
                if yeni_pos > 0:
                    kare[:, :yeni_pos] = self.donmus[:, :yeni_pos]

            # Neon Çizgi Efekti
            self.katman.fill(0)
            if dikey_mi:
                cy = min(yeni_pos, Y - 1)
                cv2.line(self.katman, (0, cy), (G, cy), CAMGOBEGI, 6, cv2.LINE_AA)
                cv2.line(kare, (0, cy), (G, cy), BEYAZ, 3, cv2.LINE_AA)
            else:
                cx = min(yeni_pos, G - 1)
                cv2.line(self.katman, (cx, 0), (cx, Y), CAMGOBEGI, 6, cv2.LINE_AA)
                cv2.line(kare, (cx, 0), (cx, Y), BEYAZ, 3, cv2.LINE_AA)

            parilti(kare, self.katman, guc=2.2, sigma=4.0)

            # Üst ipucu paneli
            panel(kare, 24, 20, 520, 74, (16, 16, 26), opak=0.7, kenar=CAMGOBEGI)
            yazi_koy(kare, "Hareket et, garip şekiller yap!", 40, 34, 28, SARI)

            # Tarama tamamlandı mı?
            if oran >= 1.0:
                self.durum = "sonuc"
                self.sonuc_baslangic = simdi
                self.flas_baslangic = simdi
                self.ses.cal("basari", 0.9)

        # Durum: SONUÇ
        elif self.durum == "sonuc":
            if self.donmus is not None:
                np.copyto(kare, self.donmus)

            gecen = simdi - self.sonuc_baslangic
            kalan = max(0.0, 5.0 - gecen)

            # Başlangıç beyaz flaşı (0.25 sn sönen)
            flas_gecen = simdi - self.flas_baslangic
            if flas_gecen < 0.25:
                flas_opak = (1.0 - flas_gecen / 0.25) * 0.85
                beyaz_katman = np.full_like(kare, 255)
                cv2.addWeighted(kare, 1.0 - flas_opak, beyaz_katman, flas_opak, 0, dst=kare)

            # Üst küçük başlık
            panel(kare, G // 2 - 160, 16, G // 2 + 160, 68, (18, 18, 28), opak=0.8, kenar=SARI)
            yazi_koy(kare, "ZAMAN YARIĞI", G // 2, 26, 32, SARI, hiza="orta")

            # Sağ altta filigran paneli
            panel(kare, G - 270, Y - 78, G - 24, Y - 24, (18, 18, 28), opak=0.8, kenar=CAMGOBEGI)
            yazi_koy(kare, "Kulüp Standı", G - 147, Y - 66, 28, BEYAZ, hiza="orta")

            # Altta geri sayım süresi çubuğu
            cubuk_tam_gen = G - 80
            cubuk_gen = int((kalan / 5.0) * cubuk_tam_gen)
            panel(kare, 40, Y - 16, 40 + cubuk_tam_gen, Y - 8, (30, 30, 40), opak=0.6)
            if cubuk_gen > 0:
                panel(kare, 40, Y - 16, 40 + cubuk_gen, Y - 8, CAMGOBEGI, opak=0.95)

            if gecen >= 5.0:
                self.durum = "bekle"
                self.tur += 1
                self.yuz_gorulme_suresi = 0.0

        return kare
