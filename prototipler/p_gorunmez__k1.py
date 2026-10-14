import math
import numpy as np
import cv2

from cekirdek import (
    G,
    Y,
    SARI,
    CAMGOBEGI,
    PEMBE,
    YESIL,
    BEYAZ,
    Maskeci,
    panel,
    baslik,
    parilti,
    yazi_koy,
)


class Prototip:
    AD = "Görünmezlik Pelerini"
    ACIKLAMA = "Kamera seni siler; Harry Potter pelerini veya Hayalet moduna geç!"
    IHTIYAC = set()
    SIRA = 13
    MODLAR = ("Pelerin", "Hayalet", "Uçan Kafa")

    def __init__(self, ses):
        self.ses = ses
        self.maskeci = Maskeci()
        self.mod = "Pelerin"  # "Pelerin", "Hayalet" veya "Uçan Kafa"
        self.plaka = None  # (360, 640, 3) float32
        self.plaka_hazir = False
        self.bos_kare_sayisi = 0
        self.kapsama = 0.0

        self.pelerin_alfa = 0.0
        self.kisi_vardi = False
        self.gorunmez_yazi_sure = 0.0
        self.alt_ipucu_sure = 0.0
        self.gecis_parilti = 0.0

        self.onceki_simdi = 0.0
        self.son_mod_degisim = 0.0

        # Kırılma efekti için 640x360 ızgara
        self.kw = G // 2
        self.kh = Y // 2
        gx, gy = np.meshgrid(
            np.arange(self.kw, dtype=np.float32),
            np.arange(self.kh, dtype=np.float32),
        )
        self.grid_x = gx
        self.grid_y = gy
        self.goruldu_sayac = np.zeros((self.kh, self.kw), dtype=np.uint8)

    def _plaka_sifirla(self) -> None:
        self.plaka = None
        self.plaka_hazir = False
        self.bos_kare_sayisi = 0
        self.kapsama = 0.0
        self.goruldu_sayac.fill(0)
        self.pelerin_alfa = 0.0

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R")):
            self._plaka_sifirla()
            self.ses.cal("bonk")
        elif k == 32:  # Boşluk
            self._mod_degistir()

    def _mod_degistir(self) -> None:
        idx = self.MODLAR.index(self.mod) if self.mod in self.MODLAR else 0
        self.mod = self.MODLAR[(idx + 1) % len(self.MODLAR)]
        self.gecis_parilti = 0.3
        self.ses.cal("woosh")

    def _inpaint_plaka(self, plaka_u8: np.ndarray) -> np.ndarray:
        hazir_degil = self.goruldu_sayac < 8
        if not np.any(hazir_degil):
            return plaka_u8
        if np.all(hazir_degil):
            return plaka_u8
        qw, qh = self.kw // 2, self.kh // 2
        p_q = cv2.resize(plaka_u8, (qw, qh), interpolation=cv2.INTER_AREA)
        m_q = cv2.resize(hazir_degil.astype(np.uint8) * 255, (qw, qh), interpolation=cv2.INTER_NEAREST)
        dolu_q = cv2.inpaint(p_q, m_q, 3, cv2.INPAINT_TELEA)
        dolu_h = cv2.resize(dolu_q, (self.kw, self.kh), interpolation=cv2.INTER_LINEAR)
        sonuc = plaka_u8.copy()
        sonuc[hazir_degil] = dolu_h[hazir_degil]
        return sonuc

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        if self.onceki_simdi <= 0.0:
            self.onceki_simdi = simdi
            self.son_mod_degisim = simdi
        dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        # Sayaçlar
        if self.gorunmez_yazi_sure > 0.0:
            self.gorunmez_yazi_sure = max(0.0, self.gorunmez_yazi_sure - dt)
        if self.alt_ipucu_sure > 0.0:
            self.alt_ipucu_sure = max(0.0, self.alt_ipucu_sure - dt)
        if self.gecis_parilti > 0.0:
            self.gecis_parilti = max(0.0, self.gecis_parilti - dt)

        # 12 saniyede bir otomatik mod değişimi
        if simdi - self.son_mod_degisim >= 12.0:
            self.son_mod_degisim = simdi
            self._mod_degistir()

        # Maske alımı
        m = self.maskeci.ver(kare)
        if m is None:
            cikti = kare.copy()
            panel(cikti, G // 2 - 200, Y // 2 - 50, G // 2 + 200, Y // 2 + 50, opak=0.75, kenar=CAMGOBEGI)
            yazi_koy(cikti, "Hazırlanıyor...", G // 2, Y // 2 - 14, 32, CAMGOBEGI, "orta")
            yazi_koy(cikti, "Kamera maskesi bekleniyor", G // 2, Y // 2 + 20, 20, BEYAZ, "orta")
            baslik(cikti, "Görünmezlik Pelerini", "Arkadaşına göster!")
            return cikti

        kare_kucuk = cv2.resize(kare, (self.kw, self.kh), interpolation=cv2.INTER_AREA)
        kare_kucuk_f = kare_kucuk.astype(np.float32)

        if self.plaka is None:
            self.plaka = kare_kucuk_f.copy()

        # Kişi oranı kontrolü
        kisi_pikselleri = m > 0.5
        kisi_alani = float(np.mean(kisi_pikselleri))
        kisi_var = kisi_alani >= 0.02

        # Plaka güncelleme ve oda ezberi
        if not self.plaka_hazir:
            dis_m = m < 0.2
            ilk_kez = dis_m & (self.goruldu_sayac == 0)
            sonraki_kez = dis_m & (self.goruldu_sayac > 0)

            if np.any(ilk_kez):
                self.plaka[ilk_kez] = kare_kucuk_f[ilk_kez]
            if np.any(sonraki_kez):
                self.plaka[sonraki_kez] = 0.85 * self.plaka[sonraki_kez] + 0.15 * kare_kucuk_f[sonraki_kez]

            artir = dis_m & (self.goruldu_sayac < 255)
            self.goruldu_sayac[artir] += 1

            if not kisi_var:
                self.bos_kare_sayisi += 1
                self.plaka = 0.9 * self.plaka + 0.1 * kare_kucuk_f

            hazir_oran = float(np.mean(self.goruldu_sayac >= 8))
            kismi_oran = float(np.mean(np.minimum(self.goruldu_sayac, 8))) / 8.0
            bos_oran = min(1.0, self.bos_kare_sayisi / 30.0)
            self.kapsama = max(hazir_oran, kismi_oran * 0.91, bos_oran)

            if hazir_oran >= 0.92 or self.bos_kare_sayisi >= 30:
                self.plaka_hazir = True
                self.kapsama = max(self.kapsama, 0.92 if hazir_oran >= 0.92 else 1.0)
        else:
            dis_m = m < 0.1
            if not kisi_var:
                self.plaka = 0.92 * self.plaka + 0.08 * kare_kucuk_f
                artir = self.goruldu_sayac < 255
                self.goruldu_sayac[artir] += 1
            else:
                ilk_kez = dis_m & (self.goruldu_sayac == 0)
                sonraki_kez = dis_m & (self.goruldu_sayac > 0)
                if np.any(ilk_kez):
                    self.plaka[ilk_kez] = kare_kucuk_f[ilk_kez]
                if np.any(sonraki_kez):
                    self.plaka[sonraki_kez] = 0.9 * self.plaka[sonraki_kez] + 0.1 * kare_kucuk_f[sonraki_kez]
                artir = dis_m & (self.goruldu_sayac < 255)
                self.goruldu_sayac[artir] += 1
            self.kapsama = max(self.kapsama, float(np.mean(self.goruldu_sayac >= 8)))

        # Plaka hazır değilse rehber ekranı
        if not self.plaka_hazir:
            cikti = kare.copy()
            oran = min(1.0, max(0.0, self.kapsama))
            yuzde = int(round(oran * 100))
            panel(cikti, G // 2 - 380, Y // 2 - 90, G // 2 + 380, Y // 2 + 95, opak=0.82, kenar=SARI)
            yazi_koy(cikti, f"Odayı ezberliyorum %{yuzde}", G // 2, Y // 2 - 52, 34, SARI, "orta")
            yazi_koy(cikti, "Biraz sağa sola kay", G // 2, Y // 2 - 12, 24, BEYAZ, "orta")

            bx0, by0, bx1, by1 = G // 2 - 250, Y // 2 + 30, G // 2 + 250, Y // 2 + 56
            cv2.rectangle(cikti, (bx0, by0), (bx1, by1), (40, 40, 50), -1)
            dolgu_w = int((bx1 - bx0) * oran)
            if dolgu_w > 0:
                cv2.rectangle(cikti, (bx0, by0), (bx0 + dolgu_w, by1), YESIL, -1)
            cv2.rectangle(cikti, (bx0, by0), (bx1, by1), BEYAZ, 2, cv2.LINE_AA)

            baslik(cikti, "Görünmezlik Pelerini", "Arka plan öğreniliyor...")
            return cikti

        # Giriş algılama
        if kisi_var and not self.kisi_vardi:
            self.pelerin_alfa = 0.0
            self.gorunmez_yazi_sure = 2.0
            self.alt_ipucu_sure = 3.0
            self.ses.cal("basari")
        self.kisi_vardi = kisi_var

        # Pelerin açılma yumuşatması
        if kisi_var:
            self.pelerin_alfa = min(1.0, self.pelerin_alfa + dt / 0.8)
        else:
            self.pelerin_alfa = max(0.0, self.pelerin_alfa - dt * 2.5)

        cikti = kare.copy()

        # Efekt uygulaması (yalnızca pelerin aktifken ve kişi varken)
        if self.pelerin_alfa > 0.01:
            a_kucuk = np.clip((m - 0.35) / 0.30, 0.0, 1.0)
            a_kucuk = cv2.GaussianBlur(a_kucuk, (7, 7), 0) * self.pelerin_alfa

            aktif_yerler = a_kucuk > 0.01
            if np.any(aktif_yerler):
                ys, xs = np.where(aktif_yerler)
                y0_k, y1_k = int(ys.min()), int(ys.max() + 1)
                x0_k, x1_k = int(xs.min()), int(xs.max() + 1)

                # "Uçan Kafa" modu: üst %24 görünür kalır (yumuşak geçişli dikey alfa)
                if self.mod == "Uçan Kafa":
                    yukseklik_k = max(1, y1_k - y0_k)
                    sinir_y = y0_k + 0.24 * yukseklik_k
                    gecis_bant = max(2.0, 0.06 * yukseklik_k)
                    y_dizi = np.arange(y0_k, y1_k, dtype=np.float32)[:, None]
                    govde_alfa = np.clip((y_dizi - sinir_y) / gecis_bant, 0.0, 1.0)
                    a_kucuk[y0_k:y1_k, x0_k:x1_k] *= govde_alfa

                y0, y1 = max(0, y0_k * 2), min(Y, y1_k * 2)
                x0, x1 = max(0, x0_k * 2), min(G, x1_k * 2)

                plaka_u8 = np.clip(self.plaka, 0, 255).astype(np.uint8)
                plaka_dolu = self._inpaint_plaka(plaka_u8)

                if self.mod in ("Pelerin", "Uçan Kafa"):
                    gy_bolge = self.grid_y[y0_k:y1_k, x0_k:x1_k]
                    gx_bolge = self.grid_x[y0_k:y1_k, x0_k:x1_k]
                    dx = 6.0 * np.sin(gy_bolge * 0.04 + simdi * 4.5).astype(np.float32)
                    dy = 6.0 * np.cos(gx_bolge * 0.04 + simdi * 4.0).astype(np.float32)

                    kirik_kucuk = cv2.remap(
                        plaka_dolu,
                        gx_bolge + dx,
                        gy_bolge + dy,
                        cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT,
                    )
                    ic_bolge = cv2.resize(kirik_kucuk, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
                else:
                    # Hayalet Modu: %25 kare + %75 plaka (mavi tonlu)
                    plaka_bolge = cv2.resize(plaka_dolu[y0_k:y1_k, x0_k:x1_k], (x1 - x0, y1 - y0))
                    kare_bolge = kare[y0:y1, x0:x1]
                    hayalet = cv2.addWeighted(kare_bolge, 0.25, plaka_bolge, 0.75, 0)
                    hayalet[:, :, 0] = np.clip(hayalet[:, :, 0].astype(np.uint16) * 13 // 10, 0, 255).astype(np.uint8)
                    ic_bolge = hayalet

                a_bolge = cv2.resize(a_kucuk[y0_k:y1_k, x0_k:x1_k], (x1 - x0, y1 - y0))[:, :, None]
                kare_kesit = kare[y0:y1, x0:x1].astype(np.float32)
                ic_kesit = ic_bolge.astype(np.float32)

                sonuc_kesit = kare_kesit * (1.0 - a_bolge) + ic_kesit * a_bolge
                cikti[y0:y1, x0:x1] = np.clip(sonuc_kesit, 0, 255).astype(np.uint8)

                # Kırılma kenarı: 1.2 sn periyotla nabız (0.6 <-> 1.0); Pelerin'de hafif gökkuşağı tonu
                kenar_bandi = ((a_kucuk >= 0.2) & (a_kucuk <= 0.8)).astype(np.float32)
                if np.any(kenar_bandi > 0):
                    nabiz_k = 0.8 + 0.2 * math.sin(2.0 * math.pi * simdi / 1.2)
                    kenar_katman = np.zeros_like(kare_kucuk)
                    ky, kx = np.where(kenar_bandi > 0)
                    if self.mod == "Pelerin":
                        faz = ky * 0.04 + kx * 0.03 + simdi * 3.0
                        b = (185.0 + 70.0 * np.sin(faz)) * nabiz_k
                        g = (185.0 + 70.0 * np.sin(faz + 2.094)) * nabiz_k
                        r = (165.0 + 90.0 * np.sin(faz + 4.188)) * nabiz_k
                        kenar_katman[ky, kx, 0] = np.clip(b, 0, 255).astype(np.uint8)
                        kenar_katman[ky, kx, 1] = np.clip(g, 0, 255).astype(np.uint8)
                        kenar_katman[ky, kx, 2] = np.clip(r, 0, 255).astype(np.uint8)
                    else:
                        renk_baz = PEMBE if self.mod == "Hayalet" else SARI
                        renk_nabiz = tuple(int(min(255, c * nabiz_k)) for c in renk_baz)
                        kenar_katman[ky, kx] = renk_nabiz

                    kenar_buyuk = cv2.resize(kenar_katman, (G, Y), interpolation=cv2.INTER_LINEAR)
                    parilti(cikti, kenar_buyuk, guc=1.4 * nabiz_k, sigma=3.0)

        # Mod geçiş parıltısı
        if self.gecis_parilti > 0.0:
            oran = (self.gecis_parilti / 0.3) * 0.4
            cv2.addWeighted(cikti, 1.0 - oran, np.full_like(cikti, 255), oran, 0, dst=cikti)

        # Üst Başlık
        baslik(cikti, "Görünmezlik Pelerini", "Arkadaşına göster! — Sen yoksun, oda var!")

        # "GÖRÜNMEZSİN!" kutlama animasyonu
        if self.gorunmez_yazi_sure > 0.0:
            yazi_alfa = min(1.0, self.gorunmez_yazi_sure / 0.5)
            nabiz = 1.0 + 0.06 * math.sin((2.0 - self.gorunmez_yazi_sure) * 12.0)
            panel(cikti, G // 2 - 270, Y // 2 - 60, G // 2 + 270, Y // 2 + 60, opak=0.85 * yazi_alfa, kenar=SARI)
            yazi_koy(cikti, "GÖRÜNMEZSİN!", G // 2, Y // 2 - 18, 56, SARI, "orta", olcek=nabiz, opak=yazi_alfa)
            yazi_koy(cikti, "Harry Potter pelerini devrede", G // 2, Y // 2 + 32, 22, BEYAZ, "orta", opak=yazi_alfa)

        # Alt 3 sn ipucu yazısı
        if self.alt_ipucu_sure > 0.0:
            ipucu_alfa = min(1.0, self.alt_ipucu_sure / 0.4)
            panel(cikti, G // 2 - 230, Y - 76, G // 2 + 230, Y - 24, opak=0.78 * ipucu_alfa, kenar=SARI)
            yazi_koy(
                cikti,
                "Arkadaşın seni görebiliyor mu?",
                G // 2,
                Y - 58,
                22,
                BEYAZ,
                "orta",
                opak=ipucu_alfa,
            )

        # Sol Alt Mod Paneli
        panel(cikti, 24, Y - 110, 360, Y - 20, opak=0.75, kenar=CAMGOBEGI)
        yazi_koy(cikti, f"Mod: {self.mod}", 40, Y - 96, 26, SARI, "sol")
        yazi_koy(cikti, "[BOŞLUK] Modu Değiştir", 40, Y - 68, 20, BEYAZ, "sol")
        yazi_koy(cikti, "[R] Arka Planı Sıfırla", 40, Y - 44, 18, (180, 180, 190), "sol")

        # Sağ Alt Bilgi
        panel(cikti, G - 260, Y - 70, G - 24, Y - 20, opak=0.75, kenar=YESIL)
        yazi_koy(cikti, "● Arka Plan Kilitli", G - 240, Y - 58, 20, YESIL, "sol")
        yazi_koy(cikti, "Odaya dinamik uyum", G - 240, Y - 36, 17, (190, 190, 200), "sol")

        return cikti
