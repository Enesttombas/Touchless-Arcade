from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    KIRMIZI,
    PEMBE,
    SARI,
    Y,
    YESIL,
    Algi,
    Parcaciklar,
    Ses,
    baslik,
    bindir_merkez,
    bulanik_karanlik,
    el_durumu,
    emoji_sprite,
    halka,
    panel,
    parilti,
    px,
    yazi_koy,
)


@dataclass
class Meyve:
    x: float
    y: float
    vx: float
    vy: float
    aci: float
    v_aci: float
    tur: int  # 0..5 meyve, -1 bomba
    bomba: bool = False


@dataclass
class YarimMeyve:
    x: float
    y: float
    vx: float
    vy: float
    aci: float
    v_aci: float
    sprite: np.ndarray
    yas: float = 0.0


class _Iz:
    def __init__(self, x: float, y: float, t: float):
        self.noktalar: List[Tuple[float, float, float]] = [(x, y, t)]
        self.son_x = x
        self.son_y = y
        self.son_t = t


class Prototip:
    AD = "Neon Kılıç"
    ACIKLAMA = "Parmağını hızla savurarak meyveleri kes, bombalardan kaç!"
    IHTIYAC = {"el"}
    SIRA = 3

    def __init__(self, ses: Ses):
        self.ses = ses
        self.durum = "bekle"
        self.skor = 0
        self.rekor = 0
        self.skorlar: List[int] = []
        self.kombo: int = 0

        self.meyveler: List[Meyve] = []
        self.yarimlar: List[YarimMeyve] = []
        self.cizikler: List[Tuple[float, float, float, float, float]] = []
        self.parcaciklar = Parcaciklar(300)

        self.onceki_t: Optional[float] = None
        self.durum_baslangic: float = 0.0
        self.avuc_sure: float = 0.0
        self.avuc_konum: Tuple[float, float] = (G / 2, Y / 2)

        self.son_firlatma: float = 0.0
        self.firlatma_sayisi: int = 0
        self.son_tik_saniye: int = -1

        self.izler: List[_Iz] = []
        self.neon_katman = np.zeros((Y, G, 3), dtype=np.uint8)

        self.skor_pop: float = 0.0
        self.sarsinti_bitis: float = 0.0
        self.kirmizi_flas: float = 0.0

        self.son_kesim_zamani: float = 0.0
        self.kombo_yazi: str = ""
        self.kombo_n: int = 0
        self.kombo_bitis: float = 0.0

        self.son_tur_skor: int = 0
        self.yeni_rekor: bool = False
        self.vurgulu_idx: int = -1

        self.rng = random.Random(42)

        # Spriteları hazırla (110 px)
        emojiler = ["🍉", "🍍", "🍊", "🍋", "🥝", "🍇"]
        self.meyve_renkler = [
            (90, 90, 255),   # Karpuz (Kırmızımsı)
            (40, 220, 255),  # Ananas (Sarı)
            (30, 140, 255),  # Portakal (Turuncu)
            (50, 245, 255),  # Limon (Açık Sarı)
            (80, 220, 100),  # Kivi (Yeşil)
            (220, 80, 180),  # Üzüm (Mor/Pembe)
        ]
        self.meyve_tam: List[np.ndarray] = [emoji_sprite(e, boyut=110) for e in emojiler]
        self.bomba_sp = emoji_sprite("💣", boyut=110)

    def _oyun_baslat(self, simdi: float) -> None:
        self.durum = "oyun"
        self.skor = 0
        self.durum_baslangic = simdi
        self.meyveler.clear()
        self.yarimlar.clear()
        self.cizikler.clear()
        self.kombo = 0
        self.son_kesim_zamani = 0.0
        self.kombo_bitis = 0.0
        self.firlatma_sayisi = 0
        self.son_tik_saniye = -1
        self.son_firlatma = simdi - 0.5
        self.ses.cal("basari")

    def _meyve_firlat(self, gecen_sure: float) -> None:
        if self.firlatma_sayisi == 0:
            adet = 1
        else:
            max_adet = 2 if gecen_sure < 10.0 else 3
            adet = self.rng.randint(1, max_adet)

        self.firlatma_sayisi += 1
        for _ in range(adet):
            x = self.rng.uniform(G * 0.18, G * 0.82)
            y = float(Y + 55)
            merkez_egilim = (G * 0.5 - x) * 0.35
            vx = merkez_egilim + self.rng.uniform(-160.0, 160.0)
            vx = max(-250.0, min(250.0, vx))
            vy = self.rng.uniform(-1350.0, -1000.0)
            aci = self.rng.uniform(0.0, 360.0)
            v_aci = self.rng.uniform(-240.0, 240.0)

            bomba_mi = (self.firlatma_sayisi > 1) and (self.rng.random() < 0.15)
            if bomba_mi:
                self.meyveler.append(Meyve(x, y, vx, vy, aci, v_aci, -1, True))
            else:
                tur = self.rng.randint(0, len(self.meyve_tam) - 1)
                self.meyveler.append(Meyve(x, y, vx, vy, aci, v_aci, tur, False))

    @staticmethod
    def _dogru_parca_uzaklik(
        px0: float, py0: float, x1: float, y1: float, x2: float, y2: float
    ) -> float:
        dx = x2 - x1
        dy = y2 - y1
        uz2 = dx * dx + dy * dy
        if uz2 < 1e-6:
            return math.hypot(px0 - x1, py0 - y1)
        t = ((px0 - x1) * dx + (py0 - y1) * dy) / uz2
        t = max(0.0, min(1.0, t))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(px0 - proj_x, py0 - proj_y)

    def _kilic_guncelle(
        self, algi: Algi, simdi: float, dt: float
    ) -> List[Tuple[float, float, float, float, float]]:
        yeni_uclar: List[Tuple[float, float]] = []
        if algi and algi.eller:
            for el in algi.eller:
                if len(el) > 8:
                    ux, uy = px(el, 8)
                    ux = max(0.0, min(float(G), ux))
                    uy = max(0.0, min(float(Y), uy))
                    yeni_uclar.append((ux, uy))

        aktif_izler = [iz for iz in self.izler if (simdi - iz.son_t) <= 0.25]
        kullanilan_iz = set()
        segmentler: List[Tuple[float, float, float, float, float]] = []
        guncel_izler: List[_Iz] = []

        for ux, uy in yeni_uclar:
            en_yakin_idx = -1
            en_yakin_mes = 380.0
            for idx, iz in enumerate(aktif_izler):
                if idx in kullanilan_iz:
                    continue
                mes = math.hypot(ux - iz.son_x, uy - iz.son_y)
                if mes < en_yakin_mes:
                    en_yakin_mes = mes
                    en_yakin_idx = idx

            if en_yakin_idx != -1:
                kullanilan_iz.add(en_yakin_idx)
                iz = aktif_izler[en_yakin_idx]
                dt_iz = max(simdi - iz.son_t, dt, 1e-4)
                sx = iz.son_x * 0.25 + ux * 0.75
                sy = iz.son_y * 0.25 + uy * 0.75
                hiz = math.hypot(ux - iz.son_x, uy - iz.son_y) / dt_iz
                segmentler.append((iz.son_x, iz.son_y, ux, uy, hiz))
                iz.noktalar.append((sx, sy, simdi))
                iz.son_x, iz.son_y, iz.son_t = sx, sy, simdi
                guncel_izler.append(iz)
            else:
                guncel_izler.append(_Iz(ux, uy, simdi))

        for idx, iz in enumerate(aktif_izler):
            if idx not in kullanilan_iz:
                guncel_izler.append(iz)

        for iz in guncel_izler:
            iz.noktalar = [(x, y, t) for (x, y, t) in iz.noktalar if (simdi - t) <= 0.25]

        self.izler = [iz for iz in guncel_izler if iz.noktalar]
        return segmentler

    def _kilic_ciz(self, kare: np.ndarray, simdi: float) -> None:
        if not self.izler and not self.cizikler:
            return
        self.neon_katman.fill(0)
        cizildi = False

        # Beyaz parlak kesiş çizgileri (0.15 sn)
        kalan_cizikler = []
        for cx1, cy1, cx2, cy2, bitis_t in self.cizikler:
            if simdi < bitis_t:
                cizildi = True
                kalan_cizikler.append((cx1, cy1, cx2, cy2, bitis_t))
                oran = (bitis_t - simdi) / 0.15
                kal_hale = max(3, int(18 * oran))
                kal_ic = max(2, int(6 * oran))
                p1 = (int(cx1), int(cy1))
                p2 = (int(cx2), int(cy2))
                cv2.line(self.neon_katman, p1, p2, BEYAZ, kal_hale, cv2.LINE_AA)
                cv2.line(kare, p1, p2, BEYAZ, kal_ic, cv2.LINE_AA)
        self.cizikler = kalan_cizikler

        # 0.25 sn kuyruk, hıza göre 4->14 px kalınlık, uçta parlak nokta
        for iz in self.izler:
            pts = iz.noktalar
            n = len(pts)
            if n >= 2:
                cizildi = True
                for i in range(n - 1):
                    x1, y1, t1 = pts[i]
                    x2, y2, t2 = pts[i + 1]
                    yas = simdi - t2
                    oran = max(0.0, min(1.0, 1.0 - yas / 0.25))
                    dt_seg = max(1e-4, t2 - t1)
                    hiz_seg = math.hypot(x2 - x1, y2 - y1) / dt_seg
                    hiz_oran = min(1.0, max(0.0, (hiz_seg - 200.0) / 1200.0))
                    kal_taban = 4.0 + 10.0 * hiz_oran
                    kal_ic = max(1, int(kal_taban * oran))
                    kal_hale = max(2, int((kal_taban + 12.0) * oran))
                    p1 = (int(x1), int(y1))
                    p2 = (int(x2), int(y2))
                    cv2.line(self.neon_katman, p1, p2, CAMGOBEGI, kal_hale, cv2.LINE_AA)
                    cv2.line(kare, p1, p2, BEYAZ, kal_ic, cv2.LINE_AA)

                # Uçta parlak nokta
                son_x, son_y, son_t = pts[-1]
                if (simdi - son_t) < 0.08:
                    sp = (int(son_x), int(son_y))
                    cv2.circle(self.neon_katman, sp, 18, CAMGOBEGI, -1, cv2.LINE_AA)
                    cv2.circle(self.neon_katman, sp, 9, BEYAZ, -1, cv2.LINE_AA)
                    cv2.circle(kare, sp, 6, BEYAZ, -1, cv2.LINE_AA)
            elif n == 1:
                cizildi = True
                x1, y1, t1 = pts[0]
                p1 = (int(x1), int(y1))
                cv2.circle(self.neon_katman, p1, 14, CAMGOBEGI, -1, cv2.LINE_AA)
                cv2.circle(kare, p1, 6, BEYAZ, -1, cv2.LINE_AA)

        if cizildi:
            parilti(kare, self.neon_katman, guc=1.9, sigma=3.0)

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.onceki_t is None:
            dt = 0.016
            self.durum_baslangic = simdi
        else:
            dt = min(max(simdi - self.onceki_t, 0.0), 0.1)
        self.onceki_t = simdi

        segmentler = self._kilic_guncelle(algi, simdi, dt)

        if self.durum == "bekle":
            self._isle_bekle(kare, algi, simdi, dt)
        elif self.durum == "oyun":
            self._isle_oyun(kare, algi, simdi, dt, segmentler)
        elif self.durum == "sonuc":
            self._isle_sonuc(kare, algi, simdi, dt)

        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(kare)
        self._kilic_ciz(kare, simdi)

        if self.kirmizi_flas > 0:
            opak = min(0.28, self.kirmizi_flas * 1.0)
            panel(kare, 0, 0, G, Y, renk=KIRMIZI, opak=opak)
            self.kirmizi_flas = max(0.0, self.kirmizi_flas - dt)

        if simdi < self.sarsinti_bitis:
            kalan = self.sarsinti_bitis - simdi
            guc = int(16 * (kalan / 0.3))
            if guc > 0:
                dx = int(math.sin(simdi * 95.0) * guc)
                dy = int(math.cos(simdi * 115.0) * guc)
                m = np.float32([[1, 0, dx], [0, 1, dy]])
                cv2.warpAffine(kare, m, (G, Y), dst=kare, borderMode=cv2.BORDER_REPLICATE)

        return kare

    def _isle_bekle(self, kare: np.ndarray, algi: Algi, simdi: float, dt: float) -> None:
        eller_var = bool(algi and algi.eller)
        avuc_acik = False
        hedef_x, hedef_y = self.avuc_konum

        if eller_var:
            for i, el in enumerate(algi.eller):
                jest = algi.jestler[i] if (algi.jestler and i < len(algi.jestler)) else None
                durum = el_durumu(el)
                if jest == "Open_Palm" or durum == "sil":
                    avuc_acik = True
                    if len(el) > 9:
                        ex, ey = px(el, 9)
                        hedef_x = max(80.0, min(float(G - 80), ex))
                        hedef_y = max(80.0, min(float(Y - 80), ey))
                    break
            if not avuc_acik and len(algi.eller[0]) > 9:
                ex, ey = px(algi.eller[0], 9)
                hedef_x = max(80.0, min(float(G - 80), ex))
                hedef_y = max(80.0, min(float(Y - 80), ey))

        self.avuc_konum = (
            self.avuc_konum[0] * 0.5 + hedef_x * 0.5,
            self.avuc_konum[1] * 0.5 + hedef_y * 0.5,
        )

        if not eller_var:
            bg = bulanik_karanlik(kare, 0.55)
            np.copyto(kare, bg)

        panel(kare, G // 2 - 420, 16, G // 2 + 420, 130, opak=0.65, kenar=CAMGOBEGI)
        baslik(kare, "NEON KILIÇ", "Parmağını savur, meyveleri ikiye böl!", renk=CAMGOBEGI)

        nabiz = 1.0 + 0.05 * math.sin(simdi * 4.5)
        panel(kare, G // 2 - 460, Y // 2 - 90, G // 2 + 460, Y // 2 + 95, opak=0.7, kenar=SARI)
        yazi_koy(
            kare,
            "Avucunu göster, başla!",
            G // 2,
            Y // 2 - 62,
            54,
            renk=SARI,
            hiza="orta",
            olcek=nabiz,
        )
        yazi_koy(
            kare,
            "Başlamak için açık avucunu 1.5 saniye ekranda tut",
            G // 2,
            Y // 2 + 22,
            28,
            renk=BEYAZ,
            hiza="orta",
        )

        if self.rekor > 0:
            panel(kare, G // 2 - 160, Y - 95, G // 2 + 160, Y - 25, opak=0.65, kenar=PEMBE)
            yazi_koy(kare, f"Rekor: {self.rekor}", G // 2, Y - 80, 34, renk=PEMBE, hiza="orta")

        if avuc_acik:
            self.avuc_sure += dt
            oran = min(1.0, self.avuc_sure / 1.5)
            cx, cy = int(self.avuc_konum[0]), int(self.avuc_konum[1])
            cv2.circle(kare, (cx, cy), 56, (40, 40, 55), 8, cv2.LINE_AA)
            halka(kare, cx, cy, oran, r=56, renk=YESIL, kalinlik=10)
            if self.avuc_sure >= 1.5:
                self.avuc_sure = 0.0
                self._oyun_baslat(simdi)
        else:
            self.avuc_sure = max(0.0, self.avuc_sure - dt * 2.5)
            if self.avuc_sure > 0.02:
                oran = min(1.0, self.avuc_sure / 1.5)
                cx, cy = int(self.avuc_konum[0]), int(self.avuc_konum[1])
                halka(kare, cx, cy, oran, r=56, renk=SARI, kalinlik=8)

    def _kesilme_yarimlari_olustur(
        self, m: Meyve, dx: float, dy: float, uz: float
    ) -> None:
        kesis_aci = math.atan2(dy, dx)
        nx = -dy / uz
        ny = dx / uz

        yerel_aci = kesis_aci - math.radians(m.aci)
        lnx = -math.sin(yerel_aci)
        lny = math.cos(yerel_aci)

        sp = self.meyve_tam[m.tur]
        h, w = sp.shape[:2]
        gy, gx = np.ogrid[:h, :w]
        maske = ((gx - (w * 0.5)) * lnx + (gy - (h * 0.5)) * lny) > 0

        sp1 = sp.copy()
        sp1[~maske] = 0
        sp2 = sp.copy()
        sp2[maske] = 0

        itme = 240.0
        vx1 = m.vx + nx * itme
        vy1 = min(m.vy * 0.3, -160.0) + ny * itme
        vx2 = m.vx - nx * itme
        vy2 = min(m.vy * 0.3, -160.0) - ny * itme

        self.yarimlar.append(YarimMeyve(m.x, m.y, vx1, vy1, m.aci, -380.0, sp1, 0.0))
        self.yarimlar.append(YarimMeyve(m.x, m.y, vx2, vy2, m.aci, 380.0, sp2, 0.0))

    def _isle_oyun(
        self,
        kare: np.ndarray,
        algi: Algi,
        simdi: float,
        dt: float,
        segmentler: List[Tuple[float, float, float, float, float]],
    ) -> None:
        gecen = simdi - self.durum_baslangic
        kalan = 30.0 - gecen

        if kalan <= 0.0:
            self.durum = "sonuc"
            self.durum_baslangic = simdi
            self.son_tur_skor = self.skor
            self.yeni_rekor = (self.skor > self.rekor)

            if self.yeni_rekor:
                self.rekor = self.skor

            self.skorlar.append(self.skor)
            self.skorlar.sort(reverse=True)
            if len(self.skorlar) > 5:
                self.skorlar = self.skorlar[:5]

            self.vurgulu_idx = -1
            for idx, s in enumerate(self.skorlar):
                if s == self.son_tur_skor:
                    self.vurgulu_idx = idx
                    break

            if self.yeni_rekor:
                self.ses.cal("basari")
                renkler = [SARI, CAMGOBEGI, PEMBE, YESIL, BEYAZ]
                for _ in range(12):
                    kx = self.rng.uniform(G * 0.15, G * 0.85)
                    ky = self.rng.uniform(Y * 0.15, Y * 0.5)
                    kr = self.rng.choice(renkler)
                    self.parcaciklar.yay(kx, ky, 10, renk=kr, hiz=self.rng.uniform(4.0, 8.0))
            else:
                self.ses.cal("basari")
            return

        # Kombo zaman aşımı kontrolü (0.5 sn seri)
        if self.kombo > 0 and (simdi - self.son_kesim_zamani) > 0.5:
            self.kombo = 0

        # Son 5 saniye hihat tık sesi
        if kalan <= 5.0 and kalan > 0.0:
            sec_tik = int(math.ceil(kalan))
            if sec_tik != self.son_tik_saniye:
                self.son_tik_saniye = sec_tik
                self.ses.cal("hihat", ses=0.85)

        # Meyve fırlatma zamanlaması
        aralik = max(0.55, 0.9 - (gecen / 30.0) * 0.30)
        if simdi - self.son_firlatma >= aralik:
            self.son_firlatma = simdi
            self._meyve_firlat(gecen)

        kalan_meyveler: List[Meyve] = []
        yercekimi = 1500.0

        for m in self.meyveler:
            m.x += m.vx * dt
            m.y += m.vy * dt
            m.vy += yercekimi * dt
            m.aci = (m.aci + m.v_aci * dt) % 360.0

            kesildi = False
            k_dx = 1.0
            k_dy = 0.0
            k_uz = 1.0

            for x1, y1, x2, y2, hiz in segmentler:
                if hiz > 800.0:
                    uzaklik = self._dogru_parca_uzaklik(m.x, m.y, x1, y1, x2, y2)
                    if uzaklik < 60.0:
                        kesildi = True
                        k_dx = x2 - x1
                        k_dy = y2 - y1
                        k_uz = max(1e-4, math.hypot(k_dx, k_dy))
                        break

            if kesildi:
                if m.bomba:
                    self.skor = max(0, self.skor - 3)
                    self.kombo = 0
                    self.son_kesim_zamani = 0.0
                    self.skor_pop = 0.3
                    self.kirmizi_flas = 0.35
                    self.sarsinti_bitis = simdi + 0.3
                    self.parcaciklar.yay(m.x, m.y, 35, renk=KIRMIZI, hiz=7.0)
                    self.ses.cal("bonk")
                else:
                    self.skor += 1
                    self.skor_pop = 0.25

                    # Kombo güncelle
                    if (simdi - self.son_kesim_zamani) <= 0.5:
                        self.kombo += 1
                    else:
                        self.kombo = 1
                    self.son_kesim_zamani = simdi

                    if self.kombo >= 3:
                        bonus = self.kombo
                        self.skor += bonus
                        self.skor_pop = 0.35
                        self.kombo_yazi = f"KOMBO x{self.kombo}!"
                        self.kombo_n = self.kombo
                        self.kombo_bitis = simdi + 0.8
                        self.ses.cal("basari", ses=0.85)

                    # Kesişte 12-18 damla parçacığı
                    renk = self.meyve_renkler[m.tur]
                    damla_sayi = self.rng.randint(12, 18)
                    self.parcaciklar.yay(m.x, m.y, damla_sayi, renk=renk, hiz=6.0)

                    # Kesiş çizgisi boyunca 0.15 sn beyaz parlak çizik
                    cx1 = m.x - (k_dx / k_uz) * 75.0
                    cy1 = m.y - (k_dy / k_uz) * 75.0
                    cx2 = m.x + (k_dx / k_uz) * 75.0
                    cy2 = m.y + (k_dy / k_uz) * 75.0
                    self.cizikler.append((cx1, cy1, cx2, cy2, simdi + 0.15))

                    self.ses.cal("pop")
                    self.ses.cal("woosh", ses=0.55)

                    # Kesilen meyveyi iki yarıma böl
                    self._kesilme_yarimlari_olustur(m, k_dx, k_dy, k_uz)

                if self.skor > self.rekor:
                    self.rekor = self.skor
                continue

            if m.y > Y + 120 and m.vy > 0:
                continue

            kalan_meyveler.append(m)

        self.meyveler = kalan_meyveler

        # Yarım meyveler 0.6 sn içinde zıt yönlere savrulup dönerek düşer ve söner
        kalan_yarimlar: List[YarimMeyve] = []
        for ym in self.yarimlar:
            ym.yas += dt
            ym.x += ym.vx * dt
            ym.y += ym.vy * dt
            ym.vy += yercekimi * dt
            ym.aci = (ym.aci + ym.v_aci * dt) % 360.0
            if ym.yas < 0.6 and ym.y < Y + 120:
                opak = max(0.0, min(1.0, 1.0 - ym.yas / 0.6))
                bindir_merkez(kare, ym.sprite, int(ym.x), int(ym.y), aci=ym.aci, opak=opak)
                kalan_yarimlar.append(ym)
        self.yarimlar = kalan_yarimlar

        # Aktif meyveler ve bombalar
        for m in self.meyveler:
            if m.bomba:
                nabiz_r = int(52 + 6 * math.sin(simdi * 18.0))
                cv2.circle(kare, (int(m.x), int(m.y)), nabiz_r, KIRMIZI, 2, cv2.LINE_AA)
                bindir_merkez(kare, self.bomba_sp, int(m.x), int(m.y), aci=m.aci)
            else:
                bindir_merkez(kare, self.meyve_tam[m.tur], int(m.x), int(m.y), aci=m.aci)

        # Kombo pop yazısı (N ile büyüyen boyut 60->90 px)
        if simdi < self.kombo_bitis:
            kalan_k = self.kombo_bitis - simdi
            t_oran = 1.0 - (kalan_k / 0.8)
            pop_scale = 1.0 + 0.22 * math.sin(t_oran * math.pi)
            temel_boyut = min(90, 60 + (self.kombo_n - 3) * 6)
            boyut_anlik = int(temel_boyut * pop_scale)
            panel(kare, G // 2 - 280, Y // 2 - 75, G // 2 + 280, Y // 2 + 75, opak=0.45, kenar=SARI)
            yazi_koy(kare, self.kombo_yazi, G // 2, Y // 2 - 42, boyut_anlik, renk=SARI, hiza="orta")
            yazi_koy(kare, f"+{self.kombo_n} PUAN BONUS!", G // 2, Y // 2 + 25, 34, renk=CAMGOBEGI, hiza="orta")

        # HUD: Sol üst skor paneli
        self.skor_pop = max(0.0, self.skor_pop - dt)
        skor_olcek = 1.0 + 0.35 * (self.skor_pop / 0.35)
        panel(kare, 24, 20, 270, 150, opak=0.65, kenar=CAMGOBEGI)
        yazi_koy(kare, "SKOR", 147, 26, 26, renk=CAMGOBEGI, hiza="orta")
        yazi_koy(kare, str(self.skor), 147, 52, 92, renk=SARI, hiza="orta", olcek=skor_olcek)

        # HUD: Üst süre çubuğu (son 5 sn kırmızı nabız)
        sure_oran = max(0.0, min(1.0, kalan / 30.0))
        if kalan <= 5.0:
            nabiz_bar = 0.5 + 0.5 * math.sin(simdi * 20.0)
            cv2.rectangle(kare, (0, 0), (int(G * sure_oran), 12), KIRMIZI, -1)
            panel(kare, 0, 0, G, 14, renk=KIRMIZI, opak=0.25 * nabiz_bar)
        else:
            cv2.rectangle(kare, (0, 0), (int(G * sure_oran), 10), CAMGOBEGI, -1)

        # HUD: Sağ üst kalan süre halkası
        panel(kare, G - 180, 20, G - 24, 150, opak=0.65, kenar=KIRMIZI if kalan <= 5.0 else PEMBE)
        cx_s, cy_s = G - 102, 85
        if kalan <= 5.0:
            r_nabiz = int(44 + 5 * math.sin(simdi * 20.0))
            cv2.circle(kare, (cx_s, cy_s), r_nabiz, (40, 20, 25), 8, cv2.LINE_AA)
            halka(kare, cx_s, cy_s, sure_oran, r=r_nabiz, renk=KIRMIZI, kalinlik=9)
        else:
            renk_s = SARI if kalan <= 10.0 else CAMGOBEGI
            cv2.circle(kare, (cx_s, cy_s), 44, (40, 40, 55), 7, cv2.LINE_AA)
            halka(kare, cx_s, cy_s, sure_oran, r=44, renk=renk_s, kalinlik=8)
        yazi_koy(kare, str(int(math.ceil(kalan))), cx_s, cy_s - 22, 40, renk=BEYAZ, hiza="orta")

    def _isle_sonuc(self, kare: np.ndarray, algi: Algi, simdi: float, dt: float) -> None:
        gecen = simdi - self.durum_baslangic
        if gecen >= 4.0:
            self.durum = "bekle"
            self.durum_baslangic = simdi
            self.meyveler.clear()
            self.yarimlar.clear()
            self.cizikler.clear()
            return

        bg = bulanik_karanlik(kare, 0.55)
        np.copyto(kare, bg)

        panel(kare, G // 2 - 380, 35, G // 2 + 380, Y - 35, opak=0.8, kenar=SARI if self.yeni_rekor else CAMGOBEGI)

        # Başlık ve yeni rekor altın parlama
        if self.yeni_rekor:
            nabiz_rekor = 1.0 + 0.06 * math.sin(simdi * 10.0)
            yazi_koy(kare, "★ YENİ REKOR! ★", G // 2, 55, 52, renk=SARI, hiza="orta", olcek=nabiz_rekor)
        else:
            yazi_koy(kare, "OYUN BİTTİ", G // 2, 55, 46, renk=CAMGOBEGI, hiza="orta")

        # Büyük skor
        nabiz_skor = 1.0 + 0.03 * math.sin(simdi * 5.0)
        yazi_koy(kare, f"SKOR {self.son_tur_skor}", G // 2, 120, 88, renk=SARI, hiza="orta", olcek=nabiz_skor)

        # İlk 5 skor listesi (bu turun skoru vurgulu)
        yazi_koy(kare, "EN İYİ 5 SKOR", G // 2, 220, 28, renk=CAMGOBEGI, hiza="orta")
        start_y = 265
        for idx, s in enumerate(self.skorlar):
            cur_y = start_y + idx * 56
            bu_tur = (idx == self.vurgulu_idx)
            if bu_tur:
                panel(kare, G // 2 - 260, cur_y - 6, G // 2 + 260, cur_y + 44, renk=(30, 65, 40), opak=0.85, kenar=YESIL)
                renk_metin = YESIL
                etiket = "◄ BU TUR"
            else:
                panel(kare, G // 2 - 260, cur_y - 6, G // 2 + 260, cur_y + 44, renk=(25, 25, 35), opak=0.55)
                renk_metin = BEYAZ
                etiket = ""

            yazi_koy(kare, f"#{idx + 1}   {s} PUAN", G // 2 - 220, cur_y + 4, 30, renk=renk_metin, hiza="sol")
            if etiket:
                yazi_koy(kare, etiket, G // 2 + 220, cur_y + 6, 22, renk=YESIL, hiza="sag")

        # 4 sn geri sayım halkası
        kalan_oran = max(0.0, min(1.0, (4.0 - gecen) / 4.0))
        halka(kare, G // 2, Y - 70, kalan_oran, r=22, renk=PEMBE, kalinlik=5)
        yazi_koy(kare, f"{int(math.ceil(4.0 - gecen))}s", G // 2, Y - 80, 20, renk=BEYAZ, hiza="orta")

    def tus(self, k: int) -> None:
        pass
