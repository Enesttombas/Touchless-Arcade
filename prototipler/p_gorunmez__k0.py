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

    def __init__(self, ses):
        self.ses = ses
        self.maskeci = Maskeci()
        self.mod = "Pelerin"  # "Pelerin" veya "Hayalet"
        self.plaka = None  # (360, 640, 3) float32
        self.plaka_hazir = False
        self.bos_kare_sayisi = 0

        self.pelerin_alfa = 0.0
        self.kisi_vardi = False
        self.gorunmez_yazi_sure = 0.0
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

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R")):
            self.plaka = None
            self.plaka_hazir = False
            self.bos_kare_sayisi = 0
            self.pelerin_alfa = 0.0
            self.ses.cal("bonk")
        elif k == 32:  # Boşluk
            self._mod_degistir()

    def _mod_degistir(self) -> None:
        self.mod = "Hayalet" if self.mod == "Pelerin" else "Pelerin"
        self.gecis_parilti = 0.3
        self.ses.cal("woosh")

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        if self.onceki_simdi <= 0.0:
            self.onceki_simdi = simdi
            self.son_mod_degisim = simdi
        dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        # Sayaçlar
        if self.gorunmez_yazi_sure > 0.0:
            self.gorunmez_yazi_sure = max(0.0, self.gorunmez_yazi_sure - dt)
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

        # Kişi oranı kontrolü
        kisi_pikselleri = m > 0.5
        kisi_alani = float(np.mean(kisi_pikselleri))
        kisi_var = kisi_alani >= 0.02

        # Plaka güncelleme
        if not kisi_var:
            self.bos_kare_sayisi += 1
            if self.plaka is None:
                self.plaka = kare_kucuk_f.copy()
            else:
                self.plaka = 0.9 * self.plaka + 0.1 * kare_kucuk_f

            if self.bos_kare_sayisi >= 30:
                self.plaka_hazir = True
        elif self.plaka is not None:
            dis_maske = (m < 0.1)[:, :, None]
            self.plaka = np.where(dis_maske, 0.9 * self.plaka + 0.1 * kare_kucuk_f, self.plaka)

        # Plaka hazır değilse rehber ekranı
        if not self.plaka_hazir:
            cikti = kare.copy()
            oran = min(1.0, self.bos_kare_sayisi / 30.0)
            panel(cikti, G // 2 - 380, Y // 2 - 80, G // 2 + 380, Y // 2 + 80, opak=0.82, kenar=SARI)
            yazi_koy(cikti, "Bir saniye ekrandan çık, odayı ezberleyeyim", G // 2, Y // 2 - 40, 30, SARI, "orta")

            bx0, by0, bx1, by1 = G // 2 - 250, Y // 2 + 15, G // 2 + 250, Y // 2 + 40
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
                # Bounding box ile sadece gerekli bölgeyi işle (yüksek performans)
                ys, xs = np.where(aktif_yerler)
                y0_k, y1_k = int(ys.min()), int(ys.max() + 1)
                x0_k, x1_k = int(xs.min()), int(xs.max() + 1)

                y0, y1 = max(0, y0_k * 2), min(Y, y1_k * 2)
                x0, x1 = max(0, x0_k * 2), min(G, x1_k * 2)

                plaka_u8 = np.clip(self.plaka, 0, 255).astype(np.uint8)

                if self.mod == "Pelerin":
                    # Kırılma efekti
                    gy_bolge = self.grid_y[y0_k:y1_k, x0_k:x1_k]
                    gx_bolge = self.grid_x[y0_k:y1_k, x0_k:x1_k]
                    dx = 6.0 * np.sin(gy_bolge * 0.04 + simdi * 4.5).astype(np.float32)
                    dy = 6.0 * np.cos(gx_bolge * 0.04 + simdi * 4.0).astype(np.float32)

                    kirik_kucuk = cv2.remap(
                        plaka_u8,
                        gx_bolge + dx,
                        gy_bolge + dy,
                        cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT,
                    )
                    ic_bolge = cv2.resize(kirik_kucuk, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
                else:
                    # Hayalet Modu: %25 kare + %75 plaka (mavi tonlu)
                    plaka_bolge = cv2.resize(plaka_u8[y0_k:y1_k, x0_k:x1_k], (x1 - x0, y1 - y0))
                    kare_bolge = kare[y0:y1, x0:x1]
                    hayalet = cv2.addWeighted(kare_bolge, 0.25, plaka_bolge, 0.75, 0)
                    # Mavi kanalı canlandır
                    hayalet[:, :, 0] = np.clip(hayalet[:, :, 0].astype(np.uint16) * 13 // 10, 0, 255).astype(np.uint8)
                    ic_bolge = hayalet

                a_bolge = cv2.resize(a_kucuk[y0_k:y1_k, x0_k:x1_k], (x1 - x0, y1 - y0))[:, :, None]
                kare_kesit = kare[y0:y1, x0:x1].astype(np.float32)
                ic_kesit = ic_bolge.astype(np.float32)

                sonuc_kesit = kare_kesit * (1.0 - a_bolge) + ic_kesit * a_bolge
                cikti[y0:y1, x0:x1] = np.clip(sonuc_kesit, 0, 255).astype(np.uint8)

                # Kenar ışıması (0.2..0.8 aralığı)
                kenar_bandi = ((a_kucuk >= 0.2) & (a_kucuk <= 0.8)).astype(np.float32)
                if np.any(kenar_bandi > 0):
                    renk_kenar = CAMGOBEGI if self.mod == "Pelerin" else PEMBE
                    kenar_katman = np.zeros_like(kare_kucuk)
                    kenar_katman[:] = renk_kenar
                    kenar_katman = (kenar_katman * kenar_bandi[:, :, None]).astype(np.uint8)
                    kenar_buyuk = cv2.resize(kenar_katman, (G, Y), interpolation=cv2.INTER_LINEAR)
                    parilti(cikti, kenar_buyuk, guc=1.4, sigma=3.0)

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
