import math
import numpy as np
import cv2

LANDMARK_SOL_OMUZ = 11
LANDMARK_SAG_OMUZ = 12
LANDMARK_SOL_KALCA = 23
LANDMARK_SAG_KALCA = 24
LANDMARK_BURUN = 0
LANDMARK_SOL_GOZ = 2
LANDMARK_SAG_GOZ = 5


def _noktalar(poz):
    if poz is None:
        return None
    lm = getattr(poz, "landmarks", poz)
    if not isinstance(lm, (list, tuple)) or len(lm) < 25:
        return None
    return lm


def _nokta_xyv(pt, w, h):
    try:
        x, y = float(pt.x), float(pt.y)
        v = float(getattr(pt, "visibility", 1.0))
    except (AttributeError, TypeError, ValueError):
        return 0.0, 0.0, 0.0
    if not all(math.isfinite(a) for a in (x, y, v)):
        return 0.0, 0.0, 0.0
    return x * w, y * h, v


def _vektor_cikar(roi_bgr, maske=None):
    if roi_bgr is None or roi_bgr.size == 0:
        return None
    h, w = roi_bgr.shape[:2]
    if h * w == 0:
        return None

    # Maske ile ayni ornekleme: polygon disindaki arkaplan sinir pikseline karismasin.
    kucuk = cv2.resize(roi_bgr, (64, 64), interpolation=cv2.INTER_NEAREST)
    hsv = cv2.cvtColor(kucuk, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(kucuk, cv2.COLOR_BGR2LAB)

    secim = np.ones((64, 64), bool) if maske is None else cv2.resize(
        maske, (64, 64), interpolation=cv2.INTER_NEAREST) > 0
    if not secim.any():
        return None
    lab_ort = np.asarray(cv2.mean(lab, secim.astype(np.uint8))[:3], dtype=np.float32)

    h_kan = hsv[:, :, 0]
    s_kan = hsv[:, :, 1]
    v_kan = hsv[:, :, 2]

    kromatik = (v_kan >= 40) & (s_kan >= 30) & secim
    akromatik = (s_kan < 30) & secim

    hs = cv2.calcHist([hsv], [0, 1], kromatik.astype(np.uint8),
                     [16, 4], [0, 180, 0, 256]).ravel()
    akro = cv2.calcHist([hsv], [2], akromatik.astype(np.uint8),
                       [4], [0, 256]).ravel()
    hist = np.concatenate((hs, akro))

    toplam = float(np.sum(hist))
    if toplam > 0:
        hist /= toplam

    return {"hist": hist, "lab": lab_ort}


def cikar(kare_bgr, poz):
    if kare_bgr is None or kare_bgr.size == 0:
        return None
    lm = _noktalar(poz)
    if lm is None:
        return None

    h, w = kare_bgr.shape[:2]
    p11_x, p11_y, v11 = _nokta_xyv(lm[LANDMARK_SOL_OMUZ], w, h)
    p12_x, p12_y, v12 = _nokta_xyv(lm[LANDMARK_SAG_OMUZ], w, h)
    if min(v11, v12) < 0.3:
        return None

    p23_x, p23_y, v23 = _nokta_xyv(lm[LANDMARK_SOL_KALCA], w, h)
    p24_x, p24_y, v24 = _nokta_xyv(lm[LANDMARK_SAG_KALCA], w, h)

    omuz_g = math.hypot(p11_x - p12_x, p11_y - p12_y)
    if omuz_g < 2.0:
        return None

    if min(v23, v24) >= 0.5:
        poly = np.array([(p11_x, p11_y), (p12_x, p12_y),
                         (p24_x, p24_y), (p23_x, p23_y)], dtype=np.float32)
    else:
        dy = 1.2 * omuz_g
        poly = np.array([(p11_x, p11_y), (p12_x, p12_y),
                         (p12_x, p12_y + dy), (p11_x, p11_y + dy)], dtype=np.float32)
    merkez = poly.mean(axis=0)
    poly = merkez + .8 * (poly - merkez)
    x1, y1 = np.floor(poly.min(axis=0)).astype(int)
    x2, y2 = np.ceil(poly.max(axis=0)).astype(int) + 1

    cx1 = max(0, x1)
    cy1 = max(0, y1)
    cx2 = min(w, x2)
    cy2 = min(h, y2)

    if cx2 <= cx1 or cy2 <= cy1 or (cx2 - cx1) * (cy2 - cy1) < 400:
        return None

    govde_roi = kare_bgr[cy1:cy2, cx1:cx2]
    maske = np.zeros(govde_roi.shape[:2], np.uint8)
    cv2.fillPoly(maske, [np.rint(poly - (cx1, cy1)).astype(np.int32)], 255)
    if cv2.countNonZero(maske) < 400:
        return None
    govde_vec = _vektor_cikar(govde_roi, maske)
    if govde_vec is None:
        return None

    sac_vec = None
    p0_x, p0_y, v0 = _nokta_xyv(lm[LANDMARK_BURUN], w, h)
    p2_x, p2_y, v2 = _nokta_xyv(lm[LANDMARK_SOL_GOZ], w, h)
    p5_x, p5_y, v5 = _nokta_xyv(lm[LANDMARK_SAG_GOZ], w, h)

    if min(v0, v2, v5) >= 0.3:
        goz_ara = max(math.hypot(p2_x - p5_x, p2_y - p5_y), 4.0)
        kare_boy = goz_ara * 1.5
        sx1 = max(0, int(round(p0_x - kare_boy * 0.5)))
        sx2 = min(w, int(round(p0_x + kare_boy * 0.5)))
        sy2 = max(0, int(round(p0_y)))
        sy1 = max(0, int(round(p0_y - kare_boy)))
        if sx2 > sx1 and sy2 > sy1 and (sx2 - sx1) * (sy2 - sy1) >= 100:
            sac_vec = _vektor_cikar(kare_bgr[sy1:sy2, sx1:sx2])

    return {"govde": govde_vec, "sac": sac_vec}


def _bhattacharyya(h1, h2):
    # Cok koyu, doygun kumasta HSV esiklerinden hic ornek gecmeyebilir.
    # Iki bos histogram aynidir; bu durumda ayrimi Lab mesafesi yapar.
    if not np.any(h1) and not np.any(h2):
        return 0.0
    carpim = np.sqrt(np.maximum(0.0, h1 * h2))
    bc = float(np.sum(carpim))
    bc = max(0.0, min(1.0, bc))
    return math.sqrt(max(0.0, 1.0 - bc))


def uzaklik(a, b):
    if a is None or b is None:
        return 1.0
    ga, gb = a.get("govde"), b.get("govde")
    if ga is None or gb is None:
        return 1.0

    d_govde = _bhattacharyya(ga["hist"], gb["hist"])
    delta_lab = float(np.linalg.norm(ga["lab"] - gb["lab"]))
    d_lab = min(1.0, delta_lab / 40.0)

    sa, sb = a.get("sac"), b.get("sac")
    if sa is not None and sb is not None:
        d_sac = _bhattacharyya(sa["hist"], sb["hist"])
        u = 0.75 * d_govde + 0.15 * d_sac + 0.10 * d_lab
    else:
        u = 0.90 * d_govde + 0.10 * d_lab

    return float(max(0.0, min(1.0, u)))


def _ema_parca(eski, yeni, alpha):
    if eski is None:
        return yeni
    if yeni is None:
        return eski
    h = (1.0 - alpha) * eski["hist"] + alpha * yeni["hist"]
    toplam = float(np.sum(h))
    if toplam > 0:
        h /= toplam
    l = (1.0 - alpha) * eski["lab"] + alpha * yeni["lab"]
    return {"hist": h, "lab": l}


class Imza:
    def __init__(self):
        self._kayitlar = {}

    def guncelle(self, kimlik, vektor, simdi, yalniz: bool):
        if not yalniz or vektor is None:
            return
        kayit = self._kayitlar.get(kimlik)
        if kayit is not None:
            kayit["zamanlar"] = [t for t in kayit["zamanlar"] if simdi - t < 1.0 - 1e-5]
            if len(kayit["zamanlar"]) >= 10:
                return

            govde = _ema_parca(kayit["vektor"]["govde"], vektor.get("govde"), 0.1)
            sac = _ema_parca(kayit["vektor"].get("sac"), vektor.get("sac"), 0.1)
            kayit["vektor"] = {"govde": govde, "sac": sac}
            kayit["ornek_sayisi"] += 1
            kayit["son_zaman"] = simdi
            kayit["zamanlar"].append(simdi)
        else:
            self._kayitlar[kimlik] = {
                "vektor": {
                    "govde": {
                        "hist": np.array(vektor["govde"]["hist"], dtype=np.float32, copy=True),
                        "lab": np.array(vektor["govde"]["lab"], dtype=np.float32, copy=True),
                    },
                    "sac": {
                        "hist": np.array(vektor["sac"]["hist"], dtype=np.float32, copy=True),
                        "lab": np.array(vektor["sac"]["lab"], dtype=np.float32, copy=True),
                    }
                    if vektor.get("sac") is not None
                    else None,
                },
                "ornek_sayisi": 1,
                "son_zaman": simdi,
                "zamanlar": [simdi],
            }

    def al(self, kimlik):
        kayit = self._kayitlar.get(kimlik)
        return kayit["vektor"] if kayit else None

    def olgun(self, kimlik):
        kayit = self._kayitlar.get(kimlik)
        return bool(kayit and kayit["ornek_sayisi"] >= 10)

    def sil(self, kimlik):
        self._kayitlar.pop(kimlik, None)

    def sifirla(self):
        self._kayitlar.clear()
