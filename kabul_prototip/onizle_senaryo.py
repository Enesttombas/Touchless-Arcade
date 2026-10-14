"""Senaryolu görsel önizleme (pencere açmaz): gerçek foto + gerçek yüz algısı + senaryolu sahte eller.

Kullanım: <venv python> onizle_senaryo.py FOTO CIKTI_DIZIN p_modul[.kopyaN] ...
Her prototip için 6 an (sn) kaydedilir ve 3x2 kontakt üretilir: CIKTI/<ad>.png
"""
import importlib.util
import math
import os
import sys
from pathlib import Path

import cv2
import numpy as np

PROTO = Path(os.environ.get("PROTO_DIZIN") or Path(__file__).resolve().parent.parent / "prototipler")
sys.path.insert(0, str(PROTO))
import cekirdek as C  # noqa: E402

ANLAR = [float(x) for x in os.environ.get("ANLAR", "0.8,2.5,4.5,7.0,10.0,14.0").split(",")]


def yukle(ad):
    spec = importlib.util.spec_from_file_location(ad.replace(".", "_"), PROTO / f"{ad}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m  # dataclass modülü sys.modules'ta arar
    spec.loader.exec_module(m)
    return m.Prototip


def eller(t):
    """0-2 sn avuç (başlatma), sonra iki el: biri hızla süpüren işaret, biri yaklaşıp açılan avuç."""
    if t < 2.0:
        return [C.sahte_el(0.5, 0.5, "avuc")], ["Open_Palm"]
    sx = 0.5 + 0.38 * math.sin(t * 5.0)
    sy = 0.35 + 0.25 * abs(math.sin(t * 2.3))
    d = 0.07 + 0.12 * max(0.0, math.sin(t * 1.3))
    return [C.sahte_el(sx, sy, "isaret"), C.sahte_el(0.5 + d, 0.55, "avuc")], [None, "Open_Palm"]


def kos(ad, foto, alg, cikti):
    P = yukle(ad)
    p = P(C.Ses(acik=False))
    taban = cv2.resize(cv2.imread(str(foto)), (C.G, C.Y))
    kareler, i, hedef = [], 0, list(ANLAR)
    while hedef:
        t = i * 0.033
        if os.environ.get("IKI_YUZ"):  # aynı kişi iki kez yan yana: düello önizlemesi
            yarim = taban[:, 260:900]
            kare = np.hstack([yarim, yarim]).copy()
        elif os.environ.get("HAREKETLI"):  # sabit arka plan, kişi dikdörtgeni hızla kayar (canlı kamera benzeri)
            kare = taban.copy()
            if os.environ.get("BOS_BASTA"):  # kişisiz oda: kişi bölgesi soldaki odayla doldurulur; ilk 2 sn kimse yok
                kare[150:, 380:900] = cv2.resize(taban[150:, 0:380], (520, C.Y - 150))
                if t < 2.0:
                    a = alg.algila(kare, P.IHTIYAC | {"yuz", "blend"})
                    out = p.isle(kare, a, 1000.0 + t)
                    if t >= hedef[0]:
                        hedef.pop(0)
                        kareler.append(cv2.resize(out, (640, 360)))
                    i += 1
                    continue
            dx = int(260 * math.sin(t * 2.2))
            x0, x1 = max(0, 380 + dx), min(C.G, 900 + dx)
            kare[150:, x0:x1] = taban[150:, x0 - dx:x1 - dx]
        else:
            M = np.float32([[1, 0, 40 * math.sin(t * 1.5)], [0, 1, 10 * math.sin(t * 2.1)]])
            kare = cv2.warpAffine(taban, M, (C.G, C.Y), borderMode=cv2.BORDER_REPLICATE)
        a = alg.algila(kare, P.IHTIYAC | {"yuz", "blend"})
        if a.blend:  # ağız açılıp kapanır (uçan kafa / ifade için), ilk gülme 6. sn'den sonra
            a.blend[0] = dict(a.blend[0], jawOpen=0.7 if (i // 10) % 2 else 0.05)
        if os.environ.get("IKI_YUZ"):  # 7. sn'den sonra soldaki güler
            for j, y in enumerate(a.yuzler):
                g = 0.9 if (t > 7 and y[1].x < 0.5) else 0.05
                a.blend[j] = dict(a.blend[j], mouthSmileLeft=g, mouthSmileRight=g)
        if "el" in P.IHTIYAC and not a.eller:
            a.eller, a.jestler = eller(t)
            a.el_taraf = ["Right", "Left"][:len(a.eller)]
        tus_ar = float(os.environ.get("TUS_ARALIK") or 0)  # her X sn'de boşluk (mod/maske döngüsü)
        if tus_ar and i and int(t / tus_ar) != int((t - 0.033) / tus_ar):
            p.tus(32)
        out = p.isle(kare, a, 1000.0 + t)
        if t >= hedef[0]:
            hedef.pop(0)
            k = cv2.resize(out, (640, 360))
            C.yazi_koy(k, f"{ad}  t={t:.1f}s  durum={getattr(p, 'durum', '-')}", 8, 6, 20, (0, 255, 255))
            kareler.append(k)
        i += 1
    ust, alt = np.hstack(kareler[:3]), np.hstack(kareler[3:])
    cv2.imwrite(str(Path(cikti) / f"{ad}.png"), np.vstack([ust, alt]))


def main():
    foto, cikti, adlar = sys.argv[1], sys.argv[2], sys.argv[3:]
    Path(cikti).mkdir(parents=True, exist_ok=True)
    alg = C.Algilayici()
    for ad in adlar:
        try:
            kos(ad, foto, alg, cikti)
            print("ok", ad)
        except Exception as e:  # noqa: BLE001
            print("HATA", ad, type(e).__name__, e)


if __name__ == "__main__":
    main()
