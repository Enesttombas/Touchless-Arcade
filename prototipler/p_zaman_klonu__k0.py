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
        self.mod = "Neon"  # "Neon" veya "Klon"
        self.son_mod_degisim = None
        self.onceki_simdi = None

        self.maskeci = Maskeci()

        # Yedek MOG2 ön plan çıkarıcı
        self.mog = cv2.createBackgroundSubtractorMOG2(
            history=300, varThreshold=32, detectShadows=False
        )
        self.cekirdek_kenar = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # Son 36 kare (640x360 uint8 BGR) ve yumuşak maskeleri (360x640 float32 0..1)
        self.tampon = deque(maxlen=36)
        self.gecikmeler = [30, 24, 18, 12, 6]

        # 5 yankı için neon renkler (en eskiden yeniye veya tersi fark etmez, tutarlı sıra)
        renk_listesi = [
            PEMBE,
            (255, 80, 160),  # Mor
            CAMGOBEGI,
            SARI,
            YESIL,
        ]
        self.renkler = [np.array(r, dtype=np.float32) for r in renk_listesi]
        self.renk_katmanlari_f32 = [
            np.full((360, 640, 3), r, dtype=np.float32) for r in renk_listesi
        ]

        self.onceki_maske = None
        self.hareket_skor = 0.0

    def tus(self, k: int) -> None:
        if k == 32:  # Boşluk tuşu
            self._mod_degistir()

    def _mod_degistir(self, simdi: float = None) -> None:
        self.mod = "Klon" if self.mod == "Neon" else "Neon"
        if simdi is not None:
            self.son_mod_degisim = simdi
        self.ses.cal("woosh", 0.6)

    def _maske_cikar(self, kare: np.ndarray, kare_yarim: np.ndarray) -> np.ndarray:
        m = self.maskeci.ver(kare)
        if m is not None:
            # 0.5 eşiği etrafında yumuşat ve 5x5 Gauss uygula
            yumusak = np.clip((m - 0.35) / 0.3, 0.0, 1.0).astype(np.float32)
            yumusak = cv2.GaussianBlur(yumusak, (5, 5), 0)
            return yumusak

        # Yedek: MOG2 (altıgen leke bırakmadan yumuşak geçişli)
        kare_ceyrek = cv2.resize(kare_yarim, (320, 180), interpolation=cv2.INTER_AREA)
        fg_ceyrek = self.mog.apply(kare_ceyrek)
        fg_f32 = fg_ceyrek.astype(np.float32) * (1.0 / 255.0)
        fg_f32 = cv2.GaussianBlur(fg_f32, (7, 7), 0)
        fg_yarim = cv2.resize(fg_f32, (640, 360), interpolation=cv2.INTER_LINEAR)
        yumusak = np.clip((fg_yarim - 0.35) / 0.3, 0.0, 1.0).astype(np.float32)
        yumusak = cv2.GaussianBlur(yumusak, (5, 5), 0)
        return yumusak

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        if self.son_mod_degisim is None:
            self.son_mod_degisim = simdi

        dt = 0.033
        if self.onceki_simdi is not None:
            dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        if simdi - self.son_mod_degisim >= 15.0:
            self._mod_degistir(simdi)

        # Yarım çözünürlük (640x360)
        kare_yarim = cv2.resize(kare, (640, 360), interpolation=cv2.INTER_LINEAR)
        maske = self._maske_cikar(kare, kare_yarim)

        # Son 2 sn maskeler arası fark ile hareket takibi
        if self.onceki_maske is not None:
            fark = float(np.mean(np.abs(maske - self.onceki_maske)))
        else:
            fark = float(np.mean(maske)) * 0.1
        self.onceki_maske = maske

        # ~2 sn zaman sabitiyle üstel yumuşatma
        alfa_h = min(1.0, dt * 1.5)
        self.hareket_skor += (fark - self.hareket_skor) * alfa_h

        # Halka tampona kaydet
        self.tampon.append((kare_yarim, maske))
        tampon_uzunluk = len(self.tampon)

        # Arka plan: güncel kare %45 karartılmış (0.55 çarpanı)
        # Karışımlar cv2.blendLinear ile uint8'de (float32 numpy kare başı ~120 ms tutuyordu)
        komp = cv2.convertScaleAbs(kare_yarim, alpha=0.55)
        if not hasattr(self, "_renk_u8"):
            self._renk_u8 = [r.astype(np.uint8) for r in self.renk_katmanlari_f32]

        neon_katman = (
            np.zeros((360, 640, 3), dtype=np.uint8) if self.mod == "Neon" else None
        )

        # 5 yankı: gecikmeler 30, 24, 18, 12, 6 (en eskiden yeniye çizilir)
        # Yankı i (0=6 kare .. 4=30 kare) opaklığı: 0.75 - 0.12 * i
        for cizim_idx, gecikme in enumerate(self.gecikmeler):
            if tampon_uzunluk <= gecikme:
                continue

            eski_kare, eski_maske = self.tampon[-1 - gecikme]
            if float(eski_maske.max()) < 0.02:
                continue

            # i: 0 en yeni yankı (gecikme 6), 4 en eski yankı (gecikme 30)
            yanki_i = 4 - cizim_idx
            opaklik = 0.75 - 0.12 * yanki_i

            w = eski_maske * opaklik

            if self.mod == "Neon":
                boyali = cv2.addWeighted(self._renk_u8[yanki_i], 0.75, eski_kare, 0.25, 0)
                komp = cv2.blendLinear(komp, boyali, 1.0 - w, w)

                # Dış kontur: dilate(maske) - maske
                genis = cv2.dilate(eski_maske, self.cekirdek_kenar)
                kenar1 = cv2.convertScaleAbs(cv2.subtract(genis, eski_maske), alpha=1.6 * 255)
                r = self.renkler[yanki_i] / 255.0
                kenar_u8 = cv2.multiply(cv2.cvtColor(kenar1, cv2.COLOR_GRAY2BGR),
                                        (float(r[0]), float(r[1]), float(r[2]), 0.0))
                cv2.max(neon_katman, kenar_u8, dst=neon_katman)
            else:
                # Klon modu: renksiz gerçek kopyalar, opaklık aynı
                komp = cv2.blendLinear(komp, eski_kare, 1.0 - w, w)

        # En üstte güncel kişi maskesiyle gerçek renkli
        komp = cv2.blendLinear(komp, kare_yarim, 1.0 - maske, maske)

        # Neon modunda kenar parıltısı
        if self.mod == "Neon" and neon_katman is not None:
            parilti(komp, neon_katman, guc=1.8, sigma=2.8)

        # Tam çözünürlüğe büyüt
        cv2.resize(komp, (G, Y), dst=kare, interpolation=cv2.INTER_LINEAR)

        # Üst başlık
        baslik(kare, "ZAMAN KLONLARI", "Hareket et, zaman yankılarını izle", renk=CAMGOBEGI)

        # Sol alt mod paneli
        panel(kare, 30, Y - 85, 285, Y - 25, renk=(18, 18, 28), opak=0.75, kenar=PEMBE)
        yazi_koy(kare, "MOD:", 45, Y - 68, 22, renk=SARI)
        mod_renk = CAMGOBEGI if self.mod == "Neon" else YESIL
        yazi_koy(kare, self.mod.upper(), 112, Y - 72, 28, renk=mod_renk)

        kalan_sure = max(0, int(15.0 - (simdi - self.son_mod_degisim)))
        yazi_koy(kare, f"({kalan_sure}s)", 220, Y - 67, 20, renk=(190, 190, 205))

        # Hareket yokken ortada davet yazısı
        if self.hareket_skor < 0.008:
            nabiz = 0.75 + 0.25 * float(np.sin(simdi * 4.5))
            panel(
                kare,
                G // 2 - 310,
                Y // 2 + 30,
                G // 2 + 310,
                Y // 2 + 145,
                renk=(15, 15, 24),
                opak=0.65,
                kenar=CAMGOBEGI,
            )
            yazi_koy(
                kare,
                "Dans et, klonlarını gör!",
                G // 2,
                Y // 2 + 45,
                42,
                renk=BEYAZ,
                hiza="orta",
                opak=nabiz,
            )
            yazi_koy(
                kare,
                "[Boşluk] tuşu ile modu değiştir",
                G // 2,
                Y // 2 + 102,
                22,
                renk=CAMGOBEGI,
                hiza="orta",
                opak=nabiz * 0.85,
            )

        return kare
