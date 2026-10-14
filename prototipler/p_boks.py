"""Refleks Boksu: Hızlı yumruklarla neon hedefleri patlatma prototipi."""
from __future__ import annotations

import math
import random
from typing import Any, List, Optional, Tuple

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    KIRMIZI,
    PEMBE,
    SARI,
    YESIL,
    Y,
    Algi,
    Parcaciklar,
    bulanik_karanlik,
    halka,
    panel,
    parilti,
    px,
    yazi_koy,
)


class Hedef:
    """Neon hedef diski ve dalgası."""

    def __init__(self, x: float, y: float, omur: float, bomba: bool = False):
        self.x = float(x)
        self.y = float(y)
        self.max_omur = omur
        self.kalan_omur = omur
        self.yaricap = 52.0
        self.bomba = bomba
        self.renk = KIRMIZI if bomba else random.choice([CAMGOBEGI, PEMBE, SARI])
        self.oluk = False
        self.olme_ani = False


class HalkaDalgasi:
    """Vurulan hedeften yayılan şok dalgası halkası."""

    def __init__(self, x: float, y: float, renk: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.r = 30.0
        self.max_r = 140.0
        self.renk = renk
        self.omur = 0.35
        self.kalan = 0.35


class Prototip:
    AD = "Refleks Boksu"
    ACIKLAMA = "Neon hedeflere hızlı yumruk at, kırmızı bombalardan kaç!"
    IHTIYAC = {"el"}
    SIRA = 7

    def __init__(self, ses: Any):
        self.ses = ses
        self.durum = "bekle"  # "bekle", "oyun", "sonuc"
        self.tur_suresi = 30.0
        self.kalan_sure = self.tur_suresi
        self.skor = 0
        self.rekor = 0

        # Zaman & yumuşatma
        self.son_simdi = 0.0
        self.sonuc_zamani = 0.0

        # Başlatma halkası
        self.basla_tutma = 0.0
        self.basla_pos = (G // 2, Y // 2)
        self.basla_r = 85

        # Hedefler & efektler
        self.hedefler: List[Hedef] = []
        self.dalgalar: List[HalkaDalgasi] = []
        self.parcaciklar = Parcaciklar(350)
        self.sarsinti = 0.0
        self.skor_pop = 1.0

        # El takibi ve hız hesabı
        self.onceki_eller: List[Tuple[float, float, float]] = []  # (x, y, t)

    def _sec_ana_eller(self, eller: List[Any]) -> List[Any]:
        """Kalabalık filtresi: En büyük (kameraya en yakın) 1 veya 2 eli seç."""
        if not eller:
            return []
        if len(eller) <= 2:
            return eller

        skorlu = []
        for el in eller:
            xs = [pt.x for pt in el]
            ys = [pt.y for pt in el]
            alan = (max(xs) - min(xs)) * (max(ys) - min(ys))
            skorlu.append((alan, el))
        skorlu.sort(key=lambda item: item[0], reverse=True)
        return [skorlu[0][1], skorlu[1][1]]

    def _yeni_hedef_uret(self):
        """Oyun alanına uygun mesafede rastgele hedef yerleştir."""
        kenar_x, kenar_y = 180, 150
        deneme = 0
        while deneme < 10:
            deneme += 1
            nx = random.uniform(kenar_x, G - kenar_x)
            ny = random.uniform(kenar_y, Y - kenar_y)

            cakisti = False
            for h in self.hedefler:
                if math.hypot(h.x - nx, h.y - ny) < 130:
                    cakisti = True
                    break
            if not cakisti:
                sure_orani = max(0.2, self.kalan_sure / self.tur_suresi)
                omur = random.uniform(1.2, 1.8) * (0.6 + 0.4 * sure_orani)
                bomba_olasiligi = 0.22 if len(self.hedefler) >= 1 else 0.08
                bomba = random.random() < bomba_olasiligi
                self.hedefler.append(Hedef(nx, ny, omur, bomba=bomba))
                break

    def _hedef_ciz(self, katman: np.ndarray, h: Hedef, nabiz: float):
        """Hacimli ve parlak neon disk çizimi."""
        cx, cy = int(h.x), int(h.y)
        omur_orani = max(0.0, h.kalan_omur / h.max_omur)
        r = int(h.yaricap * (0.92 + 0.08 * math.sin(nabiz * 8)))

        # Dış sınır / geri sayım halkası
        cv2.circle(katman, (cx, cy), r + 8, (int(h.renk[0] * 0.4), int(h.renk[1] * 0.4), int(h.renk[2] * 0.4)), 2, cv2.LINE_AA)
        halka(katman, cx, cy, omur_orani, r=r + 8, renk=h.renk, kalinlik=4)

        if h.bomba:
            # Bomba motifi: kırmızı parlayan dolgu + iç çarpı simgesi
            cv2.circle(katman, (cx, cy), r, (30, 30, 180), -1, cv2.LINE_AA)
            cv2.circle(katman, (cx, cy), int(r * 0.7), KIRMIZI, -1, cv2.LINE_AA)
            cv2.circle(katman, (cx, cy), int(r * 0.4), BEYAZ, -1, cv2.LINE_AA)
            l = int(r * 0.45)
            cv2.line(katman, (cx - l, cy - l), (cx + l, cy + l), (10, 10, 30), 4, cv2.LINE_AA)
            cv2.line(katman, (cx - l, cy + l), (cx + l, cy - l), (10, 10, 30), 4, cv2.LINE_AA)
        else:
            # Hedef diski: Hacimli iç gradyan efekti
            cv2.circle(katman, (cx, cy), r, (int(h.renk[0] * 0.3), int(h.renk[1] * 0.3), int(h.renk[2] * 0.3)), -1, cv2.LINE_AA)
            cv2.circle(katman, (cx, cy), int(r * 0.75), h.renk, 4, cv2.LINE_AA)
            cv2.circle(katman, (cx, cy), int(r * 0.5), (int(h.renk[0] * 0.8), int(h.renk[1] * 0.8), int(h.renk[2] * 0.8)), -1, cv2.LINE_AA)
            # Beyaz çekirdek parlaması
            cv2.circle(katman, (cx, cy), int(r * 0.22), BEYAZ, -1, cv2.LINE_AA)

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        dt = 0.033 if self.son_simdi == 0.0 else min(max(simdi - self.son_simdi, 0.0), 0.1)
        self.son_simdi = simdi

        # Ana oyuncu elleri
        secili_eller = self._sec_ana_eller(algi.eller)
        el_bilgileri = []  # [(cx, cy, hiz, avuc_acik)]

        # Eller arası hız ve konum hesaplama
        for i, el in enumerate(secili_eller):
            px9, py9 = px(el, 9)  # Avuç içi (orta MCP)
            px9 = max(0.0, min(float(G), px9))
            py9 = max(0.0, min(float(Y), py9))

            # Hız tespiti
            hiz = 0.0
            if i < len(self.onceki_eller):
                eski_x, eski_y, eski_t = self.onceki_eller[i]
                gecen = simdi - eski_t
                if 0.001 < gecen < 0.2:
                    mesafe = math.hypot(px9 - eski_x, py9 - eski_y)
                    hiz = mesafe / gecen

            # Parmak açıklık kontrolü (başlatma için)
            p_uc = [el[8].y, el[12].y, el[16].y, el[20].y]
            p_kok = [el[6].y, el[10].y, el[14].y, el[18].y]
            acik_sayi = sum(1 for u, k in zip(p_uc, p_kok) if u < k)
            avuc_acik = acik_sayi >= 3

            el_bilgileri.append((px9, py9, hiz, avuc_acik))

        self.onceki_eller = [(eb[0], eb[1], simdi) for eb in el_bilgileri]

        neon_katman = np.zeros_like(kare)

        # ------------------- DURUM: BEKLE -------------------
        if self.durum == "bekle":
            kare = bulanik_karanlik(kare, 0.45)
            bx, by = self.basla_pos
            nabiz = math.sin(simdi * 4.5) * 6.0
            r_simdi = int(self.basla_r + nabiz)

            el_icerde = False
            for ex, ey, _, _ in el_bilgileri:
                if math.hypot(ex - bx, ey - by) < self.basla_r + 20:
                    el_icerde = True
                    break

            if el_icerde:
                self.basla_tutma += dt
                if self.basla_tutma >= 1.0:
                    self.durum = "oyun"
                    self.kalan_sure = self.tur_suresi
                    self.skor = 0
                    self.hedefler.clear()
                    self.dalgalar.clear()
                    self.ses.cal("ding", 0.9)
                    self.basla_tutma = 0.0
            else:
                self.basla_tutma = max(0.0, self.basla_tutma - dt * 2.0)

            oran = min(1.0, self.basla_tutma / 1.0)

            cv2.circle(neon_katman, (bx, by), r_simdi, CAMGOBEGI, 4, cv2.LINE_AA)
            cv2.circle(neon_katman, (bx, by), r_simdi - 10, (40, 40, 60), -1, cv2.LINE_AA)
            halka(neon_katman, bx, by, oran, r=r_simdi, renk=SARI, kalinlik=8)

            parilti(kare, neon_katman, guc=1.6, sigma=3.5)

            yazi_koy(kare, "BAŞLA", bx, by - 16, 42, renk=BEYAZ, hiza="orta")
            yazi_koy(kare, "Elini çemberde tut", bx, by + 120, 32, renk=CAMGOBEGI, hiza="orta")

            if not el_bilgileri:
                yazi_koy(kare, "Kameraya Yaklaş", G // 2, Y - 120, 52, renk=SARI, hiza="orta")

            for ex, ey, _, _ in el_bilgileri:
                cv2.circle(kare, (int(ex), int(ey)), 24, SARI, 3, cv2.LINE_AA)
                cv2.circle(kare, (int(ex), int(ey)), 6, BEYAZ, -1, cv2.LINE_AA)

            return kare

        # ------------------- DURUM: OYUN -------------------
        elif self.durum == "oyun":
            self.kalan_sure -= dt
            if self.kalan_sure <= 0.0:
                self.kalan_sure = 0.0
                self.durum = "sonuc"
                self.sonuc_zamani = simdi
                if self.skor > self.rekor:
                    self.rekor = self.skor
                self.ses.cal("basari", 0.9)

            hedef_tavan = 2 if self.kalan_sure > 15 else 3
            if len(self.hedefler) < hedef_tavan and random.random() < 0.07:
                self._yeni_hedef_uret()

            if self.skor_pop > 1.0:
                self.skor_pop = max(1.0, self.skor_pop - dt * 2.5)

            aktif_hedefler: List[Hedef] = []
            for h in self.hedefler:
                h.kalan_omur -= dt

                vuruldu = False
                for ex, ey, hiz, _ in el_bilgileri:
                    mesafe = math.hypot(ex - h.x, ey - h.y)
                    if mesafe <= h.yaricap + 25 and hiz >= 850.0:
                        vuruldu = True
                        break

                if vuruldu:
                    if h.bomba:
                        self.skor = max(0, self.skor - 3)
                        self.sarsinti = 0.3
                        self.ses.cal("bonk", 0.9)
                        self.ses.cal("zap", 0.7)
                        self.parcaciklar.yay(h.x, h.y, 45, KIRMIZI, hiz=7.5)
                    else:
                        self.skor += 1
                        self.skor_pop = 1.35
                        self.ses.cal("pop", 0.8)
                        self.ses.cal("kick", 0.7)
                        self.parcaciklar.yay(h.x, h.y, 35, h.renk, hiz=6.0)

                    self.dalgalar.append(HalkaDalgasi(h.x, h.y, h.renk))
                    continue

                if h.kalan_omur <= 0.0:
                    if not h.bomba:
                        self.parcaciklar.yay(h.x, h.y, 10, (50, 50, 160), hiz=2.0)
                    continue

                aktif_hedefler.append(h)

            self.hedefler = aktif_hedefler

            aktif_dalgalar: List[HalkaDalgasi] = []
            for d in self.dalgalar:
                d.kalan -= dt
                d.r += (d.max_r - d.r) * (dt * 12.0)
                if d.kalan > 0:
                    aktif_dalgalar.append(d)
                    opak_oran = max(0.0, d.kalan / d.omur)
                    cv2.circle(
                        neon_katman,
                        (int(d.x), int(d.y)),
                        int(d.r),
                        (int(d.renk[0] * opak_oran), int(d.renk[1] * opak_oran), int(d.renk[2] * opak_oran)),
                        4,
                        cv2.LINE_AA,
                    )
            self.dalgalar = aktif_dalgalar

            for h in self.hedefler:
                self._hedef_ciz(neon_katman, h, simdi)

            for ex, ey, hiz, _ in el_bilgileri:
                el_renk = SARI if hiz < 850.0 else PEMBE
                el_r = 30 if hiz < 850.0 else 38
                cv2.circle(neon_katman, (int(ex), int(ey)), el_r, el_renk, 3, cv2.LINE_AA)
                cv2.circle(neon_katman, (int(ex), int(ey)), 8, BEYAZ, -1, cv2.LINE_AA)

            parilti(kare, neon_katman, guc=1.5, sigma=3.0)

            self.parcaciklar.guncelle(dt)
            self.parcaciklar.ciz(kare)

            panel(kare, 40, 24, 220, 114, renk=(15, 15, 25), opak=0.65, kenar=SARI)
            skor_boyut = int(58 * self.skor_pop)
            yazi_koy(kare, f"{self.skor}", 130, 42, skor_boyut, renk=SARI, hiza="orta")

            panel(kare, G - 220, 24, G - 40, 114, renk=(15, 15, 25), opak=0.65, kenar=CAMGOBEGI)
            kalan_int = int(math.ceil(self.kalan_sure))
            sure_renk = KIRMIZI if kalan_int <= 5 else CAMGOBEGI
            yazi_koy(kare, f"{kalan_int}s", G - 130, 42, 54, renk=sure_renk, hiza="orta")

            if self.sarsinti > 0.0:
                self.sarsinti -= dt
                dx = random.randint(-8, 8)
                dy = random.randint(-8, 8)
                M = np.float32([[1, 0, dx], [0, 1, dy]])
                kare = cv2.warpAffine(kare, M, (G, Y), borderMode=cv2.BORDER_REFLECT)

            return kare

        # ------------------- DURUM: SONUC -------------------
        elif self.durum == "sonuc":
            kare = bulanik_karanlik(kare, 0.40)
            gecen = simdi - self.sonuc_zamani

            self.parcaciklar.guncelle(dt)
            self.parcaciklar.ciz(kare)

            panel(kare, G // 2 - 320, Y // 2 - 180, G // 2 + 320, Y // 2 + 180, renk=(15, 15, 22), opak=0.82, kenar=PEMBE)

            yazi_koy(kare, "SÜRE DOLDU", G // 2, Y // 2 - 140, 48, renk=PEMBE, hiza="orta")
            yazi_koy(kare, f"{self.skor}", G // 2, Y // 2 - 70, 96, renk=SARI, hiza="orta")
            yazi_koy(kare, f"REKOR: {self.rekor}", G // 2, Y // 2 + 75, 40, renk=CAMGOBEGI, hiza="orta")

            if gecen >= 4.0:
                self.durum = "bekle"
                self.basla_tutma = 0.0

            return kare

        return kare
