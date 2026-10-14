from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from oyun_akis import sutun_carpisti

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    KIRMIZI,
    PEMBE,
    SARI,
    Y,
    YESIL,
    Algi,
    Parcaciklar,
    Ses,
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


class Prototip:
    AD = "Uçan Kafa"
    ACIKLAMA = "Ağzını açarak zıpla ve neon sütunların arasından süzül!"
    IHTIYAC = {"yuz", "blend"}
    SIRA = 5

    # Sabitler
    KUS_X = 320
    KUS_BOYUT = 96
    KUS_YARICAP = 36  # Çarpışma yarıçapı (biraz affedici)
    YERCEKIMI = 1500.0
    ZIPLAMA_HIZI = -540.0
    ZEMIN_Y = Y - 45
    TAVAN_Y = 0

    SUTUN_GENISLIK = 86
    SUTUN_ACIKLIK = 240
    SUTUN_ARALIK = 430
    TABAN_HIZ = 260.0

    def __init__(self, ses: Ses):
        self.ses = ses

        # Zorunlu durum öznitelikleri
        self.durum: str = "bekle"
        self.skor: int = 0
        self.rekor: int = 0
        self.kus_y: float = float(Y * 0.62)

        # Fizik ve zamanlama
        self.kus_vy: float = 0.0
        self.kus_aci: float = 0.0
        self.onceki_zaman: Optional[float] = None
        self.durum_zamani: float = 0.0

        # Ağız algılama ve zıplama kontrolü
        self.agiz_acik_mi: bool = False
        self.son_ziplama_zamani: float = -10.0
        self.agiz_orani: float = 0.0

        # Sütunlar: [x, bosluk_merkez_y, gecildi_mi, renk_tipi, parlama_suresi]
        self.sutunlar: List[List[Any]] = []
        self.hiz: float = self.TABAN_HIZ
        self.izgara_kayma: float = 0.0
        self.rng = np.random.RandomState(1337)

        # Efektler ve animasyonlar
        self.parcaciklar = Parcaciklar(160)
        self.sarsinti_suresi: float = 0.0
        self.kirmizi_flas: float = 0.0
        self.skor_pop: float = 0.0
        self.iz_noktalari: List[Tuple[float, float, float]] = []  # (x, y, yas)

        # Görsel önbellekler (Sprite ve maskeler)
        self.yedek_kus = emoji_sprite("🐤", self.KUS_BOYUT)
        self.kral_tac = emoji_sprite("👑", 56)
        self._maske_hazirla()
        self.son_kafa_sprite: Optional[np.ndarray] = None
        self.neon_katman = np.zeros((Y, G, 3), dtype=np.uint8)

    def _maske_hazirla(self) -> None:
        """96x96 dairesel yumuşak maske ve 4px SARI çerçeve katmanı hazırlar."""
        b = self.KUS_BOYUT
        merkez = b / 2.0 - 0.5
        y_ind, x_ind = np.ogrid[:b, :b]
        uzaklik = np.sqrt((x_ind - merkez) ** 2 + (y_ind - merkez) ** 2)

        # Dairesel alfa maskesi (yumuşak kenarlı)
        ic_r = b / 2.0 - 2.0
        alfa = np.clip((ic_r - uzaklik) * 1.5, 0.0, 1.0)
        self.daire_alfa = (alfa * 255).astype(np.uint8)

        # 4px SARI çerçeve maskesi
        cerceve_ic = b / 2.0 - 5.5
        cerceve_dis = b / 2.0 - 1.0
        c_mask = np.clip(1.0 - np.abs(uzaklik - (cerceve_ic + cerceve_dis) / 2.0) / 2.2, 0.0, 1.0)
        self.cerceve_oran = c_mask[:, :, None].astype(np.float32)
        self.sari_piksel = np.full((b, b, 3), SARI, dtype=np.float32)

    def _kafa_sprite_uret(self, kare: np.ndarray, yuz: Any) -> np.ndarray:
        """Canlı yüzün sınır kutusunu kare kırpıp 96px dairesel BGRA sprite yapar."""
        try:
            xs = [pt.x * G for pt in yuz]
            ys = [pt.y * Y for pt in yuz]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            cx = (min_x + max_x) * 0.5
            cy = (min_y + max_y) * 0.5
            boyut = max(max_x - min_x, max_y - min_y, 48.0) * 1.32
            yari = boyut * 0.5

            H, W = kare.shape[:2]
            x0 = int(max(0, min(W - 2, cx - yari)))
            y0 = int(max(0, min(H - 2, cy - yari)))
            x1 = int(max(x0 + 2, min(W, cx + yari)))
            y1 = int(max(y0 + 2, min(H, cy + yari)))

            kirp = kare[y0:y1, x0:x1]
            if kirp.size == 0:
                return self.yedek_kus

            ufak = cv2.resize(kirp, (self.KUS_BOYUT, self.KUS_BOYUT), interpolation=cv2.INTER_LINEAR)
            ufak_f = ufak.astype(np.float32)

            # 4px SARI parlak çerçeveyi uygula
            birlesik = ufak_f * (1.0 - self.cerceve_oran) + self.sari_piksel * self.cerceve_oran
            bgr = birlesik.astype(np.uint8)

            bgra = np.dstack((bgr, self.daire_alfa))
            self.son_kafa_sprite = bgra
            return bgra
        except Exception:
            return self.son_kafa_sprite if self.son_kafa_sprite is not None else self.yedek_kus

    def _agiz_acikligi_bul(self, algi: Algi) -> float:
        """jawOpen blendshape değerini (veya yedek olarak dudak açıklığını) döner."""
        deger = 0.0
        if algi.blend:
            b = algi.blend[0]
            if "jawOpen" in b:
                deger = float(b["jawOpen"])

        # Eğer blend boşsa ama yüz varsa geometrik yedek hesapla
        if deger == 0.0 and algi.yuzler:
            yuz = algi.yuzler[0]
            try:
                ust_y = yuz[13].y
                alt_y = yuz[14].y
                alin_y = yuz[10].y
                cene_y = yuz[152].y
                boy = max(0.05, abs(cene_y - alin_y))
                aciklik = abs(alt_y - ust_y) / boy
                deger = max(0.0, min(1.0, (aciklik - 0.03) * 4.5))
            except Exception:
                pass
        return deger

    def _oyunu_baslat(self, simdi: float) -> None:
        self.durum = "oyun"
        self.durum_zamani = simdi
        self.skor = 0
        self.hiz = self.TABAN_HIZ
        # Ağız açık tutulsa bile 1 saniye boyunca tavana çarpmaması için orta-alt seviyeden başlat
        self.kus_y = float(Y * 0.62)
        self.kus_vy = 0.0
        self.kus_aci = 0.0
        self.iz_noktalari.clear()

        # İlk sütun G + 100'den başlar, peşinden diğerleri gelir
        self.sutunlar.clear()
        for i in range(4):
            sx = float(G + 100 + i * self.SUTUN_ARALIK)
            sy = float(self.rng.randint(190, self.ZEMIN_Y - 190))
            self.sutunlar.append([sx, sy, False, i % 2, 0.0])

        self._zipla(simdi)

    def _zipla(self, simdi: float) -> None:
        self.kus_vy = self.ZIPLAMA_HIZI
        self.son_ziplama_zamani = simdi
        self.ses.cal("woosh", ses=0.65)
        self.parcaciklar.yay(self.KUS_X - 20, self.kus_y + 15, 12, renk=SARI, hiz=3.8)

    def _carpma_tetikle(self, simdi: float) -> None:
        self.durum = "sonuc"
        self.durum_zamani = simdi
        if self.skor > self.rekor:
            self.rekor = self.skor
            self.ses.cal("basari", ses=0.8)
        self.ses.cal("bonk", ses=0.9)
        self.sarsinti_suresi = 0.3
        self.kirmizi_flas = 0.35
        self.parcaciklar.yay(self.KUS_X, self.kus_y, 35, renk=PEMBE, hiz=6.5)
        self.parcaciklar.yay(self.KUS_X, self.kus_y, 20, renk=SARI, hiz=4.5)

    def tus(self, k: int) -> None:
        if k in (ord(" "), 13):
            simdi = self.onceki_zaman if self.onceki_zaman is not None else 1000.0
            if self.durum == "bekle":
                self._oyunu_baslat(simdi)
            elif self.durum == "oyun":
                self._zipla(simdi)
            elif self.durum == "sonuc" and (simdi - self.durum_zamani) > 0.6:
                self.durum = "bekle"
                self.durum_zamani = simdi

    def _izgara_ciz(self, img: np.ndarray, neon: np.ndarray) -> None:
        """Altta kayan paralaks neon ızgara zemin çizer."""
        zy = self.ZEMIN_Y
        panel(img, 0, zy, G, Y, renk=(18, 12, 28), opak=0.82)

        # Ana ufuk çizgisi (parıltılı)
        cv2.line(neon, (0, zy), (G, zy), PEMBE, 3, cv2.LINE_AA)
        cv2.line(img, (0, zy), (G, zy), BEYAZ, 1, cv2.LINE_AA)

        # Yatay perspektif çizgileri
        for dy in (12, 26, 40):
            y_ciz = zy + dy
            if y_ciz < Y:
                cv2.line(img, (0, y_ciz), (G, y_ciz), (90, 40, 120), 1, cv2.LINE_AA)

        # Kayan dikey perspektif çizgileri
        adim = 80
        baslangic = -int(self.izgara_kayma) % adim
        merkez_x = G * 0.5
        for x_ust in range(baslangic - adim, G + adim * 2, adim):
            x_alt = int(merkez_x + (x_ust - merkez_x) * 1.45)
            cv2.line(img, (x_ust, zy), (x_alt, Y), (140, 60, 180), 2, cv2.LINE_AA)
            cv2.line(neon, (x_ust, zy), (x_alt, Y), (90, 30, 120), 1, cv2.LINE_AA)

    def _sutunlari_ciz(self, img: np.ndarray, neon: np.ndarray) -> None:
        """Neon sütun çiftlerini yarı saydam gövde ve parlak kenarlarla çizer."""
        yari_acik = self.SUTUN_ACIKLIK // 2
        w = self.SUTUN_GENISLIK

        for s in self.sutunlar:
            sx = int(s[0])
            if sx + w < -20 or sx > G + 20:
                continue

            merkez_y = int(s[1])
            renk_tip = s[3]
            parlama = float(s[4])

            ana_renk = PEMBE if renk_tip == 0 else CAMGOBEGI
            if parlama > 0.0:
                ana_renk = BEYAZ

            ust_alt_y = max(20, merkez_y - yari_acik)
            alt_ust_y = min(self.ZEMIN_Y - 20, merkez_y + yari_acik)

            # Üst sütun gövdesi
            panel(img, sx, 0, sx + w, ust_alt_y, renk=(26, 20, 38), opak=0.68)
            # Alt sütun gövdesi
            panel(img, sx, alt_ust_y, sx + w, self.ZEMIN_Y, renk=(26, 20, 38), opak=0.68)

            # Sütun başlıkları (kapaklar)
            kapak_h = 22
            panel(img, sx - 6, ust_alt_y - kapak_h, sx + w + 6, ust_alt_y, renk=(40, 30, 55), opak=0.85)
            panel(img, sx - 6, alt_ust_y, sx + w + 6, alt_ust_y + kapak_h, renk=(40, 30, 55), opak=0.85)

            kalinlik = 4 if parlama > 0 else 3

            # Neon çerçeveler
            cv2.rectangle(neon, (sx, -4), (sx + w, ust_alt_y), ana_renk, kalinlik, cv2.LINE_AA)
            cv2.rectangle(neon, (sx - 6, ust_alt_y - kapak_h), (sx + w + 6, ust_alt_y), ana_renk, kalinlik, cv2.LINE_AA)

            cv2.rectangle(neon, (sx, alt_ust_y), (sx + w, self.ZEMIN_Y), ana_renk, kalinlik, cv2.LINE_AA)
            cv2.rectangle(neon, (sx - 6, alt_ust_y), (sx + w + 6, alt_ust_y + kapak_h), ana_renk, cv2.LINE_AA)

            # İç parlak ince çizgiler
            cv2.rectangle(img, (sx, -4), (sx + w, ust_alt_y), BEYAZ, 1, cv2.LINE_AA)
            cv2.rectangle(img, (sx, alt_ust_y), (sx + w, self.ZEMIN_Y), BEYAZ, 1, cv2.LINE_AA)

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.onceki_zaman is None:
            dt = 0.016
            self.durum_zamani = simdi
        else:
            dt = min(max(simdi - self.onceki_zaman, 0.0), 0.1)
        self.onceki_zaman = simdi

        # Ağız açıklığını oku ve yükselen kenar / basılı tutma algıla
        jaw = self._agiz_acikligi_bul(algi)
        self.agiz_orani = self.agiz_orani * 0.5 + jaw * 0.5
        esik_ustunde = jaw > 0.35
        yukselen_kenar = esik_ustunde and not self.agiz_acik_mi
        self.agiz_acik_mi = esik_ustunde

        # Kuş sprite'ını güncelle
        if algi.yuzler:
            kus_sprite = self._kafa_sprite_uret(kare, algi.yuzler[0])
        else:
            kus_sprite = self.yedek_kus

        # Durum makinesi güncellemeleri
        if self.durum == "bekle":
            # Yumuşak salınım
            hedef_y = Y * 0.58 + math.sin(simdi * 3.5) * 16.0
            self.kus_y = self.kus_y * 0.8 + hedef_y * 0.2
            self.kus_vy = 0.0
            self.kus_aci = math.sin(simdi * 3.5) * 8.0
            self.izgara_kayma = (self.izgara_kayma + self.TABAN_HIZ * 0.5 * dt) % 8000.0

            if esik_ustunde:
                self._oyunu_baslat(simdi)

        elif self.durum == "oyun":
            # Zıplama kontrolü: yükselen kenar VEYA açık tutulurken her 0.25 sn'de bir
            if yukselen_kenar or (esik_ustunde and (simdi - self.son_ziplama_zamani) >= 0.25):
                self._zipla(simdi)

            # Fizik
            self.kus_vy += self.YERCEKIMI * dt
            self.kus_vy = min(self.kus_vy, 900.0)
            self.kus_y += self.kus_vy * dt

            # Hıza göre ±25° eğim
            hedef_aci = max(-25.0, min(25.0, -self.kus_vy * 0.045))
            self.kus_aci = self.kus_aci * 0.7 + hedef_aci * 0.3

            # İz noktaları güncelle
            self.iz_noktalari.append((float(self.KUS_X), float(self.kus_y), 0.0))
            yeni_iz = []
            for ix, iy, yas in self.iz_noktalari[-12:]:
                yeni_yas = yas + dt
                if yeni_yas < 0.32:
                    yeni_iz.append((ix - self.hiz * dt, iy, yeni_yas))
            self.iz_noktalari = yeni_iz

            # Sütunları ilerlet ve çarpışma kontrolü yap
            self.izgara_kayma = (self.izgara_kayma + self.hiz * dt) % 8000.0
            yari_acik = self.SUTUN_ACIKLIK * 0.5
            carpti = False

            # Tavan veya taban çarpışması
            if self.kus_y - self.KUS_YARICAP <= self.TAVAN_Y:
                self.kus_y = float(self.TAVAN_Y + self.KUS_YARICAP)
                self.kus_vy = max(self.kus_vy, 0.0)  # tavan öldürmez: stantta çok sert

            elif self.kus_y + self.KUS_YARICAP >= self.ZEMIN_Y:
                self.kus_y = float(self.ZEMIN_Y - self.KUS_YARICAP)
                carpti = True

            for s in self.sutunlar:
                s[0] -= self.hiz * dt
                if s[4] > 0.0:
                    s[4] = max(0.0, s[4] - dt * 3.0)

                sx = s[0]
                merkez_y = s[1]
                gecildi = s[2]

                # Geçiş ve skor kontrolü
                if not gecildi and (sx + self.SUTUN_GENISLIK * 0.5) < self.KUS_X:
                    s[2] = True
                    s[4] = 1.0  # Sütun parlaması
                    self.skor += 1
                    self.hiz *= 1.04
                    self.skor_pop = 1.0
                    self.ses.cal("ding", ses=0.75)
                    self.parcaciklar.yay(self.KUS_X + 20, self.kus_y, 18, renk=CAMGOBEGI, hiz=4.5)

                # Sütun-daire çarpışma testi
                if sutun_carpisti(self.KUS_X, self.kus_y, self.KUS_YARICAP,
                                  sx, self.SUTUN_GENISLIK, merkez_y, yari_acik*2):
                    carpti = True

            # Ekran dışına çıkan sütunu sağa geri taşı
            for s in self.sutunlar:
                if s[0] + self.SUTUN_GENISLIK < -40:
                    en_sag_x = max(s2[0] for s2 in self.sutunlar)
                    s[0] = en_sag_x + self.SUTUN_ARALIK
                    s[1] = float(self.rng.randint(190, self.ZEMIN_Y - 190))
                    s[2] = False
                    s[3] = 1 - s[3]
                    s[4] = 0.0

            if carpti:
                self._carpma_tetikle(simdi)

        elif self.durum == "sonuc":
            # Kuş yere düşer
            if self.kus_y < self.ZEMIN_Y - self.KUS_YARICAP:
                self.kus_vy += self.YERCEKIMI * dt
                self.kus_y = min(float(self.ZEMIN_Y - self.KUS_YARICAP), self.kus_y + self.kus_vy * dt)
                self.kus_aci = max(-25.0, self.kus_aci - 90.0 * dt)

            if (simdi - self.durum_zamani) >= 4.0:
                self.durum = "bekle"
                self.durum_zamani = simdi
                self.sutunlar.clear()

        # Efekt sayaçlarını azalt
        if self.skor_pop > 0.0:
            self.skor_pop = max(0.0, self.skor_pop - dt * 4.0)
        if self.sarsinti_suresi > 0.0:
            self.sarsinti_suresi = max(0.0, self.sarsinti_suresi - dt)
        if self.kirmizi_flas > 0.0:
            self.kirmizi_flas = max(0.0, self.kirmizi_flas - dt)

        # --- ÇİZİM AŞAMASI ---
        # Arka plan: bulanık ve karartılmış kamera görüntüsü
        arka = bulanik_karanlik(kare, 0.62)
        np.copyto(kare, arka)
        self.neon_katman.fill(0)

        # Sütunlar ve ızgara zemin
        if self.durum in ("oyun", "sonuc"):
            self._sutunlari_ciz(kare, self.neon_katman)
        self._izgara_ciz(kare, self.neon_katman)

        # Kuşun arkasındaki neon iz
        for ix, iy, yas in self.iz_noktalari:
            oran = max(0.0, 1.0 - yas / 0.32)
            r = int(6 + 14 * oran)
            cv2.circle(self.neon_katman, (int(ix), int(iy)), r, SARI, -1, cv2.LINE_AA)

        # Kuşun etrafındaki neon halka
        kus_cx, kus_cy = int(self.KUS_X), int(self.kus_y)
        cv2.circle(self.neon_katman, (kus_cx, kus_cy), self.KUS_BOYUT // 2 + 2, SARI, 3, cv2.LINE_AA)

        # Parıltı katmanını uygula
        parilti(kare, self.neon_katman, guc=1.7, sigma=3.2)

        # Kuş sprite'ını çiz
        bindir_merkez(kare, kus_sprite, kus_cx, kus_cy, boyut=self.KUS_BOYUT, aci=self.kus_aci)
        if self.skor > 0 and self.skor >= self.rekor and self.durum == "oyun":
            bindir_merkez(kare, self.kral_tac, kus_cx, kus_cy - 54, boyut=44, aci=self.kus_aci * 0.5)

        # Parçacıklar
        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(kare)

        # Sol alt ağız açıklığı göstergesi
        panel(kare, 24, Y - 130, 230, Y - 60, renk=(18, 18, 28), opak=0.7, kenar=CAMGOBEGI if esik_ustunde else None)
        halka(
            kare,
            60,
            Y - 95,
            min(1.0, self.agiz_orani / 0.5),
            r=22,
            renk=YESIL if esik_ustunde else SARI,
            kalinlik=5,
        )
        yazi_koy(kare, "AĞIZ", 100, Y - 118, 22, renk=CAMGOBEGI if esik_ustunde else BEYAZ, hiza="sol")
        durum_metin = "Zıplıyor!" if esik_ustunde else "Aç -> Zıpla"
        yazi_koy(kare, durum_metin, 100, Y - 90, 18, renk=SARI if esik_ustunde else (190, 190, 200), hiza="sol")

        # --- DURUM ARAYÜZLERİ ---
        if self.durum == "bekle":
            baslik(kare, "UÇAN KAFA", "Kameraya bak, ağzını açarak engellerin arasından uç!", renk=SARI)

            # Ortada davet paneli
            panel(kare, G // 2 - 330, Y // 2 - 90, G // 2 + 330, Y // 2 + 125, renk=(16, 16, 26), opak=0.72, kenar=SARI)
            nabiz = 1.0 + 0.06 * math.sin(simdi * 6.0)
            yazi_koy(kare, "Ağzını aç, uç!", G // 2, Y // 2 - 65, 58, renk=SARI, hiza="orta", olcek=nabiz)

            if algi.yuzler:
                ipucu = "Harika görünüyorsun! Başlamak için ağzını kocaman aç"
                ipucu_renk = CAMGOBEGI
            else:
                ipucu = "Yüzünle uçmak için ekranın karşısına geç"
                ipucu_renk = BEYAZ
            yazi_koy(kare, ipucu, G // 2, Y // 2 + 22, 26, renk=ipucu_renk, hiza="orta")

            if self.rekor > 0:
                yazi_koy(kare, f"Günün Rekoru: {self.rekor}", G // 2, Y // 2 + 70, 28, renk=PEMBE, hiza="orta")

        elif self.durum == "oyun":
            # Üst orta büyük skor göstergesi
            panel(kare, G // 2 - 100, 18, G // 2 + 100, 128, renk=(18, 18, 28), opak=0.6, kenar=CAMGOBEGI)
            olcek = 1.0 + 0.28 * self.skor_pop
            yazi_koy(kare, str(self.skor), G // 2, 18, 92, renk=SARI if self.skor_pop > 0 else BEYAZ, hiza="orta", olcek=olcek)

            if self.rekor > 0:
                panel(kare, G - 210, 22, G - 28, 76, renk=(18, 18, 28), opak=0.6)
                yazi_koy(kare, f"REKOR: {self.rekor}", G - 119, 34, 26, renk=PEMBE, hiza="orta")

        elif self.durum == "sonuc":
            panel(kare, G // 2 - 290, Y // 2 - 175, G // 2 + 290, Y // 2 + 175, renk=(16, 14, 26), opak=0.84, kenar=PEMBE)
            yazi_koy(kare, "ÇARPTIN!", G // 2, Y // 2 - 150, 52, renk=PEMBE, hiza="orta")

            yazi_koy(kare, "SKOR", G // 2, Y // 2 - 80, 26, renk=CAMGOBEGI, hiza="orta")
            yazi_koy(kare, str(self.skor), G // 2, Y // 2 - 52, 96, renk=SARI, hiza="orta")

            rekor_yazi = f"EN İYİ SKOR: {self.rekor}"
            if self.skor > 0 and self.skor >= self.rekor:
                rekor_yazi = f"YENİ REKOR: {self.rekor}!"
            yazi_koy(kare, rekor_yazi, G // 2, Y // 2 + 72, 32, renk=YESIL if self.skor >= self.rekor and self.skor > 0 else BEYAZ, hiza="orta")

            kalan = max(0.0, 4.0 - (simdi - self.durum_zamani))
            yazi_koy(kare, f"Yeni oyun {kalan:.1f} sn...", G // 2, Y // 2 + 125, 22, renk=(180, 180, 200), hiza="orta")

        # Çarpışma anında kırmızı flaş ve 0.3 sn ekran sarsıntısı
        if self.kirmizi_flas > 0.0:
            alfa = min(0.55, self.kirmizi_flas * 1.6)
            kirmizi_katman = np.full_like(kare, KIRMIZI)
            cv2.addWeighted(kare, 1.0 - alfa, kirmizi_katman, alfa, 0, dst=kare)

        if self.sarsinti_suresi > 0.0:
            genlik = int(14 * (self.sarsinti_suresi / 0.3))
            if genlik > 0:
                dx = int(math.sin(simdi * 95.0) * genlik)
                dy = int(math.cos(simdi * 110.0) * genlik)
                M = np.float32([[1, 0, dx], [0, 1, dy]])
                cv2.warpAffine(kare, M, (G, Y), dst=kare, borderMode=cv2.BORDER_REPLICATE)

        return kare
