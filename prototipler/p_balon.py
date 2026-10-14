from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    KIRMIZI,
    PEMBE,
    SARI,
    Y,
    YESIL,
    Parcaciklar,
    baslik,
    bindir_merkez,
    bulanik_karanlik,
    emoji_sprite,
    halka,
    panel,
    parilti,
    px,
    yazi_koy,
)


@dataclass
class Balon:
    x: float
    y: float
    r: float
    tur: str  # "normal" | "altin" | "bomba"
    taban_x: float = 0.0
    hiz_y: float = 130.0
    faz: float = 0.0
    salinim_gen: float = 18.0
    salinim_hiz: float = 2.5
    kova_r: int = 46


@dataclass
class HalkaEfekt:
    x: float
    y: float
    r0: float
    renk: Tuple[int, int, int]
    t0: float
    sure: float = 0.25


@dataclass
class YaziEfekt:
    metin: str
    x: float
    y: float
    renk: Tuple[int, int, int]
    t0: float
    sure: float = 0.6


def _balon_sprite_uret(r: int, tur: str, bomba_emj: Optional[np.ndarray] = None) -> np.ndarray:
    boy = 2 * r + 12
    yy, xx = np.mgrid[0:boy, 0:boy].astype(np.float32)
    cx = cy = boy / 2.0
    dx = xx - cx
    dy = yy - cy
    dist = np.hypot(dx, dy)
    aci = np.arctan2(dy, dx)

    bgra = np.zeros((boy, boy, 4), dtype=np.uint8)
    ic = dist <= r
    norm_d = np.clip(dist / float(r), 0.0, 1.0)

    if tur == "normal":
        # Gökkuşağı kenar tonu
        b = 190.0 + 65.0 * np.sin(aci * 2.0 + 0.0)
        g = 190.0 + 65.0 * np.sin(aci * 2.0 + 2.1)
        rc = 190.0 + 65.0 * np.sin(aci * 2.0 + 4.2)

        kenar_zarf = np.exp(-((dist - (r - 2.2)) ** 2) / 7.5)
        beyaz_kenar = np.exp(-((dist - (r - 0.8)) ** 2) / 1.8)

        B = np.clip(b * kenar_zarf + 255.0 * beyaz_kenar * 0.7, 0, 255)
        Gr = np.clip(g * kenar_zarf + 255.0 * beyaz_kenar * 0.7, 0, 255)
        R = np.clip(rc * kenar_zarf + 255.0 * beyaz_kenar * 0.7, 0, 255)

        ic_alfa = (22.0 + 48.0 * (norm_d ** 3)) * ic
        kenar_alfa = (165.0 * kenar_zarf + 195.0 * beyaz_kenar) * (dist <= r + 2.0)
        A = np.clip(np.maximum(ic_alfa, kenar_alfa), 0, 245)

    elif tur == "altin":
        kenar_zarf = np.exp(-((dist - (r - 2.5)) ** 2) / 9.0)
        beyaz_kenar = np.exp(-((dist - (r - 0.8)) ** 2) / 2.0)
        parilti_ic = (1.0 - norm_d * 0.35) * ic

        B = np.clip(25.0 * parilti_ic + 90.0 * kenar_zarf + 255.0 * beyaz_kenar * 0.85, 0, 255)
        Gr = np.clip(215.0 * parilti_ic + 235.0 * kenar_zarf + 255.0 * beyaz_kenar * 0.85, 0, 255)
        R = np.clip(255.0 * parilti_ic + 255.0 * kenar_zarf + 255.0 * beyaz_kenar * 0.85, 0, 255)

        ic_alfa = (55.0 + 80.0 * (norm_d ** 2)) * ic
        kenar_alfa = (210.0 * kenar_zarf + 220.0 * beyaz_kenar) * (dist <= r + 2.0)
        A = np.clip(np.maximum(ic_alfa, kenar_alfa), 0, 250)

    else:  # "bomba"
        kenar_zarf = np.exp(-((dist - (r - 2.5)) ** 2) / 8.5)
        kirmizi_ipucu = 0.5 + 0.5 * np.sin(aci * 4.0)

        B = np.clip(95.0 * ic + 180.0 * kenar_zarf, 0, 255)
        Gr = np.clip(20.0 * ic + 45.0 * kenar_zarf, 0, 255)
        R = np.clip(85.0 * ic + (190.0 + 65.0 * kirmizi_ipucu) * kenar_zarf, 0, 255)

        ic_alfa = (155.0 + 45.0 * (norm_d ** 2)) * ic
        kenar_alfa = 225.0 * kenar_zarf * (dist <= r + 2.0)
        A = np.clip(np.maximum(ic_alfa, kenar_alfa), 0, 245)

    # Sol üst parlak yansıma noktası (sabun köpüğü hissi)
    hx = cx - r * 0.36
    hy = cy - r * 0.36
    hdist = np.hypot(xx - hx, yy - hy)
    parlak1 = np.exp(-(hdist ** 2) / max(2.0, (r * 0.16) ** 2))

    hx2 = cx - r * 0.18
    hy2 = cy - r * 0.50
    hdist2 = np.hypot(xx - hx2, yy - hy2)
    parlak2 = np.exp(-(hdist2 ** 2) / max(1.5, (r * 0.08) ** 2)) * 0.7

    parlak = np.clip(parlak1 + parlak2, 0.0, 1.0)

    B = np.clip(B + 255.0 * parlak, 0, 255)
    Gr = np.clip(Gr + 255.0 * parlak, 0, 255)
    R = np.clip(R + 255.0 * parlak, 0, 255)
    A = np.clip(A + 235.0 * parlak, 0, 255)

    bgra[..., 0] = B.astype(np.uint8)
    bgra[..., 1] = Gr.astype(np.uint8)
    bgra[..., 2] = R.astype(np.uint8)
    bgra[..., 3] = A.astype(np.uint8)

    if tur == "bomba" and bomba_emj is not None:
        em_boy = max(18, int(r * 1.15))
        em_resized = cv2.resize(bomba_emj, (em_boy, em_boy), interpolation=cv2.INTER_AREA)
        x0 = int(cx - em_boy // 2)
        y0 = int(cy - em_boy // 2)
        x1 = x0 + em_boy
        y1 = y0 + em_boy
        if x0 >= 0 and y0 >= 0 and x1 <= boy and y1 <= boy:
            hedef = bgra[y0:y1, x0:x1].astype(np.float32)
            kaynak = em_resized.astype(np.float32)
            ea = (kaynak[..., 3:4] / 255.0) * 0.95
            hedef[..., :3] = kaynak[..., :3] * ea + hedef[..., :3] * (1.0 - ea)
            hedef[..., 3:4] = np.clip(kaynak[..., 3:4] * 0.95 + hedef[..., 3:4] * (1.0 - ea), 0, 255)
            bgra[y0:y1, x0:x1] = hedef.astype(np.uint8)

    return bgra


class Prototip:
    AD = "Balon Patlat"
    ACIKLAMA = "Yükselen balonları parmak uçlarınla ya da burnunla patlat!"
    IHTIYAC = {"el", "yuz"}
    SIRA = 15

    KOVALAR = (30, 38, 46, 54, 62, 70)
    OYUN_SURESI = 45.0
    MAKS_BALON = 22

    def __init__(self, ses):
        self.ses = ses
        self.durum = "bekle"
        self.skor = 0
        self.rekor = 0
        self.balonlar: List[Balon] = []

        self.onceki_t: Optional[float] = None
        self.durum_t0: float = 0.0
        self.algilama_suresi: float = 0.0
        self.son_dogum_t: float = 0.0

        self.kombo: int = 0
        self.son_patlama_t: float = -10.0
        self.skor_pop_t: float = -10.0
        self.bomba_flas_t: float = -10.0
        self.sarsinti_t: float = -10.0

        self.parcaciklar = Parcaciklar(220)
        self.halkalar: List[HalkaEfekt] = []
        self.yazilar: List[YaziEfekt] = []
        self.yumusak_imlecler: Dict[Tuple[str, int, int], Tuple[float, float]] = {}

        self.spritelar: Dict[Tuple[str, int], np.ndarray] = {}
        self._hazir = False
        self._rng = random.Random(1337)

        # İlk başlangıçta ekranda hemen balonlar görünsün
        for i in range(6):
            b = self._yeni_balon(sadece_normal=True)
            b.y = Y - 80 - i * 95
            self.balonlar.append(b)

    def _hazirla(self) -> None:
        if self._hazir:
            return
        bomba_emj = emoji_sprite("💣", 128)
        for r in self.KOVALAR:
            self.spritelar[("normal", r)] = _balon_sprite_uret(r, "normal")
            self.spritelar[("altin", r)] = _balon_sprite_uret(r, "altin")
            self.spritelar[("bomba", r)] = _balon_sprite_uret(r, "bomba", bomba_emj)
        self._hazir = True

    def _en_yakin_kova(self, r: float) -> int:
        return min(self.KOVALAR, key=lambda k: abs(k - r))

    def _yeni_balon(self, sadece_normal: bool = False) -> Balon:
        r_float = self._rng.uniform(30.0, 70.0)
        kova = self._en_yakin_kova(r_float)
        r = float(kova)

        if sadece_normal:
            tur = "normal"
        else:
            zar = self._rng.random()
            if zar < 0.80:
                tur = "normal"
            elif zar < 0.92:
                tur = "altin"
            else:
                tur = "bomba"

        kenar_payi = int(r + 45)
        taban_x = float(self._rng.randint(kenar_payi, G - kenar_payi))
        y = float(Y + r + self._rng.uniform(5.0, 45.0))

        # Küçük balonlar biraz daha hızlı, altın balonlar biraz daha canlı
        hiz_y = self._rng.uniform(90.0, 220.0)
        if tur == "altin":
            hiz_y = max(135.0, hiz_y * 1.12)

        faz = self._rng.uniform(0.0, math.tau)
        salinim_gen = self._rng.uniform(14.0, 34.0)
        salinim_hiz = self._rng.uniform(1.6, 3.4)
        x = taban_x + math.sin(faz) * salinim_gen

        return Balon(
            x=x,
            y=y,
            r=r,
            tur=tur,
            taban_x=taban_x,
            hiz_y=hiz_y,
            faz=faz,
            salinim_gen=salinim_gen,
            salinim_hiz=salinim_hiz,
            kova_r=kova,
        )

    def _patlaticilari_topla(self, algi) -> List[Tuple[float, float, str]]:
        ham: Dict[Tuple[str, int, int], Tuple[float, float]] = {}

        if algi and algi.eller:
            for ei, el in enumerate(algi.eller):
                if len(el) > 8:
                    for idx in (8, 4):
                        x, y = px(el, idx)
                        x = max(0.0, min(float(G - 1), float(x)))
                        y = max(0.0, min(float(Y - 1), float(y)))
                        ham[("el", ei, idx)] = (x, y)

        if algi and algi.yuzler:
            for yi, yuz in enumerate(algi.yuzler):
                if len(yuz) > 1:
                    x, y = px(yuz, 1)
                    x = max(0.0, min(float(G - 1), float(x)))
                    y = max(0.0, min(float(Y - 1), float(y)))
                    ham[("yuz", yi, 1)] = (x, y)

        yeni_yumusak: Dict[Tuple[str, int, int], Tuple[float, float]] = {}
        sonuc: List[Tuple[float, float, str]] = []
        alfa = 0.55

        for anahtar, (hx, hy) in ham.items():
            if anahtar in self.yumusak_imlecler:
                ox, oy = self.yumusak_imlecler[anahtar]
                nx = ox + alfa * (hx - ox)
                ny = oy + alfa * (hy - oy)
            else:
                nx, ny = hx, hy
            yeni_yumusak[anahtar] = (nx, ny)
            sonuc.append((nx, ny, anahtar[0]))

        self.yumusak_imlecler = yeni_yumusak
        return sonuc

    def _balon_patlat(self, b: Balon, simdi: float, puanli: bool) -> None:
        if not puanli:
            self.ses.cal("pop", 0.55)
            self.parcaciklar.yay(b.x, b.y, 14, renk=CAMGOBEGI, hiz=4.2)
            self.halkalar.append(HalkaEfekt(b.x, b.y, b.r, CAMGOBEGI, simdi))
            return

        if b.tur == "bomba":
            self.kombo = 0
            degisim = -3
            self.skor += degisim
            self.ses.cal("bonk", 0.85)
            self.ses.cal("zap", 0.65)
            self.parcaciklar.yay(b.x, b.y, 18, renk=KIRMIZI, hiz=5.5)
            self.halkalar.append(HalkaEfekt(b.x, b.y, b.r, KIRMIZI, simdi))
            self.yazilar.append(YaziEfekt("-3", b.x, b.y, KIRMIZI, simdi))
            self.bomba_flas_t = simdi
            self.sarsinti_t = simdi
            self.skor_pop_t = simdi
            return

        # Normal veya altın balon
        if simdi - self.son_patlama_t <= 1.2:
            self.kombo += 1
        else:
            self.kombo = 1
        self.son_patlama_t = simdi

        carpan = 2 if self.kombo >= 5 else 1
        taban = 3 if b.tur == "altin" else 1
        degisim = taban * carpan
        self.skor += degisim
        if self.skor > self.rekor:
            self.rekor = self.skor

        self.skor_pop_t = simdi

        if b.tur == "altin":
            self.ses.cal("basari", 0.8)
            renk = SARI
            adet = 18
        else:
            self.ses.cal("pop", 0.75)
            if self.kombo >= 5:
                nota = min(84, 60 + self.kombo)
                self.ses.cal(f"nota{nota}", 0.45)
            renk = CAMGOBEGI if self.kombo < 5 else PEMBE
            adet = 15

        self.parcaciklar.yay(b.x, b.y, adet, renk=renk, hiz=4.6)
        self.halkalar.append(HalkaEfekt(b.x, b.y, b.r, renk, simdi))
        self.yazilar.append(YaziEfekt(f"+{degisim}", b.x, b.y, renk, simdi))

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R"), 32):
            self.durum = "bekle"
            self.skor = 0
            self.kombo = 0
            self.algilama_suresi = 0.0

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        self._hazirla()

        if self.onceki_t is None:
            dt = 0.016
            self.durum_t0 = simdi
            self.son_dogum_t = simdi
        else:
            dt = min(max(float(simdi - self.onceki_t), 0.0), 0.1)
        self.onceki_t = simdi

        biri_var = bool((algi and algi.eller) or (algi and algi.yuzler))
        patlaticilar = self._patlaticilari_topla(algi)

        # Durum makinesi geçişleri
        if self.durum == "bekle":
            if biri_var:
                self.algilama_suresi += dt
                if self.algilama_suresi >= 1.0:
                    self.durum = "oyun"
                    self.durum_t0 = simdi
                    self.skor = 0
                    self.kombo = 0
                    self.son_patlama_t = -10.0
                    self.son_dogum_t = simdi
                    self.algilama_suresi = 0.0
                    self.ses.cal("woosh", 0.7)
            else:
                self.algilama_suresi = max(0.0, self.algilama_suresi - dt * 2.0)

        elif self.durum == "oyun":
            gecen = simdi - self.durum_t0
            if gecen >= self.OYUN_SURESI:
                if self.skor > self.rekor:
                    self.rekor = self.skor
                self.durum = "sonuc"
                self.durum_t0 = simdi
                self.ses.cal("basari", 0.85)

        elif self.durum == "sonuc":
            if simdi - self.durum_t0 >= 4.0:
                self.durum = "bekle"
                self.durum_t0 = simdi
                self.algilama_suresi = 0.0
                self.kombo = 0

        # Balon doğurma
        if self.durum == "bekle":
            aralik = 0.75
            hedef_tavan = 10
            if simdi - self.son_dogum_t >= aralik and len(self.balonlar) < hedef_tavan:
                b = self._yeni_balon(sadece_normal=True)
                b.hiz_y = self._rng.uniform(75.0, 125.0)
                self.balonlar.append(b)
                self.son_dogum_t = simdi

        elif self.durum == "oyun":
            gecen = max(0.0, min(self.OYUN_SURESI, simdi - self.durum_t0))
            ilerleme = gecen / self.OYUN_SURESI
            aralik = 0.50 - 0.25 * ilerleme  # 0.50 sn -> 0.25 sn
            if simdi - self.son_dogum_t >= aralik and len(self.balonlar) < self.MAKS_BALON:
                self.balonlar.append(self._yeni_balon(sadece_normal=False))
                self.son_dogum_t = simdi

        # Balonları güncelle ve çarpışmaları kontrol et
        kalan_balonlar: List[Balon] = []
        puanli_mod = self.durum == "oyun"
        etkilesim_aktif = self.durum in ("bekle", "oyun")

        for b in self.balonlar:
            b.y -= b.hiz_y * dt
            b.faz += b.salinim_hiz * dt
            b.x = max(b.r + 8.0, min(G - b.r - 8.0, b.taban_x + math.sin(b.faz) * b.salinim_gen))

            if b.y < -b.r - 20.0:
                continue

            patladi = False
            if etkilesim_aktif and patlaticilar:
                # Parmak/burun yakınsa patlat (hafif cömert yarıçap +10px)
                etki_r2 = (b.r + 10.0) ** 2
                for px_x, px_y, _ in patlaticilar:
                    dx = px_x - b.x
                    dy = px_y - b.y
                    if dx * dx + dy * dy <= etki_r2:
                        patladi = True
                        break

            if patladi:
                self._balon_patlat(b, simdi, puanli=puanli_mod)
            else:
                kalan_balonlar.append(b)

        self.balonlar = kalan_balonlar

        # Kombo zaman aşımı
        if self.kombo > 0 and (simdi - self.son_patlama_t > 1.2):
            self.kombo = 0

        # Görsel çizim aşaması
        if self.durum in ("bekle", "sonuc"):
            out = bulanik_karanlik(kare, 0.55)
        else:
            out = kare

        # Balonları çiz
        for b in self.balonlar:
            sp = self.spritelar.get((b.tur, b.kova_r))
            if sp is not None:
                bindir_merkez(out, sp, int(b.x), int(b.y))

        # Parıltı (neon) katmanı: patlatıcı imleçleri ve genişleyen halkalar
        katman = np.zeros_like(out)

        # Genişleyen halkalar (0.25 sn)
        aktif_halkalar: List[HalkaEfekt] = []
        for h in self.halkalar:
            yas = simdi - h.t0
            if 0.0 <= yas < h.sure:
                p = yas / h.sure
                r_anlik = int(h.r0 * (1.0 + 0.55 * p))
                kalinlik = max(1, int(5 * (1.0 - p)))
                renk_anlik = tuple(int(c * (1.0 - p * 0.7)) for c in h.renk)
                cv2.circle(katman, (int(h.x), int(h.y)), r_anlik, renk_anlik, kalinlik, cv2.LINE_AA)
                aktif_halkalar.append(h)
        self.halkalar = aktif_halkalar

        # Patlatıcı noktalarını neon imleç olarak çiz
        for px_x, px_y, tip in patlaticilar:
            ix, iy = int(px_x), int(px_y)
            renk_imlec = PEMBE if tip == "yuz" else CAMGOBEGI
            cv2.circle(katman, (ix, iy), 14, renk_imlec, 2, cv2.LINE_AA)
            cv2.circle(katman, (ix, iy), 5, BEYAZ, -1, cv2.LINE_AA)

        if self.halkalar or patlaticilar:
            parilti(out, katman, guc=1.6, sigma=2.8)

        # Parçacıkları güncelle ve çiz
        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(out)

        # Uçuşan puan yazıları (0.6 sn)
        aktif_yazilar: List[YaziEfekt] = []
        for yz in self.yazilar:
            yas = simdi - yz.t0
            if 0.0 <= yas < yz.sure:
                p = yas / yz.sure
                yy = int(yz.y - 55.0 * p)
                opak = max(0.0, min(1.0, 1.0 - p * p))
                olcek = 1.0 + 0.25 * math.sin(p * math.pi)
                yazi_koy(out, yz.metin, int(yz.x), yy, 40, renk=yz.renk, hiza="orta", olcek=olcek, opak=opak)
                aktif_yazilar.append(yz)
        self.yazilar = aktif_yazilar

        # Bomba kırmızı kenar parlaması (0.15 sn)
        bomba_yas = simdi - self.bomba_flas_t
        if 0.0 <= bomba_yas < 0.15:
            oran = 1.0 - (bomba_yas / 0.15)
            k_kalin = int(28 * oran) + 4
            cv2.rectangle(out, (0, 0), (G - 1, Y - 1), KIRMIZI, k_kalin, cv2.LINE_AA)

        # Arayüz (HUD) ve Durum Ekranları
        if self.durum == "bekle":
            panel(out, G // 2 - 390, Y // 2 - 140, G // 2 + 390, Y // 2 + 135, opak=0.65, kenar=CAMGOBEGI)
            nabiz = 1.0 + 0.06 * math.sin(simdi * 4.5)
            yazi_koy(out, "Balonları Patlat!", G // 2, Y // 2 - 105, 62, renk=SARI, hiza="orta", olcek=nabiz)
            yazi_koy(out, "Parmağın ya da burnunla dokun", G // 2, Y // 2 - 15, 32, renk=BEYAZ, hiza="orta")

            if self.rekor > 0:
                yazi_koy(out, f"Günün Rekoru: {self.rekor}", G // 2, Y // 2 + 45, 28, renk=CAMGOBEGI, hiza="orta")

            if self.algilama_suresi > 0.05:
                oran = min(1.0, self.algilama_suresi / 1.0)
                halka(out, G // 2, Y // 2 + 92, oran, r=24, renk=YESIL, kalinlik=6)
            else:
                baslik(out, self.AD, "Başlamak için elini kaldır veya kameraya yaklaş", renk=CAMGOBEGI)

        elif self.durum == "oyun":
            gecen = max(0.0, min(self.OYUN_SURESI, simdi - self.durum_t0))
            kalan = max(0.0, self.OYUN_SURESI - gecen)
            oran_sure = kalan / self.OYUN_SURESI

            # Üst süre çubuğu
            panel(out, 260, 16, G - 260, 44, opak=0.65, kenar=BEYAZ)
            ic_gen = int((G - 528) * oran_sure)
            cubuk_renk = YESIL if oran_sure > 0.4 else (SARI if oran_sure > 0.2 else KIRMIZI)
            if ic_gen > 0:
                cv2.rectangle(out, (264, 20), (264 + ic_gen, 40), cubuk_renk, -1, cv2.LINE_AA)
            yazi_koy(out, f"{int(math.ceil(kalan))} sn", G // 2, 50, 28, renk=BEYAZ, hiza="orta")

            # Sol üst skor paneli
            panel(out, 24, 16, 235, 145, opak=0.65, kenar=SARI)
            yazi_koy(out, "SKOR", 129, 22, 24, renk=CAMGOBEGI, hiza="orta")
            pop_yas = simdi - self.skor_pop_t
            skor_olcek = 1.0 + 0.28 * math.exp(-pop_yas * 10.0) if 0.0 <= pop_yas < 0.35 else 1.0
            yazi_koy(out, str(self.skor), 129, 46, 76, renk=SARI, hiza="orta", olcek=skor_olcek)

            # Sağ üst rekor / kombo paneli
            panel(out, G - 235, 16, G - 24, 145, opak=0.65, kenar=CAMGOBEGI)
            yazi_koy(out, f"REKOR: {self.rekor}", G - 129, 26, 26, renk=BEYAZ, hiza="orta")
            if self.kombo >= 2:
                k_renk = PEMBE if self.kombo >= 5 else SARI
                yazi_koy(out, f"Seri x{self.kombo}", G - 129, 72, 34, renk=k_renk, hiza="orta")
            else:
                yazi_koy(out, "Hızlı Patlat!", G - 129, 78, 24, renk=CAMGOBEGI, hiza="orta")

            # 5+ Kombo büyük bildirim
            if self.kombo >= 5:
                k_nabiz = 1.0 + 0.08 * math.sin(simdi * 14.0)
                yazi_koy(
                    out,
                    f"KOMBO x{self.kombo}! (2x PUAN)",
                    G // 2,
                    92,
                    44,
                    renk=PEMBE,
                    hiza="orta",
                    olcek=k_nabiz,
                )

        elif self.durum == "sonuc":
            panel(out, G // 2 - 340, Y // 2 - 190, G // 2 + 340, Y // 2 + 190, opak=0.75, kenar=SARI)
            yazi_koy(out, "SÜRE DOLDU!", G // 2, Y // 2 - 165, 52, renk=CAMGOBEGI, hiza="orta")
            yazi_koy(out, str(self.skor), G // 2, Y // 2 - 95, 110, renk=SARI, hiza="orta")
            yazi_koy(out, f"Oturum Rekoru: {self.rekor}", G // 2, Y // 2 + 45, 36, renk=BEYAZ, hiza="orta")
            if self.skor >= self.rekor and self.skor > 0:
                yazi_koy(out, "YENİ REKOR!", G // 2, Y // 2 + 105, 38, renk=PEMBE, hiza="orta")

        # Bomba patladığında kısa ekran sarsıntısı (0.3 sn)
        sars_yas = simdi - self.sarsinti_t
        if 0.0 <= sars_yas < 0.30:
            guc = (1.0 - sars_yas / 0.30) * 10.0
            dx = int(math.sin(simdi * 95.0) * guc)
            dy = int(math.cos(simdi * 110.0) * guc)
            if dx != 0 or dy != 0:
                m = np.float32([[1, 0, dx], [0, 1, dy]])
                out = cv2.warpAffine(out, m, (G, Y), borderMode=cv2.BORDER_REPLICATE)

        return out
