from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

import cekirdek as ck
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
    baslik,
    bindir_merkez,
    bulanik_karanlik,
    emoji_sprite,
    panel,
    parilti,
    px,
    yazi_koy,
)


@dataclass
class _Kalp:
    x: float
    y: float
    vx: float
    vy: float
    yas: float
    omur: float
    boy: int


class _YuzTakip:
    def __init__(self, idx: int, tur: int, maske_sayisi: int, simdi: float):
        self.alin: Tuple[float, float] = (G / 2, Y / 2)
        self.burun: Tuple[float, float] = (G / 2, Y / 2)
        self.cene: Tuple[float, float] = (G / 2, Y / 2)
        self.goz_sol: Tuple[float, float] = (G / 2 - 40, Y / 2)
        self.goz_sag: Tuple[float, float] = (G / 2 + 40, Y / 2)
        self.agiz: Tuple[float, float] = (G / 2, Y / 2 + 30)
        self.s: float = 90.0
        self.aci: float = 0.0
        self.hazir: bool = False

        self.maske_idx: int = (idx + tur) % maske_sayisi
        self.eski_idx: Optional[int] = None
        self.gecis_t0: float = simdi - 10.0
        self.maske_takilma_t0: float = simdi

        self.kas_t0: float = -10.0
        self.son_ding: float = -10.0
        self.goz_kapali_sure: float = 0.0
        self.son_kirp_degisim: float = -10.0

        self.foto_tetiklendi: bool = False

    def guncelle_konum(self, lm: Any, dt: float) -> None:
        try:
            ax, ay = px(lm, 10)
            bx, by = px(lm, 1)
            cx, cy = px(lm, 152)
            gx1, gy1 = px(lm, 33)
            gx2, gy2 = px(lm, 263)
            ux, uy = px(lm, 13)
            dx, dy = px(lm, 14)
        except Exception:
            return

        if gx1 > gx2:
            gx1, gy1, gx2, gy2 = gx2, gy2, gx1, gy1

        agx, agy = (ux + dx) * 0.5, (uy + dy) * 0.5
        s_yeni = max(28.0, min(420.0, math.hypot(gx2 - gx1, gy2 - gy1)))
        aci_yeni = math.atan2(gy2 - gy1, gx2 - gx1)
        aci_yeni = max(-1.1, min(1.1, aci_yeni))

        if not self.hazir:
            self.alin = (ax, ay)
            self.burun = (bx, by)
            self.cene = (cx, cy)
            self.goz_sol = (gx1, gy1)
            self.goz_sag = (gx2, gy2)
            self.agiz = (agx, agy)
            self.s = s_yeni
            self.aci = aci_yeni
            self.hazir = True
            return

        hiz = math.hypot(bx - self.burun[0], by - self.burun[1]) / max(dt, 0.001)
        oran = min(1.0, max(0.0, (hiz - 25.0) / 280.0))
        a = 0.25 + 0.50 * oran
        b = 1.0 - a

        self.alin = (b * self.alin[0] + a * ax, b * self.alin[1] + a * ay)
        self.burun = (b * self.burun[0] + a * bx, b * self.burun[1] + a * by)
        self.cene = (b * self.cene[0] + a * cx, b * self.cene[1] + a * cy)
        self.goz_sol = (b * self.goz_sol[0] + a * gx1, b * self.goz_sol[1] + a * gy1)
        self.goz_sag = (b * self.goz_sag[0] + a * gx2, b * self.goz_sag[1] + a * gy2)
        self.agiz = (b * self.agiz[0] + a * agx, b * self.agiz[1] + a * agy)
        self.s = b * self.s + a * s_yeni

        fark = (aci_yeni - self.aci + math.pi) % (2 * math.pi) - math.pi
        self.aci = self.aci + a * fark

    def maske_degistir(self, yeni_idx: int, simdi: float) -> None:
        if yeni_idx != self.maske_idx:
            self.eski_idx = self.maske_idx
            self.maske_idx = yeni_idx
            self.gecis_t0 = simdi
            self.maske_takilma_t0 = simdi
            self.foto_tetiklendi = False


class Prototip:
    AD = "AR Maskeler"
    ACIKLAMA = "Kameraya bak, ağzını aç, kaşını kaldır veya göz kırparak maskeni değiştir!"
    IHTIYAC = {"yuz", "blend"}
    SIRA = 17

    MASKELER = [
        "Kral",
        "Havalı",
        "Kedi",
        "Şeytan",
        "Uzaylı",
        "Korsan",
        "Ayıcık",
        "Kalp Göz",
    ]

    def __init__(self, ses: Any):
        self.ses = ses
        self.maskeler: List[str] = []
        self.takipler: List[_YuzTakip] = []
        self.tur: int = 0
        self.son_oto_gecis: Optional[float] = None
        self.onceki_t: Optional[float] = None

        self.parcacik = Parcaciklar(200)
        self.kalpler: List[_Kalp] = []
        self.rng = np.random.RandomState(17)

        self._sprites: Dict[str, np.ndarray] = {}
        self._katman = np.zeros((Y, G, 3), dtype=np.uint8)
        self.flas_t0: float = -10.0

    def _sprite_al(self, e: str, boy: int = 256) -> np.ndarray:
        anahtar = f"{e}_{boy}"
        sp = self._sprites.get(anahtar)
        if sp is None:
            sp = emoji_sprite(e, boyut=boy)
            self._sprites[anahtar] = sp
        return sp

    def tus(self, k: int) -> None:
        if k == 32 or k == ord(" "):
            self._tum_maskeleri_ilerlet(self.onceki_t if self.onceki_t is not None else 0.0)

    def _tum_maskeleri_ilerlet(self, simdi: float) -> None:
        self.tur = (self.tur + 1) % len(self.MASKELER)
        self.son_oto_gecis = simdi
        n = len(self.MASKELER)
        for t in self.takipler:
            t.maske_degistir((t.maske_idx + 1) % n, simdi)
        self.ses.cal("pop", 0.7)

    @staticmethod
    def _don(merkez: Tuple[float, float], dx: float, dy: float, cos_a: float, sin_a: float) -> Tuple[int, int]:
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        return int(round(merkez[0] + rx)), int(round(merkez[1] + ry))

    def _ciz_maske(
        self,
        kare: np.ndarray,
        katman: np.ndarray,
        t: _YuzTakip,
        maske_ad: str,
        olcek_carpan: float,
        simdi: float,
    ) -> None:
        s = t.s * olcek_carpan
        if s < 8.0:
            return

        aci = t.aci
        aci_deg = math.degrees(aci)
        cos_a = math.cos(aci)
        sin_a = math.sin(aci)

        alin = t.alin
        burun = t.burun
        goz_sol = t.goz_sol
        goz_sag = t.goz_sag
        goz_merkez = ((goz_sol[0] + goz_sag[0]) * 0.5, (goz_sol[1] + goz_sag[1]) * 0.5)
        yuz_merkez = ((alin[0] + t.cene[0]) * 0.5, (alin[1] + t.cene[1]) * 0.5)

        if maske_ad == "Kral":
            sp = self._sprite_al("👑", 256)
            tx, ty = self._don(alin, 0.0, -0.9 * s, cos_a, sin_a)
            boy = max(24, min(600, int(round(1.6 * s))))
            bindir_merkez(kare, sp, tx, ty, boyut=boy, aci=-aci_deg, opak=1.0)
            for dx_k, dy_k in [(-0.55 * s, -0.95 * s), (0.0, -1.18 * s), (0.55 * s, -0.95 * s)]:
                px_k, py_k = self._don(alin, dx_k, dy_k, cos_a, sin_a)
                cv2.circle(katman, (px_k, py_k), max(3, int(0.06 * s)), SARI, -1, cv2.LINE_AA)

        elif maske_ad == "Havalı":
            kalin = max(2, int(0.07 * s))
            for isaret in (-1.0, 1.0):
                cx_off = isaret * 0.34 * s
                w, h = 0.28 * s, 0.17 * s
                pts_local = [
                    (cx_off - w * 0.85, -h),
                    (cx_off + w * 0.85, -h),
                    (cx_off + w, -h * 0.5),
                    (cx_off + w * 0.9, h * 0.85),
                    (cx_off + w * 0.6, h),
                    (cx_off - w * 0.6, h),
                    (cx_off - w * 0.9, h * 0.85),
                    (cx_off - w, -h * 0.5),
                ]
                pts = np.array([self._don(goz_merkez, px_l, py_l, cos_a, sin_a) for px_l, py_l in pts_local], dtype=np.int32)
                cv2.fillPoly(kare, [pts], (18, 18, 24), cv2.LINE_AA)
                cv2.polylines(katman, [pts], True, CAMGOBEGI, kalin, cv2.LINE_AA)
                cv2.polylines(kare, [pts], True, (40, 40, 50), max(2, kalin + 2), cv2.LINE_AA)

                y1 = self._don(goz_merkez, cx_off - w * 0.55, -h * 0.55, cos_a, sin_a)
                y2 = self._don(goz_merkez, cx_off - w * 0.10, h * 0.55, cos_a, sin_a)
                cv2.line(katman, y1, y2, CAMGOBEGI, max(2, int(0.05 * s)), cv2.LINE_AA)
                y3 = self._don(goz_merkez, cx_off + w * 0.05, -h * 0.55, cos_a, sin_a)
                y4 = self._don(goz_merkez, cx_off + w * 0.35, h * 0.25, cos_a, sin_a)
                cv2.line(katman, y3, y4, BEYAZ, max(1, int(0.03 * s)), cv2.LINE_AA)

            k1 = self._don(goz_merkez, -0.07 * s, -0.04 * s, cos_a, sin_a)
            k2 = self._don(goz_merkez, 0.07 * s, -0.04 * s, cos_a, sin_a)
            cv2.line(katman, k1, k2, CAMGOBEGI, kalin + 1, cv2.LINE_AA)
            s_sol1 = self._don(goz_merkez, -0.62 * s, -0.05 * s, cos_a, sin_a)
            s_sol2 = self._don(goz_merkez, -0.78 * s, -0.12 * s, cos_a, sin_a)
            s_sag1 = self._don(goz_merkez, 0.62 * s, -0.05 * s, cos_a, sin_a)
            s_sag2 = self._don(goz_merkez, 0.78 * s, -0.12 * s, cos_a, sin_a)
            cv2.line(katman, s_sol1, s_sol2, CAMGOBEGI, kalin, cv2.LINE_AA)
            cv2.line(katman, s_sag1, s_sag2, CAMGOBEGI, kalin, cv2.LINE_AA)

        elif maske_ad == "Kedi":
            kalin = max(2, int(0.065 * s))
            for isaret in (-1.0, 1.0):
                dis = self._don(alin, isaret * 0.68 * s, -0.05 * s, cos_a, sin_a)
                ic = self._don(alin, isaret * 0.22 * s, -0.18 * s, cos_a, sin_a)
                tepe = self._don(alin, isaret * 0.58 * s, -0.78 * s, cos_a, sin_a)
                ucgen = np.array([dis, ic, tepe], dtype=np.int32)
                cv2.polylines(katman, [ucgen], True, PEMBE, kalin, cv2.LINE_AA)

                dis_i = self._don(alin, isaret * 0.58 * s, -0.12 * s, cos_a, sin_a)
                ic_i = self._don(alin, isaret * 0.30 * s, -0.20 * s, cos_a, sin_a)
                tepe_i = self._don(alin, isaret * 0.52 * s, -0.58 * s, cos_a, sin_a)
                ic_ucgen = np.array([dis_i, ic_i, tepe_i], dtype=np.int32)
                cv2.fillPoly(katman, [ic_ucgen], (120, 40, 160), cv2.LINE_AA)

            b1 = self._don(burun, -0.11 * s, -0.04 * s, cos_a, sin_a)
            b2 = self._don(burun, 0.11 * s, -0.04 * s, cos_a, sin_a)
            b3 = self._don(burun, 0.0, 0.09 * s, cos_a, sin_a)
            b_ucgen = np.array([b1, b2, b3], dtype=np.int32)
            cv2.fillPoly(katman, [b_ucgen], PEMBE, cv2.LINE_AA)

            for isaret in (-1.0, 1.0):
                for idx_b, aci_b in enumerate([-0.14, 0.02, 0.18]):
                    dy0 = (idx_b - 1) * 0.07 * s
                    p0 = self._don(burun, isaret * 0.22 * s, dy0, cos_a, sin_a)
                    p1 = self._don(burun, isaret * 0.78 * s, dy0 + aci_b * s, cos_a, sin_a)
                    cv2.line(katman, p0, p1, PEMBE, max(2, kalin - 1), cv2.LINE_AA)

        elif maske_ad == "Şeytan":
            kalin = max(2, int(0.07 * s))
            hale_r1 = max(10, int(0.95 * s))
            hale_r2 = max(10, int(1.18 * s))
            cv2.ellipse(
                katman,
                (int(yuz_merkez[0]), int(yuz_merkez[1])),
                (hale_r1, hale_r2),
                aci_deg,
                0,
                360,
                KIRMIZI,
                max(2, int(0.055 * s)),
                cv2.LINE_AA,
            )

            for isaret in (-1.0, 1.0):
                dis_pts = []
                ic_pts = []
                for k in range(7):
                    u = k / 6.0
                    dx_dis = isaret * (0.48 * s + 0.32 * s * math.sin(u * math.pi * 0.75) - 0.12 * s * (u ** 2))
                    dy_dis = -0.05 * s - 0.82 * s * u
                    dx_ic = isaret * (0.28 * s + 0.22 * s * math.sin(u * math.pi * 0.65))
                    dy_ic = -0.10 * s - 0.82 * s * u
                    dis_pts.append(self._don(alin, dx_dis, dy_dis, cos_a, sin_a))
                    ic_pts.append(self._don(alin, dx_ic, dy_ic, cos_a, sin_a))

                poligon = np.array(dis_pts + ic_pts[::-1], dtype=np.int32)
                cv2.fillPoly(katman, [poligon], (30, 30, 180), cv2.LINE_AA)
                cv2.polylines(katman, [poligon], True, KIRMIZI, kalin, cv2.LINE_AA)

        elif maske_ad == "Uzaylı":
            kalin = max(2, int(0.06 * s))
            nabiz = 0.5 + 0.5 * math.sin(simdi * 9.0)
            for isaret in (-1.0, 1.0):
                p_alt = self._don(alin, isaret * 0.30 * s, -0.06 * s, cos_a, sin_a)
                p_orta = self._don(alin, isaret * 0.45 * s, -0.45 * s, cos_a, sin_a)
                p_uc = self._don(alin, isaret * 0.58 * s, -0.82 * s, cos_a, sin_a)
                pts_a = np.array([p_alt, p_orta, p_uc], dtype=np.int32)
                cv2.polylines(katman, [pts_a], False, YESIL, kalin, cv2.LINE_AA)

                top_r = max(5, int((0.12 + 0.06 * nabiz) * s))
                cv2.circle(katman, p_uc, top_r, YESIL, -1, cv2.LINE_AA)
                cv2.circle(katman, p_uc, max(2, top_r // 2), BEYAZ, -1, cv2.LINE_AA)

            for isaret, goz in ((-1.0, goz_sol), (1.0, goz_sag)):
                gx = int(round(goz[0] + isaret * (-0.08 * s) * cos_a))
                gy = int(round(goz[1] + isaret * (-0.08 * s) * sin_a))
                er1 = max(8, int(0.32 * s))
                er2 = max(6, int(0.22 * s))
                egim = aci_deg + isaret * 18.0
                cv2.ellipse(kare, (gx, gy), (er1, er2), egim, 0, 360, (15, 40, 15), -1, cv2.LINE_AA)
                cv2.ellipse(katman, (gx, gy), (er1, er2), egim, 0, 360, YESIL, kalin, cv2.LINE_AA)
                cv2.circle(
                    katman,
                    (gx - int(0.08 * s), gy - int(0.06 * s)),
                    max(2, int(0.045 * s)),
                    BEYAZ,
                    -1,
                    cv2.LINE_AA,
                )

        elif maske_ad == "Korsan":
            kalin = max(2, int(0.065 * s))
            ip_sol = self._don(goz_merkez, -0.95 * s, -0.35 * s, cos_a, sin_a)
            ip_sag = self._don(goz_merkez, 0.95 * s, 0.25 * s, cos_a, sin_a)
            cv2.line(kare, ip_sol, ip_sag, (20, 20, 25), kalin + 2, cv2.LINE_AA)
            cv2.line(katman, ip_sol, ip_sag, SARI, max(1, kalin - 2), cv2.LINE_AA)

            band_mx, band_my = self._don(goz_merkez, 0.35 * s, 0.0, cos_a, sin_a)
            band_r1 = max(10, int(0.28 * s))
            band_r2 = max(8, int(0.22 * s))
            cv2.ellipse(kare, (band_mx, band_my), (band_r1, band_r2), aci_deg + 12.0, 0, 360, (15, 15, 20), -1, cv2.LINE_AA)
            cv2.ellipse(katman, (band_mx, band_my), (band_r1, band_r2), aci_deg + 12.0, 0, 360, SARI, kalin, cv2.LINE_AA)

            s_sol = self._don(alin, -1.0 * s, -0.42 * s, cos_a, sin_a)
            s_sag = self._don(alin, 1.0 * s, -0.42 * s, cos_a, sin_a)
            s_tepe = self._don(alin, 0.0, -1.25 * s, cos_a, sin_a)
            s_pts = np.array([s_sol, s_sag, s_tepe], dtype=np.int32)
            cv2.fillPoly(kare, [s_pts], (18, 18, 24), cv2.LINE_AA)
            cv2.polylines(katman, [s_pts], True, SARI, kalin, cv2.LINE_AA)

            sp_kafatas = self._sprite_al("☠", 128)
            sk_x, sk_y = self._don(alin, 0.0, -0.72 * s, cos_a, sin_a)
            boy = max(24, int(0.55 * s))
            bindir_merkez(kare, sp_kafatas, sk_x, sk_y, boyut=boy, aci=-aci_deg, opak=1.0)

        elif maske_ad == "Ayıcık":
            kalin = max(2, int(0.065 * s))
            for isaret in (-1.0, 1.0):
                kx, ky = self._don(alin, isaret * 0.72 * s, -0.68 * s, cos_a, sin_a)
                kr_dis = max(12, int(0.34 * s))
                kr_ic = max(6, int(0.20 * s))
                cv2.circle(kare, (kx, ky), kr_dis, (24, 62, 108), -1, cv2.LINE_AA)
                cv2.circle(katman, (kx, ky), kr_dis, (30, 70, 125), kalin, cv2.LINE_AA)
                cv2.circle(kare, (kx, ky), kr_ic, (180, 160, 240), -1, cv2.LINE_AA)
                cv2.circle(katman, (kx, ky), kr_ic, PEMBE, max(1, kalin - 1), cv2.LINE_AA)

            bx, by = int(burun[0]), int(burun[1])
            bn_r1 = max(8, int(0.18 * s))
            bn_r2 = max(6, int(0.13 * s))
            cv2.ellipse(kare, (bx, by), (bn_r1, bn_r2), aci_deg, 0, 360, (25, 25, 30), -1, cv2.LINE_AA)
            cv2.ellipse(katman, (bx, by), (bn_r1, bn_r2), aci_deg, 0, 360, (80, 160, 255), kalin, cv2.LINE_AA)
            parlak_x, parlak_y = self._don(burun, -0.04 * s, -0.04 * s, cos_a, sin_a)
            cv2.circle(katman, (parlak_x, parlak_y), max(2, int(0.04 * s)), BEYAZ, -1, cv2.LINE_AA)

        elif maske_ad == "Kalp Göz":
            nabiz_kalp = 1.0 + 0.10 * math.sin(simdi * 8.5)
            sp_kalp = self._sprite_al("❤️", 160)
            boy_kalp = max(24, int(0.68 * s * nabiz_kalp))
            for goz in (goz_sol, goz_sag):
                gx, gy = int(goz[0]), int(goz[1])
                bindir_merkez(kare, sp_kalp, gx, gy, boyut=boy_kalp, aci=-aci_deg, opak=1.0)
                cv2.circle(katman, (gx, gy), max(4, int(0.22 * s * nabiz_kalp)), PEMBE, 2, cv2.LINE_AA)

    def _kalp_ekle(self, x: float, y: float, s: float) -> None:
        if len(self.kalpler) >= 36:
            return
        vx = float(self.rng.uniform(-50.0, 50.0))
        vy = float(self.rng.uniform(-170.0, -95.0))
        boy = max(20, min(68, int(0.38 * s)))
        self.kalpler.append(_Kalp(x=x, y=y, vx=vx, vy=vy, yas=0.0, omur=0.95, boy=boy))

    def _kalpleri_guncelle_ve_ciz(self, kare: np.ndarray, dt: float) -> None:
        if not self.kalpler:
            return
        sp = self._sprite_al("❤️", 96)
        kalan: List[_Kalp] = []
        for k in self.kalpler:
            k.yas += dt
            if k.yas >= k.omur:
                continue
            k.x += k.vx * dt + math.sin(k.yas * 8.0) * 20.0 * dt
            k.y += k.vy * dt
            oran = 1.0 - (k.yas / k.omur)
            opak = max(0.0, min(1.0, oran * 1.2))
            boy = max(12, int(k.boy * (0.7 + 0.3 * math.sin(oran * math.pi))))
            bindir_merkez(kare, sp, int(k.x), int(k.y), boyut=boy, aci=0.0, opak=opak)
            kalan.append(k)
        self.kalpler = kalan

    def isle(self, kare: np.ndarray, algi: ck.Algi, simdi: float) -> np.ndarray:
        if self.onceki_t is None:
            dt = 0.016
        else:
            dt = min(max(float(simdi - self.onceki_t), 0.0), 0.1)
        self.onceki_t = float(simdi)

        if self.son_oto_gecis is None:
            self.son_oto_gecis = float(simdi)

        yuzler_ham = algi.yuzler or []
        blend_ham = algi.blend or []

        ikililer: List[Tuple[float, Any, Dict[str, float]]] = []
        for i, yuz in enumerate(yuzler_ham[:4]):
            try:
                bx = float(yuz[1].x)
            except Exception:
                bx = 0.5
            bl = blend_ham[i] if i < len(blend_ham) and isinstance(blend_ham[i], dict) else {}
            ikililer.append((bx, yuz, bl))
        ikililer.sort(key=lambda item: item[0])

        n_yuz = len(ikililer)
        n_maske = len(self.MASKELER)

        if n_yuz == 0:
            self.takipler.clear()
            self.maskeler = []
            self.parcacik.guncelle(dt)
            self._kalpleri_guncelle_ve_ciz(kare, dt)
            self._ciz_cekim_ekrani(kare, simdi)
            return kare

        while len(self.takipler) < n_yuz:
            yeni_i = len(self.takipler)
            self.takipler.append(_YuzTakip(yeni_i, self.tur, n_maske, simdi))
        if len(self.takipler) > n_yuz:
            self.takipler = self.takipler[:n_yuz]

        if simdi - self.son_oto_gecis >= 10.0:
            self._tum_maskeleri_ilerlet(simdi)

        katman = self._katman
        katman.fill(0)

        aktif_maskeler: List[str] = []
        foto_uyari_metni: Optional[str] = None

        for idx, (_, lm, bl) in enumerate(ikililer):
            t = self.takipler[idx]
            t.guncelle_konum(lm, dt=dt)

            jaw_open = float(bl.get("jawOpen", 0.0))
            brow_up = float(bl.get("browInnerUp", 0.0))
            blink_l = float(bl.get("eyeBlinkLeft", 0.0))
            blink_r = float(bl.get("eyeBlinkRight", 0.0))

            if blink_l > 0.6 and blink_r > 0.6:
                t.goz_kapali_sure += dt
                if t.goz_kapali_sure >= 0.5 and (simdi - t.son_kirp_degisim) > 0.8:
                    t.maske_degistir((t.maske_idx + 1) % n_maske, simdi)
                    t.son_kirp_degisim = simdi
                    t.goz_kapali_sure = 0.0
                    self.ses.cal("pop", 0.75)
            else:
                t.goz_kapali_sure = 0.0

            if brow_up > 0.5 and (simdi - t.son_ding) >= 0.6:
                t.kas_t0 = simdi
                t.son_ding = simdi
                self.ses.cal("ding", 0.65)

            kas_carpan = 1.0
            kas_gecen = simdi - t.kas_t0
            if 0.0 <= kas_gecen < 0.2:
                kas_carpan = 1.0 + 0.2 * math.sin((kas_gecen / 0.2) * math.pi)

            maske_ad = self.MASKELER[t.maske_idx]
            aktif_maskeler.append(maske_ad)

            ayni_maske_sure = simdi - t.maske_takilma_t0
            if ayni_maske_sure >= 6.0 and not t.foto_tetiklendi:
                faz = ayni_maske_sure - 6.0
                if faz < 2.0:
                    sayac = max(1, 3 - int(faz * 1.5))
                    foto_uyari_metni = f"Poz ver! 📸  {sayac}"
                else:
                    self.flas_t0 = simdi
                    t.foto_tetiklendi = True
                    self.ses.cal("basari", 0.85)

            if jaw_open > 0.45:
                ax, ay = t.agiz
                if maske_ad == "Şeytan":
                    self.parcacik.yay(ax, ay, 4, renk=(20, 110, 255), hiz=4.5)
                    self.parcacik.yay(ax, ay, 2, renk=KIRMIZI, hiz=3.5)
                elif maske_ad == "Kral":
                    self.parcacik.yay(ax, ay, 5, renk=SARI, hiz=4.2)
                elif maske_ad == "Korsan":
                    self.parcacik.yay(ax, ay, 4, renk=CAMGOBEGI, hiz=4.0)
                elif maske_ad == "Ayıcık":
                    self.parcacik.yay(ax, ay, 4, renk=(40, 180, 255), hiz=3.2)
                    self.parcacik.yay(ax, ay, 2, renk=(20, 220, 255), hiz=2.8)
                elif maske_ad == "Kalp Göz":
                    for _ in range(2):
                        self._kalp_ekle(ax + float(self.rng.uniform(-16, 16)), ay, t.s)
                else:
                    if len(self.kalpler) < 36:
                        self._kalp_ekle(ax, ay, t.s)

            gecen = simdi - t.gecis_t0
            if t.eski_idx is not None and 0.0 <= gecen < 0.2:
                eski_oran = max(0.05, 1.0 - (gecen / 0.2))
                eski_ad = self.MASKELER[t.eski_idx]
                self._ciz_maske(kare, katman, t, eski_ad, eski_oran * kas_carpan, simdi)

            if 0.0 <= gecen < 0.25:
                u = gecen / 0.25
                yeni_oran = math.sin(u * math.pi * 0.5) + 0.18 * math.sin(u * math.pi)
            else:
                yeni_oran = 1.0
                t.eski_idx = None

            self._ciz_maske(kare, katman, t, maske_ad, yeni_oran * kas_carpan, simdi)

        self.maskeler = aktif_maskeler

        parilti(kare, katman, guc=1.8, sigma=3.0)
        self.parcacik.guncelle(dt)
        self.parcacik.ciz(kare)
        self._kalpleri_guncelle_ve_ciz(kare, dt)

        flas_gecen = simdi - self.flas_t0
        if 0.0 <= flas_gecen < 0.15:
            flas_oran = (1.0 - (flas_gecen / 0.15)) * 0.35
            cv2.addWeighted(
                kare,
                1.0 - flas_oran,
                np.full_like(kare, 255),
                flas_oran,
                0,
                dst=kare,
            )

        panel(kare, G // 2 - 340, 10, G // 2 + 340, 78, renk=(18, 18, 28), opak=0.72, kenar=CAMGOBEGI)
        yazi_koy(kare, "AR MASKELER", G // 2, 14, 44, renk=SARI, hiza="orta")
        yazi_koy(
            kare,
            "Ağzını aç · Kaşını kaldır · Göz kırp: maske değiştir",
            G // 2,
            54,
            22,
            renk=BEYAZ,
            hiza="orta",
        )

        if foto_uyari_metni:
            panel(kare, G // 2 - 160, 92, G // 2 + 160, 142, renk=(20, 20, 32), opak=0.82, kenar=PEMBE)
            nabiz_foto = 1.0 + 0.06 * math.sin(simdi * 12.0)
            yazi_koy(
                kare,
                foto_uyari_metni,
                G // 2,
                100,
                34,
                renk=SARI,
                hiza="orta",
                olcek=nabiz_foto,
            )

        etiket = " · ".join(self.maskeler)
        kutu_g = max(260, min(800, 140 + len(etiket) * 14))
        panel(kare, 24, Y - 76, 24 + kutu_g, Y - 20, renk=(18, 18, 28), opak=0.72, kenar=PEMBE)
        yazi_koy(kare, f"Aktif: {etiket}", 40, Y - 64, 26, renk=BEYAZ, hiza="sol")

        return kare

    def _ciz_cekim_ekrani(self, kare: np.ndarray, simdi: float) -> None:
        karart = bulanik_karanlik(kare, 0.55)
        np.copyto(kare, karart)

        kose_emojiler = [
            ("👑", 120, 120, 1.0),
            ("😎", G - 120, 120, -1.0),
            ("🐱", 120, Y - 120, -1.0),
            ("👽", G - 120, Y - 120, 1.0),
            ("☠", 280, 90, 1.0),
            ("🐻", G - 280, 90, -1.0),
            ("❤️", 280, Y - 90, -1.0),
            ("😈", G - 280, Y - 90, 1.0),
        ]
        for emo, kx, ky, yon in kose_emojiler:
            sp = self._sprite_al(emo, 128)
            aci = (simdi * 32.0 * yon) % 360.0
            boy = int(88 + 10 * math.sin(simdi * 2.5 + kx * 0.01))
            bindir_merkez(kare, sp, kx, ky, boyut=boy, aci=aci, opak=0.88)

        baslik(kare, self.AD, renk=SARI)

        panel(kare, G // 2 - 470, Y // 2 - 95, G // 2 + 470, Y // 2 + 95, renk=(18, 18, 28), opak=0.75, kenar=CAMGOBEGI)
        nabiz = 1.0 + 0.05 * math.sin(simdi * 4.2)
        yazi_koy(
            kare,
            "Kameraya bak, maskeni tak!",
            G // 2,
            Y // 2 - 62,
            52,
            renk=SARI,
            hiza="orta",
            olcek=nabiz,
        )
        yazi_koy(
            kare,
            "Ağzını aç · Kaşını kaldır · Göz kırp: maske değiştir",
            G // 2,
            Y // 2 + 22,
            28,
            renk=BEYAZ,
            hiza="orta",
        )
