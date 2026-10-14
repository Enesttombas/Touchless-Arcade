import json
import math
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

PROJE_KOK = Path(__file__).resolve().parents[1] / "prototipler"
if str(PROJE_KOK) not in sys.path:
    sys.path.insert(0, str(PROJE_KOK))

import cekirdek
import dizi_motor
import dizi_olcum
import kimlik_imza


def _sentetik_poz_uret(cx: float, cy: float, genislik: float = 0.16, yukseklik: float = 0.40):
    noktalar = [cekirdek._NoktaPoz(cx, cy, 0.0, visibility=0.1) for _ in range(33)]

    # 0: Burun, 2: Sol goz, 5: Sag goz
    noktalar[0] = cekirdek._NoktaPoz(cx, cy - yukseklik * 0.38, 0.0, 0.95)
    noktalar[2] = cekirdek._NoktaPoz(cx - 0.035, cy - yukseklik * 0.40, 0.0, 0.95)
    noktalar[5] = cekirdek._NoktaPoz(cx + 0.035, cy - yukseklik * 0.40, 0.0, 0.95)

    # 11: Sol omuz, 12: Sag omuz
    noktalar[11] = cekirdek._NoktaPoz(cx - genislik * 0.5, cy - yukseklik * 0.15, 0.0, 0.95)
    noktalar[12] = cekirdek._NoktaPoz(cx + genislik * 0.5, cy - yukseklik * 0.15, 0.0, 0.95)

    # 23: Sol kalca, 24: Sag kalca
    noktalar[23] = cekirdek._NoktaPoz(cx - genislik * 0.45, cy + yukseklik * 0.25, 0.0, 0.95)
    noktalar[24] = cekirdek._NoktaPoz(cx + genislik * 0.45, cy + yukseklik * 0.25, 0.0, 0.95)

    # 13,14: Dirsekler; 15,16: Bilekler; 25,26: Dizler; 27,28: Ayak bilekleri
    noktalar[13] = cekirdek._NoktaPoz(cx - genislik * 0.65, cy + yukseklik * 0.05, 0.0, 0.9)
    noktalar[14] = cekirdek._NoktaPoz(cx + genislik * 0.65, cy + yukseklik * 0.05, 0.0, 0.9)
    noktalar[15] = cekirdek._NoktaPoz(cx - genislik * 0.70, cy + yukseklik * 0.22, 0.0, 0.9)
    noktalar[16] = cekirdek._NoktaPoz(cx + genislik * 0.70, cy + yukseklik * 0.22, 0.0, 0.9)
    noktalar[25] = cekirdek._NoktaPoz(cx - genislik * 0.40, cy + yukseklik * 0.55, 0.0, 0.9)
    noktalar[26] = cekirdek._NoktaPoz(cx + genislik * 0.40, cy + yukseklik * 0.55, 0.0, 0.9)
    noktalar[27] = cekirdek._NoktaPoz(cx - genislik * 0.40, cy + yukseklik * 0.85, 0.0, 0.9)
    noktalar[28] = cekirdek._NoktaPoz(cx + genislik * 0.40, cy + yukseklik * 0.85, 0.0, 0.9)

    return noktalar


@pytest.fixture
def uc_sentetik_oyuncu_fiksturu():
    H, W = 720, 1280
    kare = np.full((H, W, 3), 40, dtype=np.uint8)

    merkezler = [0.22, 0.50, 0.78]
    govde_renkleri = [(20, 20, 210), (30, 200, 30), (210, 40, 30)]
    sac_renkleri = [(10, 10, 10), (40, 80, 140), (70, 180, 230)]

    pozlar = []
    for cx, g_renk, s_renk in zip(merkezler, govde_renkleri, sac_renkleri):
        poz = _sentetik_poz_uret(cx=cx, cy=0.45, genislik=0.16, yukseklik=0.40)
        pozlar.append(poz)

        px1 = int((cx - 0.09) * W)
        px2 = int((cx + 0.09) * W)
        py1 = int((0.45 - 0.07) * H)
        py2 = int((0.45 + 0.12) * H)
        cv2.rectangle(kare, (px1, py1), (px2, py2), g_renk, -1)

        sx1 = int((cx - 0.05) * W)
        sx2 = int((cx + 0.05) * W)
        sy1 = int((0.45 - 0.24) * H)
        sy2 = int((0.45 - 0.15) * H)
        cv2.rectangle(kare, (sx1, sy1), (sx2, sy2), s_renk, -1)

    return kare, pozlar


def _motor_olustur(tohum: int = 42):
    from p_islem_dizisi import Prototip
    return Prototip(cekirdek.Ses(acik=False), rng=np.random.default_rng(tohum))


def _motor_baslat(engine, algi, t: float):
    if hasattr(engine, "baslat"):
        try:
            engine.baslat(algi, t)
        except TypeError:
            engine.baslat(algi=algi, simdi=t)


def _motor_isle(engine, kare, algi, t: float):
    if hasattr(engine, "isle"):
        try:
            return engine.isle(kare, algi, t)
        except TypeError:
            try:
                return engine.isle(algi, t)
            except TypeError:
                return engine.isle(kare=kare, algi=algi, simdi=t)
    return None


def _replay(dosya_yolu: str, **kwargs):
    if hasattr(dizi_olcum, "tekrar_oynat"):
        return dizi_olcum.tekrar_oynat(dosya_yolu, **kwargs)
    if hasattr(dizi_olcum, "replay"):
        return dizi_olcum.replay(dosya_yolu, **kwargs)
    raise AttributeError("dizi_olcum modulu tekrar_oynat veya replay fonksiyonu icermelidir")


def test_dizikayit_ve_jsonl_33nokta_aday_imzalar_ve_metadata(tmp_path, uc_sentetik_oyuncu_fiksturu):
    kare, pozlar = uc_sentetik_oyuncu_fiksturu
    cikis_dosyasi = str(tmp_path / "olcum_test.jsonl")

    kaydedici = dizi_olcum.DiziKayit(dosya_yolu=cikis_dosyasi)
    kaydedici.baslat(oyun_adi="IslemDizisi", tohum=42)

    engine = _motor_olustur(tohum=42)
    algi = cekirdek.Algi(
        pozlar=pozlar,
        poz_id=[101, 102, 103],
        yuzler=[cekirdek.sahte_yuz(0.22, 0.3), cekirdek.sahte_yuz(0.50, 0.3), cekirdek.sahte_yuz(0.78, 0.3)],
    )
    algi.tahmini = []

    _motor_baslat(engine, algi, 100.0)
    algi.tahmini = [("poz", 101)]

    for i in range(5):
        t = 100.0 + i * 0.033
        _motor_isle(engine, kare, algi, t)
        kaydedici.kare_ekle(engine, algi, t, kare=kare)

    dondurulen_yol = kaydedici.durdur()
    assert dondurulen_yol == cikis_dosyasi
    assert os.path.exists(cikis_dosyasi), "Kaydedici durdurulduktan sonra JSONL dosyasi bulunamadi"

    satirlar = []
    with open(cikis_dosyasi, "r", encoding="utf-8") as f:
        for satir_no, ham in enumerate(f, 1):
            assert "base64" not in ham.lower(), f"Satir {satir_no} base64 verisi iceriyor, goruntu gomulmemeli"
            assert "data:image" not in ham.lower(), f"Satir {satir_no} data URI iceriyor"
            satirlar.append(json.loads(ham))

    assert len(satirlar) >= 5, "JSONL dosyasinda beklenen satir sayisina ulasilamadi"

    tum_metin = json.dumps(satirlar)
    assert "IslemDizisi" in tum_metin, "RNG/oyun adi metadatada bulunamadi"
    assert "42" in tum_metin, "RNG tohum metadatada bulunamadi"

    kare_satirlari = [
        s for s in satirlar if ("pozlar" in s or "landmarks" in s or "aday_imzalar" in s or "esleme" in s)
    ]
    assert len(kare_satirlari) >= 5, "Kare kayitlari ayrilamadi"

    for idx, k_veri in enumerate(kare_satirlari):
        poz_listesi = k_veri.get("pozlar") or k_veri.get("landmarks") or []
        assert len(poz_listesi) == 3, f"Kare {idx} icerisinde 3 poz bekleniyordu"

        for p_idx, tek_poz in enumerate(poz_listesi):
            lm = tek_poz.get("landmarks", tek_poz) if isinstance(tek_poz, dict) else tek_poz
            assert len(lm) == 33, f"Kare {idx} poz {p_idx} 33 nokta icermiyor"
            for pt_idx, pt in enumerate(lm):
                if isinstance(pt, dict):
                    x, y, z, v = pt["x"], pt["y"], pt["z"], pt.get("visibility", pt.get("v", 1.0))
                else:
                    x, y, z, v = pt[0], pt[1], pt[2], pt[3]
                assert all(isinstance(deger, (int, float)) and math.isfinite(deger) for deger in (x, y, z, v)), (
                    f"Kare {idx} poz {p_idx} nokta {pt_idx} sayisal ve sonlu degil"
                )

        imzalar = k_veri.get("aday_imzalar") or k_veri.get("imzalar")
        assert imzalar is not None, f"Kare {idx} aday imza verisi icermiyor"
        imza_oge_listesi = list(imzalar.values()) if isinstance(imzalar, dict) else imzalar
        assert len(imza_oge_listesi) == 3, f"Kare {idx} tum 3 aday poz icin imza icermeli"

        for aday_idx, imza in enumerate(imza_oge_listesi):
            assert "govde" in imza and imza["govde"] is not None, f"Aday {aday_idx} govde imzasi icermiyor"
            govde = imza["govde"]
            assert isinstance(govde.get("hist"), list) and len(govde["hist"]) > 0
            assert isinstance(govde.get("lab"), list) and len(govde["lab"]) == 3
            if imza.get("sac") is not None:
                sac = imza["sac"]
                assert isinstance(sac.get("hist"), list) and len(sac["hist"]) > 0
                assert isinstance(sac.get("lab"), list) and len(sac["lab"]) == 3

        assert any(k in k_veri for k in ("esleme", "mapping", "kimlik_haritasi", "stabil_esleme")), (
            f"Kare {idx} stabil->poz mapping yapisi barindirmiyor"
        )
        assert any(k in k_veri for k in ("tahmini", "tahminler", "predicted", "bayraklar")), (
            f"Kare {idx} predicted/tahmini bayrak verisi barindirmiyor"
        )

        if "olaylar" in k_veri or "events" in k_veri:
            olaylar = k_veri.get("olaylar", k_veri.get("events"))
            assert isinstance(olaylar, (list, tuple)), f"Kare {idx} olaylar liste/tuple olmali"


def test_etiketle_d_y_gecis_sonrasi_atamasi(tmp_path, uc_sentetik_oyuncu_fiksturu):
    kare, pozlar = uc_sentetik_oyuncu_fiksturu
    cikis_dosyasi = str(tmp_path / "etiket_test.jsonl")

    kaydedici = dizi_olcum.DiziKayit(dosya_yolu=cikis_dosyasi)
    kaydedici.baslat(oyun_adi="IslemDizisi", tohum=42)

    engine = _motor_olustur(tohum=42)
    algi = cekirdek.Algi(pozlar=pozlar, poz_id=[1, 2, 3])
    algi.tahmini = []
    _motor_baslat(engine, algi, 110.0)

    for i in range(3):
        t = 110.0 + i * 0.033
        _motor_isle(engine, kare, algi, t)
        kaydedici.kare_ekle(engine, algi, t, kare=kare)

    # Gecis sonrasi operator tekil atama uzerinden "D" veya "Y" etiketler (K yalnizca toggle)
    kaydedici.etiketle("D", 110.15)
    kaydedici.kare_ekle(engine, algi, 110.20, kare=kare)
    kaydedici.etiketle("Y", 110.25)

    yol = kaydedici.durdur()
    assert os.path.exists(yol)

    with open(yol, "r", encoding="utf-8") as f:
        metin = f.read()

    assert "D" in metin, "Operator tarafindan atanan 'D' etiketi kayda gecmedi"
    assert "Y" in metin, "Operator tarafindan atanan 'Y' etiketi kayda gecmedi"
    rapor = _replay(yol)
    assert rapor["ozet"]["canli_dogruluk"] == .5
    assert rapor["ozet"]["dogruluk"] == .5
    assert rapor["ozet"]["sessiz_yanlis"] == 1


def test_sayisal_replay_imzasiz_ve_cikar_cagrilmama_garantisi(tmp_path, uc_sentetik_oyuncu_fiksturu, monkeypatch):
    kare, pozlar = uc_sentetik_oyuncu_fiksturu
    cikis_dosyasi = str(tmp_path / "sayisal_replay.jsonl")

    kaydedici = dizi_olcum.DiziKayit(dosya_yolu=cikis_dosyasi)
    kaydedici.baslat(oyun_adi="IslemDizisi", tohum=42)

    engine = _motor_olustur(tohum=42)
    algi = cekirdek.Algi(pozlar=pozlar, poz_id=[10, 20, 30])
    algi.tahmini = []
    _motor_baslat(engine, algi, 200.0)

    for i in range(4):
        t = 200.0 + i * 0.033
        _motor_isle(engine, kare, algi, t)
        kaydedici.kare_ekle(engine, algi, t, kare=kare)

    kaydedici.etiketle("D", 200.12)
    yol = kaydedici.durdur()

    def sahte_cikar(*args, **kwargs):
        raise AssertionError("Sayisal replay sirasinda goruntuden cikar() cagrisi yapilamaz!")

    monkeypatch.setattr(kimlik_imza, "cikar", sahte_cikar)
    monkeypatch.setattr(dizi_motor, "cikar", sahte_cikar, raising=False)

    rapor_hibrit = _replay(yol)
    assert rapor_hibrit["esleme"][-1]["esleme"]
    rapor = _replay(yol, imzasiz=True)
    assert rapor["esleme"][-1]["esleme"]

    assert isinstance(rapor, dict), "Replay sonuclari yapilandirilmis sozluk nesnesi dondurmelidir"
    assert any(k in rapor for k in ("esleme", "mapping", "olaylar", "events", "kareler", "ozet")), (
        "Replay raporunda esleme veya olay ciktisi bulunamadi"
    )


def test_replay_belirlenimcilik_ve_dogruluk_sadece_etiketle(tmp_path, uc_sentetik_oyuncu_fiksturu):
    kare, pozlar = uc_sentetik_oyuncu_fiksturu
    cikis_dosyasi = str(tmp_path / "determinizm.jsonl")

    kaydedici = dizi_olcum.DiziKayit(dosya_yolu=cikis_dosyasi)
    kaydedici.baslat(oyun_adi="IslemDizisi", tohum=42)

    engine = _motor_olustur(tohum=42)
    algi = cekirdek.Algi(pozlar=pozlar, poz_id=[1, 2, 3])
    algi.tahmini = []
    _motor_baslat(engine, algi, 300.0)

    for i in range(4):
        t = 300.0 + i * 0.033
        _motor_isle(engine, kare, algi, t)
        kaydedici.kare_ekle(engine, algi, t, kare=kare)

    yol = kaydedici.durdur()

    rapor1 = _replay(yol)
    rapor2 = _replay(yol)

    assert isinstance(rapor1, dict) and isinstance(rapor2, dict)
    assert rapor1 == rapor2
    assert len(rapor1["esleme"][-1]["esleme"]) == 3

    esleme1 = rapor1.get("esleme", rapor1.get("mapping", rapor1.get("ozet", {}).get("esleme")))
    esleme2 = rapor2.get("esleme", rapor2.get("mapping", rapor2.get("ozet", {}).get("esleme")))
    assert esleme1 == esleme2, "Ayni kaydin tekrar oynatilmasinda esleme sonuclari birebir ayni olmalidir"

    olay1 = rapor1.get("olaylar", rapor1.get("events", rapor1.get("ozet", {}).get("olaylar")))
    olay2 = rapor2.get("olaylar", rapor2.get("events", rapor2.get("ozet", {}).get("olaylar")))
    assert olay1 == olay2, "Ayni kaydin tekrar oynatilmasinda motor olaylari birebir ayni olmalidir"

    ozet = rapor1.get("ozet", rapor1)
    dogruluk = ozet.get("dogruluk", ozet.get("accuracy"))
    assert dogruluk is None or (isinstance(dogruluk, str) and dogruluk.lower() in ("yok", "na", "none", "")), (
        "D/Y etiketleri girilmediginde replay sahte dogruluk (accuracy) uretmemelidir"
    )


def test_kare_ekle_opsiyonel_goruntu(tmp_path, uc_sentetik_oyuncu_fiksturu):
    kare, pozlar = uc_sentetik_oyuncu_fiksturu
    cikis_dosyasi = str(tmp_path / "opsiyonel_kare.jsonl")

    kaydedici = dizi_olcum.DiziKayit(dosya_yolu=cikis_dosyasi)
    kaydedici.baslat(oyun_adi="IslemDizisi", tohum=42)

    engine = _motor_olustur(tohum=42)
    algi = cekirdek.Algi(pozlar=pozlar, poz_id=[1, 2, 3])
    algi.tahmini = []
    _motor_baslat(engine, algi, 400.0)

    # kare parametresi opsiyoneldir (None veya belirtilmeden cagirildiginda basarili calismalidir)
    _motor_isle(engine, kare, algi, 400.0)
    kaydedici.kare_ekle(engine, algi, 400.0)

    _motor_isle(engine, kare, algi, 400.033)
    kaydedici.kare_ekle(engine, algi, 400.033, kare=None)

    yol = kaydedici.durdur()
    assert os.path.exists(yol)

    with open(yol, "r", encoding="utf-8") as f:
        satirlar = [line.strip() for line in f if line.strip()]
    assert len(satirlar) >= 2, "Opsiyonel kare ile kaydedilen satirlar dosyaya yazilmalidir"
