from collections import deque
import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    Maskeci,
    PEMBE,
    SARI,
    YESIL,
    Y,
    baslik,
    panel,
    parilti,
    yazi_koy,
)


class Prototip:
    AD = "Zaman Klonları"
    ACIKLAMA = "Hareket et, arkanda bıraktığın renkli zaman yankılarını izle!"
    IHTIYAC = set()
    SIRA = 11

    def __init__(self, ses):
        self.ses = ses
        self.modlar = ["Neon", "Klon", "Gökkuşağı"]
        self.mod_idx = 0
        self.mod = self.modlar[self.mod_idx]
        self.son_mod_degisim = None
        self.onceki_simdi = None

        self.maskeci = Maskeci()
        self.maskeci_ilk_zaman = None
        self.maskeci_calisti = False

        self.mog = cv2.createBackgroundSubtractorMOG2(
            history=300, varThreshold=32, detectShadows=False
        )
        self.cekirdek_kenar = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # En fazla 7 yankı için gecikmeler: 5, 10, 15, 20, 25, 30, 35
        # Tampon maxlen en az 40 olmalı
        self.tampon = deque(maxlen=45)
        self.tum_gecikmeler = [5, 10, 15, 20, 25, 30, 35]

        # 7 sabit neon renk (BGR)
        renk_listesi = [
            PEMBE,
            (255, 80, 160),   # Mor
            CAMGOBEGI,
            (255, 180, 0),    # Açık mavi / Turkuaz
            YESIL,
            SARI,
            (60, 120, 255),   # Turuncu / Mercan
        ]
        self.renkler = [np.array(r, dtype=np.float32) for r in renk_listesi]
        self._renk_u8 = [
            np.full((360, 640, 3), r, dtype=np.uint8) for r in renk_listesi
        ]

        self.onceki_maske = None
        self.hareket_skor = 0.0
        self.yanki_sayisi_f = 3.0
        self.yanki_sayisi = 3

        # Harika ödülü
        self.son_harika_zamani = -10.0

        # Vitrin (kimse yokken) durumu ve hayalet tekrar kaydı
        self.bos_sure = 0.0
        self.vitrin_aktif = False
        self.vitrin_opaklik = 0.0
        self.hayalet_tampon = deque(maxlen=60)   # Son kişinin canlı 2 sn kaydı (yarım boy)
        self.kayitli_hayalet = []                # Boş anında oynatılacak kopya
        self.hayalet_idx = 0

    def tus(self, k: int) -> None:
        if k == 32:  # Boşluk
            self._mod_degistir()

    def _mod_degistir(self, simdi: float = None) -> None:
        self.mod_idx = (self.mod_idx + 1) % len(self.modlar)
        self.mod = self.modlar[self.mod_idx]
        if simdi is not None:
            self.son_mod_degisim = simdi
        self.ses.cal("woosh", 0.6)

    def _maske_cikar(self, kare: np.ndarray, kare_yarim: np.ndarray, simdi: float) -> tuple[np.ndarray | None, bool]:
        if self.maskeci_ilk_zaman is None:
            self.maskeci_ilk_zaman = simdi

        m = self.maskeci.ver(kare)
        if m is not None:
            self.maskeci_calisti = True
            yumusak = np.clip((m - 0.35) / 0.3, 0.0, 1.0).astype(np.float32)
            yumusak = cv2.GaussianBlur(yumusak, (5, 5), 0)
            return yumusak, True

        # Henüz Maskeci maske vermedi
        gecen = simdi - self.maskeci_ilk_zaman
        if not self.maskeci_calisti and gecen < 4.0:
            return None, False

        # 4 sn sonra MOG2 yedeği devreye girer
        kare_ceyrek = cv2.resize(kare_yarim, (320, 180), interpolation=cv2.INTER_AREA)
        fg_ceyrek = self.mog.apply(kare_ceyrek)
        fg_f32 = fg_ceyrek.astype(np.float32) * (1.0 / 255.0)
        fg_f32 = cv2.GaussianBlur(fg_f32, (7, 7), 0)
        fg_yarim = cv2.resize(fg_f32, (640, 360), interpolation=cv2.INTER_LINEAR)
        yumusak = np.clip((fg_yarim - 0.35) / 0.3, 0.0, 1.0).astype(np.float32)
        yumusak = cv2.GaussianBlur(yumusak, (5, 5), 0)
        return yumusak, True

    def _gokkusagi_renk_u8(self, yanki_idx: int, simdi: float) -> tuple[np.ndarray, np.ndarray]:
        # Ton zamanla kayar, her yankı farklı açıda
        ton = int((simdi * 60.0 + yanki_idx * (180.0 / 7.0)) % 180)
        hsv_tek = np.uint8([[[ton, 240, 255]]])
        bgr_tek = cv2.cvtColor(hsv_tek, cv2.COLOR_HSV2BGR)[0, 0]
        renk_dizi = np.array(bgr_tek, dtype=np.float32)
        katman = np.full((360, 640, 3), bgr_tek, dtype=np.uint8)
        return katman, renk_dizi

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        if self.son_mod_degisim is None:
            self.son_mod_degisim = simdi

        dt = 0.033
        if self.onceki_simdi is not None:
            dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        # 15 saniyede bir otomatik mod döngüsü
        if simdi - self.son_mod_degisim >= 15.0:
            self._mod_degistir(simdi)

        # Yarım çözünürlük
        kare_yarim = cv2.resize(kare, (640, 360), interpolation=cv2.INTER_LINEAR)
        maske, hazir = self._maske_cikar(kare, kare_yarim, simdi)

        # 1. Açılış lekesi koruması: maske henüz hiç hazır değilse yankı çizme
        if not hazir or maske is None:
            cv2.convertScaleAbs(kare, dst=kare, alpha=0.45)
            baslik(kare, "ZAMAN KLONLARI", "Kamera ve model hazırlanıyor...", renk=CAMGOBEGI)
            panel(kare, G // 2 - 140, Y // 2 - 30, G // 2 + 140, Y // 2 + 30, renk=(15, 15, 24), opak=0.7, kenar=CAMGOBEGI)
            yazi_koy(kare, "Hazırlanıyor...", G // 2, Y // 2 - 10, 28, renk=SARI, hiza="orta")
            return kare

        # Maske doluluk oranı
        maske_orani = float(np.mean(maske))
        kisi_var = maske_orani >= 0.02

        # Hareket takibi
        if self.onceki_maske is not None:
            fark = float(np.mean(np.abs(maske - self.onceki_maske)))
        else:
            fark = maske_orani * 0.1
        self.onceki_maske = maske

        # Hareket skoru yumuşatma
        alfa_h = min(1.0, dt * 2.2)
        self.hareket_skor += (fark - self.hareket_skor) * alfa_h

        # 2. Dans ödülü: hareket skoruyla yankı sayısı 3 -> 7 arası dinamik
        # Hareket skoru tipik 0.005 (sakin) .. 0.05+ (hızlı dans)
        h_norm = np.clip((self.hareket_skor - 0.006) / 0.035, 0.0, 1.0)
        hedef_yanki = 3.0 + 4.0 * h_norm
        self.yanki_sayisi_f += (hedef_yanki - self.yanki_sayisi_f) * min(1.0, dt * 3.0)
        self.yanki_sayisi = int(round(self.yanki_sayisi_f))
        self.yanki_sayisi = max(3, min(7, self.yanki_sayisi))

        # "HARİKA!" dans pop bildirimi
        harika_aktif = False
        if kisi_var and h_norm >= 0.82 and (simdi - self.son_harika_zamani) >= 4.0:
            self.son_harika_zamani = simdi
            self.ses.cal("basari", 0.75)

        if simdi - self.son_harika_zamani < 1.0:
            harika_aktif = True

        # Vitrin (kimse yokken) mantığı
        if kisi_var:
            self.bos_sure = 0.0
            self.vitrin_aktif = False
            self.vitrin_opaklik = max(0.0, self.vitrin_opaklik - dt * (1.0 / 0.3))
            # Kişi varken kare+maske kaydı tut
            self.hayalet_tampon.append((kare_yarim.copy(), maske.copy()))
        else:
            self.bos_sure += dt
            if self.bos_sure >= 1.5:
                if not self.vitrin_aktif and len(self.hayalet_tampon) >= 20:
                    self.kayitli_hayalet = list(self.hayalet_tampon)
                    self.hayalet_idx = 0
                self.vitrin_aktif = True
                self.vitrin_opaklik = min(1.0, self.vitrin_opaklik + dt * 2.5)

        # Canlı tampon
        self.tampon.append((kare_yarim, maske))
        tampon_uzunluk = len(self.tampon)

        # Arka plan: güncel kare %45 karartılmış
        komp = cv2.convertScaleAbs(kare_yarim, alpha=0.55)

        # Yankılar için katman
        neon_katman = (
            np.zeros((360, 640, 3), dtype=np.uint8)
            if self.mod in ("Neon", "Gökkuşağı")
            else None
        )

        aktif_gecikmeler = self.tum_gecikmeler[: self.yanki_sayisi]
        toplam_yanki = len(aktif_gecikmeler)

        # Yankıları en eskiden en yeniye çiz
        for cizim_sira, gecikme in enumerate(reversed(aktif_gecikmeler)):
            if tampon_uzunluk <= gecikme:
                continue

            eski_kare, eski_maske = self.tampon[-1 - gecikme]
            if float(eski_maske.max()) < 0.02:
                continue

            # yanki_no: 0 en yeni, toplam_yanki-1 en eski
            yanki_no = (toplam_yanki - 1) - cizim_sira
            opaklik = 0.78 - (0.45 / max(1, toplam_yanki - 1)) * yanki_no
            w = eski_maske * max(0.15, opaklik)

            if self.mod == "Klon":
                komp = cv2.blendLinear(komp, eski_kare, 1.0 - w, w)
            else:
                if self.mod == "Neon":
                    renk_kat = self._renk_u8[yanki_no % len(self._renk_u8)]
                    renk_f = self.renkler[yanki_no % len(self.renkler)]
                else:  # Gökkuşağı
                    renk_kat, renk_f = self._gokkusagi_renk_u8(yanki_no, simdi)

                boyali = cv2.addWeighted(renk_kat, 0.72, eski_kare, 0.28, 0)
                komp = cv2.blendLinear(komp, boyali, 1.0 - w, w)

                genis = cv2.dilate(eski_maske, self.cekirdek_kenar)
                kenar1 = cv2.convertScaleAbs(cv2.subtract(genis, eski_maske), alpha=1.7 * 255)
                r_norm = renk_f / 255.0
                kenar_u8 = cv2.multiply(
                    cv2.cvtColor(kenar1, cv2.COLOR_GRAY2BGR),
                    (float(r_norm[0]), float(r_norm[1]), float(r_norm[2]), 0.0),
                )
                cv2.max(neon_katman, kenar_u8, dst=neon_katman)

        # Güncel kişi ön planda
        if kisi_var:
            komp = cv2.blendLinear(komp, kare_yarim, 1.0 - maske, maske)

        # 3. Vitrin: Hayalet tekrar oynatımı
        if self.vitrin_opaklik > 0.01 and self.kayitli_hayalet:
            self.hayalet_idx = (self.hayalet_idx + 1) % len(self.kayitli_hayalet)
            h_kare, h_maske = self.kayitli_hayalet[self.hayalet_idx]
            h_w = h_maske * (0.35 * self.vitrin_opaklik)
            # Neon pembe-mavi tonuyla karıştır
            h_renk = np.full((360, 640, 3), (255, 120, 180), dtype=np.uint8)
            h_boyali = cv2.addWeighted(h_renk, 0.45, h_kare, 0.55, 0)
            komp = cv2.blendLinear(komp, h_boyali, 1.0 - h_w, h_w)

        # Neon / Gökkuşağı parıltısı
        if neon_katman is not None:
            parilti(komp, neon_katman, guc=1.8, sigma=2.8)

        # Tam ekrana büyüt
        cv2.resize(komp, (G, Y), dst=kare, interpolation=cv2.INTER_LINEAR)

        # Üst başlık (Tek çağrı, çakışma yok)
        baslik(kare, "ZAMAN KLONLARI", "Arkanda bıraktığın renkli izleri keşfet!", renk=CAMGOBEGI)

        # "HARİKA!" Dans tebrik pop yazısı
        if harika_aktif:
            gecen_harika = simdi - self.son_harika_zamani
            olcek = 1.0 + 0.25 * float(np.sin(gecen_harika * np.pi))
            panel(kare, G // 2 - 200, 130, G // 2 + 200, 205, renk=(25, 10, 35), opak=0.85, kenar=SARI)
            yazi_koy(kare, "HARİKA!", G // 2, 142, 52, renk=SARI, hiza="orta", olcek=olcek)

        # Sol alt mod ve yankı paneli
        panel(kare, 30, Y - 95, 340, Y - 25, renk=(18, 18, 28), opak=0.8, kenar=PEMBE)
        yazi_koy(kare, "MOD:", 45, Y - 78, 20, renk=SARI)
        mod_renk = (
            CAMGOBEGI
            if self.mod == "Neon"
            else (YESIL if self.mod == "Klon" else PEMBE)
        )
        yazi_koy(kare, self.mod.upper(), 105, Y - 83, 26, renk=mod_renk)
        kalan_sure = max(0, int(15.0 - (simdi - self.son_mod_degisim)))
        yazi_koy(kare, f"({kalan_sure}s)", 245, Y - 78, 18, renk=(180, 180, 200))
        yazi_koy(kare, f"Yankı: {self.yanki_sayisi}x", 45, Y - 48, 18, renk=BEYAZ)
        yazi_koy(kare, "[Boşluk] Değiştir", 175, Y - 48, 16, renk=CAMGOBEGI)

        # Vitrin davet ekranı (Kimse yokken veya hareketsizken)
        if not kisi_var:
            nabiz = 0.75 + 0.25 * float(np.sin(simdi * 4.0))
            panel(
                kare,
                G // 2 - 380,
                Y // 2 + 50,
                G // 2 + 380,
                Y // 2 + 185,
                renk=(14, 14, 24),
                opak=0.75,
                kenar=PEMBE,
            )
            yazi_koy(
                kare,
                "Önümden geç, klonlarını gör!",
                G // 2,
                Y // 2 + 70,
                46,
                renk=BEYAZ,
                hiza="orta",
                opak=nabiz,
            )
            yazi_koy(
                kare,
                "Dans et, kollarını aç ve izle",
                G // 2,
                Y // 2 + 132,
                26,
                renk=CAMGOBEGI,
                hiza="orta",
                opak=nabiz * 0.9,
            )
        elif self.hareket_skor < 0.008:
            nabiz = 0.7 + 0.3 * float(np.sin(simdi * 4.0))
            panel(
                kare,
                G // 2 - 280,
                Y // 2 + 70,
                G // 2 + 280,
                Y // 2 + 165,
                renk=(14, 14, 24),
                opak=0.7,
                kenar=CAMGOBEGI,
            )
            yazi_koy(
                kare,
                "Daha hızlı hareket et!",
                G // 2,
                Y // 2 + 85,
                36,
                renk=SARI,
                hiza="orta",
                opak=nabiz,
            )
            yazi_koy(
                kare,
                "Yankıların çoğalacak",
                G // 2,
                Y // 2 + 130,
                22,
                renk=BEYAZ,
                hiza="orta",
                opak=nabiz * 0.85,
            )

        return kare
