from __future__ import annotations

import math
import cv2
import numpy as np

from cekirdek import (
    G,
    Y,
    SARI,
    CAMGOBEGI,
    PEMBE,
    BEYAZ,
    px,
    panel,
    parilti,
    yazi_koy,
    Parcaciklar,
)


class Prototip:
    AD = "Kaleydoskop"
    ACIKLAMA = "Kafanı eğ: desen döner · Ağzını aç: yakınlaşır · Boşluk: mod"
    IHTIYAC = {"yuz"}
    SIRA = 16

    def __init__(self, ses):
        self.ses = ses
        self.modlar = [6, 8, 12]
        self.mod_idx = 1
        self.mod = self.modlar[self.mod_idx]

        # Küçük çalışma çözünürlüğü (480x270)
        self.kw = 480
        self.kh = 270
        self.ox = self.kw / float(G)
        self.oy = self.kh / float(Y)

        # Çıktı ızgarasının merkeze göre r ve t dizileri (__init__'te bir kez)
        yy, xx = np.mgrid[0 : self.kh, 0 : self.kw].astype(np.float32)
        dx = xx - (self.kw * 0.5)
        dy = yy - (self.kh * 0.5)
        self.r_grid = np.hypot(dx, dy).astype(np.float32)
        self.t_grid = (np.arctan2(dy, dx) + np.pi).astype(np.float32)  # 0 .. 2pi

        # Merkezdeki "göz" (yarıçap 90px) yumuşak maskesi (220x220 yama)
        self.goz_r = 90
        self.yama_r = 110
        gy, gx = np.ogrid[-self.yama_r : self.yama_r, -self.yama_r : self.yama_r]
        gr = np.sqrt((gx * gx + gy * gy).astype(np.float32))
        alfa = np.clip((self.goz_r - gr) / 6.0, 0.0, 1.0)
        self.goz_alfa = alfa[:, :, None].astype(np.float32)

        # Durum değişkenleri
        self.onceki_zaman = None
        self.son_mod_degisim = None
        self.parlama_zaman = -10.0

        self.mx = G * 0.5
        self.my = Y * 0.5
        self.kafa_aci = 0.0
        self.agiz_acik = 0.0
        self.zaman_aci = 0.0
        self.yuz_var_sure = 0.0
        self.agiz_tetik = False

        self.parcaciklar = Parcaciklar(90)
        self.neon_katman = np.zeros((Y, G, 3), dtype=np.uint8)

    def _mod_degistir(self, simdi: float | None = None):
        self.mod_idx = (self.mod_idx + 1) % len(self.modlar)
        self.mod = self.modlar[self.mod_idx]
        self.ses.cal("woosh", 0.75)
        if simdi is not None:
            self.parlama_zaman = simdi
            self.son_mod_degisim = simdi
        else:
            self.parlama_zaman = self.onceki_zaman if self.onceki_zaman is not None else 0.0

    def tus(self, k: int):
        if k == 32 or k in (ord("m"), ord("M")):
            self._mod_degistir(self.onceki_zaman)

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        if self.onceki_zaman is None:
            self.onceki_zaman = simdi
            self.son_mod_degisim = simdi
        dt = min(max(simdi - self.onceki_zaman, 0.0), 0.1)
        self.onceki_zaman = simdi

        # Her 15 saniyede otomatik mod değişimi
        if self.son_mod_degisim is not None and (simdi - self.son_mod_degisim) >= 15.0:
            self._mod_degistir(simdi)

        self.zaman_aci = (self.zaman_aci + 0.15 * dt) % (2.0 * math.pi)

        yuz_var = bool(algi.yuzler)
        hedef_mx = G * 0.5
        hedef_my = Y * 0.5
        hedef_aci = 0.0
        hedef_agiz = 0.0

        if yuz_var:
            yuz = algi.yuzler[0]
            try:
                bx, by = px(yuz, 1)
                hedef_mx = float(np.clip(bx, 120.0, G - 120.0))
                hedef_my = float(np.clip(by, 120.0, Y - 120.0))

                gx1, gy1 = px(yuz, 33)
                gx2, gy2 = px(yuz, 263)
                goz_mesafe = math.hypot(gx2 - gx1, gy2 - gy1)
                if goz_mesafe > 8.0:
                    hedef_aci = math.atan2(gy2 - gy1, gx2 - gx1)

                    dx1, dy1 = px(yuz, 13)
                    dx2, dy2 = px(yuz, 14)
                    dudak_mesafe = math.hypot(dx2 - dx1, dy2 - dy1)
                    oran = (dudak_mesafe / goz_mesafe - 0.04) / 0.42
                    hedef_agiz = float(np.clip(oran, 0.0, 1.0))
            except Exception:
                pass

            if self.yuz_var_sure == 0.0:
                self.ses.cal("ding", 0.5)
            self.yuz_var_sure = min(1.0, self.yuz_var_sure + dt * 3.5)
        else:
            self.yuz_var_sure = max(0.0, self.yuz_var_sure - dt * 2.5)

        # Üstel yumuşatmalar
        a_merkez = 0.35
        self.mx += a_merkez * (hedef_mx - self.mx)
        self.my += a_merkez * (hedef_my - self.my)

        fark_aci = (hedef_aci - self.kafa_aci + math.pi) % (2.0 * math.pi) - math.pi
        self.kafa_aci += 0.35 * fark_aci
        self.agiz_acik += 0.35 * (hedef_agiz - self.agiz_acik)

        # Ağız iyice açıldığında ses + parçacık geri bildirimi
        if self.agiz_acik > 0.55 and not self.agiz_tetik:
            self.agiz_tetik = True
            self.ses.cal("pop", 0.55)
            self.parcaciklar.yay(self.mx, self.my, 18, renk=PEMBE, hiz=5.0)
        elif self.agiz_acik < 0.35:
            self.agiz_tetik = False

        # 1) Küçük boyutta kaleydoskop kutupsal katlama (480x270)
        kucuk = cv2.resize(kare, (self.kw, self.kh), interpolation=cv2.INTER_LINEAR)

        kama = float(2.0 * math.pi / self.mod)
        yari_kama = kama * 0.5
        donus = float(self.kafa_aci * 2.0 + self.zaman_aci)
        olcek = float(1.0 - 0.45 * self.agiz_acik)

        tp = np.mod(self.t_grid + donus, kama)
        tp = np.minimum(tp, kama - tp)

        r_olcek = self.r_grid * olcek
        cx_k = float(self.mx * self.ox)
        cy_k = float(self.my * self.oy)

        map_x = cx_k + r_olcek * np.cos(tp)
        map_y = cy_k + r_olcek * np.sin(tp)

        kal_kucuk = cv2.remap(
            kucuk,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT,
        )

        # 2) İnce renk katmanı: çeyrek çözünürlükte HSV hue kaydırma (%25 karışım)
        ceyrek = cv2.resize(kal_kucuk, (self.kw // 2, self.kh // 2), interpolation=cv2.INTER_NEAREST)
        hsv = cv2.cvtColor(ceyrek, cv2.COLOR_BGR2HSV)
        hue_kayma = int((simdi * 35.0 + self.agiz_acik * 60.0) % 180)
        hsv[:, :, 0] = (hsv[:, :, 0].astype(np.uint16) + hue_kayma) % 180
        hsv[:, :, 1] = np.clip(hsv[:, :, 1].astype(np.uint16) + 70, 0, 255).astype(np.uint8)
        renk_kucuk = cv2.resize(
            cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR),
            (self.kw, self.kh),
            interpolation=cv2.INTER_LINEAR,
        )
        cv2.addWeighted(kal_kucuk, 0.75, renk_kucuk, 0.25, 0.0, dst=kal_kucuk)

        # Tam ekran boyutuna büyüt (1280x720)
        cikti = cv2.resize(kal_kucuk, (G, Y), interpolation=cv2.INTER_LINEAR)

        # 3) Merkezde gerçek yüz / kaleydoskobun "gözü" (yarıçap 90 px)
        icx = int(np.clip(round(self.mx), self.yama_r, G - self.yama_r))
        icy = int(np.clip(round(self.my), self.yama_r, Y - self.yama_r))

        x0, x1 = icx - self.yama_r, icx + self.yama_r
        y0, y1 = icy - self.yama_r, icy + self.yama_r

        kaynak_yama = kare[y0:y1, x0:x1].astype(np.float32)
        hedef_yama = cikti[y0:y1, x0:x1].astype(np.float32)
        cikti[y0:y1, x0:x1] = (
            kaynak_yama * self.goz_alfa + hedef_yama * (1.0 - self.goz_alfa)
        ).astype(np.uint8)

        # 4) Neon halkalar ve simetri ışınları
        self.neon_katman.fill(0)
        halka_r = int(self.goz_r + 6 * self.agiz_acik)
        cv2.circle(self.neon_katman, (icx, icy), halka_r, CAMGOBEGI, 4, cv2.LINE_AA)
        cv2.circle(self.neon_katman, (icx, icy), halka_r + 8, PEMBE, 1, cv2.LINE_AA)

        # Kama simetri çizgileri (hafif neon)
        for i in range(self.mod):
            aci_cizgi = i * kama - donus
            ux1 = int(icx + math.cos(aci_cizgi) * (halka_r + 12))
            uy1 = int(icy + math.sin(aci_cizgi) * (halka_r + 12))
            ux2 = int(icx + math.cos(aci_cizgi) * (halka_r + 65 + 40 * self.agiz_acik))
            uy2 = int(icy + math.sin(aci_cizgi) * (halka_r + 65 + 40 * self.agiz_acik))
            renk_cizgi = SARI if i % 2 == 0 else CAMGOBEGI
            cv2.line(self.neon_katman, (ux1, uy1), (ux2, uy2), renk_cizgi, 2, cv2.LINE_AA)

        parilti(cikti, self.neon_katman, guc=1.6, sigma=3.0)

        # Parçacıklar
        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(cikti)

        # 5) Mod geçişinde 0.3 sn beyaz parlama
        gecen_parlama = simdi - self.parlama_zaman
        if 0.0 <= gecen_parlama < 0.3:
            oran_p = 1.0 - (gecen_parlama / 0.3)
            guc_p = float(oran_p * oran_p * 0.65)
            beyaz = np.full_like(cikti, 255)
            cv2.addWeighted(cikti, 1.0 - guc_p, beyaz, guc_p, 0.0, dst=cikti)

        # 6) Üstte küçük başlık & alt solda mod paneli
        panel(cikti, G // 2 - 190, 14, G // 2 + 190, 66, renk=(18, 18, 28), opak=0.65, kenar=CAMGOBEGI)
        yazi_koy(cikti, "KALEYDOSKOP", G // 2, 22, 34, renk=SARI, hiza="orta")

        panel(cikti, 24, Y - 86, 230, Y - 22, renk=(18, 18, 28), opak=0.72, kenar=PEMBE)
        yazi_koy(cikti, f"N = {self.mod}", 127, Y - 76, 36, renk=CAMGOBEGI, hiza="orta")

        # 7) Kimse yokken davet ekranı
        if not yuz_var:
            nabiz = 1.0 + 0.06 * math.sin(simdi * 4.5)
            panel(cikti, G // 2 - 420, Y - 185, G // 2 + 420, Y - 45, renk=(15, 15, 24), opak=0.75, kenar=SARI)
            yazi_koy(
                cikti,
                "Kaleydoskobun merkezine gir!",
                G // 2,
                Y - 168,
                46,
                renk=SARI,
                hiza="orta",
                olcek=nabiz,
            )
            yazi_koy(
                cikti,
                "Kafanı eğ: döner  ·  Ağzını aç: yakınlaşır",
                G // 2,
                Y - 96,
                26,
                renk=BEYAZ,
                hiza="orta",
            )

        kare[:] = cikti
        return kare
