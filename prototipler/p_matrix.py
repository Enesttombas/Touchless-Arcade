import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    KIRMIZI,
    Maskeci,
    Parcaciklar,
    SARI,
    YESIL,
    Y,
    on_plan,
    panel,
    px,
    yazi_koy,
)

CELL = 16
COLS = G // CELL  # 80
ROWS = Y // CELL  # 45


class Prototip:
    AD = "Matrix Ayna"
    ACIKLAMA = "Matrix kod yağmuruna dönüş; elini kaldır ve zamanı yavaşlat!"
    IHTIYAC = set()
    SIRA = 12

    TEMALAR = ["Yeşil", "Camgöbeği", "Kırmızı"]

    def __init__(self, ses):
        self.ses = ses
        self.tema_idx = 0
        self.tema = self.TEMALAR[self.tema_idx]

        self.onceki_simdi = None
        self.son_tus_t = -10.0
        self.hiz_carpani = 1.0
        self.yavasladi_onceki = False

        self.parcaciklar = Parcaciklar(80)
        self.maskeci = Maskeci()

        # 48 gliflik 16x16 karakter atlası oluşturma
        self.atlas = self._olustur_atlas()
        self.n_glif = self.atlas.shape[0]

        # Sütun yağmur durumları
        rng = np.random.RandomState(42)
        self.col_y = rng.uniform(-ROWS, ROWS, size=COLS).astype(np.float32)
        self.col_speed = rng.uniform(16.0, 36.0, size=COLS).astype(np.float32)
        self.col_len = rng.uniform(9.0, 22.0, size=COLS).astype(np.float32)

        # Izgara glif indeksleri
        self.grid_glifler = rng.randint(0, self.n_glif, size=(ROWS, COLS), dtype=np.int32)

        # Satır indeksleri (yayınım hesabı için)
        self.satirlar = np.arange(ROWS, dtype=np.float32)[:, None]  # (45, 1)

        # Renk temaları için LUT'lar (1, 256, 3) BGR
        self.lutlar = self._olustur_lutlar()

    def _olustur_atlas(self) -> np.ndarray:
        karakterler = (
            "0123456789"
            "ABCDEFHKMNPRTXYZ"
            "793542#*+=-:<>|/"
        )
        glifler = []
        for ch in karakterler:
            tuval = np.zeros((CELL, CELL), dtype=np.uint8)
            cv2.putText(
                tuval,
                ch,
                (2, 13),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.46,
                255,
                1,
                cv2.LINE_AA,
            )
            glifler.append(tuval)

        # Prosedürel Katakana / Matrix sembolleri (9 adet)
        for i in range(9):
            tuval = np.zeros((CELL, CELL), dtype=np.uint8)
            if i == 0:  # Ters T
                cv2.line(tuval, (3, 4), (13, 4), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (8, 4), (8, 13), 255, 1, cv2.LINE_AA)
            elif i == 1:  # Çapraz ve yatay
                cv2.line(tuval, (2, 8), (14, 8), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (11, 3), (4, 13), 255, 1, cv2.LINE_AA)
            elif i == 2:  # Kanca
                cv2.line(tuval, (4, 3), (4, 13), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (4, 13), (12, 13), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (12, 13), (12, 8), 255, 1, cv2.LINE_AA)
            elif i == 3:  # İki yatay, bir dikey
                cv2.line(tuval, (3, 4), (13, 4), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (4, 12), (12, 12), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (8, 4), (8, 12), 255, 1, cv2.LINE_AA)
            elif i == 4:  # Kutu
                cv2.rectangle(tuval, (4, 4), (12, 12), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (4, 8), (12, 8), 255, 1, cv2.LINE_AA)
            elif i == 5:  # Zikzak
                cv2.line(tuval, (3, 4), (13, 4), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (13, 4), (3, 12), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (3, 12), (13, 12), 255, 1, cv2.LINE_AA)
            elif i == 6:  # Açı
                cv2.line(tuval, (3, 3), (13, 8), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (13, 8), (3, 13), 255, 1, cv2.LINE_AA)
            elif i == 7:  # Çift çizgi
                cv2.line(tuval, (3, 5), (13, 5), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (3, 11), (13, 11), 255, 1, cv2.LINE_AA)
            else:  # Yıldız
                cv2.line(tuval, (8, 3), (8, 13), 255, 1, cv2.LINE_AA)
                cv2.line(tuval, (3, 8), (13, 8), 255, 1, cv2.LINE_AA)
            glifler.append(tuval)

        return np.stack(glifler, axis=0)

    def _olustur_lutlar(self) -> dict:
        lutlar = {}
        for tema in self.TEMALAR:
            lut = np.zeros((1, 256, 3), dtype=np.uint8)
            for i in range(256):
                if i < 14:
                    lut[0, i] = [0, 0, 0]
                elif i < 200:
                    oran = (i - 14) / 186.0
                    if tema == "Yeşil":
                        b = int(oran * 35)
                        g = int(oran * 230 + 20)
                        r = int(oran * 25)
                    elif tema == "Camgöbeği":
                        b = int(oran * 230 + 20)
                        g = int(oran * 210 + 15)
                        r = int(oran * 30)
                    else:  # Kırmızı
                        b = int(oran * 30)
                        g = int(oran * 35)
                        r = int(oran * 230 + 20)
                    lut[0, i] = [min(255, b), min(255, g), min(255, r)]
                else:
                    w = (i - 200) / 55.0
                    if tema == "Yeşil":
                        b = int(35 + w * 220)
                        g = 255
                        r = int(25 + w * 230)
                    elif tema == "Camgöbeği":
                        b = 255
                        g = int(225 + w * 30)
                        r = int(30 + w * 225)
                    else:  # Kırmızı
                        b = int(30 + w * 225)
                        g = int(35 + w * 220)
                        r = 255
                    lut[0, i] = [min(255, b), min(255, g), min(255, r)]
            lutlar[tema] = lut
        return lutlar

    def tus(self, k: int) -> None:
        if k == 32:  # Boşluk: Renk teması döngüsü
            self.tema_idx = (self.tema_idx + 1) % len(self.TEMALAR)
            self.tema = self.TEMALAR[self.tema_idx]
            self.son_tus_t = getattr(self, "_simdi", 0.0)
            self.ses.cal("zap", 0.6)

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        self._simdi = simdi
        if self.onceki_simdi is None:
            self.onceki_simdi = simdi
        dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1)
        self.onceki_simdi = simdi

        # 1. El kaldırma ve kişi kontrolü (Zamanı yavaşlatma)
        el_kalkti = False
        kisi_var = False
        el_pos = None

        if algi is not None:
            if getattr(algi, "yuzler", None):
                kisi_var = True
            if getattr(algi, "pozlar", None):
                kisi_var = True

            eller = getattr(algi, "eller", None) or []
            jestler = getattr(algi, "jestler", None) or []
            if eller:
                kisi_var = True
                # En yüksek el kontrolü
                for idx_el, el in enumerate(eller):
                    if len(el) > 8:
                        isaret = el[8]
                        if isaret.y < 0.45:
                            el_kalkti = True
                            el_pos = px(el, 8)
                    if idx_el < len(jestler):
                        j = jestler[idx_el]
                        if j in ("Pointing_Up", "Victory", "Open_Palm"):
                            if len(el) > 9 and el[9].y < 0.55:
                                el_kalkti = True
                                el_pos = px(el, 9)

        # Hız çarpanı yumuşatma (Bullet time)
        hedef_hiz = 0.25 if el_kalkti else 1.0
        self.hiz_carpani += (hedef_hiz - self.hiz_carpani) * min(1.0, dt * 8.0)

        if el_kalkti and not self.yavasladi_onceki:
            self.ses.cal("woosh", 0.5)
            if el_pos is not None:
                self.parcaciklar.yay(int(el_pos[0]), int(el_pos[1]), 16, renk=CAMGOBEGI, hiz=4.5)
        self.yavasladi_onceki = el_kalkti

        # 2. Matrix Yağmur Simülasyonu (Vektörize)
        self.col_y += self.col_speed * (dt * self.hiz_carpani)
        # Sütun sıfırlama
        bitti = (self.col_y - self.col_len) > ROWS
        if np.any(bitti):
            n_bitti = np.count_nonzero(bitti)
            self.col_y[bitti] = np.random.uniform(-14.0, 0.0, size=n_bitti)
            self.col_speed[bitti] = np.random.uniform(16.0, 36.0, size=n_bitti)
            self.col_len[bitti] = np.random.uniform(9.0, 22.0, size=n_bitti)

        # Baş mesafesi: (45, 80)
        d = self.col_y[None, :] - self.satirlar  # d = 0 baş noktası, d > 0 kuyruk
        uzunluk = np.broadcast_to(self.col_len[None, :], (ROWS, COLS))

        kuyruk_mask = (d >= 0.0) & (d < uzunluk)
        kuyruk_parlaklik = np.zeros((ROWS, COLS), dtype=np.float32)
        kuyruk_parlaklik[kuyruk_mask] = 1.0 - (d[kuyruk_mask] / uzunluk[kuyruk_mask])

        # Baş noktaları (parlak beyaz)
        bas_mask = (d >= 0.0) & (d < 1.3)

        # Glif rastgele değişimi (~%6 her kare)
        degis_mask = np.random.rand(ROWS, COLS) < 0.06
        degis_mask |= bas_mask
        if np.any(degis_mask):
            self.grid_glifler[degis_mask] = np.random.randint(
                0, self.n_glif, size=np.count_nonzero(degis_mask)
            )

        # 3. Kamera Parlaklığı ve Maske
        kare_gri = cv2.cvtColor(kare, cv2.COLOR_BGR2GRAY)
        kucuk_gri = cv2.resize(kare_gri, (COLS, ROWS), interpolation=cv2.INTER_AREA)
        kamera_norm = kucuk_gri.astype(np.float32) * (1.0 / 255.0)

        # Kişi silueti: Maskeci veya parlaklık
        siluet = None
        if self.maskeci is not None:
            m = self.maskeci.ver(kare)
            if m is not None:
                m_filtre = on_plan(m)
                siluet = cv2.resize(m_filtre, (COLS, ROWS), interpolation=cv2.INTER_LINEAR)
                if np.mean(siluet) > 0.02:
                    kisi_var = True

        if siluet is None:
            siluet = np.clip((kamera_norm - 0.28) / 0.5, 0.0, 1.0)

        # 4. Nihai Hücre Yoğunluğu Hesabı (0..255 uint8)
        # Kişi siluetinde karakterler daha yoğun ve parlak
        arka_plan = kuyruk_parlaklik * (0.35 + 0.65 * kamera_norm)
        insan_kodu = np.maximum(kuyruk_parlaklik * 0.8, 0.45) * kamera_norm + 0.35 * siluet
        birlesik = np.where(siluet > 0.35, np.maximum(arka_plan, insan_kodu), arka_plan)
        birlesik = np.clip(birlesik * 190.0, 0.0, 195.0)

        # Baş hücreleri en tepe parlaklığa (205..255 = beyaz)
        birlesik[bas_mask] = np.random.uniform(220.0, 255.0, size=np.count_nonzero(bas_mask))
        hucre_parlaklik = birlesik.astype(np.uint8)

        # 5. Vektörize Karo Dizme & Renklendirme
        ekran_glifler = self.atlas[self.grid_glifler].transpose(0, 2, 1, 3).reshape(Y, G)
        ekran_parlaklik = cv2.resize(hucre_parlaklik, (G, Y), interpolation=cv2.INTER_NEAREST)

        modul_gri = cv2.multiply(ekran_glifler, ekran_parlaklik, scale=1.0 / 255.0)
        modul_bgr = cv2.cvtColor(modul_gri, cv2.COLOR_GRAY2BGR)

        # Tema LUT uygulaması
        lut = self.lutlar[self.tema]
        sonuc = cv2.LUT(modul_bgr, lut)

        # 6. Parçacıklar
        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(sonuc)

        # 7. Arayüz: Kimse yokken davet, mod değişimi geri bildirimi
        if not kisi_var:
            # Nabız atan davet paneli
            nabiz = 0.5 + 0.5 * np.sin(simdi * 3.5)
            opaklik = 0.65 + 0.15 * nabiz
            panel(sonuc, G // 2 - 270, Y // 2 - 45, G // 2 + 270, Y // 2 + 45, renk=(12, 18, 14), opak=opaklik, kenar=YESIL)
            yazi_koy(sonuc, "Matrix'e Adım At", G // 2, Y // 2 - 26, 38, renk=BEYAZ, hiza="orta")
            yazi_koy(sonuc, "Kameraya yaklaş • Elini kaldır", G // 2, Y // 2 + 14, 20, renk=SARI, hiza="orta")
        elif el_kalkti:
            # Zaman yavaşlatıldı göstergesi
            panel(sonuc, G // 2 - 130, 20, G // 2 + 130, 56, renk=(12, 18, 14), opak=0.6, kenar=CAMGOBEGI)
            yazi_koy(sonuc, "ZAMAN YAVAŞLADI", G // 2, 27, 20, renk=CAMGOBEGI, hiza="orta")

        # Kısa tema geçiş bildirimi (tuşa basıldıktan sonra 1.5 sn)
        if simdi - self.son_tus_t < 1.5:
            panel(sonuc, 24, Y - 60, 200, Y - 20, renk=(10, 10, 16), opak=0.7)
            tema_renk = YESIL if self.tema == "Yeşil" else (CAMGOBEGI if self.tema == "Camgöbeği" else KIRMIZI)
            yazi_koy(sonuc, f"Tema: {self.tema}", 34, Y - 52, 22, renk=tema_renk, hiza="sol")

        return sonuc
