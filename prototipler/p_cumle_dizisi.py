"""Cümle Dizisi - Oyuncuların baş üstü kelime kartlarıyla doğru cümle kurma oyunu."""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np

from dizi_motor import DiziMotor

AD = "Cümle Dizisi"
IHTIYAC = {"poz"}
KAPI = {"poz_omuz_min": 0.035}
POZ_YALNIZ = True


def _harf_sayisi(kelime: str) -> int:
    """Noktalama işaretleri sayılmadan kelimedeki harf/karakter sayısı."""
    noktalama = {".", ",", "!", "?", ":", ";", "…", "'", '"', "-", "—"}
    return sum(1 for c in kelime if c not in noktalama)


def _sema_dogrula(veri: dict[str, Any]) -> list[dict[str, Any]]:
    """Cümle bankası JSON şemasını doğrular; geçersizse ValueError fırlatır."""
    if not isinstance(veri, dict):
        raise ValueError("Cümle bankası kök elemanı sözlük (dict) olmalı.")
    cumleler = veri.get("cumleler")
    if not isinstance(cumleler, list):
        raise ValueError("Cümle bankasında 'cumleler' listesi bulunamadı.")

    id_kumesi: set[str] = set()
    n_sayilari: dict[int, int] = {3: 0, 4: 0, 5: 0}

    for idx, kayit in enumerate(cumleler):
        if not isinstance(kayit, dict):
            raise ValueError(f"Kayıt {idx} sözlük değil.")

        kayit_id = kayit.get("id")
        if not isinstance(kayit_id, str) or not kayit_id.strip():
            raise ValueError(f"Kayıt {idx}: geçersiz veya boş 'id'.")
        if kayit_id in id_kumesi:
            raise ValueError(f"Kayıt {idx}: tekrarlanan id '{kayit_id}'.")
        id_kumesi.add(kayit_id)

        konu = kayit.get("konu")
        if not isinstance(konu, str) or not konu.strip():
            raise ValueError(f"Kayıt {kayit_id}: geçerli bir 'konu' alanı yok.")

        kelimeler = kayit.get("kelimeler")
        if not isinstance(kelimeler, list):
            raise ValueError(f"Kayıt {kayit_id}: 'kelimeler' bir liste olmalı.")
        n = len(kelimeler)
        if n not in (3, 4, 5):
            raise ValueError(f"Kayıt {kayit_id}: kelime sayısı 3, 4 veya 5 olmalı; bulunan: {n}.")
        n_sayilari[n] += 1

        for k_idx, kelime in enumerate(kelimeler):
            if not isinstance(kelime, str) or not kelime:
                raise ValueError(f"Kayıt {kayit_id}: kelime {k_idx} boş veya metin değil.")
            if any(c.isspace() for c in kelime):
                raise ValueError(f"Kayıt {kayit_id}: kelime '{kelime}' içinde boşluk içeremez.")
            if _harf_sayisi(kelime) > 12:
                raise ValueError(f"Kayıt {kayit_id}: kelime '{kelime}' 12 harften uzun.")

        ilk_kelime = kelimeler[0]
        if not ilk_kelime[0].isupper():
            raise ValueError(f"Kayıt {kayit_id}: ilk kelime '{ilk_kelime}' büyük harfle başlamalı.")

        son_kelime = kelimeler[-1]
        if not son_kelime.endswith("."):
            raise ValueError(f"Kayıt {kayit_id}: son kelime '{son_kelime}' nokta ile bitmeli.")

        for ara_k in kelimeler[:-1]:
            if ara_k.endswith("."):
                raise ValueError(f"Kayıt {kayit_id}: ara kelime '{ara_k}' nokta içeremez.")

        kabul = kayit.get("kabul")
        if not isinstance(kabul, list) or len(kabul) == 0:
            raise ValueError(f"Kayıt {kayit_id}: 'kabul' boş olamaz.")

        kanonik_perm = list(range(n))
        kanonik_bulundu = False

        beklenen_indeksler = set(range(n))
        for p_idx, perm in enumerate(kabul):
            if not isinstance(perm, (list, tuple)) or len(perm) != n:
                raise ValueError(f"Kayıt {kayit_id}: kabul[{p_idx}] uzunluğu {n} olmalı.")
            perm_list = list(perm)
            if set(perm_list) != beklenen_indeksler:
                raise ValueError(f"Kayıt {kayit_id}: kabul[{p_idx}] geçerli bir 0..{n-1} permütasyonu değil.")
            # IPUCU_BUYUK_HARF kuralı: büyük harfli kelime (indeks 0) daima ilk kartta olmalı,
            # noktalı son kelime (indeks n-1) daima son kartta olmalı.
            if perm_list[0] != 0:
                raise ValueError(f"Kayıt {kayit_id}: kabul[{p_idx}] ilk kart büyük harfli (0) olmalı.")
            if perm_list[-1] != n - 1:
                raise ValueError(f"Kayıt {kayit_id}: kabul[{p_idx}] son kart noktalı ({n-1}) olmalı.")
            if perm_list == kanonik_perm:
                kanonik_bulundu = True

        if not kanonik_bulundu:
            raise ValueError(f"Kayıt {kayit_id}: kanonik sıra {kanonik_perm} 'kabul' listesinde yer almalı.")

    if n_sayilari[3] < 25:
        raise ValueError(f"N=3 cümle sayısı yetersiz: {n_sayilari[3]} < 25")
    if n_sayilari[4] < 50:
        raise ValueError(f"N=4 cümle sayısı yetersiz: {n_sayilari[4]} < 50")
    if n_sayilari[5] < 30:
        raise ValueError(f"N=5 cümle sayısı yetersiz: {n_sayilari[5]} < 30")

    return cumleler


def _banka_yukle() -> list[dict[str, Any]]:
    """JSON dosyasını utf-8-sig ile okur ve doğrular."""
    yol = Path(__file__).resolve().parent / "veri" / "dizi_cumleler.json"
    if not yol.exists():
        raise FileNotFoundError(f"Cümle bankası dosyası bulunamadı: {yol}")

    with yol.open("r", encoding="utf-8-sig") as f:
        veri = json.load(f)

    return _sema_dogrula(veri)


class CumleIcerik:
    """Cümle Dizisi soru üretici ve doğrulayıcı mantığı."""

    # Banka tek seferlik doğrulanarak sınıf düzeyinde tutulur
    _BANKA_KAYITLARI: list[dict[str, Any]] | None = None

    def __init__(self, rng: np.random.Generator | None = None) -> None:
        if CumleIcerik._BANKA_KAYITLARI is None:
            CumleIcerik._BANKA_KAYITLARI = _banka_yukle()

        self._banka = CumleIcerik._BANKA_KAYITLARI
        self.rng = rng if rng is not None else np.random.default_rng()

        self.kartlar: list[str] = []
        self.kayit: dict[str, Any] = {}

        # Tur ve geçmiş hafızası
        self._gecmis_id: deque[str] = deque(maxlen=15)
        self._tur_gecmisi: set[str] = set()
        self._tur_idleri: set[str] = set()
        self._tur_konu_sayaci: dict[str, int] = {}

    def _yeni_tur_sifirla(self) -> None:
        """Soru no 0 olduğunda tur içi sayaçları sıfırlar; son 15 geçmiş korunur."""
        self._tur_gecmisi = set(self._gecmis_id)
        self._tur_idleri.clear()
        self._tur_konu_sayaci.clear()

    def uret(self, n: int, soru_no: int = 0) -> list[str]:
        """İstenen kelime sayısına (n) uygun rastgele cümle seçer ve kanonik kartları döner."""
        if n not in (3, 4, 5):
            raise ValueError(f"Desteklenmeyen oyuncu/kelime sayısı: {n}. Yalnız 3, 4 veya 5 olmalı.")

        if soru_no == 0:
            self._yeni_tur_sifirla()

        # Aday havuzu filtreleme:
        # 1. Kelime sayısı n olmalı
        # 2. Bu turda daha önce seçilmemiş olmalı
        # 3. Son 15 seçim (history) içinde yer almamalı
        # 4. Bu turdaki aynı konu sayısı 2'yi aşmamalı
        adaylar = [
            k
            for k in self._banka
            if len(k["kelimeler"]) == n
            and k["id"] not in self._tur_idleri
            and k["id"] not in self._tur_gecmisi
            and self._tur_konu_sayaci.get(k["konu"], 0) < 2
        ]

        if not adaylar:
            raise ValueError(
                f"N={n} için uygun cümle kalmadı! "
                f"(Tur içi id: {len(self._tur_idleri)}, Geçmiş: {len(self._gecmis_id)}, "
                f"Konular: {self._tur_konu_sayaci})"
            )

        secilen_idx = int(self.rng.integers(0, len(adaylar)))
        secilen = adaylar[secilen_idx]

        self.kayit = secilen
        self.kartlar = list(secilen["kelimeler"])

        # Kayıt sayaçlarını güncelle
        secilen_id = secilen["id"]
        secilen_konu = secilen["konu"]
        self._tur_idleri.add(secilen_id)
        self._gecmis_id.append(secilen_id)
        self._tur_konu_sayaci[secilen_konu] = self._tur_konu_sayaci.get(secilen_konu, 0) + 1

        return list(self.kartlar)

    def dogru_mu(self, kart_dizisi: list[str]) -> bool:
        """Verilen kart dizisinin kabul edilen sıralardan birine tam metinsel eşitliğini doğrular."""
        if not self.kayit:
            return False

        kelimeler: list[str] = self.kayit.get("kelimeler", [])
        kabul: list[list[int]] = self.kayit.get("kabul", [])

        if len(kart_dizisi) != len(kelimeler):
            return False

        # Her kabul permütasyonunu metin dizisine çevirip kontrol et.
        # Bu yaklaşım tekrarlanan kelime belirsizliklerini de metin bazında doğru kabul eder.
        for perm in kabul:
            hedef_metinler = [kelimeler[i] for i in perm]
            if kart_dizisi == hedef_metinler:
                return True

        return False


class Prototip(DiziMotor):
    """Cümle Dizisi prototip oyunu."""

    AD = AD
    ACIKLAMA = "Yer değiştirin, cümleyi doğru kurun!"
    IHTIYAC = IHTIYAC
    KAPI = KAPI
    POZ_YALNIZ = POZ_YALNIZ

    def __init__(self, ses: Any = None, rng: np.random.Generator | None = None) -> None:
        icerik = CumleIcerik(rng=rng)
        super().__init__(ses=ses, icerik=icerik, rng=rng)
