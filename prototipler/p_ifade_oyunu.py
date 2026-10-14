import random
import cv2
import numpy as np

from cekirdek import (
    G,
    Y,
    SARI,
    CAMGOBEGI,
    PEMBE,
    YESIL,
    BEYAZ,
    KIRMIZI,
    px,
    panel,
    baslik,
    halka,
    parilti,
    yazi_koy,
    emoji_sprite,
    bindir,
    bindir_merkez,
    bulanik_karanlik,
    Parcaciklar,
)


class Prototip:
    AD = "Surat Ustası"
    ACIKLAMA = "Ekrandaki emojinin ifadesini taklit et, puanları topla!"
    IHTIYAC = {"yuz", "blend"}
    SIRA = 6

    IFADELER = {
        "Gülümse 😁": ["mouthSmileLeft", "mouthSmileRight"],
        "Şaşır 😮": ["jawOpen", "browInnerUp"],
        "Göz kırp 😉": ["eyeBlinkLeft"],
        "Öpücük 😘": ["mouthPucker"],
        "Kaş kaldır 🤨": ["browOuterUpLeft", "browOuterUpRight"],
        "Kızgın 😠": ["browDownLeft", "browDownRight"],
    }

    def __init__(self, ses):
        self.ses = ses
        self.durum = "bekle"  # "bekle" | "oyun" | "sonuc"
        self.skor = 0
        self.rekor = 0
        self.hedef = "Gülümse 😁"

        self.onceki_zaman = None
        self.yuz_goruldu_sure = 0.0
        self.oyun_baslangic = 0.0
        self.hedef_zamani = 0.0
        self.tutma_suresi = 0.0
        self.sonuc_baslangic = 0.0

        # Animasyon değişkenleri
        self.pop_anim = 0.0
        self.cubuk_yumusak = 0.0
        self.parcaciklar = Parcaciklar(tavan=160)

        # Emoji spritelarını önceden oluştur
        self.emoji_cache = {}
        for ifade in self.IFADELER:
            emoji_karakter = ifade.split()[-1]
            self.emoji_cache[ifade] = emoji_sprite(emoji_karakter, boyut=256)

    def _yeni_hedef_sec(self, simdi: float):
        secenekler = [k for k in self.IFADELER.keys() if k != self.hedef]
        self.hedef = random.choice(secenekler) if secenekler else list(self.IFADELER.keys())[0]
        self.hedef_zamani = simdi
        self.tutma_suresi = 0.0

    def isle(self, kare: np.ndarray, algi, simdi: float) -> np.ndarray:
        if self.onceki_zaman is None:
            dt = 0.033
        else:
            dt = min(max(simdi - self.onceki_zaman, 0.0), 0.1)
        self.onceki_zaman = simdi

        yuz_var = len(algi.yuzler) > 0
        blend_sozluk = algi.blend[0] if algi.blend else {}

        # ---------------- DURUM GEÇİŞLERİ ----------------
        if self.durum == "bekle":
            if yuz_var:
                self.yuz_goruldu_sure += dt
                if self.yuz_goruldu_sure >= 0.5:
                    self.durum = "oyun"
                    self.skor = 0
                    self.oyun_baslangic = simdi
                    self._yeni_hedef_sec(simdi)
                    self.pop_anim = 1.0
                    self.ses.cal("pop", 0.7)
            else:
                self.yuz_goruldu_sure = 0.0

        elif self.durum == "oyun":
            gecen = simdi - self.oyun_baslangic
            kalan = max(0.0, 30.0 - gecen)

            if kalan <= 0.0:
                self.durum = "sonuc"
                self.sonuc_baslangic = simdi
                if self.skor > self.rekor:
                    self.rekor = self.skor
                self.ses.cal("basari", 0.8)
            else:
                # Eşleşme puanı hesapla
                gerekli = self.IFADELER.get(self.hedef, [])
                if blend_sozluk and gerekli:
                    en_dusuk = min(blend_sozluk.get(ad, 0.0) for ad in gerekli)
                    anlik_oran = min(1.0, max(0.0, en_dusuk / 0.5))
                else:
                    anlik_oran = 0.0

                # Yumuşatma
                self.cubuk_yumusak += (anlik_oran - self.cubuk_yumusak) * min(1.0, dt * 15.0)

                # Başarılı tutma kontrolü
                if anlik_oran >= 0.99:
                    self.tutma_suresi += dt
                    if self.tutma_suresi >= 0.4:
                        self.skor += 1
                        self.pop_anim = 1.0
                        self.ses.cal("ding", 0.8)
                        # Konfeti parçacıkları
                        self.parcaciklar.yay(1050, 310, adet=35, hiz=5.5)
                        self._yeni_hedef_sec(simdi)
                else:
                    self.tutma_suresi = max(0.0, self.tutma_suresi - dt * 2.5)

                # Zaman aşımı kontrolü (5 sn)
                if simdi - self.hedef_zamani >= 5.0:
                    self.ses.cal("bonk", 0.6)
                    self._yeni_hedef_sec(simdi)

        elif self.durum == "sonuc":
            if simdi - self.sonuc_baslangic >= 4.0:
                self.durum = "bekle"
                self.yuz_goruldu_sure = 0.0

        # Parçacık güncelleme
        self.parcaciklar.guncelle(dt)

        # ---------------- ÇİZİM VE ARAYÜZ ----------------
        if self.durum == "bekle":
            # Çekim ekranı
            kare[:] = bulanik_karanlik(kare, 0.65)
            nabiz = 1.0 + 0.06 * np.sin(simdi * 4.0)

            panel(kare, 240, 200, 1040, 520, renk=(15, 15, 24), opak=0.75, kenar=SARI)
            yazi_koy(kare, "SURAT USTASI", G // 2, 270, 68, SARI, hiza="orta", olcek=nabiz)
            yazi_koy(kare, "Yüzünü göster, ifadeleri taklit et!", G // 2, 360, 36, BEYAZ, hiza="orta")

            if yuz_var:
                ilerleme = min(1.0, self.yuz_goruldu_sure / 0.5)
                halka(kare, G // 2, 445, ilerleme, r=32, renk=YESIL, kalinlik=6)
                yazi_koy(kare, "Hazırlanıyor...", G // 2, 490, 22, CAMGOBEGI, hiza="orta")
            else:
                yazi_koy(kare, "Kameraya bak ve standa yaklaş", G // 2, 445, 26, CAMGOBEGI, hiza="orta")

        elif self.durum == "oyun":
            # Üst bilgi çubuğu
            gecen = simdi - self.oyun_baslangic
            kalan_sure = max(0.0, 30.0 - gecen)

            panel(kare, 30, 20, 420, 100, renk=(18, 18, 28), opak=0.7, kenar=CAMGOBEGI)
            yazi_koy(kare, "SÜRE", 60, 32, 20, CAMGOBEGI, hiza="sol")
            yazi_koy(kare, f"{int(np.ceil(kalan_sure))} sn", 60, 58, 42, BEYAZ, hiza="sol")

            panel(kare, 440, 20, 830, 100, renk=(18, 18, 28), opak=0.7, kenar=SARI)
            yazi_koy(kare, "SKOR", 470, 32, 20, SARI, hiza="sol")
            yazi_koy(kare, str(self.skor), 470, 56, 46, SARI, hiza="sol")
            yazi_koy(kare, f"Rekor: {self.rekor}", 790, 58, 26, BEYAZ, hiza="sag")

            # Sağdaki Emoji Görev Kartı (260 px panel)
            self.pop_anim = max(0.0, self.pop_anim - dt * 3.5)
            olcek = 1.0 + 0.18 * self.pop_anim

            kart_x0, kart_y0 = 870, 130
            kart_x1, kart_y1 = 1240, 680
            panel(kare, kart_x0, kart_y0, kart_x1, kart_y1, renk=(16, 16, 26), opak=0.82, kenar=PEMBE)

            # Emoji Sprite
            sprite = self.emoji_cache.get(self.hedef)
            if sprite is not None:
                cx_kart = (kart_x0 + kart_x1) // 2
                cy_kart = kart_y0 + 150
                boyut_anlik = int(240 * olcek)
                bindir_merkez(kare, sprite, cx_kart, cy_kart, boyut=boyut_anlik)

            # İfade Adı
            yazi_koy(kare, self.hedef.rsplit(" ", 1)[0], (kart_x0 + kart_x1) // 2, kart_y0 + 300, 34, SARI, hiza="orta")

            # Eşleşme Çubuğu
            cubuk_x = kart_x0 + 35
            cubuk_y = kart_y0 + 360
            cubuk_g = (kart_x1 - kart_x0) - 70
            cubuk_yuks = 28

            cv2.rectangle(kare, (cubuk_x, cubuk_y), (cubuk_x + cubuk_g, cubuk_y + cubuk_yuks), (35, 35, 45), -1)
            dolu_g = int(cubuk_g * max(0.0, min(1.0, self.cubuk_yumusak)))
            renk_cubuk = YESIL if self.cubuk_yumusak >= 0.95 else CAMGOBEGI
            if dolu_g > 0:
                cv2.rectangle(kare, (cubuk_x, cubuk_y), (cubuk_x + dolu_g, cubuk_y + cubuk_yuks), renk_cubuk, -1)
            cv2.rectangle(kare, (cubuk_x, cubuk_y), (cubuk_x + cubuk_g, cubuk_y + cubuk_yuks), BEYAZ, 1, cv2.LINE_AA)

            yazi_koy(kare, "Eşleşme", (kart_x0 + kart_x1) // 2, cubuk_y + 36, 22, BEYAZ, hiza="orta")

            # Tutma çemberi / geri sayım
            if self.tutma_suresi > 0:
                oran_tut = min(1.0, self.tutma_suresi / 0.4)
                halka(kare, (kart_x0 + kart_x1) // 2, cubuk_y + 90, oran_tut, r=26, renk=YESIL, kalinlik=5)

            # Hedef kalan zaman çizgisi
            kalan_hedef_oran = max(0.0, 1.0 - (simdi - self.hedef_zamani) / 5.0)
            cv2.line(
                kare,
                (kart_x0 + 20, kart_y1 - 25),
                (kart_x0 + 20 + int((kart_x1 - kart_x0 - 40) * kalan_hedef_oran), kart_y1 - 25),
                SARI,
                4,
                cv2.LINE_AA,
            )

            # Yüzün Yanında Canlı Blendshape Göstergesi
            if yuz_var and blend_sozluk:
                lm = algi.yuzler[0]
                burun_x, burun_y = px(lm, 1)

                p_x0 = int(np.clip(burun_x - 280, 20, G - 270))
                p_y0 = int(np.clip(burun_y - 60, 120, Y - 190))
                p_x1 = p_x0 + 240
                p_y1 = p_y0 + 130

                panel(kare, p_x0, p_y0, p_x1, p_y1, renk=(12, 12, 20), opak=0.65, kenar=CAMGOBEGI)
                yazi_koy(kare, "Canlı Mimik Seviyesi", p_x0 + 12, p_y0 + 8, 18, SARI, hiza="sol")

                # En yüksek 3 blendshape
                en_yuksekler = sorted(blend_sozluk.items(), key=lambda kv: kv[1], reverse=True)[:3]
                for i, (ad, val) in enumerate(en_yuksekler):
                    satir_y = p_y0 + 38 + i * 28
                    kisa_ad = ad[:11]
                    yazi_koy(kare, kisa_ad, p_x0 + 12, satir_y, 16, BEYAZ, hiza="sol")

                    bar_x = p_x0 + 115
                    bar_w = 100
                    cv2.rectangle(kare, (bar_x, satir_y + 4), (bar_x + bar_w, satir_y + 14), (40, 40, 50), -1)
                    val_w = int(bar_w * max(0.0, min(1.0, val)))
                    if val_w > 0:
                        cv2.rectangle(kare, (bar_x, satir_y + 4), (bar_x + val_w, satir_y + 14), CAMGOBEGI, -1)

        elif self.durum == "sonuc":
            kare[:] = bulanik_karanlik(kare, 0.6)
            panel(kare, 320, 120, 960, 600, renk=(18, 18, 28), opak=0.88, kenar=SARI)

            yazi_koy(kare, "SÜRE DOLDU!", G // 2, 170, 56, SARI, hiza="orta")

            if self.skor <= 3:
                unvan = "Çaylak 😉"
            elif self.skor <= 7:
                unvan = "Oyuncu 😎"
            else:
                unvan = "Usta 🎭"

            yazi_koy(kare, f"Skor: {self.skor}", G // 2, 260, 64, BEYAZ, hiza="orta")
            yazi_koy(kare, f"Unvan: {unvan}", G // 2, 350, 44, YESIL, hiza="orta")
            yazi_koy(kare, f"En Yüksek Skor: {self.rekor}", G // 2, 440, 32, CAMGOBEGI, hiza="orta")

            kalan_sonuc = max(0.0, 4.0 - (simdi - self.sonuc_baslangic))
            yazi_koy(kare, f"{int(np.ceil(kalan_sonuc))} sn içinde sıfırlanıyor...", G // 2, 530, 22, PEMBE, hiza="orta")

        # Parçacıkları en son çiz
        self.parcaciklar.ciz(kare)

        return kare
