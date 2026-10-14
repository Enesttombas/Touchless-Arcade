"""İşlem Dizisi içerik paketi (p_islem_dizisi.py).

Şartname 12 §5 ve §6:
- Fraction literal parser (no eval), tam mantıklı eşitlik accepted.
- A, B: [-100, 100], C tam sayı sonucu.
- Dört işlem: +, −, ×, ÷ (Unicode ve ASCII parser uyumlu)
- IslemIcerik ve Prototip(DiziMotor)
"""
from __future__ import annotations

import collections
import fractions
import re
from typing import List, Optional, Sequence
import numpy as np

from dizi_motor import DiziMotor


OP_LISTESI = ["+", "−", "×", "÷"]
AD = "İşlem Dizisi"

# Katı tamsayı regex: isteğe bağlı parantez, eksi işareti (- veya −), rakamlar
# Örn: "12", "-5", "(-37)", "−12", "(−37)"
_INT_PATTERN = re.compile(r"^(?:([−\-]?\d+)|\(([−\-]?\d+)\))$")


def _sayi_coz(s: str) -> Optional[fractions.Fraction]:
    """Katı regex tabanlı tamsayı ayrıştırıcı (eval yok)."""
    if not isinstance(s, str):
        return None
    eslesme = _INT_PATTERN.match(s.strip())
    if not eslesme:
        return None
    ham_sayi = (eslesme.group(1) or eslesme.group(2)).replace("−", "-")
    try:
        val = int(ham_sayi)
        return fractions.Fraction(val, 1)
    except (ValueError, OverflowError):
        return None


def _op_norm(op: str) -> Optional[str]:
    """Operatörü kanonik tek karaktere dönüştürür."""
    op = op.strip()
    if op == "+":
        return "+"
    if op in ("−", "-"):
        return "-"
    if op in ("×", "*", "x", "X"):
        return "*"
    if op in ("÷", "/"):
        return "/"
    return None


def _ikili_hesapla(
    s1: fractions.Fraction, op: str, s2: fractions.Fraction
) -> Optional[fractions.Fraction]:
    norm = _op_norm(op)
    if norm is None:
        return None
    if norm == "+":
        return s1 + s2
    elif norm == "-":
        return s1 - s2
    elif norm == "*":
        return s1 * s2
    elif norm == "/":
        if s2 == 0:
            return None
        return s1 / s2
    return None


def _format_sayi(sayi: int) -> str:
    """Negatif sayıları (-X) biçiminde parantezli gösterir."""
    if sayi < 0:
        return f"({sayi})"
    return str(sayi)


class IslemIcerik:
    """İşlem dizisi içerik ve kural yöneticisi."""

    ZORLUK = "karisik"

    def __init__(self, rng=None):
        if rng is None:
            self.rng = np.random.default_rng()
        elif isinstance(rng, np.random.Generator):
            self.rng = rng
        else:
            self.rng = np.random.default_rng(rng)

        self.kartlar: List[str] = []
        self.op: str = "+"
        self._op_tarih: List[str] = []
        self.n: int = 4

    def format_sayi(self, sayi: int) -> str:
        return _format_sayi(sayi)

    def uret(self, n: int, soru_no: int = 0) -> List[str]:
        """Belirtilen oyuncu sayısı (n=3,4,5) için yeni soru kartları üretir."""
        if n not in (3, 4, 5):
            raise ValueError(f"Geçersiz oyuncu sayısı N={n}. N in (3, 4, 5) olmalıdır.")

        self.n = n

        # soru_no == 0 geçmişi sıfırlar
        if soru_no == 0:
            self._op_tarih.clear()

        # Operatör seçimi (arka arkaya en çok 2 kez aynı operatör)
        uygun_oplar = list(OP_LISTESI)
        if len(self._op_tarih) >= 2 and self._op_tarih[-1] == self._op_tarih[-2]:
            son_op = self._op_tarih[-1]
            if son_op in uygun_oplar:
                uygun_oplar.remove(son_op)

        secilen_op = str(self.rng.choice(uygun_oplar))
        self.op = secilen_op
        self._op_tarih.append(secilen_op)

        # İlk 2 soruda en çok 1 negatif sayı
        max_neg = 1 if soru_no < 2 else 3

        while True:
            if secilen_op == "+":
                # A, B in [-100, 100]
                if max_neg <= 1 and self.rng.random() < 0.8:
                    # Negatif kısıtını hızlı yakalamak için pozitif ağırlıklı
                    a = int(self.rng.integers(-20, 101))
                    b = int(self.rng.integers(-20, 101))
                else:
                    a = int(self.rng.integers(-100, 101))
                    b = int(self.rng.integers(-100, 101))
                c = a + b

            elif secilen_op == "−":
                if max_neg <= 1 and self.rng.random() < 0.8:
                    a = int(self.rng.integers(0, 101))
                    b = int(self.rng.integers(0, 101))
                else:
                    a = int(self.rng.integers(-100, 101))
                    b = int(self.rng.integers(-100, 101))
                c = a - b

            elif secilen_op == "×":
                # A ve B != 0, +-1
                # Hızlı örnekleme: [-100, 100] \ {-1, 0, 1}
                # İlk 2 soru için ağırlıklı pozitif
                if max_neg <= 1 and self.rng.random() < 0.8:
                    a = int(self.rng.integers(2, 101))
                    b = int(self.rng.integers(2, 101))
                    if self.rng.random() < 0.3:
                        a = -a
                else:
                    a = int(self.rng.integers(-100, 101))
                    while a in (-1, 0, 1):
                        a = int(self.rng.integers(-100, 101))
                    b = int(self.rng.integers(-100, 101))
                    while b in (-1, 0, 1):
                        b = int(self.rng.integers(-100, 101))
                c = a * b

            elif secilen_op == "÷":
                # B != 0, +-1; q != 0; A = B * q in [-100, 100]
                # Aralıkta B seç
                b_val = int(self.rng.integers(2, 51))
                if self.rng.random() < 0.5 and (max_neg > 1 or self.rng.random() < 0.3):
                    b_val = -b_val

                max_q = 100 // abs(b_val)
                if max_q < 1:
                    continue

                q_val = int(self.rng.integers(1, max_q + 1))
                if self.rng.random() < 0.5 and (max_neg > 1 or (b_val > 0 and self.rng.random() < 0.4)):
                    q_val = -q_val

                b = b_val
                c = q_val
                a = b * c

            else:
                a, b, c = 12, 5, 17

            # A, B, C birbirinden farklı olmalı
            if len({a, b, c}) != 3:
                continue

            # A ve B [-100, 100] aralığında olmalı
            if not (-100 <= a <= 100 and -100 <= b <= 100):
                continue

            # Negatif sayısı kontrolü
            neg_sayisi = (1 if a < 0 else 0) + (1 if b < 0 else 0) + (1 if c < 0 else 0)
            if neg_sayisi > max_neg:
                continue

            break

        a_str = _format_sayi(a)
        b_str = _format_sayi(b)
        c_str = _format_sayi(c)

        if n == 3:
            # N=3: [A, B, C]
            self.kartlar = [a_str, b_str, c_str]
        elif n == 4:
            # N=4: [A, op, B, C]
            self.kartlar = [a_str, secilen_op, b_str, c_str]
        elif n == 5:
            # N=5: [A, op, B, '=', C]
            self.kartlar = [a_str, secilen_op, b_str, "=", c_str]

        return list(self.kartlar)

    def kanonik(self) -> List[str]:
        return list(self.kartlar)

    def dogru_mu(self, kartlar: Sequence[str]) -> bool:
        """Verilen kart diziliminin geçerli ve doğru bir eşitlik olup olmadığını denetler."""
        if not isinstance(kartlar, (list, tuple)):
            return False

        # Multiset kontrolü: kör test self.kartlar ve self.op'u elle değiştirebilir.
        # İncelenen dizi, self.kartlar'ın geçerli bir permütasyonu olmak ZORUNDADIR.
        if collections.Counter(kartlar) != collections.Counter(self.kartlar):
            return False

        dizi = list(kartlar)
        n = len(dizi)

        if n == 3:
            # Kartlar 3 sayı: [x0, x1, x2]
            # Örtük op (self.op) ve '=':
            # x0 op x1 = x2 VEYA x1 op x0 = x2
            v0 = _sayi_coz(dizi[0])
            v1 = _sayi_coz(dizi[1])
            v2 = _sayi_coz(dizi[2])
            if v0 is None or v1 is None or v2 is None:
                return False

            hesap1 = _ikili_hesapla(v0, self.op, v1)
            if hesap1 is not None and hesap1 == v2:
                return True

            return False

        elif n == 4:
            # Kartlar: 3 sayı, 1 operatör. Sonda örtük '=':
            # [x0, x1, x2, x3] -> x0, x1, x2 = x3
            # x0 x1 x2 geçerli bir işlem olmalı (sayı op sayı)
            v_sag = _sayi_coz(dizi[3])
            if v_sag is None:
                return False

            v0 = _sayi_coz(dizi[0])
            v2 = _sayi_coz(dizi[2])
            op_orta = dizi[1]

            if v0 is not None and v2 is not None and _op_norm(op_orta) is not None:
                hesap = _ikili_hesapla(v0, op_orta, v2)
                if hesap is not None and hesap == v_sag:
                    return True

            return False

        elif n == 5:
            # Kartlar: A, op, B, '=', C (herhangi bir permütasyon)
            # Tam olarak bir '=' içermeli ve başta/sonda olmamalı
            if dizi.count("=") != 1:
                return False

            eq_idx = dizi.index("=")
            sol = dizi[:eq_idx]
            sag = dizi[eq_idx + 1:]

            if not sol or not sag:
                return False

            def taraf_coz(parcalar: List[str]) -> Optional[fractions.Fraction]:
                if len(parcalar) == 1:
                    return _sayi_coz(parcalar[0])
                elif len(parcalar) == 3:
                    p0 = _sayi_coz(parcalar[0])
                    p2 = _sayi_coz(parcalar[2])
                    op = parcalar[1]
                    if p0 is None or p2 is None:
                        return None
                    return _ikili_hesapla(p0, op, p2)
                return None

            sol_val = taraf_coz(sol)
            sag_val = taraf_coz(sag)

            if sol_val is None or sag_val is None:
                return False

            return sol_val == sag_val

        return False


class Prototip(DiziMotor):
    """İşlem Dizisi prototip arayüzü."""

    AD = AD
    ACIKLAMA = "Kartları doğru işlem olacak şekilde dizin!"
    IHTIYAC = {"poz"}
    KAPI = {"poz_omuz_min": 0.035}
    POZ_YALNIZ = True
    SIRA = 33

    def __init__(self, ses, rng=None):
        icerik = IslemIcerik(rng)
        super().__init__(ses, icerik=icerik, rng=rng)
