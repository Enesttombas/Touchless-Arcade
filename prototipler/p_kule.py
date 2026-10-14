from __future__ import annotations

import math
import random
from dataclasses import dataclass
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
    Parcaciklar,
    bulanik_karanlik,
    halka,
    panel,
    parilti,
    px,
    yazi_koy,
)

PALET = [SARI, CAMGOBEGI, PEMBE, YESIL]


@dataclass
class Blok:
    dx: float
    w: float
    h: float
    renk: Tuple[int, int, int]
    pop: float = 1.0
    # Devrilme durumundaki serbest düşüş fiziği için
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    aci: float = 0.0
    v_aci: float = 0.0


def _kutu_ciz(
    img: np.ndarray,
    katman: np.ndarray,
    cx: float,
    cy: float,
    w: float,
    h: float,
    aci: float,
    renk: Tuple[int, int, int],
) -> None:
    """Hacimli, içi gölgeli, kenarı neon parlayan prosedürel blok çizer."""
    if w < 2 or h < 2 or cx < -200 or cx > G + 200 or cy < -200 or cy > Y + 200:
        return

    c = math.cos(aci)
    s = math.sin(aci)
    hw, hh = w * 0.5, h * 0.5

    def _don(lx: float, ly: float) -> List[int]:
        return [int(round(cx + lx * c - ly * s)), int(round(cy + lx * s + ly * c))]

    dis_pts = np.array(
        [_don(-hw, -hh), _don(hw, -hh), _don(hw, hh), _don(-hw, hh)],
        dtype=np.int32,
    )

    koyu = (int(renk[0] * 0.35), int(renk[1] * 0.35), int(renk[2] * 0.35))
    orta = (int(renk[0] * 0.65), int(renk[1] * 0.65), int(renk[2] * 0.65))
    acik = (
        min(255, int(renk[0] * 0.8 + 80)),
        min(255, int(renk[1] * 0.8 + 80)),
        min(255, int(renk[2] * 0.8 + 80)),
    )

    cv2.fillConvexPoly(img, dis_pts, koyu, cv2.LINE_AA)

    ihw, ihh = max(1.0, hw - 5.0), max(1.0, hh - 5.0)
    ic_pts = np.array(
        [_don(-ihw, -ihh), _don(ihw, -ihh), _don(ihw, ihh), _don(-ihw, ihh)],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(img, ic_pts, orta, cv2.LINE_AA)

    # Üst parlama şeridi (3B hacim hissi)
    ust_pts = np.array(
        [
            _don(-hw + 3, -hh + 3),
            _don(hw - 3, -hh + 3),
            _don(hw - 6, -hh + 9),
            _don(-hw + 6, -hh + 9),
        ],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(img, ust_pts, acik, cv2.LINE_AA)

    cv2.polylines(img, [dis_pts], True, acik, 2, cv2.LINE_AA)
    cv2.polylines(katman, [dis_pts], True, renk, 3, cv2.LINE_AA)


class Prototip:
    AD = "Kafada Kule"
    ACIKLAMA = "Kafanı sağa sola kaydırarak düşen blokları alnında dengele!"
    IHTIYAC = {"yuz"}
    SIRA = 5

    def __init__(self, ses: Any):
        self.ses = ses
        self.parcacik = Parcaciklar(180)
        self.katman = np.zeros((Y, G, 3), dtype=np.uint8)

        self.durum = "bekle"
        self.onceki_t: Optional[float] = None
        self.durum_t = 0.0
        self.yuz_sabit_t = 0.0
        self.son_sayim = 0

        self.skor = 0
        self.rekor = 0
        self.skor_pop = 0.0
        self.sarsinti = 0.0

        # Kafa takip durumu
        self.kafa_x = G * 0.5
        self.kafa_y = Y * 0.68
        self.kafa_vx = 0.0
        self.kafa_aci = 0.0
        self.yuz_var = False
        self.kayip_t = 0.0

        # Kule yay-sönüm fiziği
        self.kule: List[Blok] = []
        self.taban_w = 136.0
        self.blok_h = 34.0
        self.salinim = 0.0
        self.salinim_v = 0.0
        self.devrilenler: List[Blok] = []

        # Vinç ve aktif blok durumu
        self.vinc_faz = 0.0
        self.aktif_durum = "sallan"  # "sallan" | "dus"
        self.aktif_x = G * 0.5
        self.aktif_y = 110.0
        self.aktif_vx = 0.0
        self.aktif_vy = 0.0
        self.aktif_aci = 0.0
        self.aktif_w = 116.0
        self.aktif_renk = SARI
        self.sallan_t = 0.0

    def _ana_yuz(self, yuzler: List[Any]) -> Optional[Any]:
        """Kalabalık filtrelemesi: En yakın/büyük yüzü seçer, çok uzaktakileri yok sayar."""
        en_iyi = None
        en_alan = 0.0
        for y in yuzler:
            try:
                ax, ay = px(y, 10)
                cx, cy = px(y, 152)
                sx, sy = px(y, 33)
                dx, dy = px(y, 263)
                boy = math.hypot(cx - ax, cy - ay)
                en = math.hypot(dx - sx, dy - sy)
                alan = boy * en
                if boy > 42.0 and en > 28.0 and alan > en_alan:
                    en_alan = alan
                    en_iyi = y
            except Exception:
                continue
        return en_iyi

    def _yeni_aktif_blok(self) -> None:
        seviye = len(self.kule)
        self.aktif_w = max(68.0, 120.0 - seviye * 3.0)
        self.aktif_renk = PALET[seviye % len(PALET)]
        self.aktif_durum = "sallan"
        self.sallan_t = 0.0
        self.aktif_vy = 0.0
        self.aktif_vx = 0.0
        self.aktif_aci = 0.0

    def _oyun_baslat(self, simdi: float) -> None:
        self.durum = "oyun"
        self.durum_t = simdi
        self.skor = 0
        self.skor_pop = 0.0
        self.kule.clear()
        self.devrilenler.clear()
        self.salinim = 0.0
        self.salinim_v = 0.0
        self._yeni_aktif_blok()
        self.ses.cal("basari", 0.7)

    def _kuleyi_devir(self, simdi: float, yon: float) -> None:
        self.devrilenler.clear()
        taban_y = self._etkin_taban_y()
        for i, b in enumerate(self.kule):
            yuk = (i + 0.5) * b.h
            bx = self.kafa_x + b.dx + math.sin(self.salinim) * yuk
            by = taban_y - math.cos(self.salinim) * yuk
            b.x = bx
            b.y = by
            b.aci = self.salinim
            b.vx = yon * (140.0 + i * 35.0) + random.uniform(-60.0, 60.0)
            b.vy = -random.uniform(80.0, 220.0)
            b.v_aci = yon * random.uniform(2.5, 6.0)
            self.devrilenler.append(b)

        self.kule.clear()
        self.sarsinti = 0.3
        self.ses.cal("bonk", 0.9)
        self.ses.cal("zap", 0.6)
        self.parcacik.yay(self.kafa_x, taban_y - 40, 45, renk=KIRMIZI, hiz=6.0)
        self.durum = "sonuc"
        self.durum_t = simdi

    def _etkin_taban_y(self) -> float:
        """Kule yükseldikçe ekranın üstünden taşmaması için tabanı yumuşakça aşağı kaydırır."""
        kule_boy = len(self.kule) * self.blok_h
        max_taban = min(Y - 70.0, max(240.0, self.kafa_y - 18.0))
        gereken_taban = 230.0 + kule_boy
        return max(max_taban, min(Y - 50.0, gereken_taban))

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R"), 32):
            self.durum = "bekle"
            self.yuz_sabit_t = 0.0

    def isle(self, kare: np.ndarray, algi: Any, simdi: float) -> np.ndarray:
        if self.onceki_t is None:
            dt = 0.016
        else:
            dt = min(max(float(simdi - self.onceki_t), 0.0), 0.1)
        self.onceki_t = float(simdi)

        self.katman.fill(0)

        # 1. Yüz Algılama ve Yumuşatma
        yuz = self._ana_yuz(getattr(algi, "yuzler", []))
        if yuz is not None:
            self.yuz_var = True
            self.kayip_t = 0.0
            ax, ay = px(yuz, 10)
            sx, sy = px(yuz, 33)
            dx, dy = px(yuz, 263)

            hedef_x = float(np.clip(ax, 90.0, G - 90.0))
            hedef_y = float(np.clip(ay, 160.0, Y - 70.0))
            hedef_aci = float(np.clip(math.atan2(dy - sy, dx - sx), -0.65, 0.65))

            yeni_x = self.kafa_x + (hedef_x - self.kafa_x) * 0.48
            yeni_y = self.kafa_y + (hedef_y - self.kafa_y) * 0.48
            if dt > 1e-4:
                anlik_vx = (yeni_x - self.kafa_x) / dt
                self.kafa_vx = self.kafa_vx * 0.6 + anlik_vx * 0.4
            self.kafa_x = yeni_x
            self.kafa_y = yeni_y
            self.kafa_aci = self.kafa_aci + (hedef_aci - self.kafa_aci) * 0.45
        else:
            self.yuz_var = False
            self.kayip_t += dt
            self.kafa_vx *= 0.85
            self.kafa_aci *= 0.9

        if self.skor_pop > 0.0:
            self.skor_pop = max(0.0, self.skor_pop - dt * 3.5)

        # 2. Durum Makinesi
        if self.durum == "bekle":
            if not self.yuz_var:
                self.yuz_sabit_t = max(0.0, self.yuz_sabit_t - dt * 2.0)
                kare = bulanik_karanlik(kare, 0.55)

                # Çekim ekranı: dekoratif sallanan vinç ve örnek kule
                self.vinc_faz += dt * 2.0
                vx = G * 0.5 + math.sin(self.vinc_faz) * 180.0
                cv2.line(kare, (int(vx), 0), (int(vx), 95), BEYAZ, 2, cv2.LINE_AA)
                _kutu_ciz(kare, self.katman, vx, 115, 110, 34, math.sin(self.vinc_faz) * 0.1, SARI)

                parilti(kare, self.katman, guc=1.6, sigma=3.0)

                nabiz = 1.0 + 0.06 * math.sin(simdi * 4.5)
                panel(kare, G // 2 - 390, Y // 2 - 95, G // 2 + 390, Y // 2 + 95, opak=0.72, kenar=CAMGOBEGI)
                yazi_koy(
                    kare,
                    "KAFANDA KULE DİK!",
                    G // 2,
                    Y // 2 - 32,
                    54,
                    renk=SARI,
                    hiza="orta",
                    olcek=nabiz,
                )
                yazi_koy(
                    kare,
                    "Kameraya yaklaş ve kafanı sabit tut",
                    G // 2,
                    Y // 2 + 36,
                    30,
                    renk=BEYAZ,
                    hiza="orta",
                )
                return kare
            else:
                self.yuz_sabit_t += dt
                self._ciz_kafa_platformu(kare)

                if self.yuz_sabit_t < 1.0:
                    oran = self.yuz_sabit_t / 1.0
                    halka(kare, int(self.kafa_x), int(self.kafa_y - 70), oran, r=42, renk=CAMGOBEGI, kalinlik=7)
                    panel(kare, G // 2 - 260, 40, G // 2 + 260, 110, opak=0.65, kenar=CAMGOBEGI)
                    yazi_koy(kare, "BAŞLAMAK İÇİN SABİT DUR", G // 2, 75, 32, renk=BEYAZ, hiza="orta")
                else:
                    kalan = 4.0 - self.yuz_sabit_t
                    say = int(math.ceil(kalan))
                    if say != self.son_sayim and say in (1, 2, 3):
                        self.son_sayim = say
                        self.ses.cal("pop", 0.7)
                    if kalan <= 0.0:
                        self.son_sayim = 0
                        self._oyun_baslat(simdi)
                    else:
                        kesir = kalan - math.floor(kalan)
                        olcek = 1.0 + 0.35 * kesir
                        panel(kare, G // 2 - 90, Y // 2 - 90, G // 2 + 90, Y // 2 + 90, opak=0.7, kenar=SARI)
                        yazi_koy(
                            kare,
                            str(max(1, say)),
                            G // 2,
                            Y // 2,
                            110,
                            renk=SARI,
                            hiza="orta",
                            olcek=olcek,
                        )

                parilti(kare, self.katman, guc=1.7, sigma=3.0)
                return kare

        elif self.durum == "oyun":
            if self.kayip_t > 2.5:
                self.durum = "sonuc"
                self.durum_t = simdi
            else:
                self._oyun_guncelle(kare, dt, simdi)

        elif self.durum == "sonuc":
            self._sonuc_guncelle(kare, dt, simdi)

        # Parçacıklar ve Işıma
        self.parcacik.guncelle(dt)
        parilti(kare, self.katman, guc=1.8, sigma=3.0)
        self.parcacik.ciz(kare)

        # Üst Skor ve Bilgi Paneli (sadece oyun sırasında)
        if self.durum == "oyun":
            self._ciz_hud(kare)
        elif self.durum == "sonuc":
            self._ciz_sonuc_ekrani(kare, simdi)

        # Büyük olaylarda kısa ekran sarsıntısı
        if self.sarsinti > 0.0:
            self.sarsinti = max(0.0, self.sarsinti - dt)
            amp = int(12.0 * (self.sarsinti / 0.3))
            if amp > 0:
                sx = random.randint(-amp, amp)
                sy = random.randint(-amp, amp)
                M = np.float32([[1, 0, sx], [0, 1, sy]])
                kare[:] = cv2.warpAffine(kare, M, (G, Y), borderMode=cv2.BORDER_REPLICATE)

        return kare

    def _ciz_kafa_platformu(self, kare: np.ndarray) -> float:
        taban_y = self._etkin_taban_y()
        cx = int(self.kafa_x)
        cy = int(taban_y)
        hw = int(self.taban_w * 0.5)

        # Kafa üstü enerji tablası
        cv2.line(kare, (cx - hw, cy), (cx + hw, cy), BEYAZ, 6, cv2.LINE_AA)
        cv2.line(self.katman, (cx - hw - 4, cy), (cx + hw + 4, cy), CAMGOBEGI, 8, cv2.LINE_AA)
        cv2.circle(kare, (cx - hw, cy), 6, SARI, -1, cv2.LINE_AA)
        cv2.circle(kare, (cx + hw, cy), 6, SARI, -1, cv2.LINE_AA)
        return taban_y

    def _oyun_guncelle(self, kare: np.ndarray, dt: float, simdi: float) -> None:
        taban_y = self._ciz_kafa_platformu(kare)

        # Kule ağırlık merkezi ve yay-sönüm fiziği
        n = len(self.kule)
        com_dx = 0.0
        if n > 0:
            com_dx = sum(b.dx for b in self.kule) / float(n)

        hedef_salinim = (
            self.kafa_aci * 1.35
            + (com_dx / (self.taban_w * 0.5)) * 0.45 * (1.0 + n * 0.09)
            - (self.kafa_vx / 950.0) * 0.28
        )
        yay_k = 16.0
        sonum = 4.2
        ivme = (hedef_salinim - self.salinim) * yay_k - self.salinim_v * sonum
        self.salinim_v += ivme * dt
        self.salinim += self.salinim_v * dt

        # Devrilme kontrolü: toplam ağırlık merkezi veya aşırı eğim sınırı aşarsa
        etkin_kayma = abs(com_dx + math.sin(self.salinim) * (n * self.blok_h * 0.42))
        sinir = self.taban_w * 0.52
        if n > 0 and (etkin_kayma > sinir or abs(self.salinim) > 0.68):
            yon = 1.0 if (com_dx + self.salinim * 50.0) >= 0.0 else -1.0
            self._kuleyi_devir(simdi, yon)
            return

        # Mevcut kule bloklarını çiz
        ust_x = self.kafa_x
        ust_y = taban_y
        for i, b in enumerate(self.kule):
            if b.pop > 1.0:
                b.pop = max(1.0, b.pop - dt * 2.8)
            yuk = (i + 0.5) * b.h
            bx = self.kafa_x + b.dx + math.sin(self.salinim) * yuk
            by = taban_y - math.cos(self.salinim) * yuk
            _kutu_ciz(kare, self.katman, bx, by, b.w * b.pop, b.h * b.pop, self.salinim, b.renk)
            if i == n - 1:
                ust_x = self.kafa_x + b.dx + math.sin(self.salinim) * ((i + 1.0) * b.h)
                ust_y = taban_y - math.cos(self.salinim) * ((i + 1.0) * b.h)

        # Yukarıdaki vinç ve aktif blok
        hiz_carpan = min(2.4, 1.0 + n * 0.1)
        self.vinc_faz += dt * 2.1 * hiz_carpan
        vinc_x = G * 0.5 + math.sin(self.vinc_faz) * (G * 0.30)
        ip_boy = 78.0

        # Vinç rayı ve kancası
        cv2.line(kare, (120, 18), (G - 120, 18), (90, 90, 110), 4, cv2.LINE_AA)
        cv2.circle(kare, (int(vinc_x), 18), 10, SARI, -1, cv2.LINE_AA)

        if self.aktif_durum == "sallan":
            self.sallan_t += dt
            ip_aci = math.cos(self.vinc_faz) * 0.18
            bx = vinc_x + math.sin(ip_aci) * ip_boy
            by = 18.0 + math.cos(ip_aci) * ip_boy
            self.aktif_x = bx
            self.aktif_y = by
            self.aktif_aci = ip_aci * 0.5

            cv2.line(kare, (int(vinc_x), 18), (int(bx), int(by - self.blok_h * 0.5)), BEYAZ, 2, cv2.LINE_AA)
            cv2.line(
                self.katman,
                (int(vinc_x), 18),
                (int(bx), int(by - self.blok_h * 0.5)),
                CAMGOBEGI,
                2,
                cv2.LINE_AA,
            )

            # Düşey hiza kılavuz çizgisi (oyuncunun bloğu nereye oturtacağını 1 sn'de anlaması için)
            for gy in range(int(by + 25), int(ust_y - 10), 28):
                cv2.line(kare, (int(bx), gy), (int(bx), min(gy + 12, int(ust_y - 10))), (140, 140, 160), 1, cv2.LINE_AA)

            _kutu_ciz(kare, self.katman, bx, by, self.aktif_w, self.blok_h, self.aktif_aci, self.aktif_renk)

            bekleme_suresi = max(0.55, 1.15 - n * 0.04)
            hizali = abs(bx - ust_x) < 42.0 and self.sallan_t > 0.35
            if self.sallan_t >= bekleme_suresi or hizali:
                self.aktif_durum = "dus"
                self.aktif_vy = 160.0
                self.aktif_vx = math.cos(self.vinc_faz) * 55.0
                self.ses.cal("woosh", 0.5)

        elif self.aktif_durum == "dus":
            self.aktif_vy += 980.0 * dt
            self.aktif_x += self.aktif_vx * dt
            self.aktif_y += self.aktif_vy * dt
            self.aktif_aci *= 0.92

            _kutu_ciz(
                kare,
                self.katman,
                self.aktif_x,
                self.aktif_y,
                self.aktif_w,
                self.blok_h,
                self.aktif_aci,
                self.aktif_renk,
            )

            hedef_y = ust_y - self.blok_h * 0.5
            if self.aktif_y >= hedef_y and self.aktif_y - self.aktif_vy * dt <= hedef_y + 45.0:
                fark_x = self.aktif_x - ust_x
                alt_w = self.taban_w if n == 0 else self.kule[-1].w
                kabul_siniri = (alt_w + self.aktif_w) * 0.46

                if abs(fark_x) <= kabul_siniri:
                    onceki_dx = 0.0 if n == 0 else self.kule[-1].dx
                    yeni_dx = onceki_dx + fark_x * 0.82
                    yeni_blok = Blok(
                        dx=yeni_dx,
                        w=self.aktif_w,
                        h=self.blok_h,
                        renk=self.aktif_renk,
                        pop=1.28,
                    )
                    self.kule.append(yeni_blok)
                    self.skor = len(self.kule)
                    if self.skor > self.rekor:
                        self.rekor = self.skor
                    self.skor_pop = 1.0

                    # Kuleye darbe torku
                    self.salinim_v += (fark_x / 90.0) * 1.4

                    nota = min(84, 60 + self.skor * 2)
                    self.ses.cal(f"nota{nota}", 0.75)
                    self.ses.cal("pop", 0.6)
                    self.parcacik.yay(self.aktif_x, hedef_y, 26, renk=self.aktif_renk, hiz=4.5)

                    # Yeni ağırlık merkezi sınırı aştıysa hemen devril
                    yeni_com = sum(b.dx for b in self.kule) / float(len(self.kule))
                    if abs(yeni_com) > self.taban_w * 0.52:
                        self._kuleyi_devir(simdi, 1.0 if yeni_com >= 0 else -1.0)
                        return

                    self._yeni_aktif_blok()

            if self.aktif_y > Y + 60.0:
                # Blok ıskalandı: kule varsa devrilir, yoksa oyun biter
                self.ses.cal("bonk", 0.8)
                if len(self.kule) > 0:
                    self._kuleyi_devir(simdi, 1.0 if self.aktif_x >= self.kafa_x else -1.0)
                else:
                    self.durum = "sonuc"
                    self.durum_t = simdi

    def _sonuc_guncelle(self, kare: np.ndarray, dt: float, simdi: float) -> None:
        # Devrilen blokların düşüp yuvarlanması
        for b in self.devrilenler:
            b.vy += 1100.0 * dt
            b.x += b.vx * dt
            b.y += b.vy * dt
            b.aci += b.v_aci * dt
            _kutu_ciz(kare, self.katman, b.x, b.y, b.w, b.h, b.aci, b.renk)

        if simdi - self.durum_t >= 4.0:
            self.durum = "bekle"
            self.yuz_sabit_t = 0.0

    def _ciz_hud(self, kare: np.ndarray) -> None:
        panel(kare, 28, 22, 230, 145, opak=0.65, kenar=SARI)
        olcek = 1.0 + 0.28 * self.skor_pop
        yazi_koy(kare, str(self.skor), 129, 82, 92, renk=SARI, hiza="orta", olcek=olcek)

        if self.rekor > 0:
            panel(kare, G - 230, 22, G - 28, 95, opak=0.6, kenar=CAMGOBEGI)
            yazi_koy(kare, f"REKOR {self.rekor}", G - 129, 58, 32, renk=CAMGOBEGI, hiza="orta")

    def _ciz_sonuc_ekrani(self, kare: np.ndarray, simdi: float) -> None:
        gecen = min(1.0, (simdi - self.durum_t) / 0.3)
        olcek = 0.85 + 0.15 * gecen
        panel(kare, G // 2 - 280, Y // 2 - 150, G // 2 + 280, Y // 2 + 150, opak=0.78, kenar=PEMBE)
        yazi_koy(kare, "KULE DEVRİLDİ", G // 2, Y // 2 - 92, 46, renk=PEMBE, hiza="orta")
        yazi_koy(kare, str(self.skor), G // 2, Y // 2 + 5, 110, renk=SARI, hiza="orta", olcek=olcek)
        yazi_koy(kare, f"REKOR: {self.rekor}", G // 2, Y // 2 + 98, 34, renk=CAMGOBEGI, hiza="orta")
