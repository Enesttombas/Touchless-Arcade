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

        # Dikkat dağıtıcılar
        self.emojiler = ["😂", "🤡", "🐸", "🙃", "😜", "🗿"]
        self.emoji_onbellek: Dict[str, np.ndarray] = {
            e: emoji_sprite(e, 180) for e in self.emojiler
        }
        self.emoji_onbellek["kupa"] = emoji_sprite("🏆", 180)

        self.komik_sozler = [
            "Ciddi ol!",
            "Sakın gülme...",
            "Gözünü kırpma!",
            "Bıyık altından sırıtma!",
            "Dayan!",
            "Taş kesil!",
            "Gülersen bittin!",
        ]
        self.d_emoji = "😂"
        self.d_soz = "Ciddi ol!"
        self.d_pos = (G // 2, Y // 2)
        self.d_son_degisim = 0.0

        # Konfeti ve kıvılcım efektleri
        self.parcaciklar = Parcaciklar(tavan=350)
        self.ekran_sarsinti = 0.0

        # Oturum rekoru
        self.rekor_sure = 0.0

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R")):
            self.durum = "bekle"
            self.kaybeden = None
            self.sure = 0.0

    def _yuzleri_ayir(
        self, yuzler: List[Any], blends: List[Dict[str, float]]
    ) -> Tuple[Optional[Dict[str, float]], Optional[Dict[str, float]], Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
        sol_blend: Optional[Dict[str, float]] = None
        sag_blend: Optional[Dict[str, float]] = None
        sol_merkez: Optional[Tuple[float, float]] = None
        sag_merkez: Optional[Tuple[float, float]] = None

        for i, yuz in enumerate(yuzler):
            if not yuz or len(yuz) <= 1:
                continue
            b = blends[i] if i < len(blends) else {}
            bx, by = px(yuz, 1)
            norm_x = yuz[1].x
            if norm_x < 0.5:
                if sol_blend is None:
                    sol_blend = b
                    sol_merkez = (bx, by)
            else:
                if sag_blend is None:
                    sag_blend = b
                    sag_merkez = (bx, by)

        return sol_blend, sag_blend, sol_merkez, sag_merkez

    def _gulme_skoru(self, b: Optional[Dict[str, float]]) -> float:
        if not b:
            return 0.0
        sol = b.get("mouthSmileLeft", 0.0)
        sag = b.get("mouthSmileRight", 0.0)
        # Ek olarak ağız açma/sırıtma destekleri
        dimple_l = b.get("mouthDimpleLeft", 0.0) * 0.3
        dimple_r = b.get("mouthDimpleRight", 0.0) * 0.3
        return min(1.0, max(0.0, (sol + sag) * 0.5 + (dimple_l + dimple_r) * 0.5))

    def _ciz_elektrik_cizgisi(self, img: np.ndarray, t: float) -> None:
        """Ortada neon dikey titreşen elektrik zikzakı."""
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

        parilti(img, katman, guc=1.5, sigma=4.0)

    def _ciz_gulme_bar(self, img: np.ndarray, x: int, y: int, genislik: int, yukseklik: int, deger: float, taraf: str) -> None:
        panel(img, x, y, x + genislik, y + yukseklik, renk=(15, 15, 22), opak=0.7, kenar=(80, 80, 100))
        d_kirpik = min(max(deger, 0.0), 1.0)
        dolu_g = int((genislik - 4) * d_kirpik)

        # 0.5 üzeri tehlike (KIRMIZI), altı sakin (CAMGOBEGI/SARI)
        if d_kirpik > 0.5:
            oran = (d_kirpik - 0.5) / 0.5
            r = int(SARI[0] * (1 - oran) + KIRMIZI[0] * oran)
            g = int(SARI[1] * (1 - oran) + KIRMIZI[1] * oran)
            b = int(SARI[2] * (1 - oran) + KIRMIZI[2] * oran)
            bar_renk = (r, g, b)
        else:
            bar_renk = CAMGOBEGI

        if dolu_g > 0:
            if taraf == "sol":
                bx0 = x + 2
                bx1 = bx0 + dolu_g
            else:
                bx1 = x + genislik - 2
                bx0 = bx1 - dolu_g
            cv2.rectangle(img, (bx0, y + 2), (bx1, y + yukseklik - 2), bar_renk, -1)

        # 0.5 eşik çizgisi
        esik_x = x + genislik // 2
        cv2.line(img, (esik_x, y - 4), (esik_x, y + yukseklik + 4), KIRMIZI, 2, cv2.LINE_AA)

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.son_zaman is None:
            self.son_zaman = simdi
        dt = min(max(simdi - self.son_zaman, 0.0), 0.1)
        self.son_zaman = simdi

        # Yüzleri ve gülme oranlarını analiz et
        sol_blend, sag_blend, sol_pt, sag_pt = self._yuzleri_ayir(algi.yuzler, algi.blend)
        hedef_sol = self._gulme_skoru(sol_blend)
        hedef_sag = self._gulme_skoru(sag_blend)

        # Yumuşatma
        self.gulme_sol += (hedef_sol - self.gulme_sol) * min(1.0, dt * 14.0)
        self.gulme_sag += (hedef_sag - self.gulme_sag) * min(1.0, dt * 14.0)

        iki_yuz_var = (sol_blend is not None) and (sag_blend is not None)
        en_az_bir_yuz = (sol_blend is not None) or (sag_blend is not None)

        cikis = kare

        # ----------------------------- DURUM MAKİNESİ
        if self.durum == "bekle":
            self.sure = 0.0
            self.kaybeden = None
            if iki_yuz_var:
                self.iki_yuz_sayaci += dt
                if self.iki_yuz_sayaci >= 1.0:
                    self.durum = "geri_sayim"
                    self.durum_zamani = simdi
                    self.son_ding_sayi = -1
                    self.ses.cal("ding", 0.7)
            else:
                self.iki_yuz_sayaci = max(0.0, self.iki_yuz_sayaci - dt * 2.0)

        elif self.durum == "geri_sayim":
            if not iki_yuz_var:
                self.durum = "bekle"
                self.iki_yuz_sayaci = 0.0
            else:
                gecen = simdi - self.durum_zamani
                kalan = int(math.ceil(3.0 - gecen))
                if kalan != self.son_ding_sayi and kalan > 0:
                    self.son_ding_sayi = kalan
                    self.ses.cal("ding", 0.7)
                if gecen >= 3.0:
                    self.durum = "oyun"
                    self.durum_zamani = simdi
                    self.sure = 0.0
                    self.d_son_degisim = simdi
                    self.ses.cal("woosh", 0.8)

        elif self.durum == "oyun":
            if not iki_yuz_var:
                # Biri kaçarsa başa dön
                self.durum = "bekle"
                self.iki_yuz_sayaci = 0.0
            else:
                self.sure += dt
                # Gülme eşiği 0.5 kontrolü
                sol_patladi = self.gulme_sol >= 0.50
                sag_patladi = self.gulme_sag >= 0.50

                if sol_patladi or sag_patladi:
                    if sol_patladi and sag_patladi:
                        self.kaybeden = "sol" if self.gulme_sol > self.gulme_sag else "sag"
                    elif sol_patladi:
                        self.kaybeden = "sol"
                    else:
                        self.kaybeden = "sag"

                    self.durum = "sonuc"
                    self.durum_zamani = simdi
                    self.ekran_sarsinti = 0.35
                    if self.sure > self.rekor_sure:
                        self.rekor_sure = self.sure
                    self.ses.cal("bonk", 0.9)
                    self.ses.cal("basari", 0.9)

                    # Kazanan tarafa konfeti patlat
                    kazanan_x = 320 if self.kaybeden == "sag" else 960
                    self.parcaciklar.yay(kazanan_x, 360, adet=90, hiz=6.0)

                # Dikkat dağıtıcı güncelle
                if simdi - self.d_son_degisim >= 2.0:
                    self.d_son_degisim = simdi
                    self.d_emoji = random.choice(self.emojiler)
                    self.d_soz = random.choice(self.komik_sozler)
                    rx = random.randint(G // 2 - 120, G // 2 + 120)
                    ry = random.randint(220, 520)
                    self.d_pos = (rx, ry)
                    self.ses.cal("pop", 0.5)

        elif self.durum == "sonuc":
            gecen = simdi - self.durum_zamani
            if gecen >= 5.0:
                self.durum = "bekle"
                self.kaybeden = None
                self.iki_yuz_sayaci = 0.0

        # Ekran sarsıntısı
        if self.ekran_sarsinti > 0.0:
            self.ekran_sarsinti = max(0.0, self.ekran_sarsinti - dt)
            dx = int(random.uniform(-10, 10) * (self.ekran_sarsinti / 0.35))
            dy = int(random.uniform(-10, 10) * (self.ekran_sarsinti / 0.35))
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            cikis = cv2.warpAffine(cikis, M, (G, Y), borderMode=cv2.BORDER_REFLECT)

        # ----------------------------- GÖRSEL ÇİZİM
        # 1. BEKLE DURUMU
        if self.durum == "bekle":
            cikis = bulanik_karanlik(cikis, 0.45)
            nabiz = 0.95 + 0.05 * math.sin(simdi * 4.0)

            if not en_az_bir_yuz:
                panel(cikis, 240, 220, 1040, 480, renk=(15, 15, 25), opak=0.75, kenar=SARI)
                yazi_koy(cikis, "GÜLME DÜELLOSU", G // 2, 270, 56, renk=SARI, hiza="orta", olcek=nabiz)
                yazi_koy(cikis, "Gülmeden durabilir misin?", G // 2, 345, 30, renk=BEYAZ, hiza="orta")
                yazi_koy(cikis, "2 Kişi Kameranın Karşısına Geçin", G // 2, 410, 24, renk=CAMGOBEGI, hiza="orta")
            elif not iki_yuz_var:
                panel(cikis, 260, 240, 1020, 460, renk=(25, 20, 30), opak=0.75, kenar=PEMBE)
                yazi_koy(cikis, "BİR ARKADAŞINI ÇAĞIR!", G // 2, 290, 50, renk=PEMBE, hiza="orta", olcek=nabiz)
                yazi_koy(cikis, "Düello için 2 kişi gerekiyor 👥", G // 2, 370, 30, renk=BEYAZ, hiza="orta")
            else:
                # İki yüz var, 1 sn bekleniyor
                panel(cikis, 300, 260, 980, 440, renk=(20, 35, 25), opak=0.8, kenar=YESIL)
                yazi_koy(cikis, "HAZIRLANIN...", G // 2, 310, 50, renk=YESIL, hiza="orta")
                oran = min(1.0, self.iki_yuz_sayaci / 1.0)
                bw = 380
                cv2.rectangle(cikis, (G // 2 - bw // 2, 390), (G // 2 + bw // 2, 406), (40, 40, 40), -1)
                cv2.rectangle(cikis, (G // 2 - bw // 2, 390), (G // 2 - bw // 2 + int(bw * oran), 406), YESIL, -1)

            if self.rekor_sure > 0:
                yazi_koy(cikis, f"Günün Rekoru: {self.rekor_sure:.1f} sn", G // 2, Y - 50, 24, renk=SARI, hiza="orta")

            return cikis

        # 2. GERİ SAYIM DURUMU
        if self.durum == "geri_sayim":
            self._ciz_elektrik_cizgisi(cikis, simdi)
            gecen = simdi - self.durum_zamani
            kalan_sayi = max(1, int(math.ceil(3.0 - gecen)))
            fraksiyon = (gecen % 1.0)
            olcek = 1.0 + (1.0 - fraksiyon) * 0.4
            opak = 1.0 - fraksiyon * 0.2

            panel(cikis, G // 2 - 120, Y // 2 - 120, G // 2 + 120, Y // 2 + 120, renk=(15, 15, 25), opak=0.6, kenar=CAMGOBEGI)
            yazi_koy(cikis, str(kalan_sayi), G // 2, Y // 2 - 50, 110, renk=SARI, hiza="orta", olcek=olcek, opak=opak)
            yazi_koy(cikis, "GÖZLERİNİ AYIRMA!", G // 2, Y // 2 + 75, 26, renk=BEYAZ, hiza="orta")
            return cikis

        # 3. OYUN DURUMU
        if self.durum == "oyun":
            self._ciz_elektrik_cizgisi(cikis, simdi)

            # Üst sayaç paneli
            panel(cikis, G // 2 - 140, 20, G // 2 + 140, 85, renk=(20, 20, 28), opak=0.8, kenar=CAMGOBEGI)
            yazi_koy(cikis, f"{self.sure:04.1f} s", G // 2, 30, 46, renk=BEYAZ, hiza="orta")

            # Sol Gülme Metresi
            panel(cikis, 50, 24, 450, 100, renk=(20, 20, 28), opak=0.65)
            yazi_koy(cikis, "SOL YARIŞMACI", 60, 32, 22, renk=CAMGOBEGI)
            yazi_koy(cikis, f"%{int(self.gulme_sol * 100)}", 430, 32, 22, renk=BEYAZ, hiza="sag")
            self._ciz_gulme_bar(cikis, 60, 68, 380, 20, self.gulme_sol, "sol")

            # Sağ Gülme Metresi
            panel(cikis, G - 450, 24, G - 50, 100, renk=(20, 20, 28), opak=0.65)
            yazi_koy(cikis, "SAĞ YARIŞMACI", G - 440, 32, 22, renk=CAMGOBEGI)
            yazi_koy(cikis, f"%{int(self.gulme_sag * 100)}", G - 60, 32, 22, renk=BEYAZ, hiza="sag")
            self._ciz_gulme_bar(cikis, G - 440, 68, 380, 20, self.gulme_sag, "sag")

            # Dikkat dağıtıcı komik emoji & yazı
            d_gecen = simdi - self.d_son_degisim
            d_olcek = 1.0 + 0.15 * math.sin(d_gecen * 10.0)
            d_aci = math.sin(d_gecen * 6.0) * 15.0

            spr = self.emoji_onbellek.get(self.d_emoji)
            if spr is not None:
                bindir_merkez(cikis, spr, self.d_pos[0], self.d_pos[1], boyut=140, aci=d_aci, opak=0.95)

            panel(cikis, self.d_pos[0] - 160, self.d_pos[1] + 80, self.d_pos[0] + 160, self.d_pos[1] + 125,
                  renk=(10, 10, 18), opak=0.8, kenar=SARI)
            yazi_koy(cikis, self.d_soz, self.d_pos[0], self.d_pos[1] + 88, 24, renk=SARI, hiza="orta", olcek=d_olcek)

            # Gülme riski olan oyuncunun üstüne uyarı
            if self.gulme_sol > 0.35 and sol_pt:
                yazi_koy(cikis, "GÜLME!", int(sol_pt[0]), int(sol_pt[1]) - 130, 34, renk=KIRMIZI, hiza="orta")
            if self.gulme_sag > 0.35 and sag_pt:
                yazi_koy(cikis, "GÜLME!", int(sag_pt[0]), int(sag_pt[1]) - 130, 34, renk=KIRMIZI, hiza="orta")

            return cikis

        # 4. SONUÇ DURUMU
        if self.durum == "sonuc":
            gecen = simdi - self.durum_zamani
            siren_acik = (int(gecen * 6.0) % 2) == 0

            # Kaybeden & Kazanan bölgeleri
            if self.kaybeden == "sol":
                kaybeden_kutu = (0, 0, G // 2, Y)
                kazanan_kutu = (G // 2, 0, G, Y)
                kaybeden_merkez_x = G // 4
                kazanan_merkez_x = 3 * G // 4
            else:
                kaybeden_kutu = (G // 2, 0, G, Y)
                kazanan_kutu = (0, 0, G // 2, Y)
                kaybeden_merkez_x = 3 * G // 4
                kazanan_merkez_x = G // 4

            # Kaybeden tarafına kırmızı siren yanıp sönmesi
            if siren_acik:
                panel(cikis, kaybeden_kutu[0], kaybeden_kutu[1], kaybeden_kutu[2], kaybeden_kutu[3],
                      renk=(0, 0, 180), opak=0.45)
            else:
                panel(cikis, kaybeden_kutu[0], kaybeden_kutu[1], kaybeden_kutu[2], kaybeden_kutu[3],
                      renk=(0, 0, 80), opak=0.25)

            # Kazanan tarafına hafif yeşil/altın zafer tonu
            panel(cikis, kazanan_kutu[0], kazanan_kutu[1], kazanan_kutu[2], kazanan_kutu[3],
                  renk=(10, 50, 20), opak=0.25)

            # Ayırıcı neon çizgi
            cv2.line(cikis, (G // 2, 0), (G // 2, Y), SARI, 3, cv2.LINE_AA)

            # Kaybeden Yazısı
            panel(cikis, kaybeden_merkez_x - 180, 260, kaybeden_merkez_x + 180, 390,
                  renk=(15, 15, 30), opak=0.85, kenar=KIRMIZI)
            yazi_koy(cikis, "GÜLDÜN!", kaybeden_merkez_x, 280, 60, renk=KIRMIZI, hiza="orta")
            yazi_koy(cikis, "ELENDİ 💀", kaybeden_merkez_x, 345, 28, renk=BEYAZ, hiza="orta")

            # Kazanan Yazısı & Kupa
            kupa = self.emoji_onbellek.get("kupa")
            if kupa is not None:
                bindir_merkez(cikis, kupa, kazanan_merkez_x, 220, boyut=130, aci=math.sin(simdi * 3.0) * 8.0)

            panel(cikis, kazanan_merkez_x - 200, 310, kazanan_merkez_x + 200, 440,
                  renk=(15, 25, 20), opak=0.85, kenar=YESIL)
            yazi_koy(cikis, "KAZANDI!", kazanan_merkez_x, 325, 58, renk=YESIL, hiza="orta")
            yazi_koy(cikis, f"Dayanma: {self.sure:.1f} sn", kazanan_merkez_x, 395, 26, renk=SARI, hiza="orta")

            # Sürekli konfeti güncelle ve çiz
            if random.random() < 0.35:
                self.parcaciklar.yay(kazanan_merkez_x + random.randint(-80, 80), 100, adet=8, hiz=4.0)
            self.parcaciklar.guncelle(dt)
            self.parcaciklar.ciz(cikis)

            # Alt panelde geri sayım
            kalan_sonuc = max(0.0, 5.0 - gecen)
            panel(cikis, G // 2 - 160, Y - 70, G // 2 + 160, Y - 18, renk=(15, 15, 25), opak=0.8)
            yazi_koy(cikis, f"Yeniden başlama: {kalan_sonuc:.1f} s", G // 2, Y - 62, 22, renk=CAMGOBEGI, hiza="orta")

            return cikis

        return cikis
