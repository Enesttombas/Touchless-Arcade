"""Thanos Şıklatması prototipi: El şıklatma jestiyle kadrajdaki kişi toza dönüşüp dağılır ve geri toplanır."""
from __future__ import annotations

import math
from typing import Any, Optional

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
    Maskeci,
    Parcaciklar,
    bulanik_karanlik,
    on_plan,
    panel,
    parilti,
    yazi_koy,
)

ALTIN = (30, 180, 255)


class Prototip:
    AD = "Thanos Şıklatması"
    ACIKLAMA = "Yumruk yapıp elini hızla açarak şıklat, toza dönüş!"
    IHTIYAC = {"el"}
    SIRA = 9

    def __init__(self, ses):
        self.ses = ses
        self.maskeci = Maskeci()
        self.parcaciklar = Parcaciklar(tavan=400)

        # Durumlar: "bekle", "dagilma", "kayip", "toplanma"
        self.durum = "bekle"
        self.durum_baslangic = 0.0
        self.onceki_simdi = 0.0
        self.kare_sayac = 0

        # Jest takibi
        self.son_hazir_zaman = -1.0
        self.hazir_el_pos = (G // 2, Y // 2)

        # Arka plan plakası
        self.arka_plan: Optional[np.ndarray] = None
        self.arka_plan_ogrenildi = False

        # Dağılan parçacık verileri (vektörize numpy)
        self.n_parcacik = 0
        self.p_x0 = np.empty(0, dtype=np.float32)
        self.p_y0 = np.empty(0, dtype=np.float32)
        self.p_vx = np.empty(0, dtype=np.float32)
        self.p_vy = np.empty(0, dtype=np.float32)
        self.p_tetik = np.empty(0, dtype=np.float32)
        self.p_turb_a = np.empty(0, dtype=np.float32)
        self.p_turb_f = np.empty(0, dtype=np.float32)
        self.p_renk = np.empty((0, 3), dtype=np.uint8)

        # Dondurulmuş siluet maskesi ve dondurulmuş kişi karesi
        self.donmus_maske: Optional[np.ndarray] = None
        self.donmus_kare: Optional[np.ndarray] = None

        # Görsel efektler
        self.parlama = 0.0

    def _parcacik_hazirla(self, kare: np.ndarray, maske_tam: np.ndarray) -> bool:
        """Yarım çözünürlükte örneklenmiş toz taneciklerini vektör dizilerine yerleştirir."""
        kucuk_m = cv2.resize(maske_tam, (G // 2, Y // 2), interpolation=cv2.INTER_AREA)
        kucuk_kare = cv2.resize(kare, (G // 2, Y // 2), interpolation=cv2.INTER_AREA)

        ys, xs = np.where(kucuk_m > 0.45)
        toplam = len(ys)
        if toplam < 400:
            return False

        hedef_adet = min(5000, toplam)
        secilen = np.random.choice(toplam, size=hedef_adet, replace=False)
        ys = ys[secilen]
        xs = xs[secilen]

        self.n_parcacik = hedef_adet
        self.p_x0 = (xs * 2).astype(np.float32)
        self.p_y0 = (ys * 2).astype(np.float32)

        renk_orj = kucuk_kare[ys, xs].astype(np.float32)
        altin_renk = np.array(ALTIN, dtype=np.float32)
        karisik = 0.82 * renk_orj + 0.18 * altin_renk
        self.p_renk = np.clip(karisik, 0, 255).astype(np.uint8)

        min_x = float(self.p_x0.min()) if len(self.p_x0) > 0 else 0.0
        max_x = float(self.p_x0.max()) if len(self.p_x0) > 0 else float(G)
        genislik = max(1.0, max_x - min_x)

        x_norm = (self.p_x0 - min_x) / genislik
        rastgele_gecikme = np.random.uniform(0.0, 0.25, size=hedef_adet).astype(np.float32)
        self.p_tetik = (1.0 - x_norm) * 1.1 + rastgele_gecikme

        self.p_vx = -np.random.uniform(180.0, 420.0, size=hedef_adet).astype(np.float32)
        self.p_vy = -np.random.uniform(70.0, 260.0, size=hedef_adet).astype(np.float32)

        self.p_turb_a = np.random.uniform(15.0, 45.0, size=hedef_adet).astype(np.float32)
        self.p_turb_f = np.random.uniform(4.0, 10.0, size=hedef_adet).astype(np.float32)

        return True

    def _ciz_parcaciklar(self, hedef_kare: np.ndarray, dt_ilerleme: float) -> None:
        """NumPy vektörize dizilerle tanecikleri doğrudan kareye boyar."""
        if self.n_parcacik <= 0:
            return

        t_aktif = dt_ilerleme - self.p_tetik
        ucan = t_aktif > 0.0

        if not np.any(ucan):
            return

        t = t_aktif[ucan]
        x0 = self.p_x0[ucan]
        y0 = self.p_y0[ucan]
        vx = self.p_vx[ucan]
        vy = self.p_vy[ucan]
        ta = self.p_turb_a[ucan]
        tf = self.p_turb_f[ucan]
        renk = self.p_renk[ucan]

        px = x0 + vx * t + ta * np.sin(tf * t)
        py = y0 + vy * t + 35.0 * (t**1.6)

        gencer = (px >= 1) & (px < G - 2) & (py >= 1) & (py < Y - 2)
        if not np.any(gencer):
            return

        ix = px[gencer].astype(np.int32)
        iy = py[gencer].astype(np.int32)
        c = renk[gencer]

        hedef_kare[iy, ix] = c
        hedef_kare[iy + 1, ix] = c
        hedef_kare[iy, ix + 1] = c
        hedef_kare[iy + 1, ix + 1] = c

    def isle(self, kare: np.ndarray, algi: Any, simdi: float) -> np.ndarray:
        dt = min(max(simdi - self.onceki_simdi, 0.0), 0.1) if self.onceki_simdi > 0 else 0.033
        self.onceki_simdi = simdi
        self.kare_sayac += 1

        # 1. Maskeyi al ve arka plan plakasını güncelle
        ham_maske = self.maskeci.ver(kare)
        temiz_maske = None
        if ham_maske is not None:
            temiz_maske = on_plan(ham_maske, oran=0.35)

        # Arka plan plakasını hafif ve hızlı şekilde öğren
        if self.durum == "bekle":
            if self.arka_plan is None:
                self.arka_plan = kare.copy()
            elif self.kare_sayac % 3 == 0:
                if temiz_maske is not None:
                    bosluk = temiz_maske < 0.2
                    if np.any(bosluk):
                        kucuk_bg = cv2.resize(self.arka_plan, (G // 2, Y // 2))
                        kucuk_kare = cv2.resize(kare, (G // 2, Y // 2))
                        kucuk_bg[bosluk] = cv2.addWeighted(kucuk_bg[bosluk], 0.88, kucuk_kare[bosluk], 0.12, 0)
                        self.arka_plan = cv2.resize(kucuk_bg, (G, Y), interpolation=cv2.INTER_LINEAR)
                else:
                    cv2.addWeighted(self.arka_plan, 0.90, kare, 0.10, 0, dst=self.arka_plan)
                self.arka_plan_ogrenildi = True

        if self.arka_plan_ogrenildi and self.arka_plan is not None:
            bg_goruntu = self.arka_plan
        else:
            bg_goruntu = bulanik_karanlik(kare, 0.35)

        # 2. Jest ve Ana Oyuncu Tespiti (Victory / Closed_Fist -> Open_Palm)
        en_buyuk_el_idx = -1
        max_boyut = -1.0
        if algi.eller:
            for idx, el in enumerate(algi.eller):
                xs = [p.x for p in el]
                ys = [p.y for p in el]
                boyut = (max(xs) - min(xs)) * (max(ys) - min(ys))
                if boyut > max_boyut:
                    max_boyut = boyut
                    en_buyuk_el_idx = idx

        siklatma_oldu = False
        if en_buyuk_el_idx != -1 and self.durum == "bekle":
            ana_el = algi.eller[en_buyuk_el_idx]
            jest = algi.jestler[en_buyuk_el_idx] if en_buyuk_el_idx < len(algi.jestler) else None
            el_merkez = (int(ana_el[9].x * G), int(ana_el[9].y * Y))

            if jest in ("Victory", "Closed_Fist"):
                self.son_hazir_zaman = simdi
                self.hazir_el_pos = el_merkez

            elif jest == "Open_Palm":
                if 0.0 < (simdi - self.son_hazir_zaman) <= 0.6:
                    siklatma_oldu = True
                    self.son_hazir_zaman = -1.0

        # 3. Durum Mantığı
        if self.durum == "bekle":
            if siklatma_oldu and temiz_maske is not None:
                maske_tam = cv2.resize(temiz_maske, (G, Y), interpolation=cv2.INTER_LINEAR)
                if self._parcacik_hazirla(kare, maske_tam):
                    self.durum = "dagilma"
                    self.durum_baslangic = simdi
                    self.donmus_maske = maske_tam
                    self.donmus_kare = kare.copy()
                    self.parlama = 1.0
                    self.ses.cal("zap", ses=0.85)
                    self.ses.cal("woosh", ses=0.9)
                    self.parcaciklar.yay(
                        self.hazir_el_pos[0],
                        self.hazir_el_pos[1],
                        60,
                        renk=ALTIN,
                        hiz=7.0,
                    )

        cikti = kare

        if self.durum == "dagilma":
            gecen = simdi - self.durum_baslangic
            toplam_sure = 2.5
            ilerleme = min(1.0, gecen / toplam_sure)

            if self.donmus_maske is not None and self.donmus_kare is not None:
                min_x = float(self.p_x0.min()) if len(self.p_x0) > 0 else 0.0
                max_x = float(self.p_x0.max()) if len(self.p_x0) > 0 else float(G)
                genislik = max(1.0, max_x - min_x)

                esik = max_x - ilerleme * 1.25 * genislik
                kolonlar = np.linspace(0, G, G, endpoint=False)
                erime_faktoru = np.clip((kolonlar - esik) / (genislik * 0.15 + 1.0), 0.0, 1.0)
                erime_matris = np.tile(1.0 - erime_faktoru, (Y, 1))

                aktif_maske = (self.donmus_maske * erime_matris)[:, :, None]
                cikti = (self.donmus_kare * aktif_maske + bg_goruntu * (1.0 - aktif_maske)).astype(np.uint8)
            else:
                cikti = bg_goruntu.copy()

            self._ciz_parcaciklar(cikti, gecen)

            if gecen >= toplam_sure:
                self.durum = "kayip"
                self.durum_baslangic = simdi

        elif self.durum == "kayip":
            cikti = bg_goruntu.copy()
            gecen = simdi - self.durum_baslangic
            if gecen >= 1.2:
                self.durum = "toplanma"
                self.durum_baslangic = simdi
                self.ses.cal("woosh", ses=0.75)

        elif self.durum == "toplanma":
            gecen = simdi - self.durum_baslangic
            toplam_sure = 2.0
            oran = min(1.0, gecen / toplam_sure)

            simule_t = (1.0 - oran) * 2.5
            if self.donmus_maske is not None and self.donmus_kare is not None:
                min_x = float(self.p_x0.min()) if len(self.p_x0) > 0 else 0.0
                max_x = float(self.p_x0.max()) if len(self.p_x0) > 0 else float(G)
                genislik = max(1.0, max_x - min_x)

                esik = max_x - (1.0 - oran) * 1.25 * genislik
                kolonlar = np.linspace(0, G, G, endpoint=False)
                erime_faktoru = np.clip((kolonlar - esik) / (genislik * 0.15 + 1.0), 0.0, 1.0)
                erime_matris = np.tile(1.0 - erime_faktoru, (Y, 1))

                aktif_maske = (self.donmus_maske * erime_matris)[:, :, None]
                cikti = (self.donmus_kare * aktif_maske + bg_goruntu * (1.0 - aktif_maske)).astype(np.uint8)
            else:
                cikti = bg_goruntu.copy()

            self._ciz_parcaciklar(cikti, simule_t)

            if gecen >= toplam_sure:
                self.durum = "bekle"
                self.ses.cal("basari", ses=0.8)
                self.parlama = 0.5
                self.donmus_maske = None
                self.donmus_kare = None

        # 4. Altın Şıklatma Parlaması (Neon Hale)
        if self.parlama > 0.01:
            parlama_katman = np.zeros_like(cikti)
            parlama_katman[:] = (int(30 * self.parlama), int(120 * self.parlama), int(200 * self.parlama))
            parilti(cikti, parlama_katman, guc=1.2 * self.parlama, sigma=4.0)
            self.parlama = max(0.0, self.parlama - dt * 2.5)

        # 5. El etrafındaki parçacıkları güncelle ve çiz
        self.parcaciklar.guncelle(dt)
        self.parcaciklar.ciz(cikti)

        # 6. Kullanıcı Arayüzü & Davet Ekranı
        kimse_yok = not bool(algi.eller) and (temiz_maske is None or np.mean(temiz_maske) < 0.03)

        if self.durum == "bekle":
            if kimse_yok:
                nabiz = 1.0 + 0.05 * math.sin(simdi * 4.0)
                panel(cikti, G // 2 - 280, Y // 2 - 80, G // 2 + 280, Y // 2 + 80, opak=0.45, kenar=ALTIN)
                yazi_koy(
                    cikti,
                    "ELİNİ ŞIKLAT",
                    G // 2,
                    Y // 2 - 30,
                    52,
                    renk=ALTIN,
                    hiza="orta",
                    olcek=nabiz,
                )
                yazi_koy(
                    cikti,
                    "Yumruk yap ve avucunu hızla aç",
                    G // 2,
                    Y // 2 + 35,
                    24,
                    renk=BEYAZ,
                    hiza="orta",
                )
            else:
                hazir_mi = 0.0 < (simdi - self.son_hazir_zaman) <= 0.6
                panel(cikti, G // 2 - 220, Y - 72, G // 2 + 220, Y - 20, opak=0.55, kenar=ALTIN if hazir_mi else None)
                if hazir_mi:
                    yazi_koy(cikti, "ŞİMDİ AVUCUNU AÇ!", G // 2, Y - 48, 24, renk=ALTIN, hiza="orta")
                else:
                    yazi_koy(cikti, "Yumruk yap -> Avucunu hızla aç", G // 2, Y - 48, 22, renk=BEYAZ, hiza="orta")

        return cikti
