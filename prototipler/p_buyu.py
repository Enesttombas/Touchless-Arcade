from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    PEMBE,
    SARI,
    Y,
    Algi,
    Parcaciklar,
    baslik,
    bulanik_karanlik,
    el_durumu,
    halka,
    panel,
    parilti,
    px,
    yazi_koy,
)

# Doctor Strange turuncu-altın tonları (BGR)
TURUNCU = (0, 140, 255)
ALTIN = (60, 215, 255)
ACIK_ALTIN = (160, 245, 255)
MAVI_ENERJI = (255, 190, 40)


class _ElTakip:
    def __init__(self, x: float, y: float, r: float):
        self.x = x
        self.y = y
        self.r = r
        self.olcek = 0.0
        self.aktif = False
        self.aci1 = 0.0
        self.aci2 = 0.0
        self.son_gorulme = 0.0


class Prototip:
    AD = "Büyücü"
    ACIKLAMA = "Avucunu aç büyünü çağır, iki elini birleştirip hızla açarak enerji ışını fırlat!"
    IHTIYAC = {"el"}
    SIRA = 8

    def __init__(self, ses: Any):
        self.ses = ses
        self.enerji: float = 0.0
        self.atis: int = 0
        self.rekor: int = 0

        self.onceki_zaman: Optional[float] = None
        self.parcaciklar = Parcaciklar(280)
        self.katman = np.zeros((Y, G, 3), dtype=np.uint8)

        # El ve büyü çemberi takibi (en fazla 2 el yuvası)
        self.yuvlar: List[Optional[_ElTakip]] = [None, None]

        # İki el enerji topu takibi
        self.top_x: float = G / 2.0
        self.top_y: float = Y / 2.0
        self.onceki_mesafe: Optional[float] = None
        self.son_zap: float = 0.0

        # Işın ve efekt durumları
        self.isin_sure: float = 0.0
        self.isin_max_sure: float = 0.6
        self.isin_x0: float = G / 2.0
        self.isin_y0: float = Y / 2.0
        self.isin_x1: float = G
        self.isin_y1: float = Y / 2.0
        self.isin_guc: float = 1.0

        self.sarsinti_sure: float = 0.0
        self.flas_opak: float = 0.0
        self.skor_pop: float = 0.0

        self.rng = np.random.RandomState(1337)

    def _klip_px(self, lm: Any, i: int) -> Tuple[float, float]:
        x, y = px(lm, i)
        return float(max(0.0, min(G - 1.0, x))), float(max(0.0, min(Y - 1.0, y)))

    def _mandala_ciz(
        self,
        katman: np.ndarray,
        cx: float,
        cy: float,
        r: float,
        aci1: float,
        aci2: float,
    ) -> None:
        if r < 8.0:
            return

        ic_x, ic_y = int(cx), int(cy)
        ir = int(r)
        ir_ic = max(4, int(r * 0.62))
        ir_orta = max(6, int(r * 0.80))

        # Ana eşmerkezli halkalar
        cv2.circle(katman, (ic_x, ic_y), ir, TURUNCU, 2, cv2.LINE_AA)
        cv2.circle(katman, (ic_x, ic_y), ir_orta, ALTIN, 1, cv2.LINE_AA)
        cv2.circle(katman, (ic_x, ic_y), ir_ic, ALTIN, 2, cv2.LINE_AA)

        # Dönen kare / yıldız (aci1 ile döner)
        for ofset in (0.0, math.pi / 4.0):
            kose = []
            for k in range(4):
                a = aci1 + ofset + k * (math.pi / 2.0)
                kose.append([int(cx + math.cos(a) * ir_orta), int(cy + math.sin(a) * ir_orta)])
            pts = np.array(kose, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(katman, [pts], True, TURUNCU, 2, cv2.LINE_AA)

        # Ters yönde dönen iç üçgenler (aci2 ile döner)
        for ofset in (0.0, math.pi / 3.0):
            ucgen = []
            for k in range(3):
                a = aci2 + ofset + k * (2.0 * math.pi / 3.0)
                ucgen.append([int(cx + math.cos(a) * ir_ic), int(cy + math.sin(a) * ir_ic)])
            pts = np.array(ucgen, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(katman, [pts], True, ACIK_ALTIN, 1, cv2.LINE_AA)

        # Halkalar arası rün benzeri çizgiler ve küçük üçgenler
        N_run = 12
        for i in range(N_run):
            a = aci2 + i * (2.0 * math.pi / N_run)
            ca, sa = math.cos(a), math.sin(a)
            x0 = int(cx + ca * (ir_ic + 2))
            y0 = int(cy + sa * (ir_ic + 2))
            x1 = int(cx + ca * (ir - 3))
            y1 = int(cy + sa * (ir - 3))
            cv2.line(katman, (x0, y0), (x1, y1), ALTIN, 2, cv2.LINE_AA)

            # Küçük rün çentikleri
            if i % 2 == 0:
                da = 0.09
                xm = int(cx + math.cos(a + da) * ir_orta)
                ym = int(cy + math.sin(a + da) * ir_orta)
                cv2.line(katman, (x0, y0), (xm, ym), TURUNCU, 1, cv2.LINE_AA)
            else:
                da = 0.08
                p1 = (int(cx + math.cos(a - da) * ir_orta), int(cy + math.sin(a - da) * ir_orta))
                p2 = (int(cx + math.cos(a + da) * ir_orta), int(cy + math.sin(a + da) * ir_orta))
                cv2.line(katman, p1, p2, ACIK_ALTIN, 2, cv2.LINE_AA)

        # Dış halkada 12 küçük parlak nokta (aci1 ile döner)
        for i in range(12):
            a = aci1 + i * (2.0 * math.pi / 12.0)
            px_i = int(cx + math.cos(a) * (ir + 6))
            py_i = int(cy + math.sin(a) * (ir + 6))
            cv2.circle(katman, (px_i, py_i), 4, ALTIN, -1, cv2.LINE_AA)
            cv2.circle(katman, (px_i, py_i), 2, BEYAZ, -1, cv2.LINE_AA)

        # Merkez çekirdek
        cv2.circle(katman, (ic_x, ic_y), max(3, int(r * 0.12)), ACIK_ALTIN, -1, cv2.LINE_AA)

    def _ark_ciz(
        self,
        katman: np.ndarray,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        sapma: float = 18.0,
        renk: Tuple[int, int, int] = CAMGOBEGI,
    ) -> None:
        adim = 7
        dx = x1 - x0
        dy = y1 - y0
        uzunluk = math.hypot(dx, dy)
        if uzunluk < 5.0:
            return
        nx = -dy / uzunluk
        ny = dx / uzunluk

        pts = [[int(x0), int(y0)]]
        for i in range(1, adim):
            t = i / float(adim)
            bx = x0 + dx * t
            by = y0 + dy * t
            ofset = (self.rng.uniform(-1.0, 1.0)) * sapma * math.sin(t * math.pi)
            pts.append([int(bx + nx * ofset), int(by + ny * ofset)])
        pts.append([int(x1), int(y1)])

        arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(katman, [arr], False, renk, 2, cv2.LINE_AA)
        cv2.polylines(katman, [arr], False, BEYAZ, 1, cv2.LINE_AA)

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.onceki_zaman is None:
            dt = 0.033
        else:
            dt = min(max(simdi - self.onceki_zaman, 0.0), 0.1)
        self.onceki_zaman = simdi

        self.katman.fill(0)

        eller = algi.eller or []
        jestler = algi.jestler or []
        el_sayisi = len(eller)

        # Görünen ellerin bilgilerini çıkar
        girdi_eller = []
        for idx, el in enumerate(eller[:2]):
            if len(el) < 21:
                continue
            bx, by = self._klip_px(el, 0)
            mx, my = self._klip_px(el, 9)
            el_boy = math.hypot(mx - bx, my - by)
            hedef_r = max(45.0, min(170.0, el_boy * 1.35))

            jest = jestler[idx] if idx < len(jestler) else None
            durum = el_durumu(el)

            acik = (jest == "Open_Palm") or (durum == "sil")
            yumruk = (jest == "Closed_Fist") or (durum == "yok" and jest == "Closed_Fist")

            girdi_eller.append(
                {
                    "bx": bx,
                    "by": by,
                    "mx": mx,
                    "my": my,
                    "r": hedef_r,
                    "acik": acik,
                    "yumruk": yumruk,
                }
            )

        # Yuvaları eşleştir ve güncelle
        yumusa = 1.0 - math.exp(-dt * 18.0)
        for i in range(2):
            if i < len(girdi_eller):
                ge = girdi_eller[i]
                yuva = self.yuvlar[i]
                if yuva is None:
                    yuva = _ElTakip(ge["mx"], ge["my"], ge["r"])
                    self.yuvlar[i] = yuva
                else:
                    yuva.x += (ge["mx"] - yuva.x) * yumusa
                    yuva.y += (ge["my"] - yuva.y) * yumusa
                    yuva.r += (ge["r"] - yuva.r) * yumusa
                yuva.son_gorulme = simdi

                if ge["yumruk"]:
                    if yuva.aktif or yuva.olcek > 0.15:
                        # Yumruk olunca çember parçacıklarla patlar ("pop")
                        self.ses.cal("pop", ses=0.75)
                        self.parcaciklar.yay(yuva.x, yuva.y, 32, renk=ALTIN, hiz=6.5)
                        self.parcaciklar.yay(yuva.x, yuva.y, 14, renk=TURUNCU, hiz=4.5)
                    yuva.aktif = False
                    yuva.olcek = 0.0
                elif ge["acik"]:
                    if not yuva.aktif and yuva.olcek <= 0.05:
                        self.ses.cal("woosh", ses=0.35)
                    yuva.aktif = True
                else:
                    yuva.aktif = False
            else:
                yuva = self.yuvlar[i]
                if yuva is not None and (simdi - yuva.son_gorulme) > 0.15:
                    yuva.aktif = False

        # Büyü çemberlerini güncelle ve çiz
        for yuva in self.yuvlar:
            if yuva is None:
                continue
            if yuva.aktif:
                yuva.olcek = min(1.0, yuva.olcek + dt / 0.3)
            else:
                yuva.olcek = max(0.0, yuva.olcek - dt / 0.25)

            if yuva.olcek > 0.02:
                yuva.aci1 += dt * 1.9
                yuva.aci2 -= dt * 2.6
                # Ease-out büyüme
                ease_s = 1.0 - (1.0 - yuva.olcek) ** 2
                ciz_r = yuva.r * ease_s
                self._mandala_ciz(self.katman, yuva.x, yuva.y, ciz_r, yuva.aci1, yuva.aci2)

                # Çember etrafında kıvılcım parçacıkları
                if self.rng.rand() < 0.65:
                    rast_aci = self.rng.uniform(0.0, 2.0 * math.pi)
                    kx = yuva.x + math.cos(rast_aci) * ciz_r
                    ky = yuva.y + math.sin(rast_aci) * ciz_r
                    self.parcaciklar.yay(kx, ky, 2, renk=ALTIN, hiz=2.5)

        # İki el enerji topu ve atış mekaniği
        if len(girdi_eller) >= 2:
            e0, e1 = girdi_eller[0], girdi_eller[1]
            bilek_mesafe = math.hypot(e0["bx"] - e1["bx"], e0["by"] - e1["by"])
            avuc_mesafe = math.hypot(e0["mx"] - e1["mx"], e0["my"] - e1["my"])

            ort_x = (e0["mx"] + e1["mx"]) * 0.5
            ort_y = (e0["my"] + e1["my"]) * 0.5
            self.top_x += (ort_x - self.top_x) * yumusa
            self.top_y += (ort_y - self.top_y) * yumusa

            hiz_artis = 0.0
            if self.onceki_mesafe is not None and dt > 1e-4:
                d_bilek = (bilek_mesafe - self.onceki_mesafe) / dt
                hiz_artis = d_bilek
            self.onceki_mesafe = bilek_mesafe

            # Atış kontrolü: enerji > 0.3 iken iki el arası mesafe hızla açılırsa (> 600 px/s)
            if self.enerji > 0.3 and hiz_artis > 600.0:
                AtisGucu = self.enerji
                self.atis += 1
                if self.atis > self.rekor:
                    self.rekor = self.atis
                self.enerji = 0.0
                self.skor_pop = 0.35

                # Dev ışın parametreleri (toptan ekranın uzak kenarına)
                self.isin_sure = self.isin_max_sure
                self.isin_x0 = self.top_x
                self.isin_y0 = self.top_y
                self.isin_guc = AtisGucu

                # Ellerin açılma eksenine dik veya merkeze göre uzak kenara hedefle
                dx_m = self.top_x - (G * 0.5)
                dy_m = self.top_y - (Y * 0.5)
                if abs(dx_m) < 40.0 and abs(dy_m) < 40.0:
                    # Merkezdeyse yukarı-ileri veya sağ/sol uzak kenara
                    self.isin_x1 = G if self.top_x < G * 0.5 else 0.0
                    self.isin_y1 = max(80.0, min(Y - 80.0, self.top_y - 120.0))
                else:
                    # Toptan uzak kenara doğru uzat
                    hedef_x = G if self.top_x < G * 0.5 else 0.0
                    hedef_y = Y * 0.5 + (self.top_y - Y * 0.5) * 0.6
                    self.isin_x1 = float(hedef_x)
                    self.isin_y1 = float(hedef_y)

                self.sarsinti_sure = 0.4
                self.flas_opak = 0.4
                self.ses.cal("zap", ses=0.85)
                self.ses.cal("woosh", ses=0.9)
                self.parcaciklar.yay(self.top_x, self.top_y, 55, renk=CAMGOBEGI, hiz=9.0)
                self.parcaciklar.yay(self.top_x, self.top_y, 25, renk=BEYAZ, hiz=7.0)

            elif bilek_mesafe < 0.4 * G:
                # 1.5 saniyede 0 -> 1 dolar
                self.enerji = min(1.0, self.enerji + dt / 1.5)
                if simdi - self.son_zap > 0.24:
                    self.ses.cal("zap", ses=0.2)
                    self.son_zap = simdi
            else:
                self.enerji = max(0.0, self.enerji - 0.5 * dt)
        else:
            self.onceki_mesafe = None
            self.enerji = max(0.0, self.enerji - 0.5 * dt)

        # Enerji topunu ve elektrik arklarını çiz
        if self.enerji > 0.01:
            r_top = int(20.0 + 70.0 * self.enerji)
            tx, ty = int(self.top_x), int(self.top_y)

            # Dış mavi-camgöbeği enerji küresi ve dönen halkalar
            cv2.circle(self.katman, (tx, ty), r_top, MAVI_ENERJI, 3, cv2.LINE_AA)
            cv2.circle(self.katman, (tx, ty), int(r_top * 0.78), CAMGOBEGI, -1, cv2.LINE_AA)
            cv2.circle(self.katman, (tx, ty), int(r_top * 0.48), BEYAZ, -1, cv2.LINE_AA)

            # Top içi enerji dalgalanması
            dalga_aci = simdi * 6.0
            rx1 = int(r_top * 0.95)
            ry1 = max(6, int(r_top * 0.38))
            cv2.ellipse(
                self.katman,
                (tx, ty),
                (rx1, ry1),
                math.degrees(dalga_aci),
                0,
                360,
                BEYAZ,
                2,
                cv2.LINE_AA,
            )
            cv2.ellipse(
                self.katman,
                (tx, ty),
                (rx1, ry1),
                math.degrees(-dalga_aci * 1.3),
                0,
                360,
                CAMGOBEGI,
                2,
                cv2.LINE_AA,
            )

            # Ellerden topa zikzak elektrik arkları
            for ge in girdi_eller[:2]:
                self._ark_ciz(
                    self.katman,
                    ge["mx"],
                    ge["my"],
                    self.top_x,
                    self.top_y,
                    sapma=12.0 + 22.0 * self.enerji,
                    renk=CAMGOBEGI,
                )
                if self.enerji > 0.45:
                    self._ark_ciz(
                        self.katman,
                        ge["bx"],
                        ge["by"],
                        self.top_x,
                        self.top_y,
                        sapma=16.0 * self.enerji,
                        renk=MAVI_ENERJI,
                    )

            if self.rng.rand() < 0.7:
                a = self.rng.uniform(0.0, 2.0 * math.pi)
                px_e = self.top_x + math.cos(a) * r_top
                py_e = self.top_y + math.sin(a) * r_top
                self.parcaciklar.yay(px_e, py_e, 2, renk=CAMGOBEGI, hiz=3.5)

        # Dev enerji ışını çizimi (0.6 sn)
        if self.isin_sure > 0.0:
            oran_isin = self.isin_sure / self.isin_max_sure
            kalin_dis = max(6, int((28.0 + 70.0 * self.isin_guc) * oran_isin))
            kalin_ic = max(2, int(kalin_dis * 0.48))

            p0 = (int(self.isin_x0), int(self.isin_y0))
            p1 = (int(self.isin_x1), int(self.isin_y1))

            cv2.line(self.katman, p0, p1, CAMGOBEGI, kalin_dis, cv2.LINE_AA)
            cv2.line(self.katman, p0, p1, BEYAZ, kalin_ic, cv2.LINE_AA)
            cv2.circle(self.katman, p0, int(kalin_dis * 0.75), BEYAZ, -1, cv2.LINE_AA)
            cv2.circle(self.katman, p1, int(kalin_dis * 0.9), CAMGOBEGI, -1, cv2.LINE_AA)

            # Işın boyunca yıldırım arkları
            self._ark_ciz(
                self.katman,
                self.isin_x0,
                self.isin_y0,
                self.isin_x1,
                self.isin_y1,
                sapma=35.0 * oran_isin,
                renk=BEYAZ,
            )
            self.isin_sure = max(0.0, self.isin_sure - dt)

        # Neon parıltı katmanını kareye uygula
        parilti(kare, self.katman, guc=1.85, sigma=3.2)

        # Parçacıkları güncelle ve çiz
        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(kare)

        # Beyaz flaş efekti
        if self.flas_opak > 0.01:
            alfa = min(0.4, self.flas_opak)
            beyaz_k = np.full_like(kare, 255)
            cv2.addWeighted(kare, 1.0 - alfa, beyaz_k, alfa, 0, dst=kare)
            self.flas_opak = max(0.0, self.flas_opak - dt * 2.5)

        # Ekran sarsıntısı (0.4 sn)
        if self.sarsinti_sure > 0.0:
            genlik = int(16.0 * (self.sarsinti_sure / 0.4))
            if genlik > 0:
                sx = int(self.rng.randint(-genlik, genlik + 1))
                sy = int(self.rng.randint(-genlik, genlik + 1))
                M = np.float32([[1, 0, sx], [0, 1, sy]])
                cv2.warpAffine(kare, M, (G, Y), dst=kare, borderMode=cv2.BORDER_REFLECT_101)
            self.sarsinti_sure = max(0.0, self.sarsinti_sure - dt)

        # Skor pop animasyonu güncelle
        if self.skor_pop > 0.0:
            self.skor_pop = max(0.0, self.skor_pop - dt)

        # Arayüz ve Durum Ekranları
        if el_sayisi == 0 and self.isin_sure <= 0.0:
            # Kimse yokken çekim ekranı
            karart = bulanik_karanlik(kare, 0.55)
            np.copyto(kare, karart)

            panel(kare, G // 2 - 420, Y // 2 - 140, G // 2 + 420, Y // 2 + 140, opak=0.7, kenar=SARI)
            nabiz = 1.0 + 0.06 * math.sin(simdi * 4.5)
            yazi_koy(kare, "Büyücü", G // 2, Y // 2 - 105, 60, renk=SARI, hiza="orta", olcek=nabiz)
            yazi_koy(
                kare,
                "Avucunu aç, büyünü çağır!",
                G // 2,
                Y // 2 - 20,
                42,
                renk=BEYAZ,
                hiza="orta",
            )
            yazi_koy(
                kare,
                "İki elini yaklaştırıp enerji topla, hızla açarak ışın fırlat!",
                G // 2,
                Y // 2 + 55,
                26,
                renk=CAMGOBEGI,
                hiza="orta",
            )
        else:
            # Üst sol/sağ bilgi panelleri
            panel(kare, 24, 20, 310, 140, opak=0.65, kenar=CAMGOBEGI)
            yazi_koy(kare, "ENERJİ", 50, 32, 24, renk=CAMGOBEGI, hiza="sol")
            halka(
                kare,
                85,
                96,
                self.enerji,
                r=28,
                renk=CAMGOBEGI if self.enerji >= 0.3 else SARI,
                kalinlik=7,
            )
            yuzde = int(round(self.enerji * 100))
            yazi_koy(kare, f"%{yuzde}", 135, 74, 38, renk=BEYAZ, hiza="sol")

            # Sağ üst Atış sayacı (90+ px skor)
            panel(kare, G - 280, 20, G - 24, 155, opak=0.65, kenar=SARI)
            yazi_koy(kare, "ATIŞ", G - 152, 26, 24, renk=SARI, hiza="orta")
            olcek_skor = 1.0 + 0.35 * (self.skor_pop / 0.35) if self.skor_pop > 0 else 1.0
            yazi_koy(
                kare,
                str(self.atis),
                G - 152,
                52,
                92,
                renk=BEYAZ,
                hiza="orta",
                olcek=olcek_skor,
            )

            # Tek el varken veya enerji ipucu
            if el_sayisi == 1:
                panel(kare, G // 2 - 330, Y - 86, G // 2 + 330, Y - 24, opak=0.65, kenar=SARI)
                yazi_koy(
                    kare,
                    "İki elini yaklaştır, enerji topla!",
                    G // 2,
                    Y - 72,
                    32,
                    renk=SARI,
                    hiza="orta",
                )
            elif el_sayisi >= 2 and self.enerji >= 0.3:
                panel(kare, G // 2 - 350, Y - 86, G // 2 + 350, Y - 24, opak=0.65, kenar=CAMGOBEGI)
                nabiz_ipucu = 1.0 + 0.05 * math.sin(simdi * 8.0)
                yazi_koy(
                    kare,
                    "Ellerini hızla aç, ışını fırlat!",
                    G // 2,
                    Y - 72,
                    34,
                    renk=CAMGOBEGI,
                    hiza="orta",
                    olcek=nabiz_ipucu,
                )

        return kare

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R")):
            self.enerji = 0.0
            self.atis = 0
