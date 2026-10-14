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


@dataclass
class Cizik:
    x1: float
    y1: float
    x2: float
    y2: float
    bitis: float


class _Iz:
    def __init__(self, x: float, y: float, t: float):
        self.noktalar: List[Tuple[float, float, float, float]] = [(x, y, t, 0.0)]
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
        self.son_kesim_t: float = -10.0

        self.meyveler: List[Meyve] = []
        self.yarimlar: List[YarimMeyve] = []
        self.cizikler: List[Cizik] = []
        self.parcaciklar = Parcaciklar(350)

        self.onceki_t: Optional[float] = None
        self.durum_baslangic: float = 0.0
        self.avuc_sure: float = 0.0
        self.avuc_konum: Tuple[float, float] = (G / 2, Y / 2)

        self.son_firlatma: float = 0.0
        self.firlatma_sayisi: int = 0

        self.izler: List[_Iz] = []
        self.neon_katman = np.zeros((Y, G, 3), dtype=np.uint8)

        self.skor_pop: float = 0.0
        self.sarsinti_bitis: float = 0.0
        self.kirmizi_flas: float = 0.0

        self.kombo_yazi: str = ""
        self.kombo_bitis: float = 0.0
        self.kombo_boyut: int = 60
        self.kombo_x: float = G / 2
        self.kombo_y: float = Y / 2

        self.son_tik_sn: int = -1
        self.yeni_rekor_mu: bool = False
        self.konfeti_bitis: float = 0.0

        self.rng = random.Random(42)

        # Spriteları hazırla (110 px)
        emojiler = ["🍉", "🍍", "🍊", "🍋", "🥝", "🍇"]
        self.meyve_renkler = [
            (90, 90, 255),   # Karpuz
            (40, 220, 255),  # Ananas
            (30, 140, 255),  # Portakal
            (50, 245, 255),  # Limon
            (80, 220, 100),  # Kivi
            (220, 80, 180),  # Üzüm
        ]
        self.meyve_tam: List[np.ndarray] = []
        self.meyve_yarim1: List[np.ndarray] = []
        self.meyve_yarim2: List[np.ndarray] = []

        for e in emojiler:
            sp = emoji_sprite(e, boyut=110)
            self.meyve_tam.append(sp)
            h, w = sp.shape[:2]

            # Dikey yarım maskeler (kesiş doğrultusuna göre döndürülerek kullanılacak)
            y1 = sp.copy()
            y2 = sp.copy()
            y1[:, w // 2 :] = 0
            y2[:, : w // 2] = 0
            self.meyve_yarim1.append(y1)
            self.meyve_yarim2.append(y2)

        self.bomba_sp = emoji_sprite("💣", boyut=110)

    def _oyun_baslat(self, simdi: float) -> None:
        self.durum = "oyun"
        self.skor = 0
        self.kombo = 0
        self.son_kesim_t = -10.0
        self.durum_baslangic = simdi
        self.meyveler.clear()
        self.yarimlar.clear()
        self.cizikler.clear()
        self.kombo_bitis = 0.0
        self.firlatma_sayisi = 0
        self.son_firlatma = simdi - 0.5
        self.son_tik_sn = -1
        self.yeni_rekor_mu = False
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
                iz.noktalar.append((sx, sy, simdi, hiz))
                iz.son_x, iz.son_y, iz.son_t = sx, sy, simdi
                guncel_izler.append(iz)
            else:
                guncel_izler.append(_Iz(ux, uy, simdi))

        for idx, iz in enumerate(aktif_izler):
            if idx not in kullanilan_iz:
                guncel_izler.append(iz)

        for iz in guncel_izler:
            iz.noktalar = [(x, y, t, h) for (x, y, t, h) in iz.noktalar if (simdi - t) <= 0.25]

        self.izler = [iz for iz in guncel_izler if iz.noktalar]
        return segmentler

    def _kilic_ciz(self, kare: np.ndarray, simdi: float) -> None:
        if not self.izler:
            return
        self.neon_katman.fill(0)
        cizildi = False

        for iz in self.izler:
            pts = iz.noktalar
            if len(pts) >= 2:
                cizildi = True
                for i in range(len(pts) - 1):
                    x1, y1, t1, h1 = pts[i]
                    x2, y2, t2, h2 = pts[i + 1]
                    yas = simdi - t2
                    oran = max(0.0, min(1.0, 1.0 - yas / 0.25))
                    ort_hiz = (h1 + h2) * 0.5
                    hiz_oran = max(0.0, min(1.0, (ort_hiz - 200.0) / 1200.0))
                    kal_temel = 4.0 + 10.0 * hiz_oran
                    kal_hale = max(3, int((kal_temel + 12.0) * oran))
                    kal_ic = max(1, int(kal_temel * oran))

                    p1 = (int(x1), int(y1))
                    p2 = (int(x2), int(y2))
                    cv2.line(self.neon_katman, p1, p2, CAMGOBEGI, kal_hale, cv2.LINE_AA)
                    cv2.line(kare, p1, p2, BEYAZ, kal_ic, cv2.LINE_AA)

                # Uçta parlak nokta
                son_x, son_y, _, _ = pts[-1]
                cv2.circle(self.neon_katman, (int(son_x), int(son_y)), 12, CAMGOBEGI, -1, cv2.LINE_AA)
                cv2.circle(kare, (int(son_x), int(son_y)), 6, BEYAZ, -1, cv2.LINE_AA)
            elif len(pts) == 1:
                cizildi = True
                x1, y1, _, _ = pts[0]
                p1 = (int(x1), int(y1))
                cv2.circle(self.neon_katman, p1, 12, CAMGOBEGI, -1, cv2.LINE_AA)
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

        # Beyaz parlak çizikler (0.15 sn)
        if self.cizikler:
            kalan_cizik = []
            for cz in self.cizikler:
                if simdi < cz.bitis:
                    oran = (cz.bitis - simdi) / 0.15
                    kal = max(1, int(5 * oran))
                    cv2.line(kare, (int(cz.x1), int(cz.y1)), (int(cz.x2), int(cz.y2)), BEYAZ, kal, cv2.LINE_AA)
                    kalan_cizik.append(cz)
            self.cizikler = kalan_cizik

        # Parçacıklar ve kılıç izi
        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(kare)
        self._kilic_ciz(kare, simdi)

        # Kırmızı flaş (bomba patlaması - en çok 0.28 opaklık korunur)
        if self.kirmizi_flas > 0:
            opak = min(0.28, self.kirmizi_flas * 0.8)
            panel(kare, 0, 0, G, Y, renk=KIRMIZI, opak=opak)
            self.kirmizi_flas = max(0.0, self.kirmizi_flas - dt)

        # Ekran sarsıntısı (0.3 sn)
        if simdi < self.sarsinti_bitis:
            kalan_s = self.sarsinti_bitis - simdi
            guc = int(16 * (kalan_s / 0.3))
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
            self.yeni_rekor_mu = self.skor > self.rekor
            if self.yeni_rekor_mu:
                self.rekor = self.skor
                self.konfeti_bitis = simdi + 2.0
                for _ in range(120):
                    kx = self.rng.uniform(G * 0.1, G * 0.9)
                    ky = self.rng.uniform(50.0, Y * 0.7)
                    renk = self.rng.choice([SARI, CAMGOBEGI, PEMBE, YESIL, BEYAZ])
                    self.parcaciklar.yay(kx, ky, 1, renk=renk, hiz=6.5)

            # Skor tablosuna ekle
            self.skorlar.append(self.skor)
            self.skorlar.sort(reverse=True)
            self.skorlar = self.skorlar[:5]

            self.ses.cal("basari")
            return

        # 5. Kural: Son 5 sn süre çubuğu & ses
        if kalan <= 5.0:
            sn_int = int(math.ceil(kalan))
            if sn_int != self.son_tik_sn:
                self.son_tik_sn = sn_int
                self.ses.cal("hihat", ses=0.7)

        # Kombo sıfırlanma kontrolü (0.5 sn seri kuralı)
        if self.kombo > 0 and (simdi - self.son_kesim_t) > 0.5:
            self.kombo = 0

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
            k_x1, k_y1, k_x2, k_y2 = 0.0, 0.0, 0.0, 0.0
            for x1, y1, x2, y2, hiz in segmentler:
                if hiz > 800.0:
                    uz = self._dogru_parca_uzaklik(m.x, m.y, x1, y1, x2, y2)
                    if uz < 60.0:
                        kesildi = True
                        k_x1, k_y1, k_x2, k_y2 = x1, y1, x2, y2
                        break

            if kesildi:
                if m.bomba:
                    self.skor = max(0, self.skor - 3)
                    self.skor_pop = 0.3
                    self.kirmizi_flas = 0.35
                    self.sarsinti_bitis = simdi + 0.3
                    self.parcaciklar.yay(m.x, m.y, 35, renk=KIRMIZI, hiz=7.0)
                    self.ses.cal("bonk")
                    self.kombo = 0
                else:
                    self.skor += 1
                    self.skor_pop = 0.25
                    renk = self.meyve_renkler[m.tur]

                    # 2. Madde: 12-18 damla parçacığı
                    damla_adet = self.rng.randint(12, 18)
                    self.parcaciklar.yay(m.x, m.y, damla_adet, renk=renk, hiz=5.5)

                    # Kesiş çizgisi boyunca 0.15 sn beyaz parlak çizik
                    cx1 = m.x - (k_x2 - k_x1) * 0.4
                    cy1 = m.y - (k_y2 - k_y1) * 0.4
                    cx2 = m.x + (k_x2 - k_x1) * 0.4
                    cy2 = m.y + (k_y2 - k_y1) * 0.4
                    if math.hypot(cx2 - cx1, cy2 - cy1) < 40.0:
                        cx1, cy1 = m.x - 35.0, m.y - 35.0
                        cx2, cy2 = m.x + 35.0, m.y + 35.0
                    self.cizikler.append(Cizik(cx1, cy1, cx2, cy2, simdi + 0.15))

                    self.ses.cal("pop")
                    self.ses.cal("woosh", ses=0.55)

                    # 1. Madde: Kombo kontrolü (0.5 sn aralık)
                    if (simdi - self.son_kesim_t) <= 0.5:
                        self.kombo += 1
                    else:
                        self.kombo = 1
                    self.son_kesim_t = simdi

                    if self.kombo >= 3:
                        self.skor += self.kombo
                        self.skor_pop = 0.35
                        self.kombo_yazi = f"KOMBO x{self.kombo}!"
                        self.kombo_boyut = min(90, 60 + (self.kombo - 3) * 6)
                        self.kombo_bitis = simdi + 0.8
                        self.kombo_x = max(220.0, min(float(G - 220), m.x))
                        self.kombo_y = max(140.0, min(float(Y - 140), m.y))
                        self.ses.cal("basari", ses=0.8)

                    # 2. Madde: Kesiş doğrultusuna dik iki yarıma ayrılma
                    dx = k_x2 - k_x1
                    dy = k_y2 - k_y1
                    uzunluk = math.hypot(dx, dy)
                    if uzunluk > 1e-4:
                        nx = -dy / uzunluk
                        ny = dx / uzunluk
                        kesis_acisi = math.degrees(math.atan2(dy, dx))
                    else:
                        nx, ny = 1.0, 0.0
                        kesis_acisi = 0.0

                    itme_hiz = 320.0
                    sp1 = self.meyve_yarim1[m.tur]
                    sp2 = self.meyve_yarim2[m.tur]

                    self.yarimlar.append(
                        YarimMeyve(
                            m.x - nx * 14,
                            m.y - ny * 14,
                            m.vx - nx * itme_hiz,
                            m.vy - ny * itme_hiz - 150.0,
                            kesis_acisi,
                            -380.0,
                            sp1,
                        )
                    )
                    self.yarimlar.append(
                        YarimMeyve(
                            m.x + nx * 14,
                            m.y + ny * 14,
                            m.vx + nx * itme_hiz,
                            m.vy + ny * itme_hiz - 150.0,
                            kesis_acisi,
                            380.0,
                            sp2,
                        )
                    )

                if self.skor > self.rekor:
                    self.rekor = self.skor
                continue

            if m.y > Y + 120 and m.vy > 0:
                continue

            kalan_meyveler.append(m)

        self.meyveler = kalan_meyveler

        # Yarım meyveler: 0.6 sn içinde zıt yönlere savrulup dönerek düşer ve söner
        kalan_yarimlar: List[YarimMeyve] = []
        for ym in self.yarimlar:
            ym.yas += dt
            ym.x += ym.vx * dt
            ym.y += ym.vy * dt
            ym.vy += yercekimi * dt
            ym.aci = (ym.aci + ym.v_aci * dt) % 360.0
            if ym.yas < 0.6 and ym.y < Y + 120:
                opak = max(0.0, min(1.0, 1.0 - (ym.yas / 0.6)))
                bindir_merkez(kare, ym.sprite, int(ym.x), int(ym.y), aci=ym.aci, opak=opak)
                kalan_yarimlar.append(ym)
        self.yarimlar = kalan_yarimlar

        # Aktif meyveler
        for m in self.meyveler:
            if m.bomba:
                nabiz_r = int(52 + 6 * math.sin(simdi * 18.0))
                cv2.circle(kare, (int(m.x), int(m.y)), nabiz_r, KIRMIZI, 2, cv2.LINE_AA)
                bindir_merkez(kare, self.bomba_sp, int(m.x), int(m.y), aci=m.aci)
            else:
                bindir_merkez(kare, self.meyve_tam[m.tur], int(m.x), int(m.y), aci=m.aci)

        # Kombo pop yazısı
        if simdi < self.kombo_bitis:
            kalan_k = self.kombo_bitis - simdi
            olcek_k = 1.0 + 0.3 * math.sin((1.0 - kalan_k / 0.8) * math.pi)
            yazi_koy(
                kare,
                self.kombo_yazi,
                int(self.kombo_x),
                int(self.kombo_y - (0.8 - kalan_k) * 45),
                self.kombo_boyut,
                renk=SARI,
                hiza="orta",
                olcek=olcek_k,
            )

        # HUD: Sol üst skor
        self.skor_pop = max(0.0, self.skor_pop - dt)
        skor_olcek = 1.0 + 0.35 * (self.skor_pop / 0.35)
        panel(kare, 24, 20, 270, 150, opak=0.65, kenar=CAMGOBEGI)
        yazi_koy(kare, "SKOR", 147, 26, 26, renk=CAMGOBEGI, hiza="orta")
        yazi_koy(
            kare,
            str(self.skor),
            147,
            52,
            92,
            renk=SARI,
            hiza="orta",
            olcek=skor_olcek,
        )

        # HUD: Sağ üst süre + Son 5 sn kırmızı nabız
        panel(kare, G - 180, 20, G - 24, 150, opak=0.65, kenar=PEMBE)
        cx_s, cy_s = G - 102, 85
        sure_oran = kalan / 30.0

        if kalan <= 5.0:
            nabiz_kalinlik = int(8 + 4 * abs(math.sin(simdi * 8.0)))
            renk_s = KIRMIZI
            kalinlik_halka = nabiz_kalinlik
        else:
            renk_s = SARI if kalan <= 10.0 else CAMGOBEGI
            kalinlik_halka = 8

        cv2.circle(kare, (cx_s, cy_s), 44, (40, 40, 55), 7, cv2.LINE_AA)
        halka(kare, cx_s, cy_s, sure_oran, r=44, renk=renk_s, kalinlik=kalinlik_halka)
        yazi_koy(
            kare,
            str(int(math.ceil(kalan))),
            cx_s,
            cy_s - 22,
            40,
            renk=BEYAZ,
            hiza="orta",
        )

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

        # 4. Madde: Yeni rekor ise "YENİ REKOR!" altın parlama
        if self.yeni_rekor_mu:
            altin_nabiz = 1.0 + 0.08 * math.sin(simdi * 9.0)
            yazi_koy(
                kare,
                "YENİ REKOR!",
                G // 2,
                46,
                64,
                renk=SARI,
                hiza="orta",
                olcek=altin_nabiz,
            )

        panel(kare, G // 2 - 420, 120, G // 2 + 420, Y - 70, opak=0.8, kenar=SARI)

        nabiz = 1.0 + 0.04 * math.sin(simdi * 6.0)
        yazi_koy(
            kare,
            f"SKOR {self.skor}",
            G // 2,
            135,
            96,
            renk=SARI,
            hiza="orta",
            olcek=nabiz,
        )

        # Rekor tablosu: ilk 5 skor (bu turun skoru vurgulu)
        yazi_koy(kare, "LİDER TABLOSU", G // 2, 246, 32, renk=CAMGOBEGI, hiza="orta")
        vurgulandi = False
        bas_y = 290
        for idx, sk in enumerate(self.skorlar):
            bu_tur_mu = (sk == self.skor) and not vurgulandi
            if bu_tur_mu:
                vurgulandi = True
                renk_satir = YESIL
                ek = "  ★ (BU TUR)"
            else:
                renk_satir = BEYAZ
                ek = ""
            yazi_koy(
                kare,
                f"{idx + 1}.  {sk:3d} PUAN{ek}",
                G // 2 - 140,
                bas_y + idx * 42,
                30,
                renk=renk_satir,
                hiza="sol",
            )

        kalan_oran = max(0.0, min(1.0, (4.0 - gecen) / 4.0))
        halka(kare, G // 2, Y - 110, kalan_oran, r=26, renk=PEMBE, kalinlik=5)

    def tus(self, k: int) -> None:
        pass
