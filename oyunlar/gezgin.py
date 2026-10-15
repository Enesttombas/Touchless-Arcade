"""Prototipler Gezgini: tüm kamera prototiplerini tek pencerede çalıştırır veya test eder."""
from __future__ import annotations

import importlib
import math
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, List

import cv2
import numpy as np

import cekirdek

KOK = Path(__file__).resolve().parent
HATA_DOSYASI = KOK / "hata.txt"


def hata_kaydet(e: BaseException) -> None:
    try:
        with open(HATA_DOSYASI, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {''.join(traceback.format_exception(e))}\n")
    except Exception:
        pass


def kesfet() -> List[Any]:
    """Aynı klasördeki p_*.py dosyalarını içe aktarır ve Prototip sınıfı olanları sıralar."""
    bulunanlar = []
    dizin = KOK

    for dosya in sorted(dizin.glob("p_*.py")):
        modul_adi = dosya.stem
        if "__k" in modul_adi and modul_adi not in os.environ.get("SECILI", ""):
            continue  # seçim kopyaları yalnız SECILI ile yüklenir
        try:
            mod = importlib.import_module(modul_adi)
            if hasattr(mod, "Prototip"):
                P = getattr(mod, "Prototip")
                sira = getattr(P, "SIRA", 99)
                ad = getattr(P, "AD", modul_adi)
                bulunanlar.append((sira, ad, mod))
        except Exception as e:
            sys.stderr.write(f"Prototip içe aktarılamadı [{modul_adi}]: {e}\n")
            traceback.print_exc(file=sys.stderr)

    bulunanlar.sort(key=lambda x: (x[0], x[1]))
    # SECILI="p_a,p_b": stant modu; yalnız bu prototipler, verilen sırayla
    secili = [s.strip() for s in os.environ.get("SECILI", "").split(",") if s.strip()]
    if secili:
        adlar = {item[2].__name__: item[2] for item in bulunanlar}
        return [adlar[s] for s in secili if s in adlar]
    return [item[2] for item in bulunanlar]


def onizleme(foto: str, cikti: str, kare_sayisi: int = 45) -> None:
    """Pencere AÇMADAN her prototip için yeni örnek oluşturur ve ekran görüntüleri üretir."""
    cikti_yol = Path(cikti)
    cikti_yol.mkdir(parents=True, exist_ok=True)

    orijinal_kare = cv2.imread(foto)
    if orijinal_kare is None:
        raise FileNotFoundError(f"Fotoğraf okunamadı: {foto}")
    orijinal_kare = cv2.resize(orijinal_kare, (cekirdek.G, cekirdek.Y))

    prototipler = kesfet()
    alg = cekirdek.Algilayici()
    ses = cekirdek.Ses(acik=False)

    son_kareler = []

    for mod in prototipler:
        mod_adi = mod.__name__
        proto = mod.Prototip(ses)
        ihtiyac = getattr(proto, "IHTIYAC", set())

        son_islenmis = None
        for i in range(kare_sayisi):
            # Yatayda sin ile ±40 px kaydırma
            kayma = int(40 * math.sin(i * 2 * math.pi / max(1, kare_sayisi)))
            M = np.float32([[1, 0, kayma], [0, 1, 0]])
            kare = cv2.warpAffine(
                orijinal_kare,
                M,
                (cekirdek.G, cekirdek.Y),
                borderMode=cv2.BORDER_REFLECT,
            )

            algi = alg.algila(kare, ihtiyac)

            # Prototip "el" istiyorsa ve algılanan el yoksa sahte el ekle
            if "el" in ihtiyac and not algi.eller:
                # Ekranı dolaşan işaret eli
                t_el = i / max(1, kare_sayisi)
                el_x = 0.5 + 0.3 * math.sin(t_el * 2 * math.pi)
                el_y = 0.5 + 0.2 * math.cos(t_el * 2 * math.pi)
                el1 = cekirdek.sahte_el(el_x, el_y, durum="isaret")
                el2 = cekirdek.sahte_el(0.2, 0.8, durum="avuc")
                algi.eller = [el1, el2]
                algi.el_taraf = ["Right", "Left"]
                algi.jestler = [None, "Open_Palm"]

            simdi = 1000.0 + i * 0.033
            son_islenmis = proto.isle(kare.copy(), algi, simdi)

        if son_islenmis is not None:
            cikti_dosya = cikti_yol / f"{mod_adi}.png"
            cv2.imwrite(str(cikti_dosya), son_islenmis)
            son_kareler.append((mod_adi, son_islenmis))

    # Kontakt sayfası oluşturma (3 sütunlu, her biri 640x360, üstünde modül adı)
    if son_kareler:
        sutun_sayisi = 3
        kw, kh = 640, 360
        toplam = len(son_kareler)
        satir_sayisi = (toplam + sutun_sayisi - 1) // sutun_sayisi
        kontakt = np.zeros((satir_sayisi * kh, sutun_sayisi * kw, 3), dtype=np.uint8)

        for idx, (mod_adi, k) in enumerate(son_kareler):
            r = idx // sutun_sayisi
            c = idx % sutun_sayisi
            kucuk = cv2.resize(k, (kw, kh), interpolation=cv2.INTER_AREA)
            # Üstünde modül adı yazan panel/yazı
            cekirdek.panel(kucuk, 0, 0, kw, 45, renk=(15, 15, 20), opak=0.7)
            cekirdek.yazi_koy(kucuk, mod_adi, 15, 8, 28, renk=cekirdek.SARI)
            cv2.rectangle(kucuk, (0, 0), (kw - 1, kh - 1), (80, 80, 80), 1)

            kontakt[r * kh : (r + 1) * kh, c * kw : (c + 1) * kw] = kucuk

        cv2.imwrite(str(cikti_yol / "kontakt.png"), kontakt)


def olc(foto: str, kare_sayisi: int = 40) -> None:
    """Pencere açmadan her prototip için algılama + işleme ortalama ms ve FPS'ini ölçer."""
    orijinal_kare = cv2.imread(foto)
    if orijinal_kare is None:
        raise FileNotFoundError(f"Fotoğraf okunamadı: {foto}")
    orijinal_kare = cv2.resize(orijinal_kare, (cekirdek.G, cekirdek.Y))

    prototipler = kesfet()
    alg = cekirdek.Algilayici()
    ses = cekirdek.Ses(acik=False)

    for mod in prototipler:
        mod_adi = mod.__name__
        proto = mod.Prototip(ses)
        ihtiyac = getattr(proto, "IHTIYAC", set())

        sureler = []
        for i in range(kare_sayisi):
            t0 = time.perf_counter()
            algi = alg.algila(orijinal_kare, ihtiyac)
            proto.isle(orijinal_kare.copy(), algi, 1000.0 + i * 0.033)
            sureler.append(time.perf_counter() - t0)

        # İlk 3 kareyi ısınma olarak at
        gecerli = sureler[3:] if len(sureler) > 5 else sureler
        ort_sure = float(np.mean(gecerli)) if gecerli else 0.001
        ort_ms = ort_sure * 1000.0
        fps = 1000.0 / ort_ms if ort_ms > 0 else 0

        print(f"[{mod_adi}] {ort_ms:.1f} ms/kare  ~{fps:.0f} FPS  (ihtiyac={ihtiyac})")


def main() -> None:
    prototipler = kesfet()
    if not prototipler:
        print("Çalıştırılacak prototip bulunamadı!")
        return

    kam_indeks = int(os.environ.get("KAMERA", "0"))
    kam = cekirdek.Kamera(kam_indeks)
    kam.start()

    alg = cekirdek.Algilayici()
    ses = cekirdek.Ses(acik=True)

    pencere = "Prototipler"
    cv2.namedWindow(pencere, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(pencere, cekirdek.G, cekirdek.Y)

    tam_ekran = os.environ.get("TAM_EKRAN") == "1"
    if tam_ekran:
        cv2.setWindowProperty(pencere, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    otomatik_sn = float(os.environ.get("OTOMATIK", "0"))

    ornekler: dict[int, Any] = {}
    secili_idx = 0

    def etkin_prototip():
        nonlocal secili_idx
        if secili_idx not in ornekler:
            mod = prototipler[secili_idx]
            ornekler[secili_idx] = mod.Prototip(ses)
        return ornekler[secili_idx]

    degisim_t = time.time()
    son_oto_t = time.time()
    son_hata_mesaji = None
    son_hata_t = 0.0

    try:
        while True:
            if kam.kare is None:
                time.sleep(0.01)
                k = cv2.waitKey(1) & 0xFF
                if k in (ord("q"), ord("Q"), 27):
                    break
                continue

            kare = kam.kare.copy()
            simdi = time.time()

            # Otomatik vitrin modu geçişi
            if otomatik_sn > 0 and (simdi - son_oto_t >= otomatik_sn):
                secili_idx = (secili_idx + 1) % len(oyunlar)
                degisim_t = simdi
                son_oto_t = simdi

            proto = etkin_prototip()
            ihtiyac = getattr(proto, "IHTIYAC", set())
            if otomatik_sn > 0:  # vitrin: kişi varlığını ölçmek için yüz hep algılanır
                ihtiyac = set(ihtiyac) | {"yuz"}

            try:
                algi = alg.algila(kare, ihtiyac)
                # Biri oynuyorken (yüz/el var ya da oyun sürüyor) vitrin geçişi ertelenir
                if algi.yuzler or algi.eller or getattr(proto, "durum", "") == "oyun":
                    son_oto_t = simdi
                kare = proto.isle(kare, algi, simdi)
            except Exception as e:
                hata_kaydet(e)
                son_hata_mesaji = f"hata: {type(e).__name__}"
                son_hata_t = simdi

            # Hata göstergesi
            if son_hata_mesaji and (simdi - son_hata_t < 3.0):
                cekirdek.panel(kare, 20, 20, 320, 70, renk=(0, 0, 80), opak=0.8, kenar=cekirdek.KIRMIZI)
                cekirdek.yazi_koy(kare, son_hata_mesaji, 30, 28, 28, renk=cekirdek.KIRMIZI)

            # Prototip geçiş bilgilendirme paneli (2.5 sn boyunca ortada büyük ad + açıklama)
            if simdi - degisim_t < 2.5:
                p_ad = getattr(proto, "AD", f"Prototip {secili_idx + 1}")
                p_aciklama = getattr(proto, "ACIKLAMA", "")
                pw, ph = 800, 150
                px0 = (cekirdek.G - pw) // 2
                py0 = (cekirdek.Y - ph) // 2
                cekirdek.panel(kare, px0, py0, px0 + pw, py0 + ph, renk=(15, 15, 25), opak=0.85, kenar=cekirdek.SARI)
                cekirdek.yazi_koy(kare, p_ad, cekirdek.G // 2, py0 + 20, 46, renk=cekirdek.SARI, hiza="orta")
                if p_aciklama:
                    cekirdek.yazi_koy(kare, p_aciklama, cekirdek.G // 2, py0 + 85, 26, renk=cekirdek.BEYAZ, hiza="orta")

            # Sağ altta küçük sabit ipucu
            if os.environ.get("SECIM"):  # kopya karşılaştırma: hangi dosya olduğu görünsün
                ipucu = f"{prototipler[secili_idx].__name__}   N/B: sonraki/önceki"
            if not os.environ.get("SECILI") or os.environ.get("SECIM"):  # stant modunda ipucu gizli
                ipucu = ipucu if os.environ.get("SECIM") else "1-9: prototip  N/B: sonraki/önceki"
                cekirdek.panel(kare, cekirdek.G - 410, cekirdek.Y - 45, cekirdek.G - 10, cekirdek.Y - 10, renk=(20, 20, 28), opak=0.7)
                cekirdek.yazi_koy(kare, ipucu, cekirdek.G - 20, cekirdek.Y - 40, 22, renk=(200, 200, 200), hiza="sag")

            cv2.imshow(pencere, kare)
            k = cv2.waitKey(1) & 0xFF

            if k in (ord("q"), ord("Q"), 27):
                break
            elif k in (ord("f"), ord("F")):
                tam_ekran = not tam_ekran
                cv2.setWindowProperty(
                    pencere,
                    cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN if tam_ekran else cv2.WINDOW_NORMAL,
                )
            elif k in (ord("n"), ord("N")):
                secili_idx = (secili_idx + 1) % len(oyunlar)
                degisim_t = simdi
                son_oto_t = simdi
            elif k in (ord("b"), ord("B")):
                secili_idx = (secili_idx - 1) % len(oyunlar)
                degisim_t = simdi
                son_oto_t = simdi
            elif ord("1") <= k <= ord("9"):
                istenen = k - ord("1")
                if istenen < len(oyunlar):
                    secili_idx = istenen
                    degisim_t = simdi
                    son_oto_t = simdi
            elif k == ord("0"):
                istenen = 9  # 10. prototip
                if istenen < len(oyunlar):
                    secili_idx = istenen
                    degisim_t = simdi
                    son_oto_t = simdi
            elif k != 255:
                # Diğer tuşlar etkin prototipin tus() fonksiyonuna aktarılır
                if hasattr(proto, "tus") and callable(getattr(proto, "tus")):
                    try:
                        proto.tus(k)
                    except Exception as e:
                        hata_kaydet(e)

            if cv2.getWindowProperty(pencere, cv2.WND_PROP_VISIBLE) < 1:
                break

    finally:
        kam.kapat()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--olc":
        olc(sys.argv[2])
    elif len(sys.argv) > 3 and sys.argv[1] == "--onizleme":
        kare_s = int(sys.argv[4]) if len(sys.argv) > 4 else 45
        onizleme(sys.argv[2], sys.argv[3], kare_sayisi=kare_s)
    else:
        main()
