"""Çiz ve Yuvarla - Etkileşimli neon fizik rampası ve basket oyunu."""

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
    Ses,
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


class Top:
    """Fiziksel top nesnesi."""

    __slots__ = ("x", "y", "vx", "vy", "r", "aci", "v_aci", "sprite_idx")

    def __init__(self, x: float, y: float, vx: float, vy: float, sprite_idx: int):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.r = 24.0
        self.aci = 0.0
        self.v_aci = (random.random() - 0.5) * 8.0
        self.sprite_idx = sprite_idx


class Prototip:
    AD = "Çiz ve Yuvarla"
    ACIKLAMA = "Havaya parmağınla neon rampa çiz, düşen topları sepete yuvarla!"
    IHTIYAC = {"el"}
    SIRA = 14

    def __init__(self, ses: Ses):
        self.ses = ses
        self.parcaciklar = Parcaciklar(tavan=400)

        # Durum yönetimi: "bekle", "oyun", "sonuc"
        self.durum = "bekle"
        self.skor = 0
        self.rekor = 0
        self.oyun_sure = 60.0
        self.kalan_sure = 60.0
        self.sonuc_sure = 0.0

        # Zaman takibi
        self.son_simdi: Optional[float] = None

        # Çizim ve jest takibi
        # segment: ((x1, y1), (x2, y2), dogum)
        self.cizgiler: List[Tuple[Tuple[float, float], Tuple[float, float], float]] = []
        self.son_isaret: Optional[Tuple[float, float]] = None
        self.yumusak_isaret: Optional[Tuple[float, float]] = None
        self.sil_sayac = 0.0

        # Toplar
        self.toplar: List[Top] = []
        self.top_spawn_sayac = 0.0

        # Sepet
        self.sepet_genislik = 180.0
        self.sepet_yukseklik = 80.0
        self.sepet_x = float(G // 2 - 90)
        self.sepet_hedef_x = self.sepet_x
        self.sepet_y = float(Y - 100)
        self.sepet_parlama = 0.0

        # Ekran sarsıntısı ve skor pop animasyonu
        self.shake = 0.0
        self.skor_pop = 0.0

        # Sprite'lar
        self.sprite_list = [
            emoji_sprite("🏀", 48),
            emoji_sprite("⭐", 48),
            emoji_sprite("🍊", 48),
        ]

    def _yeni_sepet_konumu(self) -> None:
        min_x = 150.0
        max_x = float(G - 150 - self.sepet_genislik)
        self.sepet_hedef_x = random.uniform(min_x, max_x)

    def _top_uret(self, simdi: float) -> None:
        if len(self.toplar) >= 14:
            return
        x = random.uniform(80.0, G - 80.0)
        y = -30.0
        vx = random.uniform(-40.0, 40.0)
        vy = random.uniform(20.0, 100.0)
        sprite_idx = random.randint(0, len(self.sprite_list) - 1)
        self.toplar.append(Top(x, y, vx, vy, sprite_idx))

    def _cizgileri_patlat(self, simdi: float) -> None:
        for (x1, y1), (x2, y2), _ in self.cizgiler:
            self.parcaciklar.yay((x1 + x2) * 0.5, (y1 + y2) * 0.5, 3, renk=CAMGOBEGI, hiz=5.0)
        self.cizgiler.clear()
        self.ses.cal("woosh", 0.8)
        self.shake = 0.25

    def _segmentleri_diziye_dok(self, simdi: float):
        # 15 sn ömürlü segmentler, son 2 sn söner
        gecerli = []
        for s in self.cizgiler:
            yas = simdi - s[2]
            if yas < 15.0:
                gecerli.append(s)
        self.cizgiler = gecerli

        if not self.cizgiler:
            return None

        # (N, 4): x1, y1, x2, y2
        arr = np.empty((len(self.cizgiler), 4), dtype=np.float32)
        for i, ((x1, y1), (x2, y2), _) in enumerate(self.cizgiler):
            arr[i, 0] = x1
            arr[i, 1] = y1
            arr[i, 2] = x2
            arr[i, 3] = y2
        return arr

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.son_simdi is None:
            dt = 0.033
        else:
            dt = min(max(simdi - self.son_simdi, 0.001), 0.1)
        self.son_simdi = simdi

        # Sarsıntı sönümleme
        self.shake = max(0.0, self.shake - dt)
        self.skor_pop = max(0.0, self.skor_pop - dt * 4.0)
        self.sepet_parlama = max(0.0, self.sepet_parlama - dt * 3.0)

        # Sepet konum yumuşatma (0.4 sn ease)
        self.sepet_x += (self.sepet_hedef_x - self.sepet_x) * min(1.0, dt * 7.0)

        # Parçacık güncelleme
        self.parcaciklar.guncelle(dt)

        # ----------------------------------------------------
        # El tespiti ve Jest İşleme
        # ----------------------------------------------------
        el_var = bool(algi and algi.eller and len(algi.eller) > 0)
        isaret_pt = None
        jest_ciz = False
        jest_sil = False

        if el_var:
            birincil_el = algi.eller[0]
            durum_str = el_durumu(birincil_el)
            raw_pt = px(birincil_el, 8)
            raw_x = max(0.0, min(float(G), raw_pt[0]))
            raw_y = max(0.0, min(float(Y), raw_pt[1]))

            # İşaret ucu yumuşatma
            if self.yumusak_isaret is None:
                self.yumusak_isaret = (raw_x, raw_y)
            else:
                alpha = 0.55
                self.yumusak_isaret = (
                    self.yumusak_isaret[0] * (1.0 - alpha) + raw_x * alpha,
                    self.yumusak_isaret[1] * (1.0 - alpha) + raw_y * alpha,
                )

            isaret_pt = self.yumusak_isaret

            if durum_str == "ciz":
                jest_ciz = True
                self.sil_sayac = 0.0
            elif durum_str == "sil":
                jest_sil = True
                self.sil_sayac += dt
                if self.sil_sayac >= 0.4 and self.cizgiler:
                    self._cizgileri_patlat(simdi)
                    self.sil_sayac = 0.0
            else:
                self.sil_sayac = 0.0
                self.son_isaret = None
        else:
            self.yumusak_isaret = None
            self.son_isaret = None
            self.sil_sayac = 0.0

        # Çizim mantığı
        if jest_ciz and isaret_pt is not None:
            if self.durum == "bekle":
                # İlk çizimle oyun başlar
                self.durum = "oyun"
                self.skor = 0
                self.kalan_sure = self.oyun_sure
                self.toplar.clear()
                self._yeni_sepet_konumu()
                self.ses.cal("ding", 0.6)

            if self.son_isaret is not None:
                dx = isaret_pt[0] - self.son_isaret[0]
                dy = isaret_pt[1] - self.son_isaret[1]
                dist = math.hypot(dx, dy)
                if dist >= 12.0:
                    self.cizgiler.append((self.son_isaret, isaret_pt, simdi))
                    if len(self.cizgiler) > 80:
                        self.cizgiler.pop(0)
                    self.son_isaret = isaret_pt
                    if random.random() < 0.25:
                        self.parcaciklar.yay(isaret_pt[0], isaret_pt[1], 1, CAMGOBEGI, hiz=1.5)
            else:
                self.son_isaret = isaret_pt
        else:
            self.son_isaret = None

        # ----------------------------------------------------
        # Durum Makinesi
        # ----------------------------------------------------
        if self.durum == "oyun":
            self.kalan_sure -= dt
            if self.kalan_sure <= 0:
                self.durum = "sonuc"
                self.sonuc_sure = 4.0
                if self.skor > self.rekor:
                    self.rekor = self.skor
                self.ses.cal("basari", 0.8)

            # Top doğurma
            self.top_spawn_sayac += dt
            if self.top_spawn_sayac >= 0.7:
                self.top_spawn_sayac = 0.0
                self._top_uret(simdi)

        elif self.durum == "sonuc":
            self.sonuc_sure -= dt
            if self.sonuc_sure <= 0:
                self.durum = "bekle"
                self.cizgiler.clear()
                self.toplar.clear()

        # ----------------------------------------------------
        # Top Fiziği (Tünellemesiz Alt Adımlar)
        # ----------------------------------------------------
        seg_dizi = self._segmentleri_diziye_dok(simdi)
        yercekimi = 1300.0  # px/s^2
        max_hiz = 900.0

        sepet_sol = self.sepet_x
        sepet_sag = self.sepet_x + self.sepet_genislik
        sepet_ust = self.sepet_y
        sepet_alt = self.sepet_y + self.sepet_yukseklik

        kalan_toplar: List[Top] = []

        for top in self.toplar:
            top.aci += top.v_aci * dt

            # Alt adım sayısını belirle
            top_hiz = math.hypot(top.vx, top.vy)
            adim_yol = max(top_hiz * dt, 1.0)
            n_sub = int(math.ceil(adim_yol / 6.0))
            n_sub = max(1, min(n_sub, 8))
            sub_dt = dt / n_sub

            top_canli = True

            for _ in range(n_sub):
                if not top_canli:
                    break

                # Hız güncelleme (yerçekimi)
                top.vy += yercekimi * sub_dt
                v_mag = math.hypot(top.vx, top.vy)
                if v_mag > max_hiz:
                    top.vx = (top.vx / v_mag) * max_hiz
                    top.vy = (top.vy / v_mag) * max_hiz

                onceki_y = top.y

                top.x += top.vx * sub_dt
                top.y += top.vy * sub_dt

                # Yan duvar sekmesi
                if top.x - top.r < 0:
                    top.x = top.r
                    top.vx = abs(top.vx) * 0.7
                elif top.x + top.r > G:
                    top.x = G - top.r
                    top.vx = -abs(top.vx) * 0.7

                # Sepete giriş kontrolü:
                if (
                    onceki_y <= sepet_ust + 10.0
                    and top.y >= sepet_ust
                    and (sepet_sol + 20.0 <= top.x <= sepet_sag - 20.0)
                ):
                    if self.durum == "oyun":
                        self.skor += 1
                        self.skor_pop = 0.3
                        self.sepet_parlama = 0.5
                        self.parcaciklar.yay(top.x, sepet_ust + 20.0, 25, PEMBE, hiz=7.0)
                        self.ses.cal("ding", 0.7)
                        if self.skor % 3 == 0:
                            self._yeni_sepet_konumu()
                    top_canli = False
                    break

                # Sepet dış duvarlarına çarpma / sekme
                dx_s = top.x - sepet_sol
                if abs(dx_s) < top.r + 10.0 and sepet_ust <= top.y <= sepet_alt:
                    top.x = sepet_sol - (top.r + 10.0) if dx_s < 0 else sepet_sol + (top.r + 10.0)
                    top.vx = -top.vx * 0.5

                dx_r = top.x - sepet_sag
                if abs(dx_r) < top.r + 10.0 and sepet_ust <= top.y <= sepet_alt:
                    top.x = sepet_sag + (top.r + 10.0) if dx_r > 0 else sepet_sag - (top.r + 10.0)
                    top.vx = -top.vx * 0.5

                # Segmentlerle çarpışma kontrolü (vektörel)
                if seg_dizi is not None and len(seg_dizi) > 0:
                    x1 = seg_dizi[:, 0]
                    y1 = seg_dizi[:, 1]
                    x2 = seg_dizi[:, 2]
                    y2 = seg_dizi[:, 3]

                    dx = x2 - x1
                    dy = y2 - y1
                    seg_len_sq = dx * dx + dy * dy
                    seg_len_sq = np.maximum(seg_len_sq, 1e-4)

                    t = ((top.x - x1) * dx + (top.y - y1) * dy) / seg_len_sq
                    t = np.clip(t, 0.0, 1.0)

                    proj_x = x1 + t * dx
                    proj_y = y1 + t * dy

                    diff_x = top.x - proj_x
                    diff_y = top.y - proj_y
                    dist_sq = diff_x * diff_x + diff_y * diff_y

                    carpma_yaricap = top.r + 5.0
                    carpan_idx = np.where(dist_sq < (carpma_yaricap * carpma_yaricap))[0]

                    if len(carpan_idx) > 0:
                        k_idx = carpan_idx[np.argmin(dist_sq[carpan_idx])]
                        cx_p = proj_x[k_idx]
                        cy_p = proj_y[k_idx]
                        d = math.sqrt(dist_sq[k_idx])

                        if d > 1e-3:
                            nx = (top.x - cx_p) / d
                            ny = (top.y - cy_p) / d
                        else:
                            seg_d = math.hypot(dx[k_idx], dy[k_idx])
                            nx = -dy[k_idx] / seg_d
                            ny = dx[k_idx] / seg_d

                        itme = carpma_yaricap - d
                        top.x += nx * itme
                        top.y += ny * itme

                        vn = top.vx * nx + top.vy * ny
                        if vn < 0:
                            vt_x = top.vx - vn * nx
                            vt_y = top.vy - vn * ny

                            vn_yeni = -0.45 * vn
                            vt_x *= 0.995
                            vt_y *= 0.995

                            top.vx = vt_x + vn_yeni * nx
                            top.vy = vt_y + vn_yeni * ny

                            top.v_aci = (vt_x + vt_y) * 0.05

            if top_canli and top.y < Y + 50.0:
                kalan_toplar.append(top)

        self.toplar = kalan_toplar

        # ----------------------------------------------------
        # GÖRSELLEŞTİRME VE RENDER
        # ----------------------------------------------------
        if self.durum == "bekle":
            kare = bulanik_karanlik(kare, 0.45)

        if self.shake > 0.01:
            sh_ox = int((random.random() - 0.5) * 12.0)
            sh_oy = int((random.random() - 0.5) * 12.0)
            M = np.float32([[1, 0, sh_ox], [0, 1, sh_oy]])
            kare = cv2.warpAffine(kare, M, (G, Y), borderMode=cv2.BORDER_REFLECT)

        # Neon Parlama Katmanı
        neon_katman = np.zeros_like(kare)

        # 1. Rampa Çizgileri
        for (x1, y1), (x2, y2), dogum in self.cizgiler:
            yas = simdi - dogum
            alfa = 1.0 if yas < 13.0 else max(0.0, (15.0 - yas) / 2.0)
            if alfa <= 0:
                continue

            pt1 = (int(x1), int(y1))
            pt2 = (int(x2), int(y2))

            c_val = int(220 * alfa)
            y_val = int(255 * alfa)
            renk_neon = (y_val, c_val, int(60 * alfa))

            cv2.line(neon_katman, pt1, pt2, renk_neon, 10, cv2.LINE_AA)
            cv2.line(neon_katman, pt1, pt2, (255, 255, 255), 3, cv2.LINE_AA)

        # 2. Sepet Çizimi (Neon PEMBE U Şekli)
        sepet_renk = (255, 140, 255) if self.sepet_parlama > 0.1 else PEMBE
        kalinlik_sepet = 8 + int(self.sepet_parlama * 6)

        sx0 = int(self.sepet_x)
        sx1 = int(self.sepet_x + self.sepet_genislik)
        sy0 = int(self.sepet_y)
        sy1 = int(self.sepet_y + self.sepet_yukseklik)

        pts_sepet = np.array(
            [[sx0, sy0], [sx0, sy1], [sx1, sy1], [sx1, sy0]],
            dtype=np.int32,
        )
        cv2.polylines(neon_katman, [pts_sepet], False, sepet_renk, kalinlik_sepet, cv2.LINE_AA)
        cv2.polylines(neon_katman, [pts_sepet], False, (255, 255, 255), 2, cv2.LINE_AA)

        # File deseni
        file_renk = (int(sepet_renk[0] * 0.4), int(sepet_renk[1] * 0.4), int(sepet_renk[2] * 0.4))
        for fx in range(sx0 + 20, sx1, 25):
            cv2.line(neon_katman, (fx, sy0 + 10), (fx + 10, sy1), file_renk, 2, cv2.LINE_AA)
            cv2.line(neon_katman, (fx, sy1), (fx + 10, sy0 + 10), file_renk, 2, cv2.LINE_AA)

        # Neon parıltıyı uygula
        parilti(kare, neon_katman, guc=1.6, sigma=3.5)

        # 3. Topları Çiz
        for top in self.toplar:
            sprite = self.sprite_list[top.sprite_idx]
            bindir_merkez(kare, sprite, int(top.x), int(top.y), boyut=48, aci=math.degrees(top.aci))

        # 4. Parçacıkları Çiz
        self.parcaciklar.ciz(kare)

        # 5. El İmleci
        if isaret_pt is not None:
            ix, iy = int(isaret_pt[0]), int(isaret_pt[1])
            if jest_ciz:
                cv2.circle(kare, (ix, iy), 12, SARI, -1, cv2.LINE_AA)
                cv2.circle(kare, (ix, iy), 18, (255, 255, 255), 2, cv2.LINE_AA)
            elif jest_sil:
                ilerleme = min(1.0, self.sil_sayac / 0.4)
                halka(kare, ix, iy, ilerleme, r=26, renk=KIRMIZI, kalinlik=5)
                cv2.circle(kare, (ix, iy), 8, KIRMIZI, -1, cv2.LINE_AA)
            else:
                cv2.circle(kare, (ix, iy), 8, BEYAZ, 2, cv2.LINE_AA)

        # ----------------------------------------------------
        # HUD / Durum Arayüzü
        # ----------------------------------------------------
        if self.durum == "bekle":
            panel(kare, 240, 220, 1040, 500, renk=(15, 15, 25), opak=0.75, kenar=CAMGOBEGI)
            nabiz = 1.0 + 0.05 * math.sin(simdi * 4.0)
            yazi_koy(kare, "ÇİZ VE YUVARLA", G // 2, 270, 56, renk=SARI, hiza="orta", olcek=nabiz)
            yazi_koy(
                kare,
                "Parmağınla rampa çiz, topları sepete yuvarla!",
                G // 2,
                350,
                32,
                renk=BEYAZ,
                hiza="orta",
            )
            yazi_koy(
                kare,
                "İşaret parmağı: Çiz  ·  Açık avuç: Sil",
                G // 2,
                420,
                26,
                renk=CAMGOBEGI,
                hiza="orta",
            )

            if self.rekor > 0:
                yazi_koy(
                    kare,
                    f"Günün Rekoru: {self.rekor}",
                    G // 2,
                    465,
                    22,
                    renk=PEMBE,
                    hiza="orta",
                )

        elif self.durum == "oyun":
            panel(kare, 20, 16, 260, 110, renk=(20, 20, 30), opak=0.65, kenar=CAMGOBEGI)
            skor_olcek = 1.0 + self.skor_pop * 0.8
            yazi_koy(kare, "SKOR", 40, 42, 22, renk=CAMGOBEGI, hiza="sol")
            yazi_koy(kare, str(self.skor), 150, 68, 64, renk=BEYAZ, hiza="sol", olcek=skor_olcek)

            panel(kare, 360, 24, 920, 60, renk=(20, 20, 30), opak=0.6, kenar=None)
            oran = max(0.0, min(1.0, self.kalan_sure / self.oyun_sure))
            bar_w = int(540 * oran)
            cubuk_renk = YESIL if oran > 0.3 else (KIRMIZI if oran < 0.15 else SARI)
            cv2.rectangle(kare, (370, 32), (370 + bar_w, 52), cubuk_renk, -1)
            yazi_koy(kare, f"{int(self.kalan_sure)}s", 950, 44, 28, renk=BEYAZ, hiza="sol")

            if self.rekor > 0:
                panel(kare, 1060, 16, 1260, 75, renk=(20, 20, 30), opak=0.65, kenar=PEMBE)
                yazi_koy(kare, f"REKOR: {self.rekor}", 1160, 46, 26, renk=PEMBE, hiza="orta")

        elif self.durum == "sonuc":
            panel(kare, 320, 180, 960, 540, renk=(15, 15, 25), opak=0.85, kenar=PEMBE)
            yazi_koy(kare, "SÜRE DOLDU!", G // 2, 240, 52, renk=SARI, hiza="orta")
            yazi_koy(kare, f"SKOR: {self.skor}", G // 2, 340, 78, renk=BEYAZ, hiza="orta")

            if self.skor >= self.rekor and self.skor > 0:
                yazi_koy(kare, "YENİ REKOR!", G // 2, 425, 36, renk=YESIL, hiza="orta")
            else:
                yazi_koy(kare, f"En Yüksek: {self.rekor}", G // 2, 425, 30, renk=CAMGOBEGI, hiza="orta")

            halka(kare, G // 2, 485, max(0.0, self.sonuc_sure / 4.0), r=22, renk=PEMBE, kalinlik=4)

        return kare

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R"), 32):
            self.cizgiler.clear()
            self.toplar.clear()
