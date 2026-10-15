"""AR maskeler ve oyunlar için emoji yerine prosedürel, ışıklı aksesuar sprite'ları (BGRA).

meyve_ciz'deki kubbe ışığı / yumuşak kenar hattını kullanır: taç, kalp, çiçek, yaprak, kelebek kareleri,
bal damlası, kafatası, parıltı ve bomba.
"""
from __future__ import annotations

import math
from functools import lru_cache
from typing import List, Tuple

import cv2
import numpy as np

from meyve_ciz import AA, C, N, _bitir, _boya, _gurultu, _hacim, _icine, _m, _r, _tuval, _uzaklik


def _yumusat(m: np.ndarray, s: float = 3.0) -> np.ndarray:
    return np.clip((cv2.GaussianBlur(m, (0, 0), s) - 0.5) * 5 + 0.5, 0, 1)


def _kalp_sil(cx: float, cy: float, r: float) -> np.ndarray:
    m = _m()
    cv2.circle(m, (int(cx - r * 0.5), int(cy - r * 0.25)), int(r * 0.56), 1.0, -1, AA)
    cv2.circle(m, (int(cx + r * 0.5), int(cy - r * 0.25)), int(r * 0.56), 1.0, -1, AA)
    p = np.array([[cx - r * 1.03, cy - r * 0.05], [cx + r * 1.03, cy - r * 0.05], [cx, cy + r * 1.05]], np.int32)
    cv2.fillPoly(m, [p], 1.0, AA)
    return _yumusat(m, 4)


@lru_cache(maxsize=8)
def kalp(boy: int = 160, renk: Tuple[int, int, int] = (55, 35, 235)) -> np.ndarray:
    sil = _kalp_sil(C, C + 4, 100)
    img = _tuval(_r(*renk))
    d = _uzaklik(sil)
    _boya(img, np.clip(1.0 - d * 2.5, 0, 1), _r(*renk) * 0.55, 0.6)
    _hacim(img, sil, parlak=1.0, sert=46, taban=0.55)
    isik = _m()
    cv2.ellipse(isik, (C - 48, C - 40), (22, 12), -35, 0, 360, 1.0, -1, AA)
    _boya(img, cv2.GaussianBlur(isik, (0, 0), 3), np.array((1, 1, 1), np.float32), 0.75)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def tac(boy: int = 256) -> np.ndarray:
    sil = _m()
    cv2.rectangle(sil, (C - 104, C + 22), (C + 104, C + 74), 1.0, -1)
    uclar = [(-104, -54), (-52, -82), (0, -100), (52, -82), (104, -54)]
    taban_x = [-104, -78, -52, -26, 0, 26, 52, 78, 104]
    p = [(C - 104, C + 30)]
    for i, (ux, uy) in enumerate(uclar):
        p.append((C + ux, C + uy))
        if i < len(uclar) - 1:
            p.append((C + taban_x[2 * i + 1], C - 6))
    p.append((C + 104, C + 30))
    cv2.fillPoly(sil, [np.array(p, np.int32)], 1.0, AA)
    for ux, uy in uclar:
        cv2.circle(sil, (C + ux, C + uy - 4), 13, 1.0, -1, AA)
    sil = _yumusat(sil, 1.5)
    img = _tuval(_r(30, 175, 245))
    img *= (0.85 + 0.25 * _gurultu(10, 3))[..., None]
    bant = _m()
    cv2.rectangle(bant, (C - 104, C + 22), (C + 104, C + 74), 1.0, -1)
    _boya(img, cv2.GaussianBlur(bant, (0, 0), 2) * 0.35, _r(20, 120, 200))
    _hacim(img, sil, parlak=1.1, sert=30, taban=0.45)
    for k, (gx, renk) in enumerate(((-62, (60, 30, 210)), (0, (200, 80, 30)), (62, (70, 170, 40)))):
        tas = _m()
        cv2.ellipse(tas, (C + gx, C + 48), (17 if k != 1 else 21, 15), 0, 0, 360, 1.0, -1, AA)
        timg = _tuval(_r(*renk))
        _hacim(timg, tas, parlak=1.3, sert=50, taban=0.5)
        _boya(img, tas, 0.0)
        img += timg * tas[..., None]
    for ux, uy in uclar:
        inci = _m()
        cv2.circle(inci, (C + ux, C + uy - 4), 11, 1.0, -1, AA)
        iimg = _tuval(_r(235, 235, 245))
        _hacim(iimg, inci, parlak=1.0, sert=40, taban=0.55)
        _boya(img, inci, 0.0)
        img += iimg * inci[..., None]
    return _bitir(img, sil, boy)


@lru_cache(maxsize=16)
def cicek(boy: int = 160, yaprak: Tuple[int, int, int] = (190, 120, 250),
          orta: Tuple[int, int, int] = (40, 200, 255), adet: int = 5) -> np.ndarray:
    sil = _m()
    img = _tuval(_r(*yaprak))
    for i in range(adet):
        a = -math.pi / 2 + 2 * math.pi * i / adet
        pm = _m()
        cv2.ellipse(pm, (int(C + 58 * math.cos(a)), int(C + 58 * math.sin(a))), (62, 44),
                    math.degrees(a), 0, 360, 1.0, -1, AA)
        pm = _yumusat(pm, 2)
        pimg = _tuval(_r(*yaprak))
        d = _uzaklik(pm)
        _boya(pimg, np.clip(1.0 - d * 2.2, 0, 1), np.minimum(_r(*yaprak) * 1.25 + 0.1, 1.0), 0.6)
        _hacim(pimg, pm, parlak=0.35, sert=18, taban=0.6)
        cizgi = _m()
        cv2.line(cizgi, (C, C), (int(C + 90 * math.cos(a)), int(C + 90 * math.sin(a))), 1.0, 3, AA)
        _boya(pimg, cv2.GaussianBlur(cizgi, (0, 0), 2) * pm, _r(*yaprak) * 0.7, 0.5)
        _boya(img, pm, 0.0)
        img += pimg * pm[..., None]
        sil = np.maximum(sil, pm)
    om = _m()
    cv2.circle(om, (C, C), 34, 1.0, -1, AA)
    oimg = _tuval(_r(*orta))
    rng = np.random.default_rng(adet)
    nokta = _m()
    for _ in range(40):
        a, r = rng.uniform(0, 2 * math.pi), math.sqrt(rng.uniform()) * 28
        cv2.circle(nokta, (int(C + r * math.cos(a)), int(C + r * math.sin(a))), 3, 1.0, -1, AA)
    _boya(oimg, nokta, _r(*orta) * 0.6, 0.7)
    _hacim(oimg, om, parlak=0.6, sert=24, taban=0.5)
    _boya(img, om, 0.0)
    img += oimg * om[..., None]
    sil = np.maximum(sil, om)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def yaprak(boy: int = 110) -> np.ndarray:
    sil = _m()
    cv2.ellipse(sil, (C, C), (100, 44), -30, 0, 360, 1.0, -1, AA)
    sil = _yumusat(sil, 3)
    img = _tuval(_r(60, 170, 60))
    damar = _m()
    cv2.line(damar, (C - 86, C + 50), (C + 86, C - 50), 1.0, 4, AA)
    for k in (-50, -10, 30):
        x0, y0 = C + k, C - int(k * 0.58)
        cv2.line(damar, (x0, y0), (x0 + 22, y0 + 30), 1.0, 2, AA)
        cv2.line(damar, (x0, y0), (x0 - 30, y0 - 18), 1.0, 2, AA)
    _boya(img, cv2.GaussianBlur(damar, (0, 0), 1) * _icine(sil, 3), _r(140, 230, 150), 0.6)
    _hacim(img, sil, parlak=0.6, sert=26, taban=0.5)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=4)
def kelebek_kareleri(boy: int = 120, renk: Tuple[int, int, int] = (30, 140, 255)) -> List[np.ndarray]:
    """Kanat çırpma döngüsü için 6 kare (kanat genişliği %100 → %25)."""
    sil = _m()
    img = _tuval(_r(*renk))
    for isaret in (-1, 1):
        for (ox, oy, ax, ay, ang) in ((58, -34, 62, 46, -25), (44, 42, 40, 32, 30)):
            km = _m()
            cv2.ellipse(km, (C + isaret * ox, C + oy), (ax, ay), isaret * ang, 0, 360, 1.0, -1, AA)
            km = _yumusat(km, 2)
            kimg = _tuval(_r(*renk))
            d = _uzaklik(km)
            _boya(kimg, np.clip(d * 2.4 - 0.4, 0, 1), np.minimum(_r(*renk) * 1.3 + 0.15, 1.0), 0.8)
            kenar = np.clip(km - _icine(km, 7), 0, 1)
            _boya(kimg, kenar, _r(25, 20, 30))
            nokta = _m()
            cv2.circle(nokta, (C + isaret * (ox + ax // 2), C + oy - ay // 3), 6, 1.0, -1, AA)
            cv2.circle(nokta, (C + isaret * (ox + ax // 3), C + oy + ay // 4), 4, 1.0, -1, AA)
            _boya(kimg, nokta * km, np.array((1, 1, 1), np.float32))
            _hacim(kimg, km, parlak=0.4, sert=20, taban=0.65)
            _boya(img, km, 0.0)
            img += kimg * km[..., None]
            sil = np.maximum(sil, km)
    govde = _m()
    cv2.ellipse(govde, (C, C + 4), (9, 62), 0, 0, 360, 1.0, -1, AA)
    for isaret in (-1, 1):
        cv2.line(govde, (C, C - 54), (C + isaret * 30, C - 100), 1.0, 3, AA)
        cv2.circle(govde, (C + isaret * 30, C - 100), 5, 1.0, -1, AA)
    gimg = _tuval(_r(30, 25, 35))
    _hacim(gimg, govde, parlak=0.5, sert=24, taban=0.6)
    _boya(img, govde, 0.0)
    img += gimg * govde[..., None]
    sil = np.maximum(sil, govde)
    tam = _bitir(img, sil, boy)
    kareler = []
    for o in (1.0, 0.82, 0.58, 0.34, 0.58, 0.82):
        w = max(4, int(boy * o))
        k = np.zeros_like(tam)
        ez = cv2.resize(tam, (w, boy), interpolation=cv2.INTER_AREA)
        x0 = (boy - w) // 2
        k[:, x0:x0 + w] = ez
        kareler.append(k)
    return kareler


@lru_cache(maxsize=2)
def bal_damlasi(boy: int = 70) -> np.ndarray:
    sil = _m()
    cv2.circle(sil, (C, C + 30), 70, 1.0, -1, AA)
    cv2.fillPoly(sil, [np.array([[C - 62, C + 6], [C + 62, C + 6], [C, C - 110]], np.int32)], 1.0, AA)
    sil = _yumusat(sil, 4)
    img = _tuval(_r(20, 150, 235))
    d = _uzaklik(sil)
    _boya(img, np.clip(d * 1.6 - 0.3, 0, 1), _r(90, 215, 255), 0.7)
    _hacim(img, sil, parlak=1.2, sert=50, taban=0.6)
    return _bitir(img, sil * 0.92, boy)


@lru_cache(maxsize=2)
def kafatasi(boy: int = 128) -> np.ndarray:
    sil = _m()
    cv2.circle(sil, (C, C - 18), 86, 1.0, -1, AA)
    cv2.rectangle(sil, (C - 50, C + 30), (C + 50, C + 100), 1.0, -1)
    sil = _yumusat(sil, 5)
    img = _tuval(_r(225, 235, 240))
    delik = _m()
    for isaret in (-1, 1):
        cv2.ellipse(delik, (C + isaret * 36, C - 4), (26, 30), isaret * 10, 0, 360, 1.0, -1, AA)
    cv2.fillPoly(delik, [np.array([[C - 10, C + 40], [C + 10, C + 40], [C, C + 20]], np.int32)], 1.0, AA)
    for k in (-30, -10, 10, 30):
        cv2.line(delik, (C + k, C + 76), (C + k, C + 100), 1.0, 4, AA)
    _hacim(img, sil, parlak=0.6, sert=24, taban=0.5)
    _boya(img, cv2.GaussianBlur(delik, (0, 0), 1.5), _r(30, 25, 30))
    return _bitir(img, sil, boy)


@lru_cache(maxsize=4)
def parilti(boy: int = 64, renk: Tuple[int, int, int] = (200, 245, 255)) -> np.ndarray:
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) - C
    ax, ay = np.abs(xx) / C, np.abs(yy) / C
    yildiz = np.clip(1.0 - (np.sqrt(ax) + np.sqrt(ay)), 0, 1) ** 0.6
    hale = np.exp(-(xx * xx + yy * yy) / (2 * (C * 0.22) ** 2)) * 0.7
    a = np.clip(yildiz * 1.6 + hale, 0, 1)
    img = _tuval(_r(*renk))
    _boya(img, np.clip(yildiz * 2 - 0.6, 0, 1), np.array((1, 1, 1), np.float32))
    return _bitir(img, a, boy, golge=False)


@lru_cache(maxsize=2)
def bomba(boy: int = 120) -> np.ndarray:
    sil = _m()
    cv2.circle(sil, (C - 6, C + 18), 88, 1.0, -1, AA)
    kapak = _m()
    cv2.rectangle(kapak, (C + 22, C - 92), (C + 64, C - 56), 1.0, -1)
    kapak = _yumusat(cv2.warpAffine(kapak, cv2.getRotationMatrix2D((C + 43, C - 74), -35, 1.0), (N, N)), 1)
    fitil = _m()
    t = np.linspace(0, 1, 30)
    cv2.polylines(fitil, [np.stack([C + 58 + 40 * t, C - 92 - 20 * np.sin(t * 3)], 1).astype(np.int32)],
                  False, 1.0, 6, AA)
    img = _tuval(_r(45, 40, 50))
    _hacim(img, sil, parlak=1.2, sert=40, taban=0.35)
    kimg = _tuval(_r(110, 110, 120))
    _hacim(kimg, kapak, parlak=0.6, sert=20, taban=0.5)
    _boya(img, kapak, 0.0)
    img += kimg * kapak[..., None]
    _boya(img, fitil, _r(80, 150, 200))
    kivilcim = _m()
    cv2.circle(kivilcim, (C + 100, C - 108), 14, 1.0, -1, AA)
    kv = cv2.GaussianBlur(kivilcim, (0, 0), 5) * 1.8
    _boya(img, np.clip(kv, 0, 1), _r(80, 220, 255))
    sil = np.clip(np.maximum.reduce([sil, kapak, fitil, np.clip(kv, 0, 1)]), 0, 1)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def kopek_kulak(boy: int = 256) -> np.ndarray:
    """Dikey sarkık kulak; üst ucu kafaya bağlanır."""
    sil = _m()
    cv2.ellipse(sil, (C, C - 10), (58, 112), 0, 0, 360, 1.0, -1, AA)
    cv2.circle(sil, (C, C + 52), 64, 1.0, -1, AA)
    sil = _yumusat(sil, 5)
    img = _tuval(_r(45, 90, 150))
    img *= (0.82 + 0.3 * _gurultu(40, 7) * _gurultu(8, 8))[..., None]
    ic = _m()
    cv2.ellipse(ic, (C, C + 18), (32, 86), 0, 0, 360, 1.0, -1, AA)
    _boya(img, cv2.GaussianBlur(ic, (0, 0), 8), _r(30, 55, 100), 0.75)
    _hacim(img, sil, parlak=0.25, sert=14, taban=0.5)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def kopek_burun(boy: int = 128) -> np.ndarray:
    sil = _m()
    cv2.ellipse(sil, (C, C - 10), (104, 64), 0, 0, 360, 1.0, -1, AA)
    cv2.ellipse(sil, (C, C + 30), (60, 50), 0, 0, 360, 1.0, -1, AA)
    sil = _yumusat(sil, 5)
    img = _tuval(_r(38, 32, 40))
    delik = _m()
    for isaret in (-1, 1):
        cv2.ellipse(delik, (C + isaret * 40, C + 6), (20, 12), isaret * 25, 0, 360, 1.0, -1, AA)
    _boya(img, cv2.GaussianBlur(delik, (0, 0), 3), _r(8, 8, 10))
    _hacim(img, sil, parlak=1.1, sert=36, taban=0.45)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def dil(boy: int = 256) -> np.ndarray:
    sil = _m()
    cv2.ellipse(sil, (C, C + 6), (66, 116), 0, 0, 360, 1.0, -1, AA)
    sil = _yumusat(sil, 3)
    img = _tuval(_r(125, 105, 240))
    oluk = _m()
    cv2.line(oluk, (C, C - 100), (C, C + 70), 1.0, 7, AA)
    _boya(img, cv2.GaussianBlur(oluk, (0, 0), 5), _r(90, 65, 200), 0.8)
    _hacim(img, sil, parlak=0.8, sert=34, taban=0.55)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def tavsan_kulak(boy: int = 256) -> np.ndarray:
    sil = _m()
    cv2.ellipse(sil, (C, C), (50, 120), 0, 0, 360, 1.0, -1, AA)
    sil = _yumusat(sil, 3)
    img = _tuval(_r(238, 236, 242))
    img *= (0.94 + 0.08 * _gurultu(30, 9))[..., None]
    ic = _m()
    cv2.ellipse(ic, (C, C + 10), (24, 92), 0, 0, 360, 1.0, -1, AA)
    _boya(img, cv2.GaussianBlur(ic, (0, 0), 6), _r(180, 160, 248), 0.95)
    _hacim(img, sil, parlak=0.3, sert=16, taban=0.6)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def tavsan_dis(boy: int = 96) -> np.ndarray:
    sil = _m()
    for isaret in (-1, 1):
        x0 = C + (4 if isaret > 0 else -76)
        cv2.rectangle(sil, (x0, C - 70), (x0 + 72, C + 60), 1.0, -1)
        cv2.circle(sil, (x0 + 36, C + 56), 36, 1.0, -1, AA)
    sil = _yumusat(sil, 3)
    img = _tuval(_r(240, 245, 250))
    _hacim(img, sil, parlak=0.8, sert=30, taban=0.65)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def pikselli_gozluk(blok: int = 16) -> np.ndarray:
    """'Deal with it' gözlüğü: 16x4 blok, keskin pikseller."""
    w, h = 16, 4
    a = np.zeros((h, w), np.uint8)
    beyaz = np.zeros((h, w), bool)
    a[0, :] = 1
    for c0, c1 in ((1, 6), (9, 14)):
        a[1:3, c0:c1 + 1] = 1
        a[3, c0 + 1:c1] = 1
    for r, c in ((1, 2), (2, 3), (1, 10), (2, 11)):
        beyaz[r, c] = True
    img = np.zeros((h, w, 4), np.uint8)
    img[a == 1] = (22, 22, 24, 255)
    img[beyaz] = (245, 245, 245, 255)
    return cv2.resize(img, (w * blok, h * blok), interpolation=cv2.INTER_NEAREST)


def _ayna(rgba: np.ndarray, ayna: bool) -> np.ndarray:
    return np.ascontiguousarray(rgba[:, ::-1]) if ayna else rgba


def _ekle(img: np.ndarray, sil: np.ndarray, parca_img: np.ndarray, parca: np.ndarray) -> np.ndarray:
    """Parçayı (kendi gölgelenmiş görüntüsüyle) ana görüntünün üstüne koyar, silüeti birleştirir."""
    _boya(img, parca, 0.0)
    img += parca_img * parca[..., None]
    return np.maximum(sil, parca)


@lru_cache(maxsize=4)
def kedi_kulak(boy: int = 256, ayna: bool = False) -> np.ndarray:
    """Sivri, tüylü kedi kulağı; taban altta, uç dışa yatık (ayna=True sağ kulak)."""
    sil = _m()
    cv2.fillPoly(sil, [np.array([[C - 98, C + 112], [C + 92, C + 112], [C + 30, C - 10], [C - 44, C - 114]], np.int32)],
                 1.0, AA)
    sil = _yumusat(sil, 4)
    img = _tuval(_r(70, 140, 235))
    img *= (0.84 + 0.30 * _gurultu(60, 11) * (0.7 + 0.3 * _gurultu(9, 12)))[..., None]
    serit = _m()
    for k, y in enumerate((C + 70, C + 34)):
        cv2.line(serit, (C - 90 + 14 * k, y), (C + 70 - 18 * k, y - 18), 1.0, 9, AA)
    _boya(img, cv2.GaussianBlur(serit, (0, 0), 4) * _icine(sil, 2), _r(30, 80, 170), 0.55)
    ic = _m()
    cv2.fillPoly(ic, [np.array([[C - 62, C + 104], [C + 56, C + 104], [C + 8, C + 8], [C - 38, C - 66]], np.int32)],
                 1.0, AA)
    ic = cv2.GaussianBlur(ic, (0, 0), 6)
    _boya(img, ic, _r(175, 150, 245), 0.95)
    _boya(img, np.clip(ic * 2 - 1.2, 0, 1), _r(140, 110, 225), 0.6)
    tuy = _m()
    for k, (x0, boy_t) in enumerate(((-40, 60), (-22, 84), (-4, 70), (14, 92), (32, 58))):
        uc = (C + x0 - 14 + k * 3, C + 108 - boy_t)
        cv2.ellipse(tuy, (uc[0] + 10, C + 108), (10, boy_t), 0, 180, 270, 1.0, 2, AA)
    _boya(img, cv2.GaussianBlur(tuy, (0, 0), 1.6), _r(250, 245, 250), 0.45)
    _hacim(img, sil, parlak=0.3, sert=16, taban=0.55)
    return _ayna(_bitir(img, sil, boy), ayna)


@lru_cache(maxsize=2)
def kedi_burun(boy: int = 128) -> np.ndarray:
    """Pembe kedi burnu + altında 'w' ağız çizgisi."""
    burun = _m()
    cv2.fillPoly(burun, [np.array([[C - 66, C - 62], [C + 66, C - 62], [C, C + 8]], np.int32)], 1.0, AA)
    burun = _yumusat(burun, 6)
    img = _tuval(_r(160, 120, 240))
    _hacim(img, burun, parlak=1.1, sert=40, taban=0.55)
    isik = _m()
    cv2.ellipse(isik, (C - 18, C - 44), (20, 9), -10, 0, 360, 1.0, -1, AA)
    _boya(img, cv2.GaussianBlur(isik, (0, 0), 3), np.array((1, 1, 1), np.float32), 0.8)
    agiz = _m()
    cv2.line(agiz, (C, C), (C, C + 52), 1.0, 9, AA)
    for isaret in (-1, 1):
        cv2.ellipse(agiz, (C + isaret * 34, C + 50), (34, 30), 0, 0, 180, 1.0, 9, AA)
    agiz = cv2.GaussianBlur(agiz, (0, 0), 1.2)
    _boya(img, agiz, _r(45, 35, 55))
    return _bitir(img, np.maximum(burun, agiz), boy)


@lru_cache(maxsize=4)
def seytan_boynuz(boy: int = 256, ayna: bool = False) -> np.ndarray:
    """Kıvrık, boğumlu, parlak kırmızı boynuz; taban altta, uç dışa ve yukarı."""
    us = np.linspace(0.0, 1.0, 40)
    mx = C + 24 - 92 * us ** 1.7 + 30 * np.sin(us * math.pi)
    my = C + 112 - 226 * us
    gx, gy = np.gradient(mx), np.gradient(my)
    n = np.hypot(gx, gy) + 1e-6
    nx, ny = -gy / n, gx / n
    w = 50 * (1 - us) ** 0.85 + 3
    sol = np.stack([mx + nx * w, my + ny * w], 1)
    sag = np.stack([mx - nx * w, my - ny * w], 1)
    sil = _m()
    cv2.fillPoly(sil, [np.concatenate([sol, sag[::-1]]).astype(np.int32)], 1.0, AA)
    sil = _yumusat(sil, 1.5)
    img = _tuval(_r(40, 40, 215))
    yy = np.mgrid[0:N, 0:N][0].astype(np.float32)
    uc = np.clip((C + 112 - yy) / 226.0, 0, 1)
    _boya(img, uc ** 2.2, _r(25, 15, 95), 0.85)
    bogum = _m()
    for k in range(1, 8):
        i = int(k / 9 * 39)
        cv2.line(bogum, tuple(sol[i].astype(int)), tuple(sag[i].astype(int)), 1.0, 3, AA)
    _boya(img, cv2.GaussianBlur(bogum, (0, 0), 2.0) * _icine(sil, 1), _r(20, 15, 110), 0.45)
    _hacim(img, sil, parlak=1.25, sert=44, taban=0.42)
    return _ayna(_bitir(img, sil, boy), ayna)


@lru_cache(maxsize=2)
def ayi_kulak(boy: int = 128) -> np.ndarray:
    sil = _m()
    cv2.circle(sil, (C, C), 104, 1.0, -1, AA)
    sil = _yumusat(sil, 4)
    img = _tuval(_r(45, 85, 140))
    img *= (0.82 + 0.3 * _gurultu(64, 21) * (0.7 + 0.3 * _gurultu(10, 22)))[..., None]
    ic = _m()
    cv2.ellipse(ic, (C, C + 12), (60, 54), 0, 0, 360, 1.0, -1, AA)
    _boya(img, cv2.GaussianBlur(ic, (0, 0), 4), _r(125, 150, 215), 1.0)
    _hacim(img, sil, parlak=0.3, sert=16, taban=0.5)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def ayi_agiz(boy: int = 192) -> np.ndarray:
    """Açık kahve ağız-burun çıkıntısı + parlak siyah burun."""
    sil = _m()
    cv2.ellipse(sil, (C, C + 6), (112, 80), 0, 0, 360, 1.0, -1, AA)
    sil = _yumusat(sil, 5)
    img = _tuval(_r(145, 185, 225))
    img *= (0.92 + 0.1 * _gurultu(48, 23))[..., None]
    _hacim(img, sil, parlak=0.35, sert=18, taban=0.62)
    cizgi = _m()
    cv2.line(cizgi, (C, C - 6), (C, C + 36), 1.0, 6, AA)
    for isaret in (-1, 1):
        cv2.ellipse(cizgi, (C + isaret * 26, C + 34), (26, 20), 0, 0, 180, 1.0, 6, AA)
    _boya(img, cv2.GaussianBlur(cizgi, (0, 0), 1.2), _r(50, 50, 70))
    burun = _m()
    cv2.ellipse(burun, (C, C - 30), (50, 32), 0, 0, 360, 1.0, -1, AA)
    burun = _yumusat(burun, 3)
    bimg = _tuval(_r(30, 28, 34))
    _hacim(bimg, burun, parlak=1.3, sert=46, taban=0.5)
    sil = _ekle(img, sil, bimg, burun)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def uzayli_goz(boy: int = 160) -> np.ndarray:
    """Büyük badem uzaylı gözü: koyu cam, yeşil kenar, iki parlama."""
    sil = _m()
    cv2.ellipse(sil, (C, C), (120, 70), 0, 0, 360, 1.0, -1, AA)
    sil = _yumusat(sil, 3)
    img = _tuval(_r(18, 34, 16))
    d = _uzaklik(sil)
    _boya(img, np.clip(1.0 - d * 3.0, 0, 1), _r(60, 200, 80), 0.75)
    _hacim(img, sil, parlak=1.5, sert=60, taban=0.6)
    isik = _m()
    cv2.ellipse(isik, (C - 54, C - 30), (26, 13), -20, 0, 360, 1.0, -1, AA)
    cv2.circle(isik, (C + 50, C + 22), 7, 1.0, -1, AA)
    _boya(img, cv2.GaussianBlur(isik, (0, 0), 2), np.array((1, 1, 1), np.float32), 0.9)
    return _bitir(img, sil, boy)


@lru_cache(maxsize=4)
def kure(boy: int = 96, renk: Tuple[int, int, int] = (70, 230, 100)) -> np.ndarray:
    sil = _m()
    cv2.circle(sil, (C, C), 100, 1.0, -1, AA)
    sil = _yumusat(sil, 2)
    img = _tuval(_r(*renk))
    _hacim(img, sil, parlak=1.4, sert=50, taban=0.5)
    return _bitir(img, sil, boy, golge=False)


@lru_cache(maxsize=2)
def korsan_sapka(boy: int = 256) -> np.ndarray:
    """Üç köşeli korsan şapkası, altın şerit kenarlı (kafatası ayrıca üstüne konur)."""
    sil = _m()
    cv2.ellipse(sil, (C, C + 34), (86, 104), 0, 180, 360, 1.0, -1, AA)  # tepe (kubbe)
    kanat = [(C - 126, C - 28), (C - 104, C + 22), (C - 56, C + 54), (C, C + 62), (C + 56, C + 54), (C + 104, C + 22),
             (C + 126, C - 28), (C + 92, C + 8), (C + 46, C + 24), (C, C + 28), (C - 46, C + 24), (C - 92, C + 8)]
    cv2.fillPoly(sil, [np.array(kanat, np.int32)], 1.0, AA)  # iki yanı kalkık kenar
    sil = _yumusat(sil, 2)
    img = _tuval(_r(30, 26, 34))
    img *= (0.85 + 0.25 * _gurultu(30, 31))[..., None]
    _hacim(img, sil, parlak=0.55, sert=26, taban=0.55)
    kenar = np.clip(sil - _icine(sil, 8), 0, 1)
    simg = _tuval(_r(40, 180, 240))
    _hacim(simg, sil, parlak=1.2, sert=36, taban=0.55)
    _boya(img, kenar, 0.0)
    img += simg * kenar[..., None]
    return _bitir(img, sil, boy)


@lru_cache(maxsize=2)
def goz_bandi(boy: int = 96) -> np.ndarray:
    sil = _m()
    cv2.ellipse(sil, (C, C), (112, 96), 0, 0, 360, 1.0, -1, AA)
    sil = _yumusat(sil, 3)
    img = _tuval(_r(22, 20, 26))
    dikis = np.clip(_icine(sil, 10) - _icine(sil, 13), 0, 1)
    _boya(img, dikis, _r(70, 70, 80), 0.8)
    _hacim(img, sil, parlak=0.8, sert=34, taban=0.6)
    return _bitir(img, sil, boy)


def kontakt(yol: str) -> None:
    sp = [tac(150), kalp(130), kalp(130, (150, 80, 245)), cicek(120), cicek(120, (60, 80, 245), (40, 220, 255)),
          cicek(120, (240, 240, 245)), yaprak(100), kelebek_kareleri(130)[0],
          kelebek_kareleri(130, (220, 120, 60))[2], bal_damlasi(90), kafatasi(120), parilti(90), bomba(130), kopek_kulak(140), kopek_burun(110), dil(130),
          tavsan_kulak(150), tavsan_dis(90), pikselli_gozluk(9), kedi_kulak(150), kedi_kulak(150, True),
          kedi_burun(120), seytan_boynuz(150), seytan_boynuz(150, True), ayi_kulak(120), ayi_agiz(140),
          uzayli_goz(140), kure(90), korsan_sapka(150), goz_bandi(100)]
    hucre = 160
    zemin = np.full((hucre, hucre * len(sp), 3), 70, np.uint8)
    for i, s in enumerate(sp):
        h, w = s.shape[:2]
        y0, x0 = (hucre - h) // 2, i * hucre + (hucre - w) // 2
        a = s[:, :, 3:4].astype(np.float32) / 255.0
        bolge = zemin[y0:y0 + h, x0:x0 + w].astype(np.float32)
        zemin[y0:y0 + h, x0:x0 + w] = (bolge * (1 - a) + s[:, :, :3] * a).astype(np.uint8)
    cv2.imwrite(yol, zemin)


if __name__ == "__main__":
    import sys
    kontakt(sys.argv[1] if len(sys.argv) > 1 else "aksesuar.png")
