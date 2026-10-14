"""Kafa Topu - Alın ve kafa ile top sektirme rekabeti."""
from __future__ import annotations

import math
import cv2
import numpy as np

from cekirdek import (
    G,
    Y,
    BEYAZ,
    CAMGOBEGI,
    PEMBE,
    SARI,
    YESIL,
    KIRMIZI,
    Parcaciklar,
    Ses,
    baslik,
    bindir_merkez,
    bulanik_karanlik,
    emoji_sprite,
    panel,
    parilti,
    px,
    yazi_koy,
)


class _Top:
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.aci = 0.0
        self.r = 45.0
        self.ezilme_t = 0.0


class Prototip:
    AD = "Kafa Topu"
    ACIKLAMA = "Kafanla topu sektir!"
    IHTIYAC = {"yuz"}
    SIRA = 4

    def __init__(self, ses: Ses):
        self.ses = ses
        self.parcaciklar = Parcaciklar(tavan=160)
        self.top_sprite = emoji_sprite("⚽", 90)

        self.durum = "bekle"  # "bekle" | "oyun" | "sonuc"
        self.skor = 0
        self.rekor = 0

        self.top = _Top(G / 2, 80)
        self.kuyruk: list[tuple[float, float]] = []

        self.onceki_simdi = 0.0
        self.yuz_goruldu_sure = 0.0
        self.sonuc_baslangic = 0.0

        # Animasyon & efektler
        self.skor_pop = 0.0
        self.super_yazi_t = 0.0
        self.shake_t = 0.0
        self.shake_guc = 0.0

        # Kafa yumuşatma
        self.kafa_x = G / 2
        self.kafa_y = Y / 2
        self.kafa_r = 70.0
        self.kafa_var = False

    def _en_buyuk_yuz(self, yuzler):
        if not yuzler:
            return None
        en_iyi = None
        en_alan = -1.0
        for yuz in yuzler:
            try:
                p33 = px(yuz, 33)
                p263 = px(yuz, 263)
                p10 = px(yuz, 10)
                p152 = px(yuz, 152)
                gen = abs(p263[0] - p33[0])
                yuk = abs(p152[1] - p10[1])
                alan = gen * yuk
                if alan > en_alan:
                    en_alan = alan
                    en_iyi = yuz
            except Exception:
                continue
        return en_iyi

    def _oyun_baslat(self, baslangic_x: float):
        self.durum = "oyun"
        self.skor = 0
        bx = max(100.0, min(float(G - 100), float(baslangic_x)))
        self.top = _Top(bx, 80.0)
        self.kuyruk.clear()
        self.skor_pop = 0.0
        self.super_yazi_t = 0.0
        self.ses.cal("pop", 0.8)

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        if self.onceki_simdi <= 0.0:
            dt = 0.033
        else:
            dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        # En büyük yüzü tespit et
        yuz = self._en_buyuk_yuz(algi.yuzler)
        if yuz is not None:
            try:
                p10 = px(yuz, 10)
                p1 = px(yuz, 1)
                p33 = px(yuz, 33)
                p263 = px(yuz, 263)

                kx = (p10[0] + p1[0]) * 0.5
                ky = (p10[1] + p1[1]) * 0.5
                dx = p263[0] - p33[0]
                dy = p263[1] - p33[1]
                goz_mesafe = math.hypot(dx, dy)
                kr = max(35.0, min(180.0, goz_mesafe * 0.6))

                if not self.kafa_var:
                    self.kafa_x, self.kafa_y, self.kafa_r = kx, ky, kr
                    self.kafa_var = True
                else:
                    self.kafa_x += (kx - self.kafa_x) * 0.55
                    self.kafa_y += (ky - self.kafa_y) * 0.55
                    self.kafa_r += (kr - self.kafa_r) * 0.55
            except Exception:
                self.kafa_var = False
        else:
            self.kafa_var = False

        # Zamanlayıcılar
        if self.skor_pop > 0.0:
            self.skor_pop = max(0.0, self.skor_pop - dt * 3.5)
        if self.super_yazi_t > 0.0:
            self.super_yazi_t = max(0.0, self.super_yazi_t - dt)
        if self.shake_t > 0.0:
            self.shake_t = max(0.0, self.shake_t - dt)

        # ---------------- DURUM MAKİNESİ ----------------
        if self.durum == "bekle":
            if self.kafa_var:
                self.yuz_goruldu_sure += dt
                if self.yuz_goruldu_sure >= 0.5:
                    self._oyun_baslat(self.kafa_x)
            else:
                self.yuz_goruldu_sure = max(0.0, self.yuz_goruldu_sure - dt * 2.0)

        elif self.durum == "oyun":
            top = self.top
            # Fizik simülasyonu
            top.vy += 1500.0 * dt
            top.x += top.vx * dt
            top.y += top.vy * dt
            top.aci = (top.aci + top.vx * dt * 0.6) % 360.0

            if top.ezilme_t > 0.0:
                top.ezilme_t = max(0.0, top.ezilme_t - dt)

            # Duvarlardan sekme
            if top.x < top.r:
                top.x = top.r
                top.vx = -top.vx * 0.8
                self.ses.cal("hihat", 0.4)
            elif top.x > G - top.r:
                top.x = G - top.r
                top.vx = -top.vx * 0.8
                self.ses.cal("hihat", 0.4)

            # Kuyruk izi kaydı
            self.kuyruk.append((top.x, top.y))
            if len(self.kuyruk) > 10:
                self.kuyruk.pop(0)

            # Kafa çarpışması: Yalnız top AŞAĞI giderken
            if self.kafa_var and top.vy > 0:
                cdx = top.x - self.kafa_x
                cdy = top.y - self.kafa_y
                mesafe = math.hypot(cdx, cdy)
                if mesafe < (top.r + self.kafa_r):
                    top.vy = -min(1000.0 + 15.0 * self.skor, 1350.0)
                    sapma = (top.x - self.kafa_x) * 4.0
                    rastgele_vx = float(np.random.uniform(-60.0, 60.0))
                    top.vx = np.clip(top.vx * 0.35 + sapma + rastgele_vx, -800.0, 800.0)

                    self.skor += 1
                    top.ezilme_t = 0.15
                    self.skor_pop = 1.0

                    self.ses.cal("bonk", 0.85)
                    self.parcaciklar.yay(int(top.x), int(top.y + top.r * 0.5), adet=20, renk=SARI, hiz=5.5)

                    if self.skor in (10, 20, 30, 50):
                        self.super_yazi_t = 1.0
                        self.shake_t = 0.3
                        self.shake_guc = 9.0
                        self.ses.cal("basari", 0.9)
                        self.parcaciklar.yay(int(top.x), int(top.y), adet=35, renk=CAMGOBEGI, hiz=7.0)

            # Top alt kenarı geçti mi?
            if (top.y - top.r) > Y:
                self.ses.cal("woosh", 0.8)
                if self.skor > self.rekor:
                    self.rekor = self.skor
                self.durum = "sonuc"
                self.sonuc_baslangic = simdi
                self.shake_t = 0.25
                self.shake_guc = 7.0

        elif self.durum == "sonuc":
            if simdi - self.sonuc_baslangic >= 4.0:
                self.durum = "bekle"
                self.yuz_goruldu_sure = 0.0

        self.parcaciklar.guncelle(dt)

        # ---------------- ÇİZİM ----------------
        cikis = kare

        # Ekran sarsıntısı (shake)
        if self.shake_t > 0.0:
            sx = int(np.random.uniform(-self.shake_guc, self.shake_guc))
            sy = int(np.random.uniform(-self.shake_guc, self.shake_guc))
            M = np.float32([[1, 0, sx], [0, 1, sy]])
            cikis = cv2.warpAffine(cikis, M, (G, Y), borderMode=cv2.BORDER_REFLECT)

        # Kafa çarpışma bölgesi halkası (oyunda veya algı varsa)
        if self.kafa_var:
            kx_i, ky_i, kr_i = int(self.kafa_x), int(self.kafa_y), int(self.kafa_r)
            cv2.circle(cikis, (kx_i, ky_i), kr_i, CAMGOBEGI, 2, cv2.LINE_AA)
            cv2.circle(cikis, (kx_i, ky_i), max(4, kr_i - 8), (255, 240, 180), 1, cv2.LINE_AA)

        # Neon Parlama Katmanı
        katman = np.zeros_like(cikis)

        if self.durum == "oyun" and len(self.kuyruk) > 1:
            for i in range(len(self.kuyruk) - 1):
                p_bas = (int(self.kuyruk[i][0]), int(self.kuyruk[i][1]))
                p_bit = (int(self.kuyruk[i + 1][0]), int(self.kuyruk[i + 1][1]))
                alpha = (i + 1) / len(self.kuyruk)
                kalinlik = max(2, int(10 * alpha))
                bgr = (int(255 * alpha), int(220 * alpha), int(60 * alpha))
                cv2.line(katman, p_bas, p_bit, bgr, kalinlik, cv2.LINE_AA)

        parilti(cikis, katman, guc=1.4, sigma=2.5)

        # Top çizimi (Oyun modunda)
        if self.durum == "oyun":
            top = self.top
            olcek = 1.0
            if top.ezilme_t > 0.0:
                oran = top.ezilme_t / 0.15
                olcek = 1.0 - 0.22 * math.sin(oran * math.pi)

            boyut = int(90 * olcek)
            bindir_merkez(cikis, self.top_sprite, int(top.x), int(top.y), boyut=boyut, aci=top.aci)

        # Parçacıklar
        self.parcaciklar.ciz(cikis)

        # ---------------- DURUMA GÖRE ARAYÜZ METİNLERİ ----------------
        if self.durum == "bekle":
            cikis = bulanik_karanlik(cikis, 0.45)
            panel(cikis, G // 2 - 340, Y // 2 - 130, G // 2 + 340, Y // 2 + 130, (18, 18, 26), 0.75, SARI)

            nabiz = 1.0 + 0.06 * math.sin(simdi * 5.0)
            yazi_koy(cikis, "KAFANLA TOPU SEKTİR!", G // 2, Y // 2 - 40, int(54 * nabiz), SARI, hiza="orta")
            yazi_koy(cikis, "Başlamak için yüzünü göster", G // 2, Y // 2 + 32, 28, BEYAZ, hiza="orta")

            if self.rekor > 0:
                yazi_koy(cikis, f"Günün Rekoru: {self.rekor}", G // 2, Y // 2 + 82, 24, PEMBE, hiza="orta")

            if self.yuz_goruldu_sure > 0.0:
                oran = min(1.0, self.yuz_goruldu_sure / 0.5)
                bar_g = 400
                bx0 = (G - bar_g) // 2
                by0 = Y // 2 + 105
                cv2.rectangle(cikis, (bx0, by0), (bx0 + bar_g, by0 + 8), (40, 40, 50), -1)
                cv2.rectangle(cikis, (bx0, by0), (bx0 + int(bar_g * oran), by0 + 8), YESIL, -1)

        elif self.durum == "oyun":
            # Üst Skor Paneli
            panel(cikis, G // 2 - 140, 16, G // 2 + 140, 126, (15, 15, 22), 0.65, CAMGOBEGI)
            skor_olcek = 1.0 + 0.38 * self.skor_pop
            skor_boyut = int(82 * skor_olcek)
            skor_renk = SARI if self.skor_pop > 0.1 else BEYAZ
            yazi_koy(cikis, str(self.skor), G // 2, 70, skor_boyut, skor_renk, hiza="orta")

            # Mini rekor paneli sol üst
            panel(cikis, 30, 20, 210, 70, (15, 15, 22), 0.55)
            yazi_koy(cikis, f"REKOR: {self.rekor}", 120, 45, 24, PEMBE, hiza="orta")

            # "SÜPER!" kutlaması
            if self.super_yazi_t > 0.0:
                sy_olcek = 1.0 + 0.15 * math.sin(self.super_yazi_t * 8.0)
                yazi_koy(
                    cikis,
                    "★ SÜPER! ★",
                    G // 2,
                    Y // 2 - 60,
                    int(72 * sy_olcek),
                    PEMBE,
                    hiza="orta",
                )

        elif self.durum == "sonuc":
            panel(cikis, G // 2 - 320, Y // 2 - 150, G // 2 + 320, Y // 2 + 150, (15, 15, 24), 0.85, PEMBE)

            if self.skor >= self.rekor and self.skor > 0:
                yazi_koy(cikis, "YENİ REKOR!", G // 2, Y // 2 - 90, 52, SARI, hiza="orta")
            else:
                yazi_koy(cikis, "OYUN BİTTİ", G // 2, Y // 2 - 90, 48, KIRMIZI, hiza="orta")

            yazi_koy(cikis, f"SKOR: {self.skor}", G // 2, Y // 2 - 10, 68, BEYAZ, hiza="orta")
            yazi_koy(cikis, f"En Yüksek: {self.rekor}", G // 2, Y // 2 + 65, 32, CAMGOBEGI, hiza="orta")

            kalan_sure = max(0.0, 4.0 - (simdi - self.sonuc_baslangic))
            yazi_koy(cikis, f"{int(math.ceil(kalan_sure))} sn sonra yeniden başlar...", G // 2, Y // 2 + 115, 20, (180, 180, 180), hiza="orta")

        return cikis
