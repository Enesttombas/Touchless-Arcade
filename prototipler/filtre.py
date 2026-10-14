"""Zaman damgalı, vektörel One Euro filtresi ve sınırlı görsel öngörü."""
import math
import numpy as np


class OneEuro:
    def __init__(self, min_cutoff=1.0, beta=0.008, d_cutoff=1.0):
        self.min_cutoff, self.beta, self.d_cutoff = min_cutoff, beta, d_cutoff
        self.t = self.ham = self.son = None
        self.hiz = 0.0

    @staticmethod
    def alfa(cutoff, dt):
        return 1.0 / (1.0 + 1.0 / (2.0 * math.pi * cutoff * dt))

    def suz(self, deger, simdi):
        x = np.asarray(deger, dtype=float)
        if not np.isfinite(x).all() or not math.isfinite(simdi):
            raise ValueError("Nokta ve zaman sonlu olmalı")
        if self.t is None or x.shape != self.son.shape:
            self.t, self.ham, self.son, self.hiz = simdi, x.copy(), x.copy(), np.zeros_like(x)
            return self.son.copy()
        dt = simdi - self.t
        if dt <= 0:
            return self.son.copy()
        a = self.alfa(self.d_cutoff, dt)
        self.hiz += a * ((x - self.ham) / dt - self.hiz)
        a = self.alfa(self.min_cutoff + self.beta * np.abs(self.hiz), dt)
        self.son += a * (x - self.son)
        self.ham, self.t = x.copy(), simdi
        return self.son.copy()

    __call__ = suz


class Ongorucu:
    def __init__(self, sure_ms=30, tavan_px=35):
        self.sure, self.tavan = sure_ms / 1000, tavan_px

    def ongor(self, konum, hiz):
        delta = np.asarray(hiz, dtype=float) * self.sure
        norm = np.linalg.norm(delta, axis=-1, keepdims=True) if delta.ndim else np.abs(delta)
        delta = delta * np.minimum(1, self.tavan / np.maximum(norm, 1e-9))
        return np.asarray(konum) + np.where(norm >= 0.6, delta, 0)


class NoktaTakip:
    def __init__(self):
        self.filtreler = {}

    def suz(self, kimlik, noktalar, simdi):
        return self.filtreler.setdefault(kimlik, OneEuro()).suz(noktalar, simdi)

    def temizle(self, aktif):
        self.filtreler = {k: f for k, f in self.filtreler.items() if k in aktif}
