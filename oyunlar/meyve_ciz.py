"""Neon Kılıç için prosedürel meyve sprite'ları ve meme çıkartmaları.

Her meyve 256 px tuvalde çizilir: taban renk + doku, uzaklık dönüşümünden türetilen kubbe normaliyle
yön ışığı ve parlama, yumuşak gölge; sonra INTER_AREA ile küçültülür (kenarlar pürüzsüz kalır).
Meyve başına iki görüntü üretilir: dış (bütün meyve) ve iç (kesince görünen kesit) + meyve suyu rengi.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

N = 256
C = N // 2
AA = cv2.LINE_AA


def _r(b: int, g: int, r: int) -> np.ndarray:
    return np.array((b, g, r), np.float32) / 255.0


def _m() -> np.ndarray:
    return np.zeros((N, N), np.float32)


def _tuval(renk: np.ndarray) -> np.ndarray:
    img = np.empty((N, N, 3), np.float32)
    img[:] = renk
    return img


def _boya(img: np.ndarray, m: np.ndarray, renk: np.ndarray, opak: float = 1.0) -> None:
    a = (np.clip(m, 0.0, 1.0) * opak)[..., None]
    img *= 1.0 - a
    img += a * renk


def _gurultu(olcek: int, tohum: int) -> np.ndarray:
    rng = np.random.default_rng(tohum)
    k = max(2, N // olcek)
    g = cv2.resize(rng.random((k, k)).astype(np.float32), (N, N), interpolation=cv2.INTER_CUBIC)
    return np.clip(g, 0.0, 1.0)


def _icine(sil: np.ndarray, px: float) -> np.ndarray:
    """Silüetin kenarından px içeri çekilmiş yumuşak maske."""
    d = cv2.distanceTransform((sil > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    return np.clip((d - px) / 1.5, 0.0, 1.0)


def _uzaklik(sil: np.ndarray) -> np.ndarray:
    d = cv2.distanceTransform((sil > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    return d / max(float(d.max()), 1.0)


def _hacim(img: np.ndarray, sil: np.ndarray, parlak: float = 0.55, sert: float = 28.0,
           taban: float = 0.40, kesit: bool = False) -> None:
    """Silüeti kubbe sayıp sol-üst ışıkla gölgelendirir; kesitte (düz yüz) etki hafiftir."""
    d = cv2.distanceTransform((sil > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    dmax = max(float(d.max()), 1.0)
    h = np.sqrt(np.clip(d / dmax, 0.0, 1.0)) * dmax * (0.35 if kesit else 1.0)
    h = cv2.GaussianBlur(h, (0, 0), max(2.5, 0.16 * dmax))  # orta eksen kırışığını yumuşat
    gy, gx = np.gradient(h)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array([-0.45, -0.55, 0.70], np.float32)
    L /= np.linalg.norm(L)
    dif = np.clip(n @ L, 0.0, 1.0)
    Hv = L + np.array([0.0, 0.0, 1.0], np.float32)
    Hv /= np.linalg.norm(Hv)
    spek = np.clip(n @ Hv, 0.0, 1.0) ** sert * parlak
    if kesit:
        golge = 0.86 + 0.18 * dif
    else:
        golge = taban + (1.08 - taban) * dif
        kenar = np.clip(d / (0.10 * dmax), 0.0, 1.0)  # kenarda hafif koyulaşma
        golge *= 0.80 + 0.20 * kenar
    img *= golge[..., None]
    img += spek[..., None]


def _bitir(img: np.ndarray, sil: np.ndarray, boy: int, golge: bool = True) -> np.ndarray:
    a = cv2.GaussianBlur(np.clip(sil, 0.0, 1.0), (0, 0), 0.8)
    pre = np.clip(img, 0.0, 1.0) * a[..., None]
    if golge:
        g = cv2.GaussianBlur(np.roll(np.roll(a, 8, 0), 5, 1), (0, 0), 7) * 0.40
        at = a + g * (1.0 - a)
    else:
        at = a
    pre = cv2.resize(pre, (boy, boy), interpolation=cv2.INTER_AREA)
    at = cv2.resize(at, (boy, boy), interpolation=cv2.INTER_AREA)
    renk = pre / np.maximum(at[..., None], 1e-4)
    out = np.dstack([np.clip(renk, 0, 1) * 255.0, np.clip(at, 0, 1) * 255.0])
    return out.astype(np.uint8)


def _dondur(pts: np.ndarray, aci: float) -> np.ndarray:
    c, s = math.cos(math.radians(aci)), math.sin(math.radians(aci))
    p = pts - C
    return np.stack([p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c], 1) + C


def _cizgi(m: np.ndarray, pts: np.ndarray, kalin: int, deger: float = 1.0) -> None:
    cv2.polylines(m, [np.round(pts).astype(np.int32)], False, deger, kalin, AA)


def _dilimler(m: np.ndarray, cx: int, cy: int, r: float, adet: int, kalin: int, faz: float = 0.0) -> None:
    for i in range(adet):
        a = faz + 2 * math.pi * i / adet
        cv2.line(m, (cx, cy), (int(cx + r * math.cos(a)), int(cy + r * math.sin(a))), 1.0, kalin, AA)


def _cekirdek_dizisi(m: np.ndarray, cx: float, cy: float, rx: float, ry: float, adet: int,
                     boyut: Tuple[int, int], rng: np.random.Generator, oynama: float = 0.0) -> None:
    for i in range(adet):
        a = 2 * math.pi * i / adet + rng.uniform(-oynama, oynama)
        k = 1.0 + rng.uniform(-oynama, oynama) * 0.5
        x, y = cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)
        cv2.ellipse(m, (int(x), int(y)), boyut, math.degrees(a) + 90, 0, 360, 1.0, -1, AA)


# ---------------------------------------------------------------- meyveler
# Her fonksiyon: (dış_img, dış_sil, iç_img, iç_sil)

def _karpuz():
    rng = np.random.default_rng(1)
    sil = _m()
    cv2.ellipse(sil, (C, C), (114, 92), -18, 0, 360, 1.0, -1, AA)
    img = _tuval(_r(70, 175, 95))
    ser = _m()
    for k in (-0.92, -0.62, -0.32, -0.02, 0.28, 0.58, 0.88):
        t = np.linspace(0, math.pi, 80)
        x = C - 114 * np.cos(t)
        y = C + 92 * k * np.sin(t) + 5 * np.sin(11 * t + k * 9)
        _cizgi(ser, _dondur(np.stack([x, y], 1), -18), 15)
    ser = cv2.GaussianBlur(ser, (0, 0), 1.6)
    _boya(img, ser * sil, _r(25, 95, 35), 0.92)
    img *= (0.90 + 0.16 * _gurultu(10, 2))[..., None]
    _hacim(img, sil, parlak=0.65, sert=34)
    ic = _tuval(_r(30, 110, 40))
    _boya(ic, _icine(sil, 6), _r(160, 225, 200))
    et = _icine(sil, 11)
    d = _uzaklik(sil)
    _boya(ic, et, _r(70, 70, 235))
    _boya(ic, et * np.clip(d * 1.4 - 0.2, 0, 1), _r(110, 105, 255), 0.6)
    tane = _m()
    _cekirdek_dizisi(tane, C, C, 62, 50, 11, (4, 8), rng, 0.15)
    _cekirdek_dizisi(tane, C, C, 30, 24, 6, (4, 7), rng, 0.2)
    _boya(ic, tane, _r(25, 25, 30))
    ic *= (0.94 + 0.10 * _gurultu(4, 3))[..., None]
    _hacim(ic, sil, parlak=0.18, sert=10, kesit=True)
    return img, sil, ic, sil


def _portakal():
    rng = np.random.default_rng(4)
    sil = _m()
    cv2.circle(sil, (C, C), 96, 1.0, -1, AA)
    img = _tuval(_r(20, 140, 250))
    img *= (0.90 + 0.14 * _gurultu(3, 5))[..., None]
    gobek = _m()
    cv2.circle(gobek, (C + 38, C + 44), 6, 1.0, -1, AA)
    _boya(img, cv2.GaussianBlur(gobek, (0, 0), 2), _r(20, 95, 190), 0.8)
    sap = _m()
    cv2.circle(sap, (C - 12, C - 88), 7, 1.0, -1, AA)
    _boya(img, sap, _r(40, 110, 60))
    _hacim(img, sil, parlak=0.55, sert=22)
    ic = _tuval(_r(20, 135, 245))
    _boya(ic, _icine(sil, 6), _r(195, 228, 250))
    _boya(ic, _icine(sil, 11), _r(30, 165, 255))
    ic *= (0.88 + 0.18 * _gurultu(5, 6))[..., None]
    zar = _m()
    _dilimler(zar, C, C, 86, 10, 4, rng.uniform(0, 1))
    cv2.circle(zar, (C, C), 11, 1.0, -1, AA)
    _boya(ic, cv2.GaussianBlur(zar, (0, 0), 1.2) * _icine(sil, 8), _r(205, 235, 252), 0.9)
    _hacim(ic, sil, parlak=0.22, sert=10, kesit=True)
    return img, sil, ic, sil


def _limon():
    rng = np.random.default_rng(7)
    sil = _m()
    cv2.ellipse(sil, (C, C), (100, 78), -10, 0, 360, 1.0, -1, AA)
    for s in (-1, 1):
        x, y = _dondur(np.array([[C + s * 100.0, C]]), -10)[0]
        cv2.ellipse(sil, (int(x), int(y)), (20, 14), -10, 0, 360, 1.0, -1, AA)
    img = _tuval(_r(45, 225, 255))
    img *= (0.90 + 0.14 * _gurultu(3, 8))[..., None]
    _hacim(img, sil, parlak=0.6, sert=26)
    kes = _m()
    cv2.circle(kes, (C, C), 88, 1.0, -1, AA)
    ic = _tuval(_r(40, 215, 250))
    _boya(ic, _icine(kes, 5), _r(205, 245, 252))
    _boya(ic, _icine(kes, 10), _r(120, 240, 255))
    ic *= (0.90 + 0.15 * _gurultu(5, 9))[..., None]
    zar = _m()
    _dilimler(zar, C, C, 80, 9, 4, rng.uniform(0, 1))
    cv2.circle(zar, (C, C), 9, 1.0, -1, AA)
    _boya(ic, cv2.GaussianBlur(zar, (0, 0), 1.2) * _icine(kes, 8), _r(215, 248, 253), 0.9)
    _hacim(ic, kes, parlak=0.22, sert=10, kesit=True)
    return img, sil, ic, kes


def _elma(govde: np.ndarray, cizgi: np.ndarray, tohum: int):
    rng = np.random.default_rng(tohum)
    sil = _m()
    cv2.circle(sil, (C, C + 14), 88, 1.0, -1, AA)
    cv2.circle(sil, (C - 30, C - 18), 72, 1.0, -1, AA)
    cv2.circle(sil, (C + 30, C - 18), 72, 1.0, -1, AA)
    cukur = _m()
    cv2.circle(cukur, (C, C - 92), 14, 1.0, -1, AA)
    sil = np.clip(sil - cukur, 0, 1)
    sil = np.clip((cv2.GaussianBlur(sil, (0, 0), 4) - 0.5) * 4 + 0.5, 0, 1)
    govde_sil = sil.copy()
    img = _tuval(govde)
    ser = cv2.resize(rng.random((3, 26)).astype(np.float32), (N, N), interpolation=cv2.INTER_CUBIC)
    _boya(img, np.clip(ser, 0, 1) * 0.45, cizgi)
    _hacim(img, govde_sil, parlak=0.75, sert=40)
    sap = _m()
    cv2.line(sap, (C, C - 66), (C + 9, C - 112), 1.0, 7, AA)
    _boya(img, sap, _r(30, 60, 95))
    yaprak = _m()
    cv2.ellipse(yaprak, (C + 34, C - 100), (28, 12), -28, 0, 360, 1.0, -1, AA)
    _boya(img, yaprak, _r(45, 165, 70))
    damar = _m()
    cv2.line(damar, (C + 12, C - 88), (C + 56, C - 112), 1.0, 2, AA)
    _boya(img, damar * yaprak, _r(30, 110, 45))
    sil = np.maximum(np.maximum(sil, sap), yaprak)
    ic = _tuval(govde * 0.9)
    _boya(ic, _icine(govde_sil, 5), _r(175, 228, 248))
    d = _uzaklik(govde_sil)
    _boya(ic, _icine(govde_sil, 5) * np.clip(1.2 - d * 2, 0, 1), _r(150, 210, 235), 0.4)
    oz = _m()
    cv2.ellipse(oz, (C, C + 6), (24, 36), 0, 0, 360, 1.0, 2, AA)
    _boya(ic, oz, _r(130, 185, 215), 0.7)
    tane = _m()
    _cekirdek_dizisi(tane, C, C + 6, 15, 20, 5, (5, 9), rng)
    _boya(ic, tane, _r(25, 55, 95))
    _hacim(ic, govde_sil, parlak=0.15, sert=10, kesit=True)
    return img, sil, ic, govde_sil


def _kivi():
    rng = np.random.default_rng(10)
    sil = _m()
    cv2.ellipse(sil, (C, C), (100, 82), 12, 0, 360, 1.0, -1, AA)
    img = _tuval(_r(45, 90, 135))
    tuy = rng.random((N, N)).astype(np.float32)
    img *= (0.80 + 0.30 * cv2.GaussianBlur(tuy, (0, 0), 0.8))[..., None]
    img *= (0.90 + 0.15 * _gurultu(12, 11))[..., None]
    _hacim(img, sil, parlak=0.18, sert=12)
    ic = _tuval(_r(40, 85, 130))
    et = _icine(sil, 6)
    d = _uzaklik(sil)
    _boya(ic, et, _r(35, 175, 85))
    _boya(ic, et * np.clip(1.4 - d * 1.6, 0, 1), _r(90, 225, 160), 0.85)
    lif = _m()
    _dilimler(lif, C, C, 96, 46, 1, 0.1)
    _boya(ic, cv2.GaussianBlur(lif, (0, 0), 1.0) * et, _r(120, 235, 190), 0.35)
    tane = _m()
    for i in range(44):
        a = 2 * math.pi * i / 44 + rng.uniform(-0.05, 0.05)
        rr = rng.uniform(0.40, 0.52)
        x = C + 100 * rr * math.cos(a)
        y = C + 82 * rr * math.sin(a)
        p = _dondur(np.array([[x, y]]), 12)[0]
        cv2.ellipse(tane, (int(p[0]), int(p[1])), (2, 5), math.degrees(a) + 102, 0, 360, 1.0, -1, AA)
    _boya(ic, tane, _r(20, 25, 25))
    merkez = _m()
    cv2.ellipse(merkez, (C, C), (26, 18), 12, 0, 360, 1.0, -1, AA)
    _boya(ic, cv2.GaussianBlur(merkez, (0, 0), 3), _r(185, 235, 225))
    _hacim(ic, sil, parlak=0.25, sert=10, kesit=True)
    return img, sil, ic, sil


def _cilek():
    rng = np.random.default_rng(13)
    govde = _m()
    cv2.circle(govde, (C, C - 6), 84, 1.0, -1, AA)
    ucgen = np.array([[C - 80, C - 2], [C + 80, C - 2], [C + 6, C + 112]], np.int32)
    cv2.fillPoly(govde, [ucgen], 1.0, AA)
    govde = np.clip((cv2.GaussianBlur(govde, (0, 0), 7) - 0.5) * 5 + 0.5, 0, 1)
    img = _tuval(_r(45, 35, 225))
    yy = np.linspace(0, 1, N, dtype=np.float32)[:, None]
    _boya(img, np.broadcast_to(np.clip(yy * 1.3 - 0.4, 0, 1), (N, N)), _r(40, 25, 175), 0.6)
    yuva, tohum = _m(), _m()
    for sy in range(C - 70, C + 110, 20):
        kay = 10 if (sy // 20) % 2 else 0
        for sx in range(C - 90 + kay, C + 92, 21):
            x, y = sx + rng.uniform(-2, 2), sy + rng.uniform(-2, 2)
            cv2.circle(yuva, (int(x), int(y)), 5, 1.0, -1, AA)
            cv2.ellipse(tohum, (int(x), int(y) - 1), (2, 4), 0, 0, 360, 1.0, -1, AA)
    ic_bolge = _icine(govde, 8)
    _boya(img, cv2.GaussianBlur(yuva, (0, 0), 1.2) * ic_bolge, _r(35, 20, 160), 0.7)
    _boya(img, tohum * ic_bolge, _r(90, 215, 245))
    _hacim(img, govde, parlak=0.8, sert=36)
    yaprak = _m()
    for i in range(7):
        a = math.radians(-180 + i * 30)
        cx, cy = C + 30 * math.cos(a), C - 84 + 12 * math.sin(a)
        cv2.ellipse(yaprak, (int(cx), int(cy)), (32, 10), math.degrees(a), 0, 360, 1.0, -1, AA)
    cv2.line(yaprak, (C, C - 86), (C + 6, C - 120), 1.0, 7, AA)
    yimg = _tuval(_r(45, 160, 55))
    _hacim(yimg, yaprak, parlak=0.3, sert=16, taban=0.55)
    _boya(img, yaprak, 0.0)
    img += yimg * np.clip(yaprak, 0, 1)[..., None]
    sil = np.maximum(govde, yaprak)
    ic = _tuval(_r(45, 35, 215))
    d = _uzaklik(govde)
    et = _icine(govde, 6)
    _boya(ic, et, _r(120, 110, 245))
    _boya(ic, et * np.clip(d * 1.6 - 0.2, 0, 1), _r(200, 195, 255), 0.85)
    oz = _m()
    cv2.ellipse(oz, (C, C + 4), (16, 54), 0, 0, 360, 1.0, -1, AA)
    _boya(ic, cv2.GaussianBlur(oz, (0, 0), 6), _r(225, 225, 255), 0.8)
    _hacim(ic, govde, parlak=0.2, sert=10, kesit=True)
    return img, sil, ic, govde


def _seftali():
    sil = _m()
    cv2.circle(sil, (C, C + 4), 94, 1.0, -1, AA)
    img = _tuval(_r(70, 175, 255))
    xx, yy = np.meshgrid(np.linspace(0, 1, N), np.linspace(0, 1, N))
    allik = np.clip((xx - yy) * 1.4 + 0.35, 0, 1).astype(np.float32)
    _boya(img, allik, _r(85, 75, 235), 0.85)
    img *= (0.94 + 0.08 * _gurultu(2, 14))[..., None]
    kat = _m()
    t = np.linspace(0, 1, 40)
    _cizgi(kat, np.stack([C + 6 + 22 * np.sin(t * 2.2), C - 86 + 120 * t], 1), 5)
    _boya(img, cv2.GaussianBlur(kat, (0, 0), 3), _r(60, 80, 190), 0.5)
    _hacim(img, sil, parlak=0.3, sert=14)
    yaprak = _m()
    cv2.ellipse(yaprak, (C + 24, C - 96), (26, 11), -22, 0, 360, 1.0, -1, AA)
    _boya(img, yaprak, _r(50, 160, 70))
    sil = np.maximum(sil, yaprak)
    kes = _m()
    cv2.circle(kes, (C, C + 4), 94, 1.0, -1, AA)
    ic = _tuval(_r(70, 90, 230))
    et = _icine(kes, 5)
    _boya(ic, et, _r(70, 190, 255))
    d = _uzaklik(kes)
    _boya(ic, et * np.clip(d * 2.2 - 1.1, 0, 1), _r(70, 120, 245), 0.55)
    cekirdek = _m()
    cv2.ellipse(cekirdek, (C, C + 4), (32, 44), 8, 0, 360, 1.0, -1, AA)
    cimg = _tuval(_r(45, 80, 135))
    cimg *= (0.70 + 0.45 * _gurultu(3, 15))[..., None]
    _hacim(cimg, cekirdek, parlak=0.2, sert=14, taban=0.5)
    _boya(ic, cekirdek, 0.0)
    ic += cimg * np.clip(cekirdek, 0, 1)[..., None]
    _hacim(ic, kes, parlak=0.25, sert=10, kesit=True)
    return img, sil, ic, kes


def _hindistan():
    rng = np.random.default_rng(16)
    sil = _m()
    cv2.ellipse(sil, (C, C), (94, 86), 0, 0, 360, 1.0, -1, AA)
    img = _tuval(_r(45, 80, 120))
    lif = _m()
    for _ in range(420):
        x, y = rng.uniform(30, 226), rng.uniform(30, 226)
        a = rng.uniform(0, math.pi)
        u = rng.uniform(6, 16)
        cv2.line(lif, (int(x), int(y)), (int(x + u * math.cos(a)), int(y + u * math.sin(a))),
                 float(rng.uniform(0.3, 1.0)), 1, AA)
    _boya(img, lif, _r(25, 45, 70), 0.75)
    _boya(img, np.roll(lif, 3, 1), _r(90, 135, 175), 0.35)
    goz = _m()
    for dx, dy in ((-16, -46), (16, -46), (0, -24)):
        cv2.circle(goz, (C + dx, C + dy), 8, 1.0, -1, AA)
    _boya(img, cv2.GaussianBlur(goz, (0, 0), 1.5), _r(20, 30, 45))
    _hacim(img, sil, parlak=0.12, sert=10)
    ic = _tuval(_r(35, 65, 100))
    _boya(ic, _icine(sil, 11), _r(240, 243, 246))
    _boya(ic, _icine(sil, 30), _r(225, 220, 212))
    _hacim(ic, sil, parlak=0.35, sert=14, kesit=True)
    return img, sil, ic, sil


def _ejder():
    rng = np.random.default_rng(19)
    govde = _m()
    cv2.ellipse(govde, (C, C + 6), (82, 98), 0, 0, 360, 1.0, -1, AA)
    img = _tuval(_r(145, 45, 235))
    img *= (0.90 + 0.15 * _gurultu(8, 20))[..., None]
    _hacim(img, govde, parlak=0.55, sert=28)
    sil = govde.copy()
    for i in range(12):
        a = 2 * math.pi * i / 12 + 0.2
        bx, by = C + 76 * math.cos(a), C + 6 + 92 * math.sin(a)
        ux, uy = C + 108 * math.cos(a + 0.18), C + 6 + 120 * math.sin(a + 0.18)
        kanat = _m()
        cv2.ellipse(kanat, (int((bx + ux) / 2), int((by + uy) / 2)), (24, 9),
                    math.degrees(math.atan2(uy - by, ux - bx)), 0, 360, 1.0, -1, AA)
        uc = _m()
        cv2.circle(uc, (int(ux), int(uy)), 9, 1.0, -1, AA)
        kimg = _tuval(_r(140, 50, 225))
        _boya(kimg, cv2.GaussianBlur(uc, (0, 0), 4) * 1.4, _r(70, 200, 120))
        _hacim(kimg, kanat, parlak=0.4, sert=20, taban=0.6)
        _boya(img, kanat, 0.0)
        img += kimg * np.clip(kanat, 0, 1)[..., None]
        sil = np.maximum(sil, kanat)
    ic = _tuval(_r(150, 50, 230))
    _boya(ic, _icine(govde, 6), _r(242, 240, 248))
    tane = _m()
    for _ in range(150):
        x, y = rng.uniform(C - 80, C + 80), rng.uniform(C - 90, C + 100)
        cv2.circle(tane, (int(x), int(y)), 2, 1.0, -1, AA)
    _boya(ic, tane * _icine(govde, 12), _r(25, 25, 30))
    _hacim(ic, govde, parlak=0.25, sert=10, kesit=True)
    return img, sil, ic, govde


def _ananas():
    govde = _m()
    cv2.ellipse(govde, (C, C + 30), (74, 92), 0, 0, 360, 1.0, -1, AA)
    img = _tuval(_r(40, 165, 235))
    d = _uzaklik(govde)
    _boya(img, np.clip(1.0 - d * 3.0, 0, 1), _r(30, 105, 175), 0.6)
    ag = _m()
    for k in range(-12, 13):
        o = k * 26
        cv2.line(ag, (C + o - 200, C + 30 - 200), (C + o + 200, C + 30 + 200), 1.0, 4, AA)
        cv2.line(ag, (C + o + 200, C + 30 - 200), (C + o - 200, C + 30 + 200), 1.0, 4, AA)
    _boya(img, ag * govde, _r(25, 90, 150), 0.85)
    nokta = _m()
    for k in range(-8, 9):
        for j in range(-8, 9):
            x, y = C + (k + j) * 13, C + 30 + (k - j) * 13
            cv2.circle(nokta, (x, y), 3, 1.0, -1, AA)
    _boya(img, nokta * govde, _r(90, 215, 250))
    _hacim(img, govde, parlak=0.35, sert=18)
    tac = _m()
    for i, (aci, boy) in enumerate(((-60, 46), (-38, 58), (-16, 66), (0, 72), (16, 66), (38, 58), (60, 46))):
        a = math.radians(aci - 90)
        tx, ty = C + boy * math.cos(a), C - 52 + boy * math.sin(a)
        ny = math.radians(aci)
        p = np.array([[C - 9 * math.cos(ny), C - 52 - 9 * math.sin(ny)],
                      [tx, ty], [C + 9 * math.cos(ny), C - 52 + 9 * math.sin(ny)]], np.int32)
        cv2.fillPoly(tac, [p], 1.0, AA)
    timg = _tuval(_r(50, 150, 45))
    _boya(timg, cv2.GaussianBlur(tac, (0, 0), 3) * 0.6, _r(110, 210, 120))
    _hacim(timg, tac, parlak=0.25, sert=14, taban=0.55)
    sil = np.maximum(govde, tac)
    _boya(img, tac * (1 - govde), 0.0)
    img += timg * np.clip(tac * (1 - govde), 0, 1)[..., None]
    ic = _tuval(_r(30, 100, 165))
    et = _icine(govde, 7)
    _boya(ic, et, _r(90, 215, 255))
    _boya(ic, et * np.clip(d * 2.4 - 1.2, 0, 1), _r(165, 238, 255), 0.85)
    lif = _m()
    _dilimler(lif, C, C + 30, 90, 30, 1)
    _boya(ic, cv2.GaussianBlur(lif, (0, 0), 1) * et, _r(60, 190, 245), 0.5)
    _hacim(ic, govde, parlak=0.25, sert=10, kesit=True)
    return img, sil, ic, govde


def _avokado():
    sil = _m()
    cv2.circle(sil, (C, C + 32), 84, 1.0, -1, AA)
    cv2.circle(sil, (C, C - 44), 54, 1.0, -1, AA)
    sil = np.clip((cv2.GaussianBlur(sil, (0, 0), 14) - 0.5) * 5 + 0.5, 0, 1)
    img = _tuval(_r(35, 85, 45))
    img *= (0.75 + 0.40 * _gurultu(2, 22) * _gurultu(6, 23))[..., None]
    _hacim(img, sil, parlak=0.5, sert=30)
    ic = _tuval(_r(30, 70, 35))
    d = _uzaklik(sil)
    et = _icine(sil, 5)
    _boya(ic, et, _r(55, 175, 105))
    _boya(ic, et * np.clip(d * 2.0 - 0.15, 0, 1), _r(140, 232, 215), 0.95)
    cek = _m()
    cv2.circle(cek, (C, C + 32), 38, 1.0, -1, AA)
    cimg = _tuval(_r(35, 70, 125))
    _hacim(cimg, cek, parlak=0.6, sert=26, taban=0.45)
    _hacim(ic, sil, parlak=0.25, sert=10, kesit=True)
    _boya(ic, cek, 0.0)
    ic += cimg * np.clip(cek, 0, 1)[..., None]
    return img, sil, ic, sil


def _nar():
    rng = np.random.default_rng(25)
    govde = _m()
    cv2.circle(govde, (C, C + 10), 90, 1.0, -1, AA)
    tac = _m()
    yildiz = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        r = 26 if i % 2 == 0 else 12
        yildiz.append([C + r * math.cos(a), C - 84 + r * 0.8 * math.sin(a)])
    cv2.fillPoly(tac, [np.array(yildiz, np.int32)], 1.0, AA)
    cv2.rectangle(tac, (C - 12, C - 88), (C + 12, C - 70), 1.0, -1)
    sil = np.maximum(govde, tac)
    img = _tuval(_r(45, 35, 185))
    _boya(img, _gurultu(3, 26) * 0.6, _r(70, 120, 215))
    _hacim(img, sil, parlak=0.55, sert=30)
    ic = _tuval(_r(40, 30, 165))
    et = _icine(govde, 8)
    _boya(ic, et, _r(175, 215, 240))
    tane, isik = _m(), _m()
    for _ in range(95):
        a, rr = rng.uniform(0, 2 * math.pi), math.sqrt(rng.uniform(0, 1)) * 72
        x, y = int(C + rr * math.cos(a)), int(C + 10 + rr * math.sin(a))
        cv2.circle(tane, (x, y), 8, 1.0, -1, AA)
        cv2.circle(isik, (x - 3, y - 3), 2, 1.0, -1, AA)
    _boya(ic, tane * et, _r(70, 25, 205))
    _boya(ic, isik * et, _r(200, 170, 255), 0.9)
    _hacim(ic, govde, parlak=0.2, sert=10, kesit=True)
    return img, sil, ic, govde


def _mango():
    sil = _m()
    cv2.ellipse(sil, (C, C), (106, 80), 28, 0, 360, 1.0, -1, AA)
    img = _tuval(_r(45, 200, 250))
    xx, yy = np.meshgrid(np.linspace(-1, 1, N), np.linspace(-1, 1, N))
    eksen = (xx * math.cos(math.radians(28)) + yy * math.sin(math.radians(28))).astype(np.float32)
    _boya(img, np.clip(-eksen * 1.6, 0, 1), _r(60, 165, 90), 0.8)
    _boya(img, np.clip(eksen * 1.6 - 0.2, 0, 1), _r(70, 70, 230), 0.8)
    _hacim(img, sil, parlak=0.55, sert=26)
    ic = _tuval(_r(50, 150, 220))
    et = _icine(sil, 5)
    _boya(ic, et, _r(40, 185, 255))
    cek = _m()
    cv2.ellipse(cek, (C, C), (64, 24), 28, 0, 360, 1.0, -1, AA)
    _boya(ic, cv2.GaussianBlur(cek, (0, 0), 6), _r(120, 220, 252), 0.85)
    _hacim(ic, sil, parlak=0.25, sert=10, kesit=True)
    return img, sil, ic, sil


def _muz():
    sil, uclar, sirt = _m(), _m(), _m()
    adim = np.linspace(0.0, 1.0, 90)
    noktalar = []
    for t in adim:
        a = math.radians(52 + 76 * t)
        x, y = C + 210 * math.cos(a), C - 140 + 210 * math.sin(a)
        r = 6 + 34 * math.sin(math.pi * t) ** 0.55
        cv2.circle(sil, (int(x), int(y)), int(r), 1.0, -1, AA)
        noktalar.append((x, y))
        if t < 0.06 or t > 0.95:
            cv2.circle(uclar, (int(x), int(y)), int(r) + 2, 1.0, -1, AA)
    noktalar = np.array(noktalar)
    _cizgi(sirt, noktalar - [0, 14], 3)
    img = _tuval(_r(60, 220, 255))
    _boya(img, cv2.GaussianBlur(sirt, (0, 0), 2) * 0.6, _r(30, 170, 220))
    _boya(img, uclar, _r(30, 60, 90))
    _hacim(img, sil, parlak=0.5, sert=24)
    ic = _tuval(_r(50, 210, 250))
    _boya(ic, _icine(sil, 6), _r(175, 228, 245))
    tohum = _m()
    _cizgi(tohum, noktalar[10:-10], 3)
    _boya(ic, cv2.GaussianBlur(tohum, (0, 0), 1.5) * _icine(sil, 8), _r(110, 150, 180), 0.6)
    _hacim(ic, sil, parlak=0.2, sert=10, kesit=True)
    return img, sil, ic, sil


def _kiraz():
    tane = _m()
    cv2.circle(tane, (C - 44, C + 52), 52, 1.0, -1, AA)
    cv2.circle(tane, (C + 44, C + 40), 52, 1.0, -1, AA)
    img = _tuval(_r(45, 20, 185))
    _hacim(img, tane, parlak=0.9, sert=44)
    sap = _m()
    t = np.linspace(0, 1, 30)
    _cizgi(sap, np.stack([C - 44 + 50 * t, C + 2 - 110 * t + 30 * t * t], 1), 5)
    _cizgi(sap, np.stack([C + 44 - 36 * t, C - 10 - 98 * t + 26 * t * t], 1), 5)
    yaprak = _m()
    cv2.ellipse(yaprak, (C + 28, C - 96), (30, 12), -20, 0, 360, 1.0, -1, AA)
    _boya(img, sap * (1 - tane), _r(40, 110, 70))
    _boya(img, yaprak, _r(45, 165, 70))
    sil = np.maximum(np.maximum(tane, sap), yaprak)
    ic = _tuval(_r(40, 20, 160))
    _boya(ic, _icine(tane, 5), _r(70, 45, 215))
    cek = _m()
    cv2.circle(cek, (C - 44, C + 52), 14, 1.0, -1, AA)
    cv2.circle(cek, (C + 44, C + 40), 14, 1.0, -1, AA)
    _boya(ic, cek, _r(160, 200, 235))
    _hacim(ic, tane, parlak=0.25, sert=10, kesit=True)
    return img, sil, ic, tane


# (ad, çizici, boyut px, meyve suyu BGR)
MEYVELER = [
    ("karpuz", _karpuz, 150, (70, 60, 235)),
    ("portakal", _portakal, 118, (30, 160, 255)),
    ("limon", _limon, 112, (90, 235, 255)),
    ("elma", lambda: _elma(_r(40, 40, 205), _r(60, 130, 245), 30), 118, (160, 220, 245)),
    ("yesil_elma", lambda: _elma(_r(70, 205, 140), _r(80, 230, 210), 31), 118, (170, 235, 220)),
    ("kivi", _kivi, 108, (60, 200, 110)),
    ("cilek", _cilek, 112, (80, 60, 240)),
    ("seftali", _seftali, 118, (60, 175, 255)),
    ("hindistancevizi", _hindistan, 124, (240, 240, 240)),
    ("ejder", _ejder, 130, (200, 120, 255)),
    ("ananas", _ananas, 140, (70, 220, 255)),
    ("avokado", _avokado, 120, (110, 220, 160)),
    ("nar", _nar, 120, (80, 30, 210)),
    ("mango", _mango, 124, (40, 190, 255)),
    ("muz", _muz, 132, (170, 228, 250)),
    ("kiraz", _kiraz, 112, (70, 30, 200)),
]


@lru_cache(maxsize=1)
def meyveler() -> List[Dict]:
    """[{ad, dis, ic, suyu, boy}] — dış ve iç BGRA, aynı boyda (yarıya bölmede hizalı)."""
    sonuc = []
    for ad, fn, boy, suyu in MEYVELER:
        dis_img, dis_sil, ic_img, ic_sil = fn()
        sonuc.append({
            "ad": ad,
            "dis": _bitir(dis_img, dis_sil, boy),
            "ic": _bitir(ic_img, ic_sil, boy, golge=False),
            "suyu": suyu,
            "boy": boy,
        })
    return sonuc


@lru_cache(maxsize=64)
def leke(suyu: Tuple[int, int, int], tohum: int, boy: int = 220) -> np.ndarray:
    """Meyve suyu sıçrama lekesi (BGRA): merkez lekesi + düzensiz damlalar."""
    rng = np.random.default_rng(tohum)
    m = _m()
    cv2.circle(m, (C, C), 46, 1.0, -1, AA)
    for _ in range(14):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(30, 70)
        cv2.circle(m, (int(C + r * math.cos(a)), int(C + r * math.sin(a))), int(rng.uniform(10, 26)), 1.0, -1, AA)
    for _ in range(18):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(70, 118)
        cv2.circle(m, (int(C + r * math.cos(a)), int(C + r * math.sin(a))), int(rng.uniform(3, 9)), 1.0, -1, AA)
    m = np.clip((cv2.GaussianBlur(m, (0, 0), 3) - 0.45) * 4 + 0.5, 0, 1) * 0.85
    img = _tuval(np.array(suyu, np.float32) / 255.0)
    img *= (0.85 + 0.25 * _gurultu(6, tohum + 1))[..., None]
    return _bitir(img, m, boy, golge=False)


def meme_cikartma(yol: Path, boy: int = 150) -> Optional[np.ndarray]:
    """Meme görselini beyaz kenarlı çıkartmaya çevirir (saydam PNG'de şekli korur, opakta yuvarlak kart)."""
    im = cv2.imread(str(yol), cv2.IMREAD_UNCHANGED)
    if im is None:
        return None
    if im.ndim == 2:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGRA)
    elif im.shape[2] == 3:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)
    a = im[:, :, 3]
    if float((a < 250).mean()) < 0.02:  # opak: yuvarlak kart
        h, w = a.shape
        s = min(h, w)
        y0, x0 = (h - s) // 2, (w - s) // 2
        im = im[y0:y0 + s, x0:x0 + s].copy()
        daire = np.zeros((s, s), np.uint8)
        cv2.circle(daire, (s // 2, s // 2), s // 2 - 2, 255, -1, AA)
        im[:, :, 3] = daire
    ys, xs = np.nonzero(im[:, :, 3] > 20)
    if len(xs) == 0:
        return None
    im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    kenar = max(5, boy // 24)
    ic_boy = boy - 4 * kenar
    h, w = im.shape[:2]
    o = ic_boy / max(h, w)
    im = cv2.resize(im, (max(1, int(w * o)), max(1, int(h * o))), interpolation=cv2.INTER_AREA)
    h, w = im.shape[:2]
    tuval = np.zeros((boy, boy, 4), np.float32)
    y0, x0 = (boy - h) // 2, (boy - w) // 2
    resim = np.zeros((boy, boy, 4), np.float32)
    resim[y0:y0 + h, x0:x0 + w] = im.astype(np.float32) / 255.0
    ra = resim[:, :, 3]
    cekirdek = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * kenar + 1, 2 * kenar + 1))
    beyaz = cv2.GaussianBlur(cv2.dilate((ra > 0.3).astype(np.float32), cekirdek), (0, 0), 1.0)
    golge = cv2.GaussianBlur(np.roll(np.roll(beyaz, 6, 0), 4, 1), (0, 0), 5) * 0.45
    alfa = np.maximum(beyaz, golge)
    renk = np.zeros((boy, boy, 3), np.float32)
    renk += (beyaz / np.maximum(alfa, 1e-4))[..., None]  # gölge siyah, kenar beyaz
    renk = renk * (1 - ra[..., None]) + resim[:, :, :3] * ra[..., None]
    tuval[:, :, :3] = renk
    tuval[:, :, 3] = np.maximum(alfa, ra)
    return (np.clip(tuval, 0, 1) * 255).astype(np.uint8)


_ASSETS = Path(__file__).resolve().parent.parent / "app" / "assets"


@lru_cache(maxsize=4)
def memeler(boy: int = 170) -> Tuple[Tuple[str, np.ndarray, Optional[str], Tuple[int, int, int]], ...]:
    """(ad, çıkartma BGRA, mp3 yolu|None, baskın renk) — app/assets/gorsel içindeki tüm memeler."""
    dizin = _ASSETS / "gorsel"
    if not dizin.is_dir():
        return ()
    sonuc = []
    for yol in sorted(dizin.iterdir()):
        if yol.suffix.lower() not in (".png", ".webp", ".jpg", ".jpeg") or yol.stem == "kalp":
            continue
        sp = meme_cikartma(yol, boy=boy)
        if sp is None:
            continue
        ses = None  # oyunda ses yok
        a = sp[:, :, 3] > 200
        renk = tuple(int(v) for v in sp[:, :, :3][a].mean(0)) if a.any() else (200, 200, 200)
        sonuc.append((yol.stem, sp, ses, renk))
    return tuple(sonuc)


def kontakt(yol: str) -> None:
    """Geliştirici önizlemesi: her meyvenin dış + kesit görüntüsü, gri zemin üstünde."""
    ms = meyveler()
    hucre = 170
    sutun = 8
    satir = math.ceil(len(ms) * 2 / sutun)
    zemin = np.full((satir * hucre, sutun * hucre, 3), 70, np.uint8)
    for i, m in enumerate(ms):
        for j, anahtar in enumerate(("dis", "ic")):
            k = i * 2 + j
            r, c = divmod(k, sutun)
            sp = m[anahtar]
            h, w = sp.shape[:2]
            y0, x0 = r * hucre + (hucre - h) // 2, c * hucre + (hucre - w) // 2
            alan = zemin[y0:y0 + h, x0:x0 + w].astype(np.float32)
            a = sp[:, :, 3:4].astype(np.float32) / 255.0
            zemin[y0:y0 + h, x0:x0 + w] = (alan * (1 - a) + sp[:, :, :3] * a).astype(np.uint8)
    cv2.imwrite(yol, zemin)


if __name__ == "__main__":
    import sys
    kontakt(sys.argv[1] if len(sys.argv) > 1 else "meyveler.png")
