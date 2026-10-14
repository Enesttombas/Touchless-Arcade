"""Hava Davulu prototipi: Havada parmakla neon davul çalma deneyimi."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import cv2
import numpy as np

from cekirdek import (
    BEYAZ,
    CAMGOBEGI,
    G,
    KIRMIZI,
    PEMBE,
    SARI,
    Y,
    YESIL,
    Algi,
    Parcaciklar,
    Ses,
    baslik,
    bulanik_karanlik,
    panel,
    parilti,
    px,
    yazi_koy,
)


@dataclass
class Ped:
    x: float
    y: float
    r: float
    ses: str
    ad: str
    renk: Tuple[int, int, int]
    son_vurus: float = -10.0


@dataclass
class _Izci:
    id: int
    x: float
    y: float
    sx: float
    sy: float
    vy: float = 0.0
    son_gorulme: float = 0.0
    kilitli_pedler: Set[int] = field(default_factory=set)
    iz: List[Tuple[float, float, float]] = field(default_factory=list)


class Prototip:
    AD = "Hava Davulu"
    ACIKLAMA = "Parmağını neon pedlere yukarıdan hızla indirerek ritim tut!"
    IHTIYAC = {"el"}
    SIRA = 9

    def __init__(self, ses: Ses):
        self.ses = ses
        self.vurus: int = 0
        self.rekor: int = 0

        # Alt yarıda yay şeklinde dizili 6 ped (r: 82..90, y >= 330)
        self.pedler: List[Ped] = [
            Ped(x=155.0, y=380.0, r=82.0, ses="hihat", ad="Hi-Hat", renk=SARI),
            Ped(x=335.0, y=490.0, r=86.0, ses="snare", ad="Trampet", renk=CAMGOBEGI),
            Ped(x=530.0, y=565.0, r=90.0, ses="kick", ad="Kick", renk=PEMBE),
            Ped(x=750.0, y=565.0, r=90.0, ses="nota55", ad="Tom", renk=YESIL),
            Ped(x=945.0, y=490.0, r=86.0, ses="clap", ad="Alkış", renk=KIRMIZI),
            Ped(x=1125.0, y=380.0, r=82.0, ses="nota79", ad="Zil", renk=SARI),
        ]

        self.parcaciklar = Parcaciklar(240)
        self.dalgalar: List[Tuple[float, float, float, float, Tuple[int, int, int]]] = []
        self.gecmis_vuruslar: List[Tuple[float, int, Tuple[int, int, int]]] = []

        self.izciler: List[_Izci] = []
        self._sonraki_id = 1
        self.onceki_zaman: Optional[float] = None
        self.neon_katman = np.zeros((Y, G, 3), dtype=np.uint8)

        self.son_vurus_zamani: float = -10.0
        self.ritim_bitis: float = -10.0

    def tus(self, k: int) -> None:
        if k in (ord("r"), ord("R")):
            self.vurus = 0
            self.gecmis_vuruslar.clear()
            self.dalgalar.clear()

    def _uclar_cikar(self, algi: Algi) -> List[Tuple[float, float]]:
        uclar: List[Tuple[float, float]] = []
        if not algi or not algi.eller:
            return uclar
        for el in algi.eller:
            if not el or len(el) <= 8:
                continue
            try:
                ux, uy = px(el, 8)
                if math.isnan(ux) or math.isnan(uy):
                    continue
                ux = max(-200.0, min(float(G + 200), float(ux)))
                uy = max(-200.0, min(float(Y + 200), float(uy)))
                uclar.append((ux, uy))
            except Exception:
                continue
        return uclar

    def _izcileri_guncelle(
        self, uclar: List[Tuple[float, float]], simdi: float, dt: float
    ) -> List[Tuple[_Izci, float, float]]:
        hareketler: List[Tuple[_Izci, float, float]] = []
        eslesen_izci: Set[int] = set()
        eslesen_uc: Set[int] = set()

        ciftler: List[Tuple[float, int, int]] = []
        for i, iz in enumerate(self.izciler):
            for j, (ux, uy) in enumerate(uclar):
                d = math.hypot(ux - iz.x, uy - iz.y)
                if d < 380.0:
                    ciftler.append((d, i, j))
        ciftler.sort(key=lambda t: t[0])

        for _, i, j in ciftler:
            if i in eslesen_izci or j in eslesen_uc:
                continue
            eslesen_izci.add(i)
            eslesen_uc.add(j)

            iz = self.izciler[i]
            eski_x, eski_y = iz.x, iz.y
            ux, uy = uclar[j]

            anlik_vy = (uy - eski_y) / dt if dt > 1e-5 else 0.0
            iz.vy = anlik_vy
            iz.x = ux
            iz.y = uy
            # Üstel yumuşatma (görsel baget izi için)
            iz.sx = 0.55 * ux + 0.45 * iz.sx
            iz.sy = 0.55 * uy + 0.45 * iz.sy
            iz.son_gorulme = simdi
            iz.iz.append((iz.sx, iz.sy, simdi))
            if len(iz.iz) > 12:
                iz.iz.pop(0)

            hareketler.append((iz, eski_x, eski_y))

        # Yeni algılanan uçlar
        for j, (ux, uy) in enumerate(uclar):
            if j in eslesen_uc:
                continue
            yeni = _Izci(
                id=self._sonraki_id,
                x=ux,
                y=uy,
                sx=ux,
                sy=uy,
                vy=0.0,
                son_gorulme=simdi,
                iz=[(ux, uy, simdi)],
            )
            self._sonraki_id += 1
            # Eğer doğrudan bir pedin içinde doğduysa kilitle (çıkana kadar tetiklenmesin)
            for p_idx, p in enumerate(self.pedler):
                if math.hypot(ux - p.x, uy - p.y) <= p.r:
                    yeni.kilitli_pedler.add(p_idx)
            self.izciler.append(yeni)

        # Kaybolan izcileri temizle
        self.izciler = [iz for iz in self.izciler if (simdi - iz.son_gorulme) <= 0.25]
        return hareketler

    def _vuruslari_kontrol_et(
        self, hareketler: List[Tuple[_Izci, float, float]], simdi: float, dt: float
    ) -> None:
        if dt <= 1e-6:
            return

        for iz, eski_x, eski_y in hareketler:
            ux, uy = iz.x, iz.y
            vy = (uy - eski_y) / dt

            for p_idx, p in enumerate(self.pedler):
                mesafe = math.hypot(ux - p.x, uy - p.y)
                eski_mesafe = math.hypot(eski_x - p.x, eski_y - p.y)

                # Kilit açma: r * 1.2 dışına çıkınca tekrar vurulabilir
                if p_idx in iz.kilitli_pedler:
                    if mesafe > p.r * 1.2:
                        iz.kilitli_pedler.discard(p_idx)
                    continue

                # Vuruş koşulu:
                # 1) Aşağı hız > 450 px/s
                # 2) Ped dairesine yukarıdan giriş (eski konum daire dışında ve üst yarı-düzlemde)
                if vy > 450.0 and uy > eski_y:
                    yukaridan = (eski_y < p.y) and (eski_mesafe >= p.r * 0.85)
                    icerde = mesafe <= p.r * 1.05

                    # Çok hızlı geçişte doğru parçasının daireyi kesmesi (tünel etkisi koruması)
                    kesisti = False
                    if not icerde and eski_y < p.y and uy >= p.y - p.r * 0.5:
                        dx = ux - eski_x
                        dy = uy - eski_y
                        seg_len2 = dx * dx + dy * dy
                        if seg_len2 > 1.0:
                            t_proj = max(0.0, min(1.0, ((p.x - eski_x) * dx + (p.y - eski_y) * dy) / seg_len2))
                            nx = eski_x + t_proj * dx
                            ny = eski_y + t_proj * dy
                            if math.hypot(nx - p.x, ny - p.y) <= p.r:
                                kesisti = True

                    if yukaridan and (icerde or kesisti):
                        self._ped_tetikle(p_idx, simdi)
                        iz.kilitli_pedler.add(p_idx)

    def _ped_tetikle(self, p_idx: int, simdi: float) -> None:
        p = self.pedler[p_idx]
        p.son_vurus = simdi
        self.son_vurus_zamani = simdi
        self.vurus += 1
        if self.vurus > self.rekor:
            self.rekor = self.vurus

        self.ses.cal(p.ses, ses=0.85)
        self.parcaciklar.yay(p.x, p.y, 12, renk=p.renk, hiz=5.5)
        self.dalgalar.append((p.x, p.y, p.r, simdi, p.renk))
        self.gecmis_vuruslar.append((simdi, p_idx, p.renk))

        # Son 1.5 saniyede 4+ vuruş varsa "RİTİM!" modunu tetikle
        son_15 = sum(1 for t, _, _ in self.gecmis_vuruslar if simdi - t <= 1.5)
        if son_15 >= 4:
            self.ritim_bitis = simdi + 1.0

    def isle(self, kare: np.ndarray, algi: Algi, simdi: float) -> np.ndarray:
        if self.onceki_zaman is None:
            dt = 0.016
        else:
            dt = min(max(float(simdi - self.onceki_zaman), 0.0), 0.1)
        self.onceki_zaman = float(simdi)

        uclar = self._uclar_cikar(algi)
        kimse_yok = len(uclar) == 0

        hareketler = self._izcileri_guncelle(uclar, simdi, dt)
        self._vuruslari_kontrol_et(hareketler, simdi, dt)
        self.parcaciklar.guncelle(dt)

        # Eski dalga ve vuruş kayıtlarını temizle
        self.dalgalar = [d for d in self.dalgalar if simdi - d[3] < 0.45]
        self.gecmis_vuruslar = [v for v in self.gecmis_vuruslar if simdi - v[0] <= 4.0]

        if kimse_yok:
            kare[:] = bulanik_karanlik(kare, 0.48)

        katman = self.neon_katman
        katman.fill(0)

        # 1) Pedlerin çizimi (koyu yarı saydam iç + neon kenar + sönen parıltı)
        demo_aktif_idx = int((simdi * 2.2) % len(self.pedler)) if kimse_yok else -1
        demo_faz = (simdi * 2.2) % 1.0

        for idx, p in enumerate(self.pedler):
            gecen = simdi - p.son_vurus
            buyume = 0.0
            parlama = 0.0
            if 0.0 <= gecen < 0.15:
                k = 1.0 - (gecen / 0.15)
                buyume = 16.0 * k
                parlama = k
            elif 0.15 <= gecen < 0.45:
                parlama = 0.35 * (1.0 - (gecen - 0.15) / 0.30)

            if kimse_yok and idx == demo_aktif_idx:
                nabiz = math.sin(demo_faz * math.pi)
                buyume = max(buyume, 10.0 * nabiz)
                parlama = max(parlama, 0.75 * nabiz)

            r_ciz = int(p.r + buyume)
            cx, cy = int(p.x), int(p.y)

            # Yarı saydam koyu iç dolgu (ROI üzerinde hızlı harmanlama)
            x0, y0 = max(0, cx - r_ciz), max(0, cy - r_ciz)
            x1, y1 = min(G, cx + r_ciz), min(Y, cy + r_ciz)
            if x1 > x0 and y1 > y0:
                roi = kare[y0:y1, x0:x1]
                ic_renk = (
                    int(20 + p.renk[0] * 0.22 * (0.3 + parlama)),
                    int(20 + p.renk[1] * 0.22 * (0.3 + parlama)),
                    int(28 + p.renk[2] * 0.22 * (0.3 + parlama)),
                )
                cv2.circle(
                    roi,
                    (cx - x0, cy - y0),
                    r_ciz,
                    ic_renk,
                    -1,
                    cv2.LINE_AA,
                )

            # Dış neon çember ve iç halka
            kalinlik = int(4 + 6 * parlama)
            cv2.circle(kare, (cx, cy), r_ciz, p.renk, kalinlik, cv2.LINE_AA)
            cv2.circle(kare, (cx, cy), int(r_ciz * 0.72), p.renk, 1, cv2.LINE_AA)
            cv2.circle(katman, (cx, cy), r_ciz, p.renk, kalinlik + 2, cv2.LINE_AA)

            if parlama > 0.05:
                parlak_renk = (
                    min(255, int(p.renk[0] * parlama + 80 * parlama)),
                    min(255, int(p.renk[1] * parlama + 80 * parlama)),
                    min(255, int(p.renk[2] * parlama + 80 * parlama)),
                )
                cv2.circle(katman, (cx, cy), int(r_ciz * 0.55), parlak_renk, -1, cv2.LINE_AA)

        # 2) Dışa yayılan halka dalgaları
        for wx, wy, wr, wt, wrenk in self.dalgalar:
            gecen = simdi - wt
            ilerleme = gecen / 0.45
            if 0.0 <= ilerleme <= 1.0:
                r_dalga = int(wr + ilerleme * 85.0)
                k = 1.0 - ilerleme
                renk_d = (int(wrenk[0] * k), int(wrenk[1] * k), int(wrenk[2] * k))
                kal = max(1, int(5 * k))
                cv2.circle(kare, (int(wx), int(wy)), r_dalga, renk_d, kal, cv2.LINE_AA)
                cv2.circle(katman, (int(wx), int(wy)), r_dalga, renk_d, kal + 2, cv2.LINE_AA)

        # 3) Parmak uçlarında parlak baget izi
        for iz in self.izciler:
            n_iz = len(iz.iz)
            if n_iz >= 2:
                for k_i in range(1, n_iz):
                    x_a, y_a, _ = iz.iz[k_i - 1]
                    x_b, y_b, t_b = iz.iz[k_i]
                    yas = simdi - t_b
                    if yas > 0.25:
                        continue
                    oran = (k_i / n_iz) * max(0.0, 1.0 - yas / 0.25)
                    kal = max(2, int(10 * oran))
                    pt1 = (int(x_a), int(y_a))
                    pt2 = (int(x_b), int(y_b))
                    cv2.line(kare, pt1, pt2, CAMGOBEGI, kal, cv2.LINE_AA)
                    cv2.line(katman, pt1, pt2, CAMGOBEGI, kal + 2, cv2.LINE_AA)

            ux_i, uy_i = int(iz.sx), int(iz.sy)
            cv2.circle(kare, (ux_i, uy_i), 14, BEYAZ, -1, cv2.LINE_AA)
            cv2.circle(kare, (ux_i, uy_i), 18, SARI, 3, cv2.LINE_AA)
            cv2.circle(katman, (ux_i, uy_i), 18, SARI, -1, cv2.LINE_AA)

        # Neon parıltıyı uygula ve parçacıkları çiz
        parilti(kare, katman, guc=1.7, sigma=3.0)
        self.parcaciklar.ciz(kare)

        # Ped isimleri (parıltıdan sonra net okunması için)
        for p in self.pedler:
            yazi_koy(kare, p.ad, int(p.x), int(p.y - 16), 28, renk=BEYAZ, hiza="orta")

        # 4) Üst ritim şeridi (son 4 sn'nin vuruşları kayan noktalar) ve skor paneli
        serit_x0, serit_y0, serit_x1, serit_y1 = 270, 22, 1010, 96
        panel(kare, serit_x0, serit_y0, serit_x1, serit_y1, renk=(16, 16, 26), opak=0.72, kenar=CAMGOBEGI)

        orta_y = (serit_y0 + serit_y1) // 2
        cv2.line(kare, (serit_x0 + 20, orta_y), (serit_x1 - 20, orta_y), (60, 70, 90), 2, cv2.LINE_AA)
        # Sağ başta "şimdi" çizgisi
        simdi_x = serit_x1 - 30
        cv2.line(kare, (simdi_x, serit_y0 + 10), (simdi_x, serit_y1 - 10), SARI, 2, cv2.LINE_AA)

        genislik = float(simdi_x - (serit_x0 + 25))
        for vt, p_idx, vrenk in self.gecmis_vuruslar:
            yas = simdi - vt
            if 0.0 <= yas <= 4.0:
                vx = int(simdi_x - (yas / 4.0) * genislik)
                vy_off = ((p_idx % 3) - 1) * 14
                vy_nokta = orta_y + vy_off
                r_nokta = 9 if yas < 0.2 else 7
                cv2.circle(kare, (vx, vy_nokta), r_nokta, vrenk, -1, cv2.LINE_AA)
                cv2.circle(kare, (vx, vy_nokta), r_nokta + 2, BEYAZ, 1, cv2.LINE_AA)

        # Sol üstte büyük vuruş sayacı
        panel(kare, 24, 18, 245, 132, renk=(18, 18, 28), opak=0.72, kenar=SARI)
        pop_olcek = 1.0
        if 0.0 <= (simdi - self.son_vurus_zamani) < 0.18:
            pop_olcek = 1.0 + 0.22 * (1.0 - (simdi - self.son_vurus_zamani) / 0.18)
        yazi_koy(kare, str(self.vurus), 134, 22, 72, renk=SARI, hiza="orta", olcek=pop_olcek)
        yazi_koy(kare, "VURUŞ", 134, 98, 22, renk=BEYAZ, hiza="orta")

        # 1.5 sn'de 4+ vuruş yapıldığında "RİTİM!" bildirimi
        if simdi < self.ritim_bitis:
            kalan = self.ritim_bitis - simdi
            olcek_r = 1.0 + 0.12 * math.sin(simdi * 18.0)
            panel(kare, 1035, 22, 1256, 96, renk=(35, 15, 45), opak=0.8, kenar=PEMBE)
            yazi_koy(
                kare,
                "RİTİM!",
                1145,
                34,
                44,
                renk=PEMBE if int(simdi * 10) % 2 == 0 else SARI,
                hiza="orta",
                olcek=olcek_r,
                opak=min(1.0, kalan * 2.5),
            )
        else:
            panel(kare, 1035, 22, 1256, 96, renk=(18, 18, 28), opak=0.65, kenar=PEMBE)
            yazi_koy(kare, f"REKOR: {self.rekor}", 1145, 44, 28, renk=BEYAZ, hiza="orta")

        # 5) Kimse yokken davet ekranı
        if kimse_yok:
            panel(kare, 290, 145, 990, 295, renk=(15, 15, 24), opak=0.82, kenar=SARI)
            nabiz_olcek = 1.0 + 0.05 * math.sin(simdi * 4.5)
            yazi_koy(
                kare,
                "Hava Davulu",
                G // 2,
                160,
                56,
                renk=SARI,
                hiza="orta",
                olcek=nabiz_olcek,
            )
            yazi_koy(
                kare,
                "Parmağını pedlere vur!",
                G // 2,
                232,
                34,
                renk=BEYAZ,
                hiza="orta",
            )

        return kare
