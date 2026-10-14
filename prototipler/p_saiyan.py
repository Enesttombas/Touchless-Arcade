"""Süper Saiyan Aurası prototipi: Poz takibi ile güç toplama, aura, şimşek ve ışın."""
from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    PEMBE,
    SARI,
    G,
    Y,
    Algi,
    Maskeci,
    Parcaciklar,
    bulanik_karanlik,
    halka,
    on_plan,
    parilti,
    px,
    yazi_koy,
)


class Prototip:
    AD = "Süper Saiyan"
    ACIKLAMA = "Yumruklarını sıkıp güç topla, ellerini birleştirip ışın fırlat"
    IHTIYAC = {"poz"}
    SIRA = 3

    # Renk paletleri (Seviye 0: Sarı/Altın, Seviye 1: Mavi/Camgöbeği, Seviye 2: Mor/Pembe)
    SEVIYE_RENKLER = [
        {"ana": (20, 210, 255), "ikincil": (50, 255, 255), "ic": (200, 245, 255)},
        {"ana": (255, 180, 20), "ikincil": (255, 240, 60), "ic": (255, 255, 200)},
        {"ana": (230, 60, 210), "ikincil": (255, 120, 240), "ic": (255, 220, 255)},
    ]

    def __init__(self, ses):
        self.ses = ses
        self.maskeci = Maskeci()
        self.parcaciklar = Parcaciklar(400)
        self.onceki_zaman = 0.0

        # Güç ve seviye durumu
        self.seviye = 0
        self.guc = 0.0  # 0.0 - 1.0
        self.guc_hedef = 0.0

        # Titreme ve patlama efektleri
        self.sarsinti_kalan = 0.0
        self.son_nota_zamani = 0.0

        # Işın (Kamehameha)
        self.isin_kalan = 0.0
        self.isin_kaynak = (G // 2, Y // 2)
        self.isin_hedef = (G, Y // 2)
        self.isin_seviye = 0

        # Yumuşatılmış oyuncu noktaları
        self.son_burun = None
        self.son_omuz = None
        self.son_boyut = 0.0

    def _ana_poz_sec(self, pozlar) -> Optional[List]:
        """Kalabalıktan en öndeki / en büyük gövdeye sahip kişiyi seçer."""
        if not pozlar:
            return None
        en_iyi = None
        en_buyuk_mesafe = -1.0
        for p in pozlar:
            try:
                # Omuzlar (11, 12) ve kalçalar (23, 24)
                if p[11].visibility < 0.3 or p[12].visibility < 0.3:
                    continue
                o1 = (p[11].x * G, p[11].y * Y)
                o2 = (p[12].x * G, p[12].y * Y)
                genislik = math.hypot(o1[0] - o2[0], o1[1] - o2[1])
                if genislik > en_buyuk_mesafe and genislik > 55:
                    en_buyuk_mesafe = genislik
                    en_iyi = p
            except Exception:
                continue
        return en_iyi

    def _simsek_uret(self, p1: Tuple[int, int], p2: Tuple[int, int], kiriklik: int = 4) -> List[Tuple[int, int]]:
        pts = [p1]
        x1, y1 = p1
        x2, y2 = p2
        dx = (x2 - x1) / (kiriklik + 1)
        dy = (y2 - y1) / (kiriklik + 1)
        for i in range(1, kiriklik + 1):
            mx = x1 + dx * i + random.uniform(-25, 25)
            my = y1 + dy * i + random.uniform(-25, 25)
            pts.append((int(mx), int(my)))
        pts.append(p2)
        return pts

    def _sac_pariltisi_ciz(self, katman: np.ndarray, burun_pt: Tuple[int, int], boyut: float, renkler: dict):
        """Kafanın üzerine sivri Süper Saiyan saç alevleri çizer."""
        bx, by = burun_pt
        kafa_ust = by - int(boyut * 0.9)
        sac_renk = renkler["ikincil"]
        ic_renk = renkler["ic"]

        dikmeler = [
            (-boyut * 0.45, -boyut * 0.3, -boyut * 0.8),
            (-boyut * 0.25, -boyut * 0.6, -boyut * 1.15),
            (0.0, -boyut * 0.85, -boyut * 1.4),
            (boyut * 0.25, -boyut * 0.6, -boyut * 1.15),
            (boyut * 0.45, -boyut * 0.3, -boyut * 0.8),
        ]

        for dx_taban, dy_taban, dy_tepe in dikmeler:
            dalga = math.sin(by * 0.05 + dx_taban) * 8
            tepe_x = int(bx + dx_taban * 1.3 + dalga)
            tepe_y = int(kafa_ust + dy_tepe)
            taban_sol = (int(bx + dx_taban - 14), int(kafa_ust + dy_taban))
            taban_sag = (int(bx + dx_taban + 14), int(kafa_ust + dy_taban))

            ucgen = np.array([[taban_sol[0], taban_sol[1]], [taban_sag[0], taban_sag[1]], [tepe_x, tepe_y]], np.int32)
            cv2.fillConvexPoly(katman, ucgen, sac_renk, cv2.LINE_AA)
            cv2.line(katman, (int(bx + dx_taban), int(kafa_ust + dy_taban)), (tepe_x, tepe_y), ic_renk, 2, cv2.LINE_AA)

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.onceki_zaman <= 0.0:
            dt = 0.033
        else:
            dt = min(max(simdi - self.onceki_zaman, 0.001), 0.1)
        self.onceki_zaman = simdi

        ana_poz = self._ana_poz_sec(algi.pozlar)
        maske_raw = self.maskeci.ver(kare)

        # ----------------- KİMSE YOKKEN ÇEKİM EKRANI -----------------
        if ana_poz is None:
            self.guc = max(0.0, self.guc - dt * 2.0)
            self.isin_kalan = 0.0
            bulanik = bulanik_karanlik(kare, 0.45)
            nabiz = 1.0 + 0.08 * math.sin(simdi * 4.0)
            yazi_koy(bulanik, "GÜCÜNÜ UYANDIR", G // 2, Y // 2 - 40, int(58 * nabiz), SARI, hiza="orta")
            yazi_koy(bulanik, "Kameranın karşısına geç ve yumruklarını sık!", G // 2, Y // 2 + 35, 26, BEYAZ, hiza="orta")
            return bulanik

        # ----------------- POZ VE GEOMETRİ ANALİZİ -----------------
        b_raw = px(ana_poz, 0)
        sol_omuz = px(ana_poz, 11)
        sag_omuz = px(ana_poz, 12)
        sol_bilek = px(ana_poz, 15)
        sag_bilek = px(ana_poz, 16)
        sol_kalca = px(ana_poz, 23)
        sag_kalca = px(ana_poz, 24)

        omuz_ort_x = (sol_omuz[0] + sag_omuz[0]) * 0.5
        omuz_ort_y = (sol_omuz[1] + sag_omuz[1]) * 0.5
        omuz_gen = math.hypot(sol_omuz[0] - sag_omuz[0], sol_omuz[1] - sag_omuz[1])

        # Yumuşatma
        if self.son_burun is None:
            self.son_burun = b_raw
            self.son_omuz = (omuz_ort_x, omuz_ort_y)
            self.son_boyut = omuz_gen
        else:
            self.son_burun = (self.son_burun[0] * 0.7 + b_raw[0] * 0.3, self.son_burun[1] * 0.7 + b_raw[1] * 0.3)
            self.son_omuz = (self.son_omuz[0] * 0.7 + omuz_ort_x * 0.3, self.son_omuz[1] * 0.7 + omuz_ort_y * 0.3)
            self.son_boyut = self.son_boyut * 0.8 + omuz_gen * 0.2

        boyut = max(40.0, self.son_boyut)

        # Jest Tespiti:
        # 1) Güç Toplama Duruşu: Bilekler omuzların altında, gövdeye yakın (omuz genişliğinden çok uzak değil)
        bilekler_mesafe = math.hypot(sol_bilek[0] - sag_bilek[0], sol_bilek[1] - sag_bilek[1])
        bilekler_altta = sol_bilek[1] > sol_omuz[1] + 15 and sag_bilek[1] > sag_omuz[1] + 15
        bilek_govde_sol = abs(sol_bilek[0] - sol_omuz[0]) < boyut * 0.95
        bilek_govde_sag = abs(sag_bilek[0] - sag_omuz[0]) < boyut * 0.95
        guc_topluyor = bilekler_altta and bilek_govde_sol and bilek_govde_sag

        # 2) Kamehameha Duruşu: İki bilek birbirine çok yakın (< boyut * 0.45) ve kollar önde/uzakta
        eller_bitisik = bilekler_mesafe < boyut * 0.55
        eller_ort_x = (sol_bilek[0] + sag_bilek[0]) * 0.5
        eller_ort_y = (sol_bilek[1] + sag_bilek[1]) * 0.5
        govde_mesafe = math.hypot(eller_ort_x - omuz_ort_x, eller_ort_y - omuz_ort_y)
        kamehameha_hazir = eller_bitisik and govde_mesafe > boyut * 0.45 and (self.guc > 0.4 or self.seviye > 0)

        # ----------------- DURUM GÜNCELLEME -----------------
        if kamehameha_hazir and self.isin_kalan <= 0.05:
            # Işın ateşle!
            self.isin_kalan = 1.5
            self.isin_seviye = self.seviye
            self.ses.cal("zap", ses=0.9)
            self.ses.cal("woosh", ses=0.8)
            self.sarsinti_kalan = 0.3
            self.guc = 0.15

        if self.isin_kalan > 0.0:
            self.isin_kalan = max(0.0, self.isin_kalan - dt)
            guc_topluyor = False

        if guc_topluyor:
            self.guc = min(1.0, self.guc + dt * 0.65)
            # Ses geribildirimi (yükselen frekanslar)
            if simdi - self.son_nota_zamani > 0.12:
                nota_idx = 48 + int(self.guc * 24) + self.seviye * 5
                self.ses.cal(f"nota{nota_idx}", ses=0.45 + self.guc * 0.3)
                self.son_nota_zamani = simdi

            if self.guc >= 1.0:
                # Seviye atla
                self.ses.cal("basari", ses=0.8)
                self.ses.cal("kick", ses=0.7)
                self.sarsinti_kalan = 0.3
                self.seviye = (self.seviye + 1) % 3
                self.guc = 0.25
        else:
            # Bırakılınca yavaş söner
            self.guc = max(0.0, self.guc - dt * 0.35)

        renkler = self.SEVIYE_RENKLER[self.seviye]

        # ----------------- PARÇACIK VE GÖRSEL KATMANLAR -----------------
        katman = np.zeros_like(kare)

        # Gövde çevresinden yukarı fışkıran alev parçacıkları
        aura_oran = max(self.guc, 0.2 if self.seviye > 0 else 0.0)
        if aura_oran > 0.05:
            parcacik_adet = int(aura_oran * 8) + (self.seviye * 2)
            for _ in range(parcacik_adet):
                rx = random.uniform(omuz_ort_x - boyut * 0.7, omuz_ort_x + boyut * 0.7)
                ry = random.uniform(omuz_ort_y - boyut * 0.2, (sol_kalca[1] + sag_kalca[1]) * 0.5 + 20)
                p_renk = renkler["ana"] if random.random() < 0.65 else renkler["ikincil"]
                self.parcaciklar.yay(rx, ry, 1, renk=p_renk, hiz=random.uniform(4.0, 9.0))

            # Parçacıkları yukarı çekmek için negatif yerçekimi etkisi
            if len(self.parcaciklar.v):  # yerçekimini (9) yenip yukarı akış
                self.parcaciklar.v[:, 1] -= dt * 20.0

        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(katman)

        # Maske tabanlı alev aurası
        if maske_raw is not None and aura_oran > 0.1:
            try:
                m_filtre = on_plan(maske_raw, oran=0.3)
                m_kucuk = cv2.resize(m_filtre, (G // 4, Y // 4), interpolation=cv2.INTER_AREA)
                # Genişletip alev sınırını oluştur
                genisleme = int(3 + aura_oran * 12 + self.seviye * 3)
                cekirdek = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (genisleme, genisleme))
                genis = cv2.dilate(m_kucuk, cekirdek)
                hale_kenar = np.clip((genis - m_kucuk * 0.9) * 255.0 * (0.6 + aura_oran * 0.5), 0, 255).astype(np.uint8)

                aura_bgr = np.zeros((Y // 4, G // 4, 3), dtype=np.uint8)
                aura_bgr[:, :] = renkler["ana"]
                aura_katman_kucuk = cv2.bitwise_and(aura_bgr, aura_bgr, mask=hale_kenar)
                aura_tam = cv2.resize(aura_katman_kucuk, (G, Y), interpolation=cv2.INTER_LINEAR)
                cv2.add(katman, aura_tam, dst=katman)
            except Exception:
                pass

        # Saçın üstüne sivri Süper Saiyan alevi
        if aura_oran > 0.2:
            self._sac_pariltisi_ciz(katman, (int(self.son_burun[0]), int(self.son_burun[1])), boyut, renkler)

        # Şimşek çakmaları (%70 güç üstünde veya Seviye 1/2'de)
        if (self.guc > 0.7 or self.seviye > 0) and random.random() < (0.35 + self.guc * 0.4):
            govde_merkez = (int(omuz_ort_x), int(omuz_ort_y + boyut * 0.5))
            for _ in range(random.randint(1, 3)):
                aci = random.uniform(0, math.pi * 2)
                r_mes = random.uniform(boyut * 0.9, boyut * 1.8)
                hedef_pt = (int(govde_merkez[0] + math.cos(aci) * r_mes), int(govde_merkez[1] + math.sin(aci) * r_mes))
                simsek_pts = self._simsek_uret(govde_merkez, hedef_pt, kiriklik=random.randint(3, 5))
                for i in range(len(simsek_pts) - 1):
                    cv2.line(katman, simsek_pts[i], simsek_pts[i + 1], renkler["ic"], 3, cv2.LINE_AA)
                    cv2.line(katman, simsek_pts[i], simsek_pts[i + 1], BEYAZ, 1, cv2.LINE_AA)

        # ----------------- KAMEHAMEHA IŞINI -----------------
        if self.isin_kalan > 0.0:
            oran = self.isin_kalan / 1.5
            isin_genislik = int((35 + math.sin(simdi * 25.0) * 8 + 30 * oran) * (1.0 + self.isin_seviye * 0.3))

            kx, ky = int(eller_ort_x), int(eller_ort_y)
            # İleri yön (gövdeden ellere doğru yön vektörü)
            yon_dx = eller_ort_x - omuz_ort_x
            yon_dy = eller_ort_y - omuz_ort_y
            hipot = math.hypot(yon_dx, yon_dy)
            if hipot > 5:
                yon_dx /= hipot
                yon_dy /= hipot
            else:
                yon_dx, yon_dy = 1.0, 0.0

            hx = int(kx + yon_dx * 1500)
            hy = int(ky + yon_dy * 1500)

            isin_renk = CAMGOBEGI if self.isin_seviye != 2 else PEMBE

            # Dış huzme ve iç parlama
            cv2.line(katman, (kx, ky), (hx, hy), isin_renk, isin_genislik * 2, cv2.LINE_AA)
            cv2.line(katman, (kx, ky), (hx, hy), BEYAZ, max(4, isin_genislik // 2), cv2.LINE_AA)
            cv2.circle(katman, (kx, ky), int(isin_genislik * 1.6), isin_renk, -1, cv2.LINE_AA)
            cv2.circle(katman, (kx, ky), int(isin_genislik * 0.9), BEYAZ, -1, cv2.LINE_AA)

            # Işın etrafında helezonik şimşekler
            for _ in range(4):
                fx = random.randint(0, G)
                fy = int(ky + yon_dy * (fx - kx) + random.uniform(-isin_genislik, isin_genislik))
                cv2.circle(katman, (fx, fy), random.randint(2, 6), BEYAZ, -1)

        # Parlama efekti uygulama
        parilti(kare, katman, guc=1.7, sigma=2.8)

        # ----------------- DOLUM HALKASI VE SEVİYE GÖSTERGESİ -----------------
        if self.guc > 0.05 and self.isin_kalan <= 0.0:
            halka_x = int(omuz_ort_x)
            halka_y = int(omuz_ort_y - boyut * 0.4)
            halka(kare, halka_x, halka_y, self.guc, r=int(boyut * 0.38), renk=renkler["ana"], kalinlik=7)
            halka(kare, halka_x, halka_y, self.guc, r=int(boyut * 0.38), renk=BEYAZ, kalinlik=2)

        # ----------------- EKRAN SARSINTISI -----------------
        if self.sarsinti_kalan > 0.0:
            self.sarsinti_kalan = max(0.0, self.sarsinti_kalan - dt)
            ofset_x = random.randint(-9, 9)
            ofset_y = random.randint(-9, 9)
            M = np.float32([[1, 0, ofset_x], [0, 1, ofset_y]])
            kare = cv2.warpAffine(kare, M, (G, Y), borderMode=cv2.BORDER_REFLECT)

        # Sadece oyun durumu için küçük temiz seviye rozeti (alt ortada sade)
        seviye_adlari = ["SSJ 1", "SSJ 2 (BLUE)", "SSJ 3 (ULTRA)"]
        yazi_koy(kare, seviye_adlari[self.seviye], G // 2, Y - 48, 28, renkler["ikincil"], hiza="orta")

        return kare
