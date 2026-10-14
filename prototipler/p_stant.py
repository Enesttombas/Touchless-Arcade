"""Stand prototip sarmalayıcısı: Filtre + İmza Duvarı."""
from __future__ import annotations

import cekirdek


class Prototip:
    AD = "Filtre + İmza Duvarı"
    ACIKLAMA = "İşaret parmağını kaldır havaya çiz, başparmak yukarı ile kaydet"
    IHTIYAC = {"yuz", "el", "poz?"}
    SIRA = 1

    def __init__(self, ses):
        self.ses = ses
        self.stant = cekirdek.Stant()
        self.simdi = 0.0

    def isle(self, kare, algi: cekirdek.Algi, simdi: float):
        self.simdi = simdi
        return self.stant.isle(
            kare,
            algi.yuzler,
            algi.eller,
            algi.jestler,
            algi.pozlar,
            simdi,
        )

    def tus(self, k: int) -> None:
        if k in (ord("e"), ord("E")):
            self.stant.efekt_ilerlet(self.simdi)  # isle'nin saati; time.time() sahte saatte taşar
        elif k in (ord("c"), ord("C")):
            # Tuval temizle
            self.stant.tuval[:] = 0
