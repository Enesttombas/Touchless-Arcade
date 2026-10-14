"""İnsan Dizisi ortak oyun motoru (İşlem Dizisi ve Cümle Dizisi).

Kamera karşısındaki 3-5 oyuncunun yer değiştirerek üzerlerindeki kartları
doğru sıraya dizmesini denetleyen ortak motor altyapısı.
"""
from __future__ import annotations

import copy
import itertools
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    KIRMIZI,
    PEMBE,
    SARI,
    YESIL,
    Algi,
    G,
    Y,
    halka,
    panel,
    yazi_koy,
    yazi_sprite,
)
from filtre import OneEuro as BirEuro
from kimlik_imza import (
    LANDMARK_BURUN,
    LANDMARK_SAG_KALCA,
    LANDMARK_SAG_OMUZ,
    LANDMARK_SOL_KALCA,
    LANDMARK_SOL_OMUZ,
    Imza,
    cikar,
    uzaklik,
)
from oyun_akis import OyunAkisi
from oyuncu import OyuncuKapisi

# Renk paleti
RENKLER = [
    CAMGOBEGI,               # Oyuncu 1
    (255, 130, 40),          # Turuncu / Sıcak
    PEMBE,                   # Pembe
    YESIL,                   # Yeşil
    (240, 70, 70),           # Parlak Kırmızı/Mercan
    SARI,                    # Sarı
]

SKELETON_BAGLANTILAR = [
    (11, 12), (11, 13), (13, 15),
    (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27),
    (24, 26), (26, 28)
]

TAKIM_ISIMLERI = [
    "Neon Kartallar", "Mor Şimşekler", "Kutup Ayıları", "Sonsuz Döngü",
    "Altın Oran", "Kuantum Gücü", "Siber Yıldızlar", "Hızlı Nöronlar",
    "Gök Gürültüsü", "Fırtına Koşucuları", "Derin Kodlar", "Piksel Kaplanları",
    "Kozmik Rüzgar", "Ateşböcekleri", "Güneş Patlaması", "Zaman Yolcuları",
    "Yüksek Frekans", "Algoritma Devleri", "Mavi Dalga", "Matrix Şampiyonları"
]


@dataclass
class DiziOyuncu:
    kimlik: int
    poz_id: int
    kart: str
    x: float
    renk: Tuple[int, int, int]
    durum: str = "normal"  # normal | donmus | belirsiz
    omuz: float = 0.08
    poz: Any = None
    y_bas: float = 0.2
    hiz_x: float = 0.0
    son_gorulme: float = 0.0
    orijinal_imza: Optional[Any] = None

    @property
    def kart_str(self) -> str:
        return str(self.kart)

    @kart_str.setter
    def kart_str(self, val: str) -> None:
        self.kart = str(val)


@dataclass
class KarismaKaydi:
    kimlikler: List[int]
    giris_x: Dict[int, float]
    giris_hiz: Dict[int, float]
    giris_imza: Dict[int, Any]
    baslangic_t: float
    son_cakisma_t: float
    ayrik_baslangic: Optional[float] = None


class DiziMotor(OyunAkisi):
    """İnsan Dizisi genel mekaniği."""

    AD = "Dizi Motoru"
    IHTIYAC: Set[str] = {"poz"}
    KAPI = {"poz_omuz_min": 0.035}
    POZ_YALNIZ = True
    SORU_SAYISI = 5

    # Süre sabitleri
    SURE_LOBI_STABIL = 1.5
    SURE_LOBI_EL = 0.8
    SURE_DAGITIM = 0.8
    SURE_DAGITIM_ADIM = 0.1
    SURE_SAYIM = 3.0
    SURE_SAYIM_TOLERANS = 0.3
    SURE_KAYIP_BEKLE = 0.5
    SURE_KUTLAMA = 1.0
    SURE_BELIRSIZ_TAKAS_EL = 0.8
    SURE_BELIRSIZ_YENIDEN = 2.5
    SURE_BELIRSIZ_ASIMI = 6.0
    SURE_EKSILME_DURAKLA = 2.0
    SURE_EKSILME_BITIR = 8.0
    SURE_SONUC_RESET = 6.0
    SURE_IPUCU_1 = 20.0
    SURE_IPUCU_SON = 35.0
    SURE_PAS_IZIN = 50.0

    def __init__(self, ses: Any, icerik: Any, rng: Optional[np.random.Generator] = None):
        super().__init__(ses)
        self.icerik = icerik
        self.rng = rng or np.random.default_rng()

        self.kapi = OyuncuKapisi(self.KAPI)
        self.imzalar = Imza()
        self.olaylar: List[Tuple[Any, ...]] = []
        self.oyuncular: Dict[int, DiziOyuncu] = {}
        self.sayac_kimlik = 0

        self.N: int = 4
        self._operator_n: Optional[int] = None
        self._lobi_idler: Tuple[int, ...] = ()
        self.faz: str = "lobi"  # lobi, dagit, oyna, kutla, durakla, sonuc
        self.durum: str = "lobi"
        self.soru_no: int = 0
        self.skor: int = 0
        self.toplam_sure: float = 0.0
        self.simdi: float = 0.0
        self.son_algi: Optional[Algi] = None

        # Kart filtreleri (OneEuro: min_cutoff, beta, d_cutoff)
        self.kart_x_filtre: Dict[int, BirEuro] = {}
        self.kart_y_filtre: Dict[int, BirEuro] = {}

        # Lobi sayaçları
        self._lobi_stabil_sayi: int = 0
        self._lobi_stabil_t: float = 0.0
        self._lobi_el_t: Dict[int, float] = {}

        # Soru/tur akışı
        self.soru_baslangic_t: float = 0.0
        self.kanonik_cevap: List[str] = []
        self.mevcut_soru_kartlar: List[str] = []
        self.dagitim_baslangic_t: float = 0.0
        self.sayim_baslangic_t: Optional[float] = None
        self.sayim_gecen: float = 0.0
        self.bozulma_t: Optional[float] = None
        self.son_tik_sn: int = -1
        self.kutlama_t: float = 0.0
        self.eksik_baslangic_t: Optional[float] = None
        self.durakla_t: Optional[float] = None
        self.sonuc_baslangic_t: float = 0.0
        self.takim_adi: str = ""
        self.gecmis_skorlar: List[Tuple[str, int]] = []
        self.en_iyiler: List[Tuple[str, int]] = []

        # Karışma / Belirsizlik
        self.aktif_karismalar: List[KarismaKaydi] = []
        self.belirsiz_baslangic: Dict[Tuple[int, int], float] = {}
        self.belirsiz_el_t: Dict[int, float] = {}
        self.pas_el_t: Dict[int, float] = {}

        # Sıralama histerezisi
        self._onceki_sira: List[int] = []

        # Ses zamanlayıcıları
        self._son_imza_t: Dict[int, float] = {}
        self._geri_donus_imza: Dict[int, Tuple[float, Any]] = {}
        self.mesaj_uyari: str = ""
        self.mesaj_uyari_bitis: float = 0.0

        # Kayıt ve tekrar oynatma
        self.imzasiz: bool = False
        self.imza_override: Optional[Dict[int, Any]] = None
        self.kayit_araci: Optional[Any] = None

    # ---------------------------------------------------------
    # Temel Yaşam Döngüsü
    # ---------------------------------------------------------
    def baslat(self, algi: Optional[Algi] = None, simdi: float = 0.0) -> None:
        self.simdi = simdi
        self.son_algi = algi
        self.olaylar.clear()
        self.kart_x_filtre.clear()
        self.kart_y_filtre.clear()
        self._lobi_stabil_sayi = 0
        self._lobi_idler = ()
        self._lobi_stabil_t = simdi
        self._lobi_el_t.clear()
        self.aktif_karismalar.clear()
        self.belirsiz_baslangic.clear()
        self.belirsiz_el_t.clear()
        self.pas_el_t.clear()
        self.eksik_baslangic_t = None
        self.durakla_t = None
        self.sayim_baslangic_t = None
        self.sayim_gecen = 0.0
        self.bozulma_t = None
        self.son_tik_sn = -1

        if algi is not None:
            poz_list = self._suzulmus_pozlar(algi)
            gecerli_pozlar = [p for p in poz_list if not p[2]]
            k = len(gecerli_pozlar)
            if k in (3, 4, 5):
                self.N = k
                self._tur_baslat(gecerli_pozlar, simdi)
                return

        # Aksi takdirde lobiye dön
        self.faz = "lobi"
        self.durum = "lobi"
        self.soru_no = 0
        self.skor = 0
        self.toplam_sure = 0.0
        self.oyuncular.clear()
        self._onceki_sira.clear()
        self.imzalar.sifirla()

    def tus(self, k: Any) -> None:
        if isinstance(k, str):
            karakter = k
            kod = ord(k) if len(k) == 1 else -1
        elif isinstance(k, int):
            kod = k
            try:
                karakter = chr(k)
            except (ValueError, OverflowError):
                karakter = ""
        else:
            return

        if karakter in ("3", "4", "5") or kod in (ord("3"), ord("4"), ord("5")):
            val = int(karakter if karakter in ("3", "4", "5") else chr(kod))
            self.N = val
            self._operator_n = val
            self._lobi_stabil_sayi = self.N
            self._lobi_stabil_t = self.simdi - self.SURE_LOBI_STABIL - 0.1
        elif kod == 32 or karakter == " ":
            if self.faz == "lobi":
                self._operator_baslat()
        elif karakter in ("k", "K") or kod in (ord("k"), ord("K")):
            self._kayit_degistir()
        elif karakter in ("d", "D") or kod in (ord("d"), ord("D")):
            if self.kayit_araci is not None and hasattr(self.kayit_araci, "etiketle"):
                self.kayit_araci.etiketle("D", self.simdi)
        elif karakter in ("y", "Y") or kod in (ord("y"), ord("Y")):
            if self.kayit_araci is not None and hasattr(self.kayit_araci, "etiketle"):
                self.kayit_araci.etiketle("Y", self.simdi)

    def _kayit_degistir(self) -> None:
        from dizi_olcum import DiziKayit
        if self.kayit_araci is None:
            self.kayit_araci = DiziKayit()
            self.kayit_araci.baslat(self.__class__.__module__)
            self._uyari_ver("Sayısal kayıt açık: " + str(self.kayit_araci.yol), 5)
        else:
            yol = self.kayit_araci.durdur()
            self.kayit_araci = None
            self._uyari_ver("Kayıt tamamlandı: " + yol, 5)

    def _uyari_ver(self, metin: str, sure: float = 1.0) -> None:
        self.mesaj_uyari = metin
        self.mesaj_uyari_bitis = self.simdi + sure

    # ---------------------------------------------------------
    # Geometri, Poz ve Algı Yardımcıları
    # ---------------------------------------------------------
    @staticmethod
    def _poz_gecerli_mi(lm: Any) -> bool:
        if lm is None or len(lm) < 25:
            return False
        try:
            o1, o2 = lm[LANDMARK_SOL_OMUZ], lm[LANDMARK_SAG_OMUZ]
            omuz_w = math.hypot(float(o1.x) - float(o2.x), float(o1.y) - float(o2.y))
            if not math.isfinite(omuz_w) or omuz_w < 0.035:
                return False
            x_m = (float(o1.x) + float(o2.x)) * 0.5
            if not (0.04 <= x_m <= 0.96):
                return False
            return True
        except (AttributeError, ValueError, TypeError):
            return False

    @staticmethod
    def _poz_x(lm: Any) -> Optional[float]:
        try:
            k1, k2 = lm[LANDMARK_SOL_KALCA], lm[LANDMARK_SAG_KALCA]
            v_k1 = float(getattr(k1, "visibility", 1.0))
            v_k2 = float(getattr(k2, "visibility", 1.0))
            if min(v_k1, v_k2) >= 0.5:
                return (float(k1.x) + float(k2.x)) * 0.5

            o1, o2 = lm[LANDMARK_SOL_OMUZ], lm[LANDMARK_SAG_OMUZ]
            v_o1 = float(getattr(o1, "visibility", 1.0))
            v_o2 = float(getattr(o2, "visibility", 1.0))
            if min(v_o1, v_o2) >= 0.5:
                return (float(o1.x) + float(o2.x)) * 0.5
            return None
        except Exception:
            return None

    @staticmethod
    def _poz_omuz(lm: Any) -> float:
        try:
            o1, o2 = lm[LANDMARK_SOL_OMUZ], lm[LANDMARK_SAG_OMUZ]
            return float(math.hypot(float(o1.x) - float(o2.x), float(o1.y) - float(o2.y)))
        except Exception:
            return 0.08

    @staticmethod
    def _el_burun_ustunde_mi(lm: Any) -> bool:
        try:
            b_y = float(lm[LANDMARK_BURUN].y)
            w1_y = float(lm[15].y)
            w2_y = float(lm[16].y)
            w1_v = float(getattr(lm[15], "visibility", 1.0))
            w2_v = float(getattr(lm[16], "visibility", 1.0))
            return (w1_v > 0.3 and w1_y < b_y) or (w2_v > 0.3 and w2_y < b_y)
        except Exception:
            return False

    @staticmethod
    def _torso_kutu(lm: Any, pay: float = 0.3) -> Tuple[float, float, float, float]:
        o1, o2 = lm[LANDMARK_SOL_OMUZ], lm[LANDMARK_SAG_OMUZ]
        k1, k2 = lm[LANDMARK_SOL_KALCA], lm[LANDMARK_SAG_KALCA]
        xs = [float(p.x) for p in (o1, o2, k1, k2)]
        ys = [float(p.y) for p in (o1, o2, k1, k2)]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w = max(0.01, max_x - min_x)
        h = max(0.01, max_y - min_y)
        return min_x - w * pay, min_y - h * pay, max_x + w * pay, max_y + h * pay

    @staticmethod
    def _kutu_kesisiyor_mu(b1: Tuple[float, float, float, float], b2: Tuple[float, float, float, float]) -> bool:
        return not (b1[2] < b2[0] or b1[0] > b2[2] or b1[3] < b2[1] or b1[1] > b2[3])

    # ---------------------------------------------------------
    # Poz Süzme ve İmza Güncelleme
    # ---------------------------------------------------------
    def _suzulmus_pozlar(self, algi: Optional[Algi]) -> List[Tuple[int, Any, bool]]:
        """(poz_id, lm, tahmini_mi) üçlüleri."""
        if algi is None:
            return []
        tahmini_idler: Set[int] = set()
        tahmini_raw = getattr(algi, "tahmini", [])
        if isinstance(tahmini_raw, (set, list, tuple)):
            for item in tahmini_raw:
                if isinstance(item, (int, np.integer)):
                    tahmini_idler.add(int(item))
                elif isinstance(item, (tuple, list)) and len(item) == 2:
                    if item[0] == "poz":
                        tahmini_idler.add(int(item[1]))
                elif isinstance(item, tuple) and len(item) == 1:
                    tahmini_idler.add(int(item[0]))

        sonuclar = []
        for pid, lm in zip(getattr(algi, "poz_id", []), getattr(algi, "pozlar", [])):
            if self._poz_gecerli_mi(lm):
                sonuclar.append((int(pid), lm, int(pid) in tahmini_idler))
        return sonuclar

    def _imza_guncelle(self, kare: np.ndarray, poz_list: List[Tuple[int, Any, bool]]) -> None:
        if self.imzasiz or ((kare is None or kare.size == 0) and not self.imza_override):
            return

        yalniz_haritasi: Dict[int, bool] = {}
        kutular = {}
        for pid, lm, tahmini in poz_list:
            if tahmini:
                yalniz_haritasi[pid] = False
            else:
                kutular[pid] = self._torso_kutu(lm, pay=0.3)

        for pid1, b1 in kutular.items():
            yalniz = True
            for pid2, b2 in kutular.items():
                if pid1 != pid2 and self._kutu_kesisiyor_mu(b1, b2):
                    yalniz = False
                    break
            yalniz_haritasi[pid1] = yalniz

        for pid, lm, tahmini in poz_list:
            if tahmini:
                continue
            oyuncu = next((o for o in self.oyuncular.values() if o.poz_id == pid), None)
            if oyuncu is None:
                continue

            son_t = self._son_imza_t.get(oyuncu.kimlik, 0.0)
            if self.simdi - son_t >= 0.1 - 1e-9:
                vec = None
                if self.imza_override is not None:
                    vec = self.imza_override.get(pid) or self.imza_override.get(oyuncu.kimlik)
                elif kare is not None and kare.size > 0:
                    vec = cikar(kare, lm)

                if vec is not None:
                    self.imzalar.guncelle(oyuncu.kimlik, vec, self.simdi, yalniz=yalniz_haritasi.get(pid, False))
                    self._son_imza_t[oyuncu.kimlik] = self.simdi
                    if oyuncu.orijinal_imza is None and self.imzalar.olgun(oyuncu.kimlik):
                        oyuncu.orijinal_imza = copy.deepcopy(self.imzalar.al(oyuncu.kimlik))

    # ---------------------------------------------------------
    # Karışma ve Çözüm Yönetimi
    # ---------------------------------------------------------
    def _karisma_gruplari_tespit_et(self, poz_list: List[Tuple[int, Any, bool]]) -> List[Set[int]]:
        pidler = [p[0] for p in poz_list]
        komsu: Dict[int, Set[int]] = {pid: set() for pid in pidler}
        lm_sozluk = {p[0]: p[1] for p in poz_list}
        tahmin_sozluk = {p[0]: p[2] for p in poz_list}

        for i in range(len(pidler)):
            for j in range(i + 1, len(pidler)):
                id1, id2 = pidler[i], pidler[j]
                lm1, lm2 = lm_sozluk[id1], lm_sozluk[id2]
                b1 = self._torso_kutu(lm1, pay=0.3)
                b2 = self._torso_kutu(lm2, pay=0.3)
                kesisiyor = self._kutu_kesisiyor_mu(b1, b2)

                x1 = self._poz_x(lm1) or 0.5
                x2 = self._poz_x(lm2) or 0.5
                omuz_ort = 0.5 * (self._poz_omuz(lm1) + self._poz_omuz(lm2))
                yakin = abs(x1 - x2) < 1.5 * max(0.035, omuz_ort)
                tahmini_var = tahmin_sozluk[id1] or tahmin_sozluk[id2]

                if kesisiyor or (tahmini_var and yakin):
                    komsu[id1].add(id2)
                    komsu[id2].add(id1)

        bilesenler: List[Set[int]] = []
        ziyaret = set()
        for pid in pidler:
            if pid not in ziyaret:
                yigin = [pid]
                grup = set()
                while yigin:
                    cur = yigin.pop()
                    if cur not in grup:
                        grup.add(cur)
                        ziyaret.add(cur)
                        for k in komsu[cur]:
                            if k not in grup:
                                yigin.append(k)
                if len(grup) >= 2:
                    bilesenler.append(grup)
        return bilesenler

    def _karisma_ve_cozum_yonetimi(self, poz_list: List[Tuple[int, Any, bool]], kare: np.ndarray) -> None:
        if not self.oyuncular:
            return

        poz_haritasi = {p[0]: p for p in poz_list}
        anlik_gruplar = self._karisma_gruplari_tespit_et(poz_list)

        for grup_pids in anlik_gruplar:
            grup_oyuncu_ids = [
                o.kimlik for o in self.oyuncular.values()
                if o.poz_id in grup_pids
            ]
            if len(grup_oyuncu_ids) < 2:
                continue

            mevcut = None
            for k in self.aktif_karismalar:
                if set(k.kimlikler) == set(grup_oyuncu_ids):
                    mevcut = k
                    break

            if mevcut is None:
                giris_x = {oid: self.oyuncular[oid].x for oid in grup_oyuncu_ids}
                giris_hiz = {oid: self.oyuncular[oid].hiz_x for oid in grup_oyuncu_ids}
                giris_imza = {oid: copy.deepcopy(self.imzalar.al(oid)) for oid in grup_oyuncu_ids}
                kayit = KarismaKaydi(
                    kimlikler=grup_oyuncu_ids,
                    giris_x=giris_x,
                    giris_hiz=giris_hiz,
                    giris_imza=giris_imza,
                    baslangic_t=self.simdi,
                    son_cakisma_t=self.simdi,
                )
                self.aktif_karismalar.append(kayit)
                self.olaylar.append(("karisma", self.simdi, grup_oyuncu_ids))
                for oid in grup_oyuncu_ids:
                    self.oyuncular[oid].durum = "donmus"
            else:
                mevcut.son_cakisma_t = self.simdi
                mevcut.ayrik_baslangic = None

        tamamlananlar = []
        for kayit in self.aktif_karismalar:
            grup_pids = {self.oyuncular[oid].poz_id for oid in kayit.kimlikler if oid in self.oyuncular}
            hala_cakisiyor = any(len(grup_pids.intersection(g)) >= 2 for g in anlik_gruplar)

            if not hala_cakisiyor:
                if kayit.ayrik_baslangic is None:
                    kayit.ayrik_baslangic = self.simdi
                gecen_ayrik = max(self.simdi - kayit.ayrik_baslangic, self.simdi - kayit.son_cakisma_t)
                if gecen_ayrik >= 0.25:
                    self._karismayi_coz(kayit, poz_haritasi, kare)
                    tamamlananlar.append(kayit)
            else:
                kayit.son_cakisma_t = self.simdi
                kayit.ayrik_baslangic = None

        for t in tamamlananlar:
            self.aktif_karismalar.remove(t)

    def _karismayi_coz(self, kayit: KarismaKaydi, poz_haritasi: Dict[int, Any], kare: np.ndarray) -> None:
        k = len(kayit.kimlikler)
        if k < 2 or k > 5:
            for oid in kayit.kimlikler:
                if oid in self.oyuncular:
                    self.oyuncular[oid].durum = "normal"
            return

        eski_kimlikler = list(kayit.kimlikler)
        simdiki_poz_kayitlari = [poz_haritasi.get(self.oyuncular[oid].poz_id) for oid in eski_kimlikler]

        if any(p is None for p in simdiki_poz_kayitlari):
            kalan_pozlar = list(poz_haritasi.values())
            if len(kalan_pozlar) >= k:
                simdiki_poz_kayitlari = kalan_pozlar[:k]
            else:
                for oid in eski_kimlikler:
                    if oid in self.oyuncular:
                        self.oyuncular[oid].durum = "normal"
                return

        simdiki_pozlar = [p[1] for p in simdiki_poz_kayitlari]
        simdiki_pids = [p[0] for p in simdiki_poz_kayitlari]

        maliyet_matrisi = np.zeros((k, k), dtype=np.float32)
        tum_olgun = True

        for i, oid in enumerate(eski_kimlikler):
            if not self.imzalar.olgun(oid):
                tum_olgun = False
            imza_i = kayit.giris_imza.get(oid) or self.imzalar.al(oid)
            giris_x = kayit.giris_x.get(oid, 0.5)
            giris_v = kayit.giris_hiz.get(oid, 0.0)
            dt = max(0.01, self.simdi - kayit.baslangic_t)
            ongorulen_x = giris_x + giris_v * dt

            for j, lm in enumerate(simdiki_pozlar):
                anlik_imza = None
                pid_j = simdiki_pids[j]
                if self.imza_override is not None:
                    anlik_imza = self.imza_override.get(pid_j) or self.imza_override.get(oid)
                elif kare is not None and kare.size > 0 and not self.imzasiz:
                    anlik_imza = cikar(kare, lm)

                d_imza = uzaklik(imza_i, anlik_imza) if (imza_i and anlik_imza and not self.imzasiz) else 0.5
                anlik_x = self._poz_x(lm) or 0.5
                omuz = self._poz_omuz(lm)
                d_hareket = min(1.0, abs(anlik_x - ongorulen_x) / max(0.05, omuz))

                if self.imzasiz:
                    maliyet = d_hareket
                else:
                    maliyet = 0.7 * d_imza + 0.3 * d_hareket
                maliyet_matrisi[i, j] = maliyet

        permutasyonlar = list(itertools.permutations(range(k)))
        skorlar = []
        for p in permutasyonlar:
            toplam_m = sum(maliyet_matrisi[i, p[i]] for i in range(k))
            skorlar.append((toplam_m, p))

        skorlar.sort(key=lambda s: s[0])
        en_iyi_skor, en_iyi_p = skorlar[0]
        ikinci_skor = skorlar[1][0] if len(skorlar) > 1 else en_iyi_skor + 1.0
        pay = float(ikinci_skor - en_iyi_skor)

        atama_sonuc = {}
        for i, oid in enumerate(eski_kimlikler):
            hedef_pid = simdiki_pids[en_iyi_p[i]]
            atama_sonuc[oid] = hedef_pid
            self.oyuncular[oid].poz_id = hedef_pid

        guvenli = (pay >= 0.15) and (tum_olgun or self.imzasiz)
        self.olaylar.append(("cozum", self.simdi, atama_sonuc, pay))

        if guvenli:
            for oid in eski_kimlikler:
                self.oyuncular[oid].durum = "normal"
        else:
            self.olaylar.append(("belirsiz", self.simdi, list(eski_kimlikler)))
            for oid in eski_kimlikler:
                self.oyuncular[oid].durum = "belirsiz"
            if len(eski_kimlikler) == 2:
                pair = (min(eski_kimlikler), max(eski_kimlikler))
                self.belirsiz_baslangic[pair] = self.simdi

    # ---------------------------------------------------------
    # Oyuncu Güncelleme ve Kadro
    # ---------------------------------------------------------
    def _oyuncu_durumlarini_guncelle(self, poz_list: List[Tuple[int, Any, bool]], kare: Optional[np.ndarray] = None) -> None:
        poz_haritasi = {p[0]: p for p in poz_list}
        kullanilan = {o.poz_id for o in self.oyuncular.values()}
        adaylar = [p for p in poz_list if p[0] not in kullanilan and not p[2]]
        for o in self.oyuncular.values():
            if o.poz_id in poz_haritasi or not self.imzalar.olgun(o.kimlik):
                continue
            referans = o.orijinal_imza or self.imzalar.al(o.kimlik)
            maliyetler = []
            for pid, lm, _ in adaylar:
                if self.imzasiz:
                    continue
                if self.imza_override is not None:
                    vec = self.imza_override.get(pid)
                else:
                    t0, vec = self._geri_donus_imza.get(pid, (-math.inf, None))
                    if self.simdi - t0 >= 0.1 - 1e-9:
                        vec = cikar(kare, lm)
                        self._geri_donus_imza[pid] = (self.simdi, vec)
                if vec is not None:
                    maliyetler.append((uzaklik(referans, vec), pid, lm))
            maliyetler.sort(key=lambda v: v[0])
            if maliyetler and maliyetler[0][0] <= 0.25 and (len(maliyetler) == 1 or maliyetler[1][0] - maliyetler[0][0] >= 0.15):
                onceki_pid = o.poz_id
                o.poz_id = maliyetler[0][1]
                adaylar = [p for p in adaylar if p[0] != o.poz_id]
                self.olaylar.append(("geri_donus", self.simdi, o.kimlik, onceki_pid, o.poz_id))

        for oid, o in list(self.oyuncular.items()):
            if o.poz_id in poz_haritasi:
                _, lm, tahmini = poz_haritasi[o.poz_id]
                if tahmini:
                    continue
                yeni_x = self._poz_x(lm)
                if yeni_x is not None:
                    dt = max(1e-3, self.simdi - o.son_gorulme)
                    o.hiz_x = 0.5 * o.hiz_x + 0.5 * (yeni_x - o.x) / dt
                    o.x = yeni_x
                o.omuz = self._poz_omuz(lm)
                o.poz = lm
                o.son_gorulme = self.simdi
                try:
                    o.y_bas = float(lm[LANDMARK_BURUN].y)
                except Exception:
                    o.y_bas = 0.2
            else:
                if self.simdi - o.son_gorulme > self.SURE_KAYIP_BEKLE:
                    o.hiz_x = 0.0

    def _belirsizlik_ve_el_takas_yonetimi(self) -> None:
        belirsiz_ciftler = list(self.belirsiz_baslangic.items())

        for pair, t_bas in belirsiz_ciftler:
            id1, id2 = pair
            o1 = self.oyuncular.get(id1)
            o2 = self.oyuncular.get(id2)
            if not o1 or not o2:
                self.belirsiz_baslangic.pop(pair, None)
                continue

            gecen = self.simdi - t_bas
            el1 = self._el_burun_ustunde_mi(o1.poz) if o1.poz else False
            el2 = self._el_burun_ustunde_mi(o2.poz) if o2.poz else False

            if el1 or el2:
                aktif_id = id1 if el1 else id2
                t0 = self.belirsiz_el_t.setdefault(aktif_id, self.simdi)
                if self.simdi - t0 >= self.SURE_BELIRSIZ_TAKAS_EL:
                    o1.kart, o2.kart = o2.kart, o1.kart
                    o1.durum = "normal"
                    o2.durum = "normal"
                    self.olaylar.append(("el_takas", self.simdi, id1, id2))
                    self.ses.cal("ding", 0.8)
                    self._uyari_ver("Kartlar Değişti!", 1.0)
                    self.belirsiz_baslangic.pop(pair, None)
                    self.belirsiz_el_t.clear()
                    continue
            else:
                self.belirsiz_el_t.pop(id1, None)
                self.belirsiz_el_t.pop(id2, None)

            ayrik = abs(o1.x - o2.x) >= 1.5 * max(o1.omuz, o2.omuz)
            if gecen >= self.SURE_BELIRSIZ_YENIDEN and ayrik:
                imza1 = self.imzalar.al(id1)
                imza2 = self.imzalar.al(id2)
                if imza1 and imza2 and o1.orijinal_imza and o2.orijinal_imza:
                    d_duz = uzaklik(o1.orijinal_imza, imza1) + uzaklik(o2.orijinal_imza, imza2)
                    d_ters = uzaklik(o1.orijinal_imza, imza2) + uzaklik(o2.orijinal_imza, imza1)
                    if abs(d_duz - d_ters) >= 0.15:
                        if d_ters < d_duz:
                            o1.kart, o2.kart = o2.kart, o1.kart
                            self.olaylar.append(("el_takas", self.simdi, id1, id2))
                        o1.durum = "normal"
                        o2.durum = "normal"
                        self.belirsiz_baslangic.pop(pair, None)
                        continue

            if gecen >= self.SURE_BELIRSIZ_ASIMI:
                o1.durum = "normal"
                o2.durum = "normal"
                self.belirsiz_baslangic.pop(pair, None)

    # ---------------------------------------------------------
    # Sıra Kontrolü ve Histerezis
    # ---------------------------------------------------------
    def _mevcut_dizilim(self) -> List[DiziOyuncu]:
        if not self.oyuncular:
            return []

        mevcut_idler = [kid for kid in self._onceki_sira if kid in self.oyuncular]
        for kid in self.oyuncular:
            if kid not in mevcut_idler:
                mevcut_idler.append(kid)

        if len(mevcut_idler) != len(self._onceki_sira):
            mevcut_idler.sort(key=lambda kid: self.oyuncular[kid].x)

        degisti = True
        while degisti:
            degisti = False
            for i in range(len(mevcut_idler) - 1):
                id_a, id_b = mevcut_idler[i], mevcut_idler[i + 1]
                oa, ob = self.oyuncular[id_a], self.oyuncular[id_b]
                if oa.x > ob.x:
                    esik = 0.25 * 0.5 * (oa.omuz + ob.omuz)
                    if (oa.x - ob.x) >= esik:
                        mevcut_idler[i], mevcut_idler[i + 1] = id_b, id_a
                        degisti = True

        self._onceki_sira = mevcut_idler
        return [self.oyuncular[kid] for kid in mevcut_idler]

    def _mevcut_kartlar_sirasi(self) -> List[str]:
        return [o.kart for o in self._mevcut_dizilim()]

    # ---------------------------------------------------------
    # Lobi Mantığı
    # ---------------------------------------------------------
    def _lobi_guncelle(self, poz_list: List[Tuple[int, Any, bool]]) -> None:
        gecerli_pozlar = [p for p in poz_list if not p[2]]
        sayi = len(gecerli_pozlar)
        idler = tuple(sorted(p[0] for p in gecerli_pozlar))
        if idler != self._lobi_idler:
            self._lobi_idler = idler
            self._lobi_stabil_t = self.simdi
            self._lobi_el_t.clear()

        if sayi in (3, 4, 5):
            if sayi == self._lobi_stabil_sayi:
                if self.simdi - self._lobi_stabil_t >= self.SURE_LOBI_STABIL:
                    tum_eller = True
                    for pid, lm, _ in gecerli_pozlar:
                        if self._el_burun_ustunde_mi(lm):
                            t0 = self._lobi_el_t.setdefault(pid, self.simdi)
                            if self.simdi - t0 < self.SURE_LOBI_EL:
                                tum_eller = False
                        else:
                            self._lobi_el_t.pop(pid, None)
                            tum_eller = False

                    if tum_eller and len(self._lobi_el_t) == sayi:
                        self.N = sayi
                        self._tur_baslat(gecerli_pozlar, self.simdi)
            else:
                self._lobi_stabil_sayi = sayi
                self._lobi_stabil_t = self.simdi
                self._lobi_el_t.clear()
        else:
            self._lobi_stabil_sayi = sayi
            self._lobi_stabil_t = self.simdi
            self._lobi_el_t.clear()

    def _operator_baslat(self) -> None:
        gecerli_pozlar = [p for p in self._suzulmus_pozlar(self.son_algi) if not p[2]]
        k = len(gecerli_pozlar)
        if self._operator_n is not None and k >= self._operator_n:
            self.N = self._operator_n
            sirali = sorted(gecerli_pozlar, key=lambda p: self._poz_x(p[1]) or 0.5)
            self._tur_baslat(sirali[:self.N], self.simdi)
        elif self._operator_n is None and k in (3, 4, 5):
            self.N = k
            self._tur_baslat(gecerli_pozlar, self.simdi)

    def _tur_baslat(self, poz_list: List[Tuple[int, Any, bool]], simdi: float) -> None:
        self.durum = "oyun"
        self.oyuncular.clear()
        self.imzalar.sifirla()
        self._son_imza_t.clear()
        self._geri_donus_imza.clear()
        self.aktif_karismalar.clear()
        self.belirsiz_baslangic.clear()
        self.belirsiz_el_t.clear()
        self.kart_x_filtre.clear()
        self.kart_y_filtre.clear()
        self.eksik_baslangic_t = None
        self.durakla_t = None
        self.sayac_kimlik = 0

        sirali_pozlar = sorted(poz_list[:self.N], key=lambda p: self._poz_x(p[1]) or 0.5)
        for i, (pid, lm, _) in enumerate(sirali_pozlar):
            kid = i + 1
            x_val = self._poz_x(lm) or (0.2 + 0.6 * i / max(1, self.N - 1))
            self.oyuncular[kid] = DiziOyuncu(
                kimlik=kid,
                poz_id=pid,
                kart="",
                x=x_val,
                renk=RENKLER[i % len(RENKLER)],
                durum="normal",
                omuz=self._poz_omuz(lm),
                poz=lm,
                son_gorulme=simdi,
            )

        self._onceki_sira = list(self.oyuncular.keys())
        self.soru_no = 0
        self.skor = 0
        self.toplam_sure = 0.0
        self._yeni_soru_hazirla()

    # ---------------------------------------------------------
    # Soru Hazırlama ve Dağıtım
    # ---------------------------------------------------------
    def _yeni_soru_hazirla(self) -> None:
        if self.soru_no >= self.SORU_SAYISI:
            self._tur_sonuclandir()
            return

        kanonik = list(self.icerik.uret(self.N, soru_no=self.soru_no))
        self.kanonik_cevap = list(kanonik)

        esik_degisim = math.ceil(self.N / 2)
        kartlar = list(kanonik)

        deneme = 0
        while deneme < 300:
            self.rng.shuffle(kartlar)
            degisen = sum(1 for a, b in zip(kanonik, kartlar) if a != b)
            if not self.icerik.dogru_mu(kartlar) and degisen >= esik_degisim:
                break
            deneme += 1

        self.mevcut_soru_kartlar = kartlar
        self.faz = "dagit"
        self.dagitim_baslangic_t = self.simdi
        self.ses.cal("woosh", 0.6)

        sirali_oyuncular = sorted(self.oyuncular.values(), key=lambda o: o.x)
        for o, k in zip(sirali_oyuncular, self.mevcut_soru_kartlar):
            o.kart = k
            o.durum = "normal"

        self.sayim_baslangic_t = None
        self.sayim_gecen = 0.0
        self.bozulma_t = None
        self.son_tik_sn = -1
        self.pas_el_t.clear()

    # ---------------------------------------------------------
    # Oyun Döngüsü
    # ---------------------------------------------------------
    def _oyun_dongusu_guncelle(self) -> None:
        if self.faz == "dagit":
            toplam_dagit = self.SURE_DAGITIM + self.N * self.SURE_DAGITIM_ADIM
            if self.simdi - self.dagitim_baslangic_t >= toplam_dagit:
                self.faz = "oyna"
                self.soru_baslangic_t = self.simdi

        if self.faz == "kutla":
            if self.simdi - self.kutlama_t >= self.SURE_KUTLAMA:
                if self.soru_no >= self.SORU_SAYISI:
                    self._tur_sonuclandir()
                else:
                    self._yeni_soru_hazirla()
            return

        # Eksik oyuncu takibi
        mevcut_pids = set()
        if self.son_algi is not None:
            mevcut_pids = {int(p) for p in getattr(self.son_algi, "poz_id", [])}
        tahmini_pids = {p[0] for p in self._suzulmus_pozlar(self.son_algi) if p[2]}

        eksik_var = any(
            o.poz_id not in mevcut_pids or o.poz_id in tahmini_pids or (self.simdi - o.son_gorulme > self.SURE_KAYIP_BEKLE)
            for o in self.oyuncular.values()
        )

        if eksik_var:
            if self.eksik_baslangic_t is None:
                self.eksik_baslangic_t = self.simdi

            gecen_eksik = self.simdi - self.eksik_baslangic_t
            if gecen_eksik >= self.SURE_EKSILME_BITIR:
                self._tur_sonuclandir()
                return
            elif gecen_eksik >= self.SURE_EKSILME_DURAKLA:
                if self.faz != "durakla":
                    self.faz = "durakla"
                    self.durakla_t = self.simdi
                    self._uyari_ver(f"Biri eksik, {self.N} kişi lazım!", 3.0)
                if self.durakla_t and (self.simdi - self.durakla_t >= (self.SURE_EKSILME_BITIR - self.SURE_EKSILME_DURAKLA)):
                    self._tur_sonuclandir()
                    return
        else:
            self.eksik_baslangic_t = None
            self.durakla_t = None
            if self.faz == "durakla":
                self.faz = "oyna"

        if self.faz == "durakla":
            return

        # Soru çözümü kontrolü
        donmus_var = any(o.durum == "donmus" for o in self.oyuncular.values())
        kart_dizisi = self._mevcut_kartlar_sirasi()
        dogru = (len(kart_dizisi) == self.N) and self.icerik.dogru_mu(kart_dizisi)

        if dogru and not donmus_var:
            self.bozulma_t = None
            if self.sayim_baslangic_t is None:
                self.sayim_baslangic_t = self.simdi
                self.sayim_gecen = 0.0

            self.sayim_gecen = self.simdi - self.sayim_baslangic_t
            kalan_sn = int(math.ceil(max(0.0, self.SURE_SAYIM - self.sayim_gecen)))

            if kalan_sn != self.son_tik_sn and kalan_sn > 0:
                self.son_tik_sn = kalan_sn
                self.ses.cal("pop" if kalan_sn > 1 else "ding", 0.5)

            if self.sayim_gecen >= self.SURE_SAYIM:
                gecen_sn = self.simdi - self.soru_baslangic_t
                ipucu_kesinti = 0
                if gecen_sn >= self.SURE_IPUCU_SON:
                    ipucu_kesinti = 300
                elif gecen_sn >= self.SURE_IPUCU_1:
                    ipucu_kesinti = 150

                soru_puan = max(100, int(1000 - 12 * gecen_sn - ipucu_kesinti))
                self.skor += soru_puan
                self.toplam_sure += gecen_sn

                self.soru_no += 1
                self.faz = "kutla"
                self.kutlama_t = self.simdi
                self.sayim_baslangic_t = None
                self.sayim_gecen = 0.0
                self.bozulma_t = None
                self.ses.cal("basari", 0.8)
                return
        else:
            if self.sayim_baslangic_t is not None:
                if self.bozulma_t is None:
                    self.bozulma_t = self.simdi
                elif self.simdi - self.bozulma_t > self.SURE_SAYIM_TOLERANS:
                    self.sayim_baslangic_t = None
                    self.sayim_gecen = 0.0
                    self.bozulma_t = None
                    self.son_tik_sn = -1
                    self.ses.cal("bonk", 0.4)
                    self._uyari_ver("Bozuldu!", 0.6)

        soru_gecen = self.simdi - self.soru_baslangic_t
        if soru_gecen >= self.SURE_PAS_IZIN:
            hepsi_el = True
            for o in self.oyuncular.values():
                if o.poz and self._el_burun_ustunde_mi(o.poz):
                    t0 = self.pas_el_t.setdefault(o.kimlik, self.simdi)
                    if self.simdi - t0 < 0.8:
                        hepsi_el = False
                else:
                    self.pas_el_t.pop(o.kimlik, None)
                    hepsi_el = False

            if hepsi_el and len(self.pas_el_t) == self.N:
                self._uyari_ver("Pas geçildi!", 1.0)
                self.toplam_sure += soru_gecen
                self.soru_no += 1
                self.faz = "kutla"
                self.kutlama_t = self.simdi
                self.ses.cal("bonk", 0.6)

    def _tur_sonuclandir(self) -> None:
        self.faz = "sonuc"
        self.durum = "sonuc"
        self.sonuc_baslangic_t = self.simdi
        self.takim_adi = str(self.rng.choice(TAKIM_ISIMLERI))
        self.gecmis_skorlar.append((self.takim_adi, self.skor))
        self.gecmis_skorlar.sort(key=lambda x: x[1], reverse=True)
        self.en_iyiler = list(self.gecmis_skorlar[:5])
        self.ses.cal("basari", 0.9)

    # ---------------------------------------------------------
    # Ana İşleme Döngüsü (isle)
    # ---------------------------------------------------------
    def isle(self, kare: np.ndarray, algi: Optional[Algi], simdi: float) -> np.ndarray:
        self.simdi = simdi
        self.son_algi = algi
        cikis = cv2.convertScaleAbs(kare, alpha=0.65) if (kare is not None and kare.size > 0) else np.zeros((Y, G, 3), dtype=np.uint8)

        poz_list = self._suzulmus_pozlar(algi)

        if self.faz == "lobi":
            self._lobi_guncelle(poz_list)
        elif self.faz in ("dagit", "oyna", "kutla", "durakla"):
            self._oyuncu_durumlarini_guncelle(poz_list, kare)
            self._imza_guncelle(kare, poz_list)
            if not self.imzasiz:
                self._karisma_ve_cozum_yonetimi(poz_list, kare)
                self._belirsizlik_ve_el_takas_yonetimi()
            self._oyun_dongusu_guncelle()
        elif self.faz == "sonuc":
            if self.simdi - self.sonuc_baslangic_t >= self.SURE_SONUC_RESET:
                self.faz = "lobi"
                self.durum = "bekle"
                self.oyuncular.clear()
                self._onceki_sira.clear()
                self._lobi_idler = ()
                self._lobi_stabil_t = self.simdi
                self._lobi_el_t.clear()

        # Kayıt kancası
        if self.kayit_araci is not None and hasattr(self.kayit_araci, "kare_ekle"):
            self.kayit_araci.kare_ekle(self, algi, self.simdi, kare=kare)

        self._ciz_iskeletler(cikis, poz_list)
        self._ciz_arayuz(cikis, poz_list)

        return cikis

    # ---------------------------------------------------------
    # Çizim Yardımcıları
    # ---------------------------------------------------------
    def _ciz_iskeletler(self, img: np.ndarray, poz_list: List[Tuple[int, Any, bool]]) -> None:
        katman = img.copy()
        pid_renk = {o.poz_id: o.renk for o in self.oyuncular.values()}

        for pid, lm, _ in poz_list:
            renk = pid_renk.get(pid, (120, 120, 120))
            for i1, i2 in SKELETON_BAGLANTILAR:
                try:
                    p1, p2 = lm[i1], lm[i2]
                    v1 = float(getattr(p1, "visibility", 1.0))
                    v2 = float(getattr(p2, "visibility", 1.0))
                    if v1 > 0.4 and v2 > 0.4:
                        x1, y1 = int(p1.x * G), int(p1.y * Y)
                        x2, y2 = int(p2.x * G), int(p2.y * Y)
                        cv2.line(katman, (x1, y1), (x2, y2), renk, 2, cv2.LINE_AA)
                except Exception:
                    pass

        cv2.addWeighted(img, 0.6, katman, 0.4, 0, dst=img)

    @staticmethod
    def _kart_tipi(metin: str) -> str:
        m = metin.strip()
        if m in ("+", "-", "×", "÷", "−", "*", "/"):
            return "islem"
        if m == "=":
            return "esittir"
        return "dikdortgen"

    @classmethod
    def _kart_genisligi(cls, metin: str) -> int:
        tip = cls._kart_tipi(metin)
        if tip == "islem":
            return 100
        if tip == "esittir":
            return 130
        return max(150, yazi_sprite(metin, 56).shape[1] + 32)

    def _ciz_kart(self, img: np.ndarray, x: float, y: float, metin: str, renk: Tuple[int, int, int], durum: str, ok_hedef: Optional[Tuple[int, int]] = None) -> None:
        H, W = img.shape[:2]
        cx, cy = int(x * W), int(y * H)
        tip = self._kart_tipi(metin)

        font_boy = 56
        kart_g = self._kart_genisligi(metin)
        kart_y = 90
        bolge = (max(0, cy - 60), min(H, cy + 60), max(0, cx - kart_g // 2 - 8), min(W, cx + kart_g // 2 + 8))
        y0b, y1b, x0b, x1b = bolge
        arka = img[y0b:y1b, x0b:x1b].copy() if durum == "donmus" else None

        if tip == "islem":
            r = 50
            cv2.circle(img, (cx, cy), r, (24, 24, 32), -1, cv2.LINE_AA)
            cv2.circle(img, (cx, cy), r, renk, 3 if durum == "normal" else 2, cv2.LINE_AA)
            yazi_koy(img, metin, cx, cy - font_boy // 2, font_boy, renk=BEYAZ, hiza="orta")
        elif tip == "esittir":
            rw, rh = 65, 30
            panel(img, cx - rw, cy - rh, cx + rw, cy + rh, renk=(24, 24, 32), opak=0.85, kenar=renk)
            yazi_koy(img, metin, cx, cy - font_boy // 2, font_boy, renk=BEYAZ, hiza="orta")
        else:
            x0 = cx - kart_g // 2
            y0 = cy - kart_y // 2
            x1 = cx + kart_g // 2
            y1 = cy + kart_y // 2
            panel(img, x0, y0, x1, y1, renk=(20, 20, 28), opak=0.85, kenar=renk)
            yazi_koy(img, metin, cx, cy - font_boy // 2 + 2, font_boy, renk=BEYAZ, hiza="orta")

        if durum == "donmus":
            hedef = img[y0b:y1b, x0b:x1b]
            if hedef.size:
                cv2.addWeighted(arka, .35, hedef, .65, 0, dst=hedef)
            halka(img, cx + kart_g // 2 - 10, cy - kart_y // 2 + 10, (self.simdi * 2) % 1.0, r=14, renk=SARI, kalinlik=3)
        elif durum == "belirsiz":
            cv2.circle(img, (cx + kart_g // 2 - 12, cy - kart_y // 2 + 12), 16, SARI, -1, cv2.LINE_AA)
            yazi_koy(img, "?", cx + kart_g // 2 - 12, cy - kart_y // 2 - 2, 28, renk=(0, 0, 0), hiza="orta")

        if ok_hedef is not None:
            tx, ty = ok_hedef
            cv2.arrowedLine(img, (cx, cy + kart_y // 2), (tx, ty), renk, 2, cv2.LINE_AA, tipLength=0.15)

    def _ciz_arayuz(self, img: np.ndarray, poz_list: List[Tuple[int, Any, bool]]) -> None:
        if self.mesaj_uyari and self.simdi < self.mesaj_uyari_bitis:
            panel(img, G // 4, 30, 3 * G // 4, 90, renk=(30, 10, 10), opak=0.9, kenar=KIRMIZI)
            yazi_koy(img, self.mesaj_uyari, G // 2, 42, 38, renk=SARI, hiza="orta")

        if self.faz == "lobi":
            self._ciz_lobi(img, poz_list)
        elif self.faz in ("dagit", "oyna", "kutla", "durakla"):
            self._ciz_oyun_ve_kartlar(img)
        elif self.faz == "sonuc":
            self._ciz_sonuc(img)

    def _ciz_lobi(self, img: np.ndarray, poz_list: List[Tuple[int, Any, bool]]) -> None:
        sayi = len([p for p in poz_list if not p[2]])
        yazi_koy(img, f"{self.AD}", G // 2, Y - 240, 48, renk=SARI, hiza="orta")

        kural_metni = "Kartları doğru işlem olacak şekilde dizin!" if "İşlem" in self.AD else "Yer değiştirin, cümleyi doğru kurun!"
        yazi_koy(img, kural_metni, G // 2, Y - 184, 30, renk=BEYAZ, hiza="orta")

        for pid, lm, _ in poz_list:
            try:
                bx, by = float(lm[LANDMARK_BURUN].x), float(lm[LANDMARK_BURUN].y)
                cx, cy = int(bx * G), int(max(0.12, by - 0.18) * Y)
                panel(img, cx - 60, cy - 35, cx + 60, cy + 35, renk=(20, 20, 30), opak=0.7, kenar=CAMGOBEGI)
                if pid in self._lobi_el_t:
                    oran = min(1.0, (self.simdi - self._lobi_el_t[pid]) / self.SURE_LOBI_EL)
                    halka(img, cx, cy, oran, r=26, renk=YESIL, kalinlik=4)
            except Exception:
                pass

        if sayi < 3:
            yazi_koy(img, "En az 3 kişi lazım", G // 2, Y - 120, 40, renk=PEMBE, hiza="orta")
        elif sayi > 5:
            yazi_koy(img, "En fazla 5 kişi, biri geri çekilsin", G // 2, Y - 120, 40, renk=PEMBE, hiza="orta")
        else:
            if self.simdi - self._lobi_stabil_t >= self.SURE_LOBI_STABIL:
                yazi_koy(img, f"{sayi} kişi hazır! Başlamak için elinizi kaldırın", G // 2, Y - 120, 36, renk=YESIL, hiza="orta")
            else:
                yazi_koy(img, f"{sayi} kişi algılandı, bekleniyor...", G // 2, Y - 120, 36, renk=SARI, hiza="orta")

    def _ciz_oyun_ve_kartlar(self, img: np.ndarray) -> None:
        soru_sure = self.simdi - self.soru_baslangic_t if self.faz == "oyna" else 0.0
        gosterim_soru_no = min(self.SORU_SAYISI, self.soru_no + 1)
        yazi_koy(img, f"Soru: {gosterim_soru_no}/{self.SORU_SAYISI}", 80, 8, 28, renk=CAMGOBEGI)
        yazi_koy(img, f"Puan: {self.skor}", G // 2, 8, 28, renk=SARI, hiza="orta")
        yazi_koy(img, f"Süre: {int(soru_sure)}s", G - 120, 8, 28, renk=BEYAZ, hiza="orta")

        sirali = self._mevcut_dizilim()
        genislikler = [self._kart_genisligi(o.kart) for o in sirali]
        satirlar, satir = [], []
        for idx, genislik in enumerate(genislikler):
            if satir and sum(genislikler[i] for i in satir) + genislik + 16 * len(satir) > G - 24:
                satirlar.append(satir)
                satir = []
            satir.append(idx)
        if satir:
            satirlar.append(satir)
        kart_x_hedefleri = [o.x for o in sirali]
        satir_no = {}
        for no, indeksler in enumerate(satirlar):
            for idx in indeksler:
                fx = self.kart_x_filtre.setdefault(sirali[idx].kimlik, BirEuro())
                kart_x_hedefleri[idx] = float(fx.suz(sirali[idx].x, self.simdi)) * G
                satir_no[idx] = no
            ilk, son = indeksler[0], indeksler[-1]
            kart_x_hedefleri[ilk] = max(12 + genislikler[ilk] / 2, kart_x_hedefleri[ilk])
            for once, idx in zip(indeksler, indeksler[1:]):
                kart_x_hedefleri[idx] = max(kart_x_hedefleri[idx], kart_x_hedefleri[once] + (genislikler[once] + genislikler[idx]) / 2 + 16)
            kart_x_hedefleri[son] = min(G - 12 - genislikler[son] / 2, kart_x_hedefleri[son])
            for idx, sonra in reversed(list(zip(indeksler, indeksler[1:]))):
                kart_x_hedefleri[idx] = min(kart_x_hedefleri[idx], kart_x_hedefleri[sonra] - (genislikler[idx] + genislikler[sonra]) / 2 - 16)

        for idx, o in enumerate(sirali):
            fy = self.kart_y_filtre.setdefault(o.kimlik, BirEuro(min_cutoff=1.0, beta=0.008, d_cutoff=1.0))

            hedef_x = kart_x_hedefleri[idx] / G
            hedef_y = max(0.14, o.y_bas - 0.18) + satir_no[idx] * 106 / Y

            if self.faz == "dagit":
                t_kisisel = max(0.0, (self.simdi - self.dagitim_baslangic_t) - idx * self.SURE_DAGITIM_ADIM)
                oran = min(1.0, t_kisisel / self.SURE_DAGITIM)
                hedef_y = -0.1 + (hedef_y + 0.1) * oran

            filtreli_x = hedef_x
            filtreli_y = float(fy.suz(hedef_y, self.simdi))

            bas_piksel = (int(o.x * G), int(max(0.15, o.y_bas - 0.05) * Y))
            self._ciz_kart(img, filtreli_x, filtreli_y, o.kart, o.renk, o.durum, ok_hedef=bas_piksel)

        kutu_g = 120
        ara_bosluk = 30
        toplam_w = self.N * kutu_g + (self.N - 1) * ara_bosluk
        bas_x = (G - toplam_w) // 2
        kutu_y = Y - 90

        tam_dogru = (self.sayim_baslangic_t is not None)
        for i in range(self.N):
            kx = bas_x + i * (kutu_g + ara_bosluk)
            renk_kutu = YESIL if tam_dogru else (60, 60, 75)
            panel(img, kx, kutu_y, kx + kutu_g, kutu_y + 60, renk=(20, 20, 30), opak=0.8, kenar=renk_kutu)
            yazi_koy(img, str(i + 1), kx + kutu_g // 2, kutu_y + 12, 34, renk=BEYAZ, hiza="orta")

            if soru_sure >= self.SURE_IPUCU_1 and i == 0 and len(self.kanonik_cevap) > 0:
                yazi_koy(img, self.kanonik_cevap[0], kx + kutu_g // 2, kutu_y - 30, 26, renk=SARI, hiza="orta")
            if soru_sure >= self.SURE_IPUCU_SON and i == self.N - 1 and len(self.kanonik_cevap) > 0:
                yazi_koy(img, self.kanonik_cevap[-1], kx + kutu_g // 2, kutu_y - 30, 26, renk=SARI, hiza="orta")

        if self.sayim_baslangic_t is not None:
            oran = min(1.0, self.sayim_gecen / self.SURE_SAYIM)
            halka(img, G // 2, Y // 2, oran, r=80, renk=YESIL, kalinlik=10)
            kalan_rakam = str(max(1, int(math.ceil(self.SURE_SAYIM - self.sayim_gecen))))
            yazi_koy(img, kalan_rakam, G // 2, Y // 2 - 35, 72, renk=YESIL, hiza="orta")

        belirsiz_var = any(o.durum == "belirsiz" for o in self.oyuncular.values())
        if belirsiz_var:
            panel(img, G // 4, Y - 160, 3 * G // 4, Y - 110, renk=(40, 35, 10), opak=0.9, kenar=SARI)
            yazi_koy(img, "Kart yanlış kişide mi? Elini kaldır.", G // 2, Y - 150, 32, renk=SARI, hiza="orta")

        if self.faz == "kutla":
            gecen = self.simdi - self.kutlama_t
            dalga_x = int(gecen * G * 1.5)
            cv2.line(img, (dalga_x, 0), (dalga_x, Y), YESIL, 6, cv2.LINE_AA)

    def _ciz_sonuc(self, img: np.ndarray) -> None:
        panel(img, G // 4, 80, 3 * G // 4, Y - 80, renk=(15, 15, 24), opak=0.95, kenar=CAMGOBEGI)
        yazi_koy(img, "TUR TAMAMLANDI!", G // 2, 110, 48, renk=YESIL, hiza="orta")
        yazi_koy(img, f"Takım: {self.takim_adi}", G // 2, 170, 36, renk=SARI, hiza="orta")
        yazi_koy(img, f"Toplam Skor: {self.skor}", G // 2, 220, 40, renk=BEYAZ, hiza="orta")

        yazi_koy(img, "EN İYİLER", G // 2, 290, 32, renk=CAMGOBEGI, hiza="orta")
        for i, (ad, sk) in enumerate(self.en_iyiler[:5]):
            satir = f"{i + 1}. {ad} - {sk}"
            yazi_koy(img, satir, G // 2, 340 + i * 45, 30, renk=BEYAZ if ad != self.takim_adi else SARI, hiza="orta")

    # ---------------------------------------------------------
    # Ölçüm ve Kayıt Arayüzü (JSON-safe, görüntü yok)
    # ---------------------------------------------------------
    def yalin_kayit(self, algi: Optional[Algi], simdi: float) -> Dict[str, Any]:
        """Görüntü barındırmayan, 33 landmarks ve imza vektörlerini içeren JSON-safe kayıt."""
        kayit: Dict[str, Any] = {
            "t": float(simdi),
            "faz": self.faz,
            "durum": self.durum,
            "soru_no": self.soru_no,
            "skor": self.skor,
            "esleme": {kid: o.poz_id for kid, o in self.oyuncular.items()},
            "oyuncular": {},
            "pozlar": {},
            "olaylar": copy.deepcopy(self.olaylar),
        }

        if algi is not None:
            for pid, lm in zip(getattr(algi, "poz_id", []), getattr(algi, "pozlar", [])):
                pts = []
                for p in lm[:33]:
                    pts.append([
                        float(getattr(p, "x", 0.0)),
                        float(getattr(p, "y", 0.0)),
                        float(getattr(p, "z", 0.0)),
                        float(getattr(p, "visibility", 1.0)),
                    ])
                kayit["pozlar"][int(pid)] = pts

        for kid, o in self.oyuncular.items():
            imza_vec = self.imzalar.al(kid)
            hist_list = imza_vec["govde"]["hist"].tolist() if (imza_vec and "govde" in imza_vec) else []
            lab_list = imza_vec["govde"]["lab"].tolist() if (imza_vec and "govde" in imza_vec) else []
            kayit["oyuncular"][kid] = {
                "poz_id": o.poz_id,
                "kart": o.kart,
                "x": float(o.x),
                "durum": o.durum,
                "imza_hist": hist_list,
                "imza_lab": lab_list,
            }

        return kayit
