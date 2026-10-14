"""Gülme Düellosu - İki kişilik kameralı stant deneyimi.

Karşılıklı iki yarışmacı birbirine bakar; ilk gülen kaybeder.
MediaPipe blendshapes üzerinden sol/sağ dudak kıvrımları (smile) ölçülür.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    KIRMIZI,
    PEMBE,
    SARI,
    YESIL,
    Y,
    Algi,
    Parcaciklar,
    Ses,
    bindir_merkez,
    bulanik_karanlik,
    emoji_sprite,
    panel,
    parilti,
    px,
    yazi_koy,
)


class Prototip:
    AD = "Gülme Düellosu"
    ACIKLAMA = "İki kişi ekrana bakar: İlk gülen elenir, ciddi kalan kazanır!"
    IHTIYAC = {"yuz", "blend"}
    SIRA = 7

    def __init__(self, ses: Ses):
        self.ses = ses

        # Durum makinesi
        self.durum = "bekle"  # "bekle" | "geri_sayim" | "oyun" | "sonuc"
        self.kaybeden: Optional[str] = None  # None | "sol" | "sag"
        self.sure: float = 0.0  # Düello saniyesi

        # Dahili zamanlayıcılar
        self.durum_zamani: float = 0.0
        self.iki_yuz_sayaci: float = 0.0
        self.son_ding_sayi: int = -1
        self.son_zaman: Optional[float] = None

        # Gülme yumuşatma filtreleri (0.0 .. 1.0)
        self.gulme_sol = 0.0
        self.gulme_sag = 0.0

        # Yüz merkez ve yarıçap yumuşatmaları
        self.sol_pos = [float(G // 4), float(Y // 2)]
        self.sag_pos = [float(3 * G // 4), float(Y // 2)]
        self.sol_r = 95.0
        self.sag_r = 95.0

        # Kışkırtma emojileri ve önbellek
        self.emojiler = ["😜", "🤪", "🐸", "🙈", "🤡", "🦆"]
        self.emoji_onbellek: Dict[str, np.ndarray] = {
            e: emoji_sprite(e, 240) for e in self.emojiler
        }
        self.emoji_onbellek["tac"] = emoji_sprite("👑", 180)
        self.emoji_onbellek["damga"] = emoji_sprite("😂", 240)

        self.kiskirtma_zamani: float = -10.0
        self.son_kiskirtma_endeks: int = -1
        self.d_emoji = "😜"

        # Konfeti ve kıvılcım efektleri
        self.parcaciklar = Parcaciklar(tavan=300)
        self.konfeti_sayac = 0
        self.ekran_sarsinti = 0.0
        self.konfeti_renkler = [SARI, CAMGOBEGI, PEMBE, YESIL, BEYAZ]

        # Oturum rekoru
        self.rekor = 0.0
        self.rekor_sure = 0.0

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R")):
            self.durum = "bekle"
            self.kaybeden = None
            self.sure = 0.0

    def _yuzleri_ayir(
        self, yuzler: List[Any], blends: List[Dict[str, float]]
    ) -> Tuple[
        Optional[Dict[str, float]],
        Optional[Dict[str, float]],
        Optional[Tuple[float, float, float]],
        Optional[Tuple[float, float, float]],
    ]:
        sol_blend: Optional[Dict[str, float]] = None
        sag_blend: Optional[Dict[str, float]] = None
        sol_bilgi: Optional[Tuple[float, float, float]] = None
        sag_bilgi: Optional[Tuple[float, float, float]] = None

        for i, yuz in enumerate(yuzler):
            if not yuz or len(yuz) <= 152:
                continue
            b = blends[i] if i < len(blends) else {}
            bx, by = px(yuz, 1)
            ax, ay = px(yuz, 10)
            cx, cy = px(yuz, 152)
            r = max(55.0, min(180.0, math.hypot(cx - ax, cy - ay) * 0.58))

            norm_x = yuz[1].x
            if norm_x < 0.5:
                if sol_blend is None:
                    sol_blend = b
                    sol_bilgi = (bx, by, r)
            else:
                if sag_blend is None:
                    sag_blend = b
                    sag_bilgi = (bx, by, r)

        return sol_blend, sag_blend, sol_bilgi, sag_bilgi

    def _gulme_skoru(self, b: Optional[Dict[str, float]]) -> float:
        if not b:
            return 0.0
        sol = b.get("mouthSmileLeft", 0.0)
        sag = b.get("mouthSmileRight", 0.0)
        dimple_l = b.get("mouthDimpleLeft", 0.0) * 0.3
        dimple_r = b.get("mouthDimpleRight", 0.0) * 0.3
        return min(1.0, max(0.0, (sol + sag) * 0.5 + (dimple_l + dimple_r) * 0.5))

    def _ciz_elektrik_cizgisi(
        self, img: np.ndarray, t: float, sol_c: Optional[Tuple[int, int, int]] = None, sag_c: Optional[Tuple[int, int, int]] = None
    ) -> None:
        """Ortada neon dikey titreşen elektrik zikzakı ve oyuncu yüz halkaları."""
        katman = np.zeros_like(img)
        adims = 24
        dy = Y / adims
        pts = []
        cx = G // 2

        rng = np.random.RandomState(int(t * 40) % 100000)
        for i in range(adims + 1):
            py = int(i * dy)
            if i == 0 or i == adims:
                px_val = cx
            else:
                salinim = math.sin(t * 8.0 + i * 0.5) * 8.0
                gurultu = rng.uniform(-14.0, 14.0)
                px_val = int(cx + salinim + gurultu)
            pts.append((px_val, py))

        for i in range(len(pts) - 1):
            cv2.line(katman, pts[i], pts[i + 1], CAMGOBEGI, 4, cv2.LINE_AA)
            cv2.line(katman, pts[i], pts[i + 1], BEYAZ, 2, cv2.LINE_AA)

        if sol_c is not None:
            cv2.circle(katman, (sol_c[0], sol_c[1]), sol_c[2], CAMGOBEGI, 5, cv2.LINE_AA)
            cv2.circle(img, (sol_c[0], sol_c[1]), sol_c[2], BEYAZ, 2, cv2.LINE_AA)
        if sag_c is not None:
            cv2.circle(katman, (sag_c[0], sag_c[1]), sag_c[2], PEMBE, 5, cv2.LINE_AA)
            cv2.circle(img, (sag_c[0], sag_c[1]), sag_c[2], BEYAZ, 2, cv2.LINE_AA)

        parilti(img, katman, guc=1.5, sigma=4.0)

    def _ciz_bas_ustu_bar(
        self, img: np.ndarray, cx: int, cy: int, r: int, oran: float, ana_renk: Tuple[int, int, int]
    ) -> None:
        """Oyuncunun başı üstünde yatay dolan gülme çubuğu (%70 üstü SARI->KIRMIZI ve ±3 px titrer)."""
        oran_k = min(max(oran, 0.0), 1.0)
        bw, bh = 180, 22
        bx = int(max(20, min(G - bw - 20, cx - bw // 2)))
        by = int(max(25, cy - r - 52))

        if oran_k > 0.70:
            bx += random.randint(-3, 3)
            by += random.randint(-3, 3)
            t = (oran_k - 0.70) / 0.30
            bar_renk = (
                int(SARI[0] * (1.0 - t) + KIRMIZI[0] * t),
                int(SARI[1] * (1.0 - t) + KIRMIZI[1] * t),
                int(SARI[2] * (1.0 - t) + KIRMIZI[2] * t),
            )
            kenar_renk = KIRMIZI
        else:
            t = oran_k / 0.70 if oran_k > 0 else 0.0
            bar_renk = (
                int(ana_renk[0] * (1.0 - t) + SARI[0] * t),
                int(ana_renk[1] * (1.0 - t) + SARI[1] * t),
                int(ana_renk[2] * (1.0 - t) + SARI[2] * t),
            )
            kenar_renk = ana_renk

        panel(img, bx, by, bx + bw, by + bh, renk=(15, 15, 24), opak=0.8, kenar=kenar_renk)
        dolu = int((bw - 6) * oran_k)
        if dolu > 0:
            cv2.rectangle(img, (bx + 3, by + 3), (bx + 3 + dolu, by + bh - 3), bar_renk, -1)

        if oran_k > 0.70:
            yazi_koy(img, "SAKİN OL!", bx + bw // 2, by - 28, 22, renk=KIRMIZI, hiza="orta")

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.son_zaman is None:
            self.son_zaman = simdi
        dt = min(max(simdi - self.son_zaman, 0.0), 0.1)
        self.son_zaman = simdi

        # Yüzleri ve gülme oranlarını analiz et
        sol_blend, sag_blend, sol_bilgi, sag_bilgi = self._yuzleri_ayir(algi.yuzler, algi.blend)
        hedef_sol = self._gulme_skoru(sol_blend)
        hedef_sag = self._gulme_skoru(sag_blend)

        # Gülme yumuşatma
        self.gulme_sol += (hedef_sol - self.gulme_sol) * min(1.0, dt * 14.0)
        self.gulme_sag += (hedef_sag - self.gulme_sag) * min(1.0, dt * 14.0)

        # Yüz konumu üstel yumuşatma (a ≈ 0.5)
        if sol_bilgi is not None:
            self.sol_pos[0] += (sol_bilgi[0] - self.sol_pos[0]) * 0.5
            self.sol_pos[1] += (sol_bilgi[1] - self.sol_pos[1]) * 0.5
            self.sol_r += (sol_bilgi[2] - self.sol_r) * 0.4
        if sag_bilgi is not None:
            self.sag_pos[0] += (sag_bilgi[0] - self.sag_pos[0]) * 0.5
            self.sag_pos[1] += (sag_bilgi[1] - self.sag_pos[1]) * 0.5
            self.sag_r += (sag_bilgi[2] - self.sag_r) * 0.4

        iki_yuz_var = (sol_blend is not None) and (sag_blend is not None)
        en_az_bir_yuz = (sol_blend is not None) or (sag_blend is not None)

        cikis = kare
        ESIK = 0.50

        # ----------------------------- DURUM MAKİNESİ
        if self.durum == "bekle":
            self.sure = 0.0
            self.kaybeden = None
            if iki_yuz_var:
                self.iki_yuz_sayaci += dt
                if self.iki_yuz_sayaci >= 0.6:
                    self.durum = "geri_sayim"
                    self.durum_zamani = simdi
                    self.son_ding_sayi = 3
                    self.ses.cal("ding", 0.8)
            else:
                self.iki_yuz_sayaci = max(0.0, self.iki_yuz_sayaci - dt * 2.0)

        elif self.durum == "geri_sayim":
            if not iki_yuz_var:
                self.durum = "bekle"
                self.iki_yuz_sayaci = 0.0
            else:
                gecen = simdi - self.durum_zamani
                if gecen < 2.1:
                    adim = int(gecen / 0.7)  # 0->3, 1->2, 2->1
                    sayi = 3 - adim
                    if sayi != self.son_ding_sayi and sayi >= 1:
                        self.son_ding_sayi = sayi
                        self.ses.cal("ding", 0.8)
                elif gecen < 2.5:
                    if self.son_ding_sayi != 0:
                        self.son_ding_sayi = 0
                        self.ses.cal("woosh", 0.85)
                else:
                    self.durum = "oyun"
                    self.durum_zamani = simdi
                    self.sure = 0.0
                    self.son_kiskirtma_endeks = 0
                    self.kiskirtma_zamani = -10.0

        elif self.durum == "oyun":
            if not iki_yuz_var:
                self.durum = "bekle"
                self.iki_yuz_sayaci = 0.0
            else:
                self.sure += dt

                # Her 4 sn'de ortada rastgele komik emoji kışkırtması
                k_endeks = int(self.sure // 4.0)
                if k_endeks > self.son_kiskirtma_endeks:
                    self.son_kiskirtma_endeks = k_endeks
                    self.kiskirtma_zamani = simdi
                    self.d_emoji = random.choice(self.emojiler)
                    self.ses.cal(random.choice(["pop", "bonk"]), 0.8)

                # Gülme eşiği kontrolü
                sol_patladi = self.gulme_sol >= ESIK
                sag_patladi = self.gulme_sag >= ESIK

                if sol_patladi or sag_patladi:
                    if sol_patladi and sag_patladi:
                        self.kaybeden = "sol" if self.gulme_sol > self.gulme_sag else "sag"
                    elif sol_patladi:
                        self.kaybeden = "sol"
                    else:
                        self.kaybeden = "sag"

                    self.durum = "sonuc"
                    self.durum_zamani = simdi
                    self.ekran_sarsinti = 0.30
                    if self.sure > self.rekor:
                        self.rekor = self.sure
                        self.rekor_sure = self.sure
                    self.ses.cal("bonk", 0.9)
                    self.ses.cal("basari", 0.9)

                    # Kazanan tarafta yukarıdan 150 renkli konfeti başlat
                    self.konfeti_sayac = 0
                    kazanan_x0 = G // 2 + 40 if self.kaybeden == "sol" else 40
                    kazanan_x1 = G - 40 if self.kaybeden == "sol" else G // 2 - 40
                    for _ in range(10):
                        rx = random.randint(kazanan_x0, kazanan_x1)
                        ry = random.randint(20, 140)
                        renk = random.choice(self.konfeti_renkler)
                        self.parcaciklar.yay(rx, ry, adet=9, renk=renk, hiz=5.0)
                        self.konfeti_sayac += 9

        elif self.durum == "sonuc":
            gecen = simdi - self.durum_zamani
            if gecen >= 4.5:
                self.durum = "bekle"
                self.kaybeden = None
                self.iki_yuz_sayaci = 0.0

        # Ekran sarsıntısı (yalnız gülme anında 0.3 sn)
        if self.ekran_sarsinti > 0.0:
            self.ekran_sarsinti = max(0.0, self.ekran_sarsinti - dt)
            oran_s = self.ekran_sarsinti / 0.30
            dx = int(random.uniform(-12, 12) * oran_s)
            dy = int(random.uniform(-12, 12) * oran_s)
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            cikis = cv2.warpAffine(cikis, M, (G, Y), borderMode=cv2.BORDER_REFLECT)

        sol_c = (int(self.sol_pos[0]), int(self.sol_pos[1]), int(self.sol_r)) if sol_bilgi else None
        sag_c = (int(self.sag_pos[0]), int(self.sag_pos[1]), int(self.sag_r)) if sag_bilgi else None

        # ----------------------------- GÖRSEL ÇİZİM
        # 1. BEKLE DURUMU
        if self.durum == "bekle":
            cikis = bulanik_karanlik(cikis, 0.45)
            if sol_c or sag_c:
                self._ciz_elektrik_cizgisi(cikis, simdi, sol_c, sag_c)

            nabiz = 0.95 + 0.05 * math.sin(simdi * 4.0)

            if not en_az_bir_yuz:
                panel(cikis, 240, 220, 1040, 480, renk=(15, 15, 25), opak=0.75, kenar=SARI)
                yazi_koy(cikis, "GÜLME DÜELLOSU", G // 2, 270, 56, renk=SARI, hiza="orta", olcek=nabiz)
                yazi_koy(cikis, "Gülmeden durabilir misin?", G // 2, 345, 30, renk=BEYAZ, hiza="orta")
                yazi_koy(cikis, "2 Kişi Kameranın Karşısına Geçin", G // 2, 410, 24, renk=CAMGOBEGI, hiza="orta")
            elif not iki_yuz_var:
                panel(cikis, 260, 240, 1020, 460, renk=(25, 20, 30), opak=0.75, kenar=PEMBE)
                yazi_koy(cikis, "BİR ARKADAŞINI ÇAĞIR!", G // 2, 290, 50, renk=PEMBE, hiza="orta", olcek=nabiz)
                yazi_koy(cikis, "Düello için 2 kişi gerekiyor", G // 2, 370, 30, renk=BEYAZ, hiza="orta")
            else:
                panel(cikis, 300, 260, 980, 440, renk=(20, 35, 25), opak=0.8, kenar=YESIL)
                yazi_koy(cikis, "HAZIRLANIN...", G // 2, 310, 50, renk=YESIL, hiza="orta")
                oran = min(1.0, self.iki_yuz_sayaci / 0.6)
                bw = 380
                cv2.rectangle(cikis, (G // 2 - bw // 2, 390), (G // 2 + bw // 2, 406), (40, 40, 40), -1)
                cv2.rectangle(cikis, (G // 2 - bw // 2, 390), (G // 2 - bw // 2 + int(bw * oran), 406), YESIL, -1)

            if self.rekor > 0:
                yazi_koy(cikis, f"Günün Rekoru: {self.rekor:.1f} sn", G // 2, Y - 50, 24, renk=SARI, hiza="orta")

            return cikis

        # 2. GERİ SAYIM DURUMU (3-2-1 her biri 0.7 sn, 200->120 px pop, sonra 0.4 sn BAŞLA!)
        if self.durum == "geri_sayim":
            self._ciz_elektrik_cizgisi(cikis, simdi, sol_c, sag_c)
            gecen = simdi - self.durum_zamani

            if gecen < 2.1:
                adim = int(gecen / 0.7)
                sayi = max(1, 3 - adim)
                faz = (gecen - adim * 0.7) / 0.7
                boyut_oran = (200.0 - 80.0 * faz) / 200.0
                panel(cikis, G // 2 - 140, Y // 2 - 140, G // 2 + 140, Y // 2 + 140, renk=(15, 15, 25), opak=0.65, kenar=CAMGOBEGI)
                yazi_koy(cikis, str(sayi), G // 2, Y // 2 - 90, 200, renk=SARI, hiza="orta", olcek=boyut_oran)
            else:
                faz = min(1.0, (gecen - 2.1) / 0.4)
                olcek = 0.85 + 0.25 * math.sin(faz * math.pi)
                panel(cikis, G // 2 - 220, Y // 2 - 90, G // 2 + 220, Y // 2 + 90, renk=(15, 25, 20), opak=0.75, kenar=YESIL)
                yazi_koy(cikis, "BAŞLA!", G // 2, Y // 2 - 45, 92, renk=YESIL, hiza="orta", olcek=olcek)

            return cikis

        # 3. OYUN DURUMU
        if self.durum == "oyun":
            self._ciz_elektrik_cizgisi(cikis, simdi, sol_c, sag_c)

            # Üst sayaç paneli
            panel(cikis, G // 2 - 135, 18, G // 2 + 135, 84, renk=(20, 20, 28), opak=0.8, kenar=SARI)
            yazi_koy(cikis, f"{self.sure:04.1f} sn", G // 2, 26, 46, renk=BEYAZ, hiza="orta")

            # Oyuncuların başı üstünde yatay gülme çubukları
            if sol_c is not None:
                self._ciz_bas_ustu_bar(cikis, sol_c[0], sol_c[1], sol_c[2], self.gulme_sol / ESIK, CAMGOBEGI)
            if sag_c is not None:
                self._ciz_bas_ustu_bar(cikis, sag_c[0], sag_c[1], sag_c[2], self.gulme_sag / ESIK, PEMBE)

            # Kışkırtma emojisi (her 4 sn'de 1.2 sn boyunca 0 -> 220 px ease-out büyür, sallanır, söner)
            k_gecen = simdi - self.kiskirtma_zamani
            if 0.0 <= k_gecen <= 1.2:
                u = k_gecen / 1.2
                if u < 0.35:
                    t_in = u / 0.35
                    ease = 1.0 - (1.0 - t_in) ** 3
                    boyut = int(max(12, 220 * ease))
                    opak = 1.0
                elif u < 0.80:
                    boyut = 220
                    opak = 1.0
                else:
                    t_out = (u - 0.80) / 0.20
                    boyut = int(max(12, 220 * (1.0 - 0.25 * t_out)))
                    opak = max(0.0, 1.0 - t_out)

                aci = math.sin(k_gecen * 16.0) * 14.0
                spr = self.emoji_onbellek.get(self.d_emoji)
                if spr is not None:
                    bindir_merkez(cikis, spr, G // 2, Y // 2, boyut=boyut, aci=aci, opak=opak)

            return cikis

        # 4. SONUÇ DURUMU (4.5 sn)
        if self.durum == "sonuc":
            gecen = simdi - self.durum_zamani
            self._ciz_elektrik_cizgisi(cikis, simdi, sol_c, sag_c)

            if self.kaybeden == "sol":
                kaybeden_pos = (int(self.sol_pos[0]), int(self.sol_pos[1]), int(self.sol_r))
                kazanan_pos = (int(self.sag_pos[0]), int(self.sag_pos[1]), int(self.sag_r))
                kazanan_x0, kazanan_x1 = G // 2 + 40, G - 40
            else:
                kaybeden_pos = (int(self.sag_pos[0]), int(self.sag_pos[1]), int(self.sag_r))
                kazanan_pos = (int(self.sol_pos[0]), int(self.sol_pos[1]), int(self.sol_r))
                kazanan_x0, kazanan_x1 = 40, G // 2 - 40

            # Yukarıdan yağan toplam 150 renkli konfeti tamamlaması
            if self.konfeti_sayac < 150:
                ek = min(12, 150 - self.konfeti_sayac)
                rx = random.randint(kazanan_x0, kazanan_x1)
                ry = random.randint(15, 90)
                self.parcaciklar.yay(rx, ry, adet=ek, renk=random.choice(self.konfeti_renkler), hiz=4.5)
                self.konfeti_sayac += ek

            self.parcaciklar.guncelle(dt)
            self.parcaciklar.ciz(cikis)

            # Kazanan yüzünün üstünde 👑 ve "KAZANAN!"
            k_cx, k_cy, k_r = kazanan_pos
            tac_y = max(75, k_cy - k_r - 35)
            tac = self.emoji_onbellek.get("tac")
            if tac is not None:
                bindir_merkez(cikis, tac, k_cx, tac_y, boyut=125, aci=math.sin(simdi * 4.0) * 8.0)

            kz_y = max(20, tac_y - 95)
            panel(cikis, k_cx - 165, kz_y - 8, k_cx + 165, kz_y + 56, renk=(15, 30, 20), opak=0.85, kenar=YESIL)
            yazi_koy(cikis, "KAZANAN!", k_cx, kz_y, 48, renk=YESIL, hiza="orta")

            # Kaybeden yüzünün üstüne 😂 emoji damgası (0.3 sn pop) ve "GÜLDÜN!"
            l_cx, l_cy, l_r = kaybeden_pos
            pop_t = min(1.0, gecen / 0.3)
            pop_olcek = 1.0 - (1.0 - pop_t) ** 3
            damga_boyut = int(max(24, 190 * (0.3 + 0.7 * pop_olcek)))
            damga = self.emoji_onbellek.get("damga")
            if damga is not None:
                bindir_merkez(cikis, damga, l_cx, l_cy, boyut=damga_boyut, aci=-12.0 * pop_olcek)

            gl_y = max(30, l_cy - l_r - 85)
            panel(cikis, l_cx - 155, gl_y - 8, l_cx + 155, gl_y + 58, renk=(35, 15, 20), opak=0.85, kenar=KIRMIZI)
            yazi_koy(cikis, "GÜLDÜN!", l_cx, gl_y, 50, renk=KIRMIZI, hiza="orta", olcek=0.7 + 0.3 * pop_olcek)

            # Ortada dayanma süresi
            panel(cikis, G // 2 - 260, Y - 155, G // 2 + 260, Y - 45, renk=(15, 15, 26), opak=0.88, kenar=SARI)
            yazi_koy(cikis, f"{self.sure:.1f} sn dayandınız", G // 2, Y - 140, 44, renk=SARI, hiza="orta")
            yazi_koy(cikis, f"Oturum Rekoru: {self.rekor:.1f} sn", G // 2, Y - 82, 24, renk=BEYAZ, hiza="orta")

            return cikis

        return cikis
