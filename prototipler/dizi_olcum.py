"""İnsan Dizisi ölçüm, deterministik tekrar ve doğrulama aracı.

Kamera ve operatör kayıtlarını JSONL formatında depolar, sentetik veya gerçek
kayıtları kamera olmaksızın motora tekrar oynatır, 8 adet durum önizleme
PNG'si üretir ve 2000 karelik yoğun gürültü testini yürütür.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np

# Prototip ve motor bağımlılıklarını çalışma yoluna ekle
_mevcut_dizin = Path(__file__).resolve().parent
if str(_mevcut_dizin) not in sys.path:
    sys.path.insert(0, str(_mevcut_dizin))

from cekirdek import G, Y, Algi, Ses
from dizi_motor import RENKLER, DiziMotor, DiziOyuncu, KarismaKaydi
from kimlik_imza import cikar
import p_cumle_dizisi
import p_islem_dizisi


# -----------------------------------------------------------------------------
# Sentetik Poz ve Landmark Yardımcıları
# -----------------------------------------------------------------------------
@dataclass
class _SentetikNokta:
    x: float
    y: float
    z: float = 0.0
    visibility: float = 0.95


def sentetik_33_poz(
    cx: float,
    cy: float = 0.55,
    omuz_w: float = 0.12,
    el_yukarda: bool = False,
    gorunurluk: float = 0.95,
) -> List[_SentetikNokta]:
    """MediaPipe uyumlu 33 landmark sentetik poz üretir."""
    pts = [_SentetikNokta(float(cx), float(cy), 0.0, visibility=gorunurluk) for _ in range(33)]

    # Burun ve Gözler
    pts[0] = _SentetikNokta(cx, cy - 0.28, 0.0, visibility=gorunurluk)
    pts[2] = _SentetikNokta(cx - 0.02, cy - 0.30, 0.0, visibility=gorunurluk)
    pts[5] = _SentetikNokta(cx + 0.02, cy - 0.30, 0.0, visibility=gorunurluk)

    # Omuzlar
    pts[11] = _SentetikNokta(cx - omuz_w * 0.5, cy - 0.18, 0.0, visibility=gorunurluk)
    pts[12] = _SentetikNokta(cx + omuz_w * 0.5, cy - 0.18, 0.0, visibility=gorunurluk)

    # Kalçalar
    pts[23] = _SentetikNokta(cx - omuz_w * 0.35, cy + 0.18, 0.0, visibility=gorunurluk)
    pts[24] = _SentetikNokta(cx + omuz_w * 0.35, cy + 0.18, 0.0, visibility=gorunurluk)

    # Dirsek ve Bilekler
    if el_yukarda:
        pts[15] = _SentetikNokta(cx - 0.08, cy - 0.38, 0.0, visibility=gorunurluk)
        pts[16] = _SentetikNokta(cx + 0.08, cy - 0.38, 0.0, visibility=gorunurluk)
    else:
        pts[15] = _SentetikNokta(cx - omuz_w * 0.6, cy + 0.05, 0.0, visibility=gorunurluk)
        pts[16] = _SentetikNokta(cx + omuz_w * 0.6, cy + 0.05, 0.0, visibility=gorunurluk)

    # Diz ve Ayaklar
    pts[25] = _SentetikNokta(cx - omuz_w * 0.35, cy + 0.40, 0.0, visibility=gorunurluk)
    pts[26] = _SentetikNokta(cx + omuz_w * 0.35, cy + 0.40, 0.0, visibility=gorunurluk)
    pts[27] = _SentetikNokta(cx - omuz_w * 0.35, cy + 0.60, 0.0, visibility=gorunurluk)
    pts[28] = _SentetikNokta(cx + omuz_w * 0.35, cy + 0.60, 0.0, visibility=gorunurluk)

    return pts


def sentetik_kare_boya(
    kare: np.ndarray,
    poz_list: List[List[_SentetikNokta]],
    renkler: List[Tuple[int, int, int]],
) -> None:
    """Sentetik pozların gövdelerini belirgin renklerle doldurur."""
    h, w = kare.shape[:2]
    for lm, rnk in zip(poz_list, renkler):
        o1, o2 = lm[11], lm[12]
        k1, k2 = lm[23], lm[24]
        poly = np.array([
            [int(o1.x * w), int(o1.y * h)],
            [int(o2.x * w), int(o2.y * h)],
            [int(k2.x * w), int(k2.y * h)],
            [int(k1.x * w), int(k1.y * h)],
        ], dtype=np.int32)
        cv2.fillPoly(kare, [poly], rnk)
        # Saç/baş bölgesi
        b = lm[0]
        cv2.circle(kare, (int(b.x * w), int((b.y - 0.04) * h)), int(w * 0.025), rnk, -1)


# -----------------------------------------------------------------------------
# JSONL Kayıt Sınıfı (DiziKayit)
# -----------------------------------------------------------------------------
def _sayisal(veri):
    if isinstance(veri, np.ndarray):
        if veri.ndim > 1:
            raise ValueError("Kayıt görüntü içeremez")
        return veri.tolist()
    if isinstance(veri, np.generic):
        return veri.item()
    if isinstance(veri, dict):
        return {str(k): _sayisal(v) for k, v in veri.items()}
    if isinstance(veri, (list, tuple, set, deque)):
        return [_sayisal(v) for v in veri]
    if isinstance(veri, _SentetikNokta) or hasattr(veri, "x"):
        return {k: float(getattr(veri, k, d)) for k, d in (("x", 0), ("y", 0), ("z", 0), ("visibility", 1))}
    return veri


def _vektor(veri):
    if isinstance(veri, dict):
        return {k: np.asarray(v, dtype=np.float32) if k in ("hist", "lab") else _vektor(v) for k, v in veri.items()}
    return veri


_DURUM_ALANLARI = (
    "N", "faz", "durum", "soru_no", "skor", "toplam_sure", "simdi",
    "kanonik_cevap", "mevcut_soru_kartlar", "dagitim_baslangic_t", "soru_baslangic_t",
    "sayim_baslangic_t", "sayim_gecen", "bozulma_t", "son_tik_sn", "kutlama_t",
    "eksik_baslangic_t", "durakla_t", "sonuc_baslangic_t", "takim_adi", "gecmis_skorlar",
    "en_iyiler", "_onceki_sira", "_lobi_stabil_sayi", "_lobi_stabil_t", "_lobi_idler", "_operator_n",
)
_ICERIK_ALANLARI = ("kartlar", "op", "n", "kayit", "_op_tarih", "_gecmis_id", "_tur_gecmisi", "_tur_idleri", "_tur_konu_sayaci")


def _durum_kopyasi(oyun):
    return _sayisal({
        "alanlar": {k: getattr(oyun, k) for k in _DURUM_ALANLARI},
        "oyuncular": {k: asdict(o) for k, o in oyun.oyuncular.items()},
        "imzalar": oyun.imzalar._kayitlar,
        "icerik": {k: getattr(oyun.icerik, k) for k in _ICERIK_ALANLARI if hasattr(oyun.icerik, k)},
        "rng": oyun.rng.bit_generator.state,
        "karismalar": [asdict(g) for g in oyun.aktif_karismalar],
        "belirsiz": [[list(k), t] for k, t in oyun.belirsiz_baslangic.items()],
        "zamanlar": {k: getattr(oyun, k) for k in ("_son_imza_t", "_lobi_el_t", "belirsiz_el_t", "pas_el_t")},
        "olaylar": oyun.olaylar,
    })


def _durum_yukle(oyun, durum):
    for k, v in durum["alanlar"].items():
        setattr(oyun, k, v)
    for k, v in durum["icerik"].items():
        if k == "_gecmis_id":
            v = deque(v, maxlen=15)
        elif k in ("_tur_gecmisi", "_tur_idleri"):
            v = set(v)
        setattr(oyun.icerik, k, v)
    oyun.rng.bit_generator.state = durum["rng"]
    oyun.oyuncular = {}
    for k, v in durum["oyuncular"].items():
        v = dict(v)
        v["poz"] = [_SentetikNokta(**p) for p in v["poz"]] if v.get("poz") else None
        v["orijinal_imza"] = _vektor(v.get("orijinal_imza"))
        oyun.oyuncular[int(k)] = DiziOyuncu(**v)
    oyun.imzalar._kayitlar = {int(k): _vektor(v) for k, v in durum["imzalar"].items()}
    oyun.aktif_karismalar = []
    for g in durum["karismalar"]:
        for k in ("giris_x", "giris_hiz", "giris_imza"):
            g[k] = {int(i): _vektor(v) for i, v in g[k].items()}
        oyun.aktif_karismalar.append(KarismaKaydi(**g))
    oyun.belirsiz_baslangic = {tuple(k): t for k, t in durum["belirsiz"]}
    for k, v in durum["zamanlar"].items():
        setattr(oyun, k, {int(i): t for i, t in v.items()})
    oyun.olaylar = [tuple(v) for v in durum["olaylar"]]


class DiziKayit:
    """Oyun esnasında nümerik poz ve imza verilerini JSONL dosyasına yazar."""

    def __init__(self, dosya_yolu: Optional[str] = None):
        if dosya_yolu:
            self.yol = Path(dosya_yolu)
        else:
            fd, tmp = tempfile.mkstemp(prefix="dizi_kayit_", suffix=".jsonl")
            os.close(fd)
            self.yol = Path(tmp)

        self._dosya = None
        self.aktif: bool = False
        self.son_etiket: Optional[str] = None
        self.etiketler: List[Dict[str, Any]] = []
        self._ilk = True
        self._aday_cache = {}
        self._son_esleme = {}
        self._son_belirsiz = False

    def baslat(self, oyun_adi: str = "IslemDizisi", tohum: int = 42) -> None:
        self._dosya = open(self.yol, "w", encoding="utf-8")
        self.aktif = True
        self._ilk = True
        self._aday_cache.clear()
        meta = {
            "tip": "metadata",
            "oyun": oyun_adi,
            "tohum": tohum,
            "baslangic_zaman": time.time(),
        }
        self._dosya.write(json.dumps(meta) + "\n")
        self._dosya.flush()

    def etiketle(self, etiket: str, t: float) -> None:
        """Operatörün D (Doğru) veya Y (Yanlış) etiketini işler."""
        if etiket.upper() in ("D", "Y"):
            self.son_etiket = etiket.upper()
            kayit = {"t": float(t), "etiket": self.son_etiket, "esleme": dict(self._son_esleme),
                     "belirsiz": self._son_belirsiz}
            self.etiketler.append(kayit)
            if self._dosya and self.aktif:
                self._dosya.write(json.dumps({"tip": "etiket", **kayit}) + "\n")
                self._dosya.flush()

    def kare_ekle(self, oyun: DiziMotor, algi: Optional[Algi], t: float, kare=None) -> None:
        if not self.aktif or self._dosya is None:
            return

        if self._ilk:
            self._dosya.write(json.dumps({"tip": "baslangic", "modul": oyun.__class__.__module__,
                                         "durum": _durum_kopyasi(oyun)}, allow_nan=False) + "\n")
            self._ilk = False

        poz_verileri = []
        if algi is not None:
            pids = getattr(algi, "poz_id", [])
            pozlar = getattr(algi, "pozlar", [])
            for pid, lm in zip(pids, pozlar):
                pts_seri = []
                for pt in lm:
                    pts_seri.append({
                        "x": float(getattr(pt, "x", 0.0)),
                        "y": float(getattr(pt, "y", 0.0)),
                        "z": float(getattr(pt, "z", 0.0)),
                        "v": float(getattr(pt, "visibility", 1.0)),
                    })
                poz_verileri.append({"poz_id": int(pid), "landmarks": pts_seri})

        adaylar = {}
        for pid, lm in zip(getattr(algi, "poz_id", []), getattr(algi, "pozlar", [])):
            onceki_t, vec = self._aday_cache.get(int(pid), (-float("inf"), None))
            if kare is not None and t - onceki_t >= .1 - 1e-9:
                vec = cikar(kare, lm)
                self._aday_cache[int(pid)] = (t, vec)
            adaylar[str(pid)] = _sayisal(vec)
        self._son_esleme = {str(k): int(o.poz_id) for k, o in oyun.oyuncular.items()}
        self._son_belirsiz = any(o.durum == "belirsiz" for o in oyun.oyuncular.values())

        # Motor oyuncuları ve imza vektörleri
        oyuncu_haritasi = {}
        for kid, o in oyun.oyuncular.items():
            imza_vec = oyun.imzalar.al(kid)
            hist_list = []
            lab_list = []
            if imza_vec and "govde" in imza_vec and imza_vec["govde"]:
                g = imza_vec["govde"]
                if "hist" in g:
                    hist_list = np.asarray(g["hist"], dtype=float).tolist()
                if "lab" in g:
                    lab_list = np.asarray(g["lab"], dtype=float).tolist()

            oyuncu_haritasi[str(kid)] = {
                "poz_id": int(o.poz_id),
                "kart": str(o.kart),
                "x": float(o.x),
                "durum": str(o.durum),
                "olgun": bool(oyun.imzalar.olgun(kid)),
                "imza_hist": hist_list,
                "imza_lab": lab_list,
            }

        kare_kaydi = {
            "tip": "kare",
            "t": float(t),
            "faz": str(oyun.faz),
            "soru_no": int(oyun.soru_no),
            "skor": int(oyun.skor),
            "pozlar": poz_verileri,
            "oyuncular": oyuncu_haritasi,
            "aday_imzalar": adaylar,
            "esleme": self._son_esleme,
            "tahmini": _sayisal(getattr(algi, "tahmini", [])),
            "olaylar": _sayisal(oyun.olaylar),
            "olay_sayisi": len(oyun.olaylar),
            "etiket": self.son_etiket,
        }
        self.son_etiket = None  # Tek karelik tüketim

        self._dosya.write(json.dumps(kare_kaydi, allow_nan=False) + "\n")
        self._dosya.flush()

    def durdur(self) -> str:
        self.aktif = False
        if self._dosya:
            self._dosya.close()
            self._dosya = None
        return str(self.yol)


# -----------------------------------------------------------------------------
# Deterministik Tekrar ve Raporlama (--tekrar)
# -----------------------------------------------------------------------------
def tekrar_oynat(dosya_yolu: str, imzasiz: bool = False) -> dict:
    """Kaydedilmiş aday imzalarıyla çalışır; kameradan imza çıkarmaz."""
    with open(dosya_yolu, encoding="utf-8") as f:
        satirlar = [json.loads(v) for v in f if v.strip()]
    meta = next(v for v in satirlar if v.get("tip") == "metadata")
    ilk = next(v for v in satirlar if v.get("tip") == "baslangic")
    modul = p_cumle_dizisi if "cumle" in ilk["modul"].lower() else p_islem_dizisi
    motor = modul.Prototip(Ses(acik=False), rng=np.random.default_rng(meta["tohum"]))
    _durum_yukle(motor, ilk["durum"])
    motor.imzasiz = bool(imzasiz)
    if imzasiz:
        motor.aktif_karismalar.clear()
        motor.belirsiz_baslangic.clear()
        for o in motor.oyuncular.values():
            o.durum = "normal"
    kareler = []
    belirsiz_sure = 0.0
    onceki_t = None
    bos = np.zeros((Y, G, 3), dtype=np.uint8)
    for k in (v for v in satirlar if v.get("tip") == "kare"):
        t = float(k["t"])
        pozlar = [[_SentetikNokta(pt["x"], pt["y"], pt.get("z", 0), pt.get("v", 1))
                   for pt in p["landmarks"]] for p in k["pozlar"]]
        algi = Algi(pozlar=pozlar, poz_id=[p["poz_id"] for p in k["pozlar"]])
        algi.tahmini = k.get("tahmini", [])
        motor.imza_override = {int(pid): _vektor(vec) for pid, vec in k["aday_imzalar"].items()}
        if onceki_t is not None:
            motor.isle(bos, algi, t)
        else:
            motor.son_algi = algi
            if imzasiz:
                motor._oyuncu_durumlarini_guncelle(motor._suzulmus_pozlar(algi))
        if any(o.durum == "belirsiz" for o in motor.oyuncular.values()):
            belirsiz_sure += max(0, t - onceki_t) if onceki_t is not None else 0
        onceki_t = t
        kareler.append({"t": t, "esleme": {str(i): int(o.poz_id) for i, o in motor.oyuncular.items()},
                        "belirsiz": any(o.durum == "belirsiz" for o in motor.oyuncular.values())})
    etiketler = [v for v in satirlar if v.get("tip") == "etiket"]
    bilinen = [v for v in etiketler if v.get("esleme")]
    degerlendirilen = 0
    yanlis = 0
    sessiz_yanlis = 0
    for v in bilinen:
        onceki = [k for k in kareler if k["t"] <= v["t"]]
        if not onceki:
            continue
        ayni = onceki[-1]["esleme"] == v["esleme"]
        # Y farklı bir eşlemeyi doğrulamaz; bu örnekte doğruluk bilinmiyor.
        if v["etiket"] == "Y" and not ayni:
            continue
        degerlendirilen += 1
        hatali = (v["etiket"] == "Y") or not ayni
        yanlis += int(hatali)
        sessiz_yanlis += int(hatali and not onceki[-1]["belirsiz"])
    ozet = {"kare_sayisi": len(kareler), "imzasiz": bool(imzasiz),
            "karisma": sum(e[0] == "karisma" for e in motor.olaylar),
            "cozum": sum(e[0] == "cozum" for e in motor.olaylar),
            "belirsiz_sure": round(belirsiz_sure, 6),
            "operator_d": sum(v["etiket"] == "D" for v in etiketler),
            "operator_y": sum(v["etiket"] == "Y" for v in etiketler),
            "sessiz_yanlis": sessiz_yanlis, "degerlendirilen": degerlendirilen,
            "bilinmeyen": len(etiketler) - degerlendirilen,
            "dogruluk": (1 - yanlis / degerlendirilen) if degerlendirilen else None,
            "canli_dogruluk": sum(v["etiket"] == "D" for v in etiketler) / len(etiketler) if etiketler else None}
    rapor = {"ozet": ozet, "esleme": kareler, "olaylar": _sayisal(motor.olaylar)}
    print(json.dumps(ozet, ensure_ascii=False))
    return rapor


# -----------------------------------------------------------------------------
# 8 Önizleme Ekran Görüntüsü Üretimi (--onizleme)
# -----------------------------------------------------------------------------
def onizlemeleri_uret(hedef_dizin: str) -> None:
    """Gerçek Prototip.isle çizim çağrılarıyla 8 durumu PNG olarak kaydeder."""
    cikti = Path(hedef_dizin)
    cikti.mkdir(parents=True, exist_ok=True)
    ses = Ses(acik=False)

    print(f"8 adet önizleme görüntüsü hazırlanıyor -> {cikti.resolve()}")

    # 1. LOBİ 4 KİŞİ (lobby4)
    motor = p_islem_dizisi.Prototip(ses=ses, rng=np.random.default_rng(101))
    motor.baslat(simdi=1.0)
    motor.faz = "lobi"
    pozlar_lobi = [sentetik_33_poz(0.20 + i * 0.20, cy=0.55) for i in range(4)]
    kare = np.zeros((Y, G, 3), dtype=np.uint8)
    sentetik_kare_boya(kare, pozlar_lobi, RENKLER[:4])
    algi = Algi(pozlar=pozlar_lobi, poz_id=[1, 2, 3, 4])
    res = motor.isle(kare, algi, simdi=1.5)
    cv2.imwrite(str(cikti / "01_lobi4.png"), res)

    # 2. DAĞITIM (dagit)
    motor = p_islem_dizisi.Prototip(ses=ses, rng=np.random.default_rng(102))
    motor.baslat(simdi=1.0)
    motor.N = 4
    for i in range(4):
        motor.oyuncular[i + 1] = DiziOyuncu(
            kimlik=i + 1, poz_id=i + 1, kart=f"K{i+1}", x=0.20 + i * 0.20,
            renk=RENKLER[i], durum="normal", omuz=0.10, y_bas=0.35, son_gorulme=2.0
        )
    motor.mevcut_soru_kartlar = ["(-25)", "+", "40", "15"]
    motor.faz = "dagit"
    motor.dagitim_baslangic_t = 2.0
    pozlar_dagit = [sentetik_33_poz(0.20 + i * 0.20, cy=0.55) for i in range(4)]
    kare = np.zeros((Y, G, 3), dtype=np.uint8)
    sentetik_kare_boya(kare, pozlar_dagit, RENKLER[:4])
    algi = Algi(pozlar=pozlar_dagit, poz_id=[1, 2, 3, 4])
    res = motor.isle(kare, algi, simdi=2.3)
    cv2.imwrite(str(cikti / "02_dagit.png"), res)

    # 3. İŞLEM DİZİSİ 5 KİŞİ (islem5) - Simge ve parantez okunurluğu
    motor = p_islem_dizisi.Prototip(ses=ses, rng=np.random.default_rng(103))
    motor.baslat(simdi=1.0)
    motor.N = 5
    motor.soru_no = 2
    motor.faz = "oyna"
    motor.soru_baslangic_t = 2.0
    kartlar_islem = ["(-37)", "×", "2", "=", "(-74)"]
    pozlar_islem = [sentetik_33_poz(0.12 + i * 0.19, cy=0.55) for i in range(5)]
    for i in range(5):
        motor.oyuncular[i + 1] = DiziOyuncu(
            kimlik=i + 1, poz_id=i + 1, kart=kartlar_islem[i], x=0.12 + i * 0.19,
            renk=RENKLER[i % len(RENKLER)], durum="normal", omuz=0.09, y_bas=0.35, son_gorulme=3.0
        )
    kare = np.zeros((Y, G, 3), dtype=np.uint8)
    sentetik_kare_boya(kare, pozlar_islem, RENKLER[:5])
    algi = Algi(pozlar=pozlar_islem, poz_id=[1, 2, 3, 4, 5])
    res = motor.isle(kare, algi, simdi=4.0)
    cv2.imwrite(str(cikti / "03_islem5.png"), res)

    # 4. BELİRSİZ KART "?" (belirsiz)
    motor = p_islem_dizisi.Prototip(ses=ses, rng=np.random.default_rng(104))
    motor.baslat(simdi=1.0)
    motor.N = 4
    motor.faz = "oyna"
    motor.soru_baslangic_t = 2.0
    kartlar_b = ["12", "+", "5", "17"]
    durumlar_b = ["normal", "belirsiz", "belirsiz", "normal"]
    pozlar_b = [sentetik_33_poz(0.20 + i * 0.20, cy=0.55) for i in range(4)]
    for i in range(4):
        motor.oyuncular[i + 1] = DiziOyuncu(
            kimlik=i + 1, poz_id=i + 1, kart=kartlar_b[i], x=0.20 + i * 0.20,
            renk=RENKLER[i], durum=durumlar_b[i], omuz=0.10, y_bas=0.35, son_gorulme=3.0
        )
    motor.belirsiz_baslangic[(2, 3)] = 3.0
    kare = np.zeros((Y, G, 3), dtype=np.uint8)
    sentetik_kare_boya(kare, pozlar_b, RENKLER[:4])
    algi = Algi(pozlar=pozlar_b, poz_id=[1, 2, 3, 4])
    res = motor.isle(kare, algi, simdi=4.2)
    cv2.imwrite(str(cikti / "04_belirsiz.png"), res)

    # 5. GERİ SAYIM (countdown)
    motor = p_islem_dizisi.Prototip(ses=ses, rng=np.random.default_rng(105))
    motor.baslat(simdi=1.0)
    motor.N = 4
    motor.faz = "oyna"
    motor.soru_baslangic_t = 2.0
    motor.sayim_baslangic_t = 3.0
    motor.sayim_gecen = 1.8
    kartlar_cd = ["8", "÷", "2", "4"]
    pozlar_cd = [sentetik_33_poz(0.20 + i * 0.20, cy=0.55) for i in range(4)]
    for i in range(4):
        motor.oyuncular[i + 1] = DiziOyuncu(
            kimlik=i + 1, poz_id=i + 1, kart=kartlar_cd[i], x=0.20 + i * 0.20,
            renk=RENKLER[i], durum="normal", omuz=0.10, y_bas=0.35, son_gorulme=4.8
        )
    kare = np.zeros((Y, G, 3), dtype=np.uint8)
    sentetik_kare_boya(kare, pozlar_cd, RENKLER[:4])
    algi = Algi(pozlar=pozlar_cd, poz_id=[1, 2, 3, 4])
    res = motor.isle(kare, algi, simdi=4.8)
    cv2.imwrite(str(cikti / "05_countdown.png"), res)

    # 6. DOĞRU DALGASI / KUTLAMA (dogru)
    motor = p_islem_dizisi.Prototip(ses=ses, rng=np.random.default_rng(106))
    motor.baslat(simdi=1.0)
    motor.N = 4
    motor.faz = "kutla"
    motor.kutlama_t = 5.0
    motor.skor = 850
    pozlar_d = [sentetik_33_poz(0.20 + i * 0.20, cy=0.55) for i in range(4)]
    for i in range(4):
        motor.oyuncular[i + 1] = DiziOyuncu(
            kimlik=i + 1, poz_id=i + 1, kart=["9", "×", "3", "27"][i], x=0.20 + i * 0.20,
            renk=RENKLER[i], durum="normal", omuz=0.10, y_bas=0.35, son_gorulme=5.4
        )
    kare = np.zeros((Y, G, 3), dtype=np.uint8)
    sentetik_kare_boya(kare, pozlar_d, RENKLER[:4])
    algi = Algi(pozlar=pozlar_d, poz_id=[1, 2, 3, 4])
    res = motor.isle(kare, algi, simdi=5.4)
    cv2.imwrite(str(cikti / "06_dogru.png"), res)

    # 7. CÜMLE DİZİSİ 4 KİŞİ (cumle4)
    motor_c = p_cumle_dizisi.Prototip(ses=ses, rng=np.random.default_rng(107))
    motor_c.baslat(simdi=1.0)
    motor_c.N = 4
    motor_c.faz = "oyna"
    motor_c.soru_baslangic_t = 2.0
    kelimeler = ["Kedi", "bardağı", "masadan", "düşürdü."]
    pozlar_c = [sentetik_33_poz(0.18 + i * 0.21, cy=0.55) for i in range(4)]
    for i in range(4):
        motor_c.oyuncular[i + 1] = DiziOyuncu(
            kimlik=i + 1, poz_id=i + 1, kart=kelimeler[i], x=0.18 + i * 0.21,
            renk=RENKLER[i], durum="normal", omuz=0.10, y_bas=0.35, son_gorulme=3.5
        )
    kare = np.zeros((Y, G, 3), dtype=np.uint8)
    sentetik_kare_boya(kare, pozlar_c, RENKLER[:4])
    algi = Algi(pozlar=pozlar_c, poz_id=[1, 2, 3, 4])
    res = motor_c.isle(kare, algi, simdi=3.5)
    cv2.imwrite(str(cikti / "07_cumle4.png"), res)

    # 8. SONUÇ EKRANI (result)
    motor_r = p_islem_dizisi.Prototip(ses=ses, rng=np.random.default_rng(108))
    motor_r.baslat(simdi=1.0)
    motor_r.skor = 4250
    motor_r.toplam_sure = 48.5
    motor_r._tur_sonuclandir()
    res = motor_r.isle(np.zeros((Y, G, 3), dtype=np.uint8), Algi(), simdi=2.0)
    cv2.imwrite(str(cikti / "08_result.png"), res)

    print("8 adet PNG başarıyla üretildi.")


# -----------------------------------------------------------------------------
# 2000 Kare Gürültü Dayanıklılık Testi (--gurultu)
# -----------------------------------------------------------------------------
def gurultu_testi() -> None:
    """Her iki oyun motoruna 2000 kare aşırı bozuk/gürültülü poz verisi sunar."""
    print("2000 karelik yoğun gürültü testi başlatılıyor...")
    ses = Ses(acik=False)
    motorlar = [
        ("İşlem Dizisi", p_islem_dizisi.Prototip(ses=ses, rng=np.random.default_rng(2001))),
        ("Cümle Dizisi", p_cumle_dizisi.Prototip(ses=ses, rng=np.random.default_rng(2002))),
    ]

    rng = np.random.default_rng(42)

    for ad, motor in motorlar:
        print(f" -> {ad} test ediliyor (2000 kare)...")
        t = 0.0
        baslangic = Algi(pozlar=[sentetik_33_poz(x) for x in [.12, .31, .5, .69, .88]], poz_id=[1,2,3,4,5])
        motor.baslat(baslangic, t)
        aktif_kare = 0

        for kare_idx in range(2000):
            t += 0.033

            # Rastgele 2-6 poz
            n_poz = int(rng.integers(2, 7))
            pozlar = []
            poz_idler = []

            for i in range(n_poz):
                pid = i + 1
                # Poz koordinatlarında aşırı gürültü, NaN veya None olasılığı
                cx = float(rng.uniform(-0.2, 1.2))
                cy = float(rng.uniform(0.1, 0.9))
                omuz = float(rng.uniform(0.01, 0.35))

                if rng.random() < 0.05:  # Eksik landmark dizisi
                    pts = [_SentetikNokta(cx, cy) for _ in range(int(rng.integers(5, 20)))]
                elif rng.random() < 0.05:  # NaN koordinatlar
                    pts = [_SentetikNokta(float("nan"), cy) for _ in range(33)]
                else:
                    el_up = bool(rng.random() < 0.3)
                    vis = float(rng.choice([0.1, 0.4, 0.95]))
                    pts = sentetik_33_poz(cx, cy=cy, omuz_w=omuz, el_yukarda=el_up, gorunurluk=vis)

                pozlar.append(pts)
                poz_idler.append(pid)

            # Rastgele boş kare ya da boyut bozukluğu
            if rng.random() < 0.02:
                kare = np.zeros((0, 0, 3), dtype=np.uint8)
            else:
                kare = np.zeros((Y, G, 3), dtype=np.uint8)

            algi = Algi(pozlar=pozlar, poz_id=poz_idler)

            if motor.faz in ("lobi", "sonuc"):
                motor.baslat(baslangic, t)
            if motor.faz != "lobi":
                aktif_kare += 1
            # Motor çağrısı - Asla istisna fırlatmamalı
            try:
                motor.isle(kare, algi, simdi=t)
            except Exception as e:
                print(f"HATA: {ad} motoru kare {kare_idx}'de çöktü: {e}")
                raise

        assert aktif_kare >= 500, aktif_kare
        print(f" -> {ad} 2000 kareyi tamamladı; {aktif_kare} aktif oyun karesi.")

    print("Gürültü dayanıklılık testi başarıyla sonuçlandı.\n")


# -----------------------------------------------------------------------------
# Komut Satırı Arayüzü (CLI)
# -----------------------------------------------------------------------------
def ana() -> None:
    parser = argparse.ArgumentParser(
        description="İnsan Dizisi Ölçüm, Tekrar Oynatma ve Görsel Kabul Aracı"
    )
    parser.add_argument(
        "--tekrar",
        type=str,
        metavar="FILE",
        help="JSONL kayıt dosyasını kameraya ihtiyaç duymadan motora tekrar oynatır",
    )
    parser.add_argument(
        "--imzasiz",
        action="store_true",
        help="Görünüş imzasını devre dışı bırakarak sadece konum takibi tabanını ölçer",
    )
    parser.add_argument(
        "--onizleme",
        action="store_true",
        help="8 adet durum kabul ekran görüntüsünü (PNG) üretir",
    )
    parser.add_argument(
        "--cikti",
        type=str,
        default="onizlemeler_dizi",
        metavar="DIR",
        help="Önizleme PNG'lerinin kaydedileceği hedef dizin (varsayılan: onizlemeler_dizi)",
    )
    parser.add_argument(
        "--gurultu",
        "--gürültü",
        action="store_true",
        dest="gurultu",
        help="Her iki oyun için 2000 karelik yoğun gürültü ve dayanıklılık testini koşar",
    )

    args = parser.parse_args()

    herhangi_bir_gorev = False

    if args.tekrar:
        herhangi_bir_gorev = True
        tekrar_oynat(args.tekrar, imzasiz=args.imzasiz)

    if args.onizleme:
        herhangi_bir_gorev = True
        onizlemeleri_uret(args.cikti)

    if args.gurultu:
        herhangi_bir_gorev = True
        gurultu_testi()

    if not herhangi_bir_gorev:
        parser.print_help()


if __name__ == "__main__":
    ana()
