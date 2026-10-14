"""Işık Tozu prototipi: Hareket tabanlı partikül ve ışık etkileşimi simülasyonu."""
from __future__ import annotations

import math
from typing import Optional, Set

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    PEMBE,
    SARI,
    Y,
    Algi,
    panel,
    yazi_koy,
)


class Prototip:
    AD = "Işık Tozu"
    ACIKLAMA = "Hareket et, bedenini ışık tozuna ve büyüye dönüştür!"
    IHTIYAC: Set[str] = set()
    SIRA = 10

    TEMALAR = ("Ateş", "Galaksi", "Kar")
    TAVAN = 5000

    def __init__(self, ses):
        self.ses = ses
        self.tema_idx = 0
        self.tema = self.TEMALAR[self.tema_idx]
        self.tema_degisim_zamani = 0.0

        # Zaman ve hareket takipçileri
        self.onceki_simdi = 0.0
        self.onceki_kucuk: Optional[np.ndarray] = None
        self.son_hareket_zamani = 0.0
        self.hareket_skor = 0.0

        # Morfolojik çekirdek
        self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

        # Parçacık veri havuzu (Vektörel NumPy)
        self.kapasite = self.TAVAN
        self.pos = np.zeros((self.kapasite, 2), dtype=np.float32)
        self.vel = np.zeros((self.kapasite, 2), dtype=np.float32)
        self.renk = np.zeros((self.kapasite, 3), dtype=np.float32)
        self.omur = np.zeros(self.kapasite, dtype=np.float32)
        self.toplam_omur = np.ones(self.kapasite, dtype=np.float32)
        self.aktif_sayisi = 0

        # Ekran merkezi
        self.cx = G * 0.5
        self.cy = Y * 0.5

    def tus(self, k: int) -> None:
        if k == 32:  # Boşluk tuşu ile temayı döngüsel değiştir
            self._sonraki_tema()

    def _sonraki_tema(self) -> None:
        self.tema_idx = (self.tema_idx + 1) % len(self.TEMALAR)
        self.tema = self.TEMALAR[self.tema_idx]
        self.ses.cal("woosh", 0.6)

    def _parcacik_dogur(self, pts_xy: np.ndarray, tema: str) -> None:
        m = len(pts_xy)
        if m == 0 or self.aktif_sayisi >= self.kapasite:
            return

        bos_yer = self.kapasite - self.aktif_sayisi
        eklenecek = min(m, bos_yer)
        if eklenecek <= 0:
            return

        secilen = pts_xy[:eklenecek]
        idx_bas = self.aktif_sayisi
        idx_son = idx_bas + eklenecek

        # ±4 piksel dağılım
        sapma = (np.random.rand(eklenecek, 2).astype(np.float32) - 0.5) * 8.0
        self.pos[idx_bas:idx_son] = secilen + sapma

        omurler = np.random.uniform(1.2, 2.5, size=eklenecek).astype(np.float32)
        self.omur[idx_bas:idx_son] = omurler
        self.toplam_omur[idx_bas:idx_son] = omurler

        if tema == "Ateş":
            # Ateş: Düşük Mavi, orta Yeşil, yüksek Kırmızı. Yukarı yükselir, hafif titrer
            b = np.random.uniform(15.0, 45.0, size=eklenecek).astype(np.float32)
            g = np.random.uniform(70.0, 180.0, size=eklenecek).astype(np.float32)
            r = np.random.uniform(230.0, 255.0, size=eklenecek).astype(np.float32)
            self.renk[idx_bas:idx_son] = np.column_stack([b, g, r])

            vx = np.random.uniform(-30.0, 30.0, size=eklenecek).astype(np.float32)
            vy = np.random.uniform(-180.0, -90.0, size=eklenecek).astype(np.float32)
            self.vel[idx_bas:idx_son] = np.column_stack([vx, vy])

        elif tema == "Galaksi":
            # Galaksi: Mor, pembe, elektrik mavisi.
            b = np.random.uniform(200.0, 255.0, size=eklenecek).astype(np.float32)
            g = np.random.uniform(50.0, 140.0, size=eklenecek).astype(np.float32)
            r = np.random.uniform(170.0, 255.0, size=eklenecek).astype(np.float32)
            self.renk[idx_bas:idx_son] = np.column_stack([b, g, r])

            # Merkeze göre teğetsel girdap hızı
            fark = self.pos[idx_bas:idx_son] - np.array([self.cx, self.cy], dtype=np.float32)
            dist = np.hypot(fark[:, 0], fark[:, 1]) + 1e-4
            teget_x = -fark[:, 1] / dist
            teget_y = fark[:, 0] / dist
            hiz = np.random.uniform(80.0, 180.0, size=eklenecek).astype(np.float32)
            self.vel[idx_bas:idx_son] = np.column_stack([teget_x * hiz, teget_y * hiz])

        else:  # "Kar"
            # Kar: Parlak beyaz-camgöbeği. Yavaş düşer, yatay sallanır
            b = np.random.uniform(220.0, 255.0, size=eklenecek).astype(np.float32)
            g = np.random.uniform(210.0, 255.0, size=eklenecek).astype(np.float32)
            r = np.random.uniform(180.0, 230.0, size=eklenecek).astype(np.float32)
            self.renk[idx_bas:idx_son] = np.column_stack([b, g, r])

            vx = np.random.uniform(-25.0, 25.0, size=eklenecek).astype(np.float32)
            vy = np.random.uniform(40.0, 110.0, size=eklenecek).astype(np.float32)
            self.vel[idx_bas:idx_son] = np.column_stack([vx, vy])

        self.aktif_sayisi += eklenecek

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.onceki_simdi == 0.0:
            self.onceki_simdi = simdi
            self.tema_degisim_zamani = simdi
            self.son_hareket_zamani = simdi

        dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        # 20 saniyede bir otomatik tema değişimi
        if simdi - self.tema_degisim_zamani >= 20.0:
            self.tema_degisim_zamani = simdi
            self._sonraki_tema()

        # 1. HAREKET TESPİTİ (160x90 gri)
        kucuk_gri = cv2.cvtColor(
            cv2.resize(kare, (160, 90), interpolation=cv2.INTER_AREA),
            cv2.COLOR_BGR2GRAY,
        )

        yeni_noktalar = []
        if self.onceki_kucuk is not None:
            fark = cv2.absdiff(kucuk_gri, self.onceki_kucuk)
            _, esik = cv2.threshold(fark, 18, 255, cv2.THRESH_BINARY)
            esik = cv2.morphologyEx(esik, cv2.MORPH_OPEN, self.kernel)

            ys, xs = np.nonzero(esik)
            adet = len(xs)
            self.hareket_skor = self.hareket_skor * 0.85 + adet * 0.15

            if adet > 35:
                self.son_hareket_zamani = simdi
                ornek_sayisi = min(adet, 150)
                secim = np.random.choice(adet, size=ornek_sayisi, replace=False)
                sx = xs[secim].astype(np.float32) * (G / 160.0)
                sy = ys[secim].astype(np.float32) * (Y / 90.0)
                pts = np.column_stack([sx, sy])

                # Her örnekten 1-2 parçacık doğur
                yeni_noktalar.append(pts)
                if ornek_sayisi < 100:
                    yeni_noktalar.append(pts)

        self.onceki_kucuk = kucuk_gri

        if yeni_noktalar:
            tum_yeni = np.vstack(yeni_noktalar)
            self._parcacik_dogur(tum_yeni, self.tema)

        # 2. VEKTÖREL FİZİK GÜNCELLEMESİ
        N = self.aktif_sayisi
        if N > 0:
            self.omur[:N] -= dt
            canli_mask = self.omur[:N] > 0.0

            if not np.all(canli_mask):
                kalan_sayi = int(np.sum(canli_mask))
                if kalan_sayi > 0:
                    self.pos[:kalan_sayi] = self.pos[:N][canli_mask]
                    self.vel[:kalan_sayi] = self.vel[:N][canli_mask]
                    self.renk[:kalan_sayi] = self.renk[:N][canli_mask]
                    self.omur[:kalan_sayi] = self.omur[:N][canli_mask]
                    self.toplam_omur[:kalan_sayi] = self.toplam_omur[:N][canli_mask]
                self.aktif_sayisi = kalan_sayi
                N = kalan_sayi

        if N > 0:
            # Temaya özel kuvvetler
            if self.tema == "Ateş":
                # Ateş hafif yatay dalgalanır ve hızla yukarı ivmelenir
                titreme = (np.random.rand(N, 2).astype(np.float32) - 0.5) * 50.0
                self.vel[:N, 0] += titreme[:, 0] * dt
                self.vel[:N, 1] -= 40.0 * dt
            elif self.tema == "Galaksi":
                # Merkeze doğru hafif çekim + girdap koruma
                fark = self.pos[:N] - np.array([self.cx, self.cy], dtype=np.float32)
                dist = np.hypot(fark[:, 0], fark[:, 1]) + 1e-4
                cekme = (fark / dist[:, None]) * (-35.0 * dt)
                self.vel[:N] += cekme
            else:  # Kar
                # Yatay salınım
                dalga = np.sin(simdi * 3.0 + self.pos[:N, 1] * 0.03).astype(np.float32)
                self.vel[:N, 0] += dalga * 15.0 * dt

            self.pos[:N] += self.vel[:N] * dt

        # 3. ÇİZİM VE IŞIMA (BUFFER ACCUMULATION)
        # Kamera görüntüsünü %25 parlaklığa çek
        cikis = cv2.convertScaleAbs(kare, alpha=0.25)

        if N > 0:
            oranlar = np.clip(self.omur[:N] / self.toplam_omur[:N], 0.0, 1.0)
            isik = (oranlar * 0.75)[:, None]
            etkin_renk = (self.renk[:N] * isik).astype(np.float32)

            # Çeyrek çözünürlük tampon (320x180) - Parıltı katmanı
            q_w, q_h = 320, 180
            qx = (self.pos[:N, 0] * (q_w / G)).astype(np.int32)
            qy = (self.pos[:N, 1] * (q_h / Y)).astype(np.int32)

            q_mask = (qx >= 0) & (qx < q_w) & (qy >= 0) & (qy < q_h)
            if np.any(q_mask):
                qx_c = qx[q_mask]
                qy_c = qy[q_mask]
                renk_c = etkin_renk[q_mask]

                tampon_q = np.zeros((q_h, q_w, 3), dtype=np.float32)
                np.add.at(tampon_q, (qy_c, qx_c), renk_c)

                # Gauss bulanıklık ile neon halesi
                tampon_q = np.clip(tampon_q, 0.0, 255.0).astype(np.uint8)
                hale_q = cv2.GaussianBlur(tampon_q, (0, 0), sigmaX=3.2, sigmaY=3.2)
                hale_tam = cv2.resize(hale_q, (G, Y), interpolation=cv2.INTER_LINEAR)
                hale_tam = cv2.convertScaleAbs(hale_tam, alpha=1.7)
                cv2.add(cikis, hale_tam, dst=cikis)

            # Yarım çözünürlük tampon (640x360) - Keskin çekirdek noktaları
            h_w, h_h = 640, 360
            hx = (self.pos[:N, 0] * (h_w / G)).astype(np.int32)
            hy = (self.pos[:N, 1] * (h_h / Y)).astype(np.int32)

            h_mask = (hx >= 0) & (hx < h_w) & (hy >= 0) & (hy < h_h)
            if np.any(h_mask):
                hx_c = hx[h_mask]
                hy_c = hy[h_mask]
                renk_h = etkin_renk[h_mask] * 1.3

                tampon_h = np.zeros((h_h, h_w, 3), dtype=np.float32)
                np.add.at(tampon_h, (hy_c, hx_c), renk_h)
                tampon_h = np.clip(tampon_h, 0.0, 255.0).astype(np.uint8)
                cekirdek_tam = cv2.resize(tampon_h, (G, Y), interpolation=cv2.INTER_LINEAR)
                cv2.add(cikis, cekirdek_tam, dst=cikis)

        # 4. ARAYÜZ VE TEMA BİLGİSİ
        # Sol altta tema etiketi
        panel(cikis, 30, Y - 75, 230, Y - 25, renk=(15, 15, 24), opak=0.65, kenar=(60, 60, 90))
        tema_renk = SARI if self.tema == "Ateş" else (PEMBE if self.tema == "Galaksi" else CAMGOBEGI)
        yazi_koy(cikis, f"TEMA: {self.tema.upper()}", 45, Y - 65, 24, renk=tema_renk, hiza="sol")

        # 3 saniyeden uzun süre az hareket varsa ortada nabız yazısı
        hareketsiz_sure = simdi - self.son_hareket_zamani
        if hareketsiz_sure > 3.0:
            nabiz = (math.sin(simdi * 4.0) + 1.0) * 0.5  # 0..1 dalga
            alfa_yazi = 0.55 + 0.45 * nabiz
            olcek = 1.0 + 0.04 * nabiz

            # Arka plan yumuşak odak paneli
            panel(cikis, G // 2 - 360, Y // 2 - 60, G // 2 + 360, Y // 2 + 50, renk=(10, 10, 18), opak=0.55 * alfa_yazi)
            yazi_koy(
                cikis,
                "Hareket et, ışığa dönüş!",
                G // 2,
                Y // 2 - 40,
                46,
                renk=BEYAZ,
                hiza="orta",
                olcek=olcek,
                opak=alfa_yazi,
            )
            yazi_koy(
                cikis,
                "Bedenini ve ellerini salla",
                G // 2,
                Y // 2 + 15,
                24,
                renk=CAMGOBEGI,
                hiza="orta",
                opak=alfa_yazi,
            )

        return cikis
