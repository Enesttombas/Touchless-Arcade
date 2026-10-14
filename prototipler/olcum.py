"""Kamerasız oyun çizim kıyası; bu sonuç kamera gecikmesi değildir."""
import argparse
import importlib
import sys
from collections import defaultdict, deque
from contextlib import contextmanager
from time import perf_counter
import cv2
import numpy as np


class Profil:
    def __init__(self):
        self.sureler = defaultdict(lambda: deque(maxlen=300))

    def ekle(self, ad, ms):
        self.sureler[ad].append(ms)

    @contextmanager
    def asama(self, ad):
        bas = perf_counter()
        try:
            yield
        finally:
            self.ekle(ad, (perf_counter() - bas) * 1000)

    def ozet(self):
        return {ad: tuple(np.percentile(s, [50, 95])) for ad, s in self.sureler.items() if s}


class _NoktaPozFixture:
    def __init__(self, x: float = 0.5, y: float = 0.5, z: float = 0.0, visibility: float = 0.95):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.visibility = float(visibility)


import kimlik_imza  # noqa: E402


def _fixture_bes_poz_ve_kare(G: int, Y: int):
    """5 farklı renkli gövde ve MediaPipe 33 landmark standardında pozlar."""
    kare = np.full((Y, G, 3), 210, dtype=np.uint8)
    cv2.rectangle(kare, (0, int(Y * 0.7)), (G, Y), (160, 150, 140), -1)

    pozlar = []
    renkler = [
        (40, 40, 220),   # Kırmızı
        (40, 200, 40),   # Yeşil
        (220, 100, 30),  # Mavi
        (30, 210, 230),  # Sarı
        (200, 50, 200),  # Magenta
    ]
    xs = [0.16, 0.33, 0.50, 0.67, 0.84]

    for k, cx in enumerate(xs):
        pts = [_NoktaPozFixture(cx, 0.5, 0.0, 0.95) for _ in range(33)]

        # Burun (0) ve Gözler (2, 5)
        pts[0] = _NoktaPozFixture(cx, 0.20, 0.0, 0.95)
        pts[2] = _NoktaPozFixture(cx - 0.015, 0.18, 0.0, 0.95)
        pts[5] = _NoktaPozFixture(cx + 0.015, 0.18, 0.0, 0.95)

        # Omuzlar (11, 12)
        pts[11] = _NoktaPozFixture(cx - 0.045, 0.34, 0.0, 0.95)
        pts[12] = _NoktaPozFixture(cx + 0.045, 0.34, 0.0, 0.95)

        # Bilekler (15, 16) - burun seviyesi altında (normal durum)
        pts[15] = _NoktaPozFixture(cx - 0.06, 0.55, 0.0, 0.95)
        pts[16] = _NoktaPozFixture(cx + 0.06, 0.55, 0.0, 0.95)

        # Kalçalar (23, 24)
        pts[23] = _NoktaPozFixture(cx - 0.035, 0.62, 0.0, 0.95)
        pts[24] = _NoktaPozFixture(cx + 0.035, 0.62, 0.0, 0.95)

        pozlar.append(pts)

        # Kareye renkli gövde poligonu ve baş çiz
        p11_px = (int((cx - 0.045) * G), int(0.34 * Y))
        p12_px = (int((cx + 0.045) * G), int(0.34 * Y))
        p24_px = (int((cx + 0.035) * G), int(0.62 * Y))
        p23_px = (int((cx - 0.035) * G), int(0.62 * Y))
        poly = np.array([p11_px, p12_px, p24_px, p23_px], dtype=np.int32)
        cv2.fillPoly(kare, [poly], renkler[k])

        cv2.circle(kare, (int(cx * G), int(0.18 * Y)), int(0.035 * Y), (25, 30, 45), -1)
        cv2.circle(kare, (int(cx * G), int(0.20 * Y)), int(0.025 * Y), (160, 190, 230), -1)

    return kare, pozlar


def kiyas(kareler=300):
    import cekirdek as ck
    from stant_app import DENEYIMLER

    yeni_oyunlar = {"p_islem_dizisi", "p_cumle_dizisi"}
    basarisiz = False

    print("Oyun | isle p50 ms | p95 ms (kamera ve algı hariç)")
    for ad in DENEYIMLER:
        if ad in yeni_oyunlar:
            oyun = importlib.import_module(ad).Prototip(ck.Ses(acik=False))
            kare_ref, pozlar = _fixture_bes_poz_ve_kare(ck.G, ck.Y)
            poz_idler = [101, 102, 103, 104, 105]
            algi = ck.Algi(pozlar=pozlar, poz_id=poz_idler)

            oyun.baslat(algi, 1000.0)
            if oyun.durum != "oyun" or len(oyun.oyuncular) != 5:
                raise RuntimeError(f"{ad}: beş kişilik tur başlatılamadı")

            # 10 ısınma karesi (ölçüme dahil edilmez)
            for i in range(10):
                kare = kare_ref.copy()
                oyun.isle(kare, algi, 1000.0 + i / 60.0)

            prof = Profil()
            for i in range(kareler):
                kare = kare_ref.copy()
                with prof.asama(ad):
                    oyun.isle(kare, algi, 1000.0 + (10 + i) / 60.0)

            p50, p95 = prof.ozet()[ad]
            print(f"{ad} | {p50:.2f} | {p95:.2f}")

            # Yeni oyun hedef kontrolü: medyan <= 14ms, p95 <= 25ms
            if p50 > 14.0 or p95 > 25.0:
                basarisiz = True
        else:
            oyun = importlib.import_module(ad).Prototip(ck.Ses(acik=False))
            algi = ck.Algi(eller=[ck.sahte_el()], yuzler=[ck.sahte_yuz()], blend=[{}], el_id=[1], yuz_id=[2])
            if hasattr(oyun, "baslat"):
                oyun.baslat(algi, 1000.0)
            elif not isinstance(getattr(type(oyun), "durum", None), property):
                oyun.durum = "oyun"
            prof = Profil()
            for i in range(kareler + 10):
                kare = np.zeros((ck.Y, ck.G, 3), np.uint8)
                with prof.asama(ad):
                    oyun.isle(kare, algi, 1000 + i / 60)
            p50, p95 = prof.ozet()[ad]
            print(f"{ad} | {p50:.2f} | {p95:.2f}")

    # 5 Kişi İmza Çıkarımı Ölçümü (10Hz, bağımsız kimlikler)
    kare_ref, pozlar = _fixture_bes_poz_ve_kare(ck.G, ck.Y)
    for i in range(10):
        pids = [1000 + i * 10 + j for j in range(5)]
        for pid, lm in zip(pids, pozlar):
            kimlik_imza.cikar(kare_ref, lm)

    prof_imza = Profil()
    ad_imza = "5_imza"
    for i in range(kareler):
        pids = [2000 + i * 10 + j for j in range(5)]
        with prof_imza.asama(ad_imza):
            for pid, lm in zip(pids, pozlar):
                kimlik_imza.cikar(kare_ref, lm)

    imza_p50, imza_p95 = prof_imza.ozet()[ad_imza]
    print(f"{ad_imza} | {imza_p50:.2f} | {imza_p95:.2f}")

    # İmza çıkarımı hedef kontrolü: medyan <= 2ms
    if imza_p50 > 2.0:
        basarisiz = True

    return 1 if basarisiz else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kiyas", action="store_true")
    parser.add_argument("--kareler", type=int, default=300)
    parser.add_argument("--flagfail", action="store_true")
    args = parser.parse_args()
    if args.kiyas:
        kod = kiyas(args.kareler)
        if kod != 0:
            sys.exit(kod)
