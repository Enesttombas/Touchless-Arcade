from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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
    el_durumu,
    halka,
    panel,
    parilti,
    px,
    yazi_koy,
)


def _yukle_font(boyut: int):
    adaylar = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "C:\\Windows\\Fonts\\consolab.ttf",
    ]
    for yol in adaylar:
        try:
            return ImageFont.truetype(yol, boyut)
        except Exception:
            pass
    return ImageFont.load_default()


class Prototip:
    AD = "Stil Aynası"
    ACIKLAMA = "Avucunu salla veya aç, görüntü sanata dönüşsün!"
    IHTIYAC = {"el"}
    SIRA = 12

    STILLER: List[str] = [
        "Matrix",
        "ASCII",
        "Piksel",
        "Termal",
        "Çizgi Roman",
        "Neon Kenar",
    ]

    def __init__(self, ses: Ses):
        self.ses = ses
        self.stil_idx: int = 0
        self.stil: str = self.STILLER[0]

        self.onceki_simdi: Optional[float] = None
        self.son_degisim: float = 0.0
        self.son_otomatik: float = 0.0
        self.flas_sure: float = 0.0
        self.yazi_sure: float = 0.0

        # El ve jest takibi
        self.onceki_avuc: bool = False
        self.avuc_gecmisi: List[Tuple[float, float, float]] = []
        self.el_x: float = G / 2
        self.el_y: float = Y / 2
        self.el_gorunur: float = 0.0

        self.parcaciklar = Parcaciklar(160)

        # 16x16 hücre ızgarası (80x45 = 1280x720)
        self.gw = G // 16  # 80
        self.gh = Y // 16  # 45

        self._hazirla_matrix()
        self._hazirla_ascii()
        self._hazirla_neon()

    def _hazirla_matrix(self) -> None:
        semboller = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%&*+=<>?!"
        n = 16
        atlas = np.zeros((n, 16, 16, 3), dtype=np.uint8)
        fnt = _yukle_font(14)

        for i in range(1, n):
            im = Image.new("L", (16, 16), 0)
            dr = ImageDraw.Draw(im)
            ch = semboller[(i * 3) % len(semboller)]
            try:
                bb = dr.textbbox((0, 0), ch, font=fnt)
                w, h = bb[2] - bb[0], bb[3] - bb[1]
                dr.text(((16 - w) / 2 - bb[0], (16 - h) / 2 - bb[1]), ch, fill=255, font=fnt)
            except Exception:
                dr.text((3, 1), ch, fill=255, font=fnt)

            arr = np.array(im, dtype=np.float32) / 255.0
            seviye = 0.25 + 0.75 * (i / (n - 1))

            if i == n - 1:
                # Parlak beyazımsı-yeşil "kafa" karakteri
                b = np.clip(arr * 220, 0, 255)
                g = np.clip(arr * 255, 0, 255)
                r = np.clip(arr * 220, 0, 255)
            else:
                b = np.clip(arr * 45 * seviye, 0, 255)
                g = np.clip(arr * 255 * seviye, 0, 255)
                r = np.clip(arr * 30 * seviye, 0, 255)

            atlas[i, :, :, 0] = b.astype(np.uint8)
            atlas[i, :, :, 1] = g.astype(np.uint8)
            atlas[i, :, :, 2] = r.astype(np.uint8)

        # Arka plan koyu yeşilimsi siyah
        atlas[0, :, :] = (4, 12, 4)
        self.matrix_atlas = atlas

        rng = np.random.RandomState(1337)
        self.matrix_y = rng.uniform(0, self.gh, size=(1, self.gw)).astype(np.float32)
        self.matrix_hiz = rng.uniform(12.0, 28.0, size=(1, self.gw)).astype(np.float32)
        self.matrix_satir = np.arange(self.gh, dtype=np.float32)[:, None]

    def _hazirla_ascii(self) -> None:
        karakterler = " .:-=+*#%@"
        n = len(karakterler)
        atlas = np.zeros((n, 16, 16, 3), dtype=np.uint8)
        fnt = _yukle_font(15)

        for i, ch in enumerate(karakterler):
            im = Image.new("L", (16, 16), 0)
            dr = ImageDraw.Draw(im)
            if ch != " ":
                try:
                    bb = dr.textbbox((0, 0), ch, font=fnt)
                    w, h = bb[2] - bb[0], bb[3] - bb[1]
                    dr.text(((16 - w) / 2 - bb[0], (16 - h) / 2 - bb[1]), ch, fill=255, font=fnt)
                except Exception:
                    dr.text((3, 1), ch, fill=255, font=fnt)

            arr = np.array(im, dtype=np.float32) / 255.0
            t = i / max(1, n - 1)
            # Koyu lacivert zeminde camgöbeği -> sarı -> beyaz gradyanlı karakterler
            b_val = 18 + arr * (255 * (0.5 + 0.5 * (1.0 - t * 0.4)))
            g_val = 14 + arr * (245 * (0.35 + 0.65 * t))
            r_val = 22 + arr * (255 * (t ** 1.1))

            atlas[i, :, :, 0] = np.clip(b_val, 0, 255).astype(np.uint8)
            atlas[i, :, :, 1] = np.clip(g_val, 0, 255).astype(np.uint8)
            atlas[i, :, :, 2] = np.clip(r_val, 0, 255).astype(np.uint8)

        self.ascii_atlas = atlas

    def _hazirla_neon(self) -> None:
        # Yarım çözünürlükte (640x360) açı haritası
        yy, xx = np.mgrid[0 : Y // 2, 0 : G // 2].astype(np.float32)
        self.neon_faz = (xx * 0.015 + yy * 0.015)

    def _sonraki_stil(self, simdi: float, merkez: Optional[Tuple[float, float]] = None) -> None:
        self.stil_idx = (self.stil_idx + 1) % len(self.STILLER)
        self.stil = self.STILLER[self.stil_idx]
        self.son_degisim = simdi
        self.son_otomatik = simdi
        self.flas_sure = 0.35
        self.yazi_sure = 0.90
        self.ses.cal("woosh", ses=0.8)

        cx, cy = merkez if merkez is not None else (G * 0.5, Y * 0.5)
        cx = max(40.0, min(G - 40.0, cx))
        cy = max(40.0, min(Y - 40.0, cy))
        self.parcaciklar.yay(cx, cy, 36, renk=CAMGOBEGI, hiz=6.5)
        self.parcaciklar.yay(cx, cy, 24, renk=SARI, hiz=4.5)

    def tus(self, k: int) -> None:
        if k == 32 or k == ord(" "):
            zaman = self.onceki_simdi if self.onceki_simdi is not None else 1000.0
            self._sonraki_stil(zaman)
        elif ord("1") <= k <= ord("6"):
            idx = k - ord("1")
            if 0 <= idx < len(self.STILLER):
                zaman = self.onceki_simdi if self.onceki_simdi is not None else 1000.0
                self.stil_idx = idx - 1
                self._sonraki_stil(zaman)

    # ---------------------------------------------------------------- Stil Efektleri
    def _efekt_matrix(self, kare: np.ndarray, dt: float) -> np.ndarray:
        kucuk = cv2.resize(kare, (self.gw, self.gh), interpolation=cv2.INTER_AREA)
        gri = cv2.cvtColor(kucuk, cv2.COLOR_BGR2GRAY)

        self.matrix_y = (self.matrix_y + self.matrix_hiz * dt) % self.gh
        fark = (self.matrix_y - self.matrix_satir) % self.gh

        # Akan yağmur kuyruğu + kamera parlaklığı
        yagmur = np.clip(1.0 - fark / 14.0, 0.0, 1.0)
        kafa = fark < 1.15

        parlaklik = gri.astype(np.float32) * (1.0 / 255.0)
        kombine = np.clip(parlaklik * 0.80 + yagmur * 0.55, 0.0, 1.0)

        indeks = (kombine * 14.0).astype(np.int32)
        indeks[kafa & (parlaklik > 0.12)] = 15

        hucreler = self.matrix_atlas[indeks]  # (45, 80, 16, 16, 3)
        cikti = hucreler.transpose(0, 2, 1, 3, 4).reshape(Y, G, 3)
        return cikti.copy()

    def _efekt_ascii(self, kare: np.ndarray) -> np.ndarray:
        kucuk = cv2.resize(kare, (self.gw, self.gh), interpolation=cv2.INTER_AREA)
        gri = cv2.cvtColor(kucuk, cv2.COLOR_BGR2GRAY)

        # Kontrastı hafif güçlendir
        norm = np.clip((gri.astype(np.int32) - 16) * 280 // 255, 0, 255)
        indeks = (norm * (len(self.ascii_atlas) - 1)) // 255

        hucreler = self.ascii_atlas[indeks]  # (45, 80, 16, 16, 3)
        cikti = hucreler.transpose(0, 2, 1, 3, 4).reshape(Y, G, 3)
        return cikti.copy()

    def _efekt_piksel(self, kare: np.ndarray) -> np.ndarray:
        # 24 px mozaik + 16 renk benzeri keskin palet kuantizasyonu
        pw = max(1, G // 24)
        ph = max(1, Y // 24)
        kucuk = cv2.resize(kare, (pw, ph), interpolation=cv2.INTER_AREA)

        # Parlaklık ve doygunluk artışı + BGR kuantizasyonu (her kanalda 2-3 seviye -> ~16 canlı ton)
        q = (kucuk // 85) * 85 + 42
        # En baskın kanalı öne çıkararak retro 16-renk palet hissi ver
        ust = q.max(axis=2, keepdims=True)
        paletli = np.where(q >= ust - 30, np.minimum(255, q + 35), q // 2).astype(np.uint8)

        mozaik = cv2.resize(paletli, (G, Y), interpolation=cv2.INTER_NEAREST)
        # Hafif piksel ızgara çizgisi
        mozaik[::24, :, :] = (mozaik[::24, :, :] * 0.75).astype(np.uint8)
        mozaik[:, ::24, :] = (mozaik[:, ::24, :] * 0.75).astype(np.uint8)
        return mozaik

    def _efekt_termal(self, kare: np.ndarray) -> np.ndarray:
        kucuk = cv2.resize(kare, (G // 2, Y // 2), interpolation=cv2.INTER_AREA)
        gri = cv2.cvtColor(kucuk, cv2.COLOR_BGR2GRAY)
        bulanik = cv2.GaussianBlur(gri, (9, 9), 2.0)
        renkli = cv2.applyColorMap(bulanik, cv2.COLORMAP_INFERNO)
        return cv2.resize(renkli, (G, Y), interpolation=cv2.INTER_LINEAR)

    def _efekt_cizgi_roman(self, kare: np.ndarray) -> np.ndarray:
        cw, ch = G // 4, Y // 4
        c_kucuk = cv2.resize(kare, (cw, ch), interpolation=cv2.INTER_AREA)
        yumusak = cv2.bilateralFilter(c_kucuk, d=5, sigmaColor=65, sigmaSpace=65)

        # 6 seviye renk posterize
        seviye = 256 // 6
        poster_kucuk = ((yumusak // seviye) * seviye + seviye // 2).astype(np.uint8)
        poster = cv2.resize(poster_kucuk, (G, Y), interpolation=cv2.INTER_LINEAR)

        # Yarım çözünürlükte kalın siyah Canny kenarları
        yw, yh = G // 2, Y // 2
        y_kucuk = cv2.resize(kare, (yw, yh), interpolation=cv2.INTER_AREA)
        gri = cv2.cvtColor(y_kucuk, cv2.COLOR_BGR2GRAY)
        gri_b = cv2.GaussianBlur(gri, (5, 5), 1.2)
        kenar = cv2.Canny(gri_b, 55, 135)
        cekirdek = np.ones((3, 3), dtype=np.uint8)
        kalin = cv2.dilate(kenar, cekirdek, iterations=1)
        kalin_tam = cv2.resize(kalin, (G, Y), interpolation=cv2.INTER_NEAREST)

        poster[kalin_tam > 0] = (15, 15, 22)
        return poster

    def _efekt_neon_kenar(self, kare: np.ndarray, simdi: float) -> np.ndarray:
        yw, yh = G // 2, Y // 2
        kucuk = cv2.resize(kare, (yw, yh), interpolation=cv2.INTER_AREA)
        gri = cv2.cvtColor(kucuk, cv2.COLOR_BGR2GRAY)
        gri_b = cv2.GaussianBlur(gri, (5, 5), 1.2)
        kenar = cv2.Canny(gri_b, 50, 130)

        # Renk döngüsü (yarım çözünürlükte hızlı sinüs tabanlı RGB)
        faz = self.neon_faz + simdi * 3.2
        b = ((np.sin(faz) * 0.5 + 0.5) * 255.0).astype(np.uint8)
        g = ((np.sin(faz + 2.094) * 0.5 + 0.5) * 255.0).astype(np.uint8)
        r = ((np.sin(faz + 4.188) * 0.5 + 0.5) * 255.0).astype(np.uint8)

        renkli_kucuk = cv2.merge([b, g, r])
        maske = kenar > 0
        katman_kucuk = np.zeros_like(renkli_kucuk)
        katman_kucuk[maske] = renkli_kucuk[maske]

        katman = cv2.resize(katman_kucuk, (G, Y), interpolation=cv2.INTER_LINEAR)
        # Siyahmsı koyu zemin (silüet çok hafif belli olsun)
        zemin = (kare >> 4).astype(np.uint8)
        parilti(zemin, katman, guc=2.2, sigma=3.2)
        return zemin

    # ---------------------------------------------------------------- Algı & Geçiş Kontrolü
    def _kontrol_el(self, algi: Algi, simdi: float, dt: float) -> bool:
        eller = algi.eller or []
        jestler = algi.jestler or []

        if not eller:
            self.onceki_avuc = False
            self.avuc_gecmisi.clear()
            self.el_gorunur = max(0.0, self.el_gorunur - dt * 4.0)
            return False

        el = eller[0]
        ax, ay = px(el, 9)  # Avuç merkezi
        ax = max(0.0, min(float(G), ax))
        ay = max(0.0, min(float(Y), ay))

        # Konumu üstel yumuşat
        a = 0.55
        self.el_x = self.el_x * (1.0 - a) + ax * a
        self.el_y = self.el_y * (1.0 - a) + ay * a
        self.el_gorunur = min(1.0, self.el_gorunur + dt * 6.0)

        # Avuç açık mı? (GestureRecognizer VEYA el_durumu)
        avuc_acik = False
        for i, e in enumerate(eller):
            j = jestler[i] if i < len(jestler) else None
            if j == "Open_Palm" or el_durumu(e) == "sil":
                avuc_acik = True
                break

        # Geçmişi güncelle (son 0.30 sn)
        self.avuc_gecmisi.append((simdi, ax, ay))
        alt_sinir = simdi - 0.30
        while self.avuc_gecmisi and self.avuc_gecmisi[0][0] < alt_sinir:
            self.avuc_gecmisi.pop(0)

        soguma_ok = (simdi - self.son_degisim) > 1.2  # el sallamaya devam edince stil art arda çevrilmesin

        # 1) Open_Palm yükselen kenarı
        yukselen_avuc = avuc_acik and not self.onceki_avuc
        self.onceki_avuc = avuc_acik

        # 2) 0.3 sn içinde yatayda 250+ px hareket
        yatay_sallama = False
        if len(self.avuc_gecmisi) >= 2:
            xs = [k[1] for k in self.avuc_gecmisi]
            if (max(xs) - min(xs)) >= 250.0:
                yatay_sallama = True

        if soguma_ok and (yukselen_avuc or yatay_sallama):
            self.avuc_gecmisi.clear()
            self._sonraki_stil(simdi, merkez=(self.el_x, self.el_y))
            return True

        return True

    # ---------------------------------------------------------------- Ana Döngü
    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.onceki_simdi is None:
            dt = 0.016
            self.son_degisim = simdi
            self.son_otomatik = simdi
            self.yazi_sure = 0.90
        else:
            dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        el_var = self._kontrol_el(algi, simdi, dt)

        # El yokken 10 sn'de bir otomatik geçiş
        if not el_var and (simdi - self.son_otomatik) >= 10.0:
            self._sonraki_stil(simdi)

        # Seçili sanat stilini uygula
        s = self.stil
        if s == "Matrix":
            cikti = self._efekt_matrix(kare, dt)
        elif s == "ASCII":
            cikti = self._efekt_ascii(kare)
        elif s == "Piksel":
            cikti = self._efekt_piksel(kare)
        elif s == "Termal":
            cikti = self._efekt_termal(kare)
        elif s == "Çizgi Roman":
            cikti = self._efekt_cizgi_roman(kare)
        else:
            cikti = self._efekt_neon_kenar(kare, simdi)

        # El imleci (neon halka + hafif iz)
        if self.el_gorunur > 0.05:
            ex, ey = int(self.el_x), int(self.el_y)
            r = int(26 + 6 * math.sin(simdi * 6.0))
            cv2.circle(cikti, (ex, ey), r, CAMGOBEGI, 3, cv2.LINE_AA)
            cv2.circle(cikti, (ex, ey), 6, BEYAZ, -1, cv2.LINE_AA)

        # Parçacıklar
        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(cikti)

        # Kimse yokken (el algılanmıyorken) davetkâr nabız göstergesi
        if not el_var:
            nabiz = 0.94 + 0.06 * math.sin(simdi * 3.5)
            panel(cikti, G // 2 - 330, 22, G // 2 + 330, 118, renk=(16, 16, 26), opak=0.68, kenar=CAMGOBEGI)
            yazi_koy(
                cikti,
                "ELİNİ SALLA, SANATA DÖNÜŞ!",
                G // 2,
                34,
                42,
                renk=SARI,
                hiza="orta",
                olcek=nabiz,
            )
            yazi_koy(
                cikti,
                f"Aktif Stil: {self.stil}  •  6 Canlı Filtre",
                G // 2,
                84,
                22,
                renk=BEYAZ,
                hiza="orta",
            )

        # Alt sol bilgi paneli (zorunlu)
        panel(cikti, 28, Y - 132, 540, Y - 24, renk=(18, 18, 28), opak=0.78, kenar=SARI)
        yazi_koy(cikti, self.stil, 50, Y - 120, 44, renk=SARI, hiza="sol")
        yazi_koy(cikti, "Avucunu salla: stil değiştir", 50, Y - 64, 24, renk=BEYAZ, hiza="sol")

        # Stil sıra noktaları (alt sağda şık gösterge)
        for i, ad in enumerate(self.STILLER):
            nx = G - 220 + i * 32
            ny = Y - 52
            aktif = i == self.stil_idx
            renk_nokta = SARI if aktif else (110, 110, 130)
            yaricap = 9 if aktif else 5
            cv2.circle(cikti, (nx, ny), yaricap, renk_nokta, -1, cv2.LINE_AA)

        # Yeni stil adının dev yazısı solarak
        if self.yazi_sure > 0.0:
            self.yazi_sure = max(0.0, self.yazi_sure - dt)
            oran = min(1.0, self.yazi_sure / 0.75)
            olcek = 1.0 + (1.0 - oran) * 0.18
            yazi_koy(
                cikti,
                self.stil.upper(),
                G // 2,
                Y // 2 - 48,
                92,
                renk=BEYAZ,
                hiza="orta",
                olcek=olcek,
                opak=oran,
            )

        # 0.35 sn beyaz flaş
        if self.flas_sure > 0.0:
            self.flas_sure = max(0.0, self.flas_sure - dt)
            alfa = (self.flas_sure / 0.35) * 0.65
            if alfa > 0.01:
                beyaz = np.full_like(cikti, 255)
                cv2.addWeighted(cikti, 1.0 - alfa, beyaz, alfa, 0, dst=cikti)

        return cikti
