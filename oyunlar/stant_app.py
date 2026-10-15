"""Stant uygulaması: seçilen deneyimler tek pencerede.

Ziyaretçi ana menüde elini bir kartın üstünde tutarak seçer. Kadrajda 40 sn kimse kalmazsa (oyun sürmüyorsa)
ya da sol alt köşeye avuç/bilek tutulursa menüye dönülür. Operatör: 1-9 seç, M menü, N/B sonraki/önceki,
F tam ekran, Q/Esc çıkış; diğer tuşlar etkin deneyime gider (boşluk: mod).
Ortam: KAMERA (varsayılan 0), TAM_EKRAN=1.
"""
from __future__ import annotations

import importlib
import math
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cekirdek as ck  # noqa: E402
import meyve_ciz  # noqa: E402
import sus_ciz  # noqa: E402
from oyuncu import OyuncuKapisi
from cekirdek import BEYAZ, CAMGOBEGI, G, PEMBE, SARI, YESIL, Y, bindir_merkez, panel, parilti, px, yazi_koy  # noqa: E402

DENEYIMLER = [
    "p_neon_kilic",
    "p_gulmeme",
    "p_maske",
    "p_parmak_kusu",
    "p_cevap_yagmuru",
    "p_refleks",
    "p_hayalet_klon",
    "p_penalti",
    "p_ciz_tahmin",
    "p_tas_kagit",
]
RENKLER = [CAMGOBEGI, SARI, YESIL]
SECIM_SN = 1.0
BOS_DONUS_SN = 40.0  # 12 sn kısa kaldı, oyuncular beklerken menüye atıyordu (Enes 2026-10-13)
EV_SN = 3.0  # sarkan el yanlışlıkla menüye atmasın (Enes 2026-10-12, 2026-10-13: 2 -> 3 sn)
KAPALI: set = {"p_tas_kagit"}  # menüde soluk durur, açılmaz; TKM devre dışı, kartı soluk görünür (Enes 2026-10-15)
KENDI_IMLECI = {"p_neon_kilic", "p_maske"}  # parmağı kendisi çiziyor; oyun da KENDI_IMLECI=True diyebilir
UCLAR = (8,)  # yalnız oyunu oynatan işaret parmağı ucu (Enes 2026-10-13: tek parmak izi)


def _az_hareket() -> bool:
    """REDUCED_MOTION veya AZ_HAREKET=1 ortam değişkeni kontrolü."""
    return os.environ.get("REDUCED_MOTION", "").lower() in ("1", "true", "yes") or os.environ.get("AZ_HAREKET", "").lower() in ("1", "true", "yes")


def parmak_izi(kare: np.ndarray, algi: Any, izler: List[list], simdi: float) -> None:
    """Algılanan her elin işaret parmağı ucu: neon nokta + yumuşak ışıltılı iz."""
    eller = [e for e in (algi.eller or []) if len(e) > 20]
    if not eller:
        izler.clear()
        return
    katman = np.zeros_like(kare)
    yeni: List[list] = []
    az = _az_hareket()
    max_iz = 3 if az else 7
    sure_limit = 0.12 if az else 0.25
    for el in eller:
        ux, uy = px(el, 8)
        iz = min((z for z in izler if all(z is not y for y in yeni)),
                 key=lambda z: math.hypot(z[-1][0] - ux, z[-1][1] - uy), default=None)
        if iz is None or math.hypot(iz[-1][0] - ux, iz[-1][1] - uy) > 220:
            iz = []
        iz = [p for p in iz if simdi - p[2] <= sure_limit][-max_iz:] + [(ux, uy, simdi)]
        yeni.append(iz)
        for k in range(1, len(iz)):
            cv2.line(katman, tuple(map(int, iz[k - 1][:2])), tuple(map(int, iz[k][:2])), CAMGOBEGI, 2 + 2 * k, cv2.LINE_AA)
        for i in UCLAR:
            x, y = map(int, px(el, i))
            cv2.circle(katman, (x, y), 13 if i == 8 else 7, CAMGOBEGI, -1, cv2.LINE_AA)
            cv2.circle(kare, (x, y), 6 if i == 8 else 3, BEYAZ, -1, cv2.LINE_AA)
    izler[:] = yeni
    if not az:
        parilti(kare, katman, guc=1.6, sigma=3.0)
    else:
        cv2.addWeighted(kare, 1.0, katman, 0.7, 0, dst=kare)


KISAYOLLAR = (("F", "tam ekran"), ("M", "menü"))
_KISAYOL_SERIT: Optional[np.ndarray] = None


def _kisayol_serit() -> np.ndarray:
    """Sol alttaki tuş şeridi: klavye tuşu gibi küçük çerçeveli harf + soluk etiket (bir kez çizilir, BGRA)."""
    global _KISAYOL_SERIT
    if _KISAYOL_SERIT is None:
        from PIL import Image, ImageDraw, ImageFont
        yol = ck.stand.FONT_YAZI
        f = ImageFont.truetype(yol, 13) if yol else ImageFont.load_default()
        olcu = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        w = 10 + sum(22 + 6 + int(olcu.textlength(e, font=f)) + 16 for _, e in KISAYOLLAR) - 6
        h, taban = 34, 22  # yazılar ortak taban çizgisine oturur
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=8, fill=(28, 18, 22, 120))
        x = 10
        for tus, etiket in KISAYOLLAR:
            d.rounded_rectangle((x, 6, x + 22, 28), radius=4, outline=(165, 150, 150, 230), width=1)
            d.text((x + 11, taban), tus, font=f, fill=(240, 235, 235, 255), anchor="ms")
            d.text((x + 28, taban), etiket, font=f, fill=(178, 165, 165, 255), anchor="ls")
            x += 22 + 6 + int(d.textlength(etiket, font=f)) + 16
        _KISAYOL_SERIT = cv2.cvtColor(np.array(im), cv2.COLOR_RGBA2BGRA)
    return _KISAYOL_SERIT


def _kisayollar(kare: np.ndarray) -> None:
    """Sol altta her zaman duran, göze batmayan tuş ipuçları."""
    serit = _kisayol_serit()
    ck.stand.bindir(kare, serit, 12, Y - serit.shape[0] - 10, 0.85)


# ---------------------------------------------------------------- kart ikonları (prosedürel, emoji yok)
def _tuval(boy: int = 200) -> Tuple[np.ndarray, np.ndarray]:
    return np.zeros((boy, boy, 3), np.uint8), np.zeros((boy, boy, 3), np.uint8)


def _bgra(img: np.ndarray, isik: np.ndarray, guc: float = 1.6) -> np.ndarray:
    parilti(img, isik, guc=guc, sigma=3.0)
    alfa = np.clip(img.max(axis=2).astype(np.float32) * 3.0, 0, 255).astype(np.uint8)
    return np.dstack([img, alfa])


def _siluet(isik: np.ndarray, cx: int, renk, kal: int = 4) -> None:
    cv2.circle(isik, (cx, 62), 24, renk, kal, cv2.LINE_AA)
    cv2.ellipse(isik, (cx, 150), (40, 56), 0, 180, 360, renk, kal, cv2.LINE_AA)
    cv2.line(isik, (cx - 40, 150), (cx + 40, 150), renk, kal, cv2.LINE_AA)


def ikon_klon() -> np.ndarray:
    img, isik = _tuval()
    for cx, renk in ((62, (200, 90, 255)), (100, CAMGOBEGI), (138, SARI)):
        _siluet(isik, cx, renk)
    img[:] = isik // 3
    return _bgra(img, isik)


def ikon_kilic() -> np.ndarray:
    img, isik = _tuval()
    m = meyve_ciz.meyveler()[0]
    sp = cv2.resize(m["dis"], (150, 150), interpolation=cv2.INTER_AREA)
    a = sp[:, :, 3:4].astype(np.float32) / 255.0
    img[25:175, 25:175] = (sp[:, :, :3] * a).astype(np.uint8)
    cv2.line(isik, (18, 170), (182, 30), CAMGOBEGI, 9, cv2.LINE_AA)
    cv2.line(img, (18, 170), (182, 30), BEYAZ, 3, cv2.LINE_AA)
    parilti(img, isik, guc=1.6, sigma=3.0)
    alfa = np.zeros((200, 200), np.uint8)
    alfa[25:175, 25:175] = sp[:, :, 3]
    alfa = np.maximum(alfa, np.clip(isik.max(axis=2).astype(np.int32) * 3, 0, 255).astype(np.uint8))
    return np.dstack([img, alfa])


def ikon_gulme() -> np.ndarray:
    img, isik = _tuval()
    for cx, renk, guler in ((58, CAMGOBEGI, False), (142, PEMBE, True)):
        cv2.circle(img, (cx, 100), 38, (150, 185, 235), -1, cv2.LINE_AA)
        cv2.circle(isik, (cx, 100), 44, renk, 4, cv2.LINE_AA)
        for d in (-13, 13):
            cv2.circle(img, (cx + d, 92), 4, (40, 35, 40), -1, cv2.LINE_AA)
        if guler:
            cv2.ellipse(img, (cx, 108), (16, 14), 0, 0, 180, (60, 50, 160), -1, cv2.LINE_AA)
        else:
            cv2.line(img, (cx - 12, 116), (cx + 12, 116), (60, 50, 120), 3, cv2.LINE_AA)
    yazi_koy(isik, "VS", 100, 150, 30, renk=SARI, hiza="orta")
    return _bgra(img, isik)


def ikon_gorunmez() -> np.ndarray:
    img, isik = _tuval()
    for k in range(0, 360, 24):  # kesik çizgili siluet
        a0, a1 = math.radians(k), math.radians(k + 12)
        cv2.line(isik, (int(100 + 26 * math.cos(a0)), int(60 + 26 * math.sin(a0))),
                 (int(100 + 26 * math.cos(a1)), int(60 + 26 * math.sin(a1))), BEYAZ, 3, cv2.LINE_AA)
    for k in range(180, 360, 20):
        a0, a1 = math.radians(k), math.radians(k + 10)
        cv2.line(isik, (int(100 + 50 * math.cos(a0)), int(160 + 64 * math.sin(a0))),
                 (int(100 + 50 * math.cos(a1)), int(160 + 64 * math.sin(a1))), BEYAZ, 3, cv2.LINE_AA)
    img[:] = isik // 4
    sonuc = _bgra(img, isik, guc=1.2)
    renk, alfa = np.ascontiguousarray(sonuc[:, :, :3]), sonuc[:, :, 3].copy()
    p = sus_ciz.parilti(50)
    for x, y in ((150, 50), (48, 120), (158, 150)):
        bindir_merkez(renk, p, x, y, boyut=40)
        alfa[y - 20:y + 20, x - 20:x + 20] = np.maximum(alfa[y - 20:y + 20, x - 20:x + 20],
                                                         cv2.resize(p[:, :, 3], (40, 40)))
    return np.dstack([renk, alfa])


def ikon_hayalet_klon() -> np.ndarray:
    """Tek kart, iki deneyim: dolu iki klon silueti + yanında kesik çizgili hayalet (Enes 2026-10-13)."""
    img, isik = _tuval()
    for cx, renk in ((54, (200, 90, 255)), (92, CAMGOBEGI)):
        _siluet(isik, cx, renk)
    img[:] = isik // 3
    for k in range(0, 360, 24):
        a0, a1 = math.radians(k), math.radians(k + 12)
        cv2.line(isik, (int(146 + 24 * math.cos(a0)), int(62 + 24 * math.sin(a0))),
                 (int(146 + 24 * math.cos(a1)), int(62 + 24 * math.sin(a1))), BEYAZ, 3, cv2.LINE_AA)
    for k in range(180, 360, 20):
        a0, a1 = math.radians(k), math.radians(k + 10)
        cv2.line(isik, (int(146 + 40 * math.cos(a0)), int(150 + 56 * math.sin(a0))),
                 (int(146 + 40 * math.cos(a1)), int(150 + 56 * math.sin(a1))), BEYAZ, 3, cv2.LINE_AA)
    sonuc = _bgra(img, isik, guc=1.4)
    renk, alfa = np.ascontiguousarray(sonuc[:, :, :3]), sonuc[:, :, 3].copy()
    p = sus_ciz.parilti(40)
    for x, y in ((178, 30), (172, 120)):
        bindir_merkez(renk, p, x, y, boyut=32)
        alfa[y - 16:y + 16, x - 16:x + 16] = np.maximum(alfa[y - 16:y + 16, x - 16:x + 16],
                                                         cv2.resize(p[:, :, 3], (32, 32)))
    return np.dstack([renk, alfa])


def ikon_kus() -> np.ndarray:
    img, isik = _tuval()
    for x0, ust, alt in ((12, 60, 140), (152, 36, 116)):  # boşlukları kayık iki boru
        for a, b in ((0, ust), (alt, 200)):
            cv2.rectangle(img, (x0, a), (x0 + 36, b), (40, 110, 40), -1)
            cv2.rectangle(isik, (x0, a), (x0 + 36, b), YESIL, 4, cv2.LINE_AA)
    for k in range(3):
        cv2.line(isik, (54, 88 + k * 12), (66, 88 + k * 12), BEYAZ, 2, cv2.LINE_AA)
    cv2.ellipse(img, (100, 98), (30, 24), -10, 0, 360, SARI, -1, cv2.LINE_AA)
    cv2.ellipse(isik, (100, 98), (34, 28), -10, 0, 360, SARI, 3, cv2.LINE_AA)
    cv2.ellipse(img, (88, 104), (16, 9), -25, 0, 360, (0, 150, 230), -1, cv2.LINE_AA)
    cv2.circle(img, (112, 89), 7, BEYAZ, -1, cv2.LINE_AA)
    cv2.circle(img, (114, 89), 3, (30, 30, 30), -1, cv2.LINE_AA)
    cv2.fillPoly(img, [np.array([(127, 96), (147, 101), (127, 108)], np.int32)], (40, 120, 255), cv2.LINE_AA)
    return _bgra(img, isik)


def ikon_yagmur() -> np.ndarray:
    img, isik = _tuval()
    for cx, cy, aci, renk, harf in ((46, 66, -12, CAMGOBEGI, "A"), (100, 128, 5, YESIL, "B"), (154, 54, 14, PEMBE, "C")):
        kutu = cv2.boxPoints(((cx, cy), (54, 44), aci)).astype(np.int32)
        cv2.fillPoly(img, [kutu], tuple(c // 3 for c in renk), cv2.LINE_AA)
        cv2.polylines(isik, [kutu], True, renk, 4, cv2.LINE_AA)
        yazi_koy(img, harf, cx, cy - 17, 28, renk=BEYAZ, hiza="orta")
        for k in (1, 2):  # düşme izi
            cv2.line(isik, (cx - 12, cy - 22 - k * 13), (cx - 12, cy - 30 - k * 13), renk, 2, cv2.LINE_AA)
            cv2.line(isik, (cx + 12, cy - 22 - k * 13), (cx + 12, cy - 30 - k * 13), renk, 2, cv2.LINE_AA)
    cv2.polylines(isik, [np.array([(84, 176), (96, 188), (118, 162)], np.int32)], False, YESIL, 6, cv2.LINE_AA)
    return _bgra(img, isik)


def ikon_duello() -> np.ndarray:
    img, isik = _tuval()
    for yon, renk in ((-1, CAMGOBEGI), (1, PEMBE)):  # sırt sırta iki tabanca, namlu dışa
        def p(x, y):
            return (int(100 + yon * (8 + x)), int(y))
        govde = np.array([p(0, 74), p(70, 74), p(70, 88), p(34, 88), p(30, 100), p(20, 144), p(0, 144), p(6, 100)], np.int32)
        cv2.fillPoly(img, [govde], tuple(c // 3 for c in renk), cv2.LINE_AA)
        cv2.polylines(isik, [govde], True, renk, 3, cv2.LINE_AA)
        cv2.circle(isik, p(28, 92), 11, renk, 3, cv2.LINE_AA)
        uc = p(76, 81)
        for k in range(8):  # namlu alevi
            a = k * math.pi / 4
            cv2.line(isik, uc, (int(uc[0] + 13 * math.cos(a)), int(uc[1] + 13 * math.sin(a))), SARI, 3, cv2.LINE_AA)
    yazi_koy(isik, "!", 100, 8, 54, renk=SARI, hiza="orta")
    return _bgra(img, isik)


def ikon_tkm() -> np.ndarray:
    img, isik = _tuval()
    cv2.circle(img, (52, 64), 26, (60, 70, 80), -1, cv2.LINE_AA)
    cv2.circle(isik, (52, 64), 28, CAMGOBEGI, 4, cv2.LINE_AA)
    cv2.rectangle(img, (122, 38), (172, 94), (90, 90, 90), -1)
    cv2.rectangle(isik, (122, 38), (172, 94), SARI, 4, cv2.LINE_AA)
    for cx in (84, 116):
        cv2.circle(isik, (cx, 166), 12, PEMBE, 4, cv2.LINE_AA)
    cv2.line(isik, (90, 155), (126, 112), PEMBE, 5, cv2.LINE_AA)
    cv2.line(isik, (110, 155), (74, 112), PEMBE, 5, cv2.LINE_AA)
    return _bgra(img, isik)


def ikon_penalti() -> np.ndarray:
    img, isik = _tuval()
    for x in range(46, 170, 18):  # file
        cv2.line(img, (x, 34), (x, 108), (90, 90, 90), 1)
    for y in range(50, 110, 16):
        cv2.line(img, (24, y), (176, y), (90, 90, 90), 1)
    cv2.polylines(isik, [np.array([(24, 110), (24, 30), (176, 30), (176, 110)], np.int32)], False, BEYAZ, 5, cv2.LINE_AA)
    for k in range(1, 10):  # parmakla çizilen kavisli yol
        t = k / 10
        x = (1 - t) ** 2 * 60 + 2 * t * (1 - t) * 52 + t * t * 154
        y = (1 - t) ** 2 * 166 + 2 * t * (1 - t) * 50 + t * t * 52
        cv2.circle(isik, (int(x), int(y)), 3 + k // 4, SARI, -1, cv2.LINE_AA)
    for k in range(8):  # altın köşe
        a = k * math.pi / 4
        cv2.line(isik, (154, 52), (int(154 + 16 * math.cos(a)), int(52 + 16 * math.sin(a))), SARI, 3, cv2.LINE_AA)
    cv2.circle(img, (60, 168), 18, BEYAZ, -1, cv2.LINE_AA)
    cv2.circle(img, (60, 168), 7, (40, 40, 40), -1, cv2.LINE_AA)
    cv2.circle(isik, (60, 168), 20, BEYAZ, 2, cv2.LINE_AA)
    return _bgra(img, isik)


def ikon_ciz() -> np.ndarray:
    img, isik = _tuval()
    iz = np.array([(16 + k * 6, int(150 + 20 * math.sin(k * .6))) for k in range(20)], np.int32)
    cv2.polylines(isik, [iz], False, PEMBE, 5, cv2.LINE_AA)
    uc, yon, n = iz[-1].astype(float), np.array([.6, -.8]), np.array([.8, .6])
    taban, son = uc + yon * 24, uc + yon * 82
    govde = np.array([taban + n * 10, son + n * 10, son - n * 10, taban - n * 10], np.int32)
    cv2.fillPoly(img, [govde], (40, 160, 255), cv2.LINE_AA)
    cv2.fillPoly(img, [np.array([uc, taban + n * 10, taban - n * 10], np.int32)], (150, 200, 235), cv2.LINE_AA)
    cv2.polylines(isik, [govde], True, SARI, 3, cv2.LINE_AA)
    yazi_koy(isik, "?", 58, 18, 70, renk=CAMGOBEGI, hiza="orta")
    return _bgra(img, isik)


# ---------------------------------------------------------------- menü
class AnaMenu:
    def __init__(self, adlar: List[str], ikonlar: List[np.ndarray], kapali: Optional[set] = None):
        self.adlar = adlar
        self.ikonlar = ikonlar
        self.kapali = kapali or set()
        self.uzerinde: Optional[int] = None
        self.sure = 0.0
        self.imlecler: List[Tuple[float, float]] = []
        self.giris_t: float = 0.0
        self._soluklar: Dict[int, np.ndarray] = {}

    def _soluk_ikon(self, i: int) -> np.ndarray:
        """Kapalı kartın gri ve yarı saydam ikonu (bir kez hazırlanır)."""
        if i not in self._soluklar:
            ikon = self.ikonlar[i].copy()
            gri = cv2.cvtColor(np.ascontiguousarray(ikon[:, :, :3]), cv2.COLOR_BGR2GRAY)
            ikon[:, :, :3] = cv2.cvtColor(gri, cv2.COLOR_GRAY2BGR)
            ikon[:, :, 3] = (ikon[:, :, 3].astype(np.float32) * 0.35).astype(np.uint8)
            self._soluklar[i] = ikon
        return self._soluklar[i]

    def kartlar(self) -> List[Tuple[int, int, int, int]]:
        """Bütün oyunlar tek ekranda: 9'a kadar 3x3, daha fazlasında 5 sütun."""
        sutun = 3 if len(self.adlar) <= 9 else 5
        satir = 3 if sutun == 3 else math.ceil(len(self.adlar) / sutun)
        n = sutun * satir  # eksik yuvalar boş kart olarak çizilir
        ara_x, ara_y, top, alt = 24, 16, 134, Y - 40
        w = 320 if sutun == 3 else (G - 80 - (sutun - 1) * ara_x) // sutun
        h = min(230, (alt - top - (satir - 1) * ara_y) // satir)
        x0 = (G - (sutun * w + (sutun - 1) * ara_x)) // 2
        kutular = []
        for i in range(n):
            r, c = divmod(i, sutun)
            kx = x0 + c * (w + ara_x)
            ky = top + r * (h + ara_y)
            kutular.append((kx, ky, kx + w, ky + h))
        return kutular

    def isle(self, kare: np.ndarray, algi: Any, simdi: float, dt: float) -> Optional[int]:
        """Seçim tamamlanırsa global kart indeksini döndürür."""
        cv2.addWeighted(kare, 0.45, np.zeros_like(kare), 0.55, 0, dst=kare)
        if self.giris_t <= 0.0:
            self.giris_t = simdi
        self.imlecler = []
        for el in algi.eller or []:
            try:
                self.imlecler.append(px(el, 9))
            except Exception:
                pass
        kartlar = self.kartlar()
        hedef = None
        for ix, iy in self.imlecler:
            for local_i in range(len(kartlar)):
                global_i = local_i
                if global_i >= len(self.adlar):
                    continue
                x0, y0, x1, y1 = kartlar[local_i]
                if x0 <= ix <= x1 and y0 <= iy <= y1 and global_i not in self.kapali:
                    hedef = global_i
                    break
            if hedef is not None:
                break
        if hedef is not None and hedef == self.uzerinde:
            self.sure += dt
        else:
            self.uzerinde, self.sure = hedef, 0.0

        az = _az_hareket()
        yazi_koy(kare, "BİR OYUN SEÇ", G // 2, 38, 42, renk=SARI, hiza="orta",
                 olcek=1.0 if az else (1.0 + 0.03 * math.sin(simdi * 3.0)))
        yazi_koy(kare, "1-9 ile seç veya elini kartın üstünde tut", G // 2, 92, 20, renk=BEYAZ, hiza="orta")

        w_card = kartlar[0][2] - kartlar[0][0]
        for local_i, (x0, y0, x1, y1) in enumerate(kartlar):
            global_i = local_i
            h_kart = y1 - y0
            ikon_y, ikon_boy = int(h_kart * 0.40), int(min(x1 - x0, h_kart) * 0.38)
            if not az:
                stagger = local_i * 0.025
                dt_giris = max(0.0, simdi - self.giris_t - stagger)
                t_giris = min(1.0, dt_giris / 0.22)
                ease = 1.0 - (1.0 - t_giris) ** 3
                giris_dy = int(10 * (1.0 - ease))
                bob = 0 if global_i in self.kapali else int(6 * math.sin(simdi * 2.0 + local_i * 0.9))
                yuk = bob + giris_dy
            else:
                yuk = 0

            if global_i < len(self.adlar):
                secili = global_i == self.uzerinde
                progress = min(1.0, self.sure / SECIM_SN) if secili else 0.0
                renk = RENKLER[global_i % len(RENKLER)]
                if global_i in self.kapali:
                    renk = tuple(int(c * 0.3) for c in renk)
                buyu = 0 if az else (int(3 + 3 * progress) if secili else 0)
                panel(kare, x0 - buyu, y0 + yuk - buyu, x1 + buyu, y1 + yuk + buyu, renk=(22, 18, 30), opak=0.86 if secili else 0.82)
                cv2.rectangle(kare, (x0 - buyu, y0 + yuk - buyu), (x1 + buyu, y1 + yuk + buyu),
                              YESIL if secili else renk, 4 if secili else 2, cv2.LINE_AA)
                cx = (x0 + x1) // 2
                if local_i < 9:
                    yazi_koy(kare, str(local_i + 1), cx, y0 + yuk + 5, 18, renk=renk, hiza="orta")
                if global_i not in self.kapali:
                    bindir_merkez(kare, self.ikonlar[global_i], cx, y0 + yuk + ikon_y, boyut=ikon_boy)
                else:  # soluk ikon + "KAPALI" etiketi: kart görünür ama seçilemez
                    bindir_merkez(kare, self._soluk_ikon(global_i), cx, y0 + yuk + ikon_y, boyut=ikon_boy)
                    yazi_koy(kare, "KAPALI", x1 - 46, y0 + yuk + 8, 16, renk=(150, 150, 160), hiza="orta")
                satirlar = self.adlar[global_i].split(" ", 1)
                if len(satirlar) > 1:
                    yazi_koy(kare, satirlar[0], cx, y1 + yuk - 56, 20, renk=renk, hiza="orta")
                    yazi_koy(kare, satirlar[1], cx, y1 + yuk - 32, 20, renk=renk, hiza="orta")
                else:
                    yazi_koy(kare, satirlar[0], cx, y1 + yuk - 46, 20, renk=renk, hiza="orta")
                if secili:
                    ck.halka(kare, cx, y0 + yuk + ikon_y, progress, r=ikon_boy * 5 // 8, renk=YESIL, kalinlik=4)
                    bar_w = int((w_card - 28) * progress)
                    if bar_w > 0:
                        cv2.line(kare, (x0 - buyu + 14, y1 + yuk + buyu - 5),
                                 (x0 - buyu + 14 + bar_w, y1 + yuk + buyu - 5), YESIL, 3, cv2.LINE_AA)
                    if not az:
                        parlaklik = int(30 * (1.0 + math.sin(simdi * 8.0)))
                        cv2.rectangle(kare, (x0 - buyu - 1, y0 + yuk - buyu - 1), (x1 + buyu + 1, y1 + yuk + buyu + 1),
                                      (0, min(255, 200 + parlaklik), 0), 1, cv2.LINE_AA)
            else:
                panel(kare, x0, y0, x1, y1, renk=(16, 14, 22), opak=0.4)
                cv2.rectangle(kare, (x0, y0), (x1, y1), (45, 40, 55), 1, cv2.LINE_AA)

        for ix, iy in self.imlecler:
            cv2.circle(kare, (int(ix), int(iy)), 20, CAMGOBEGI, 3, cv2.LINE_AA)
            cv2.circle(kare, (int(ix), int(iy)), 7, BEYAZ, -1, cv2.LINE_AA)
        if self.uzerinde is not None and self.sure >= SECIM_SN:
            secim, self.uzerinde, self.sure = self.uzerinde, None, 0.0
            return secim
        return None


# ---------------------------------------------------------------- uygulama mantığı (kamerasız test edilebilir)
class StantUygulama:
    def __init__(self, ses: Any, moduller: Optional[List[Any]] = None):
        self.ses = ses
        self.kapi = OyuncuKapisi()
        self.moduller = moduller or [importlib.import_module(ad) for ad in DENEYIMLER]
        self.ornekler: Dict[int, Any] = {}
        self.etkin: Optional[int] = None  # None = ana menü
        self.gecis_t = -10.0
        self.son_kisi_t = 0.0
        self.ev_sure = 0.0
        self.onceki_t: Optional[float] = None
        self.cokmeler: Dict[int, List[float]] = {}
        self.dinlenme_t = -10.0
        self.parmak_izler: List[list] = []
        adlar = [getattr(getattr(m, "Prototip", None), "AD", getattr(m, "__name__", f"Oyun {i + 1}"))
                 for i, m in enumerate(self.moduller)]
        maske = self._ornek(DENEYIMLER.index("p_maske")) if "p_maske" in DENEYIMLER and len(self.moduller) > DENEYIMLER.index("p_maske") else None
        ciz = {
            "p_neon_kilic": ikon_kilic,
            "p_gulmeme": ikon_gulme,
            "p_parmak_kusu": ikon_kus,
            "p_cevap_yagmuru": ikon_yagmur,
            "p_refleks": ikon_duello,
            "p_tas_kagit": ikon_tkm,
            "p_hayalet_klon": ikon_hayalet_klon,
            "p_penalti": ikon_penalti,
            "p_ciz_tahmin": ikon_ciz,
        }
        ikonlar = []
        for i, m in enumerate(self.moduller):
            ad = getattr(m, "__name__", "")
            if ad == "p_maske" and maske and hasattr(maske, "_ikon_hazirla"):
                ikonlar.append(maske._ikon_hazirla()[0])
            elif ad in ciz:
                ikonlar.append(ciz[ad]())
            else:  # tanımsız modül (testlerdeki sahte modüller): numaralı yedek
                img, isik = _tuval()
                yazi_koy(isik, str(i + 1), 100, 40, 95, renk=RENKLER[i % len(RENKLER)], hiza="orta")
                ikonlar.append(_bgra(img, isik))
        self.kapali = {i for i, m in enumerate(self.moduller) if getattr(m, "__name__", "") in KAPALI}
        self.menu = AnaMenu(adlar, ikonlar, self.kapali)

    def _ornek(self, i: int) -> Any:
        if i not in self.ornekler:
            self.ornekler[i] = self.moduller[i].Prototip(self.ses)
        return self.ornekler[i]

    def _poz_yalniz(self, i: Optional[int]) -> bool:
        if i is None or i >= len(self.moduller):
            return False
        mod = self.moduller[i]
        proto_cls = getattr(mod, "Prototip", None)
        ad = getattr(mod, "__name__", "")
        return bool(getattr(mod, "POZ_YALNIZ", False) or getattr(proto_cls, "POZ_YALNIZ", False))

    @property
    def ihtiyac(self) -> set:
        if self.etkin is None:
            return {"el", "yuz"}
        mod = self.moduller[self.etkin]
        proto_cls = getattr(mod, "Prototip", None)
        if self._poz_yalniz(self.etkin):
            return set(getattr(proto_cls, "IHTIYAC", {"poz"}))
        return set(getattr(proto_cls, "IHTIYAC", set())) | {"el", "yuz"}

    def sec(self, i: Optional[int], simdi: float) -> None:
        if i is not None and i in self.kapali:
            return
        self.etkin = i
        self.gecis_t = simdi
        self.son_kisi_t = simdi
        self.ev_sure = 0.0
        # Oyun açma ve menüye dönüşte ses yok (Enes 2026-10-15)

    def isle(self, kare: np.ndarray, algi: Any, simdi: float) -> np.ndarray:
        kare = self._isle_ic(kare, algi, simdi)
        _kisayollar(kare)
        return kare

    def _isle_ic(self, kare: np.ndarray, algi: Any, simdi: float) -> np.ndarray:
        dt = 0.033 if self.onceki_t is None else min(max(simdi - self.onceki_t, 0.0), 0.1)
        self.onceki_t = simdi
        kural = getattr(self._ornek(self.etkin), "KAPI", {}) if self.etkin is not None else {}
        ham_kisi = bool(getattr(algi, "yuzler", None) or getattr(algi, "eller", None) or getattr(algi, "pozlar", None))
        algi = self.kapi.suz(algi, simdi, kural)
        kisi_var = ham_kisi or bool(getattr(algi, "yuzler", None) or getattr(algi, "eller", None) or getattr(algi, "pozlar", None))
        if kisi_var:
            self.son_kisi_t = simdi

        if self.etkin is None:
            secim = self.menu.isle(kare, algi, simdi, dt)
            if secim is not None:
                self.sec(secim, simdi)
            if simdi - self.dinlenme_t < 2:
                panel(kare, 340, 310, 940, 390, opak=.95)
                yazi_koy(kare, 'Bu oyun dinleniyor', G // 2, 325, 36, renk=SARI, hiza='orta')
            return kare

        proto = self._ornek(self.etkin)
        oyunda = getattr(proto, "durum", "") == "oyun"
        poz_yalniz = self._poz_yalniz(self.etkin)
        poz_var = bool(getattr(algi, "pozlar", None))
        if not oyunda and not (poz_yalniz and poz_var) and simdi - self.son_kisi_t > BOS_DONUS_SN:
            self.sec(None, simdi)
            self.menu.isle(kare, algi, simdi, dt)
            return kare
        try:
            kare = proto.isle(kare, algi, simdi)
        except Exception as e:
            self.hata(e, simdi)
            return kare
        if (getattr(self.moduller[self.etkin], "__name__", "") not in KENDI_IMLECI
                and not getattr(proto, "KENDI_IMLECI", False)):
            parmak_izi(kare, algi, self.parmak_izler, simdi)
        self._ev_dugmesi(kare, algi, simdi, dt)
        self._gecis_karti(kare, proto, simdi)
        return kare

    def hata(self, e: Exception, simdi: float) -> None:
        import gezgin
        gezgin.hata_kaydet(e)
        i = self.etkin
        if i is None:
            return
        once = [t for t in self.cokmeler.get(i, []) if simdi - t <= 10]
        self.cokmeler[i] = once + [simdi]
        self.ornekler.pop(i, None)
        if len(self.cokmeler[i]) >= 3:
            self.dinlenme_t = simdi
            self.sec(None, simdi)
        else:
            self.gecis_t = simdi

    def _ev_dugmesi(self, kare: np.ndarray, algi: Any, simdi: float, dt: float) -> None:
        """Sol alt köşeye avuç ya da pozlu oyunda bilek: menü."""
        icinde = False
        poz_yalniz = self._poz_yalniz(self.etkin)
        if poz_yalniz:
            for poz in getattr(algi, "pozlar", []) or []:
                for b_idx in (15, 16):
                    try:
                        bx, by = px(poz, b_idx)
                        if bx < 170 and by > Y - 170:
                            icinde = True
                            break
                    except Exception:
                        continue
                if icinde:
                    break
        else:
            for el, jest in zip(algi.eller or [], (algi.jestler or []) + [None] * 4):
                try:
                    ex, ey = px(el, 9)
                except Exception:
                    continue
                if ex < 170 and ey > Y - 170 and jest == "Open_Palm":
                    icinde = True
                    break
        self.ev_sure = self.ev_sure + dt if icinde else 0.0
        if icinde:
            panel(kare, 20, Y - 150, 150, Y - 20, renk=(20, 18, 30), opak=0.6)
            ck.halka(kare, 85, Y - 85, min(1.0, self.ev_sure / EV_SN), r=48, renk=SARI, kalinlik=7)
            yazi_koy(kare, "MENÜ", 85, Y - 100, 26, renk=BEYAZ, hiza="orta")
        if self.ev_sure >= EV_SN:
            self.sec(None, simdi)

    def _gecis_karti(self, kare: np.ndarray, proto: Any, simdi: float) -> None:
        gecen = simdi - self.gecis_t
        if not 0.0 <= gecen < 1.7:
            return
        az = _az_hareket()
        opak = min(1.0, (1.7 - gecen) / 0.4)
        kayma = 0 if az else int(60 * max(0.0, 1.0 - gecen / 0.35) ** 2)
        y0 = Y // 2 - 80 + kayma
        panel(kare, 0, y0, G, y0 + 160, renk=(14, 12, 22), opak=0.8 * opak)
        renk = RENKLER[self.etkin % len(RENKLER)] if self.etkin is not None else SARI
        cv2.line(kare, (0, y0), (G, y0), renk, 3, cv2.LINE_AA)
        cv2.line(kare, (0, y0 + 160), (G, y0 + 160), renk, 3, cv2.LINE_AA)
        if opak > 0.3:
            yazi_koy(kare, getattr(proto, "AD", ""), G // 2, y0 + 18, 62, renk=renk, hiza="orta")
            yazi_koy(kare, getattr(proto, "ACIKLAMA", ""), G // 2, y0 + 104, 26, renk=BEYAZ, hiza="orta")

    def tus(self, k: int, simdi: float) -> bool:
        """Uygulama tuşu ise True; değilse etkin deneyime aktarılır."""
        if self.etkin is not None:
            if k in (ord("m"), ord("M")):
                self.sec(None, simdi)
                return True
            if k in (ord("n"), ord("N"), ord("b"), ord("B")):
                adim = 1 if k in (ord("n"), ord("N")) else -1
                i = self.etkin
                for _ in range(len(self.moduller)):
                    i = (i + adim) % len(self.moduller)
                    if i not in self.kapali:
                        break
                self.sec(i, simdi)
                return True
            proto = self._ornek(self.etkin)
            poz_yalniz = self._poz_yalniz(self.etkin)
            if poz_yalniz and k in (ord("3"), ord("4"), ord("5"), 32) and hasattr(proto, "tus"):
                proto.tus(k)
                return True
            if ord("1") <= k <= ord("9"):
                idx = k - ord("1")
                if idx < len(self.moduller):
                    self.sec(idx, simdi)
                return True
            if hasattr(proto, "tus"):
                proto.tus(k)
                return True
            return False
        else:
            if ord("1") <= k <= ord("9"):
                local_idx = k - ord("1")
                if local_idx < len(self.moduller):
                    self.sec(local_idx, simdi)
                return True
            if k in (ord("m"), ord("M")):
                self.sec(None, simdi)
                return True
            return False


class AlgiIscisi(threading.Thread):
    """Algılamayı çizim döngüsünden ayırır: döngü her kareyi hemen çizer, en son algı sonucunu kullanır
    (algı en fazla bir kare geride). ASENKRON_ALGI=0 ile eski seri davranış."""

    def __init__(self, alg: ck.Algilayici):
        super().__init__(daemon=True)
        self.alg, self.son = alg, ck.Algi()
        self._is: Optional[Tuple[np.ndarray, set]] = None
        self._olay = threading.Event()

    def ver(self, kare: np.ndarray, ihtiyac: set) -> None:
        self._is = (kare, set(ihtiyac))
        self._olay.set()

    def run(self) -> None:
        while True:
            self._olay.wait()
            self._olay.clear()
            kare, ihtiyac = self._is
            try:
                self.son = self.alg.algila(kare, ihtiyac)
            except Exception:  # algı hatası çizimi durdurmasın
                self.son = ck.Algi()


def main() -> None:
    kam = ck.Kamera(os.environ.get("KAMERA", "0"))
    kam.start()
    alg = ck.Algilayici()
    isci = AlgiIscisi(alg) if os.environ.get("ASENKRON_ALGI", "1") == "1" else None
    if isci:
        isci.start()
    son_kare_t = 0.0
    uyg = StantUygulama(ck.Ses(acik=True))
    pencere = "Stant"
    cv2.namedWindow(pencere, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(pencere, G, Y)
    tam = os.environ.get("TAM_EKRAN") == "1"
    if tam:
        cv2.setWindowProperty(pencere, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    olc = os.environ.get("FPS_LOG") == "1"  # 2 sn'de bir döngü FPS'i ve aşama süreleri (ms)
    o_t, o_n, o_alg, o_isle, o_goster = time.time(), 0, 0.0, 0.0, 0.0
    try:
        while True:
            if olc and time.time() - o_t >= 2 and o_n:
                print(f"FPS {o_n / (time.time() - o_t):.1f} algila {o_alg / o_n * 1000:.0f}ms "
                      f"isle {o_isle / o_n * 1000:.0f}ms goster {o_goster / o_n * 1000:.0f}ms "
                      f"ihtiyac {sorted(uyg.ihtiyac)} yuz {len(algi.yuzler)} el {len(algi.eller)} "
                      f"poz {len(algi.pozlar)}", flush=True)
                o_t, o_n, o_alg, o_isle, o_goster = time.time(), 0, 0.0, 0.0, 0.0
            kamera_bekle = (kam.kare is None) or (
                hasattr(kam, "bagli")
                and (not getattr(kam, "bagli", True) or (time.time() - getattr(kam, "t_son", 0.0) > 1.0))
            )
            if kamera_bekle:
                siyah = np.zeros((Y, G, 3), dtype=np.uint8)
                ck.yazi_koy(siyah, "Kamera bekleniyor", G // 2, Y // 2, 36, renk=BEYAZ, hiza="orta")
                cv2.imshow(pencere, siyah)
                k = cv2.waitKey(10) & 0xFF
                if k in (ord("q"), ord("Q"), 27) or cv2.getWindowProperty(pencere, cv2.WND_PROP_VISIBLE) < 1:
                    break
                continue
            if isci and kam.t_son == son_kare_t:  # yeni kamera karesi yok: aynı kareyi yeniden işleme
                if ((cv2.waitKey(2) & 0xFF) in (ord("q"), ord("Q"), 27)
                        or cv2.getWindowProperty(pencere, cv2.WND_PROP_VISIBLE) < 1):
                    break
                continue
            son_kare_t = kam.t_son
            kare = kam.kare.copy()
            simdi = time.time()
            try:
                t1 = time.perf_counter()
                if isci:
                    isci.ver(kare.copy(), uyg.ihtiyac)
                    algi = isci.son
                else:
                    algi = alg.algila(kare, uyg.ihtiyac)
                t2 = time.perf_counter()
                kare = uyg.isle(kare, algi, simdi)
                o_alg, o_isle = o_alg + t2 - t1, o_isle + time.perf_counter() - t2
            except Exception as e:
                uyg.hata(e, simdi)
            t3 = time.perf_counter()
            cv2.imshow(pencere, kare)
            k = cv2.waitKey(1) & 0xFF
            o_goster, o_n = o_goster + time.perf_counter() - t3, o_n + 1
            if k in (ord("q"), ord("Q"), 27):
                break
            if k in (ord("f"), ord("F")):
                tam = not tam
                cv2.setWindowProperty(pencere, cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN if tam else cv2.WINDOW_NORMAL)
            elif k != 255:
                uyg.tus(k, simdi)
            if cv2.getWindowProperty(pencere, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        kam.kapat()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
    os._exit(0)  # arka plan algı/kamera iş parçacıkları süreci açık tutmasın (pencere kapandı = süreç biter)
