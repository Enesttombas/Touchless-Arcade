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

    MODLAR = ["Neon", "Klon", "Gökkuşağı"]

    def __init__(self, ses):
        self.ses = ses
        self.mod = "Neon"
        self.yanki_sayisi = 3
        self._yanki_sayisi_f = 3.0

        self.son_mod_degisim = None
        self.onceki_simdi = None
        self.baslangic_zamani = None

        self.maskeci = Maskeci()
        self.maskeci_hazir = False

        # MOG2 ön plan çıkarıcı (yalnız Maskeci 4 sn boyunca None dönerse devreye girer)
        self.mog = cv2.createBackgroundSubtractorMOG2(
            history=300, varThreshold=32, detectShadows=False
        )
        self.cekirdek_kenar = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # En çok 42 karelik tampon (7 yankı * 5 kare aralık + pay)
        self.tampon = deque(maxlen=45)

        # 7 yankı için sabit neon paleti (BGR)
        neon_renkler = [
            (255, 60, 180),   # Neon Pembe
            (255, 80, 240),   # Macenta
            (255, 120, 80),   # Mavi / Mor
            (255, 230, 60),   # Camgöbeği
            (80, 240, 180),   # Turkuaz
            (60, 240, 60),    # Yeşil
            (0, 220, 255),    # Sarı
        ]
        self.neon_bgr = [np.array(r, dtype=np.float32) for r in neon_renkler]
        self._neon_katman_u8 = [
            np.full((360, 640, 3), r, dtype=np.uint8) for r in neon_renkler
        ]

        self.onceki_maske = None
        self.hareket_skor = 0.0

        # Dans ödülü "HARİKA!" pop bildirimi
        self.son_harika_zamani = -10.0
        self.harika_gosterim_son = -10.0

        # Vitrin (kimse yokken son kişinin 2 sn'lik hayalet kaydı)
        self.hayalet_tampon = deque(maxlen=60)
        self.hayalet_idx = 0
        self.bos_sure = 0.0
        self.vitrin_alfa = 0.0

    def tus(self, k: int) -> None:
        if k == 32:  # Boşluk tuşu
            self._sonraki_mod()

    def _sonraki_mod(self, simdi: float = None) -> None:
        curr_idx = self.MODLAR.index(self.mod)
        self.mod = self.MODLAR[(curr_idx + 1) % len(self.MODLAR)]
        if simdi is not None:
            self.son_mod_degisim = simdi
        self.ses.cal("woosh", 0.6)

    def _maske_cikar(self, kare: np.ndarray, kare_yarim: np.ndarray, simdi: float) -> np.ndarray:
        m = self.maskeci.ver(kare)
        if m is not None:
            self.maskeci_hazir = True
            yumusak = np.clip((m - 0.35) / 0.3, 0.0, 1.0).astype(np.float32)
            return cv2.GaussianBlur(yumusak, (5, 5), 0)

        # Maskeci henüz hazır değil ve 4 sn dolmadıysa maske üretme
        if not self.maskeci_hazir and (simdi - self.baslangic_zamani < 4.0):
            return None

        # 4 sn sonra hala Maskeci yoksa MOG2 yedek devreye girer
        kare_ceyrek = cv2.resize(kare_yarim, (320, 180), interpolation=cv2.INTER_AREA)
        fg_ceyrek = self.mog.apply(kare_ceyrek)
        fg_f32 = fg_ceyrek.astype(np.float32) * (1.0 / 255.0)
        fg_f32 = cv2.GaussianBlur(fg_f32, (7, 7), 0)
        fg_yarim = cv2.resize(fg_f32, (640, 360), interpolation=cv2.INTER_LINEAR)
        yumusak = np.clip((fg_yarim - 0.35) / 0.3, 0.0, 1.0).astype(np.float32)
        return cv2.GaussianBlur(yumusak, (5, 5), 0)

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        if self.baslangic_zamani is None:
            self.baslangic_zamani = simdi
        if self.son_mod_degisim is None:
            self.son_mod_degisim = simdi

        dt = 0.033
        if self.onceki_simdi is not None:
            dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        # 15 saniyede bir otomatik mod döngüsü
        if simdi - self.son_mod_degisim >= 15.0:
            self._sonraki_mod(simdi)

        # Yarım çözünürlükte çalış (640x360)
        kare_yarim = cv2.resize(kare, (640, 360), interpolation=cv2.INTER_LINEAR)
        maske = self._maske_cikar(kare, kare_yarim, simdi)

        # 1. Açılış lekesi koruması: Maskeci hazır değilken yankı çizme
        if maske is None:
            karartilmis = cv2.convertScaleAbs(kare, alpha=0.5)
            yazi_koy(
                karartilmis,
                "Hazırlanıyor...",
                G // 2,
                Y // 2,
                34,
                renk=CAMGOBEGI,
                hiza="orta",
                opak=0.8 + 0.2 * float(np.sin(simdi * 6.0)),
            )
            return karartilmis

        # Maske doluluk oranı ve hareket hesaplama
        maske_alani = float(np.mean(maske > 0.15))
        if self.onceki_maske is not None:
            fark = float(np.mean(np.abs(maske - self.onceki_maske)))
        else:
            fark = float(np.mean(maske)) * 0.1
        self.onceki_maske = maske

        alfa_h = min(1.0, dt * 1.8)
        self.hareket_skor += (fark - self.hareket_skor) * alfa_h

        # 2. Dans ödülü: hareket skoruyla yankı sayısı 3 -> 7 arası dinamik
        hareket_norm = np.clip((self.hareket_skor - 0.006) / 0.024, 0.0, 1.0)
        hedef_yanki = 3.0 + 4.0 * hareket_norm
        self._yanki_sayisi_f += (hedef_yanki - self._yanki_sayisi_f) * min(1.0, dt * 3.0)
        self.yanki_sayisi = int(round(self._yanki_sayisi_f))
        self.yanki_sayisi = max(3, min(7, self.yanki_sayisi))

        # Üst %20 çok yüksek hareket: "HARİKA!" pop bildirimi (en sık 4 sn'de bir)
        if hareket_norm >= 0.80 and (simdi - self.son_harika_zamani >= 4.0):
            self.son_harika_zamani = simdi
            self.harika_gosterim_son = simdi + 1.0
            self.ses.cal("basari", 0.75)

        # 3. Vitrin yönetimi (kimse yokken hayalet tekrar oynatımı)
        kisi_var = maske_alani >= 0.02
        if kisi_var:
            self.bos_sure = 0.0
            self.hayalet_tampon.append((kare_yarim.copy(), maske.copy()))
        else:
            self.bos_sure += dt

        vitrin_hedef = 1.0 if (self.bos_sure >= 1.5 and len(self.hayalet_tampon) >= 15) else 0.0
        # Kişi girince 0.3 sn'de sönsün (hız ~1.0 / 0.3 = 3.3)
        hiz = 1.8 if vitrin_hedef > self.vitrin_alfa else 3.5
        self.vitrin_alfa += (vitrin_hedef - self.vitrin_alfa) * min(1.0, dt * hiz)

        # Halka tampona ekle
        self.tampon.append((kare_yarim, maske))
        tampon_len = len(self.tampon)

        # Arka plan: güncel kare %45 karartılmış (0.55 çarpanı)
        komp = cv2.convertScaleAbs(kare_yarim, alpha=0.55)

        neon_katman = (
            np.zeros((360, 640, 3), dtype=np.uint8)
            if self.mod in ("Neon", "Gökkuşağı")
            else None
        )

        # Vitrin hayaleti arka plana hafifçe bindirilir
        if self.vitrin_alfa > 0.02:
            self.hayalet_idx = (self.hayalet_idx + 1) % len(self.hayalet_tampon)
            h_kare, h_maske = self.hayalet_tampon[self.hayalet_idx]
            h_w = h_maske * (0.35 * self.vitrin_alfa)
            # Hayalet neon camgöbeği/pembe karışımı
            h_boyali = cv2.addWeighted(h_kare, 0.4, self._neon_katman_u8[0], 0.6, 0)
            komp = cv2.blendLinear(komp, h_boyali, 1.0 - h_w, h_w)

        # Yankılar: 5 kare aralıklı, en eskiden yeniye doğru çizilir
        # yanki_sayisi kadar gecikme: örn 5 yankı -> 25, 20, 15, 10, 5
        gecikmeler = [ (i + 1) * 5 for i in range(self.yanki_sayisi) ]
        gecikmeler.reverse()

        for cizim_sira, gecikme in enumerate(gecikmeler):
            if tampon_len <= gecikme:
                continue

            eski_kare, eski_maske = self.tampon[-1 - gecikme]
            if float(eski_maske.max()) < 0.03:
                continue

            # yanki_k: 0 en yeni, yanki_sayisi-1 en eski
            yanki_k = len(gecikmeler) - 1 - cizim_sira
            opaklik = max(0.2, 0.78 - 0.09 * yanki_k)
            w = eski_maske * opaklik

            if self.mod == "Neon":
                renk_idx = yanki_k % len(self._neon_katman_u8)
                boyali = cv2.addWeighted(
                    self._neon_katman_u8[renk_idx], 0.72, eski_kare, 0.28, 0
                )
                komp = cv2.blendLinear(komp, boyali, 1.0 - w, w)

                # Dış kontur
                genis = cv2.dilate(eski_maske, self.cekirdek_kenar)
                kenar_mask = cv2.convertScaleAbs(
                    cv2.subtract(genis, eski_maske), alpha=1.5 * 255
                )
                r_katman = self._neon_katman_u8[renk_idx]
                kenar_bgr = cv2.bitwise_and(r_katman, r_katman, mask=kenar_mask)
                cv2.max(neon_katman, kenar_bgr, dst=neon_katman)

            elif self.mod == "Gökkuşağı":
                # Ton döngüsü: zamanla kayan hue
                ton = int((simdi * 55.0 + yanki_k * (180.0 / self.yanki_sayisi)) % 180)
                hsv_piksel = np.uint8([[[ton, 240, 255]]])
                gok_bgr = cv2.cvtColor(hsv_piksel, cv2.COLOR_HSV2BGR)[0, 0]
                gok_katman = np.full((360, 640, 3), gok_bgr, dtype=np.uint8)

                boyali = cv2.addWeighted(gok_katman, 0.70, eski_kare, 0.30, 0)
                komp = cv2.blendLinear(komp, boyali, 1.0 - w, w)

                genis = cv2.dilate(eski_maske, self.cekirdek_kenar)
                kenar_mask = cv2.convertScaleAbs(
                    cv2.subtract(genis, eski_maske), alpha=1.5 * 255
                )
                kenar_bgr = cv2.bitwise_and(gok_katman, gok_katman, mask=kenar_mask)
                cv2.max(neon_katman, kenar_bgr, dst=neon_katman)

            else:
                # Klon modu: renksiz doğal kopyalar
                komp = cv2.blendLinear(komp, eski_kare, 1.0 - w, w)

        # En üstte güncel kişi maskesiyle gerçek renkli görüntü
        komp = cv2.blendLinear(komp, kare_yarim, 1.0 - maske, maske)

        # Neon / Gökkuşağı modunda kenar parıltısı
        if neon_katman is not None:
            parilti(komp, neon_katman, guc=1.7, sigma=2.6)

        # Tam çözünürlüğe ölçekle
        cv2.resize(komp, (G, Y), dst=kare, interpolation=cv2.INTER_LINEAR)

        # 5. Başlık tek çağrı
        baslik(kare, "ZAMAN KLONLARI", "Hareket et, zaman yankılarını izle", renk=CAMGOBEGI)

        # Dans ödülü: HARİKA! pop bildirimi
        if simdi < self.harika_gosterim_son:
            pop_oran = (self.harika_gosterim_son - simdi) / 1.0
            pop_olcek = 1.0 + 0.15 * float(np.sin(pop_oran * np.pi))
            panel(
                kare,
                G // 2 - 130,
                118,
                G // 2 + 130,
                175,
                renk=(24, 20, 36),
                opak=0.85,
                kenar=SARI,
            )
            yazi_koy(
                kare,
                "HARİKA!",
                G // 2,
                126,
                38,
                renk=SARI,
                hiza="orta",
                olcek=pop_olcek,
            )

        # Sol alt mod paneli (başlıkla çakışma yok)
        panel(kare, 30, Y - 85, 330, Y - 25, renk=(18, 18, 28), opak=0.75, kenar=PEMBE)
        yazi_koy(kare, "MOD:", 45, Y - 68, 20, renk=SARI)
        if self.mod == "Neon":
            m_renk = CAMGOBEGI
        elif self.mod == "Gökkuşağı":
            m_renk = PEMBE
        else:
            m_renk = YESIL
        yazi_koy(kare, self.mod.upper(), 105, Y - 72, 26, renk=m_renk)

        kalan = max(0, int(15.0 - (simdi - self.son_mod_degisim)))
        yazi_koy(kare, f"({kalan}s)", 235, Y - 67, 19, renk=(190, 190, 205))
        yazi_koy(kare, f"Klon: {self.yanki_sayisi}", 282, Y - 67, 19, renk=SARI)

        # 3. Vitrin: Kimse yokken (veya çok hareketsizken) nabız atan Türkçe davet
        if not kisi_var or self.hareket_skor < 0.007:
            nabiz = 0.75 + 0.25 * float(np.sin(simdi * 4.5))
            panel(
                kare,
                G // 2 - 330,
                Y // 2 + 30,
                G // 2 + 330,
                Y // 2 + 150,
                renk=(15, 15, 24),
                opak=0.70,
                kenar=CAMGOBEGI,
            )
            yazi_koy(
                kare,
                "Önümden geç, klonlarını gör!",
                G // 2,
                Y // 2 + 45,
                42,
                renk=BEYAZ,
                hiza="orta",
                opak=nabiz,
            )
            yazi_koy(
                kare,
                "Dans et, kollarını aç • [Boşluk] Mod Değiştir",
                G // 2,
                Y // 2 + 105,
                22,
                renk=CAMGOBEGI,
                hiza="orta",
                opak=nabiz * 0.9,
            )

        return kare
