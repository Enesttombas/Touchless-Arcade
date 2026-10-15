from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

import cekirdek as ck
import sus_ciz as sc
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


@dataclass(eq=False)
class _ElIz:
    """Bir elin yatay hamlesi: yön değişince yeni hamle başlar; bir sallama yalnız bir kez sayılır."""
    x: float
    y: float
    t: float
    x0: float
    t0: float
    yon: int = 0
    sakin: float = 0.0
    kilit: bool = False


# Yüz ovali (MediaPipe FACE_OVAL): yüz tonu için
OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176,
        149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]


@dataclass
class _BalDamla:
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

        self.iris_sol: Tuple[float, float] = self.goz_sol
        self.iris_sag: Tuple[float, float] = self.goz_sag
        self.jaw: float = 0.0
        self.son_gorulme: float = simdi
        self.egim_hazir: bool = False  # baş önce düz konuma gelmeli; sonra yana eğmek maske değiştirir
        self.egim_sure: float = 0.0

        self.maske_idx: int = (idx + tur) % maske_sayisi
        self.eski_idx: Optional[int] = None
        self.gecis_t0: float = simdi  # yeni gelen yüzde maske büyüyerek girer (gözlük yukarıdan düşer)

        self.kas_t0: float = -10.0
        self.kas_taban: Optional[float] = None  # kişinin doğal kaş seviyesi (yavaş öğrenilir)
        self.kas_sure: float = 0.0
        self.kas_hazir: bool = True
        self.oval: Optional[np.ndarray] = None
        self.goz_kapali_sure: float = 0.0
        self.son_kirp_degisim: float = -10.0

        self.son_maske_degisim: float = simdi
        self.foto_baslangic: Optional[float] = None
        self.foto_tamamlandi: bool = False
        self.flas_t0: float = -10.0

    def guncelle_konum(self, lm: Any) -> None:
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
        try:
            ix1, iy1 = px(lm, 468)
            ix2, iy2 = px(lm, 473)
        except Exception:
            ix1, iy1 = gx1 + (gx2 - gx1) * 0.12, gy1 + (gy2 - gy1) * 0.12
            ix2, iy2 = gx2 - (gx2 - gx1) * 0.12, gy2 - (gy2 - gy1) * 0.12

        try:
            self.oval = np.array([px(lm, i) for i in OVAL], np.int32)
        except Exception:
            self.oval = None

        if gx1 > gx2:
            gx1, gy1, gx2, gy2 = gx2, gy2, gx1, gy1
            ix1, iy1, ix2, iy2 = ix2, iy2, ix1, iy1

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
            self.iris_sol = (ix1, iy1)
            self.iris_sag = (ix2, iy2)
            self.s = s_yeni
            self.aci = aci_yeni
            self.hazir = True
            return

        hiz_px = math.hypot(bx - self.burun[0], by - self.burun[1])
        oran = min(max((hiz_px - 2.0) / 24.0, 0.0), 1.0)
        a = 0.25 + 0.50 * oran
        b = 1.0 - a

        self.alin = (b * self.alin[0] + a * ax, b * self.alin[1] + a * ay)
        self.burun = (b * self.burun[0] + a * bx, b * self.burun[1] + a * by)
        self.cene = (b * self.cene[0] + a * cx, b * self.cene[1] + a * cy)
        self.goz_sol = (b * self.goz_sol[0] + a * gx1, b * self.goz_sol[1] + a * gy1)
        self.goz_sag = (b * self.goz_sag[0] + a * gx2, b * self.goz_sag[1] + a * gy2)
        self.agiz = (b * self.agiz[0] + a * agx, b * self.agiz[1] + a * agy)
        self.iris_sol = (b * self.iris_sol[0] + a * ix1, b * self.iris_sol[1] + a * iy1)
        self.iris_sag = (b * self.iris_sag[0] + a * ix2, b * self.iris_sag[1] + a * iy2)
        self.s = b * self.s + a * s_yeni
        fark = (aci_yeni - self.aci + math.pi) % (2 * math.pi) - math.pi
        self.aci = self.aci + a * fark

    def maske_degistir(self, yeni_idx: int, simdi: float) -> None:
        if yeni_idx != self.maske_idx:
            self.eski_idx = self.maske_idx
            self.maske_idx = yeni_idx
            self.gecis_t0 = simdi
            self.son_maske_degisim = simdi
            self.foto_baslangic = None
            self.foto_tamamlandi = False


class Prototip:
    AD = "AR Maskeler"
    ACIKLAMA = "Başını yana yatır: maskeni değiştir!"
    ESKI_TETIKLER = False
    AVUC_TETIK = False  # avuç aç-kapa canlıda güvenilmez çıktı (Enes 2026-10-12)
    KAS_TETIK = False  # kaş yalnız efekt; şaşırınca kaş kalkar, yanlış değişim yapar
    KAFA_TETIK = True  # Enes 2026-10-12 "akıcı ve kolay": başı sağa yatır sonraki, sola önceki (önizlemeli)
    # Enes 2026-10-13: kalabalıkta maske "ışık hızıyla" değişiyordu, önizleme topları sağa sola geziyordu
    KAFA_ESIK = 0.36  # rad (~21°); gülerken eğim ~10-15°
    KAFA_SN = 0.45  # eşiği bu kadar tutmak gerekir
    KAFA_ARA = 1.0  # aynı yüzde iki baş değişimi arası en az
    ONIZLEME_ORAN = 0.75  # önizleme topu ancak eğim eşiğin %75'ine gelince çıkar
    # yuz2: tam karede 2'den az yüz varsa kare parçalarında da ara (uzaktaki/küçük yüzler)
    IHTIYAC = {"yuz", "blend", "el", "yuz2"}
    TUTMA_SN = 0.35
    SIRA = 17

    # Popüler olanlar başta; eski 8 maske korunur
    MASKELER = ["Köpek", "Çiçek Taç", "Dev Gözler", "Havalı", "Tavşan", "Gökkuşağı", "Kalp Göz", "Kral",
                "Kedi", "Şeytan", "Uzaylı", "Korsan", "Ayıcık", "Kelebek"]

    def __init__(self, ses: Any):
        self.ses = ses
        self.maskeler: List[str] = []
        self.takipler: List[_YuzTakip] = []
        self.tur: int = 0
        self.son_oto_gecis: Optional[float] = None
        self.onceki_t: Optional[float] = None

        self.parcacik = Parcaciklar(200)
        self.kalpler: List[_Kalp] = []
        self.ballar: List[_BalDamla] = []
        self.rng = np.random.RandomState(17)

        self._ikonlar: List[np.ndarray] = []
        self._karusel_konum: float = 0.0
        self._avuc_t: float = -10.0
        self._avuc_durum: Dict[Any, Dict[str, float]] = {}
        self._avuc_ipucu: List[Tuple[float, float]] = []
        self._el_izler: List[_ElIz] = []
        self._dugme_sure: Dict[int, float] = {-1: 0.0, 1: 0.0}
        self._dugme_kilit: Dict[int, bool] = {-1: False, 1: False}
        self._dugme_t: Optional[float] = None
        self._son_kalp: float = -10.0
        self._katman = np.zeros((Y, G, 3), dtype=np.uint8)
        self._ok_merkez = {-1: np.array([112., Y * .42]), 1: np.array([G - 112., Y * .42])}
        self._el_sahipleri = []
        self.hedef_yuz = None

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

    GOKKUSAGI = [(60, 60, 240), (40, 150, 255), (60, 230, 255), (90, 210, 90), (240, 170, 50), (180, 80, 70), (200, 90, 180)]
    @staticmethod
    def _bukul(kare: np.ndarray, cx: float, cy: float, r: float, guc: float) -> None:
        """Yerel büyüteç: r yarıçap içinde merkez 1/(1-guc) kat büyür, kenarda sürekli biter."""
        # numpy float64 merkez (filtreli noktalar) haritayı float64'e yükseltip cv2.remap'i çökertiyordu
        r, cx, cy, guc = float(r), float(cx), float(cy), float(guc)
        if r < 6 or guc <= 0.01:
            return
        x0, y0 = max(0, int(cx - r)), max(0, int(cy - r))
        x1, y1 = min(G, int(cx + r) + 1), min(Y, int(cy + r) + 1)
        if x1 - x0 < 4 or y1 - y0 < 4:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xx - cx, yy - cy
        d2 = np.minimum((dx * dx + dy * dy) / (r * r), 1.0)
        f = 1.0 - guc * (1.0 - d2) ** 2
        harita_x = (cx + dx * f).astype(np.float32)
        harita_y = (cy + dy * f).astype(np.float32)
        kare[y0:y1, x0:x1] = cv2.remap(kare, harita_x, harita_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    def _gokkusagi(self, kare: np.ndarray, katman: np.ndarray, t: "_YuzTakip", s: float, guc: float, simdi: float) -> None:
        """Ağızdan aşağı dalgalanarak akan gökkuşağı (Snapchat klasiği)."""
        ax, ay = t.agiz
        boy = (Y + 40 - ay) * (0.35 + 0.65 * guc)
        n = 24
        genis = 0.55 * s
        bant = genis / len(self.GOKKUSAGI)
        merkez = []
        for k in range(n + 1):
            u = k / n
            yk = ay + u * boy
            xk = ax + math.sin(simdi * 7.0 - u * 6.0) * (0.08 * s + u * 0.45 * s)
            merkez.append((xk, yk, 0.55 + 0.9 * u))
        for j, renk in enumerate(self.GOKKUSAGI):
            ofs = (j - (len(self.GOKKUSAGI) - 1) / 2) * bant
            pts = np.array([(int(x + ofs * g), int(y)) for x, y, g in merkez], np.int32)
            kal = max(2, int(bant * 1.25 * merkez[-1][2]))
            cv2.polylines(kare, [pts[: n // 2 + 1]], False, renk, max(2, int(bant * 1.1)), cv2.LINE_AA)
            cv2.polylines(kare, [pts[n // 2:]], False, renk, kal, cv2.LINE_AA)
            cv2.polylines(katman, [pts], False, tuple(int(c * 0.35) for c in renk), max(2, int(bant)), cv2.LINE_AA)
        if self.rng.rand() < 0.5:
            x, y, _ = merkez[-4]
            self.parcacik.yay(x, min(y, Y - 10), 2, renk=self.GOKKUSAGI[self.rng.randint(7)], hiz=3.0)

    @staticmethod
    def _yuz_boya(kare: np.ndarray, oval: Optional[np.ndarray], renk: Tuple[int, int, int], guc: float) -> None:
        """Yüz ovalini yumuşak kenarla renge boyar; parlaklık (gölge, ışık) korunur."""
        if oval is None or guc <= 0.0:
            return
        x, y, w, h = cv2.boundingRect(oval)
        if w < 24 or h < 24:
            return
        pay = int(0.12 * w)
        x0, y0, x1, y1 = max(0, x - pay), max(0, y - pay), min(G, x + w + pay), min(Y, y + h + pay)
        if x1 - x0 < 8 or y1 - y0 < 8:
            return
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        cv2.fillPoly(m, [oval - np.array([x0, y0], np.int32)], 255, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), max(2.0, 0.05 * w))
        bolge = kare[y0:y1, x0:x1]
        gri = cv2.cvtColor(bolge, cv2.COLOR_BGR2GRAY).astype(np.float32) * (1.25 / 255.0)
        boyali = np.clip(gri[..., None] * np.array(renk, np.float32), 0, 255)
        a = (m.astype(np.float32) * (guc / 255.0))[..., None]
        kare[y0:y1, x0:x1] = (bolge * (1.0 - a) + boyali * a).astype(np.uint8)

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
        goz_merkez = ((t.goz_sol[0] + t.goz_sag[0]) * 0.5, (t.goz_sol[1] + t.goz_sag[1]) * 0.5)
        yuz_merkez = ((alin[0] + t.cene[0]) * 0.5, (alin[1] + t.cene[1]) * 0.5)

        if maske_ad == "Kral":
            sp = sc.tac(256)
            tx, ty = self._don(alin, 0.0, -0.9 * s, cos_a, sin_a)
            boy = max(24, min(600, int(round(1.6 * s))))
            bindir_merkez(kare, sp, tx, ty, boyut=boy, aci=-aci_deg, opak=1.0)
            for dx_k, dy_k in [(-0.55 * s, -0.95 * s), (0.0, -1.18 * s), (0.55 * s, -0.95 * s)]:
                px_k, py_k = self._don(alin, dx_k, dy_k, cos_a, sin_a)
                cv2.circle(katman, (px_k, py_k), max(3, int(0.06 * s)), SARI, -1, cv2.LINE_AA)

        elif maske_ad == "Havalı":
            # "Deal with it" piksel gözlüğü: maske gelince yukarıdan düşüp gözlere oturur
            gecen_h = simdi - t.gecis_t0
            u = min(1.0, max(0.0, gecen_h / 0.7))
            dus = (1.0 - u) ** 3
            gx, gy = goz_merkez
            gy_d = gy - dus * (gy + 0.6 * t.s)
            bindir_merkez(kare, sc.pikselli_gozluk(16), int(gx), int(gy_d), boyut=max(20, int(1.75 * t.s)), aci=-aci_deg)

        elif maske_ad == "Kedi":
            for isaret in (-1.0, 1.0):
                oyna = 4.0 * math.sin(simdi * 2.3 + isaret)
                kx, ky = self._don(alin, isaret * 0.56 * s, -0.48 * s, cos_a, sin_a)
                bindir_merkez(kare, sc.kedi_kulak(256, isaret > 0), kx, ky, boyut=max(16, int(0.98 * s)),
                              aci=-aci_deg - isaret * (6.0 + oyna))
            for isaret in (-1.0, 1.0):  # bıyık: koyu kontur + beyaz tel
                for dy0, egim in ((-0.02, -0.12), (0.06, 0.0), (0.14, 0.12)):
                    p0 = self._don(burun, isaret * 0.22 * s, (0.10 + dy0) * s, cos_a, sin_a)
                    p1 = self._don(burun, isaret * 0.90 * s, (0.10 + dy0 + egim) * s, cos_a, sin_a)
                    cv2.line(kare, p0, p1, (40, 35, 45), max(2, int(0.032 * s)), cv2.LINE_AA)
                    cv2.line(kare, p0, p1, (245, 245, 250), max(1, int(0.014 * s)), cv2.LINE_AA)
            bx, by = self._don(burun, 0.0, 0.07 * s, cos_a, sin_a)
            bindir_merkez(kare, sc.kedi_burun(128), bx, by, boyut=max(10, int(0.42 * s)), aci=-aci_deg)

        elif maske_ad == "Şeytan":
            self._yuz_boya(kare, t.oval, (90, 90, 255), 0.22 * min(1.0, olcek_carpan))
            nabiz = 0.5 + 0.5 * math.sin(simdi * 3.0)
            cv2.ellipse(katman, (int(yuz_merkez[0]), int(yuz_merkez[1])), (max(10, int(1.0 * s)), max(10, int(1.22 * s))),
                        aci_deg, 0, 360, (20, 20, int(120 + 80 * nabiz)), max(2, int(0.03 * s)), cv2.LINE_AA)
            for isaret in (-1.0, 1.0):
                hx, hy = self._don(alin, isaret * 0.42 * s, -0.42 * s, cos_a, sin_a)
                bindir_merkez(kare, sc.seytan_boynuz(256, isaret > 0), hx, hy, boyut=max(16, int(0.92 * s)),
                              aci=-aci_deg - isaret * 4.0)
            for iris in (t.iris_sol, t.iris_sag):  # kor gibi yanan gözler
                cv2.circle(katman, (int(iris[0]), int(iris[1])), max(2, int(0.07 * s)), (30, 40, 255), -1, cv2.LINE_AA)

        elif maske_ad == "Uzaylı":
            self._yuz_boya(kare, t.oval, (110, 255, 120), 0.45 * min(1.0, olcek_carpan))
            nabiz = 0.5 + 0.5 * math.sin(simdi * 6.0)
            for isaret in (-1.0, 1.0):
                pts = [self._don(alin, isaret * (0.20 + 0.14 * u + 0.16 * u * u) * s,
                                 (-0.05 - 0.80 * u + 0.03 * math.sin(simdi * 3.0 + u * 4.0 + isaret)) * s, cos_a, sin_a)
                       for u in np.linspace(0.0, 1.0, 9)]
                cizgi = np.array(pts, np.int32)
                cv2.polylines(kare, [cizgi], False, (25, 70, 30), max(3, int(0.06 * s)), cv2.LINE_AA)
                cv2.polylines(kare, [cizgi], False, (80, 215, 100), max(2, int(0.03 * s)), cv2.LINE_AA)
                ux, uy = pts[-1]
                cv2.circle(katman, (ux, uy), max(3, int((0.10 + 0.05 * nabiz) * s)), (60, 255, 110), -1, cv2.LINE_AA)
                bindir_merkez(kare, sc.kure(96, (70, 230, 100)), ux, uy, boyut=max(8, int((0.24 + 0.03 * nabiz) * s)))
            for isaret, goz in ((-1.0, t.goz_sol), (1.0, t.goz_sag)):
                gx, gy = self._don(goz, isaret * 0.06 * s, -0.02 * s, cos_a, sin_a)
                bindir_merkez(kare, sc.uzayli_goz(160), gx, gy, boyut=max(12, int(0.80 * s)),
                              aci=-(aci_deg + isaret * 18.0))

        elif maske_ad == "Korsan":
            p_sol = self._don(goz_merkez, -1.0 * s, -0.42 * s, cos_a, sin_a)
            p_sag = self._don(goz_merkez, 1.0 * s, 0.05 * s, cos_a, sin_a)
            cv2.line(kare, p_sol, p_sag, (22, 20, 26), max(3, int(0.055 * s)), cv2.LINE_AA)
            cv2.line(kare, p_sol, p_sag, (70, 68, 78), max(1, int(0.015 * s)), cv2.LINE_AA)
            bindir_merkez(kare, sc.goz_bandi(128), int(t.goz_sag[0] - 0.08 * s * cos_a), int(t.goz_sag[1] - 0.08 * s * sin_a),
                          boyut=max(12, int(0.62 * s)), aci=-aci_deg)
            hx, hy = self._don(alin, 0.0, -0.52 * s, cos_a, sin_a)
            bindir_merkez(kare, sc.korsan_sapka(256), hx, hy, boyut=max(24, int(2.1 * s)), aci=-aci_deg)
            sx, sy = self._don(alin, 0.0, -0.72 * s, cos_a, sin_a)
            bindir_merkez(kare, sc.kafatasi(128), sx, sy, boyut=max(16, int(0.40 * s)), aci=-aci_deg)

        elif maske_ad == "Ayıcık":
            for isaret in (-1.0, 1.0):
                kx, ky = self._don(alin, isaret * 0.66 * s, -0.42 * s, cos_a, sin_a)
                bindir_merkez(kare, sc.ayi_kulak(128), kx, ky, boyut=max(12, int(0.66 * s)), aci=-aci_deg)
                yx, yy = self._don(goz_merkez, isaret * 0.62 * s, 0.50 * s, cos_a, sin_a)  # allık
                cv2.circle(katman, (yx, yy), max(4, int(0.13 * s)), (70, 50, 130), -1, cv2.LINE_AA)
            bx, by = self._don(burun, 0.0, 0.08 * s, cos_a, sin_a)
            bindir_merkez(kare, sc.ayi_agiz(192), bx, by, boyut=max(12, int(0.72 * s)), aci=-aci_deg)

        elif maske_ad == "Köpek":
            sall = 7.0 * math.sin(simdi * 3.1)
            for isaret in (-1.0, 1.0):
                kx, ky = self._don(alin, isaret * 0.80 * s, -0.05 * s, cos_a, sin_a)
                bindir_merkez(kare, sc.kopek_kulak(256), kx, ky, boyut=max(16, int(1.15 * s)),
                              aci=-aci_deg - isaret * (24.0 + sall))
            bx, by = self._don(burun, 0.0, -0.06 * s, cos_a, sin_a)
            bindir_merkez(kare, sc.kopek_burun(128), bx, by, boyut=max(10, int(0.48 * s)), aci=-aci_deg)
            if t.jaw > 0.2:
                uz = s * (0.35 + 0.55 * min(1.0, (t.jaw - 0.2) / 0.4))
                dx_, dy_ = self._don(t.agiz, 0.0, uz * 0.42, cos_a, sin_a)
                bindir_merkez(kare, sc.dil(256), dx_, dy_, boyut=max(10, int(uz)),
                              aci=-aci_deg + 4.0 * math.sin(simdi * 7.0))

        elif maske_ad == "Tavşan":
            for isaret in (-1.0, 1.0):
                sall = 5.0 * math.sin(simdi * 2.4 + isaret)
                kx, ky = self._don(alin, isaret * 0.36 * s, -0.95 * s, cos_a, sin_a)
                bindir_merkez(kare, sc.tavsan_kulak(256), kx, ky, boyut=max(16, int(1.35 * s)),
                              aci=-aci_deg - isaret * (12.0 + sall))
            bx, by = self._don(burun, 0.0, -0.02 * s, cos_a, sin_a)
            bindir_merkez(kare, sc.kalp(160, (150, 110, 240)), bx, by, boyut=max(8, int(0.22 * s)), aci=-aci_deg)
            for isaret in (-1.0, 1.0):
                for dy0, egim in ((-0.03, -0.10), (0.04, 0.0), (0.11, 0.10)):
                    p0 = self._don(burun, isaret * 0.16 * s, dy0 * s, cos_a, sin_a)
                    p1 = self._don(burun, isaret * 0.70 * s, (dy0 + egim) * s, cos_a, sin_a)
                    cv2.line(kare, p0, p1, (235, 235, 240), max(1, int(0.02 * s)), cv2.LINE_AA)
            tx, ty = self._don(t.agiz, 0.0, 0.02 * s + t.jaw * 0.05 * s, cos_a, sin_a)
            bindir_merkez(kare, sc.tavsan_dis(96), tx, ty, boyut=max(8, int(0.26 * s)), aci=-aci_deg)

        elif maske_ad == "Çiçek Taç":
            renkler = [(190, 120, 250), (60, 200, 255), (60, 80, 245), (240, 240, 245), (230, 140, 200)]
            noktalar = []
            for k in range(-3, 4):
                u = k / 3.0
                lx, ly = u * 0.95 * s, -0.42 * s + 0.24 * s * u * u + 0.02 * s * math.sin(simdi * 3 + k)
                noktalar.append((k, lx, ly))
            for k, lx, ly in noktalar[:-1]:
                yx, yy = self._don(alin, lx + 0.16 * s, ly + 0.05 * s, cos_a, sin_a)
                bindir_merkez(kare, sc.yaprak(110), yx, yy, boyut=max(8, int(0.30 * s)), aci=-aci_deg - 20 + k * 15)
            for k, lx, ly in noktalar:
                cx_c, cy_c = self._don(alin, lx, ly, cos_a, sin_a)
                yr = renkler[(k + 3) % len(renkler)]
                orta = (40, 120, 230) if yr == (60, 200, 255) else (40, 200, 255)
                boyc = (0.56 if k == 0 else 0.44) * s
                bindir_merkez(kare, sc.cicek(160, yr, orta), cx_c, cy_c, boyut=max(8, int(boyc)),
                              aci=-aci_deg + k * 12 + 6 * math.sin(simdi * 1.5 + k))

        elif maske_ad == "Dev Gözler":
            for iris in (t.iris_sol, t.iris_sag):
                self._bukul(kare, iris[0], iris[1], 0.5 * s, 0.6 * min(1.0, olcek_carpan))
            if t.jaw > 0.35:
                self._bukul(kare, t.agiz[0], t.agiz[1], 0.55 * s, 0.35 * min(1.0, (t.jaw - 0.35) / 0.3))

        elif maske_ad == "Gökkuşağı":
            for k in range(4):
                a_k = simdi * 1.4 + k * math.pi / 2
                px_k, py_k = self._don(yuz_merkez, math.cos(a_k) * 1.05 * s, math.sin(a_k) * 1.2 * s, cos_a, sin_a)
                parla = 0.6 + 0.4 * math.sin(simdi * 6 + k * 2)
                bindir_merkez(kare, sc.parilti(64), px_k, py_k, boyut=max(8, int(0.32 * s * parla)), aci=simdi * 40)
            if t.jaw > 0.3:
                self._gokkusagi(kare, katman, t, s, min(1.0, (t.jaw - 0.3) / 0.35), simdi)
            else:
                bx_, by_ = self._don(alin, 0.0, -0.55 * s, cos_a, sin_a)
                for j, renk_g in enumerate(self.GOKKUSAGI[::2]):
                    cv2.ellipse(katman, (bx_, by_), (int((0.75 - 0.07 * j) * s), int((0.48 - 0.07 * j) * s)), aci_deg,
                                200, 340, renk_g, max(2, int(0.045 * s)), cv2.LINE_AA)

        elif maske_ad == "Kelebek":
            renkler_k = [(30, 140, 255), (220, 120, 60), (170, 80, 230)]
            for k in range(3):
                a_k = simdi * 1.1 + k * 2 * math.pi / 3
                lx, ly = math.cos(a_k) * 1.15 * s, math.sin(a_k) * 0.55 * s - 0.75 * s
                kx, ky = self._don(yuz_merkez, lx, ly, cos_a, sin_a)
                kareler = sc.kelebek_kareleri(120, renkler_k[k])
                faz = int(simdi * 16 + k * 2) % len(kareler)
                bindir_merkez(kare, kareler[faz], kx, ky, boyut=max(10, int(0.68 * s)),
                              aci=-aci_deg + 20 * math.cos(a_k))
            kx, ky = self._don(burun, 0.0, -0.05 * s, cos_a, sin_a)
            kareler = sc.kelebek_kareleri(120, (60, 80, 245))
            bindir_merkez(kare, kareler[int(simdi * 5) % len(kareler)], kx, ky, boyut=max(10, int(0.55 * s)), aci=-aci_deg)

        elif maske_ad == "Kalp Göz":
            nabiz = 1.0 + 0.10 * math.sin(simdi * 9.0)
            boy_kalp = max(20, min(300, int(0.68 * s * nabiz)))
            sp_kalp = sc.kalp(160)
            for goz in (t.goz_sol, t.goz_sag):
                gx, gy = int(round(goz[0])), int(round(goz[1]))
                bindir_merkez(kare, sp_kalp, gx, gy, boyut=boy_kalp, aci=-aci_deg, opak=1.0)
                cv2.circle(katman, (gx, gy), max(5, int(0.24 * s * nabiz)), PEMBE, -1, cv2.LINE_AA)

    def _kalp_ekle(self, x: float, y: float, s: float) -> None:
        if len(self.kalpler) >= 40:
            return
        vx = float(self.rng.choice([-1.0, 1.0]) * self.rng.uniform(90.0, 170.0))
        vy = float(self.rng.uniform(-220.0, -140.0))
        boy = max(20, min(70, int(0.38 * s)))
        self.kalpler.append(_Kalp(x=x, y=y, vx=vx, vy=vy, yas=0.0, omur=0.95, boy=boy))

    def _kalpleri_guncelle_ve_ciz(self, kare: np.ndarray, dt: float) -> None:
        if not self.kalpler:
            return
        sp = sc.kalp(96, (120, 60, 245))
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

    def _bal_ekle(self, x: float, y: float, s: float) -> None:
        if len(self.ballar) >= 25:
            return
        vx = float(self.rng.uniform(-35.0, 35.0))
        vy = float(self.rng.uniform(-140.0, -80.0))
        boy = max(18, min(60, int(0.34 * s)))
        self.ballar.append(_BalDamla(x=x, y=y, vx=vx, vy=vy, yas=0.0, omur=0.9, boy=boy))

    def _ballari_guncelle_ve_ciz(self, kare: np.ndarray, dt: float) -> None:
        if not self.ballar:
            return
        sp = sc.bal_damlasi(70)
        kalan: List[_BalDamla] = []
        for b in self.ballar:
            b.yas += dt
            if b.yas >= b.omur:
                continue
            b.x += b.vx * dt + math.sin(b.yas * 7.0) * 15.0 * dt
            b.y += b.vy * dt
            oran = 1.0 - (b.yas / b.omur)
            opak = max(0.0, min(1.0, oran * 1.2))
            boy = max(12, int(b.boy * (0.75 + 0.25 * math.sin(oran * math.pi))))
            bindir_merkez(kare, sp, int(b.x), int(b.y), boyut=boy, aci=0.0, opak=opak)
            kalan.append(b)
        self.ballar = kalan

    # ------------------------------------------------------------------ maske değiştirme
    def _degistir(self, t: _YuzTakip, adim: int, simdi: float) -> None:
        t.maske_degistir((t.maske_idx + adim) % len(self.MASKELER), simdi)
        self.son_oto_gecis = simdi
        self.ses.cal("pop", 0.75)
        ax, ay = self._don(t.alin, 0.0, -0.3 * t.s, math.cos(t.aci), math.sin(t.aci))
        for renk in (SARI, PEMBE, CAMGOBEGI):
            self.parcacik.yay(ax, ay, 6, renk=renk, hiz=5.0)

    def _yakin_yuz(self, x: float, y: float) -> Optional[_YuzTakip]:
        """Elin sahibi sayılan görünür yüz: tek yüz varsa o; kalabalıkta ele en yakın ve makul uzaklıkta olan."""
        adaylar = [tk for tk in self.takipler if tk.son_gorulme == self.onceki_t]
        if not adaylar:
            return None
        if len(adaylar) == 1:
            return adaylar[0]
        tk = min(adaylar, key=lambda a: math.hypot(a.burun[0] - x, a.burun[1] - y))
        return tk if math.hypot(tk.burun[0] - x, tk.burun[1] - y) < max(380.0, 5.5 * tk.s) else None

    def _el_hareketleri(self, algi: ck.Algi, simdi: float) -> None:
        # Avuç aç → kapa (yumruk) 1.2 sn içinde: ele en yakın yüzün maskesi ilerler (Enes 2026-10-12).
        # Avuç en az 2 karede açık görülmeli; değişimden sonra el yeniden açılmadan ikinci değişim yok.
        self._avuc_ipucu = []
        for i, (el, jest) in enumerate(zip(algi.eller or [], algi.jestler or [])):
            if not (self.ESKI_TETIKLER or self.AVUC_TETIK):
                break
            anahtar = algi.el_id[i] if i < len(algi.el_id) else i
            d = self._avuc_durum.setdefault(anahtar, {"t": -10.0, "kare": 0})
            if jest == "Open_Palm":
                d["t"], d["kare"] = simdi, d["kare"] + 1
                if d["kare"] >= 2:
                    self._avuc_ipucu.append(px(el, 9))
            elif jest == "Closed_Fist":
                if d["kare"] >= 2 and simdi - d["t"] < 1.2:
                    tk = self._yakin_yuz(float(el[0].x) * G, float(el[0].y) * Y)
                    if tk is not None:
                        self._degistir(tk, 1, simdi)
                d["kare"] = 0
        noktalar: List[Tuple[float, float]] = []
        uclar: List[Tuple[float, float]] = []
        self._el_sahipleri = []
        for i, el in enumerate(algi.eller or []):
            try:
                noktalar.append(px(el, 9))
                uclar.extend((px(el, 9), px(el, 8), px(el, 12)))
                eid = algi.el_id[i] if i < len(algi.el_id) else None
                sahibi = getattr(algi, "kisi_id", {}).get(("el", eid))
                self._el_sahipleri.extend([(p, sahibi) for p in (px(el, 9), px(el, 8), px(el, 12))])
            except Exception:
                continue
        if self.ESKI_TETIKLER:
            self._salla(noktalar, simdi)
        self._dugmeler(uclar, simdi)

    SALLA_HIZ = 750.0  # px/sn: kolu yana uzatmak (düğmeye gitmek) bundan yavaş

    def _salla(self, noktalar: List[Tuple[float, float]], simdi: float) -> None:
        """El sallama = sonraki maske. Gidiş-dönüş hamleleri tek sallama sayılır (eskiden ileri+geri birbirini
        siliyordu); el durulunca (0.3 sn) yeni sallama kabul edilir. Bulanıklıkla düşen kareler (<0.4 sn) izi koparmaz."""
        yeni: List[_ElIz] = []
        for x, y in noktalar:
            iz = min((e for e in self._el_izler if not any(e is k for k in yeni)),
                     key=lambda e: math.hypot(e.x - x, e.y - y), default=None)
            if iz is None or math.hypot(iz.x - x, iz.y - y) > 340.0 or simdi - iz.t > 0.4:
                yeni.append(_ElIz(x, y, simdi, x, simdi))
                continue
            dt = max(simdi - iz.t, 1e-3)
            dx = x - iz.x
            yon = 1 if dx > 3.0 else (-1 if dx < -3.0 else 0)
            if yon and yon != iz.yon:
                iz.x0, iz.t0, iz.yon = iz.x, iz.t, yon
            iz.sakin = iz.sakin + dt if abs(dx) / dt < 250.0 else 0.0
            if iz.sakin > 0.3:
                iz.kilit = False
            iz.x, iz.y, iz.t = x, y, simdi
            yeni.append(iz)
            tk = self._yakin_yuz(x, y)
            genlik, sure = abs(x - iz.x0), simdi - iz.t0
            if (tk is not None and not iz.kilit and sure > 0.0 and genlik >= max(90.0, 0.6 * tk.s)
                    and genlik / sure >= self.SALLA_HIZ):
                iz.kilit = True
                self._degistir(tk, 1, simdi)
        yeni.extend(e for e in self._el_izler if not any(e is k for k in yeni) and simdi - e.t <= 0.4)
        self._el_izler = yeni

    DUGME_R = 70
    DUGME_SN = 0.6

    def _dugme_merkez(self, yon: int) -> Tuple[int, int]:
        return tuple(map(int, self._ok_merkez[yon]))

    def _dugmeler(self, uclar: List[Tuple[float, float]], simdi: float) -> None:
        """Dokunmasız oklar: ele 0.6 sn tutunca sol = önceki, sağ = sonraki maske (en garantili yol)."""
        dt = 0.0 if self._dugme_t is None else min(max(simdi - self._dugme_t, 0.0), 0.1)
        self._dugme_t = simdi
        self.hedef_yuz = None
        for yon in (-1, 1):
            mx, my = self._dugme_merkez(yon)
            icindeki = [(x, y) for x, y in uclar if math.hypot(x - mx, y - my) < self.DUGME_R + 30]
            if not icindeki:
                self._dugme_sure[yon] = 0.0
                self._dugme_kilit[yon] = False
                continue
            if self._dugme_kilit[yon]:
                continue
            sahip = next((s for p, s in self._el_sahipleri if p == icindeki[0]), None)
            tk = next((t for t in self.takipler if getattr(t, "kimlik", None) == sahip), None) if sahip is not None else None
            tk = tk or self._yakin_yuz(*icindeki[0])
            self.hedef_yuz = tk
            self._dugme_sure[yon] += dt
            if self._dugme_sure[yon] >= self.DUGME_SN:
                if tk is not None:
                    self._dugme_kilit[yon] = True
                    self._dugme_sure[yon] = 0.0
                    for e in self._el_izler:  # düğmeye uzanan kol ayrıca sallama sayılmasın
                        e.kilit = True
                    self._degistir(tk, yon, simdi)

    def _ciz_dugmeler(self, kare: np.ndarray, ana: _YuzTakip) -> None:
        ikonlar = self._ikon_hazirla()
        n = len(self.MASKELER)
        for yon in (-1, 1):
            mx, my = self._dugme_merkez(yon)
            oran = min(1.0, self._dugme_sure[yon] / self.DUGME_SN)
            r = self.DUGME_R
            bindir_merkez(kare, ikonlar[(ana.maske_idx + yon) % n], mx, my, boyut=2 * r - 6, opak=0.55 + 0.45 * oran)
            cv2.circle(kare, (mx, my), r, BEYAZ, 2, cv2.LINE_AA)
            if oran > 0.0:
                cv2.ellipse(kare, (mx, my), (r + 7, r + 7), -90, 0, 360 * oran, SARI, 7, cv2.LINE_AA)
            ux = mx + yon * (r + 22)
            ok = np.array([(ux - yon * 10, my - 16), (ux + yon * 6, my), (ux - yon * 10, my + 16)], np.int32)
            cv2.polylines(kare, [ok], False, (20, 20, 25), 9, cv2.LINE_AA)
            cv2.polylines(kare, [ok], False, BEYAZ, 5, cv2.LINE_AA)
            yazi_koy(kare, "ELİNİ TUT", mx, my + r + 18, 20, renk=BEYAZ, hiza="orta")
        if self.hedef_yuz is not None:
            cv2.circle(kare, tuple(map(int, self.hedef_yuz.burun)), int(self.hedef_yuz.s * 1.8), SARI, 2, cv2.LINE_AA)
        for tk in self.takipler:  # baş eğilirken sıradaki maske o yandan kayarak gelir, halka dolunca değişir
            oran = min(1.0, abs(tk.aci) / self.KAFA_ESIK) if self.KAFA_TETIK and tk.egim_hazir else 0.0
            if oran > self.ONIZLEME_ORAN and tk.son_gorulme == self.onceki_t:
                yon = 1 if tk.aci > 0 else -1
                ix = int(tk.burun[0] + yon * tk.s * (2.6 - oran))
                iy = int(tk.burun[1] - tk.s * 0.6)
                bindir_merkez(kare, ikonlar[(tk.maske_idx + yon) % n], ix, iy, boyut=int(tk.s * 1.3), opak=oran)
                dolu = min(1.0, tk.egim_sure / self.KAFA_SN)
                if dolu > 0:
                    cv2.ellipse(kare, (ix, iy), (int(tk.s * .75),) * 2, -90, 0, 360 * dolu, SARI, 6, cv2.LINE_AA)
        for x, y in self._avuc_ipucu:  # açık avuç görüldü: kapatınca maske değişir
            cv2.circle(kare, (int(x), int(y)), 58, SARI, 4, cv2.LINE_AA)
            yazi_koy(kare, "YUMRUK YAP!", int(x), int(y) - 96, 26, renk=SARI, hiza="orta")

    # ------------------------------------------------------------------ yüz eşleme (kalabalık)
    def _yuzleri_esle(self, algi: ck.Algi, simdi: float) -> List[Tuple[_YuzTakip, Any, Dict[str, float]]]:
        """Yüzleri burun konumuyla takiplere bağlar: biri girip çıkınca maskeler kişiden kişiye atlamaz.
        Arkadaki çok küçük yüzler (göz arası < 22 px) yok sayılır."""
        n = len(self.MASKELER)
        adaylar = []
        blend_ham = algi.blend or []
        for i, yuz in enumerate((algi.yuzler or [])[:4]):
            try:
                bx, by = px(yuz, 1)
                g1, g2 = px(yuz, 33), px(yuz, 263)
            except Exception:
                continue
            if math.hypot(g2[0] - g1[0], g2[1] - g1[1]) < 22.0:
                continue
            bl = blend_ham[i] if i < len(blend_ham) and isinstance(blend_ham[i], dict) else {}
            kimlik = algi.yuz_id[i] if i < len(algi.yuz_id) else None
            adaylar.append((bx, by, yuz, bl, kimlik))
        adaylar.sort(key=lambda a: a[0])
        bos = list(self.takipler)
        sonuc = []
        for bx, by, yuz, bl, kimlik in adaylar:
            tk = next((t for t in bos if kimlik is not None and getattr(t, "kimlik", None) == kimlik), None)
            tk = tk or min(bos, key=lambda a: math.hypot(a.burun[0] - bx, a.burun[1] - by), default=None)
            if tk is not None and math.hypot(tk.burun[0] - bx, tk.burun[1] - by) < max(120.0, 2.5 * tk.s):
                bos.remove(tk)
            else:
                kullanilan = {a.maske_idx for a in self.takipler}
                idx = next((k for k in range(n) if (self.tur + k) % n not in kullanilan), len(self.takipler))
                tk = _YuzTakip(idx, self.tur, n, simdi)
                self.takipler.append(tk)
            tk.son_gorulme = simdi
            tk.kimlik = kimlik
            tk.son_lm, tk.son_bl = yuz, bl
            sonuc.append((tk, yuz, bl))
        # Algı tek-iki kare yüzü kaçırırsa maske düşüp vitrin yanıp sönmesin: kısa süre son konumda tut
        for tk in bos:
            if simdi - tk.son_gorulme < self.TUTMA_SN and getattr(tk, "son_lm", None) is not None:
                sonuc.append((tk, tk.son_lm, tk.son_bl))
        self.takipler = [tk for tk in self.takipler if simdi - tk.son_gorulme < 0.6]
        return sonuc

    # ------------------------------------------------------------------ ana döngü
    def isle(self, kare: np.ndarray, algi: ck.Algi, simdi: float) -> np.ndarray:
        if self.onceki_t is None:
            dt = 0.016
        else:
            dt = min(max(float(simdi - self.onceki_t), 0.0), 0.1)
        self.onceki_t = float(simdi)
        if self.son_oto_gecis is None:
            self.son_oto_gecis = float(simdi)

        eslesen = self._yuzleri_esle(algi, simdi)
        if not eslesen:
            if simdi - self.son_oto_gecis >= 12.0:
                self._tum_maskeleri_ilerlet(simdi)
            self._dugmeler([], simdi)
            self.maskeler = []
            self.parcacik.guncelle(dt)
            self._kalpleri_guncelle_ve_ciz(kare, dt)
            self._ballari_guncelle_ve_ciz(kare, dt)
            self._ciz_cekim_ekrani(kare, simdi)
            return kare

        ana_lm = max(eslesen, key=lambda e: abs(e[1][263].x - e[1][33].x))[1]
        cx = ana_lm[1].x * G
        dar = cx < .3 * G or cx > .7 * G
        for yon in (-1, 1):
            hedef = np.array([np.clip(cx + yon * 230, 112, G - 112), Y * .42]) if dar else np.array([112 if yon < 0 else G - 112, Y * .42])
            self._ok_merkez[yon] += (hedef - self._ok_merkez[yon]) * min(1., dt * 6)

        self._el_hareketleri(algi, simdi)

        katman = self._katman
        katman.fill(0)
        aktif_maskeler: List[str] = []
        foto_aktif: Optional[str] = None
        flas_gucu = 0.0

        for t, lm, bl in eslesen:
            t.guncelle_konum(lm)
            t.jaw = float(bl.get("jawOpen", 0.0))
            brow_up = float(bl.get("browInnerUp", 0.0))
            blink_l = float(bl.get("eyeBlinkLeft", 0.0))
            blink_r = float(bl.get("eyeBlinkRight", 0.0))

            # Göz kırpma (tek göz ya da iki göz ~0.2 sn): sonraki maske
            if (blink_l > 0.5 and blink_r > 0.5) or (max(blink_l, blink_r) > 0.55 and abs(blink_l - blink_r) > 0.3):
                t.goz_kapali_sure += dt
                if self.ESKI_TETIKLER and t.goz_kapali_sure >= 0.18 and (simdi - t.son_kirp_degisim) > 0.9:
                    self._degistir(t, 1, simdi)
                    t.son_kirp_degisim = simdi
                    t.goz_kapali_sure = 0.0
            else:
                t.goz_kapali_sure = 0.0

            # Başı yana eğme (~20°): sağa sonraki, sola önceki; tekrar için baş düzelmeli
            if self.ESKI_TETIKLER and t.egim_hazir and abs(t.aci) > 0.35:
                self._degistir(t, 1 if t.aci > 0 else -1, simdi)
                t.egim_hazir = False
            elif (self.KAFA_TETIK and t.egim_hazir and abs(t.aci) > self.KAFA_ESIK
                  and simdi - getattr(t, "son_kafa", -9.0) >= self.KAFA_ARA):
                t.egim_sure += dt
                if t.egim_sure >= self.KAFA_SN:
                    self._degistir(t, 1 if t.aci > 0 else -1, simdi)
                    t.son_kafa = simdi
                    t.egim_hazir, t.egim_sure = False, 0.0
            else:
                t.egim_sure = 0.0
            if abs(t.aci) < 0.15:
                t.egim_hazir = True

            # Kaş kaldırma: kişinin doğal seviyesine göre ~0.12 sn yukarıda tutunca sonraki maske
            kas = max(brow_up, 0.5 * (float(bl.get("browOuterUpLeft", 0.0)) + float(bl.get("browOuterUpRight", 0.0))))
            if t.kas_taban is None:
                t.kas_taban = min(kas, 0.25)
            if kas < t.kas_taban + 0.2:
                t.kas_taban += (kas - t.kas_taban) * min(1.0, dt * 0.8)
            kas_esik = max(0.38, t.kas_taban + 0.25)
            if kas >= kas_esik:
                t.kas_sure += dt
                if t.kas_hazir and t.kas_sure >= 0.2 and simdi - t.son_kirp_degisim > 0.6:
                    t.kas_hazir = False
                    t.kas_t0 = simdi
                    t.son_kirp_degisim = simdi
                    if self.ESKI_TETIKLER or self.KAS_TETIK:
                        self._degistir(t, 1, simdi)
            else:
                t.kas_sure = 0.0
                if kas < kas_esik - 0.1:
                    t.kas_hazir = True

            kas_carpan = 1.0
            kas_gecen = simdi - t.kas_t0
            if 0.0 <= kas_gecen < 0.2:
                kas_carpan = 1.0 + 0.2 * math.sin((kas_gecen / 0.2) * math.pi)
            t.kas_carpan = kas_carpan
            t.goz_efekti = max(blink_l, blink_r) > .55
            if t.goz_efekti:
                cv2.drawMarker(kare, tuple(map(int, t.burun)), SARI, cv2.MARKER_STAR, 24, 2)

            maske_ad = self.MASKELER[t.maske_idx]
            aktif_maskeler.append(maske_ad)

            if not t.foto_tamamlandi:
                if simdi - t.son_maske_degisim >= 6.0 and t.foto_baslangic is None:
                    t.foto_baslangic = simdi
                if t.foto_baslangic is not None:
                    foto_gecen = simdi - t.foto_baslangic
                    if foto_gecen < 2.0:
                        foto_aktif = "3" if foto_gecen < 0.7 else ("2" if foto_gecen < 1.4 else "1")
                    else:
                        t.flas_t0 = simdi
                        t.foto_tamamlandi = True
                        t.son_maske_degisim = simdi + 4.0
                        self.ses.cal("basari", 0.8)

            flas_gecen = simdi - t.flas_t0
            if 0.0 <= flas_gecen < 0.15:
                flas_gucu = max(flas_gucu, 0.35 * (1.0 - flas_gecen / 0.15))

            if t.jaw > 0.45:
                ax, ay = t.agiz
                if maske_ad == "Şeytan":
                    self.parcacik.yay(ax, ay, 4, renk=(20, 110, 255), hiz=4.5)
                    self.parcacik.yay(ax, ay, 2, renk=KIRMIZI, hiz=3.5)
                elif maske_ad == "Kral":
                    self.parcacik.yay(ax, ay, 5, renk=SARI, hiz=4.2)
                elif maske_ad == "Ayıcık":
                    self.parcacik.yay(ax, ay, 3, renk=(20, 180, 255), hiz=3.8)
                    self._bal_ekle(ax, ay, t.s)
                elif maske_ad == "Kalp Göz" and simdi - self._son_kalp > 0.12:
                    self._son_kalp = simdi
                    self._kalp_ekle(ax, ay, t.s)

            gecen = simdi - t.gecis_t0
            if t.eski_idx is not None and 0.0 <= gecen < 0.2:
                eski_oran = max(0.05, 1.0 - (gecen / 0.2))
                self._ciz_maske(kare, katman, t, self.MASKELER[t.eski_idx], eski_oran * kas_carpan, simdi)
            if 0.0 <= gecen < 0.25:
                u = gecen / 0.25
                yeni_oran = math.sin(u * math.pi * 0.5) + 0.18 * math.sin(u * math.pi)
            else:
                yeni_oran = 1.0
                t.eski_idx = None
            self._ciz_maske(kare, katman, t, maske_ad, yeni_oran * kas_carpan, simdi)
            t.etiket = f"→ {maske_ad.upper()}" if 0 <= simdi - t.gecis_t0 < 1 else ""
            if t.etiket:
                yazi_koy(kare, t.etiket, int(t.alin[0]), max(10, int(t.alin[1] - t.s)), 28, renk=SARI, hiza="orta")

        self.maskeler = aktif_maskeler

        parilti(kare, katman, guc=1.8, sigma=3.0)
        self.parcacik.guncelle(dt)
        self.parcacik.ciz(kare)
        self._kalpleri_guncelle_ve_ciz(kare, dt)
        self._ballari_guncelle_ve_ciz(kare, dt)

        if flas_gucu > 0.005:
            cv2.addWeighted(kare, 1.0 - flas_gucu, np.full_like(kare, 255), flas_gucu, 0, dst=kare)

        ana = max((tk for tk, _, _ in eslesen), key=lambda a: a.s)
        # Benzer boydaki iki yüz arasında ana yüz kare kare değişip alttaki şerit sağa sola kaymasın
        onceki = getattr(self, "_ana", None)
        if onceki is not None and onceki is not ana and any(tk is onceki for tk, _, _ in eslesen) and ana.s < 1.3 * onceki.s:
            ana = onceki
        self._ana = ana
        self._karusel(kare, ana, simdi)
        self._ciz_dugmeler(kare, ana)
        yas = simdi - getattr(ana, "ogretim_bas", simdi)
        if not hasattr(ana, "ogretim_bas"):
            ana.ogretim_bas = simdi
        if yas < 4.0:  # öğretici: başın üstünde sağa-sola sallanan yay, "başını yatır"
            sal = math.degrees(0.35 * math.sin(yas * 4.0))
            mx, my, r = int(ana.burun[0]), int(ana.burun[1]), int(ana.s * 1.5)
            cv2.ellipse(kare, (mx, my), (r, r), -90 + sal, -28, 28, CAMGOBEGI, 5, cv2.LINE_AA)
            for uc in (-28, 28):
                aci = math.radians(-90 + sal + uc)
                ux, uy = int(mx + r * math.cos(aci)), int(my + r * math.sin(aci))
                cv2.circle(kare, (ux, uy), 9, CAMGOBEGI, -1, cv2.LINE_AA)
            yazi_koy(kare, "BAŞINI YANA YATIR → MASKE DEĞİŞİR", G // 2, 160, 28, renk=SARI, hiza="orta")
        if foto_aktif is not None:
            panel(kare, G // 2 - 150, 24, G // 2 + 150, 92, renk=(20, 16, 32), opak=0.8, kenar=PEMBE)
            yazi_koy(kare, f"Poz ver!  {foto_aktif}", G // 2, 36, 40, renk=SARI, hiza="orta")
        return kare

    # ------------------------------------------------------------------ karusel
    def _ikon_hazirla(self) -> List[np.ndarray]:
        """Her maskenin küçük önizlemesi: sade bir avatar yüze maskeyi takıp kırpar (bir kez)."""
        if self._ikonlar:
            return self._ikonlar
        kayit_parcacik, kayit_kalp, kayit_bal = self.parcacik, self.kalpler, self.ballar
        self.parcacik, self.kalpler, self.ballar = Parcaciklar(10), [], []
        cx, cy, s = G // 2, Y // 2, 120.0
        for i, ad in enumerate(self.MASKELER):
            tuval = np.zeros((Y, G, 3), np.uint8)
            tuval[:] = (60, 40, 46)
            cv2.circle(tuval, (cx, cy), int(1.05 * s), (150, 185, 235), -1, cv2.LINE_AA)
            cv2.circle(tuval, (cx - int(0.12 * s), cy - int(0.15 * s)), int(0.82 * s), (175, 205, 245), -1, cv2.LINE_AA)
            for isaret in (-1, 1):
                gc = (cx + isaret * int(0.36 * s), cy - int(0.12 * s))
                cv2.ellipse(tuval, gc, (int(0.15 * s), int(0.10 * s)), 0, 0, 360, (245, 245, 250), -1, cv2.LINE_AA)
                cv2.circle(tuval, gc, int(0.07 * s), (60, 45, 35), -1, cv2.LINE_AA)
                cv2.circle(tuval, (gc[0] - int(0.025 * s), gc[1] - int(0.025 * s)), int(0.02 * s), (255, 255, 255), -1, cv2.LINE_AA)
            cv2.ellipse(tuval, (cx, cy + int(0.42 * s)), (int(0.24 * s), int(0.12 * s)), 0, 10, 170, (60, 60, 150), 6, cv2.LINE_AA)
            t = _YuzTakip(0, 0, len(self.MASKELER), 1000.0)
            t.hazir = True
            t.alin, t.burun, t.cene = (cx, cy - 0.85 * s), (cx, cy + 0.12 * s), (cx, cy + 1.0 * s)
            t.goz_sol, t.goz_sag = (cx - 0.5 * s, cy - 0.12 * s), (cx + 0.5 * s, cy - 0.12 * s)
            t.iris_sol, t.iris_sag = (cx - 0.36 * s, cy - 0.12 * s), (cx + 0.36 * s, cy - 0.12 * s)
            t.agiz, t.s, t.aci = (cx, cy + 0.45 * s), s, 0.0
            t.jaw = 0.75 if ad in ("Köpek", "Gökkuşağı") else 0.0
            t.gecis_t0 = 0.0
            katman = np.zeros_like(tuval)
            self._ciz_maske(tuval, katman, t, ad, 1.0, 1000.4)
            parilti(tuval, katman, guc=1.6, sigma=3.0)
            kirp = tuval[cy - int(2.55 * s):cy + int(1.85 * s), cx - int(2.2 * s):cx + int(2.2 * s)]
            ikon = cv2.resize(kirp, (120, 120), interpolation=cv2.INTER_AREA)
            alfa = np.zeros((120, 120), np.uint8)
            cv2.circle(alfa, (60, 60), 58, 255, -1, cv2.LINE_AA)
            self._ikonlar.append(np.dstack([ikon, alfa]))
        self.parcacik, self.kalpler, self.ballar = kayit_parcacik, kayit_kalp, kayit_bal
        return self._ikonlar

    def _karusel(self, kare: np.ndarray, ana: _YuzTakip, simdi: float) -> None:
        """Altta maske şeridi: ortadaki = ana (en büyük) yüzün maskesi; yan yana komşular."""
        ikonlar = self._ikon_hazirla()
        n = len(self.MASKELER)
        # kayma animasyonu: hedef indekse yumuşak yaklaş (sarma yönü kısa yoldan)
        fark = (ana.maske_idx - self._karusel_konum + n / 2) % n - n / 2
        self._karusel_konum = (self._karusel_konum + fark * 0.25) % n
        ara, yc = 104, Y - 78
        panel(kare, G // 2 - 3 * ara - 70, yc - 66, G // 2 + 3 * ara + 70, yc + 62, renk=(16, 14, 24), opak=0.45)
        for k in range(-4, 5):
            idx = int(round(self._karusel_konum)) + k
            kayma = self._karusel_konum - round(self._karusel_konum)
            ofs = k - kayma
            if abs(ofs) > 3.4:
                continue
            x = int(G // 2 + ofs * ara)
            yakin = max(0.0, 1.0 - abs(ofs))
            boy = int(70 + 34 * yakin)
            bindir_merkez(kare, ikonlar[idx % n], x, yc, boyut=boy, opak=0.55 + 0.45 * yakin if abs(ofs) > 0.5 else 1.0)
            if abs(ofs) < 0.5:
                cv2.circle(kare, (x, yc), boy // 2 + 4, SARI, 3, cv2.LINE_AA)
        isim_yas = simdi - ana.son_maske_degisim
        ad = self.MASKELER[ana.maske_idx]
        olcek = 1.0 + 0.25 * max(0.0, 1.0 - isim_yas / 0.3) if 0 <= isim_yas else 1.0
        yazi_koy(kare, ad.upper(), G // 2, yc - 122, 40, renk=SARI, hiza="orta", olcek=olcek)

    def _ciz_cekim_ekrani(self, kare: np.ndarray, simdi: float) -> None:
        # Enes 2026-10-12: kamera net kalır, bulanıklık/karartma yok

        # Bekleme vitrini: maskelerin avatar önizlemeleri ekranın iki yanında süzülür
        ikonlar = self._ikon_hazirla()
        n = len(ikonlar)
        for i in range(8):
            idx = (i + int(simdi / 3.0)) % n
            sol = i < 4
            kx = 95 if sol else G - 95
            ky = 150 + (i % 4) * 150 + int(10 * math.sin(simdi * 2.0 + i))
            bindir_merkez(kare, ikonlar[idx], kx, ky, boyut=124, opak=0.95)
            cv2.circle(kare, (kx, ky), 64, SARI if i % 3 == 0 else CAMGOBEGI, 2, cv2.LINE_AA)

        baslik(kare, self.AD, renk=SARI)

