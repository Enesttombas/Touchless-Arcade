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

    ESIK = 0.50

    def __init__(self, ses: Ses):
        self.ses = ses

        # Durum makinesi
        self.durum = "bekle"  # "bekle" | "geri_sayim" | "oyun" | "sonuc"
        self.kaybeden: Optional[str] = None  # None | "sol" | "sag"
        self.sure: float = 0.0  # Düello saniyesi

        # Dahili zamanlayıcılar
        self.durum_zamani: float = 0.0
        self.iki_yuz_sayaci: float = 0.0
        self.son_ding_adim: int = -1
        self.son_zaman: Optional[float] = None

        # Gülme yumuşatma filtreleri (0.0 .. 1.0)
        self.gulme_sol = 0.0
        self.gulme_sag = 0.0

        # Yüz merkez ve yarıçap yumuşatıcıları
        self.sol_merkez: Tuple[float, float] = (G * 0.25, Y * 0.5)
        self.sag_merkez: Tuple[float, float] = (G * 0.75, Y * 0.5)
        self.sol_r: float = 110.0
        self.sag_r: float = 110.0

        # Kışkırtma (provokasyon) emojileri
        self.emojiler = ["😜", "🤪", "🐸", "🙈", "🤡", "🦆"]
        self.emoji_onbellek: Dict[str, np.ndarray] = {
            e: emoji_sprite(e, 220) for e in self.emojiler
        }
        self.emoji_onbellek["tac"] = emoji_sprite("👑", 130)
        self.emoji_onbellek["guldu"] = emoji_sprite("😂", 200)

        self.kiskirtma_emoji = "😜"
        self.kiskirtma_zamani = -10.0
        self.sonraki_kiskirtma = 4.0

        # Konfeti ve kıvılcım efektleri
        self.parcaciklar = Parcaciklar(tavan=250)
        self.konfeti_renkleri = [SARI, CAMGOBEGI, PEMBE, YESIL, KIRMIZI, BEYAZ]
        self.ekran_sarsinti = 0.0

        # Oturum rekoru
        self.rekor = 0.0
        self.rekor_sure = 0.0

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R")):
            self.durum = "bekle"
            self.kaybeden = None
            self.sure = 0.0
            self.iki_yuz_sayaci = 0.0

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
        sol_info: Optional[Tuple[float, float, float]] = None
        sag_info: Optional[Tuple[float, float, float]] = None

        for i, yuz in enumerate(yuzler):
            if not yuz or len(yuz) <= 152:
                continue
            b = blends[i] if i < len(blends) else {}
            bx, by = px(yuz, 1)
            ax, ay = px(yuz, 10)
            cx_pt, cy_pt = px(yuz, 152)
            r = max(70.0, min(190.0, math.hypot(cx_pt - ax, cy_pt - ay) * 0.62))

            norm_x = yuz[1].x
            if norm_x < 0.5:
                if sol_blend is None:
                    sol_blend = b
                    sol_info = (bx, by, r)
            else:
                if sag_blend is None:
                    sag_blend = b
                    sag_info = (bx, by, r)

        return sol_blend, sag_blend, sol_info, sag_info

    def _gulme_skoru(self, b: Optional[Dict[str, float]]) -> float:
        if not b:
            return 0.0
        sol = b.get("mouthSmileLeft", 0.0)
        sag = b.get("mouthSmileRight", 0.0)
        dimple_l = b.get("mouthDimpleLeft", 0.0) * 0.3
        dimple_r = b.get("mouthDimpleRight", 0.0) * 0.3
        return min(1.0, max(0.0, (sol + sag) * 0.5 + (dimple_l + dimple_r) * 0.5))

    def _ciz_elektrik_cizgisi(self, img: np.ndarray, t: float) -> None:
        """Ortada neon dikey titreşen elektrik zikzakı."""
        katman = np.zeros_like(img)
        adims = 20
        dy = Y / adims
        pts = []
        cx = G // 2

        rng = np.random.RandomState(int(t * 35) % 100000)
        for i in range(adims + 1):
            py = int(i * dy)
            if i == 0 or i == adims:
                px_val = cx
            else:
                salinim = math.sin(t * 8.0 + i * 0.5) * 6.0
                gurultu = rng.uniform(-11.0, 11.0)
                px_val = int(cx + salinim + gurultu)
            pts.append((px_val, py))

        for i in range(len(pts) - 1):
            cv2.line(katman, pts[i], pts[i + 1], CAMGOBEGI, 4, cv2.LINE_AA)
            cv2.line(katman, pts[i], pts[i + 1], BEYAZ, 2, cv2.LINE_AA)

        parilti(img, katman, guc=1.5, sigma=3.5)

    def _ciz_yuz_cerceveleri(
        self,
        img: np.ndarray,
        sol_var: bool,
        sag_var: bool,
    ) -> None:
        """Solda CAMGOBEGI, sağda PEMBE neon yüz halkası."""
        katman = np.zeros_like(img)
        if sol_var:
            sx, sy = int(self.sol_merkez[0]), int(self.sol_merkez[1])
            sr = int(self.sol_r)
            cv2.circle(katman, (sx, sy), sr, CAMGOBEGI, 4, cv2.LINE_AA)
            cv2.circle(img, (sx, sy), sr + 4, CAMGOBEGI, 1, cv2.LINE_AA)
        if sag_var:
            dx, dy = int(self.sag_merkez[0]), int(self.sag_merkez[1])
            dr = int(self.sag_r)
            cv2.circle(katman, (dx, dy), dr, PEMBE, 4, cv2.LINE_AA)
            cv2.circle(img, (dx, dy), dr + 4, PEMBE, 1, cv2.LINE_AA)
        if sol_var or sag_var:
            parilti(img, katman, guc=1.4, sigma=3.0)

    def _ciz_kafa_ustu_bar(
        self,
        img: np.ndarray,
        cx: float,
        cy: float,
        r: float,
        gulme: float,
        cerceve_renk: Tuple[int, int, int],
        simdi: float,
    ) -> None:
        """Başın üstünde yatay dolan gülme çubuğu; %70 üstünde SARI->KIRMIZI ve ±3 px titrer."""
        oran = min(1.0, max(0.0, gulme / self.ESIK))
        genislik = 170
        yukseklik = 20

        tx, ty = 0, 0
        if oran >= 0.70:
            tx = int(math.sin(simdi * 55.0) * 3.0)
            ty = int(math.cos(simdi * 63.0) * 3.0)

        x0 = max(16, min(G - genislik - 16, int(cx - genislik // 2 + tx)))
        y0 = max(18, min(Y - yukseklik - 18, int(cy - r - 42 + ty)))
        x1 = x0 + genislik
        y1 = y0 + yukseklik

        panel(img, x0, y0, x1, y1, renk=(15, 15, 24), opak=0.80, kenar=cerceve_renk)

        if oran >= 0.70:
            t_kirmizi = min(1.0, (oran - 0.70) / 0.30)
            b_k = int(SARI[0] * (1.0 - t_kirmizi) + KIRMIZI[0] * t_kirmizi)
            g_k = int(SARI[1] * (1.0 - t_kirmizi) + KIRMIZI[1] * t_kirmizi)
            r_k = int(SARI[2] * (1.0 - t_kirmizi) + KIRMIZI[2] * t_kirmizi)
            bar_renk = (b_k, g_k, r_k)
        else:
            bar_renk = SARI if oran >= 0.35 else cerceve_renk

        dolu = int((genislik - 6) * oran)
        if dolu > 0:
            cv2.rectangle(img, (x0 + 3, y0 + 3), (x0 + 3 + dolu, y1 - 3), bar_renk, -1)

        if oran >= 0.70:
            yazi_koy(img, "GÜLME!", (x0 + x1) // 2, y0 - 28, 22, renk=KIRMIZI, hiza="orta")

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.son_zaman is None:
            self.son_zaman = simdi
        dt = min(max(simdi - self.son_zaman, 0.0), 0.1)
        self.son_zaman = simdi

        # Yüzleri ve gülme oranlarını analiz et
        sol_blend, sag_blend, sol_info, sag_info = self._yuzleri_ayir(algi.yuzler, algi.blend)
        hedef_sol = self._gulme_skoru(sol_blend)
        hedef_sag = self._gulme_skoru(sag_blend)

        # Gülme yumuşatma
        self.gulme_sol += (hedef_sol - self.gulme_sol) * min(1.0, dt * 14.0)
        self.gulme_sag += (hedef_sag - self.gulme_sag) * min(1.0, dt * 14.0)

        # Konum yumuşatma (a ≈ 0.5)
        if sol_info is not None:
            self.sol_merkez = (
                self.sol_merkez[0] * 0.5 + sol_info[0] * 0.5,
                self.sol_merkez[1] * 0.5 + sol_info[1] * 0.5,
            )
            self.sol_r = self.sol_r * 0.5 + sol_info[2] * 0.5
        if sag_info is not None:
            self.sag_merkez = (
                self.sag_merkez[0] * 0.5 + sag_info[0] * 0.5,
                self.sag_merkez[1] * 0.5 + sag_info[1] * 0.5,
            )
            self.sag_r = self.sag_r * 0.5 + sag_info[2] * 0.5

        iki_yuz_var = (sol_blend is not None) and (sag_blend is not None)
        en_az_bir_yuz = (sol_blend is not None) or (sag_blend is not None)

        cikis = kare

        # ----------------------------- DURUM MAKİNESİ
        if self.durum == "bekle":
            self.sure = 0.0
            self.kaybeden = None
            if iki_yuz_var:
                self.iki_yuz_sayaci += dt
                if self.iki_yuz_sayaci >= 0.45:
                    self.durum = "geri_sayim"
                    self.durum_zamani = simdi
                    self.son_ding_adim = 0
                    self.ses.cal("ding", 0.75)
            else:
                self.iki_yuz_sayaci = max(0.0, self.iki_yuz_sayaci - dt * 2.0)

        elif self.durum == "geri_sayim":
            if not iki_yuz_var:
                self.durum = "bekle"
                self.iki_yuz_sayaci = 0.0
            else:
                gecen = simdi - self.durum_zamani
                if gecen < 2.1:
                    adim = int(gecen / 0.7)  # 0 -> "3", 1 -> "2", 2 -> "1"
                    if adim != self.son_ding_adim:
                        self.son_ding_adim = adim
                        self.ses.cal("ding", 0.75)
                elif gecen < 2.5:
                    if self.son_ding_adim != 3:
                        self.son_ding_adim = 3
                        self.ses.cal("woosh", 0.85)
                else:
                    self.durum = "oyun"
                    self.durum_zamani = simdi
                    self.sure = 0.0
                    self.kiskirtma_zamani = -10.0
                    self.sonraki_kiskirtma = 4.0

        elif self.durum == "oyun":
            if not iki_yuz_var:
                self.durum = "bekle"
                self.iki_yuz_sayaci = 0.0
            else:
                self.sure += dt
                sol_patladi = self.gulme_sol >= self.ESIK
                sag_patladi = self.gulme_sag >= self.ESIK

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

                    # Kazanan tarafta yukarıdan 150 renkli konfeti patlat
                    kazanan_x = G // 4 if self.kaybeden == "sag" else (3 * G) // 4
                    for idx in range(6):
                        renk_k = self.konfeti_renkleri[idx % len(self.konfeti_renkleri)]
                        kx = kazanan_x + random.randint(-200, 200)
                        ky = random.randint(25, 110)
                        self.parcaciklar.yay(kx, ky, adet=25, renk=renk_k, hiz=5.0)

                # Her 4 sn'de kışkırtma emojisi
                if self.sure >= self.sonraki_kiskirtma:
                    self.sonraki_kiskirtma += 4.0
                    self.kiskirtma_zamani = simdi
                    self.kiskirtma_emoji = random.choice(self.emojiler)
                    self.ses.cal(random.choice(["bonk", "pop"]), 0.75)

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

        # ----------------------------- GÖRSEL ÇİZİM
        # 1. BEKLE DURUMU
        if self.durum == "bekle":
            cikis = bulanik_karanlik(cikis, 0.45)
            self._ciz_yuz_cerceveleri(cikis, sol_info is not None, sag_info is not None)
            nabiz = 0.95 + 0.05 * math.sin(simdi * 4.0)

            if not en_az_bir_yuz:
                panel(cikis, 230, 210, 1050, 490, renk=(15, 15, 25), opak=0.78, kenar=SARI)
                yazi_koy(cikis, "GÜLME DÜELLOSU", G // 2, 260, 56, renk=SARI, hiza="orta", olcek=nabiz)
                yazi_koy(cikis, "Bakışın, İlk Gülen Kaybeder!", G // 2, 345, 32, renk=BEYAZ, hiza="orta")
                yazi_koy(cikis, "2 Kişi Yan Yana Kameraya Geçin", G // 2, 415, 26, renk=CAMGOBEGI, hiza="orta")
            elif not iki_yuz_var:
                panel(cikis, 250, 230, 1030, 470, renk=(25, 18, 32), opak=0.78, kenar=PEMBE)
                yazi_koy(cikis, "BİR ARKADAŞINI ÇAĞIR!", G // 2, 285, 52, renk=PEMBE, hiza="orta", olcek=nabiz)
                yazi_koy(cikis, "Düello için 2 yüz görünmeli", G // 2, 370, 30, renk=BEYAZ, hiza="orta")
            else:
                panel(cikis, 300, 260, 980, 440, renk=(18, 32, 24), opak=0.82, kenar=YESIL)
                yazi_koy(cikis, "İKİ OYUNCU HAZIR!", G // 2, 310, 48, renk=YESIL, hiza="orta")
                oran = min(1.0, self.iki_yuz_sayaci / 0.45)
                bw = 380
                cv2.rectangle(cikis, (G // 2 - bw // 2, 390), (G // 2 + bw // 2, 406), (40, 40, 40), -1)
                cv2.rectangle(cikis, (G // 2 - bw // 2, 390), (G // 2 - bw // 2 + int(bw * oran), 406), YESIL, -1)

            if self.rekor > 0:
                yazi_koy(cikis, f"Rekor Dayanma: {self.rekor:.1f} sn", G // 2, Y - 50, 26, renk=SARI, hiza="orta")

            return cikis

        # 2. GERİ SAYIM DURUMU (3 - 2 - 1 her biri 0.7 sn, 200->120 px pop, sonra BAŞLA! 0.4 sn)
        if self.durum == "geri_sayim":
            self._ciz_elektrik_cizgisi(cikis, simdi)
            self._ciz_yuz_cerceveleri(cikis, sol_info is not None, sag_info is not None)

            gecen = simdi - self.durum_zamani
            panel(
                cikis,
                G // 2 - 220,
                Y // 2 - 140,
                G // 2 + 220,
                Y // 2 + 140,
                renk=(15, 15, 25),
                opak=0.72,
                kenar=CAMGOBEGI,
            )

            if gecen < 2.1:
                adim = int(gecen / 0.7)
                sayi = 3 - adim
                faz = (gecen - adim * 0.7) / 0.7  # 0.0 -> 1.0
                boyut_px = int(200 - 80 * min(1.0, max(0.0, faz)))
                yazi_koy(
                    cikis,
                    str(sayi),
                    G // 2,
                    Y // 2 - boyut_px // 2 - 10,
                    boyut_px,
                    renk=SARI,
                    hiza="orta",
                )
                yazi_koy(cikis, "CİDDİ KAL!", G // 2, Y // 2 + 82, 28, renk=BEYAZ, hiza="orta")
            else:
                faz = min(1.0, max(0.0, (gecen - 2.1) / 0.4))
                olcek = 0.85 + 0.25 * math.sin(faz * math.pi)
                yazi_koy(
                    cikis,
                    "BAŞLA!",
                    G // 2,
                    Y // 2 - 55,
                    92,
                    renk=YESIL,
                    hiza="orta",
                    olcek=olcek,
                )

            return cikis

        # 3. OYUN DURUMU
        if self.durum == "oyun":
            self._ciz_elektrik_cizgisi(cikis, simdi)
            self._ciz_yuz_cerceveleri(cikis, True, True)

            # Üst sayaç paneli
            panel(cikis, G // 2 - 145, 18, G // 2 + 145, 86, renk=(20, 20, 28), opak=0.82, kenar=SARI)
            yazi_koy(cikis, f"{self.sure:04.1f} sn", G // 2, 28, 46, renk=BEYAZ, hiza="orta")

            # Her oyuncunun başı üstünde yatay gülme çubuğu
            self._ciz_kafa_ustu_bar(
                cikis,
                self.sol_merkez[0],
                self.sol_merkez[1],
                self.sol_r,
                self.gulme_sol,
                CAMGOBEGI,
                simdi,
            )
            self._ciz_kafa_ustu_bar(
                cikis,
                self.sag_merkez[0],
                self.sag_merkez[1],
                self.sag_r,
                self.gulme_sag,
                PEMBE,
                simdi,
            )

            # Kışkırtma emojisi (her 4 sn'de 1.2 sn boyunca: 0->220 px ease-out büyür, sallanır, söner)
            k_gecen = simdi - self.kiskirtma_zamani
            if 0.0 <= k_gecen <= 1.2:
                u = k_gecen / 1.2
                # Ease-out büyüme (ilk %40'ta hızla 220 px'e ulaşır, sonra korunur)
                grow_u = min(1.0, u / 0.45)
                ease_out = 1.0 - (1.0 - grow_u) ** 3
                boyut = max(12, int(220 * ease_out))
                aci = math.sin(k_gecen * 18.0) * 18.0
                opak = 1.0 if u < 0.72 else max(0.0, (1.0 - u) / 0.28)

                spr = self.emoji_onbellek.get(self.kiskirtma_emoji)
                if spr is not None and boyut > 12 and opak > 0.02:
                    bindir_merkez(cikis, spr, G // 2, Y // 2, boyut=boyut, aci=aci, opak=opak)

            return cikis

        # 4. SONUÇ DURUMU (4.5 sn)
        if self.durum == "sonuc":
            gecen = simdi - self.durum_zamani

            if self.kaybeden == "sol":
                kaybeden_kutu = (0, 0, G // 2, Y)
                kazanan_kutu = (G // 2, 0, G, Y)
                kaybeden_pt = self.sol_merkez
                kazanan_pt = self.sag_merkez
                kazanan_r = self.sag_r
                kaybeden_r = self.sol_r
                kazanan_renk = PEMBE
                kazanan_merkez_x = (3 * G) // 4
            else:
                kaybeden_kutu = (G // 2, 0, G, Y)
                kazanan_kutu = (0, 0, G // 2, Y)
                kaybeden_pt = self.sag_merkez
                kazanan_pt = self.sol_merkez
                kazanan_r = self.sol_r
                kaybeden_r = self.sag_r
                kazanan_renk = CAMGOBEGI
                kazanan_merkez_x = G // 4

            # Yarı saydam bölge vurguları
            panel(cikis, kaybeden_kutu[0], kaybeden_kutu[1], kaybeden_kutu[2], kaybeden_kutu[3], renk=(10, 10, 90), opak=0.28)
            panel(cikis, kazanan_kutu[0], kazanan_kutu[1], kazanan_kutu[2], kazanan_kutu[3], renk=(10, 50, 20), opak=0.22)

            # Renkli yüz çerçeveleri
            self._ciz_yuz_cerceveleri(cikis, True, True)

            # Ayırıcı neon çizgi
            cv2.line(cikis, (G // 2, 0), (G // 2, Y), SARI, 3, cv2.LINE_AA)

            # Kazanan yüzünün üstünde 👑 ve "KAZANAN!"
            kx, ky = int(kazanan_pt[0]), int(kazanan_pt[1])
            kr = int(kazanan_r)
            tac_y = max(65, ky - kr - 45)
            tac_spr = self.emoji_onbellek.get("tac")
            if tac_spr is not None:
                bindir_merkez(
                    cikis,
                    tac_spr,
                    kx,
                    tac_y,
                    boyut=120,
                    aci=math.sin(simdi * 4.0) * 8.0,
                )

            kaz_panel_y = min(Y - 120, ky + kr + 15)
            panel(
                cikis,
                kx - 175,
                kaz_panel_y,
                kx + 175,
                kaz_panel_y + 78,
                renk=(15, 28, 20),
                opak=0.88,
                kenar=kazanan_renk,
            )
            yazi_koy(cikis, "KAZANAN!", kx, kaz_panel_y + 10, 48, renk=YESIL, hiza="orta")

            # Kaybeden yüzün üstüne 😂 emoji damgası (0.3 sn pop) ve "GÜLDÜN!"
            lx, ly = int(kaybeden_pt[0]), int(kaybeden_pt[1])
            lr = int(kaybeden_r)
            pop_u = min(1.0, max(0.0, gecen / 0.30))
            # Overshoot pop (0.3 sn içinde büyüyüp yerine oturur)
            pop_olcek = math.sin(pop_u * math.pi * 0.5) * (1.0 + 0.22 * math.sin(pop_u * math.pi))
            damga_boyut = max(20, int(190 * pop_olcek))

            guldu_spr = self.emoji_onbellek.get("guldu")
            if guldu_spr is not None:
                bindir_merkez(cikis, guldu_spr, lx, ly, boyut=damga_boyut, aci=-8.0)

            kay_panel_y = min(Y - 120, ly + lr + 15)
            panel(
                cikis,
                lx - 170,
                kay_panel_y,
                lx + 170,
                kay_panel_y + 78,
                renk=(28, 15, 20),
                opak=0.88,
                kenar=KIRMIZI,
            )
            yazi_koy(cikis, "GÜLDÜN!", lx, kay_panel_y + 10, 48, renk=KIRMIZI, hiza="orta")

            # Kazanan tarafta yukarıdan devam eden konfeti yağmuru
            if gecen < 3.6 and random.random() < 0.45:
                renk_y = random.choice(self.konfeti_renkleri)
                self.parcaciklar.yay(
                    kazanan_merkez_x + random.randint(-190, 190),
                    30,
                    adet=6,
                    renk=renk_y,
                    hiz=3.5,
                )
            self.parcaciklar.guncelle(dt)
            self.parcaciklar.ciz(cikis)

            # Ortada dayanma süresi paneli: "12.4 sn dayandınız"
            panel(
                cikis,
                G // 2 - 260,
                30,
                G // 2 + 260,
                145,
                renk=(15, 15, 26),
                opak=0.90,
                kenar=SARI,
            )
            yazi_koy(
                cikis,
                f"{self.sure:.1f} sn dayandınız",
                G // 2,
                42,
                46,
                renk=SARI,
                hiza="orta",
            )
            yazi_koy(
                cikis,
                f"Rekor: {self.rekor:.1f} sn",
                G // 2,
                102,
                26,
                renk=BEYAZ,
                hiza="orta",
            )

            return cikis

        return cikis
